"""
DataMaturity/visualizations.py
================================
Enhancement 3: "Uniqus" text top-right (capital U, purple #5b2d90, size 15)
Enhancement 4: Maturity scale colors on bar charts (1=grey,2=orange,3=blue,4=purple,5=teal)
Enhancement 1: Aptos font applied to all matplotlib text
"""

import numpy as np
from io import BytesIO
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Wedge, Circle, Rectangle

from DataMaturity.config import (
    UNIQU_PURPLE, UNIQU_MAGENTA, UNIQU_LIGHT_BG, UNIQU_TEXT, UNIQU_GREY,
)
from DataMaturity.helpers import safe_float, safe_rating

# ── Enhancement 1: Aptos font setup ──────────────────────────────────────────
# Try Aptos first, fall back gracefully through the stack
_FONT_STACK = ["Aptos", "Segoe UI", "Arial", "DejaVu Sans", "sans-serif"]

def _best_font() -> str:
    """Return the first font from the stack that matplotlib can find."""
    available = {f.name for f in fm.fontManager.ttflist}
    for font in _FONT_STACK:
        if font in available:
            return font
    return "DejaVu Sans"

_FONT_NAME = _best_font()

def _set_global_font():
    """Apply best available font globally in matplotlib."""
    plt.rcParams.update({
        "font.family":     _FONT_NAME,
        "font.size":       10,
        "axes.titleweight": "bold",
    })

# Enhancement 4: Maturity scale color map
_MATURITY_BAR_COLORS = {
    1: "#64748b",   # Adhoc       → slate grey
    2: "#b45309",   # Repeatable  → orange
    3: "#1d4ed8",   # Defined     → blue
    4: "#5b2d90",   # Managed     → purple
    5: "#0f766e",   # Optimised   → teal
}

def _maturity_bar_color(score: float) -> str:
    """Return the maturity color for a score in [1, 5]."""
    level = max(1, min(5, int(round(score))))
    return _MATURITY_BAR_COLORS.get(level, "#5b2d90")


# ── Internal: Maturity Wheel ──────────────────────────────────────────────────
def _draw_maturity_wheel(ax) -> None:
    cx, cy   = 0.09, 0.42
    ro, ri   = 0.150, 0.067
    magenta  = "#b0127b"
    seg_col  = ["#d9cff2", "#bda7ea", "#8f63d7", "#4a1f7a", "#1d0b3f"]

    n  = 5
    ts = -90.0
    te = +90.0
    step = (te - ts) / n

    for i in range(n):
        si = (n - 1) - i
        t1 = ts + si * step
        t2 = ts + (si + 1) * step
        ax.add_patch(Wedge(
            (cx, cy), ro, t1, t2,
            width=(ro - ri), transform=ax.transAxes,
            facecolor=seg_col[i], edgecolor="white", linewidth=1.2, zorder=3,
        ))

    ax.add_patch(Circle(
        (cx, cy), ri - 0.005, transform=ax.transAxes,
        facecolor="#9a86c6", edgecolor="white", linewidth=1.2, zorder=4,
    ))
    ax.text(cx, cy, "Data\nManagement\nMaturity Scale",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=8.2, color="white", fontweight="bold",
            fontfamily=_FONT_NAME, linespacing=1.15, zorder=5)

    for i in range(n):
        si  = (n - 1) - i
        mid = ts + (si + 0.5) * step
        rad = np.deg2rad(mid)
        rm  = (ro + ri) / 2
        ax.text(
            cx + rm * np.cos(rad), cy + rm * np.sin(rad),
            f"{i + 1:02d}", transform=ax.transAxes,
            ha="center", va="center", fontsize=14,
            fontfamily=_FONT_NAME,
            color="white" if i >= 3 else "#6d6d6d", zorder=6,
        )

    callouts = [
        ("Initial/Ad Hoc",
         "Processes are unstructured, reactive,\nand vary widely across the organization",
         0.74, 0),
        ("Repeatable",
         "Some processes are defined, but they are\ninconsistent and may lack formal documentation",
         0.60, 1),
        ("Defined",
         "Processes are standardized, documented,\nand consistently followed",
         0.44, 2),
        ("Managed",
         "Processes are monitored and measured. Data governance\nroles are formalized, and there's accountability",
         0.28, 3),
        ("Optimized",
         "Continuous improvement practices are in place, with proactive data\nquality, security, and governance strategies",
         0.11, 4),
    ]

    x_bus_base = cx + ro + 0.030
    x_dot = 0.310
    x_txt = 0.320

    for title, desc, y_t, idx in callouts:
        si  = (n - 1) - idx
        mid = ts + (si + 0.5) * step
        rad = np.deg2rad(mid)
        x0  = cx + ro * np.cos(rad)
        y0  = cy + ro * np.sin(rad)
        x_bus = x_bus_base + idx * 0.008

        ax.plot([x0, x_bus], [y0, y0],   transform=ax.transAxes, color=magenta, lw=1.2, zorder=2)
        ax.plot([x_bus, x_bus], [y0, y_t], transform=ax.transAxes, color=magenta, lw=1.2, zorder=2)
        ax.plot([x_bus, x_dot], [y_t, y_t], transform=ax.transAxes, color=magenta, lw=1.2, zorder=2)
        ax.scatter([x_dot], [y_t], transform=ax.transAxes, s=18, color="white", edgecolor=magenta, linewidth=1.2, zorder=3)

        ax.text(x_txt, y_t + 0.012, title,
                transform=ax.transAxes, ha="left", va="bottom",
                fontsize=8.2, fontweight="bold", fontfamily=_FONT_NAME, color=UNIQU_TEXT, zorder=3)
        ax.text(x_txt, y_t - 0.006, desc,
                transform=ax.transAxes, ha="left", va="top",
                fontsize=7.6, fontfamily=_FONT_NAME, color="#444444", linespacing=1.15, zorder=3)


