# Pong RAM 策略报告

[English](POLICY.md) | 中文

## 最终策略概览

最终策略是一个只依赖 RAM 精简状态的确定性启发式策略。策略文件为 `pong_policy.py`，并且只包含一个函数：

```python
def policy(state):
    ...
```

策略不读取图像 observation，不读取比分，不区分第几局或第几分，也不保存任何跨 step 的内部状态。所有回合、所有比分、所有分数点都使用同一套规则。

最终固定评估结果：

```text
conda run -n HL python eval_pong.py --runs 30 --seed 0
average_result=11.00-5.57 average_margin=5.43
```

在 seeds `0..29` 的 30 局 11 分制评估中，最终策略全部获胜。

## 输入状态

策略使用的 state 字段如下：

```text
ball_visible
ball_x
ball_y
ball_dx
ball_dy
player_y
player_dy
```

字段含义：

- `ball_visible`：球是否处于可见/有效状态。发球或重置间隔中，球可能不可见。
- `ball_x`：球的 RAM 横坐标。
- `ball_y`：球的 RAM 纵坐标。
- `ball_dx`：当前 step 与上一 step 的球横向位移。
- `ball_dy`：当前 step 与上一 step 的球纵向位移。
- `player_y`：我方右侧挡板的 RAM 纵坐标。
- `player_dy`：当前 step 与上一 step 的我方挡板纵向位移。

坐标方向：

- `y` 越小越靠上。
- `y` 越大越靠下。
- 动作 `2` 表示向上移动。
- 动作 `3` 表示向下移动。

## 发球状态

代码：

```python
if not state.get("ball_visible", False):
    return 1
```

说明：

当球不可见时，策略直接返回动作 `1`，也就是 `FIRE`。这用于发球或继续开始下一分。

这里没有做回中站位。曾测试过在球不可见时根据 `player_y` 回到中间位置，但会破坏节奏，正式评估明显下降。因此最终策略在不可见状态只负责发球。

## 读取 RAM 状态

代码：

```python
player_y = state["player_y"]
ball_y = state["ball_y"]
ball_x = state["ball_x"]
ball_dx = state.get("ball_dx", 0)
ball_dy = state.get("ball_dy", 0)
player_dy = state.get("player_dy", 0)
```

说明：

策略先读取我方挡板位置、球位置、球速度、挡板速度。

`ball_dx`、`ball_dy`、`player_dy` 使用 `.get(..., 0)`，表示如果某个状态缺失，则默认速度为 `0`。这让策略在第一帧或状态不完整时仍能运行。

## 默认目标位置

代码：

```python
target_y = 118
```

说明：

`target_y` 是策略希望挡板移动到的纵向目标。

默认值 `118` 是一个中间偏稳的位置。它不是精确屏幕中心，而是在当前 RAM 坐标和 Pong 右侧挡板行为下表现较好的默认回收位置。

当球远离我方且不需要立即防守时，策略倾向回到这个位置。

## 球向我方移动时的目标预测

代码：

```python
if ball_dx > 0:
```

说明：

`ball_dx > 0` 表示球正在向右移动，也就是向我方挡板移动。此时策略进入防守/截球逻辑。

### 近距离直接追球

代码：

```python
if ball_x >= 196:
    target_y = ball_y
```

说明：

当 `ball_x >= 196` 时，球已经非常接近我方挡板一侧。此时继续做远距离预测反而不稳定，因此策略直接把目标设置为当前 `ball_y`。

边界数字：

- `196`：进入最后接球区的横坐标阈值。
- 当球到达这个区域后，策略不再用预测落点，而是直接追当前球纵坐标。

### 中远距离预测落点

代码：

```python
else:
    target_offset = 0 if ball_dy > 0 else -8
    target_y = ball_y + ball_dy * max(0, 188 - ball_x) / max(1, abs(ball_dx)) + target_offset
```

说明：

当球正在向我方移动，但还没有到达 `ball_x >= 196` 的最后接球区时，策略预测球到达右侧附近时的 `y` 位置。

