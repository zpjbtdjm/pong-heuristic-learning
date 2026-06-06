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


def run_episode(env, max_steps, score_limit):
    ram, _ = env.reset()
    state = build_state(ram)
    total_reward = 0.0
    player_points = 0
    opponent_points = 0

    for step in range(max_steps):
        action = int(policy(state))
        ram, reward, terminated, truncated, _ = env.step(action)
        total_reward += float(reward)
        if reward > 0:
            player_points += 1
        elif reward < 0:
            opponent_points += 1
        state = build_state(ram, state)

        if (
            terminated
            or truncated
            or player_points >= score_limit
            or opponent_points >= score_limit
        ):
            return total_reward, step + 1, player_points, opponent_points

    return total_reward, max_steps, player_points, opponent_points


def main():
    parser = argparse.ArgumentParser(description="Run a simple heuristic policy on Gymnasium Atari Pong.")
    parser.add_argument("--env-id", default="ALE/Pong-v5")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--max-steps", type=int, default=10000)
    parser.add_argument("--score-limit", type=int, default=11)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()

    render_mode = None if args.no_render else "human"
    gym.register_envs(ale_py)
    env = gym.make(args.env_id, obs_type="ram", render_mode=render_mode)

    try:
        for episode in range(1, args.episodes + 1):
            reward, steps, player_points, opponent_points = run_episode(
                env, args.max_steps, args.score_limit
            )
            if player_points > opponent_points:
                winner = "Player"
            elif opponent_points > player_points:
                winner = "Opponent"
            else:
                winner = "Tie"
            print(
                f"episode={episode} result={player_points}-{opponent_points} "
                f"winner={winner} reward={reward:.1f} steps={steps}"
            )
    finally:
        env.close()


if __name__ == "__main__":
    main()
