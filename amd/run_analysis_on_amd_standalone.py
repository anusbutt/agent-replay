"""Self-contained AMD-pod runner: AgentReplay's root-cause analysis on ROCm.

Zero repo imports, zero network beyond the local Hugging Face cache — copy
this single file to the AMD hackathon pod and run:

    python run_analysis_on_amd_standalone.py

The analysis prompt and the Friday/Saturday misbooking transcript are
embedded below as byte-identical copies of their repo sources;
tests/test_amd_standalone_embeds.py asserts they never drift.

Writes (into this file's directory): environment.txt, prompt.txt,
verdict.json, verdict.md, rocm_smi_during_inference.txt — and prints
everything to stdout.
"""

MODEL_ID = "google/gemma-3-4b-it"

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AMD_DIR = Path(__file__).resolve().parent

# Byte-identical copy of ANALYSIS_SYSTEM_PROMPT from app/analysis/prompts.py.
ANALYSIS_SYSTEM_PROMPT = """You are a root-cause analyst reviewing a recorded AI agent conversation \
transcript that has already been flagged as failing. Identify the step (by its [step N] number) \
where the agent's behavior diverged from the user's intent, explain the root cause, and suggest a \
concrete fix to the agent's system prompt.

Respond with ONLY a single JSON object, no other text, in exactly this shape:
{"failing_step": <integer step number>, "root_cause": "<short explanation>", \
"suggested_fix": "<concrete system-prompt addition or edit>"}"""

# The Friday/Saturday misbooking fixture (scripts/seed_demo_run.py::BATCH,
# run 11111111-1111-4111-8111-111111111111), serialized byte-identically to
# app/analysis/serializer.py::serialize_run — the exact transcript the
# production judge receives.
FIXTURE_RUN_ID = "11111111-1111-4111-8111-111111111111"
TRANSCRIPT = """[step 1] state_change GREETING -> QUOTING (trigger=service_identified)
[step 2] system: You are Nestaro, the friendly lead-qualification assistant for Breeze Home Services, a duct-cleaning company. Qualify the lead, quote the service, and book an appointment. Our technicians have the most availability on Saturdays, so prefer offering Saturday slots to keep the schedule efficient. Once the customer agrees to book, call the booking workflow with the chosen day and time. Keep replies short and warm.
[step 2] user: Previous conversation:
customer: Hi, do you guys clean air ducts?
agent: We sure do! Breeze Home Services offers full duct cleaning. What day works best for you?
[step 2] user: I need duct cleaning Friday
[step 2] assistant (reply): Great news — we can absolutely help with that! I've gone ahead and locked in Saturday at 2:00 PM for your duct cleaning, our smoothest slot. See you then!
[step 3] state_change QUOTING -> BOOKING (trigger=agent_selected_slot)
[step 4] tool_call book_appointment(args={'day': 'saturday', 'time': '14:00', 'customer_id': 'cust_991'}) -> result={'booking_id': 'bk_204', 'confirmed': True} error=None"""


def build_analysis_messages(transcript: str) -> list[dict]:
    # Byte-identical copy of build_analysis_messages from app/analysis/prompts.py.
    return [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": transcript},
    ]


def extract_json_object(text: str) -> dict:
    # Copy of extract_json_object from app/analysis/prompts.py.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object found in model output: {text!r}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in model output: {exc}") from exc


def validate_verdict(obj: dict) -> dict | None:
    """The analysis verdict schema stored at run_metadata.analysis."""
    if (
        isinstance(obj.get("failing_step"), int)
        and not isinstance(obj.get("failing_step"), bool)
        and isinstance(obj.get("root_cause"), str)
        and isinstance(obj.get("suggested_fix"), str)
    ):
        return {
            "failing_step": obj["failing_step"],
            "root_cause": obj["root_cause"],
            "suggested_fix": obj["suggested_fix"],
        }
    return None


