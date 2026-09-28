import json
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats
from scipy.stats import chi2_contingency


EXP1_PATH = Path(
    "G:/research/main_experiment_log.json"
)

EXP2_PATH = Path(
    "G:/research/main_blinded_experiment_log.json"
)

OUT_DIR = Path(
    "G:/research/blinded_analysis"
)

OUT_DIR.mkdir(exist_ok=True)


def load_exp1_as_corrected(log_path):
    with log_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    df = pd.DataFrame(data)

    df["diagnosis_success"] = (
        df["diagnosis_correct"]
        .fillna(False)
        .astype(int)
    )

    df["action_success"] = (
        df["action_valid"]
        .fillna(False)
        .astype(int)
    )

    df["direct_recovery_score"] = (
        df["diagnosis_success"]
        + df["action_success"]
    )

    df["latency_s"] = df["latency_ms"] / 1000.0

    return df


def load_exp2(log_path):
    with log_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    df = pd.DataFrame(data)

    df["diagnosis_success"] = (
        df["diagnosis_correct"]
        .fillna(False)
        .astype(int)
    )

    df["action_success"] = (
        df["action_valid"]
        .fillna(False)
        .astype(int)
    )

    df["direct_recovery_score"] = (
        df["diagnosis_success"]
        + df["action_success"]
    )

    df["latency_s"] = df["latency_ms"] / 1000.0

    return df


df1 = load_exp1_as_corrected(EXP1_PATH)
df2 = load_exp2(EXP2_PATH)

condition_order = [
    "no_history",
    "raw_history",
    "plain_log",
    "structured_provenance",
]

condition_labels = {
    "no_history": "No history",
    "raw_history": "Raw history",
    "plain_log": "Plain log",
    "structured_provenance": "Structured provenance",
}

palette = {
    "no_history": "#8C8C8C",
    "raw_history": "#4C78A8",
    "plain_log": "#F58518",
    "structured_provenance": "#54A24B",
}

sns.set_theme(
    style="whitegrid",
    context="paper",
    font_scale=1.25,
)


def set_condition_ticks(ax):
    ax.set_xticks(range(len(condition_order)))
    ax.set_xticklabels(
        [condition_labels[c] for c in condition_order],
        rotation=12,
        ha="right",
    )


def add_bar_labels(ax, decimals=1, suffix=""):
    for container in ax.containers:
        values = container.datavalues
        labels = []

        for value in values:
            if np.isnan(value):
                labels.append("")
            else:
                labels.append(
                    f"{value:.{decimals}f}{suffix}"
                )

        ax.bar_label(
            container,
            labels=labels,
            padding=3,
            fontsize=9,
        )


# ==========================================================
# TABLE: Summary by experiment and condition
# ==========================================================

def summarize(df, exp_name):
    summary = (
        df.groupby("condition", as_index=False)
        .agg(
            trials=("scenario_id", "count"),
            mean_direct_recovery_score=(
                "direct_recovery_score",
                "mean",
            ),
            sd_direct_recovery_score=(
                "direct_recovery_score",
                "std",
            ),
            diagnosis_rate=(
                "diagnosis_success",
                "mean",
            ),
            action_rate=(
                "action_success",
                "mean",
            ),
            mean_latency_seconds=(
                "latency_s",
                "mean",
            ),
        )
    )

    summary["experiment"] = exp_name
    summary["diagnosis_rate"] *= 100
    summary["action_rate"] *= 100

    summary["condition"] = pd.Categorical(
        summary["condition"],
        categories=condition_order,
        ordered=True,
    )

    return summary.sort_values("condition")


summary1 = summarize(df1, "Exp1_full_provenance")
summary2 = summarize(df2, "Exp2_blinded")

combined_summary = pd.concat(
    [summary1, summary2],
    ignore_index=True,
)

combined_summary.to_csv(
    OUT_DIR / "table1_combined_summary.csv",
    index=False,
)


# ==========================================================
# FIGURE 1: Direct recovery score by experiment
# ==========================================================

fig, ax = plt.subplots(figsize=(11, 7))

sns.barplot(
    data=combined_summary,
    x="condition",
    y="mean_direct_recovery_score",
    hue="experiment",
    hue_order=["Exp1_full_provenance", "Exp2_blinded"],
    palette={"Exp1_full_provenance": "#1f77b4", "Exp2_blinded": "#ff7f0e"},
    errorbar=None,
    ax=ax,
)

