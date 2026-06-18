from dataclasses import dataclass, field
from pathlib import Path
from analyzer.reader import ProjectStructure
from analyzer.language import StackInfo
from analyzer.dependency import DependencyGraph
from analyzer.ast_parser import ModuleInfo
from analyzer.risk import ProjectRisks


@dataclass
class AnalysisResult:
    structure: ProjectStructure
    stack: StackInfo
    graph: DependencyGraph
    module_info: dict[str, ModuleInfo]
    risks: ProjectRisks
    root_name: str