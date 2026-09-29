"""Aggregate completed local pilot runs into paper-facing tables and SVG figures."""
import argparse
import csv
import html
import json
from collections import defaultdict
from pathlib import Path


CONDITIONS = {
    'A': ('plain', 'json'),
    'B': ('structured', 'json'),
    'C': ('plain', 'schema'),
    'D': ('structured', 'schema'),
}

SCENARIO_TYPES = (
    'invalid_arguments',
    'persistent_unavailability',
    'temporary_timeout',
    'malformed_output',
    'plausible_incorrect_output',
)

SCENARIO_LABELS = {
    'invalid_arguments': 'Invalid args',
    'persistent_unavailability': 'Offline primary',
    'temporary_timeout': 'Timeout',
    'malformed_output': 'Malformed',
    'plausible_incorrect_output': 'Stale output',
}

PALETTE = {
    'A': '#4068b5',
    'B': '#49a078',
    'C': '#c45a3f',
    'D': '#7a5aa6',
}


def pct(successes, episodes):
    return round(100 * successes / episodes, 1) if episodes else 0.0


def pct_text(successes, episodes):
    return f'{pct(successes, episodes):.1f}%'


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_run(run_dir):
    manifest_path = run_dir / 'manifest.json'
    condition_path = run_dir / 'analysis_by_condition.csv'
    type_path = run_dir / 'analysis_by_scenario_type.csv'
    if not manifest_path.exists() or not condition_path.exists() or not type_path.exists():
        raise SystemExit(f'Missing manifest or analysis CSVs in {run_dir}')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('status') != 'COMPLETED' or int(manifest.get('completed_episodes', 0)) != 100:
        raise SystemExit(f'Not a completed 100-episode run: {run_dir}')
    return {
        'run_dir': run_dir,
        'run_id': run_dir.name,
        'model': manifest.get('model', 'unknown'),
        'seed': int(manifest.get('generation_seed', manifest.get('options', {}).get('seed', -1))),
        'by_condition': read_csv(condition_path),
        'by_type': read_csv(type_path),
    }


def discover_runs(outputs):
    runs = []
    for run_dir in sorted(outputs.glob('local_pilot_*')):
        manifest_path = run_dir / 'manifest.json'
        condition_path = run_dir / 'analysis_by_condition.csv'
        type_path = run_dir / 'analysis_by_scenario_type.csv'
        if not (manifest_path.exists() and condition_path.exists() and type_path.exists()):
            continue
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest.get('status') == 'COMPLETED' and int(manifest.get('completed_episodes', 0)) == 100:
            runs.append(run_dir)
    if not runs:
        raise SystemExit(f'No completed 100-episode local_pilot_* runs found under {outputs}')
    return runs


def add_counts(grouped, key, successes, episodes, response_errors=0):
    row = grouped[key]
    row['successes'] += int(successes)
    row['episodes'] += int(episodes)
    row['response_errors'] += int(response_errors)


