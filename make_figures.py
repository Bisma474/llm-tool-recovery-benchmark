import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats
from scipy.stats import chi2_contingency


LOG_PATH = Path("G:/research/main_experiment_log.json")
OUT_DIR = Path("G:/research/figures_corrected")

OUT_DIR.mkdir(exist_ok=True)

with LOG_PATH.open("r", encoding="utf-8") as file:
    data = json.load(file)

df = pd.DataFrame(data)

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

tool_order = [
    "calculator",
    "document_search",
    "database_lookup",
    "file_reader",
    "data_analysis",
]

tool_labels = {
    "calculator": "Calculator",
    "document_search": "Document search",
    "database_lookup": "Database lookup",
    "file_reader": "File reader",
    "data_analysis": "Data analysis",
}

failure_order = [
    "invalid_parameter",
    "timeout",
    "unavailable_tool",
    "malformed_output",
    "misleading_output",
]

failure_labels = {
    "invalid_parameter": "Invalid parameter",
    "timeout": "Timeout",
    "unavailable_tool": "Unavailable tool",
    "malformed_output": "Malformed output",
    "misleading_output": "Misleading output",
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


def set_condition_ticks(ax):
    ax.set_xticks(range(len(condition_order)))
    ax.set_xticklabels(
        [condition_labels[c] for c in condition_order],
        rotation=12,
        ha="right",
    )


# ==========================================================
# FIGURE 1: Direct recovery score by condition
# ==========================================================

fig, ax = plt.subplots(figsize=(9, 6))

sns.barplot(
    data=df,
    x="condition",
    y="direct_recovery_score",
    order=condition_order,
    hue="condition",
    hue_order=condition_order,
    palette=palette,
    errorbar=("ci", 95),
    capsize=0.12,
    legend=False,
    ax=ax,
)

ax.set_xlabel("")
ax.set_ylabel("Mean direct recovery score (0–2)")
ax.set_title(
    "Structured provenance improves direct recovery",
    weight="bold",
)
ax.set_ylim(0, 2.15)

set_condition_ticks(ax)
add_bar_labels(ax, decimals=2)

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig1_direct_recovery_score_by_condition.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# FIGURE 2: Correct first-stage diagnosis by condition
# ==========================================================

diagnosis_summary = (
    df.groupby("condition", as_index=False)
    .agg(
        diagnosis_rate=(
            "diagnosis_success",
            "mean",
        )
    )
)

diagnosis_summary["diagnosis_rate"] *= 100

fig, ax = plt.subplots(figsize=(9, 6))

sns.barplot(
    data=diagnosis_summary,
    x="condition",
    y="diagnosis_rate",
    order=condition_order,
    hue="condition",
    hue_order=condition_order,
    palette=palette,
    legend=False,
    ax=ax,
)

ax.set_xlabel("")
ax.set_ylabel("Correct first-stage diagnosis (%)")
ax.set_title(
    "Structured provenance enables failure diagnosis",
    weight="bold",
)
ax.set_ylim(0, 100)

set_condition_ticks(ax)
add_bar_labels(ax, decimals=1, suffix="%")

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig2_first_stage_diagnosis_by_condition.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# FIGURE 3: Correct recovery action by condition
# ==========================================================

action_summary = (
    df.groupby("condition", as_index=False)
    .agg(
        action_rate=(
            "action_success",
            "mean",
        )
    )
)

action_summary["action_rate"] *= 100

fig, ax = plt.subplots(figsize=(9, 6))

sns.barplot(
    data=action_summary,
    x="condition",
    y="action_rate",
    order=condition_order,
    hue="condition",
    hue_order=condition_order,
    palette=palette,
    legend=False,
    ax=ax,
)

ax.set_xlabel("")
ax.set_ylabel("Correct recovery action (%)")
ax.set_title(
    "Structured provenance improves recovery actions",
    weight="bold",
)
ax.set_ylim(0, 100)

set_condition_ticks(ax)
add_bar_labels(ax, decimals=1, suffix="%")

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig3_correct_action_by_condition.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# FIGURE 4: Direct recovery score by tool
# ==========================================================

fig, ax = plt.subplots(figsize=(13, 7))

sns.barplot(
    data=df,
    x="tool_name",
    y="direct_recovery_score",
    hue="condition",
    order=tool_order,
    hue_order=condition_order,
    palette=palette,
    errorbar=("ci", 95),
    capsize=0.05,
    ax=ax,
)

ax.set_xlabel("Tool")
ax.set_ylabel("Mean direct recovery score (0–2)")
ax.set_title(
    "Structured provenance advantage across tools",
    weight="bold",
)
ax.set_ylim(0, 2.15)

ax.set_xticks(range(len(tool_order)))
ax.set_xticklabels(
    [tool_labels[t] for t in tool_order],
    rotation=12,
    ha="right",
)

handles, labels = ax.get_legend_handles_labels()

ax.legend(
    handles,
    [condition_labels[c] for c in condition_order],
    title="Condition",
    frameon=True,
    loc="upper left",
)

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig4_direct_recovery_by_tool.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# FIGURE 5: Direct recovery score by failure type
# ==========================================================

fig, ax = plt.subplots(figsize=(14, 7))

sns.barplot(
    data=df,
    x="failure_type",
    y="direct_recovery_score",
    hue="condition",
    order=failure_order,
    hue_order=condition_order,
    palette=palette,
    errorbar=("ci", 95),
    capsize=0.05,
    ax=ax,
)

ax.set_xlabel("Failure type")
ax.set_ylabel("Mean direct recovery score (0–2)")
ax.set_title(
    "Structured provenance advantage across failure types",
    weight="bold",
)
ax.set_ylim(0, 2.15)

ax.set_xticks(range(len(failure_order)))
ax.set_xticklabels(
    [failure_labels[f] for f in failure_order],
    rotation=12,
    ha="right",
)

handles, labels = ax.get_legend_handles_labels()

ax.legend(
    handles,
    [condition_labels[c] for c in condition_order],
    title="Condition",
    frameon=True,
    loc="upper left",
)

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig5_direct_recovery_by_failure_type.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# FIGURE 6: Quality-latency trade-off
# ==========================================================

latency_summary = (
    df.groupby("condition", as_index=False)
    .agg(
        mean_latency_s=(
            "latency_s",
            "mean",
        ),
        mean_direct_score=(
            "direct_recovery_score",
            "mean",
        ),
        diagnosis_rate=(
            "diagnosis_success",
            "mean",
        ),
    )
)

latency_summary["diagnosis_rate"] *= 100

fig, ax = plt.subplots(figsize=(9, 7))

for _, row in latency_summary.iterrows():
    condition = row["condition"]
    bubble_size = 250 + row["diagnosis_rate"] * 18

    ax.scatter(
        row["mean_latency_s"],
        row["mean_direct_score"],
        s=bubble_size,
        color=palette[condition],
        alpha=0.85,
        edgecolor="black",
        linewidth=0.8,
        zorder=3,
    )

    ax.annotate(
        condition_labels[condition],
        (
            row["mean_latency_s"],
            row["mean_direct_score"],
        ),
        xytext=(7, 7),
        textcoords="offset points",
        fontsize=10,
    )

ax.set_xlabel("Mean latency (seconds)")
ax.set_ylabel("Mean direct recovery score (0–2)")
ax.set_title(
    "Recovery quality versus latency",
    weight="bold",
)

ax.text(
    0.02,
    0.02,
    "Bubble size represents correct diagnosis rate",
    transform=ax.transAxes,
    fontsize=9,
    bbox={
        "facecolor": "white",
        "edgecolor": "#CCCCCC",
        "alpha": 0.9,
    },
)

fig.tight_layout()
fig.savefig(
    OUT_DIR / "fig6_latency_vs_direct_recovery.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)


# ==========================================================
# TABLE 1: Overall condition metrics
# ==========================================================

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
        sd_latency_seconds=(
            "latency_s",
            "std",
        ),
    )
)

