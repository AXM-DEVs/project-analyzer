import shutil
from pathlib import Path
from dataclasses import dataclass, field
from utils.fs import walk_project, is_text_file, read_text_safe, extract_zip, clone_github
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FileNode:
    path: Path
    relative_path: str
    extension: str
    size_bytes: int
    content: str | None
    is_entry_point: bool = False
    is_config: bool = False
    is_critical: bool = False


@dataclass
class ProjectStructure:
    root: Path
    tmp_dir: Path | None  # Para limpiar al finalizar
    files: list[FileNode] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    total_files: int = 0
    total_dirs: int = 0


ENTRY_POINT_NAMES = {
    "main.py", "app.py", "server.py", "index.py", "run.py", "manage.py",
    "index.js", "index.ts", "server.js", "server.ts", "app.js", "app.ts",
    "main.js", "main.ts", "index.jsx", "index.tsx",
    "main.go", "main.rs", "Program.cs", "Main.java",
}

CONFIG_NAMES = {
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "Cargo.toml",
    "go.mod", "pom.xml", "build.gradle", "requirements.txt", "Pipfile",
    "composer.json", "Gemfile", ".env", ".env.example", "config.py",
    "config.js", "config.ts", "settings.py", "webpack.config.js",
    "vite.config.js", "vite.config.ts", "tsconfig.json", "jest.config.js",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".github/workflows", "Makefile", ".eslintrc.js", ".eslintrc.json",
    "babel.config.js", "tailwind.config.js", "next.config.js",
}


class ProjectReader:
    def __init__(self, source: str, max_depth: int, exclude_dirs: set[str]):
        self.source = source
        self.max_depth = max_depth
        self.exclude_dirs = exclude_dirs

    def read(self) -> ProjectStructure:
        root, tmp_dir = self._resolve_source()
        structure = ProjectStructure(root=root, tmp_dir=tmp_dir)

        for dir_path, subdirs, filenames in walk_project(root, self.max_depth, self.exclude_dirs):
            rel_dir = str(dir_path.relative_to(root))
            if rel_dir != ".":
                structure.directories.append(rel_dir)
                structure.total_dirs += 1

            for fname in filenames:
                fpath = dir_path / fname
                rel_path = str(fpath.relative_to(root))
                ext = fpath.suffix.lower()

                content = None
                if is_text_file(fpath):
                    content = read_text_safe(fpath)

                try:
                    size = fpath.stat().st_size
                except OSError:
                    size = 0

                node = FileNode(
                    path=fpath,
                    relative_path=rel_path,
                    extension=ext,
                    size_bytes=size,
                    content=content,
                    is_entry_point=fname in ENTRY_POINT_NAMES,
                    is_config=fname in CONFIG_NAMES or ext in {".env", ".yml", ".yaml", ".toml", ".ini"},
                )
                structure.files.append(node)
                structure.total_files += 1

        return structure

    def _resolve_source(self) -> tuple[Path, Path | None]:
        src = self.source.strip()

        if src.startswith("https://github.com") or src.startswith("git@github.com"):
            logger.warning("Clonando repositorio GitHub: %s", src)
            tmp_dir, root = clone_github(src)
            return root, tmp_dir

        path = Path(src)
        if not path.exists():
            raise FileNotFoundError(f"La fuente no existe: {src}")

        if path.is_dir():
            return path.resolve(), None

        if path.suffix.lower() == ".zip":
            tmp_dir, root = extract_zip(str(path))
            return root, tmp_dir

        raise ValueError(f"Fuente no reconocida: {src}. Usa una carpeta, ZIP, o URL de GitHub.")