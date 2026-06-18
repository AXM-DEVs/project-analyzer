from dataclasses import dataclass, field
from analyzer.reader import ProjectStructure, FileNode
from analyzer.dependency import DependencyGraph
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RiskAssessment:
    level: str          # "critical", "high", "medium", "low"
    reasons: list[str]
    score: int          # 0-100


@dataclass
class ProjectRisks:
    file_risks: dict[str, RiskAssessment] = field(default_factory=dict)
    critical_files: list[str] = field(default_factory=list)
    high_risk_files: list[str] = field(default_factory=list)


class RiskEvaluator:
    def __init__(self, structure: ProjectStructure, graph: DependencyGraph):
        self.structure = structure
        self.graph = graph

    def evaluate(self) -> ProjectRisks:
        risks = ProjectRisks()
        ref_map: dict[str, int] = dict(self.graph.most_referenced)

        for file_node in self.structure.files:
            assessment = self._assess_file(file_node, ref_map)
            risks.file_risks[file_node.relative_path] = assessment

            if assessment.level == "critical":
                risks.critical_files.append(file_node.relative_path)
                file_node.is_critical = True
            elif assessment.level == "high":
                risks.high_risk_files.append(file_node.relative_path)

        return risks

    def _assess_file(self, node: FileNode, ref_map: dict[str, int]) -> RiskAssessment:
        score = 0
        reasons: list[str] = []

        # +40 si es punto de entrada
        if node.is_entry_point:
            score += 40
            reasons.append("Es el punto de entrada del proyecto")

        # +30 si es muy referenciado por otros archivos
        ref_count = ref_map.get(node.relative_path, 0)
        if ref_count >= 5:
            score += 30
            reasons.append(f"Referenciado por {ref_count} archivos — cambios en cascada")
        elif ref_count >= 2:
            score += 15
            reasons.append(f"Referenciado por {ref_count} archivos")

        # +20 si es archivo de configuración
        if node.is_config:
            score += 20
            reasons.append("Archivo de configuración del proyecto o entorno")

        # +15 si tiene muchos imports salientes (alta acoplabilidad)
        outgoing = len(self.graph.internal_refs.get(node.relative_path, []))
        if outgoing >= 8:
            score += 15
            reasons.append(f"Alto acoplamiento — importa {outgoing} módulos internos")

        # +10 por tamaño (archivos grandes suelen ser nucleares)
        if node.size_bytes > 20_000:
            score += 10
            reasons.append("Archivo grande (>20KB) — posible módulo nuclear")

        if not reasons:
            reasons.append("Sin dependencias críticas detectadas")

        level = "low"
        if score >= 70:
            level = "critical"
        elif score >= 45:
            level = "high"
        elif score >= 20:
            level = "medium"

        return RiskAssessment(level=level, reasons=reasons, score=min(score, 100))