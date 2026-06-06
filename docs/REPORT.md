# Heuristic Learning Report

[English](REPORT.md) | Chinese

## Optimization History
- **Turn 0** I asked the model to perform 3 improvements to verify whether it could iterate normally.
- **Turn 3** I again asked the model to perform 3 additional improvements to further test its iterative capability.
- **Turn 4** The model's optimization became blocked, and it attempted to conduct a large-scale parameter search on its own; I stopped this behavior and asked the model to make substantive changes instead of merely staying at parameter tuning.
- **Turn 12** Due to prolonged failure in self-optimization, the model exhibited early stopping; I restarted the model and required it to continue iterating until I manually terminated it.
- **Turn 13** The model automatically identified and started `/goal` mode.
- **Turn 35** Since performance over multiple turns had long hovered around -1.00 to -0.90, I asked the model to conduct a large-scale direction search; this shift achieved significant results.
- **Turn 38** The model independently identified that racket speed information was missing from the state and proactively supplemented this information; this addition produced significant effects in subsequent searches.
- **Turn 55** After discovering that only one game remained failed, the model automatically expanded the analysis scope, first examining the failure near the end of that game before deciding whether to continue adjusting.
- **Turn 59** The model independently read the contents of all games, analyzed the true points of loss, and found that these loss points were difficult to summarize as a single type of pattern.
- **Turn 65** The model attempted targeted handling for special games, but this approach resembled a kind of hacking and was unreasonable, so I rejected it; at the same time, the model gradually entered parameter-tuning mode again, a phenomenon that seemed more likely to occur when approaching the context length limit.
- **Turn 68** The model continued attempting to modify new state information to obtain more information, but this information was actually unhelpful, so I stopped it.

![policy_archive_performance.png](../results/policy_archive_performance.png)

## Decision-Making Process
1. Human manually guided decisions that were effective, a total of **1** time:
   - Required the model to search more directions.

2. Reasonable and effective model decisions, a total of **3** times:
   - Automatically identified and started `/goal` mode;
   - Independently identified that racket speed information was missing from the state;
   - Independently expanded the analysis scope.

3. Incorrect model decisions that were later manually corrected by the human, a total of **4** times:
   - Attempted to conduct a large-scale parameter search on its own;
   - Exhibited early stopping on its own;
   - Attempted targeted handling for special games;
   - Continued attempting to modify new state information.

## Lessons
- **Time Audit**: The model lacks time-auditing capability and may start tasks that take too long to execute, such as large-scale parameter searches.
- **Fixed Mindset**: When the context becomes too long, the model can easily fall into a local fixed mindset, causing the strategy to converge prematurely and eventually degrade into parameter tuning, making it difficult to continue effective search.
- **Task Drift**: After clearing the context, the model's understanding of task boundaries may drift, resulting in some hacking strategies that misunderstand feasible solutions.

## Insights
- **Joint Optimization**: In the process of optimizing the target strategy, the model's behavior is not fixed; it may actively adjust and optimize its own optimization process by self-setting goals, supplementing missing information, expanding the analysis scope, and so on.