summary["diagnosis_rate"] *= 100
summary["action_rate"] *= 100

summary["condition"] = pd.Categorical(
    summary["condition"],
    categories=condition_order,
    ordered=True,
)

summary = summary.sort_values("condition")

summary.to_csv(
    OUT_DIR / "table1_condition_summary.csv",
    index=False,
)


# ==========================================================
# TABLE 2: Tool and failure type breakdown
# ==========================================================

tool_breakdown = (
    df.groupby(
        ["tool_name", "condition"],
        as_index=False,
    )
    .agg(
        trials=("scenario_id", "count"),
        mean_direct_recovery_score=(
            "direct_recovery_score",
            "mean",
        ),
        diagnosis_rate=(
            "diagnosis_success",
            "mean",
        ),
        action_rate=(
            "action_success",
            "mean",
        ),
    )
)

tool_breakdown["diagnosis_rate"] *= 100
tool_breakdown["action_rate"] *= 100

tool_breakdown.to_csv(
    OUT_DIR / "table2_tool_breakdown.csv",
    index=False,
)

failure_breakdown = (
    df.groupby(
        ["failure_type", "condition"],
        as_index=False,
    )
    .agg(
        trials=("scenario_id", "count"),
        mean_direct_recovery_score=(
            "direct_recovery_score",
            "mean",
        ),
        diagnosis_rate=(
            "diagnosis_success",
            "mean",
        ),
        action_rate=(
            "action_success",
            "mean",
        ),
    )
)

