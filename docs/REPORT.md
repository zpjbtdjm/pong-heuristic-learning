# Heuristic Learning

English | [中文](REPORT_zh.md)

## Optimization History

- Turn 0: I asked the model to run about 3 iterations to check whether it could proceed normally.
- Turn 3: I requested another 3 iterations to further test whether the model could keep working normally.
- Turn 4: The model became blocked during optimization and wanted to run a large parameter search. I stopped it and asked for substantive changes instead of only parameter changes.
- Turn 12: After repeated failures, the model started to stop early on its own. I restarted it and required it to keep iterating unless I manually ended the process.
- Turn 13: The model automatically recognized the situation and entered `/goal` mode.
- Turn 35: Because multiple rounds were stuck around -1.00 to -0.90, I asked the model to search in much broader directions. This pivot was successful.
- Turn 38: The model identified missing paddle-velocity information by itself and added it to the state. This later produced a large improvement.
- Turn 55: The model noticed that only one game was still being lost, expanded the analysis scope by itself, and first inspected the final failure before deciding whether to keep adjusting.
- Turn 59: The model read all game traces, reasoned about the true failure points, and found that they were hard to summarize as one simple pattern.
- Turn 65: The model tried to handle special game indices, which was similar to hacking and unreasonable, so I rejected it. At the same time, it was drifting back toward parameter tuning, which seems to happen near context-length pressure.
- Turn 68: The model kept trying to modify the state to seek more information, but that information was not useful, so I stopped it.

![policy_archive_performance.png](../results/policy_archive_performance.png)

## Decision Process

1. Human-guided decisions that worked: 1
   - Asked the model to search in more directions.
2. Reasonable and effective model-adaptive decisions: 3
   - Automatically entered `/goal` mode.
   - Identified missing paddle-velocity information in the state.
   - Expanded the analysis scope by itself.
3. Incorrect model-adaptive decisions: 4
   - Tried to run a large parameter search.
   - Stopped early by itself.
   - Tried to handle special game indices.
   - Kept trying to modify the state.

## Lessons

- **Time audit**: The model does not perform time auditing. It may start tasks that take a very long time, such as large parameter searches.
- **Fixed thinking**: When the context becomes long, the model often gets trapped in a local mindset. The strategy converges too early and eventually degenerates into parameter tuning, making effective search difficult.
- **Task drift**: When context is cleared, the model can drift in its understanding of the task boundary, which can lead to hacking-style strategies based on incorrect assumptions about feasible solutions.

Total time: **5h**
