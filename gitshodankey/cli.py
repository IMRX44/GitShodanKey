import asyncio
import time
from pathlib import Path

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from .config import Config
from .extractors.key_extractor import KeyExtractor
from .models import Finding, ScanResult
from .output.formatters import get_formatter
from .output.notifiers import DiscordNotifier, TelegramNotifier
from .output.reporter import generate_html_report
from .searchers.github import GitHubSearcher
from .searchers.gitlab import GitLabSearcher
from .utils.dedup import Deduplicator
from .utils.resume import ResumeState
from .validators import get_validator

console = Console()

BANNER = """[bold blue]
  ██████╗ ██╗████████╗███████╗██╗  ██╗ ██████╗ ██████╗  █████╗ ███╗   ██╗
 ██╔════╝ ██║╚══██╔══╝██╔════╝██║  ██║██╔═══██╗██╔══██╗██╔══██╗████╗  ██║
 ██║  ███╗██║   ██║   ███████╗███████║██║   ██║██║  ██║███████║██╔██╗ ██║
 ██║   ██║██║   ██║   ╚════██║██╔══██║██║   ██║██║  ██║██╔══██║██║╚██╗██║
 ╚██████╔╝██║   ██║   ███████║██║  ██║╚██████╔╝██████╔╝██║  ██║██║ ╚████║
  ╚═════╝ ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝
[/bold blue][dim]  v2.0 — Async API Key Hunter | GitHub + GitLab | 11 Key Types[/dim]
"""


@click.group()
def main():
    """GitShodanKey v2 — Find leaked API keys in public repositories"""
    pass


@main.command()
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub API token")
@click.option("--gitlab-token", envvar="GITLAB_TOKEN", help="GitLab API token")
@click.option("--services", default="all", show_default=True,
              help="Comma-separated: shodan,virustotal,aws,... or 'all'")
@click.option("--output", "-o", default="results", show_default=True, help="Output file name (no extension)")
@click.option("--format", "-f", "fmt", default="html",
              type=click.Choice(["json", "csv", "txt", "html"]), show_default=True)
@click.option("--notify-telegram", nargs=2, metavar="TOKEN CHAT_ID", default=None,
              help="Telegram bot token and chat ID for live alerts")
@click.option("--notify-discord", metavar="WEBHOOK_URL", default=None,
              help="Discord webhook URL for live alerts")
@click.option("--resume", is_flag=True, help="Resume from previous checkpoint")
@click.option("--concurrency", default=10, show_default=True, help="Max concurrent requests")
@click.option("--no-validate", is_flag=True, help="Skip API key validation")
@click.option("--config", "config_file", default=None, help="Path to config YAML file")
def scan(token, gitlab_token, services, output, fmt, notify_telegram, notify_discord,
         resume, concurrency, no_validate, config_file):
    """Scan GitHub/GitLab for leaked API keys across 11 services"""
    console.print(BANNER)

    cfg = Config.from_file(config_file) if config_file else Config(
        github_token=token,
        gitlab_token=gitlab_token,
        concurrency=concurrency,
    )
    if token:
        cfg.github_token = token
    if gitlab_token:
        cfg.gitlab_token = gitlab_token

    if not cfg.github_token and not cfg.gitlab_token:
        console.print("[red]Error:[/red] At least one of --token (GitHub) or --gitlab-token is required.")
        raise SystemExit(1)

    service_list = None if services == "all" else [s.strip() for s in services.split(",")]

    notifiers = []
    if notify_telegram:
        notifiers.append(TelegramNotifier(notify_telegram[0], notify_telegram[1]))
    if notify_discord:
        notifiers.append(DiscordNotifier(notify_discord))

    asyncio.run(_scan_async(
        cfg=cfg,
        service_list=service_list,
        output=output,
        fmt=fmt,
        notifiers=notifiers,
        resume=resume,
        no_validate=no_validate,
    ))


