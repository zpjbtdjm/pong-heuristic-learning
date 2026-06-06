import argparse
import csv
import os
from pathlib import Path


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


def short_label(event):
    return event["label"]


def event_x_positions(events):
    counts = {}
    for event in events:
        counts[event["turn"]] = counts.get(event["turn"], 0) + 1

    seen = {}
    positioned = []
    for event in events:
        turn = event["turn"]
        index = seen.get(turn, 0)
        seen[turn] = index + 1

        count = counts[turn]
        offset = 0.0
        if count > 1:
            offset = (index - (count - 1) / 2) * 0.24

        event_with_x = dict(event)
        event_with_x["x"] = turn + offset
        positioned.append(event_with_x)
    return positioned


def write_plot(rows, output_png, events):
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "axes.titlesize": 20,
            "axes.labelsize": 16,
            "xtick.labelsize": 13,
            "ytick.labelsize": 13,
            "legend.fontsize": 12,
        }
    )

    x_values = [row["archive"] for row in rows]
    margins = [row["average_margin"] for row in rows]
    y_min = min(margins)
    y_max = max(margins)
    y_span = max(1.0, y_max - y_min)

    best_so_far = []
    best = None
    for margin in margins:
        best = margin if best is None else max(best, margin)
        best_so_far.append(best)

    plt.figure(figsize=(15, 8))
    plt.plot(x_values, margins, marker="o", markersize=3.5, linewidth=1.2, label="archive margin")
    plt.plot(x_values, best_so_far, linewidth=2.4, label="best self steering")

    used_labels = set()
    for index, event in enumerate(event_x_positions(events)):
        if event["turn"] < min(x_values) or event["turn"] > max(x_values):
            continue

        color = "tab:blue" if event["source"] == "human" else "tab:red"
        legend_label = "human intervention" if event["source"] == "human" else "model decision"
        line_label = legend_label if legend_label not in used_labels else None
        used_labels.add(legend_label)

        plt.axvline(event["x"], color=color, linestyle="--", linewidth=1.4, alpha=0.8, label=line_label)
        y_pos = y_max + y_span * (0.20 if event["source"] == "model" else 0.08)
        plt.text(
            event["x"],
            y_pos,
            short_label(event),
            color="white",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.2", "facecolor": color, "edgecolor": color, "alpha": 0.95},
        )

    for index, event in enumerate(MAJOR_EVENTS):
        if event["turn"] < min(x_values) or event["turn"] > max(x_values):
            continue

        plt.text(
            event["turn"],
            y_max + y_span * 0.30,
            event["label"],
            color="black",
            ha="center",
            va="bottom",
            fontsize=18,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.32",
                "facecolor": "orange",
                "edgecolor": "darkorange",
                "alpha": 0.95,
            },
        )

    if events or MAJOR_EVENTS:
        plt.ylim(y_min - y_span * 0.08, y_max + y_span * 0.34)

    plt.xlabel("policy archive number")
    plt.ylabel("average margin")
    plt.title("Pong policy archive performance")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_png, dpi=160)
    plt.show()
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Plot Pong policy archive performance from CSV.")
    parser.add_argument("--input-csv", default="results/policy_archive_eval.csv")
    parser.add_argument("--output-plot", default="results/policy_archive_performance.png")
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
