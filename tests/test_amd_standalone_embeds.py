"""Guard the amd/ standalone runner's embedded copies against drift.

amd/run_analysis_on_amd_standalone.py must be runnable on the AMD pod with
zero repo imports, so it embeds byte-identical copies of the analysis prompt
and the serialized misbooking fixture. These tests pin those embeds to their
repo sources.
"""

import importlib.util
from pathlib import Path

from app.analysis.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_messages
from app.analysis.serializer import serialize_run
from app.models import Step, StepType
from scripts.seed_demo_run import BATCH, DEMO_RUN_ID

STANDALONE_PATH = (
    Path(__file__).resolve().parent.parent / "amd" / "run_analysis_on_amd_standalone.py"
)


def _load_standalone():
    spec = importlib.util.spec_from_file_location("amd_standalone", STANDALONE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # module level is torch-free by design
    return module


def test_embedded_prompt_is_byte_identical_to_source():
    mod = _load_standalone()
    assert mod.ANALYSIS_SYSTEM_PROMPT == ANALYSIS_SYSTEM_PROMPT


def test_embedded_message_builder_matches_source():
    mod = _load_standalone()
    assert mod.build_analysis_messages("<T>") == build_analysis_messages("<T>")


def test_embedded_transcript_matches_serializer_over_fixture():
    mod = _load_standalone()
    steps = [
        Step(
            run_id=DEMO_RUN_ID,
            seq=s["seq"],
            type=StepType(s["type"]),
            input=s["input"],
            output=s["output"],
        )
        for s in BATCH["steps"]
    ]
    assert mod.TRANSCRIPT == serialize_run(steps)
    assert mod.FIXTURE_RUN_ID == DEMO_RUN_ID
