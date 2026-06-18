import click
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from analyzer.core import ProjectAnalyzer
from generator.html_export import HTMLExporter
from utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def cli():
    """Project Analyzer — Generador automático de documentación técnica visual."""
    pass


@cli.command()
@click.argument("source")
@click.option("--output", "-o", default="architecture.html", help="Archivo HTML de salida")
@click.option("--depth", "-d", default=6, help="Profundidad máxima de directorios")
@click.option("--exclude", "-e", multiple=True, default=[], help="Directorios a excluir")
def analyze(source: str, output: str, depth: int, exclude: tuple):
    """
    Analiza un proyecto y genera documentación técnica visual.

    SOURCE puede ser:
      - Ruta a carpeta local: ./mi-proyecto
      - Archivo ZIP: ./mi-proyecto.zip
      - Repositorio GitHub: https://github.com/user/repo
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Iniciando análisis...", total=None)

        try:
            analyzer = ProjectAnalyzer(
                source=source,
                max_depth=depth,
                exclude_dirs=set(exclude) | {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build"},
            )

            progress.update(task, description="Leyendo estructura del proyecto...")
            analyzer.read_structure()

            progress.update(task, description="Detectando lenguaje y frameworks...")
            analyzer.detect_stack()

            progress.update(task, description="Analizando dependencias e imports...")
            analyzer.analyze_dependencies()

            progress.update(task, description="Evaluando riesgos de modificación...")
            analyzer.evaluate_risks()

            progress.update(task, description="Generando documentación...")
            docs = analyzer.generate_documentation()

            progress.update(task, description="Exportando HTML interactivo...")
            exporter = HTMLExporter(analysis=analyzer.result, docs=docs)
            exporter.export(output_path=output)

        except FileNotFoundError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
        except PermissionError as e:
            console.print(f"[red]Permiso denegado:[/red] {e}")
            sys.exit(1)
        except Exception as e:
            logger.exception("Error inesperado durante el análisis")
            console.print(f"[red]Error inesperado:[/red] {e}")
            sys.exit(1)

    console.print(f"\n[green]✓[/green] Documentación generada: [bold]{output}[/bold]")
    console.print(f"  Abre el archivo en tu navegador para ver el resultado.")


if __name__ == "__main__":
    cli()