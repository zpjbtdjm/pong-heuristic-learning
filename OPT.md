# OPT.md

## Policy Optimization Loop

When optimizing `pong_policy.py`, follow this loop every time:

1. Run evaluation first.

```bash
conda run -n HL python eval_pong.py
```

Use the printed `average_result` and `average_margin` as the baseline metric for the current policy.

2. Read the first trace from the evaluation.

```bash
sed -n '1,220p' eval_traces/pong_policy_trace_01.md
```

Analyze the current policy's strengths and weaknesses from this trace before editing code. Focus on information that `pong_policy.py` can actually use:

- ball position: `x`, `y`
- ball velocity: `dx`, `dy`
- player paddle position: `py`
- chosen action: `a`
- point winner: `Player Win` or `Opponent Win`

Ignore variables that are not available to `pong_policy.py`.

3. Archive the previous policy before editing.

Before changing `pong_policy.py`, create a numbered archive entry for the current code:

```bash
mkdir -p policy_archive/001
cp pong_policy.py policy_archive/001/pong_policy.py
```

Use the next available three-digit number for each optimization attempt, such as `002`, `003`, and so on. Never overwrite an existing archive entry.

Each archive entry represents the policy code before that optimization attempt. This keeps the full optimization history traceable even when a candidate policy is later rejected.

4. Update only `pong_policy.py`.

The policy file must remain a single-function file:

```python
def policy(state):
    ...
```

Do not add extra top-level functions, imports, classes, or side effects.

5. Re-run evaluation.

```bash
conda run -n HL python eval_pong.py
```

Compare the new `average_margin` against the baseline. Higher is better.

6. Keep or revert.

- If the new `average_margin` improves, keep the updated `pong_policy.py`.
- If the new `average_margin` does not improve, restore `pong_policy.py` from the numbered archive entry created for this attempt.
- Do not keep a policy change that only looks better in a single trace but fails the 10-run evaluation.

7. Repeat the loop.

Each iteration must be based on the latest evaluation result and the latest `eval_traces/pong_policy_trace_01.md`.
