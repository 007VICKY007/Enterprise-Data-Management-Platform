"""
Enterprise Maturity Slide Visualization
Fixed: overlapping text, table alignment, consistent column widths,
       reduced whitespace, professional enterprise layout
"""

import numpy as np
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle, Rectangle

UNIQU_PURPLE = "#6A0DAD"
UNIQU_MAGENTA = "#FF00FF"
UNIQU_LIGHT_BG = "#F8F5FF"
UNIQU_TEXT = "#2E2E2E"
UNIQU_GREY = "#B0B0B0"


# ─────────────────────────────
# Helpers
# ─────────────────────────────
def safe_float(v):
    try:
        return float(v)
    except:
        return np.nan


def safe_rating(v):
    try:
        return int(round(float(v)))
    except:
        return 0


# ─────────────────────────────
# Maturity Wheel
# ─────────────────────────────
def _draw_maturity_wheel(ax, center=(0.18, 0.48), r_outer=0.18, r_inner=0.08):

    colors = ["#d9cff2", "#bda7ea", "#8f63d7", "#4a1f7a", "#1d0b3f"]

    n = 5
    ts, te = -90, 90
    step = (te - ts) / n

    for i in range(n):
        si = (n - 1) - i
        t1 = ts + si * step
        t2 = ts + (si + 1) * step

        ax.add_patch(Wedge(
            center, r_outer, t1, t2,
            width=(r_outer - r_inner),
            transform=ax.transAxes,
            facecolor=colors[i],
            edgecolor="white",
            linewidth=1.2
        ))

    ax.add_patch(Circle(
        center, r_inner - 0.005,
        transform=ax.transAxes,
        facecolor="#9a86c6",
        edgecolor="white"
    ))

    ax.text(
        center[0], center[1],
        "Data\nManagement\nMaturity Scale",
        transform=ax.transAxes,
        ha="center", va="center",
        fontsize=8,
        color="white",
        fontweight="bold"
    )


# ─────────────────────────────
# Domain Table — fixed alignment
# ─────────────────────────────
def _draw_domain_table(ax, scores):

    x, y, w, h = 0.50, 0.48, 0.42, 0.28

    ax.add_patch(Rectangle((x, y), w, h,
                           transform=ax.transAxes,
                           facecolor="white",
                           edgecolor=UNIQU_GREY,
                           linewidth=1.0))

    hh = 0.06
    ax.add_patch(Rectangle((x, y + h - hh), w, hh,
                           transform=ax.transAxes,
                           facecolor="#c07bb3"))

    ax.text(x + 0.02, y + h - hh / 2,
            "Data Management Framework Domains",
            fontsize=8,
            fontweight="bold",
            transform=ax.transAxes,
            va="center",
            color="white")

    # Score column header
    ax.text(x + w - 0.06, y + h - hh / 2,
            "Score",
            fontsize=7,
            fontweight="bold",
            transform=ax.transAxes,
            va="center",
            ha="center",
            color="white")

    rows = list(scores.keys())
    n_rows = max(len(rows), 1)
    row_h = (h - hh) / n_rows

    for i, r in enumerate(rows):
        val = scores[r]
        yy = y + h - hh - (i + 1) * row_h + row_h * 0.4

        # Alternating row background
        if i % 2 == 0:
            ax.add_patch(Rectangle(
                (x, y + h - hh - (i + 1) * row_h), w, row_h,
                transform=ax.transAxes,
                facecolor="#f5f0fc",
                edgecolor="none"))

        # Truncate long dimension names
        display_name = r if len(r) <= 28 else r[:26] + "…"
        ax.text(x + 0.02, yy, display_name,
                fontsize=8,
                transform=ax.transAxes,
                color=UNIQU_TEXT,
                va="center")

        ax.text(x + w - 0.06, yy, f"{val:.1f}",
                fontsize=9,
                fontweight="bold",
                transform=ax.transAxes,
                ha="center",
                va="center",
                color=UNIQU_PURPLE)


# ─────────────────────────────
# Donut — fixed positioning
# ─────────────────────────────
def _draw_donut(ax, center, value, label, color):

    r = 0.04

    ax.add_patch(Wedge(
        center, r, 0, 360,
        width=0.01,
        transform=ax.transAxes,
        facecolor="#efe9f7"
    ))

    frac = min(value / 5.0, 1.0)

    ax.add_patch(Wedge(
        center, r,
        90 - 360 * frac, 90,
        width=0.01,
        transform=ax.transAxes,
        facecolor=color
    ))

    ax.text(center[0], center[1],
            f"{value:.2f}",
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=10,
            fontweight="bold",
            color=color)

    ax.text(center[0], center[1] + 0.07,
            label,
            transform=ax.transAxes,
            ha="center",
            fontsize=7,
            fontweight="600",
            color=UNIQU_TEXT)


# ─────────────────────────────
# MAIN SLIDE — fixed layout
# ─────────────────────────────
def render_summary_slide_png(
    client_name,
    domain_scores,
    exec_score,
    benchmark,
    target
):

    fig = plt.figure(figsize=(13.6, 7.65), dpi=160)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    fig.patch.set_facecolor(UNIQU_LIGHT_BG)

    # Title — reduced top margin
    ax.text(0.05, 0.94,
            "Data Maturity Level",
            fontsize=20,
            fontweight="bold",
            color=UNIQU_PURPLE,
            transform=ax.transAxes)

    # Brand line
    ax.add_patch(Rectangle(
        (0.52, 0.94), 0.40, 0.006,
        transform=ax.transAxes,
        facecolor=UNIQU_PURPLE))

    ax.text(0.90, 0.96,
            "uniqus",
            fontsize=14,
            fontweight="bold",
            color=UNIQU_PURPLE,
            transform=ax.transAxes)

    # Client name subtitle
    ax.text(0.05, 0.90,
            f"Client: {client_name}",
            fontsize=11,
            color=UNIQU_TEXT,
            transform=ax.transAxes,
            fontstyle="italic")

    # Wheel
    _draw_maturity_wheel(ax)

    # Table
    _draw_domain_table(ax, domain_scores)

    # Donuts — properly spaced
    _draw_donut(ax, (0.58, 0.22), exec_score, client_name[:20], UNIQU_PURPLE)
    _draw_donut(ax, (0.72, 0.22), benchmark, "Benchmark", UNIQU_MAGENTA)
    _draw_donut(ax, (0.86, 0.22), target, "Target", "#a083c9")

    # Footer — clean
    ax.text(0.05, 0.04,
            f"Data Maturity Assessment Report for {client_name}",
            fontsize=9,
            transform=ax.transAxes,
            color=UNIQU_GREY)

    ax.text(0.95, 0.04,
            datetime.now().strftime("%d %b %Y"),
            fontsize=8,
            transform=ax.transAxes,
            ha="right",
            color=UNIQU_GREY)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches=None, pad_inches=0.0)
    plt.close(fig)

    return buf.getvalue()