# ── Internal: Domain Score Table ──────────────────────────────────────────────
def _draw_domain_table(ax, domain_scores: dict) -> None:
    """Right-panel table with Enhancement 4: maturity-scale colored mini bars."""
    x, y, w, h = 0.48, 0.50, 0.49, 0.27

    ax.add_patch(Rectangle((x, y), w, h, transform=ax.transAxes,
                            facecolor="white", edgecolor=UNIQU_GREY, linewidth=1))

    hh = 0.07
    ax.add_patch(Rectangle((x, y + h - hh), w, hh, transform=ax.transAxes,
                            facecolor="#c07bb3", edgecolor="none", alpha=0.95))
    ax.text(x + 0.018, y + h - hh / 2,
            "Data Management Framework\nDomains",
            transform=ax.transAxes, fontsize=9,
            fontfamily=_FONT_NAME, color="black", fontweight="bold", va="center")
    ax.text(x + 0.285, y + h - hh / 2, "DAMA Maturity Level",
            transform=ax.transAxes, fontsize=9,
            fontfamily=_FONT_NAME, color="black", fontweight="bold", va="center")

    rows   = list(domain_scores.keys())
    avail  = h - hh - 0.016
    row_h  = avail / max(len(rows), 1)
    y_top  = y + h - hh - 0.008

    for i, rname in enumerate(rows):
        v   = domain_scores[rname]
        rt  = y_top - i * row_h
        rm  = rt - row_h / 2

        ax.plot([x, x + w], [rt, rt], transform=ax.transAxes, color=UNIQU_GREY, lw=1)

        ax.text(x + 0.018, rm, rname,
                transform=ax.transAxes, fontsize=8.6,
                fontfamily=_FONT_NAME, color=UNIQU_TEXT, va="center", linespacing=1.1)

        vv   = safe_float(v)
        vtxt = "N/A" if not np.isfinite(vv) else f"{vv:.1f}"
        ax.text(x + 0.245, rm, vtxt,
                transform=ax.transAxes, fontsize=8.8,
                fontfamily=_FONT_NAME, color=UNIQU_TEXT, va="center")

        # Enhancement 4: maturity-scale colored mini bars
        bx, bw  = x + 0.298, 0.175
        bh      = min(0.030, row_h * 0.45)
        by      = rm - bh / 2
        gap     = 0.005
        nb      = 5
        bkw     = (bw - gap * (nb - 1)) / nb

        # Empty bars (background)
        for b in range(nb):
            ax.add_patch(Rectangle(
                (bx + b * (bkw + gap), by), bkw, bh,
                transform=ax.transAxes, facecolor="#e9e2f4", edgecolor="none"))

        # Filled bars with maturity scale colors (Enhancement 4)
        filled_levels = safe_rating(v)
        for b in range(filled_levels):
            bar_level = b + 1  # levels 1..5
            bar_color = _MATURITY_BAR_COLORS.get(bar_level, "#5b2d90")
            ax.add_patch(Rectangle(
                (bx + b * (bkw + gap), by), bkw, bh,
                transform=ax.transAxes, facecolor=bar_color, edgecolor="none"))

        # Position marker
        if np.isfinite(vv):
            mx = bx + float(np.clip((vv - 1) / 4, 0.0, 1.0)) * bw
            ax.plot([mx, mx], [by - 0.01, by + bh + 0.01],
                    transform=ax.transAxes, color="#2a2a2a", lw=1)

    ax.plot([x, x + w], [y, y], transform=ax.transAxes, color=UNIQU_GREY, lw=1)


