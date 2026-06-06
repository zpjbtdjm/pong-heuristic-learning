# Heuristic Learning Experiment on Atari Pong

English | [中文](README_zh.md)

This project documents a **heuristic learning** policy optimization experiment on Atari Pong. The idea is inspired by Jiayi Weng's blog post [Learning Beyond Gradients](https://trinkle23897.github.io/learning-beyond-gradients/).

- Main Result: after 100 rounds of heuristic optimization with Codex, the final policy wins **all** 30 matches under different seed settings, improving the average score margin from -6.40 to 5.43.

## Project Contents

- `pong_policy.py`: final Pong heuristic policy.
- `eval_pong.py`: batch policy evaluation, defaulting to 30 games with an 11-point score limit, and generating `eval_traces/`.
- `trace_pong_state_action.py`: emits a step-by-step trace of state, action, and scoring for one game.
- `eval_policy_archive.py`: evaluates historical policies under `policy_archive/` and writes a CSV summary.
- `plot_policy_archive.py`: plots the archive performance curve from evaluation results.
- `policy_archive/`: historical policy versions saved during optimization.
- `original/`: backup of the initial policy and tracing script.
- `results/`: archive evaluation data and performance plots.
- `sessions/`: full Codex conversation history.

## Result Documents

- [POLICY.md](docs/POLICY.md): final policy explanation, covering policy structure, available state fields, control logic, and fixed evaluation results.
- [REPORT.md](docs/REPORT.md): heuristic learning process report, summarizing optimization history, human/model decisions, and lessons learned.

## Optimization Process

The whole run used Codex-v0.135.0 + GPT-5.5. When optimizing `pong_policy.py`, the process followed [OPT.md](OPT.md). The core policy lives in `pong_policy.py` and is evaluated in batches with fixed seeds through `eval_pong.py`.

- Run evaluation first and record the baseline.
- Before editing, save the current `pong_policy.py` to the next `policy_archive/NNN/` entry.
- `pong_policy.py` may contain only one top-level function: `def policy(state): ...`.
- Use only state fields that are actually visible to the policy.
- Keep a new policy only if the full evaluation improves `average_margin`; otherwise restore from the archive.

The process is recorded in `sessions/rollout.jsonl`. It optimized 100 policy versions in about 5 hours.

Optimization performance curve:

![policy_archive_performance.png](results/policy_archive_performance.png)

The policy's average score margin over the opponent improved from -6.40 to 5.43. The match outcome improved from winning only 1 out of 30 eleven-point games to winning every game.

## Quick Start

### Environment

Install the project dependencies:

```shell
pip install -r requirements.txt
```

### Standard Evaluation

Run the evaluation for the final policy:

```shell
python eval_pong.py --runs 30 --seed 0
```

Evaluation generates per-game traces under `eval_traces/`.

### Single-Game Run

Run the policy without rendering:

```shell
python play_pong.py
```

Generate a single-game trace:

```shell
python trace_pong_state_action.py
```

### Archive Evaluation

Evaluate historical policies in `policy_archive/` and write a CSV:

```shell
python eval_policy_archive.py --runs 30 --seed 0
```

Plot the performance curve from the CSV:

```shell
python plot_policy_archive.py
```

The default output is `results/policy_archive_performance.png`.

## Acknowledgements

Thanks to Jiayi Weng for sharing the heuristic learning idea in [Learning Beyond Gradients](https://trinkle23897.github.io/learning-beyond-gradients/), which provided important inspiration for this project.
