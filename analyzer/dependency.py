# analyzer/dependency.py
import re
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path
from analyzer.reader import ProjectStructure, FileNode
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DependencyGraph:
    nodes: list[str] = field(default_factory=list)          # relative paths
    edges: list[tuple[str, str]] = field(default_factory=list)  # (from, to)
    external_deps: dict[str, list[str]] = field(default_factory=dict)  # file -> [pkg]
    internal_refs: dict[str, list[str]] = field(default_factory=dict)  # file -> [file]
    most_referenced: list[tuple[str, int]] = field(default_factory=list)


IMPORT_PATTERNS: dict[str, list[re.Pattern]] = {
    ".py": [
        re.compile(r"^(?:from|import)\s+([\w.]+)", re.MULTILINE),
    ],
    ".js": [
        re.compile(r"""(?:import|require)\s*(?:\(?\s*['"])([\./][\w\./\-@]+)['"]"""),
        re.compile(r"""import\s+.*?\s+from\s+['"]([^'"]+)['"]"""),
    ],
    ".ts": [
        re.compile(r"""import\s+.*?\s+from\s+['"]([^'"]+)['"]"""),
    ],
    ".jsx": [
        re.compile(r"""import\s+.*?\s+from\s+['"]([^'"]+)['"]"""),
    ],
    ".tsx": [
        re.compile(r"""import\s+.*?\s+from\s+['"]([^'"]+)['"]"""),
    ],
}
# Compartir el mismo patrón para extensiones derivadas
IMPORT_PATTERNS[".mjs"] = IMPORT_PATTERNS[".js"]
IMPORT_PATTERNS[".cjs"] = IMPORT_PATTERNS[".js"]


def _is_relative(imp: str, ext: str) -> bool:
    if ext == ".py":
        return False  # Python usa nombres de módulo, no paths relativos en imports
    return imp.startswith("./") or imp.startswith("../") or imp.startswith("/")


class DependencyAnalyzer:
    def __init__(self, structure: ProjectStructure):
        self.structure = structure
        self._path_index: dict[str, FileNode] = {
            f.relative_path: f for f in structure.files
        }

    def analyze(self) -> DependencyGraph:
        graph = DependencyGraph()
        ref_count: dict[str, int] = defaultdict(int)

        graph.nodes = [f.relative_path for f in self.structure.files]

        for file_node in self.structure.files:
            if not file_node.content:
                continue
            patterns = IMPORT_PATTERNS.get(file_node.extension, [])
            if not patterns:
                continue

            external: list[str] = []
            internal: list[str] = []

            for pattern in patterns:
                for match in pattern.finditer(file_node.content):
                    imp = match.group(1)
                    if _is_relative(imp, file_node.extension):
                        resolved = self._resolve_relative(file_node, imp)
                        if resolved:
                            internal.append(resolved)
                            graph.edges.append((file_node.relative_path, resolved))
                            ref_count[resolved] += 1
                    else:
                        pkg = imp.split(".")[0] if file_node.extension == ".py" else imp.split("/")[0]
                        if pkg and not pkg.startswith("."):
                            external.append(pkg)

            graph.external_deps[file_node.relative_path] = list(set(external))
            graph.internal_refs[file_node.relative_path] = list(set(internal))

        graph.most_referenced = sorted(ref_count.items(), key=lambda x: x[1], reverse=True)[:10]
        return graph

    def _resolve_relative(self, source: FileNode, imp: str) -> str | None:
        source_dir = source.path.parent
        candidate = (source_dir / imp).resolve()

        # Intentar con extensiones comunes si no tiene extensión
        suffixes = [".py", ".js", ".ts", ".jsx", ".tsx", "/__init__.py", "/index.js", "/index.ts"]
        for suffix in ["", *suffixes]:
            full = Path(str(candidate) + suffix)
            rel = None
            try:
                rel = str(full.relative_to(self.structure.root))
            except ValueError:
                continue
            if rel in self._path_index:
                return rel
        return None