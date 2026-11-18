from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Wedge

OUT = Path(__file__).resolve().parents[1] / "assets"
OUT.mkdir(exist_ok=True)

TEAL, TEAL_LIGHT, BLUE, INK = "#0f766e", "#99f6e4", "#1d4ed8", "#0f172a"
GREEN, AMBER, ROSE, SKY, LIGHT = "#22c55e", "#f59e0b", "#e11d48", "#38bdf8", "#ecfeff"


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=140)
    fig.patch.set_facecolor(LIGHT)
    ax.set_axis_off()
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / name, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def hero():
    fig, ax = canvas(6, 4.5)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.5)
    ax.add_patch(Circle((5, 4.0), 2.9, color=TEAL_LIGHT))
    ax.add_patch(Circle((5, 4.0), 2.2, color=TEAL))
    ax.add_patch(Polygon([(5, 6.25), (4.05, 4.35), (5.95, 4.35)], closed=True, color="white"))
    ax.add_patch(Circle((5, 3.9), 0.98, color="white"))
    x = np.linspace(0.6, 9.4, 200)
    ax.plot(x, 1.0 + 0.35 * np.sin(x * 1.3) + 0.15 * x / 9.4, color=BLUE, lw=3, alpha=0.85)
    ax.text(5, 0.25, "Know your numbers", ha="center", color=INK, fontsize=14, weight="bold")
    save(fig, "hero.png")


def healthy_plate():
    fig, ax = canvas(5, 5)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal")
    ax.add_patch(Wedge((0, 0), 1.0, 0, 180, color=GREEN, ec="white", lw=3))
    ax.add_patch(Wedge((0, 0), 1.0, 180, 270, color=ROSE, ec="white", lw=3))
    ax.add_patch(Wedge((0, 0), 1.0, 270, 360, color=AMBER, ec="white", lw=3))
    ax.text(0, 0.5, "Vegetables\nand salad", ha="center", va="center", color="white", weight="bold")
    ax.text(-0.5, -0.5, "Protein", ha="center", va="center", color="white", weight="bold")
    ax.text(0.5, -0.5, "Whole\ngrains", ha="center", va="center", color=INK, weight="bold")
    ax.text(0, -1.2, "Half your plate: vegetables. Add water, not sugary drinks.",
            ha="center", color=INK, fontsize=9)
    save(fig, "healthy_plate.png")


def warning_signs():
    items = ["Very thirsty", "Urinating often", "Constant tiredness",
             "Blurred vision", "Slow-healing\nsores", "Unplanned\nweight loss"]
    fig, ax = canvas(7, 4.2)
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 2)
    for i, label in enumerate(items):
        col, row = i % 3, 1 - i // 3
        ax.add_patch(FancyBboxPatch((col + 0.08, row + 0.08), 0.84, 0.84,
                                    boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc="white", ec=TEAL, lw=2))
        ax.text(col + 0.5, row + 0.5, label, ha="center", va="center", color=INK,
                fontsize=11, weight="bold", wrap=True)
    ax.set_title("Possible warning signs: see a clinician if you notice these",
                 color=INK, fontsize=11)
    save(fig, "warning_signs.png")


def activity():
    fig, ax = canvas(6, 3.6)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ax.set_xlim(-0.5, 6.5)
    ax.set_ylim(0, 40)
    ax.bar(range(7), [21.4] * 7, color=[TEAL] * 7, width=0.6)
    for i, d in enumerate(days):
        ax.text(i, -3.2, d, ha="center", color=INK, fontsize=9)
    ax.axhline(21.4, color=AMBER, ls="--", lw=1)
    ax.text(6.4, 23, "about 21 min/day", ha="right", color=AMBER, fontsize=9)
    ax.set_title("150 minutes of moderate activity a week, for example brisk walking",
                 color=INK, fontsize=10)
    ax.set_ylabel("Minutes", color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "activity.png")


def bmi_scale():
    fig, ax = canvas(7, 2.4)
    bands = [(10, 18.5, SKY, "Under"), (18.5, 25, GREEN, "Healthy"),
             (25, 30, AMBER, "Overweight"), (30, 40, ROSE, "Obesity range")]
    for lo, hi, c, label in bands:
        ax.barh(0, hi - lo, left=lo, color=c, height=0.5)
        ax.text((lo + hi) / 2, 0.45, label, ha="center", va="bottom", color=INK, fontsize=9,
                weight="bold")
    ax.set_xlim(10, 40)
    ax.set_ylim(-0.6, 1.1)
    ax.set_xticks([18.5, 25, 30])
    ax.set_yticks([])
    ax.set_xlabel("BMI (kg/m²). Adult WHO categories; a clinician interprets results.",
                  color=INK, fontsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    save(fig, "bmi_scale.png")


if __name__ == "__main__":
    hero()
    healthy_plate()
    warning_signs()
    activity()
    bmi_scale()
    print("assets:", sorted(p.name for p in OUT.glob("*.png")))
