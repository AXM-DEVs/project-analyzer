# utils/fs.py
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Generator


BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp4", ".mp3", ".wav", ".avi", ".mov",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".pyc", ".pyo", ".class",
    ".lock", ".sum",
    ".ttf", ".woff", ".woff2", ".eot",
}

TEXT_SIZE_LIMIT = 512 * 1024  # 512KB max por archivo de texto


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return False
    try:
        size = path.stat().st_size
        if size > TEXT_SIZE_LIMIT:
            return False
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return False
        return True
    except (OSError, PermissionError):
        return False


def read_text_safe(path: Path) -> str | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, PermissionError):
        return None


def walk_project(
    root: Path,
    max_depth: int,
    exclude_dirs: set[str],
) -> Generator[tuple[Path, list[str], list[str]], None, None]:
    """Genera (dirpath, subdirs, files) respetando profundidad y exclusiones."""
    root = root.resolve()

    def _walk(current: Path, depth: int):
        if depth > max_depth:
            return
        try:
            entries = list(current.iterdir())
        except PermissionError:
            return

        dirs = []
        files = []
        for entry in sorted(entries, key=lambda e: (e.is_file(), e.name)):
            if entry.is_dir():
                if entry.name not in exclude_dirs and not entry.name.startswith("."):
                    dirs.append(entry.name)
                    yield from _walk(entry, depth + 1)
            elif entry.is_file():
                files.append(entry.name)

        yield current, dirs, files

    yield from _walk(root, 0)


def extract_zip(zip_path: str) -> tuple[Path, Path]:
    """Extrae un ZIP a un directorio temporal. Devuelve (tmp_dir, project_root)."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="project_analyzer_"))
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_dir)

    # Si el ZIP contiene un único directorio raíz, úsalo directamente
    contents = list(tmp_dir.iterdir())
    if len(contents) == 1 and contents[0].is_dir():
        return tmp_dir, contents[0]
    return tmp_dir, tmp_dir


def clone_github(url: str) -> tuple[Path, Path]:
    """Clona un repositorio GitHub a un directorio temporal."""
    import git  # gitpython

    tmp_dir = Path(tempfile.mkdtemp(prefix="project_analyzer_"))
    try:
        git.Repo.clone_from(url, tmp_dir, depth=1)
    except git.exc.GitCommandError as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError(f"No se pudo clonar el repositorio: {e}") from e
    return tmp_dir, tmp_dir