# ── Internal: Donut Score Indicator ──────────────────────────────────────────
def _draw_donut(ax, center: tuple, value: float, label: str, color: str) -> None:
    r, t = 0.04, 0.01
    ax.add_patch(Wedge(center, r, 0, 360, width=t,
                       transform=ax.transAxes,
                       facecolor="#efe9f7", edgecolor="none"))
    frac = float(np.clip(value / 5.0, 0, 1))
    ax.add_patch(Wedge(center, r, 90 - 360 * frac, 90, width=t,
                       transform=ax.transAxes,
                       facecolor=color, edgecolor="none"))
    ax.text(center[0], center[1], f"{value:.2f}",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=11, fontweight="bold", fontfamily=_FONT_NAME, color=UNIQU_TEXT)
    ax.text(center[0], center[1] + 0.085, label,
            transform=ax.transAxes, ha="center", va="center",
            fontsize=8.5, fontfamily=_FONT_NAME, color=UNIQU_TEXT, fontweight="bold")


# ── Public: Render full summary slide → PNG bytes ─────────────────────────────
def render_slide_png(
    client_name:   str,
    domain_scores: dict,
    exec_score:    float,
    benchmark:     float,
    target:        float,
) -> bytes:
    _set_global_font()

    fig = plt.figure(figsize=(20, 11.25), dpi=150)
    fig.subplots_adjust(0, 0, 1, 1)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    fig.patch.set_facecolor(UNIQU_LIGHT_BG)

    # ── Title & subtitle ──────────────────────────────────────────────────
    ax.text(0.05, 0.92, "Data Maturity Level",
            transform=ax.transAxes, fontsize=20,
            fontweight="bold", fontfamily=_FONT_NAME, color=UNIQU_PURPLE)
    ax.text(
        0.05, 0.875,
        "Maturity level assesses an organization's data management capabilities "
        "across the key domains. This report summarizes the current maturity "
        "assessment aligned to DAMA principles.",
        transform=ax.transAxes, fontsize=9, fontfamily=_FONT_NAME, color="#444444",
    )

    # ── Brand accent lines ────────────────────────────────────────────────
    ax.add_patch(Rectangle((0.44, 0.920), 0.51, 0.008,
                            transform=ax.transAxes,
                            facecolor=UNIQU_PURPLE, edgecolor="none"))
    ax.add_patch(Rectangle((0.44, 0.912), 0.51, 0.004,
                            transform=ax.transAxes,
                            facecolor=UNIQU_MAGENTA, edgecolor="none"))

    # Enhancement 3: "Uniqus" top-right, capital U, purple, font ~15
    ax.text(0.975, 0.945, "Uniqus",
            transform=ax.transAxes,
            ha="right", va="center",
            fontsize=15, fontweight="bold",
            fontfamily=_FONT_NAME,
            color=UNIQU_PURPLE,
            zorder=10)

    # ── Maturity wheel ────────────────────────────────────────────────────
    _draw_maturity_wheel(ax)

    # ── Domain scores table ───────────────────────────────────────────────
    _draw_domain_table(ax, domain_scores)

    # ── Bottom donuts ─────────────────────────────────────────────────────
    client_label = client_name.strip() if client_name.strip() else "Client Score"
    _draw_donut(ax, (0.60, 0.24), exec_score,  client_label,          UNIQU_PURPLE)
    _draw_donut(ax, (0.76, 0.24), benchmark,   "Industry\nBenchmark", UNIQU_MAGENTA)
    _draw_donut(ax, (0.92, 0.24), target,       "Target",              "#a083c9")

    # ── Footer ────────────────────────────────────────────────────────────
    cn = client_name.strip() or "Client"
    ax.text(0.05, 0.04, f"Data Maturity Assessment Report for {cn}",
            transform=ax.transAxes, fontsize=10,
            fontfamily=_FONT_NAME, color="#555555", fontweight="bold")
    ax.text(0.05, 0.02,
            f"Generated on: {datetime.now().strftime('%d %b %Y, %H:%M')}",
            transform=ax.transAxes, fontsize=8.5,
            fontfamily=_FONT_NAME, color="#666666")

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches=None, pad_inches=0.0)
    plt.close(fig)
    return buf.getvalue()