async def _scan_async(cfg, service_list, output, fmt, notifiers, resume, no_validate):
    start_time = time.time()
    extractor = KeyExtractor(service_list)
    dedup = Deduplicator()
    resume_state = ResumeState()
    findings: list[Finding] = []
    completed_keywords: list[str] = []

    if resume and Path(cfg.resume_file).exists():
        state = resume_state.load(cfg.resume_file)
        completed_keywords = state["completed_keywords"]
        findings = state["findings"]
        for f in findings:
            dedup.add(f.key)
        console.print(f"[yellow]Resuming:[/yellow] {len(completed_keywords)} keywords done, {len(findings)} findings loaded")

    # Build keyword list: (service, pattern, language)
    all_keywords = []
    for service in extractor.all_services:
        lang = extractor.get_language(service)
        for pattern in extractor.get_search_patterns(service):
            key = f"{service}:{pattern}"
            if key not in completed_keywords:
                all_keywords.append((service, pattern, lang))

    searchers = []
    if cfg.github_token:
        searchers.append(GitHubSearcher(cfg.github_token, cfg.concurrency))
    if cfg.gitlab_token:
        searchers.append(GitLabSearcher(cfg.gitlab_token, cfg.concurrency))

    console.print(f"[green]Targets:[/green] {', '.join(s.__class__.__name__ for s in searchers)}")
    console.print(f"[green]Services:[/green] {', '.join(extractor.all_services)}")
    console.print(f"[green]Keywords:[/green] {len(all_keywords)} patterns | [green]Concurrency:[/green] {cfg.concurrency}\n")

    results_table = Table(
        "Service", "Masked Key", "Repository", "Validated",
        title="[bold]Live Findings[/bold]", border_style="blue", show_lines=False,
    )

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )
    task_id = progress.add_task("Scanning...", total=len(all_keywords))

    async def process_keyword(service, pattern, lang):
        for searcher in searchers:
            try:
                raw_results = await searcher.search(pattern, lang)
            except Exception:
                continue
            for content, url, repo, file_path in raw_results:
                new_findings = extractor.extract(content, url, repo, file_path)
                for finding in new_findings:
                    if dedup.is_duplicate(finding.key):
                        continue
                    dedup.add(finding.key)

                    if not no_validate:
                        validator = get_validator(finding.service)
                        finding = await validator.validate(finding)

                    findings.append(finding)
                    results_table.add_row(
                        f"[blue]{finding.service.value.upper()}[/blue]",
                        f"[yellow]{finding.masked_key}[/yellow]",
                        finding.repo,
                        "[green]✓ VALID[/green]" if finding.validated else "[red]✗[/red]",
                    )

                    for notifier in notifiers:
                        try:
                            await notifier.notify(finding)
                        except Exception:
                            pass

        completed_keywords.append(f"{service}:{pattern}")
        resume_state.save(cfg.resume_file, completed_keywords, findings)
        progress.advance(task_id)

    with Live(console=console, refresh_per_second=4):
        console.print(progress)
        sem = asyncio.Semaphore(cfg.concurrency)

        async def bounded(service, pattern, lang):
            async with sem:
                await process_keyword(service, pattern, lang)

        await asyncio.gather(*[bounded(s, p, l) for s, p, l in all_keywords])

    for s in searchers:
        await s.close()

    duration = time.time() - start_time
    validated = sum(1 for f in findings if f.validated)
    result = ScanResult(
        findings=findings,
        total_found=len(findings),
        total_validated=validated,
        scan_duration=duration,
        services_scanned=extractor.all_services,
    )

    # Save output
    output_path = f"{output}.{fmt}"
    if fmt == "html":
        Path(output_path).write_text(generate_html_report(result))
    else:
        formatter = get_formatter(fmt)
        Path(output_path).write_text(formatter.format(findings))

    console.print(results_table)
    console.print(Panel(
        f"[green]Total found:[/green] {len(findings)}  |  "
        f"[green]Validated:[/green] {validated}  |  "
        f"[blue]Duration:[/blue] {duration:.1f}s  |  "
        f"[yellow]Output:[/yellow] {output_path}",
        title="Scan Complete",
        border_style="green",
    ))

    # Clean up resume file on success
    if Path(cfg.resume_file).exists():
        Path(cfg.resume_file).unlink()


@main.command("list-services")
def list_services():
    """List all supported API key services"""
    extractor = KeyExtractor()
    table = Table("Service", "Patterns", "Key Format", title="Supported Services", border_style="blue")
    for service in extractor.all_services:
        patterns = extractor.get_search_patterns(service)
        config = extractor.configs[service]
        table.add_row(
            f"[blue]{service.upper()}[/blue]",
            str(len(patterns)),
            f"[yellow]{config.get('key_regex', 'N/A')}[/yellow]",
        )
    console.print(table)


if __name__ == "__main__":
    main()
