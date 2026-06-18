import ast
from dataclasses import dataclass, field
from analyzer.reader import FileNode
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ModuleInfo:
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    has_main_guard: bool = False
    docstring: str | None = None
    complexity_score: int = 0  # nodos AST como proxy de complejidad


class ASTParser:
    """Parser AST para Python 3.11+. Extrae clases, funciones y métricas básicas."""

    def parse_python(self, node: FileNode) -> ModuleInfo | None:
        if not node.content or node.extension != ".py":
            return None
        try:
            tree = ast.parse(node.content, filename=node.relative_path)
        except SyntaxError as e:
            logger.debug("SyntaxError en %s: %s", node.relative_path, e)
            return None

        info = ModuleInfo()
        info.docstring = ast.get_docstring(tree)
        info.complexity_score = sum(1 for _ in ast.walk(tree))

        for child in ast.walk(tree):
            if isinstance(child, ast.ClassDef):
                info.classes.append(child.name)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Solo top-level functions (no métodos de clase)
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    info.functions.append(child.name)
            elif isinstance(child, (ast.If)):
                # Detectar `if __name__ == "__main__":`
                test = child.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "__name__"
                ):
                    info.has_main_guard = True

        # Extraer decoradores únicos
        decorators: set[str] = set()
        for child in ast.walk(tree):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for dec in child.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.add(dec.id)
                    elif isinstance(dec, ast.Attribute):
                        decorators.add(f"{dec.attr}")

        info.decorators = list(decorators)
        return info