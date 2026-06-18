import json
from analyzer.models import AnalysisResult
from utils.logger import get_logger

logger = get_logger(__name__)


class ArchitectureMapper:
    """Genera datos para el diagrama de arquitectura interactivo (D3.js force graph)."""

    RISK_COLORS = {
        "critical": "#E24B4A",
        "high": "#EF9F27",
        "medium": "#1D9E75",
        "low": "#888780",
    }
    EXT_COLORS = {
        ".py": "#3776AB",
        ".js": "#F7DF1E",
        ".ts": "#3178C6",
        ".jsx": "#61DAFB",
        ".tsx": "#61DAFB",
        ".vue": "#4FC08D",
        ".go": "#00ADD8",
        ".rs": "#CE422B",
        ".json": "#888",
        ".yml": "#CB171E",
        ".yaml": "#CB171E",
        ".md": "#555",
        ".env": "#EAD75F",
        ".html": "#E34F26",
        ".css": "#1572B6",
    }

    def __init__(self, result: AnalysisResult):
        self.r = result

    def build_graph_data(self) -> dict:
        nodes = []
        links = []
        node_index: dict[str, int] = {}

        # Construir nodos solo con archivos que tienen conexiones o son importantes
        important = set(self.r.risks.critical_files) | set(self.r.risks.high_risk_files)
        connected = set()
        for src, dst in self.r.graph.edges:
            connected.add(src)
            connected.add(dst)

        included = (important | connected) or {f.relative_path for f in self.r.structure.files[:60]}

        for f in self.r.structure.files:
            if f.relative_path not in included:
                continue
            risk = self.r.risks.file_risks.get(f.relative_path)
            idx = len(nodes)
            node_index[f.relative_path] = idx
            nodes.append({
                "id": f.relative_path,
                "label": f.path.name,
                "group": self._group_from_path(f.relative_path),
                "risk": risk.level if risk else "low",
                "score": risk.score if risk else 0,
                "color": self.EXT_COLORS.get(f.extension, "#888780"),
                "risk_color": self.RISK_COLORS.get(risk.level if risk else "low", "#888780"),
                "is_entry": f.is_entry_point,
                "is_config": f.is_config,
                "size": max(8, min(20, 8 + (risk.score if risk else 0) // 10)),
            })

        for src, dst in self.r.graph.edges:
            if src in node_index and dst in node_index:
                links.append({
                    "source": node_index[src],
                    "target": node_index[dst],
                    "value": 1,
                })

        return {"nodes": nodes, "links": links}

    def _group_from_path(self, rel_path: str) -> str:
        parts = rel_path.split("/")
        return parts[0] if len(parts) > 1 else "root"

    def build_tree_data(self) -> dict:
        """Árbol de directorios para el panel lateral."""
        tree: dict = {"name": self.r.root_name, "children": {}, "files": []}

        for f in self.r.structure.files:
            parts = f.relative_path.split("/")
            node = tree
            for part in parts[:-1]:
                node["children"].setdefault(part, {"name": part, "children": {}, "files": []})
                node = node["children"][part]
            risk = self.r.risks.file_risks.get(f.relative_path)
            node["files"].append({
                "name": parts[-1],
                "path": f.relative_path,
                "ext": f.extension,
                "risk": risk.level if risk else "low",
                "is_entry": f.is_entry_point,
                "is_config": f.is_config,
            })

        return self._dict_to_list(tree)

    def _dict_to_list(self, node: dict) -> dict:
        node["children"] = [self._dict_to_list(c) for c in node["children"].values()]
        return node