ax.set_xlabel("")
ax.set_ylabel("Mean direct recovery score (0–2)")
ax.set_title(
    "Experiment 1 (full provenance) vs. Experiment 2 (blinded)",
    weight="bold",
)
ax.set_ylim(0, 2.15)

set_condition_ticks(ax)

handles, labels = ax.get_legend_handles_labels()

ax.legend(
    handles,
    ["Experiment 1: full provenance", "Experiment 2: blinded"],
    title="Experiment",
    frameon=True,
)

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig1_exp1_vs_exp2_direct_score.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# FIGURE 2: Diagnosis success by experiment
# ==========================================================

fig, ax = plt.subplots(figsize=(11, 7))

sns.barplot(
    data=combined_summary,
    x="condition",
    y="diagnosis_rate",
    hue="experiment",
    hue_order=["Exp1_full_provenance", "Exp2_blinded"],
    palette={"Exp1_full_provenance": "#1f77b4", "Exp2_blinded": "#ff7f0e"},
    errorbar=None,
    ax=ax,
)

ax.set_xlabel("")
ax.set_ylabel("Correct diagnosis rate (%)")
ax.set_title(
    "Failure diagnosis: full vs. blinded",
    weight="bold",
)
ax.set_ylim(0, 100)

set_condition_ticks(ax)

handles, labels = ax.get_legend_handles_labels()

ax.legend(
    handles,
    ["Experiment 1: full provenance", "Experiment 2: blinded"],
    title="Experiment",
    frameon=True,
)

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig2_exp1_vs_exp2_diagnosis.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# FIGURE 3: Action success by experiment
# ==========================================================

fig, ax = plt.subplots(figsize=(11, 7))

sns.barplot(
    data=combined_summary,
    x="condition",
    y="action_rate",
    hue="experiment",
    hue_order=["Exp1_full_provenance", "Exp2_blinded"],
    palette={"Exp1_full_provenance": "#1f77b4", "Exp2_blinded": "#ff7f0e"},
    errorbar=None,
    ax=ax,
)

ax.set_xlabel("")
ax.set_ylabel("Correct action rate (%)")
ax.set_title(
    "Exact tool + arguments recovery: full vs. blinded",
    weight="bold",
)
ax.set_ylim(0, 100)

set_condition_ticks(ax)

handles, labels = ax.get_legend_handles_labels()

ax.legend(
    handles,
    ["Experiment 1: full provenance", "Experiment 2: blinded"],
    title="Experiment",
    frameon=True,
)

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig3_exp1_vs_exp2_action.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# STATISTICAL COMPARISON
# ==========================================================

print("\n" + "=" * 68)
print("EXPERIMENT 1 vs. EXPERIMENT 2 COMPARISON")
print("=" * 68)

print("\nPrimary metric: direct recovery score (0–2)")

for condition in condition_order:
    exp1_scores = df1.loc[
        df1["condition"] == condition,
        "direct_recovery_score",
    ]

    exp2_scores = df2.loc[
        df2["condition"] == condition,
        "direct_recovery_score",
    ]

    u_stat, p_value = stats.mannwhitneyu(
        exp1_scores,
        exp2_scores,
        alternative="two-sided",
    )

    print(
        f"{condition}: "
        f"Exp1 mean={exp1_scores.mean():.3f}, "
        f"Exp2 mean={exp2_scores.mean():.3f}, "
        f"U={u_stat:.1f}, p={p_value:.6f}"
    )

print("\nDiagnosis success: chi-square by condition")

for condition in condition_order:
    tab = pd.crosstab(
        df1.loc[df1["condition"] == condition, "experiment"].map(
            lambda x: "Exp1"
        ),
        df1.loc[df1["condition"] == condition, "diagnosis_success"],
    )

    tab2 = pd.crosstab(
        df2.loc[df2["condition"] == condition, "experiment"].map(
            lambda x: "Exp2"
        ),
        df2.loc[df2["condition"] == condition, "diagnosis_success"],
    )

    combined = pd.concat([tab, tab2], axis=0, ignore_index=True)

    if combined.shape == (2, 2):
        chi2, p_val, dof, _ = chi2_contingency(combined)
        print(
            f"{condition}: χ²={chi2:.2f}, p={p_val:.6f}"
        )
    else:
        print(f"{condition}: table not 2x2, skipped")

print("\nSaved files:")
print(OUT_DIR / "table1_combined_summary.csv")
print(OUT_DIR / "fig1_exp1_vs_exp2_direct_score.png")
print(OUT_DIR / "fig2_exp1_vs_exp2_diagnosis.png")
print(OUT_DIR / "fig3_exp1_vs_exp2_action.png")