failure_breakdown["diagnosis_rate"] *= 100
failure_breakdown["action_rate"] *= 100

failure_breakdown.to_csv(
    OUT_DIR / "table3_failure_type_breakdown.csv",
    index=False,
)


# ==========================================================
# STATISTICAL TESTS
# ==========================================================

structured_scores = df.loc[
    df["condition"] == "structured_provenance",
    "direct_recovery_score",
]

comparison_conditions = [
    "no_history",
    "raw_history",
    "plain_log",
]

print("\n" + "=" * 68)
print("CORRECTED STATISTICAL RESULTS")
print("=" * 68)

print("\nPrimary metric: direct recovery score (0–2)")
print(
    "Direct score = first-stage correct diagnosis "
    "+ first-stage correct action"
)

print("\nMann-Whitney U tests")
print(
    "Alternative hypothesis: structured provenance > comparison"
)

for comparison in comparison_conditions:
    comparison_scores = df.loc[
        df["condition"] == comparison,
        "direct_recovery_score",
    ]

    u_stat, p_value = stats.mannwhitneyu(
        structured_scores,
        comparison_scores,
        alternative="greater",
    )

    print(
        f"structured_provenance vs {comparison}: "
        f"U = {u_stat:.1f}, p = {p_value:.10f}"
    )

print("\nEffect sizes: Cliff's delta")

for comparison in comparison_conditions:
    comparison_scores = df.loc[
        df["condition"] == comparison,
        "direct_recovery_score",
    ]

    greater = 0
    lower = 0

    for structured_value in structured_scores:
        greater += np.sum(
            structured_value > comparison_scores
        )
        lower += np.sum(
            structured_value < comparison_scores
        )

    cliff_delta = (
        greater - lower
    ) / (
        len(structured_scores)
        * len(comparison_scores)
    )

    print(
        f"structured_provenance vs {comparison}: "
        f"Cliff's delta = {cliff_delta:.3f}"
    )

print("\nCorrect diagnosis: chi-square test")
print(
    "Structured provenance versus all non-structured conditions"
)

diagnosis_table = pd.crosstab(
    df["condition"] == "structured_provenance",
    df["diagnosis_success"],
)

chi2, p_value, dof, expected = chi2_contingency(
    diagnosis_table
)

print(f"Chi-square = {chi2:.3f}")
print(f"p-value = {p_value:.12f}")
print(f"Degrees of freedom = {dof}")

print("\nCorrect recovery action: chi-square test")
print(
    "Structured provenance versus all non-structured conditions"
)

action_table = pd.crosstab(
    df["condition"] == "structured_provenance",
    df["action_success"],
)

chi2_action, p_action, dof_action, expected_action = (
    chi2_contingency(action_table)
)

print(f"Chi-square = {chi2_action:.3f}")
print(f"p-value = {p_action:.12f}")
print(f"Degrees of freedom = {dof_action}")

print("\nCondition summary:")
print(
    summary.round(
        {
            "mean_direct_recovery_score": 3,
            "sd_direct_recovery_score": 3,
            "diagnosis_rate": 1,
            "action_rate": 1,
            "mean_latency_seconds": 2,
            "sd_latency_seconds": 2,
        }
    ).to_string(index=False)
)

print("\nSaved figures and tables:")
print(OUT_DIR / "fig1_direct_recovery_score_by_condition.png")
print(OUT_DIR / "fig2_first_stage_diagnosis_by_condition.png")
print(OUT_DIR / "fig3_correct_action_by_condition.png")
print(OUT_DIR / "fig4_direct_recovery_by_tool.png")
print(OUT_DIR / "fig5_direct_recovery_by_failure_type.png")
print(OUT_DIR / "fig6_latency_vs_direct_recovery.png")
print(OUT_DIR / "table1_condition_summary.csv")
print(OUT_DIR / "table2_tool_breakdown.csv")
print(OUT_DIR / "table3_failure_type_breakdown.csv")