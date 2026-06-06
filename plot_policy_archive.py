import argparse
import csv
import os
from pathlib import Path

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import to_rgba


REPORT_EVENTS = [
    {"turn": 0, "source": "human", "label": "H", "text": "要求约 3 次迭代"},
    {"turn": 3, "source": "human", "label": "H", "text": "要求额外 3 次迭代"},
    {"turn": 4, "source": "model", "label": "M", "text": "倾向大量参数搜索"},
    {"turn": 4, "source": "human", "label": "H", "text": "制止参数搜索，要求实质改动"},
    {"turn": 12, "source": "model", "label": "M", "text": "长期失败后早停止"},
    {"turn": 12, "source": "human", "label": "H", "text": "要求继续迭代直到手动结束"},
    {"turn": 13, "source": "model", "label": "M", "text": "自动进入 goal 模式"},
    {"turn": 35, "source": "human", "label": "H", "text": "要求大规模转向搜索"},
    {"turn": 38, "source": "model", "label": "M", "text": "识别并补充 state"},
    {"turn": 55, "source": "model", "label": "M", "text": "定位只剩一局输并分析末端失败"},
    {"turn": 59, "source": "model", "label": "M", "text": "汇总失分点并识别模式复杂"},
    {"turn": 65, "source": "model", "label": "M", "text": "尝试特殊局数处理"},
    {"turn": 65, "source": "human", "label": "H", "text": "拒绝特殊局数 hacking"},
    {"turn": 68, "source": "model", "label": "M", "text": "继续倾向改其他无关 state"},
    {"turn": 68, "source": "human", "label": "H", "text": "制止继续改 state"},
]

MAJOR_EVENTS = [
    {"turn": 13, "label": "*", "text": "自动开启 /goal 模式"},
    {"turn": 35, "label": "*", "text": "要求大规模转向搜索"},
    {"turn": 38, "label": "*", "text": "自动补充 state"},
    {"turn": 55, "label": "*", "text": "自动分析其他失败"},
]


def output_path(root, value):
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def read_rows(input_csv):
    rows = []
    with input_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "archive": int(row["archive"]),
                    "average_player": float(row["average_player"]),
                    "average_opponent": float(row["average_opponent"]),
                    "average_margin": float(row["average_margin"]),
                }
            )

    if not rows:
        raise RuntimeError(f"no rows found in {input_csv}")

    return rows


def event_x_positions(events):
    grouped = {}

    for event in events:
        grouped.setdefault(event["turn"], []).append(event)

    positioned = []

    for turn, group in grouped.items():
        sources = [event["source"] for event in group]

        is_mh_pair = (
            len(group) == 2
            and set(sources) == {"model", "human"}
        )

        if is_mh_pair:
            positioned.append(
                {
                    "turn": turn,
                    "source": "mh",
                    "label": "MH",
                    "text": "Model-Human adjacent decision",
                    "x": turn,
                    "event_lane": "mh_pair",
                }
            )
        else:
            count = len(group)

            for index, event in enumerate(group):
                offset = 0.0

                if count > 1:
                    offset = (index - (count - 1) / 2) * 1.1

                event_with_x = dict(event)
                event_with_x["x"] = turn + offset

                if event["source"] == "human":
                    event_with_x["event_lane"] = "single_human"
                else:
                    event_with_x["event_lane"] = "single_model"

                positioned.append(event_with_x)

    positioned.sort(key=lambda e: e["x"])

    return positioned


def gradient_box_text(ax, x, y, text, left_color, right_color, edge_color, y_span):
    width = 2.8
    height = y_span * 0.062

    left = np.array(to_rgba(left_color))
    right = np.array(to_rgba(right_color))
    gradient = np.linspace(left, right, 256).reshape(1, 256, 4)

    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle=f"round,pad=0,rounding_size={height * 0.2}",
        facecolor="none",
        edgecolor="none",
        linewidth=0,
        zorder=5,
    )
    ax.add_patch(patch)

    image = ax.imshow(
        gradient,
        extent=[
            x - width / 2,
            x + width / 2,
            y - height / 2,
            y + height / 2,
        ],
        origin="lower",
        aspect="auto",
        zorder=4.9,
    )
    image.set_clip_path(patch)

    ax.text(
        x,
        y,
        text,
        color="white",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        zorder=6,
    )


