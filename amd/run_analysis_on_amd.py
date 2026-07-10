"""Run AgentReplay's real root-cause analysis prompt on AMD hardware via ROCm.

Executed on the hackathon's AMD compute pod (Radeon gfx1100 / RDNA3, ROCm).
Loads MODEL_ID onto the AMD GPU through PyTorch-for-ROCm, feeds it the exact
analysis prompt AgentReplay uses in production (imported unmodified from
app/analysis/prompts.py) over the real Friday/Saturday misbooking fixture,
and writes the evidence artifacts into this directory:

  environment.txt                 torch/ROCm/device fingerprint
  prompt.txt                      the exact prompt string sent to the model
  verdict.json                    machine-readable verdict + provenance
  verdict.md                      human-readable verdict
  rocm_smi_during_inference.txt   rocm-smi captured while the model occupied VRAM

Run from the repo root:  python amd/run_analysis_on_amd.py
Requires only torch (ROCm build) + transformers. No FastAPI, no DB, no
network beyond the local Hugging Face cache.
"""

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

import json
import subprocess
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

AMD_DIR = Path(__file__).resolve().parent
REPO_ROOT = AMD_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

import torch

# A CUDA build silently "working" through HIP aliases would invalidate this
# artifact — the whole point is inference through ROCm. Fail loud and first.
if not torch.version.hip:
    raise SystemExit(
        f"FATAL: torch.version.hip is {torch.version.hip!r} — this is not a "
        "ROCm build of PyTorch. Install torch for ROCm and re-run."
    )
if torch.version.cuda is not None:
    raise SystemExit(
        f"FATAL: torch.version.cuda is {torch.version.cuda!r} (expected None) "
        "— this torch was built against CUDA, not ROCm. Re-run on the ROCm build."
    )
if not torch.cuda.is_available():
    raise SystemExit("FATAL: no ROCm device visible to torch (torch.cuda.is_available() is False).")

# The production prompt builder + JSON extractor, imported UNMODIFIED — the
# evidence is that the SAME prompt AgentReplay serves in production ran on AMD.
from app.analysis.prompts import build_analysis_messages, extract_json_object

# The Friday/Saturday misbooking fixture lives in scripts/seed_demo_run.py as
# BATCH. That module imports httpx for its own CLI use; httpx isn't needed
# here and may be absent, so stub it before import if missing.
try:
    import httpx  # noqa: F401
except ModuleNotFoundError:
    sys.modules["httpx"] = types.ModuleType("httpx")
from scripts.seed_demo_run import BATCH, DEMO_RUN_ID


def render_transcript(steps: list[dict]) -> str:
    """Mirror app/analysis/serializer.py::serialize_run over fixture dicts.

    That module can't be imported here (it pulls app.models -> sqlmodel,
    excluded from this environment), so the rendering is replicated
    line-for-line to produce the identical "[step N] ..." transcript format
    the production judge receives.
    """
    lines: list[str] = []
    for step in steps:
        if step["type"] == "llm_call":
            for msg in step["input"].get("messages", []):
                lines.append(f"[step {step['seq']}] {msg.get('role', '?')}: {msg.get('content', '')}")
            choices = step["output"].get("choices", [])
            if choices:
                reply = choices[0].get("message", {}).get("content", "")
                lines.append(f"[step {step['seq']}] assistant (reply): {reply}")
        elif step["type"] == "tool_call":
            name = step["input"].get("name", "?")
            args = step["input"].get("args", {})
            result = step["output"].get("result")
            error = step["output"].get("error")
            lines.append(f"[step {step['seq']}] tool_call {name}(args={args}) -> result={result} error={error}")
        elif step["type"] == "state_change":
            from_state = step["input"].get("from_state", "?")
            to_state = step["input"].get("to_state", "?")
            trigger = step["input"].get("trigger", "?")
            lines.append(f"[step {step['seq']}] state_change {from_state} -> {to_state} (trigger={trigger})")
    return "\n".join(lines)


def validate_verdict(obj: dict) -> dict | None:
    """Check the parsed object against the analysis verdict schema used
    everywhere else in the codebase: {failing_step: int, root_cause: str,
    suggested_fix: str}."""
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


def capture_rocm_smi() -> str:
    """Run rocm-smi while the model is resident in VRAM. Mandatory evidence —
    a missing rocm-smi means the capture can't exist, so fail loud."""
    sections: list[str] = []
    try:
        plain = subprocess.run(["rocm-smi"], capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise SystemExit("FATAL: rocm-smi not found on PATH — cannot capture VRAM evidence.")
    sections.append(plain.stdout + (plain.stderr or ""))
    try:
        vram = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram"], capture_output=True, text=True, timeout=30
        )
        sections.append(vram.stdout + (vram.stderr or ""))
    except Exception as exc:  # noqa: BLE001 — the plain capture above already suffices
        sections.append(f"(rocm-smi --showmeminfo vram failed: {exc})")
    return "\n".join(sections)


def main() -> int:
    from transformers import AutoModelForCausalLM, AutoTokenizer

    props = torch.cuda.get_device_properties(0)
    total_vram_gb = props.total_memory / 2**30

    print(f"== loading {MODEL_ID} (float16) onto {props.gcnArchName} via ROCm {torch.version.hip} ==")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float16).to("cuda")
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

    transcript = render_transcript(BATCH["steps"])
    messages = build_analysis_messages(transcript)
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
            pad_token_id=tokenizer.eos_token_id,
        )
    raw_output = tokenizer.decode(
        output_ids[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
    )
    print("== raw model output ==")
    print(raw_output)

    # Capture VRAM evidence NOW — model still resident, process still alive.
    torch_alloc_gb = torch.cuda.memory_allocated() / 2**30
    smi_capture = capture_rocm_smi()
    smi_text = (
        f"captured while {MODEL_ID} was resident in VRAM, after generation, "
        f"before process exit ({datetime.now(timezone.utc).isoformat()})\n"
        f"torch.cuda.memory_allocated() = {torch_alloc_gb:.2f} GB\n\n{smi_capture}"
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
        "fixture": f"scripts/seed_demo_run.py::BATCH (run {DEMO_RUN_ID})",
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

    print("== done — artifacts written to amd/ ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
