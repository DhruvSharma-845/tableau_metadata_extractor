#!/usr/bin/env python3
"""
Tableau Metadata Extractor - Main Entry Point

A comprehensive tool to extract 100% accurate metadata from Tableau workbooks.

Usage:
    python main.py extract /path/to/workbook.twbx [options]
    python main.py compare /path/to/workbook.twbx --server URL [options]
    python main.py validate /path/to/workbook.twbx [options]
    python main.py list-workbooks --server URL [options]
"""

import sys
import json
from pathlib import Path
from typing import Optional

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Required packages not installed. Please run:")
    print("  pip install click rich")
    sys.exit(1)

from extractors.xml_extractor import XMLMetadataExtractor
from extractors.metadata_api import TableauMetadataAPIClient
from utils.comparison import MetadataComparator
from utils.validation import MetadataValidator
from utils.output import OutputGenerator

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Tableau Metadata Extractor - Extract comprehensive metadata from Tableau workbooks.
    
    Supports both local .twbx/.twb files (Option A: XML parsing) and 
    published workbooks on Tableau Server/Online (Option C: Metadata API).
    """
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', type=click.Choice(['json', 'excel', 'html', 'summary']), 
              default='json', help='Output format')
@click.option('--validate/--no-validate', default=True, help='Run validation after extraction')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def extract(file_path: str, output: Optional[str], format: str, validate: bool, verbose: bool):
    """
    Extract metadata from a Tableau workbook file.
    
    Examples:
        python main.py extract workbook.twbx
        python main.py extract workbook.twbx -o metadata.json
        python main.py extract workbook.twbx -f excel -o metadata.xlsx
        python main.py extract workbook.twbx -f html -o report.html
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Extract metadata
        task = progress.add_task("Extracting metadata...", total=None)
        
        try:
            extractor = XMLMetadataExtractor(file_path)
            metadata = extractor.extract()
            progress.update(task, description="[green]Extraction complete!")
        except Exception as e:
            console.print(f"[red]Error extracting metadata: {e}[/red]")
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    # Display summary
    console.print()
    _display_summary(metadata)
    
    # Validate if requested
    if validate:
        console.print()
        console.print("[bold]Running validation...[/bold]")
        validator = MetadataValidator()
        validation_result = validator.validate(metadata)
        
        if validation_result.is_valid:
            console.print(f"[green]✓ Validation passed (score: {validation_result.get_score()}/100)[/green]")
        else:
            console.print(f"[yellow]⚠ Validation completed with issues (score: {validation_result.get_score()}/100)[/yellow]")
            console.print(f"  Errors: {validation_result.errors_count}, Warnings: {validation_result.warnings_count}")
        
        if verbose and validation_result.issues:
            console.print()
            for issue in validation_result.issues[:10]:
                icon = "🔴" if issue.level.value == "error" else "🟡" if issue.level.value == "warning" else "ℹ️"
                console.print(f"  {icon} [{issue.category}] {issue.message}")
    
    # Generate output
    output_generator = OutputGenerator(metadata)
    
    if output:
        output_path = Path(output)
        
        if format == 'json':
            output_generator.to_json(str(output_path))
            console.print(f"\n[green]✓ JSON saved to: {output_path}[/green]")
        
        elif format == 'excel':
            output_generator.to_excel(str(output_path))
            console.print(f"\n[green]✓ Excel saved to: {output_path}[/green]")
        
        elif format == 'html':
            output_generator.to_html(str(output_path))
            console.print(f"\n[green]✓ HTML report saved to: {output_path}[/green]")
        
        elif format == 'summary':
            summary = output_generator.to_summary()
            with open(output_path, 'w') as f:
                f.write(summary)
            console.print(f"\n[green]✓ Summary saved to: {output_path}[/green]")
    
    elif format == 'json':
        # Print JSON to stdout if no output file specified
        console.print()
        console.print("[bold]Metadata JSON:[/bold]")
        console.print(metadata.to_json())


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--server', '-s', required=True, help='Tableau Server URL')
@click.option('--site', default='', help='Tableau site content URL')
@click.option('--token-name', help='Personal access token name')
@click.option('--token-secret', help='Personal access token secret')
@click.option('--username', '-u', help='Username (if not using PAT)')
@click.option('--password', '-p', help='Password (if not using PAT)')
@click.option('--workbook-name', '-w', help='Workbook name on server (defaults to file name)')
@click.option('--project', help='Project name to filter')
@click.option('--output', '-o', type=click.Path(), help='Output comparison report')
def compare(
    file_path: str,
    server: str,
    site: str,
    token_name: Optional[str],
    token_secret: Optional[str],
    username: Optional[str],
    password: Optional[str],
    workbook_name: Optional[str],
    project: Optional[str],
    output: Optional[str]
):
    """
    Compare metadata from local file (Option A) vs Tableau Server API (Option C).
    
    This helps validate which extraction method is more suitable for your use case.
    
    Examples:
        python main.py compare workbook.twbx -s https://tableau.company.com --token-name MyToken --token-secret secret123
    """
    console.print("[bold]Tableau Metadata Comparison[/bold]")
    console.print(f"Local file: {file_path}")
    console.print(f"Server: {server}")
    console.print()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Extract from local file
        task1 = progress.add_task("Extracting from local file (Option A)...", total=None)
        try:
            xml_extractor = XMLMetadataExtractor(file_path)
            xml_metadata = xml_extractor.extract()
            progress.update(task1, description="[green]✓ Local extraction complete")
        except Exception as e:
            console.print(f"[red]Error extracting from local file: {e}[/red]")
            sys.exit(1)
        
        # Connect to server and extract
        task2 = progress.add_task("Connecting to Tableau Server (Option C)...", total=None)
        try:
            api_client = TableauMetadataAPIClient(
                server_url=server,
                site_id=site,
                token_name=token_name,
                token_secret=token_secret,
                username=username,
                password=password,
            )
            api_client.authenticate()
            progress.update(task2, description="[green]✓ Connected to server")
        except Exception as e:
            console.print(f"[red]Error connecting to server: {e}[/red]")
            sys.exit(1)
        
        # Extract from API
        task3 = progress.add_task("Extracting from Metadata API...", total=None)
        try:
            wb_name = workbook_name or Path(file_path).stem
            api_metadata = api_client.get_workbook_metadata(wb_name, project)
            progress.update(task3, description="[green]✓ API extraction complete")
        except Exception as e:
            console.print(f"[red]Error extracting from API: {e}[/red]")
            console.print("[yellow]Note: Workbook must be published to server with same name[/yellow]")
            sys.exit(1)
        finally:
            api_client.close()
        
        # Compare
        task4 = progress.add_task("Comparing metadata...", total=None)
        comparator = MetadataComparator()
        result = comparator.compare(xml_metadata, api_metadata)
        progress.update(task4, description="[green]✓ Comparison complete")
    
    # Display results
    console.print()
    console.print(Panel.fit(
        f"[bold]Match Percentage: {result.get_match_percentage()}%[/bold]",
        title="Comparison Result",
        border_style="green" if result.get_match_percentage() > 90 else "yellow"
    ))
    
    console.print()
    table = Table(title="Comparison Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("XML (Option A)", justify="right")
    table.add_column("API (Option C)", justify="right")
    
    xml_stats = result.summary.get("xml_stats", {})
    api_stats = result.summary.get("api_stats", {})
    
    for key in xml_stats:
        table.add_row(
            key.replace("_", " ").title(),
            str(xml_stats.get(key, 0)),
            str(api_stats.get(key, 0))
        )
    
    console.print(table)
    
    # Show differences
    if result.differences:
        console.print()
        console.print(f"[bold]Differences Found: {result.total_differences}[/bold]")
        console.print(f"  Critical: {result.critical_differences}")
        console.print(f"  Errors: {result.error_differences}")
        console.print(f"  Warnings: {result.warning_differences}")
        console.print(f"  Info: {result.info_differences}")
    
    # Save report if output specified
    if output:
        report = comparator.generate_report(result)
        with open(output, 'w') as f:
            f.write(report)
        console.print(f"\n[green]✓ Comparison report saved to: {output}[/green]")
    
    # Recommendation
    console.print()
    if result.get_match_percentage() > 95:
        console.print("[green]✓ Both methods produce highly consistent results.[/green]")
        console.print("  Recommendation: Use Option A (XML) for local files, Option C (API) for server workbooks.")
    elif result.get_match_percentage() > 80:
        console.print("[yellow]⚠ Minor differences detected between methods.[/yellow]")
        console.print("  Recommendation: Option A (XML) typically provides more detail for local analysis.")
    else:
        console.print("[red]⚠ Significant differences detected.[/red]")
        console.print("  Review the comparison report and verify workbook versions match.")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--strict', is_flag=True, help='Treat warnings as errors')
@click.option('--output', '-o', type=click.Path(), help='Save validation report')
def validate(file_path: str, strict: bool, output: Optional[str]):
    """
    Validate extracted metadata for completeness and accuracy.
    
    Examples:
        python main.py validate workbook.twbx
        python main.py validate workbook.twbx --strict
    """
    console.print("[bold]Validating Tableau Workbook Metadata[/bold]")
    console.print(f"File: {file_path}")
    console.print()
    
    # Extract
    with console.status("Extracting metadata..."):
        extractor = XMLMetadataExtractor(file_path)
        metadata = extractor.extract()
    
    # Validate
    with console.status("Running validation checks..."):
        validator = MetadataValidator(strict_mode=strict)
        result = validator.validate(metadata)
    
    # Display results
    console.print()
    score_color = "green" if result.get_score() >= 80 else "yellow" if result.get_score() >= 60 else "red"
    console.print(Panel.fit(
        f"[bold]Validation Score: [{score_color}]{result.get_score()}/100[/{score_color}][/bold]\n"
        f"Status: {'[green]PASSED[/green]' if result.is_valid else '[red]FAILED[/red]'}",
        title="Validation Result"
    ))
    
    console.print()
    console.print(f"Items Checked: {result.checked_items}")
    console.print(f"Items Passed: {result.passed_items}")
    console.print(f"Critical Issues: {result.critical_count}")
    console.print(f"Errors: {result.errors_count}")
    console.print(f"Warnings: {result.warnings_count}")
    
    # Show issues
    if result.issues:
        console.print()
        console.print("[bold]Issues Found:[/bold]")
        for issue in result.issues[:20]:
            if issue.level.value == "critical":
                icon = "[red]🔴[/red]"
            elif issue.level.value == "error":
                icon = "[red]❌[/red]"
            elif issue.level.value == "warning":
                icon = "[yellow]⚠️[/yellow]"
            else:
                icon = "[blue]ℹ️[/blue]"
            
            console.print(f"  {icon} [{issue.category}] {issue.item}: {issue.message}")
            if issue.suggestion:
                console.print(f"      → {issue.suggestion}")
        
        if len(result.issues) > 20:
            console.print(f"  ... and {len(result.issues) - 20} more issues")
    
    # Save report
    if output:
        report = validator.generate_report(result)
        with open(output, 'w') as f:
            f.write(report)
        console.print(f"\n[green]✓ Validation report saved to: {output}[/green]")
    
    # Exit code
    if not result.is_valid:
        sys.exit(1)


@cli.command('list-workbooks')
@click.option('--server', '-s', required=True, help='Tableau Server URL')
@click.option('--site', default='', help='Tableau site content URL')
@click.option('--token-name', help='Personal access token name')
@click.option('--token-secret', help='Personal access token secret')
@click.option('--username', '-u', help='Username')
@click.option('--password', '-p', help='Password')
@click.option('--project', help='Filter by project name')
def list_workbooks(
    server: str,
    site: str,
    token_name: Optional[str],
    token_secret: Optional[str],
    username: Optional[str],
    password: Optional[str],
    project: Optional[str]
):
    """
    List workbooks available on Tableau Server.
    
    Examples:
        python main.py list-workbooks -s https://tableau.company.com --token-name MyToken --token-secret secret
    """
    console.print(f"[bold]Connecting to: {server}[/bold]")
    
    try:
        client = TableauMetadataAPIClient(
            server_url=server,
            site_id=site,
            token_name=token_name,
            token_secret=token_secret,
            username=username,
            password=password,
        )
        client.authenticate()
        console.print("[green]✓ Connected successfully[/green]")
        
        workbooks = client.list_workbooks(project)
        client.close()
        
        if not workbooks:
            console.print("[yellow]No workbooks found[/yellow]")
            return
        
        table = Table(title=f"Workbooks ({len(workbooks)} found)")
        table.add_column("Name", style="cyan")
        table.add_column("Project", style="magenta")
        table.add_column("Owner", style="green")
        table.add_column("Created", style="dim")
        
        for wb in workbooks:
            table.add_row(
                wb.get("name", "N/A"),
                wb.get("projectName", "N/A"),
                wb.get("owner", {}).get("name", "N/A"),
                wb.get("createdAt", "N/A")[:10] if wb.get("createdAt") else "N/A"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _display_summary(metadata):
    """Display extraction summary."""
    table = Table(title="Extraction Summary")
    table.add_column("Component", style="cyan")
    table.add_column("Count", justify="right", style="green")
    
    table.add_row("Data Sources", str(len(metadata.datasources)))
    table.add_row("Worksheets", str(metadata.total_sheets))
    table.add_row("Dashboards", str(metadata.total_dashboards))
    table.add_row("Total Fields", str(metadata.total_fields))
    table.add_row("Calculated Fields", str(metadata.total_calculated_fields))
    table.add_row("Parameters", str(metadata.total_parameters))
    table.add_row("Total Filters", str(metadata.total_filters))
    
    console.print(table)
    
    # Show worksheets
    if metadata.sheets:
        console.print()
        sheets_table = Table(title="Worksheets")
        sheets_table.add_column("Name", style="cyan")
        sheets_table.add_column("Chart Type", style="magenta")
        sheets_table.add_column("Filters", justify="right")
        sheets_table.add_column("Fields", justify="right")
        
        for sheet in metadata.sheets[:10]:
            chart_type = sheet.visual.chart_type.value if sheet.visual else "N/A"
            sheets_table.add_row(
                sheet.name,
                chart_type,
                str(len(sheet.filters)),
                str(len(sheet.all_fields_used))
            )
        
        if len(metadata.sheets) > 10:
            sheets_table.add_row("...", f"({len(metadata.sheets) - 10} more)", "", "")
        
        console.print(sheets_table)


# Simple API for programmatic use
def extract_metadata(file_path: str):
    """
    Simple function to extract metadata from a Tableau workbook.
    
    Args:
        file_path: Path to .twbx or .twb file
        
    Returns:
        WorkbookMetadata: Extracted metadata
    """
    extractor = XMLMetadataExtractor(file_path)
    return extractor.extract()


def compare_extraction_methods(
    file_path: str,
    server_url: str,
    site_id: str = "",
    token_name: Optional[str] = None,
    token_secret: Optional[str] = None,
    workbook_name: Optional[str] = None
):
    """
    Compare XML extraction vs API extraction.
    
    Args:
        file_path: Path to local .twbx file
        server_url: Tableau Server URL
        site_id: Site content URL
        token_name: PAT name
        token_secret: PAT secret
        workbook_name: Name of workbook on server
        
    Returns:
        ComparisonResult: Comparison results
    """
    # XML extraction
    xml_extractor = XMLMetadataExtractor(file_path)
    xml_metadata = xml_extractor.extract()
    
    # API extraction
    api_client = TableauMetadataAPIClient(
        server_url=server_url,
        site_id=site_id,
        token_name=token_name,
        token_secret=token_secret,
    )
    api_client.authenticate()
    
    wb_name = workbook_name or Path(file_path).stem
    api_metadata = api_client.get_workbook_metadata(wb_name)
    api_client.close()
    
    # Compare
    comparator = MetadataComparator()
    return comparator.compare(xml_metadata, api_metadata)


if __name__ == "__main__":
    cli()
