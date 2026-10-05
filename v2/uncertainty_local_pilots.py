"""Compute uncertainty and paired scenario-level contrasts for local pilots."""
import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path


CONDITIONS = ("A", "B", "C", "D")
CONTRASTS = {
    "schema_minus_json": (("C", "D"), ("A", "B")),
    "structured_minus_plain": (("B", "D"), ("A", "C")),
    "interaction": (("D", "C"), ("B", "A")),
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"Expected boolean value, got {value!r}")


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def wilson(successes, total, z=1.959963984540054):
    if not total:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return 100 * max(0.0, center - margin), 100 * min(1.0, center + margin)


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return 0.0
    position = (len(values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def bootstrap_ci(cluster_values, seed=20261005, iterations=10000):
    rng = random.Random(seed)
    if not cluster_values:
        return 0.0, 0.0
    estimates = []
    for _ in range(iterations):
        sample = [rng.choice(cluster_values) for _ in cluster_values]
        estimates.append(100 * sum(sample) / len(sample))
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def load_runs(run_dirs):
    runs = []
    for run_dir in run_dirs:
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("status") != "COMPLETED":
            raise SystemExit(f"Run is not completed: {run_dir}")
        rows = read_csv(run_dir / "analysis_episodes.csv")
        if len(rows) != 100:
            raise SystemExit(f"Expected 100 analyzed episodes in {run_dir}, found {len(rows)}")
        runs.append({
            "run_id": run_dir.name,
            "model": manifest.get("model", "unknown"),
            "seed": int(manifest.get("generation_seed", manifest.get("options", {}).get("seed", -1))),
            "rows": rows,
        })
    return runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("v2/analysis/local_pilots"))
    parser.add_argument("--bootstrap-iterations", type=int, default=10000)
    args = parser.parse_args()
    runs = load_runs(args.run_dirs)

    summary_rows = []
    for model in sorted({run["model"] for run in runs}):
        model_runs = [run for run in runs if run["model"] == model]
        for condition in CONDITIONS:
            values = [int(as_bool(row["task_success"])) for run in model_runs for row in run["rows"] if row["condition"] == condition]
            low, high = wilson(sum(values), len(values))
            summary_rows.append({
                "model": model,
                "condition": condition,
                "successes": sum(values),
                "episodes": len(values),
                "success_rate_percent": f"{100 * sum(values) / len(values):.2f}",
                "wilson_95_low_percent": f"{low:.2f}",
                "wilson_95_high_percent": f"{high:.2f}",
            })

    contrast_rows = []
    for model in sorted({run["model"] for run in runs}):
        model_runs = [run for run in runs if run["model"] == model]
        scenario_values = defaultdict(lambda: defaultdict(list))
        for run in model_runs:
            for row in run["rows"]:
                scenario_values[row["scenario_id"]][row["condition"]].append(int(as_bool(row["task_success"])))
        clusters = {}
        for name, (positive, negative) in CONTRASTS.items():
            values = []
            for scenario in sorted(scenario_values):
                cell = scenario_values[scenario]
                if name == "interaction":
                    values.append(
                        (cell["D"][0] - cell["C"][0])
                        - (cell["B"][0] - cell["A"][0])
                    )
                else:
                    positive_rate = sum(cell[c][0] for c in positive) / len(positive)
                    negative_rate = sum(cell[c][0] for c in negative) / len(negative)
                    values.append(positive_rate - negative_rate)
            clusters[name] = values
            low, high = bootstrap_ci(values, iterations=args.bootstrap_iterations)
            contrast_rows.append({
                "model": model,
                "contrast": name,
                "scenario_clusters": len(values),
                "estimate_percentage_points": f"{100 * sum(values) / len(values):.2f}",
                "bootstrap_95_low_points": f"{low:.2f}",
                "bootstrap_95_high_points": f"{high:.2f}",
            })

    out = args.out_dir
    write_csv(out / "uncertainty_by_model_condition.csv", summary_rows, list(summary_rows[0]))
    write_csv(out / "paired_contrasts.csv", contrast_rows, list(contrast_rows[0]))

    lines = [
        "# Uncertainty Analysis for Local Pilots",
        "",
        f"Runs analyzed: {len(runs)}; bootstrap iterations: {args.bootstrap_iterations}.",
        "Wilson intervals describe aggregate success proportions. Contrast intervals use a scenario-cluster bootstrap: each of the 25 scenario IDs is one resampling unit, with seed results averaged within scenario.",
        "",
        "## Success Rates",
        "",
        "| Model | Condition | Successes | Rate | Wilson 95% interval |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(f"| `{row['model']}` | {row['condition']} | {row['successes']}/{row['episodes']} | {row['success_rate_percent']}% | [{row['wilson_95_low_percent']}%, {row['wilson_95_high_percent']}%] |")
    lines += ["", "## Paired Contrasts", "", "| Model | Contrast | Estimate | Bootstrap 95% interval |", "| --- | --- | ---: | ---: |"]
    for row in contrast_rows:
        lines.append(f"| `{row['model']}` | {row['contrast']} | {row['estimate_percentage_points']} points | [{row['bootstrap_95_low_points']}, {row['bootstrap_95_high_points']}] |")
    lines += ["", "These intervals quantify uncertainty for this controlled pilot. They do not justify broad population-level claims beyond the tested models and scenario family."]
    (out / "UNCERTAINTY_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Analyzed {len(runs)} completed runs.")
    print(f"Wrote {out / 'UNCERTAINTY_ANALYSIS.md'}")


if __name__ == "__main__":
    main()
