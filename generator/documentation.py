# generator/documentation.py
from analyzer.models import AnalysisResult
from analyzer.reader import FileNode
from utils.logger import get_logger

logger = get_logger(__name__)

RISK_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}


class DocumentationGenerator:
    def __init__(self, result: AnalysisResult):
        self.r = result

    def generate(self) -> dict:
        return {
            "summary": self._project_summary(),
            "file_tree": self._file_tree(),
            "modules": self._module_descriptions(),
            "dependencies": self._dependency_overview(),
            "system_flow": self._system_flow(),
            "critical_files": self._critical_files_section(),
            "risks": self._risk_section(),
            "onboarding": self._onboarding_guide(),
        }

    def _project_summary(self) -> str:
        s = self.r.stack
        entry_points = [f.relative_path for f in self.r.structure.files if f.is_entry_point]
        lines = [
            f"## {self.r.root_name}",
            f"**Lenguaje principal:** {s.primary_language}",
            f"**Tipo de proyecto:** {s.project_type.capitalize()}",
        ]
        if s.frameworks:
            lines.append(f"**Frameworks:** {', '.join(s.frameworks)}")
        if s.runtime:
            lines.append(f"**Runtime:** {s.runtime}")
        if s.package_manager:
            lines.append(f"**Package manager:** {s.package_manager}")
        if s.database_hints:
            lines.append(f"**Bases de datos detectadas:** {', '.join(s.database_hints)}")
        if s.api_hints:
            lines.append(f"**Patrones API:** {', '.join(s.api_hints)}")
        if entry_points:
            lines.append(f"**Puntos de entrada:** {', '.join(entry_points)}")
        lines.append(f"**Total archivos:** {self.r.structure.total_files}")
        lines.append(f"**Total directorios:** {self.r.structure.total_dirs}")
        return "\n".join(lines)

    def _file_tree(self) -> list[dict]:
        """Árbol de archivos como lista de nodos para el HTML."""
        nodes = []
        for f in sorted(self.r.structure.files, key=lambda x: x.relative_path):
            risk = self.r.risks.file_risks.get(f.relative_path)
            module = self.r.module_info.get(f.relative_path)
            nodes.append({
                "path": f.relative_path,
                "ext": f.extension,
                "size": f.size_bytes,
                "is_entry": f.is_entry_point,
                "is_config": f.is_config,
                "is_critical": f.is_critical,
                "risk_level": risk.level if risk else "low",
                "risk_score": risk.score if risk else 0,
                "classes": module.classes if module else [],
                "functions": module.functions[:8] if module else [],
                "docstring": module.docstring if module else None,
            })
        return nodes

    def _module_descriptions(self) -> list[dict]:
        mods = []
        for path, info in self.r.module_info.items():
            risk = self.r.risks.file_risks.get(path)
            mods.append({
                "path": path,
                "classes": info.classes,
                "functions": info.functions,
                "decorators": info.decorators,
                "docstring": info.docstring,
                "has_main_guard": info.has_main_guard,
                "complexity": info.complexity_score,
                "risk_level": risk.level if risk else "low",
                "risk_reasons": risk.reasons if risk else [],
            })
        mods.sort(key=lambda m: m["complexity"], reverse=True)
        return mods

    def _dependency_overview(self) -> dict:
        graph = self.r.graph
        all_external: dict[str, int] = {}
        for deps in graph.external_deps.values():
            for d in deps:
                all_external[d] = all_external.get(d, 0) + 1

        top_external = sorted(all_external.items(), key=lambda x: x[1], reverse=True)[:20]

        return {
            "most_referenced_files": graph.most_referenced[:10],
            "top_external_packages": top_external,
            "total_internal_edges": len(graph.edges),
            "isolated_files": [
                n for n in graph.nodes
                if not graph.internal_refs.get(n) and not any(e[1] == n for e in graph.edges)
            ][:10],
        }

    def _system_flow(self) -> list[str]:
        entries = [f.relative_path for f in self.r.structure.files if f.is_entry_point]
        flow = []
        for entry in entries[:3]:
            refs = self.r.graph.internal_refs.get(entry, [])
            flow.append(f"**{entry}** → {' → '.join(refs[:5])}" if refs else f"**{entry}** (sin imports internos detectados)")
        return flow

    def _critical_files_section(self) -> list[dict]:
        critical = []
        for path in self.r.risks.critical_files:
            risk = self.r.risks.file_risks[path]
            critical.append({
                "path": path,
                "score": risk.score,
                "reasons": risk.reasons,
            })
        for path in self.r.risks.high_risk_files:
            risk = self.r.risks.file_risks[path]
            critical.append({
                "path": path,
                "score": risk.score,
                "reasons": risk.reasons,
            })
        return sorted(critical, key=lambda x: x["score"], reverse=True)

    def _risk_section(self) -> list[dict]:
        result = []
        for path, risk in sorted(
            self.r.risks.file_risks.items(),
            key=lambda x: x[1].score,
            reverse=True
        )[:20]:
            result.append({
                "path": path,
                "level": risk.level,
                "score": risk.score,
                "reasons": risk.reasons,
                "emoji": RISK_EMOJI.get(risk.level, "⚪"),
            })
        return result

    def _onboarding_guide(self) -> list[str]:
        s = self.r.stack
        steps = ["## Guía para nuevos desarrolladores"]

        if s.runtime:
            steps.append(f"**1. Instalar runtime:** {s.runtime}")

        if s.package_manager:
            if "pip" in s.package_manager:
                steps.append("**2. Instalar dependencias:** `pip install -r requirements.txt`")
            elif "npm" in s.package_manager:
                steps.append("**2. Instalar dependencias:** `npm install`")
            elif "yarn" in s.package_manager:
                steps.append("**2. Instalar dependencias:** `yarn`")
            elif "cargo" in s.package_manager:
                steps.append("**2. Construir:** `cargo build`")

        entries = [f.relative_path for f in self.r.structure.files if f.is_entry_point]
        if entries:
            steps.append(f"**3. Punto de entrada principal:** `{entries[0]}`")

        if s.database_hints:
            steps.append(f"**4. Bases de datos:** Configura {', '.join(s.database_hints)} antes de correr el proyecto")

        configs = [f.relative_path for f in self.r.structure.files if f.is_config and ".env" in f.relative_path]
        if configs:
            steps.append(f"**5. Variables de entorno:** Copia `{configs[0]}` a `.env` y configura los valores")

        critical = self.r.risks.critical_files[:3]
        if critical:
            steps.append(f"**⚠ Archivos críticos:** Modifica con precaución: {', '.join(critical)}")

        return steps