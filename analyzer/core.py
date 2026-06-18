import shutil
from analyzer.reader import ProjectReader
from analyzer.language import LanguageDetector
from analyzer.dependency import DependencyAnalyzer
from analyzer.ast_parser import ASTParser
from analyzer.risk import RiskEvaluator
from analyzer.models import AnalysisResult
from utils.logger import get_logger

logger = get_logger(__name__)


class ProjectAnalyzer:
    def __init__(self, source: str, max_depth: int, exclude_dirs: set[str]):
        self.source = source
        self.max_depth = max_depth
        self.exclude_dirs = exclude_dirs
        self.result: AnalysisResult | None = None
        self._structure = None
        self._stack = None
        self._graph = None
        self._module_info: dict = {}
        self._risks = None

    def read_structure(self):
        reader = ProjectReader(
            source=self.source,
            max_depth=self.max_depth,
            exclude_dirs=self.exclude_dirs,
        )
        self._structure = reader.read()
        logger.warning(
            "Estructura leída: %d archivos, %d directorios",
            self._structure.total_files,
            self._structure.total_dirs,
        )

    def detect_stack(self):
        detector = LanguageDetector(self._structure)
        self._stack = detector.detect()

    def analyze_dependencies(self):
        analyzer = DependencyAnalyzer(self._structure)
        self._graph = analyzer.analyze()

        ast_parser = ASTParser()
        self._module_info = {}
        for f in self._structure.files:
            info = ast_parser.parse_python(f)
            if info:
                self._module_info[f.relative_path] = info

    def evaluate_risks(self):
        evaluator = RiskEvaluator(self._structure, self._graph)
        self._risks = evaluator.evaluate()

    def generate_documentation(self) -> dict:
        from generator.documentation import DocumentationGenerator  # deferred import — safe here
        self.result = AnalysisResult(
            structure=self._structure,
            stack=self._stack,
            graph=self._graph,
            module_info=self._module_info,
            risks=self._risks,
            root_name=self._structure.root.name,
        )
        gen = DocumentationGenerator(self.result)
        return gen.generate()

    def __del__(self):
        if self._structure and self._structure.tmp_dir:
            shutil.rmtree(self._structure.tmp_dir, ignore_errors=True)