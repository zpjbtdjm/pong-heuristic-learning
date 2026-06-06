# Pong RAM Policy Report

English | [中文](POLICY_zh.md)

## Final Policy Overview

The final policy is a deterministic heuristic policy that depends only on a compact RAM-derived state. The policy file is `pong_policy.py`, and it contains exactly one function:

```python
def policy(state):
    ...
```

The policy does not read image observations, does not read the score, does not distinguish games or points, and does not keep any internal state across steps. The same rule set is used for every rally, score, and point.

Final fixed evaluation result:

```text
conda run -n HL python eval_pong.py --runs 30 --seed 0
average_result=11.00-5.57 average_margin=5.43
```

Across 30 eleven-point games with seeds `0..29`, the final policy wins every game.

## Input State

The policy uses the following state fields:

```text
ball_visible
ball_x
ball_y
ball_dx
ball_dy
player_y
player_dy
```

Field meanings:

- `ball_visible`: whether the ball is visible/valid. During serve or reset intervals, the ball may be invisible.
- `ball_x`: RAM x-coordinate of the ball.
- `ball_y`: RAM y-coordinate of the ball.
- `ball_dx`: horizontal displacement of the ball from the previous step to the current step.
- `ball_dy`: vertical displacement of the ball from the previous step to the current step.
- `player_y`: RAM y-coordinate of the right-side player paddle.
- `player_dy`: vertical displacement of the player paddle from the previous step to the current step.

Coordinate direction:

- Smaller `y` means higher on the screen.
- Larger `y` means lower on the screen.
- Action `2` moves up.
- Action `3` moves down.

## Serve State

Code:

```python
if not state.get("ball_visible", False):
    return 1
```

Explanation:

When the ball is not visible, the policy directly returns action `1`, which is `FIRE`. This serves the ball or starts the next point.

The policy does not recenter the paddle here. A version that moved toward the center based on `player_y` during invisible-ball states was tested, but it broke the rhythm and noticeably reduced formal evaluation performance. Therefore, the final policy only serves when the ball is invisible.

## Reading RAM State

Code:

```python
player_y = state["player_y"]
ball_y = state["ball_y"]
ball_x = state["ball_x"]
ball_dx = state.get("ball_dx", 0)
ball_dy = state.get("ball_dy", 0)
player_dy = state.get("player_dy", 0)
```

Explanation:

The policy first reads the player paddle position, ball position, ball velocity, and paddle velocity.

`ball_dx`, `ball_dy`, and `player_dy` use `.get(..., 0)`, so a missing velocity field defaults to `0`. This lets the policy still run on the first frame or with incomplete state.

## Default Target Position

Code:

```python
target_y = 118
```

Explanation:

`target_y` is the vertical target that the policy wants the paddle to move toward.

The default value `118` is a moderately stable central position. It is not the exact screen center, but it performs well under the current RAM coordinates and right-side Pong paddle behavior.

When the ball is moving away from the player and immediate defense is not needed, the policy tends to return to this position.

## Target Prediction When the Ball Moves Toward the Player

Code:

```python
if ball_dx > 0:
```

Explanation:

`ball_dx > 0` means the ball is moving right, toward the player paddle. The policy then enters its defense/interception logic.

### Direct Tracking at Close Range

Code:

```python
if ball_x >= 196:
    target_y = ball_y
```

Explanation:

When `ball_x >= 196`, the ball is already very close to the player side. At this point, continuing to use long-range prediction is less stable, so the policy sets the target directly to the current `ball_y`.

Boundary number:

- `196`: x-coordinate threshold for the final interception zone.
- Once the ball reaches this zone, the policy stops using predicted landing position and directly tracks the current ball y-coordinate.

### Medium- and Long-Range Landing Prediction

Code:

```python
else:
    target_offset = 0 if ball_dy > 0 else -8
    target_y = ball_y + ball_dy * max(0, 188 - ball_x) / max(1, abs(ball_dx)) + target_offset
```

Explanation:

