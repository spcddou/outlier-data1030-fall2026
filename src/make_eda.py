"""Export three exploratory figures and their data; captions belong to the team."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bls_pipeline import ROOT, TARGET, write_json


def make_figures(root=ROOT):
    root = Path(root)
    panel = pd.read_csv(root / "data/processed/state_month_panel.csv")
    panel = panel[panel.month >= "2015-01"].copy()
    model = pd.read_csv(root / "data/processed/model_table.csv")
    figures = root / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": "#25313d", "text.color": "#25313d"})
    dates = pd.to_datetime(panel.month)
    trend = panel.pivot(index="month", columns="state", values="unemployment_rate")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for state in trend:
        ax.plot(pd.to_datetime(trend.index), trend[state], color="#b4bcc4", alpha=.35, linewidth=.7)
    ax.plot(pd.to_datetime(trend.index), trend.mean(axis=1), color="#28608c", linewidth=2.3,
            label="Equal-state mean (not the national rate)")
    ax.set(title="State unemployment rates: 2015–2024", xlabel="Reference month",
           ylabel="Seasonally adjusted unemployment rate (%)", ylim=(0, None))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(dates.min(), dates.max())
    ax.legend(loc="upper right", frameon=False)
    ax.grid(axis="y", color="#e6e8eb", linewidth=.6)
    fig.tight_layout(); fig.savefig(figures / "01_unemployment_trends.png", dpi=180); plt.close(fig)
    trend.to_csv(figures / "01_unemployment_trends_data.csv")

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(model.unemployment_rate, model[TARGET], s=9, alpha=.18, color="#28608c", linewidths=0)
    high = float(max(model.unemployment_rate.max(), model[TARGET].max())) + .5
    ax.plot([0, high], [0, high], "--", color="#4f5660", linewidth=1.3, label="Persistence: future = current")
    ax.set(title="Current vs three-month-ahead unemployment", xlabel="Current unemployment rate (%)",
           ylabel="Unemployment rate three months later (%)", xlim=(0, high), ylim=(0, high))
    ax.set_aspect("equal", adjustable="box")
    ax.legend(frameon=False, loc="upper left")
    ax.text(.97, .03, f"{len(model):,} state-month pairs", transform=ax.transAxes, ha="right")
    fig.tight_layout(); fig.savefig(figures / "02_current_vs_future.png", dpi=180); plt.close(fig)
    model[["state", "month", "target_month", "unemployment_rate", TARGET]].to_csv(figures / "02_current_vs_future_data.csv", index=False)

    change = model[TARGET] - model.unemployment_rate
    bins = np.linspace(float(change.min()) - .1, float(change.max()) + .1, 41)
    pandemic = model.month.between("2020-01", "2021-12")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharex=True, sharey=True)
    for ax, mask, name, color in [(axes[0], ~pandemic, "Origins outside 2020–2021", "#28608c"),
                                  (axes[1], pandemic, "Origins in 2020–2021", "#c08434")]:
        ax.hist(change[mask], bins=bins, weights=np.full(mask.sum(), 100 / mask.sum()),
                color=color, rwidth=.97)
        ax.axvline(0, color="#4f5660", linestyle="--", linewidth=1)
        ax.set(title=f"{name}\nn = {mask.sum():,}", xlabel="Three-month change (percentage points)")
        ax.grid(axis="y", color="#e6e8eb", linewidth=.6)
    axes[0].set_ylabel("Share of each origin-period group (%)")
    fig.suptitle("Three-month unemployment changes across periods", y=1.01)
    fig.tight_layout(); fig.savefig(figures / "03_three_month_changes.png", dpi=180, bbox_inches="tight"); plt.close(fig)
    change_data = model[["state", "month", "target_month"]].copy()
    change_data["change_percentage_points"] = change
    change_data["origin_in_2020_2021"] = pandemic
    change_data.to_csv(figures / "03_three_month_changes_data.csv", index=False)
    summary = {"rows": len(model), "unemployment_rate_range_percent": [float(panel.unemployment_rate.min()), float(panel.unemployment_rate.max())],
               "three_month_change_range_percentage_points": [float(change.min()), float(change.max())],
               "notes": ["Exploratory EDA includes all labeled periods, including the eventual test period; "
                         "the test period is not pristine for later adaptive research.",
                         "State lines use common axes. Equal-state mean is not a labor-force-weighted national estimate.",
                         "Period grouping uses forecast origin month, not target month; no causal interpretation."]}
    write_json(root / "results/eda_summary.json", summary)
    print(f"Saved three exploratory figures and their source tables to {figures.relative_to(root)}", flush=True)
    return summary


if __name__ == "__main__":
    make_figures()
