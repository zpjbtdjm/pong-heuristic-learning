import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path


AVERAGE_RE = re.compile(
    r"average_result=([0-9.]+)-([0-9.]+)\s+average_margin=([-0-9.]+)"
)


def archive_entries(archive_dir):
    entries = []
    for path in sorted(archive_dir.iterdir()):
        if not path.is_dir() or not path.name.isdigit():
            continue
        policy_path = path / "pong_policy.py"
        if policy_path.exists():
            entries.append((int(path.name), path.name, policy_path))
    return entries


def parse_eval_output(output):
    match = AVERAGE_RE.search(output)
    if not match:
        raise RuntimeError("could not parse eval_pong.py average line")
    return {
        "average_player": float(match.group(1)),
        "average_opponent": float(match.group(2)),
        "average_margin": float(match.group(3)),
    }


def run_eval(args, archive_name, trace_dir):
    command = [
        sys.executable,
        "eval_pong.py",
        "--runs",
        str(args.runs),
        "--seed",
        str(args.seed),
        "--score-limit",
        str(args.score_limit),
        "--max-steps",
        str(args.max_steps),
        "--output-dir",
        str(trace_dir),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    result = parse_eval_output(completed.stdout)
    result["archive"] = archive_name
    result["stdout"] = completed.stdout
    return result


def output_path(root, value):
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def write_csv(rows, output_csv):
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "archive",
                "average_player",
                "average_opponent",
                "average_margin",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "archive": row["archive"],
                    "average_player": f"{row['average_player']:.4f}",
                    "average_opponent": f"{row['average_opponent']:.4f}",
                    "average_margin": f"{row['average_margin']:.4f}",
                }
            )


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate archived Pong policies and write a CSV summary."
    )
    parser.add_argument("--archive-dir", default="policy_archive")
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--score-limit", type=int, default=11)
    parser.add_argument("--max-steps", type=int, default=100000)
    parser.add_argument("--output-csv", default="results/policy_archive_eval.csv")
    parser.add_argument("--start", type=int, default=None, help="First archive number to evaluate.")
    parser.add_argument("--end", type=int, default=None, help="Last archive number to evaluate.")
    parser.add_argument(
        "--trace-root",
        default="eval_traces",
        help="Shared eval trace directory. Each archive evaluation overwrites the previous traces.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    archive_dir = root / args.archive_dir
    policy_path = root / "pong_policy.py"
    backup_path = root / ".pong_policy_eval_backup.py"
    output_csv = output_path(root, args.output_csv)
    trace_root = output_path(root, args.trace_root)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    trace_root.mkdir(parents=True, exist_ok=True)

    entries = archive_entries(archive_dir)
    if args.start is not None:
        entries = [entry for entry in entries if entry[0] >= args.start]
    if args.end is not None:
        entries = [entry for entry in entries if entry[0] <= args.end]
    if not entries:
        raise SystemExit(f"no archived policies found in {archive_dir}")

    shutil.copyfile(policy_path, backup_path)
    rows = []

    try:
        for _, archive_name, archived_policy in entries:
            shutil.copyfile(archived_policy, policy_path)
            row = run_eval(args, archive_name, trace_root)
            rows.append(row)
            print(
                f"archive={archive_name} "
                f"average_result={row['average_player']:.2f}-{row['average_opponent']:.2f} "
                f"average_margin={row['average_margin']:.2f}",
                flush=True,
            )
    finally:
        shutil.copyfile(backup_path, policy_path)
        backup_path.unlink(missing_ok=True)

    write_csv(rows, output_csv)
    print(f"wrote_csv={output_csv}")


if __name__ == "__main__":
    main()
