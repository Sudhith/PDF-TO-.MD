"""
AeroDoc Command Line Interface
Fast, elegant CLI powered by Typer and Rich for batch and single-file PDF conversion.
"""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from aerodoc.config import ConversionConfig
from aerodoc.core.converter import PDFConverter

app = typer.Typer(
    name="aerodoc",
    help="AeroDoc: High-Precision PDF to Antigravity Markdown Converter",
    add_completion=False
)
console = Console(highlight=False)


@app.command()
def convert(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF file to convert"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target .md output path"),
    embed_images: bool = typer.Option(False, "--embed-images", "-e", help="Embed images as Base64 data URIs into a single standalone .md file"),
    no_images: bool = typer.Option(False, "--no-images", help="Disable image extraction"),
    no_frontmatter: bool = typer.Option(False, "--no-frontmatter", help="Omit YAML frontmatter metadata"),
    no_tables: bool = typer.Option(False, "--no-tables", help="Disable table detection"),
    no_math: bool = typer.Option(False, "--no-math", help="Disable KaTeX math formatting"),
    no_callouts: bool = typer.Option(False, "--no-callouts", help="Disable Antigravity alert transformation"),
):
    """Converts a single PDF document into Antigravity Markdown."""
    if not pdf_path.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {pdf_path}")
        raise typer.Exit(code=1)

    if output is None:
        output = pdf_path.with_suffix(".md")

    config = ConversionConfig(
        extract_images=not no_images,
        embed_images=embed_images,
        include_frontmatter=not no_frontmatter,
        detect_tables=not no_tables,
        detect_math=not no_math,
        detect_callouts=not no_callouts,
        output_path=output
    )

    console.print(Panel(
        f"[bold cyan]AeroDoc Engine[/bold cyan] -> Converting [yellow]{pdf_path.name}[/yellow]\n"
        f"Target: [green]{output}[/green] | Embed Images: [magenta]{embed_images}[/magenta]",
        title="Document Ingestion",
        border_style="cyan"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description="Extracting topology, tables, math, and text...", total=None)
        converter = PDFConverter(config)
        try:
            _, stats = converter.convert_file(pdf_path, output_path=output)
        except Exception as e:
            console.print(f"[bold red]Conversion failed:[/bold red] {e}")
            raise typer.Exit(code=1)

    # Display conversion metrics table
    summary_table = Table(title="Conversion Summary", border_style="cyan")
    summary_table.add_column("Metric", style="dim", width=24)
    summary_table.add_column("Value", style="bold green")

    summary_table.add_row("Pages Processed", str(stats["pages"]))
    summary_table.add_row("Headings Identified", str(stats["headings_found"]))
    summary_table.add_row("GFM Tables Parsed", str(stats["tables_extracted"]))
    summary_table.add_row("Figures / Images", str(stats["images_extracted"]))
    summary_table.add_row("Equations Detected", str(stats["equations_found"]))
    summary_table.add_row("Antigravity Alerts", str(stats["callouts_transformed"]))
    summary_table.add_row("Processing Duration", f"{stats['elapsed_seconds']}s")
    summary_table.add_row("Destination", str(output))

    console.print(summary_table)
    console.print(f"\n[bold green][SUCCESS] Conversion completed successfully![/bold green] Ready for Antigravity.\n")


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Directory containing PDF files"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Directory to save .md files"),
    embed_images: bool = typer.Option(False, "--embed-images", "-e", help="Embed images as Base64 data URIs"),
):
    """Batch converts all PDF files in a directory."""
    if not input_dir.exists() or not input_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] Directory not found: {input_dir}")
        raise typer.Exit(code=1)

    if output_dir is None:
        output_dir = input_dir / "converted_markdown"
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        console.print(f"[yellow]No .pdf files found in {input_dir}[/yellow]")
        return

    console.print(f"[bold cyan]Starting batch conversion of {len(pdf_files)} PDFs...[/bold cyan]")
    config = ConversionConfig(embed_images=embed_images)
    converter = PDFConverter(config)

    for pdf in pdf_files:
        target = output_dir / f"{pdf.stem}.md"
        console.print(f"-> Processing [yellow]{pdf.name}[/yellow]...")
        _, stats = converter.convert_file(pdf, output_path=target)
        console.print(f"   [green]Done in {stats['elapsed_seconds']}s[/green] ({stats['pages']} pages)")

    console.print(f"\n[bold green][SUCCESS] Batch conversion complete! Files written to {output_dir}[/bold green]")


@app.command()
def serve(
    port: int = typer.Option(8765, "--port", "-p", help="Port to run Web Studio on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host address")
):
    """Launches the interactive AeroDoc Web Studio."""
    import uvicorn
    console.print(Panel(
        f"[bold cyan]AeroDoc Web Studio[/bold cyan]\n"
        f"Server starting on [bold green]http://{host}:{port}[/bold green]\n"
        f"Press Ctrl+C to terminate.",
        title="Web Interface",
        border_style="cyan"
    ))
    uvicorn.run("aerodoc.web.server:app", host=host, port=port, log_level="info")


def main():
    app()


if __name__ == "__main__":
    main()
