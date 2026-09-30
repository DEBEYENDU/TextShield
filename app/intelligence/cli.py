"""Intelligence CLI commands."""

from __future__ import annotations
import click
from .repository import list_all
from .gaps import detect_gaps_from_candidates
from .coverage import calculate_coverage, overall_coverage
from .freshness import detect_stale_candidates


@click.group(name="intelligence")
def intelligence_cli():
    """Intelligence operations commands."""
    pass


@intelligence_cli.command("list")
@click.option("--limit", default=50, help="Number of candidates to list")
def list_candidates(limit):
    candidates = list_all(limit=limit)
    click.echo(f"Found {len(candidates)} candidates")
    for c in candidates[:limit]:
        click.echo(f"{c.candidate_id} - {c.title} [{c.status}]")


@intelligence_cli.command("gaps")
def gaps_cmd():
    candidates = list_all(limit=500)
    gaps = detect_gaps_from_candidates(candidates)
    click.echo(f"Detected {len(gaps)} gaps")
    for g in gaps:
        click.echo(f"{g.gap_id} - {g.gap_type} - {g.description[:80]}")


@intelligence_cli.command("coverage")
def coverage_cmd():
    candidates = list_all(limit=500)
    gaps = detect_gaps_from_candidates(candidates)
    metrics = calculate_coverage(candidates, gaps)
    overall = overall_coverage(metrics)
    click.echo(f"Overall coverage: {overall:.2%}")
    for domain, m in metrics.items():
        click.echo(f"{domain.value}: {m.coverage_score:.2%} ({m.total_candidates} candidates)")


@intelligence_cli.command("stale")
@click.option("--days", default=90, help="Max age days")
def stale_cmd(days):
    candidates = list_all(limit=500)
    stale = detect_stale_candidates(candidates, max_age_days=days)
    click.echo(f"Stale candidates: {len(stale)}")
    for r in stale:
        click.echo(f"{r.candidate_id} - age {r.age_days:.1f}d score {r.staleness_score:.2f}")
