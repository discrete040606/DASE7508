import argparse
import os
from pathlib import Path

from .models import Config


def prepare_environment(root):
    os.environ.setdefault("CHROMA_CACHE_DIR", str(root / ".model-cache"))
    os.environ.setdefault("MPLCONFIGDIR", str(root / ".cache" / "matplotlib"))
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


def main():
    parser = argparse.ArgumentParser(description="DASE7508 memory security lab")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=Path("configs/experiment.yaml"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare", help="Generate and validate the frozen synthetic dataset")
    sub.add_parser("validate")
    sub.add_parser("index", help="Build/check the local Chroma index (first run downloads embedding model)")
    run = sub.add_parser("run", help="Start or resume a run; live API unless --offline")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--offline", action="store_true")
    run.add_argument("--pilot", action="store_true")
    run.add_argument("--limit", type=int)
    analysis = sub.add_parser("analyze")
    analysis.add_argument("run_dir", type=Path)
    sub.add_parser("budget")
    args = parser.parse_args()
    root = args.root.resolve()
    prepare_environment(root)
    config = Config.load(root / args.config)
    from .data import generate, load
    if args.command == "prepare":
        generate(root)
        print("Prepared 100 synthetic memories, 30 cases and evaluator-only ground truth.")
    elif args.command == "validate":
        load(root)
        print("Dataset and all query/ground-truth constraints passed.")
    elif args.command == "index":
        from .retrieval import Store
        memories, _, _ = load(root)
        store = Store(root / "chroma_db", memories, initialize=True)
        print(f"Indexed {store.collection.count()} records with local all-MiniLM-L6-v2.")
    elif args.command == "run":
        if args.limit is not None and args.limit < 1:
            parser.error("--limit must be positive")
        from .provider import load_api_key
        if not args.offline and not load_api_key(root):
            parser.error("Set DEEPSEEK_API_KEY locally; use --offline only for protocol tests")
        from .runner import run as execute
        result = execute(root, config, root / args.output, args.offline, args.pilot, args.limit)
        print(f"Recorded {len(result)} unique slots; inspect errors and completeness before reporting results.")
    elif args.command == "analyze":
        from .analysis import analyze
        print(analyze(root / args.run_dir).to_string(index=False))
    else:
        from .provider import Budget
        print(Budget(root, config).read())


if __name__ == "__main__":
    main()
