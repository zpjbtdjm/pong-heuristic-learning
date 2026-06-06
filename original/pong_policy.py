def policy(state):
    if not state.get("ball_visible", False):
        return 1

    player_y = state["player_y"]
    ball_y = state["ball_y"]
    ball_x = state["ball_x"]
    ball_dx = state.get("ball_dx", 0)
    ball_dy = state.get("ball_dy", 0)

    target_y = ball_y
    if ball_dx > 0:
        target_y = ball_y + ball_dy * max(0, 190 - ball_x) / max(1, abs(ball_dx))

    if target_y < player_y - 3:
        return 2
    if target_y > player_y + 3:
        return 3
    return 0