def write_plot(rows, output_png, events):
    bg_color = "#1e1e2e"
    surface_color = "#252536"
    text_color = "#e8e8f0"
    grid_color = "#3a3a50"

    human_color = "#ff6b6b"
    model_color = "#54c8ff"
    mh_line_color = "#4ade80"
    major_color = "#ffb347"

    # curve_color = "#4ade80"
    curve_color = "#7c9cff"

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "Times New Roman", "Times"],
            "axes.unicode_minus": False,
            "axes.titlesize": 28,
            "axes.labelsize": 20,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "legend.fontsize": 15,
            "figure.facecolor": bg_color,
            "axes.facecolor": surface_color,
            "axes.edgecolor": grid_color,
            "axes.labelcolor": text_color,
            "xtick.color": text_color,
            "ytick.color": text_color,
            "text.color": text_color,
            "grid.color": grid_color,
            "grid.linestyle": "-",
            "grid.linewidth": 0.5,
            "legend.facecolor": surface_color,
            "legend.edgecolor": grid_color,
            "legend.labelcolor": text_color,
        }
    )

    x_values = np.array([row["archive"] for row in rows])
    margins = np.array([row["average_margin"] for row in rows])

    y_min = float(margins.min())
    y_max = float(margins.max())
    y_span = max(1.0, y_max - y_min)
    best_index = int(np.argmax(margins))
    best_x = x_values[best_index]
    best_y = margins[best_index]

    fig, ax = plt.subplots(figsize=(16, 9))

    ax.fill_between(
        x_values,
        margins,
        alpha=0.15,
        color=curve_color,
        zorder=1,
    )

    ax.plot(
        x_values,
        margins,
        marker="o",
        markersize=4.5,
        linewidth=2.0,
        color=curve_color,
        markeredgecolor=curve_color,
        markerfacecolor=curve_color,
        alpha=0.9,
        label="Current Best Margin",
        zorder=3,
    )

    ax.axhline(
        0,
        color="#555566",
        linewidth=1.0,
        linestyle="-",
        zorder=1,
    )
    ax.axvline(
        best_x,
        color="#ffd166",
        linestyle="-.",
        linewidth=1.8,
        alpha=0.9,
        zorder=2,
    )

    ax.text(
        best_x + 5.4,
        y_max - y_span * 0.285,
        "Converged\nMargin=5.43",
        color="#2e2e3e",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.32",
            "facecolor": "#f6c58f",
            "edgecolor": "#e8aa62",
            "alpha": 0.88,
        },
        zorder=5,
    )

    positioned_events = event_x_positions(events)

    for event in positioned_events:
        if event["turn"] < x_values.min() or event["turn"] > x_values.max():
            continue

        if event["source"] == "mh":
            color = mh_line_color
        elif event["source"] == "human":
            color = human_color
        else:
            color = model_color

        ax.axvline(
            event["x"],
            color=color,
            linestyle="--",
            linewidth=1.2,
            alpha=0.6,
            zorder=2,
        )

        if event.get("event_lane") == "mh_pair":
            y_base = y_max + y_span * 0.13

            gradient_box_text(
                ax,
                event["x"],
                y_base,
                event["label"],
                model_color,
                human_color,
                mh_line_color,
                y_span,
            )

        elif event.get("event_lane") == "single_human":
            y_base = y_max + y_span * 0.035

            ax.text(
                event["x"],
                y_base,
                event["label"],
                color="white",
                ha="center",
                va="center",
                fontsize=13,
                fontweight="bold",
                bbox={
                    "boxstyle": "round,pad=0.28",
                    "facecolor": human_color,
                    "edgecolor": human_color,
                    "alpha": 0.92,
                },
                zorder=5,
            )

        else:
            y_base = y_max + y_span * 0.225

            ax.text(
                event["x"],
                y_base,
                event["label"],
                color="white",
                ha="center",
                va="center",
                fontsize=13,
                fontweight="bold",
                bbox={
                    "boxstyle": "round,pad=0.28",
                    "facecolor": model_color,
                    "edgecolor": model_color,
                    "alpha": 0.92,
                },
                zorder=5,
            )

    for event in MAJOR_EVENTS:
        if event["turn"] < x_values.min() or event["turn"] > x_values.max():
            continue

        ax.text(
            event["turn"],
            y_max + y_span * 0.34,
            event["label"],
            color="#1e1e2e",
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.32",
                "facecolor": major_color,
                "edgecolor": "#e69520",
                "alpha": 0.95,
            },
            zorder=5,
        )

    ax.set_xlim(x_values.min() - 1, x_values.max() + 1)
    ax.set_ylim(y_min - y_span * 0.10, y_max + y_span * 0.43)

    ax.set_xlabel(
        "Policy Iteration Steps",
        labelpad=12,
        fontweight="bold",
    )
    ax.set_ylabel(
        "Average Margin (player - opponent)",
        labelpad=12,
        fontweight="bold",
    )
    ax.set_title(
        "Pong Policy Performance",
        pad=20,
        fontweight="bold",
    )

    ax.grid(True, alpha=0.5, zorder=0)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    legend_elements = [
        Line2D(
            [0],
            [0],
            color=curve_color,
            marker="o",
            markersize=6,
            linewidth=1.6,
            label="Current Best Margin",
        ),
        Line2D(
            [0],
            [0],
            color=human_color,
            linestyle="--",
            linewidth=1.5,
            label="Human Intervention (H)",
        ),
        Line2D(
            [0],
            [0],
            color=model_color,
            linestyle="--",
            linewidth=1.5,
            label="Model Decision (M)",
        ),
        Line2D(
            [0],
            [0],
            color=mh_line_color,
            linestyle="--",
            linewidth=1.5,
            label="Model Error → Human Correction (MH)",
        ),
        Line2D(
            [0],
            [0],
            color=major_color,
            marker="s",
            markersize=10,
            linestyle="None",
            markerfacecolor=major_color,
            label="Key Interventions / Decisions (*)",
        ),
    ]

    ax.legend(
        handles=legend_elements,
        loc="lower right",
        framealpha=0.95,
        edgecolor=grid_color,
        fontsize=14,
        fancybox=True,
    )

    fig.tight_layout()
    fig.savefig(
        output_png,
        dpi=180,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.show()
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Plot Pong policy archive performance from CSV."
    )
    parser.add_argument(
        "--input-csv",
        default="results/policy_archive_eval.csv",
    )
    parser.add_argument(
        "--output-plot",
        default="results/policy_archive_performance.png",
    )

    args = parser.parse_args()

    root = Path.cwd()
    input_csv = output_path(root, args.input_csv)
    output_png = output_path(root, args.output_plot)

    output_png.parent.mkdir(parents=True, exist_ok=True)

    rows = read_rows(input_csv)
    write_plot(rows, output_png, REPORT_EVENTS)

    print(f"wrote_plot={output_png}")


if __name__ == "__main__":
    main()