def aggregate(runs):
    by_run = []
    by_model_condition = defaultdict(lambda: {'successes': 0, 'episodes': 0, 'response_errors': 0})
    by_model_type = defaultdict(lambda: {'successes': 0, 'episodes': 0, 'response_errors': 0})

    for run in runs:
        for row in run['by_condition']:
            condition = row['condition']
            successes = int(row['successes'])
            episodes = int(row['episodes'])
            response_errors = int(row['response_errors'])
            by_run.append({
                'run_id': run['run_id'],
                'model': run['model'],
                'seed': run['seed'],
                'condition': condition,
                'history': row['history'],
                'mode': row['mode'],
                'successes': successes,
                'episodes': episodes,
                'success_rate': pct_text(successes, episodes),
                'response_errors': response_errors,
            })
            key = (run['model'], condition)
            add_counts(by_model_condition, key, successes, episodes, response_errors)

        for row in run['by_type']:
            key = (run['model'], row['condition'], row['scenario_type'])
            add_counts(by_model_type, key, row['successes'], row['episodes'])

    model_condition_rows = []
    for model, condition in sorted(by_model_condition):
        counts = by_model_condition[(model, condition)]
        history, mode = CONDITIONS[condition]
        model_condition_rows.append({
            'model': model,
            'condition': condition,
            'history': history,
            'mode': mode,
            'successes': counts['successes'],
            'episodes': counts['episodes'],
            'success_rate': pct_text(counts['successes'], counts['episodes']),
            'response_errors': counts['response_errors'],
        })

    type_rows = []
    for model, condition, scenario_type in sorted(by_model_type):
        counts = by_model_type[(model, condition, scenario_type)]
        history, mode = CONDITIONS[condition]
        type_rows.append({
            'model': model,
            'condition': condition,
            'history': history,
            'mode': mode,
            'scenario_type': scenario_type,
            'successes': counts['successes'],
            'episodes': counts['episodes'],
            'success_rate': pct_text(counts['successes'], counts['episodes']),
        })

    contrast_rows = []
    models = sorted({row['model'] for row in model_condition_rows})
    lookup = {(row['model'], row['condition']): row for row in model_condition_rows}
    for model in models:
        rates = {c: pct(lookup[(model, c)]['successes'], lookup[(model, c)]['episodes']) for c in CONDITIONS}
        json_rate = (rates['A'] + rates['B']) / 2
        schema_rate = (rates['C'] + rates['D']) / 2
        plain_rate = (rates['A'] + rates['C']) / 2
        structured_rate = (rates['B'] + rates['D']) / 2
        contrast_rows.append({
            'model': model,
            'json_mean_success_rate': f'{json_rate:.1f}%',
            'schema_mean_success_rate': f'{schema_rate:.1f}%',
            'schema_minus_json_points': f'{schema_rate - json_rate:.1f}',
            'plain_mean_success_rate': f'{plain_rate:.1f}%',
            'structured_mean_success_rate': f'{structured_rate:.1f}%',
            'structured_minus_plain_points': f'{structured_rate - plain_rate:.1f}',
            'interaction_d_minus_c_minus_b_minus_a_points': f'{(rates["D"] - rates["C"]) - (rates["B"] - rates["A"]):.1f}',
        })

    return by_run, model_condition_rows, type_rows, contrast_rows


def svg_text(x, y, text, size=13, anchor='middle', weight='400', color='#222'):
    return (f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{html.escape(str(text))}</text>')


def success_bar_svg(rows, path):
    models = sorted({row['model'] for row in rows})
    lookup = {(row['model'], row['condition']): row for row in rows}
    width, height = 900, 520
    left, right, top, bottom = 90, 40, 56, 82
    chart_h = height - top - bottom
    group_w = (width - left - right) / len(models)
    bar_w = 34
    gap = 12
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(width / 2, 28, 'Verified Recovery Success by Condition', 18, weight='700'),
        f'<line x1="{left}" y1="{top + chart_h}" x2="{width - right}" y2="{top + chart_h}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}" stroke="#333"/>',
    ]
    for tick in range(0, 101, 20):
        y = top + chart_h - chart_h * tick / 100
        parts.append(f'<line x1="{left - 5}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#e4e4e4"/>')
        parts.append(svg_text(left - 12, y + 4, f'{tick}%', 12, anchor='end', color='#444'))
    for i, model in enumerate(models):
        start = left + i * group_w + group_w / 2 - (4 * bar_w + 3 * gap) / 2
        parts.append(svg_text(left + i * group_w + group_w / 2, height - 32, model, 13, weight='700'))
        for j, condition in enumerate(CONDITIONS):
            row = lookup[(model, condition)]
            rate = pct(row['successes'], row['episodes'])
            x = start + j * (bar_w + gap)
            bar_h = chart_h * rate / 100
            y = top + chart_h - bar_h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" fill="{PALETTE[condition]}"/>')
            parts.append(svg_text(x + bar_w / 2, y - 6, f'{rate:.0f}%', 11))
            parts.append(svg_text(x + bar_w / 2, top + chart_h + 18, condition, 12, weight='700'))
    legend_x = width - right - 260
    legend_y = 44
    for i, condition in enumerate(CONDITIONS):
        x = legend_x + i * 64
        parts.append(f'<rect x="{x}" y="{legend_y}" width="14" height="14" fill="{PALETTE[condition]}"/>')
        parts.append(svg_text(x + 21, legend_y + 12, condition, 12, anchor='start'))
    parts.append('</svg>')
    path.write_text('\n'.join(parts) + '\n', encoding='utf-8')