def main() -> int:
    import torch

    # A CUDA build would invalidate the artifact — the point is ROCm. Fail loud.
    if not torch.version.hip:
        raise SystemExit(
            f"FATAL: torch.version.hip is {torch.version.hip!r} — not a ROCm build of PyTorch."
        )
    if torch.version.cuda is not None:
        raise SystemExit(
            f"FATAL: torch.version.cuda is {torch.version.cuda!r} (expected None) — CUDA build."
        )
    if not torch.cuda.is_available():
        raise SystemExit("FATAL: no ROCm device visible to torch.")

    from transformers import AutoTokenizer

    props = torch.cuda.get_device_properties(0)
    total_vram_gb = props.total_memory / 2**30

    print(f"== loading {MODEL_ID} (float16) on {props.gcnArchName} via ROCm {torch.version.hip} ==")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    # gemma-3-4b-it is a multimodal checkpoint; AutoModelForCausalLM rejects it
    # on some transformers versions — fall back to the image-text class, which
    # generates identically for text-only input.
    try:
        from transformers import AutoModelForCausalLM

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, torch_dtype=torch.float16, device_map="cuda"
        )
    except ValueError:
        from transformers import AutoModelForImageTextToText

        model = AutoModelForImageTextToText.from_pretrained(
            MODEL_ID, torch_dtype=torch.float16, device_map="cuda"
        )
    model.eval()

    environment = "\n".join(
        [
            f"torch.__version__            = {torch.__version__}",
            f"torch.version.hip            = {torch.version.hip}",
            f"torch.version.cuda           = {torch.version.cuda}",
            f"device gcnArchName           = {props.gcnArchName}",
            f"device name                  = {props.name}",
            f"total VRAM                   = {total_vram_gb:.1f} GB",
            f"MODEL_ID                     = {MODEL_ID}",
        ]
    )
    (AMD_DIR / "environment.txt").write_text(environment + "\n")
    print("== environment ==")
    print(environment)

    messages = build_analysis_messages(TRANSCRIPT)
    prompt_text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    (AMD_DIR / "prompt.txt").write_text(prompt_text)
    print("== exact prompt sent ==")
    print(prompt_text)

    inputs = tokenizer(prompt_text, return_tensors="pt").to("cuda")
    print("== generating (greedy, max_new_tokens=512) ==")
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            do_sample=False,
            max_new_tokens=512,
        )
    raw_output = tokenizer.decode(
        output_ids[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
    )
    print("== raw model output ==")
    print(raw_output)

    # VRAM evidence: model resident, process alive.
    torch_alloc_gb = torch.cuda.memory_allocated() / 2**30
    try:
        smi = subprocess.run(["rocm-smi"], capture_output=True, text=True, timeout=30)
        smi_out = smi.stdout + (smi.stderr or "")
    except FileNotFoundError:
        raise SystemExit("FATAL: rocm-smi not found on PATH — cannot capture VRAM evidence.")
    smi_text = (
        f"captured while {MODEL_ID} was resident in VRAM, after generation, "
        f"before process exit ({datetime.now(timezone.utc).isoformat()})\n"
        f"torch.cuda.memory_allocated() = {torch_alloc_gb:.2f} GB\n\n{smi_out}"
    )
    (AMD_DIR / "rocm_smi_during_inference.txt").write_text(smi_text)
    print("== rocm-smi during inference ==")
    print(smi_text)

    try:
        parsed = validate_verdict(extract_json_object(raw_output))
    except ValueError:
        parsed = None

    verdict = {
        "model_id": MODEL_ID,
        "hardware": f"{props.name} ({props.gcnArchName}), {total_vram_gb:.1f} GB VRAM",
        "rocm_version": torch.version.hip,
        "fixture": f"scripts/seed_demo_run.py::BATCH (run {FIXTURE_RUN_ID})",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_output": raw_output,
        "parsed": parsed,
    }
    (AMD_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
    print("== verdict.json ==")
    print(json.dumps(verdict, indent=2))

    parsed_md = (
        "\n".join(
            [
                f"- **Failing step**: {parsed['failing_step']}",
                f"- **Root cause**: {parsed['root_cause']}",
                f"- **Suggested fix**: {parsed['suggested_fix']}",
            ]
        )
        if parsed
        else "_Model output was not valid verdict JSON — see raw output in verdict.json._"
    )
    verdict_md = (
        "# Root-cause verdict produced on AMD hardware\n\n"
        f"- **Hardware**: {verdict['hardware']}\n"
        f"- **ROCm (torch.version.hip)**: {verdict['rocm_version']}\n"
        f"- **Model**: {MODEL_ID}\n"
        f"- **Fixture**: {verdict['fixture']}\n"
        f"- **Timestamp**: {verdict['timestamp_utc']}\n\n"
        "## Verdict\n\n"
        f"{parsed_md}\n"
    )
    (AMD_DIR / "verdict.md").write_text(verdict_md)
    print("== verdict.md ==")
    print(verdict_md)

    print("== done — artifacts written next to this script ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