When the ball is moving toward the player but has not yet reached the final interception zone at `ball_x >= 196`, the policy predicts the y-position where the ball will arrive near the right side.

The prediction can be understood as:

```text
predicted target = current ball y + vertical velocity * remaining horizontal distance / horizontal velocity + empirical offset
```

Boundary numbers:

- `188`: target x-coordinate used for interception prediction. The policy estimates the vertical position before the ball reaches the right-side paddle.
- `max(0, 188 - ball_x)`: keeps the remaining horizontal distance from becoming negative.
- `max(1, abs(ball_dx))`: avoids division by zero; if horizontal velocity is 0, it is treated as at least 1.
- `-8`: when `ball_dy <= 0`, meaning the ball is moving upward or nearly horizontally, the target is shifted upward by 8 RAM y-units.

`target_offset` rule:

- `ball_dy > 0`: the ball is moving downward, offset is `0`.
- `ball_dy <= 0`: the ball is moving upward or horizontally, offset is `-8`.

This `-8` is a critical empirical correction in the final policy. Repeated tests showed that changing it to `-6` or `-10` significantly reduced average performance.

## Top/Bottom Wall Bounce Prediction

Code:

```python
while target_y < 42 or target_y > 208:
    if target_y < 42:
        target_y = 84 - target_y
    elif target_y > 208:
        target_y = 416 - target_y
```

Explanation:

The predicted `target_y` may cross Pong's effective vertical boundaries. This block uses mirror reflection to approximate wall bounces.

Boundary numbers:

- `42`: upper boundary used in prediction.
- `208`: lower boundary used in prediction.
- `84`: equal to `2 * 42`, used to mirror a target that crosses the upper boundary.
- `416`: equal to `2 * 208`, used to mirror a target that crosses the lower boundary.

Example:

```text
If target_y = 30, below the upper boundary 42:
reflected target_y = 84 - 30 = 54
```

```text
If target_y = 220, above the lower boundary 208:
reflected target_y = 416 - 220 = 196
```

The loop continues until `target_y` falls back into `[42, 208]`.

## Short Follow-Through After the Ball Leaves the Player Side

Code:

```python
elif ball_x > 150:
    target_y = ball_y
```

Explanation:

If the ball is not moving toward the player but is still near the right half, the policy briefly follows the current `ball_y`.

Boundary number:

- `150`: x-coordinate threshold that still allows following after the ball leaves the player side.

When `ball_x <= 150` and the ball is not moving toward the player, the policy stops following the ball and keeps the default target `118`, preparing for the next incoming ball.

## Movement Tolerance

Code:

```python
tolerance = 2 if ball_dx > 0 and ball_x >= 196 else 4
if ball_dx > 0 and ball_x >= 204:
    tolerance = 0
```

Explanation:

`tolerance` is the allowed error between the paddle and the target.

If the distance to the target is within the tolerance, the policy may choose not to move. If it exceeds the tolerance, the policy moves up or down.

Boundary numbers:

- `4`: default tolerance in ordinary states.
- `2`: tightened tolerance after the ball enters the final interception zone at `ball_x >= 196`.
- `0`: tightened to zero when the ball is extremely close to the player at `ball_x >= 204`.
- `196`: start of direct tracking and strict interception.
- `204`: final extreme phase before contact.

The most important improvement in the final optimization was:

```python
if ball_dx > 0 and ball_x >= 204:
    tolerance = 0
```

This means that when the ball is already very close to the player paddle, the policy no longer allows a "close enough" pause. As long as the target distance has not crossed zero, it continues correcting the paddle position.

This rule improved fixed-seed 30-game evaluation from:

```text
average_margin=5.13
```

to:

```text
average_margin=5.43
```

## Paddle-Velocity Lead

Code:

```python
player_lead = player_dy / 2
if player_dy > 12:
    player_lead = player_dy * 0.75
elif player_dy < -12:
    player_lead = player_dy * 0.75
```

Explanation:

The paddle does not move instantly to the target. It has a current velocity, `player_dy`, so comparing only `target_y - player_y` often causes overshoot.

