"""Run the 21 released turns once against the current context-managed pipeline.

Use --run for a new isolated evaluation or --resume to continue one whose
write-ahead state is already present. Private prompts, answers, memory, and DBs
are saved under data/evaluations/context-pipeline-final/ (gitignored).
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/evaluations/context-pipeline-final"


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else "--run"
    if mode not in {"--run", "--resume"} or len(sys.argv) > 2:
        raise SystemExit("usage: python3 scripts/evaluate_context_pipeline.py [--run|--resume]")
    state_path = OUT / "state.json"
    output_exists = OUT.exists() and any(OUT.iterdir())
    if mode == "--run" and output_exists:
        raise SystemExit(f"Evaluation output already exists at {OUT}; use --resume or archive it first")
    if mode == "--resume" and not state_path.exists():
        raise SystemExit(f"No saved evaluation state at {state_path}; start with --run")

    spec = importlib.util.spec_from_file_location("evaluate_final", ROOT / "scripts/evaluate_final.py")
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    evaluator.OUT = OUT
    evaluator.main()


if __name__ == "__main__":
    main()
