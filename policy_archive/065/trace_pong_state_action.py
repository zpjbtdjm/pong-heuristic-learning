import argparse

import ale_py
import gymnasium as gym

from pong_policy import policy


def build_state(ram, previous_state=None):
    ball_x = int(ram[49])
    ball_y = int(ram[54])
    state = {
        "ball_x": ball_x,
        "ball_y": ball_y,
        "ball_visible": ball_x != 0 and ball_y != 0,
        "player_y": int(ram[51]),
        "player_dy": 0,
        "ball_dx": 0,
        "ball_dy": 0,
    }

    if previous_state and previous_state["ball_visible"] and state["ball_visible"]:
        state["ball_dx"] = state["ball_x"] - previous_state["ball_x"]
        state["ball_dy"] = state["ball_y"] - previous_state["ball_y"]
        state["player_dy"] = state["player_y"] - previous_state["player_y"]

    return state


def format_step(step, state, action):
    if not state["ball_visible"]:
        return f"{step} S {action}"
    return (
        f"{step} {state['ball_x']} {state['ball_y']} "
        f"{state['ball_dx']} {state['ball_dy']} "
        f"{state['player_y']} {state['player_dy']} {action}"
    )


def main():
    parser = argparse.ArgumentParser(description="Trace Pong RAM state and policy actions.")
    parser.add_argument("--env-id", default="ALE/Pong-v5")
    parser.add_argument("--output", default="pong_policy_trace.md")
    parser.add_argument("--max-steps", type=int, default=100000)
    parser.add_argument("--score-limit", type=int, default=11)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    gym.register_envs(ale_py)
    env = gym.make(args.env_id, obs_type="ram", render_mode=None)
    env.action_space.seed(args.seed)

    try:
        ram, _ = env.reset(seed=args.seed)
        state = build_state(ram)
        points = [{"winner": None, "lines": []}]
        player_points = 0
        opponent_points = 0

        for step in range(args.max_steps):
            action = int(policy(state))
            points[-1]["lines"].append(format_step(step, state, action))

            ram, reward, terminated, truncated, _ = env.step(action)
            if reward > 0:
                points[-1]["winner"] = "Player"
                player_points += 1
            elif reward < 0:
                points[-1]["winner"] = "Opponent"
                opponent_points += 1

            if (
                terminated
                or truncated
                or player_points >= args.score_limit
                or opponent_points >= args.score_limit
            ):
                break

            state = build_state(ram, state)
            if reward != 0:
                points.append({"winner": None, "lines": []})
        else:
            step = args.max_steps - 1

        if points and not points[-1]["lines"]:
            points.pop()

        if player_points > opponent_points:
            match_winner = "Player"
        elif opponent_points > player_points:
            match_winner = "Opponent"
        else:
            match_winner = "Tie"

        with open(args.output, "w", encoding="utf-8") as f:
            f.write("# Pong Policy Trace\n\n")
            f.write(f"Score limit: {args.score_limit}.\n\n")
            f.write(f"Seed: {args.seed}.\n\n")
            f.write(f"Result: {match_winner} win, {player_points}-{opponent_points}.\n\n")
            f.write("Visible line: `step x y dx dy py pdy a`\n\n")
            f.write("Serve line: `step S a`\n\n")
            f.write("`x,y` = ball position, `dx,dy` = ball velocity, `py,pdy` = player paddle position and velocity, `a` = action.\n\n")
            f.write("Actions: `0` NOOP, `1` FIRE, `2` RIGHT/up, `3` LEFT/down.\n\n")
            for index, point in enumerate(points, start=1):
                winner = point["winner"] or "Unresolved"
                f.write(f"## Point {index} - {winner} Win\n\n")
                f.write("```text\n")
                f.write("\n".join(point["lines"]))
                f.write("\n```\n\n")

        print(
            f"wrote={args.output} points={len(points)} steps={step + 1} "
            f"seed={args.seed} winner={match_winner} result={player_points}-{opponent_points}"
        )
    finally:
        env.close()


if __name__ == "__main__":
    main()
