import argparse
import re
import subprocess
import sys
from pathlib import Path


RESULT_RE = re.compile(r"result=(\d+)-(\d+)")


def run_trace(index, output_dir, score_limit, max_steps, seed):
    output_path = output_dir / f"pong_policy_trace_{index:02d}.md"
    command = [
        sys.executable,
        "trace_pong_state_action.py",
        "--output",
        str(output_path),
        "--score-limit",
        str(score_limit),
        "--max-steps",
        str(max_steps),
        "--seed",
        str(seed),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    match = RESULT_RE.search(completed.stdout)
    if not match:
        raise RuntimeError(f"could not parse trace result: {completed.stdout.strip()}")

    player_score = int(match.group(1))
    opponent_score = int(match.group(2))
    return player_score, opponent_score, completed.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Evaluate the Pong policy over repeated traces.")
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--score-limit", type=int, default=11)
    parser.add_argument("--max-steps", type=int, default=100000)
    parser.add_argument("--output-dir", default="eval_traces")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    player_scores = []
    opponent_scores = []

    for index in range(1, args.runs + 1):
        seed = args.seed + index - 1
        player_score, opponent_score, summary = run_trace(
            index, output_dir, args.score_limit, args.max_steps, seed
        )
        player_scores.append(player_score)
        opponent_scores.append(opponent_score)
        print(f"run={index} {summary}")

    avg_player = sum(player_scores) / args.runs
    avg_opponent = sum(opponent_scores) / args.runs
    avg_margin = avg_player - avg_opponent

    print(
        f"average_result={avg_player:.2f}-{avg_opponent:.2f} "
        f"average_margin={avg_margin:.2f}"
    )


if __name__ == "__main__":
    main()
