def policy(state):
    if not state.get("ball_visible", False):
        return 1

    player_y = state["player_y"]
    ball_y = state["ball_y"]
    ball_x = state["ball_x"]
    ball_dx = state.get("ball_dx", 0)
    ball_dy = state.get("ball_dy", 0)
    player_dy = state.get("player_dy", 0)

    target_y = 118
    if ball_dx > 0:
        if ball_x >= 196:
            target_y = ball_y
            if ball_y < 64 and ball_dy < 0:
                target_y = ball_y + 8
                if player_dy < -8:
                    target_y = ball_y + 14
            elif ball_y > 190 and ball_dy > 0:
                target_y = ball_y - 8
                if player_dy > 8:
                    target_y = ball_y - 14
        else:
            target_offset = 0 if ball_dy > 0 else -8
            target_y = ball_y + ball_dy * max(0, 188 - ball_x) / max(1, abs(ball_dx)) + target_offset
            while target_y < 42 or target_y > 208:
                if target_y < 42:
                    target_y = 84 - target_y
                elif target_y > 208:
                    target_y = 416 - target_y
    elif ball_x > 150:
        target_y = ball_y

    tolerance = 2 if ball_dx > 0 and ball_x >= 196 else 4

    distance = target_y - (player_y + player_dy / 2)
    if abs(distance) <= 10:
        if distance < 0 and player_dy < -4:
            return 0
        if distance > 0 and player_dy > 4:
            return 0

    if distance < -tolerance:
        return 2
    if distance > tolerance:
        return 3
    return 0