def heatmap_svg(rows, path):
    models = sorted({row['model'] for row in rows})
    lookup = {(row['model'], row['condition'], row['scenario_type']): row for row in rows}
    cell_w, cell_h = 108, 36
    left, top = 185, 70
    width = left + len(SCENARIO_TYPES) * cell_w + 45
    height = top + len(models) * len(CONDITIONS) * cell_h + 70
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(width / 2, 28, 'Success Rate by Model, Condition, and Failure Type', 18, weight='700'),
    ]
    for j, kind in enumerate(SCENARIO_TYPES):
        parts.append(svg_text(left + j * cell_w + cell_w / 2, top - 16, SCENARIO_LABELS[kind], 11))
    row_index = 0
    for model in models:
        for condition in CONDITIONS:
            y = top + row_index * cell_h
            label = f'{model} {condition}'
            parts.append(svg_text(left - 12, y + 23, label, 12, anchor='end', weight='700' if condition == 'A' else '400'))
            for j, kind in enumerate(SCENARIO_TYPES):
                row = lookup[(model, condition, kind)]
                rate = pct(row['successes'], row['episodes'])
                intensity = rate / 100
                red = int(245 - 125 * intensity)
                green = int(247 - 52 * intensity)
                blue = int(244 - 95 * intensity)
                fill = f'#{red:02x}{green:02x}{blue:02x}'
                x = left + j * cell_w
                parts.append(f'<rect x="{x}" y="{y}" width="{cell_w - 3}" height="{cell_h - 3}" fill="{fill}" stroke="#ffffff"/>')
                parts.append(svg_text(x + cell_w / 2, y + 22, f'{rate:.0f}%', 12))
            row_index += 1
    parts.append('</svg>')
    path.write_text('\n'.join(parts) + '\n', encoding='utf-8')


def write_markdown(path, runs, condition_rows, contrast_rows):
    lines = [
        '# Aggregated Local Pilot Results',
        '',
        f'Aggregated runs: {len(runs)}',
        '',
        '| Run | Model | Seed |',
        '| --- | --- | ---: |',
    ]
    for run in runs:
        lines.append(f"| `{run['run_id']}` | `{run['model']}` | {run['seed']} |")
    lines += [
        '',
        '## Main Table',
        '',
        '| Model | Condition | History | Output mode | Successes | Success rate | Response errors |',
        '| --- | --- | --- | --- | ---: | ---: | ---: |',
    ]
    for row in condition_rows:
        lines.append(
            f"| `{row['model']}` | {row['condition']} | {row['history']} | {row['mode']} | "
            f"{row['successes']}/{row['episodes']} | {row['success_rate']} | {row['response_errors']} |"
        )
    lines += [
        '',
        '## Contrasts',
        '',
        '| Model | Schema minus JSON | Structured minus plain | Interaction |',
        '| --- | ---: | ---: | ---: |',
    ]
    for row in contrast_rows:
        lines.append(
            f"| `{row['model']}` | {row['schema_minus_json_points']} pts | "
            f"{row['structured_minus_plain_points']} pts | "
            f"{row['interaction_d_minus_c_minus_b_minus_a_points']} pts |"
        )
    lines += [
        '',
        '## Figures',
        '',
        '- `success_by_condition.svg`',
        '- `success_heatmap_by_failure_type.svg`',
    ]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dirs', nargs='*', help='Completed local_pilot_* directories. Defaults to every completed 100-episode run.')
    parser.add_argument('--out-dir', default=str(here / 'analysis' / 'local_pilots'), help='Directory for aggregated CSVs and SVG figures.')
    args = parser.parse_args()

    run_dirs = [Path(p) for p in args.run_dirs] if args.run_dirs else discover_runs(here / 'outputs')
    runs = [load_run(path) for path in run_dirs]
    by_run, condition_rows, type_rows, contrast_rows = aggregate(runs)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / 'aggregate_by_run_condition.csv', by_run, list(by_run[0]))
    write_csv(out_dir / 'aggregate_by_model_condition.csv', condition_rows, list(condition_rows[0]))
    write_csv(out_dir / 'aggregate_by_model_condition_scenario_type.csv', type_rows, list(type_rows[0]))
    write_csv(out_dir / 'aggregate_contrasts.csv', contrast_rows, list(contrast_rows[0]))
    success_bar_svg(condition_rows, out_dir / 'success_by_condition.svg')
    heatmap_svg(type_rows, out_dir / 'success_heatmap_by_failure_type.svg')
    write_markdown(out_dir / 'RESULTS_AGGREGATED.md', runs, condition_rows, contrast_rows)

    print(f'Aggregated {len(runs)} completed local pilot runs.')
    print(f'Wrote {out_dir}')


if __name__ == '__main__':
    main()