预测公式可以拆开理解：

```text
预测目标 = 当前球 y + 纵向速度 * 剩余横向距离 / 横向速度 + 经验偏移
```

边界数字：

- `188`：预测截球用的目标横坐标。策略估计球到达接近右侧挡板前的纵向位置。
- `max(0, 188 - ball_x)`：确保剩余横向距离不会变成负数。
- `max(1, abs(ball_dx))`：避免除以 0；如果横向速度为 0，则至少按 1 处理。
- `-8`：当 `ball_dy <= 0`，也就是球向上或近似水平移动时，目标向上偏移 8 个 RAM y 单位。

`target_offset` 的规则：

- `ball_dy > 0`：球向下，偏移为 `0`。
- `ball_dy <= 0`：球向上或水平，偏移为 `-8`。

这个 `-8` 是最终策略中非常关键的经验修正。多次测试表明，把它改成 `-6` 或 `-10` 都会明显降低平均表现。

## 上下边界反弹预测

代码：

```python
while target_y < 42 or target_y > 208:
    if target_y < 42:
        target_y = 84 - target_y
    elif target_y > 208:
        target_y = 416 - target_y
```

说明：

预测出的 `target_y` 可能越过 Pong 的有效上下边界。这里用镜像反射的方式模拟球撞墙反弹。

边界数字：

- `42`：预测中使用的上边界。
- `208`：预测中使用的下边界。
- `84`：等于 `2 * 42`，用于把越过上边界的目标镜像回来。
- `416`：等于 `2 * 208`，用于把越过下边界的目标镜像回来。

例子：

```text
如果 target_y = 30，小于上边界 42：
反弹后 target_y = 84 - 30 = 54
```

```text
如果 target_y = 220，大于下边界 208：
反弹后 target_y = 416 - 220 = 196
```

这个循环会一直执行，直到 `target_y` 回到 `[42, 208]` 区间内。

## 球刚离开我方时的短暂跟随

代码：

```python
elif ball_x > 150:
    target_y = ball_y
```

说明：

如果球不是向我方移动，但仍然在右半侧附近，策略短暂跟随球的当前 `y`。

边界数字：

- `150`：球离开我方后，仍然允许跟随的横坐标阈值。

当 `ball_x <= 150` 且球不向我方移动时，策略不再跟随球，而是保留默认目标 `118`，准备下一次来球。

## 移动容忍度

代码：

```python
tolerance = 2 if ball_dx > 0 and ball_x >= 196 else 4
if ball_dx > 0 and ball_x >= 204:
    tolerance = 0
```

说明：

`tolerance` 是允许挡板与目标之间存在的误差范围。

如果距离目标的误差在容忍度以内，策略可以选择不移动；如果超过容忍度，则向上或向下移动。

边界数字：

- `4`：普通状态下的默认容忍度。
- `2`：球进入最后接球区 `ball_x >= 196` 后，容忍度收紧到 2。
- `0`：球极度接近我方时 `ball_x >= 204`，容忍度收紧到 0。
- `196`：进入直接追球和严格接球阶段。
- `204`：最终接触前的极限阶段。

最终优化中最重要的提升就是：

```python
if ball_dx > 0 and ball_x >= 204:
    tolerance = 0
```

含义是：当球已经非常接近我方挡板时，不再允许“差一点也可以”的停顿。只要目标距离还没有越过 0，就继续修正挡板位置。

这个规则把固定 seed 30 局评估从：

```text
average_margin=5.13
```

提升到：

```text
average_margin=5.43
```

## 挡板速度提前量

代码：

```python
player_lead = player_dy / 2
if player_dy > 12:
    player_lead = player_dy * 0.75
elif player_dy < -12:
    player_lead = player_dy * 0.75
```

说明：

挡板不是瞬间移动到目标位置的。它有当前速度 `player_dy`，所以如果只比较 `target_y - player_y`，会经常过冲。