`player_lead` predicts how much the paddle will continue moving on the next step.

Rules:

- At ordinary speeds, the lead is `player_dy / 2`.
- When `player_dy > 12`, the paddle is moving downward quickly, so the lead increases to `player_dy * 0.75`.
- When `player_dy < -12`, the paddle is moving upward quickly, so the lead increases to `player_dy * 0.75`.

Boundary numbers:

- `12`: threshold for detecting fast paddle movement.
- `0.5`: uses half the velocity as lead under ordinary speed.
- `0.75`: uses a larger velocity ratio under high speed.

## Lead Limit

Code:

```python
if player_lead > 14:
    player_lead = 14
elif player_lead < -14:
    player_lead = -14
```

Explanation:

If the policy fully trusts the velocity lead, the paddle overcompensates at high speed. Therefore, `player_lead` is clamped to `[-14, 14]`.

Boundary numbers:

- `14`: maximum downward lead.
- `-14`: maximum upward lead.

This limit is an important part of stability. Testing larger or smaller ranges reduced overall performance.

## Target Distance Calculation

Code:

```python
distance = target_y - (player_y + player_lead)
```

Explanation:

The policy does not compare:

```text
target_y - player_y
```

Instead, it compares:

```text
target_y - (player_y + player_lead)
```

This accounts for inertial movement caused by the paddle's current velocity.

Result meaning:

- `distance < 0`: the target is above the paddle, so it needs to move up.
- `distance > 0`: the target is below the paddle, so it needs to move down.
- `distance` close to 0: the paddle is already close to the target.

## Braking Near the Target

Code:

```python
if abs(distance) <= 10:
    if distance < 0 and player_dy < -4:
        return 0
    if distance > 0 and player_dy > 4:
        return 0
```

Explanation:

When the paddle is already near the target, if it is still moving toward the target, the policy stops early to reduce overshoot.

Boundary numbers:

- `10`: distance threshold for entering the near-target braking zone.
- `-4`: velocity threshold indicating the paddle is clearly moving upward.
- `4`: velocity threshold indicating the paddle is clearly moving downward.

Specific logic:

- If the target is above and the paddle is already moving upward with `player_dy < -4`, return `0` to stop.
- If the target is below and the paddle is already moving downward with `player_dy > 4`, return `0` to stop.

This is a simple braking mechanism that suppresses paddle oscillation.

## Final Action Selection

Code:

```python
if distance < -tolerance:
    return 2
if distance > tolerance:
    return 3
return 0
```

Explanation:

The final action is decided by `distance` and `tolerance`.

Action meanings:

- `2`: move up.
- `3`: move down.
- `0`: do not move.

Decision rules:

- If `distance < -tolerance`, the target is clearly above, so return `2`.
- If `distance > tolerance`, the target is clearly below, so return `3`.
- Otherwise, the error is within the tolerance, so return `0`.

In the final phase, when `ball_x >= 204`, `tolerance = 0`. Therefore, as long as `distance` has not exactly crossed the target, the policy keeps making precise corrections.

## Policy Summary

The final policy can be summarized as:

1. Serve directly when the ball is invisible.
2. When the ball is moving toward the player, prioritize predicting the interception point.
3. When the ball is very close to the player, abandon long-range prediction and directly track the current ball position.
4. Account for top/bottom wall bounces during prediction, using boundaries `42..208`.
5. Use an empirical `-8` offset for upward or horizontal incoming balls.
6. Briefly follow the ball after it leaves the player side but is still on the right; otherwise return to the default position `118`.
7. Use `player_dy` to estimate paddle inertia and correct the target distance in advance.
8. Clamp the lead to `[-14, 14]`.
9. Brake near the target to avoid overshoot.
10. Use `tolerance = 0` in the final interception phase at `ball_x >= 204` to improve precision in the last few frames.

The core of the final policy is not complex state or special score rules, but three stable control components:

- Reliable landing prediction.
- Paddle-velocity compensation.
- Zero-tolerance final correction.
