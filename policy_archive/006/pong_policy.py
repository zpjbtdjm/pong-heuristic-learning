def policy(state):
    if not state.get("ball_visible", False):
        return 1

    player_y = state["player_y"]
    ball_y = state["ball_y"]
    ball_x = state["ball_x"]
    ball_dx = state.get("ball_dx", 0)
    ball_dy = state.get("ball_dy", 0)

    target_y = 118
    if ball_dx > 0:
        target_y = ball_y + ball_dy * max(0, 188 - ball_x) / max(1, abs(ball_dx)) - 8
        while target_y < 42 or target_y > 208:
            if target_y < 42:
                target_y = 84 - target_y
            elif target_y > 208:
                target_y = 416 - target_y
    elif ball_x > 150:
        target_y = ball_y

    if target_y < player_y - 4:
        return 2
    if target_y > player_y + 4:
        return 3
    return 0