`player_lead` 用来预测挡板下一步会继续移动多少。

规则：

- 普通速度时，提前量为 `player_dy / 2`。
- 当 `player_dy > 12`，说明挡板正在快速向下移动，提前量增加到 `player_dy * 0.75`。
- 当 `player_dy < -12`，说明挡板正在快速向上移动，提前量增加到 `player_dy * 0.75`。

边界数字：

- `12`：判断挡板是否高速移动的阈值。
- `0.5`：普通速度下使用一半速度作为提前量。
- `0.75`：高速移动时使用更大的速度比例作为提前量。

## 提前量限制

代码：

```python
if player_lead > 14:
    player_lead = 14
elif player_lead < -14:
    player_lead = -14
```

说明：

如果完全相信速度提前量，挡板在高速运动时会过度补偿。因此策略把 `player_lead` 限制在 `[-14, 14]` 内。

边界数字：

- `14`：最大向下提前量。
- `-14`：最大向上提前量。

这个限制是稳定性的重要组成部分。测试过更大或更小的范围，都会降低整体表现。

## 目标距离计算

代码：

```python
distance = target_y - (player_y + player_lead)
```

说明：

策略不是比较：

```text
target_y - player_y
```

而是比较：

```text
target_y - (player_y + player_lead)
```

也就是把挡板当前速度造成的惯性移动考虑进去。

结果含义：

- `distance < 0`：目标在挡板上方，需要向上。
- `distance > 0`：目标在挡板下方，需要向下。
- `distance` 接近 0：挡板已经接近目标。

## 近目标刹车

代码：

```python
if abs(distance) <= 10:
    if distance < 0 and player_dy < -4:
        return 0
    if distance > 0 and player_dy > 4:
        return 0
```

说明：

当挡板已经接近目标时，如果它还在朝目标方向移动，就提前停止，减少过冲。

边界数字：

- `10`：进入近目标刹车区的距离阈值。
- `-4`：挡板正在明显向上移动的速度阈值。
- `4`：挡板正在明显向下移动的速度阈值。

具体逻辑：

- 如果目标在上方，且挡板已经以 `player_dy < -4` 的速度向上移动，则返回 `0` 停止。
- 如果目标在下方，且挡板已经以 `player_dy > 4` 的速度向下移动，则返回 `0` 停止。

这是一种简单的刹车机制，用于抑制挡板来回震荡。

## 最终动作选择

代码：

```python
if distance < -tolerance:
    return 2
if distance > tolerance:
    return 3
return 0
```

说明：

最终动作根据 `distance` 和 `tolerance` 决定。

动作含义：

- `2`：向上移动。
- `3`：向下移动。
- `0`：不移动。

判断规则：

- 如果 `distance < -tolerance`，目标明显在上方，返回 `2`。
- 如果 `distance > tolerance`，目标明显在下方，返回 `3`。
- 否则误差在容忍范围内，返回 `0`。

在最终阶段 `ball_x >= 204` 时，`tolerance = 0`，因此只要 `distance` 不是正好越过目标，策略就会继续精确修正。

## 策略总结

最终策略可以概括为：

1. 球不可见时直接发球。
2. 球向我方移动时，优先预测截球点。
3. 球非常接近我方时，放弃远距离预测，直接追当前球位置。
4. 预测时考虑上下边界反弹，边界为 `42..208`。
5. 对向上或水平来球使用 `-8` 的经验偏移。
6. 球离开我方但还在右侧时，短暂跟随球；否则回到默认位置 `118`。
7. 用 `player_dy` 估计挡板惯性，提前修正目标距离。
8. 用 `[-14, 14]` 限制速度提前量。
9. 接近目标时提前刹车，避免过冲。
10. 最终接球阶段 `ball_x >= 204` 使用 `tolerance = 0`，提高最后几帧的精度。

最终策略的核心不是复杂状态或特殊比分规则，而是三个稳定控制要点：

- 可靠的落点预测。
- 挡板速度补偿。
- 最后阶段零容忍精修。
