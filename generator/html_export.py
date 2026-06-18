# generator/html_export.py
import json
from pathlib import Path
from generator.architecture import ArchitectureMapper
from analyzer.models import AnalysisResult
from utils.logger import get_logger

logger = get_logger(__name__)


class HTMLExporter:
    def __init__(self, analysis: AnalysisResult, docs: dict):
        self.analysis = analysis
        self.docs = docs
        self.mapper = ArchitectureMapper(analysis)

    def export(self, output_path: str):
        graph_data = self.mapper.build_graph_data()
        tree_data = self.mapper.build_tree_data()
        html = self._render(graph_data, tree_data)
        Path(output_path).write_text(html, encoding="utf-8")

    def _render(self, graph_data: dict, tree_data: dict) -> str:
        stack = self.analysis.stack
        risks = self.docs["risks"]
        modules = self.docs["modules"]
        onboarding = self.docs["onboarding"]
        deps = self.docs["dependencies"]
        flow = self.docs["system_flow"]
        critical = self.docs["critical_files"]

        graph_json = json.dumps(graph_data)
        tree_json = json.dumps(tree_data)
        risks_json = json.dumps(risks)
        modules_json = json.dumps(modules)
        files_json = json.dumps(self.docs["file_tree"])
        deps_json = json.dumps(deps)

        languages_labels = json.dumps(list(stack.languages.keys()))
        languages_data = json.dumps(list(stack.languages.values()))

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self.analysis.root_name} — Arquitectura</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}

:root{{
  /* Core palette */
  --bg:#08090e;
  --bg1:#0c0e16;
  --bg2:#0f111a;
  --bg3:#13161f;
  --bg4:#181c28;
  --bg5:#1e2332;
  --border:#1e2436;
  --border2:#252d42;
  --border3:#2e3850;

  /* Text */
  --text:#e8eaf2;
  --text2:#8892a8;
  --text3:#4e5970;
  --text4:#2e3650;

  /* Accents */
  --indigo:#6c72f5;
  --indigo2:#8b90f8;
  --indigo3:#a8adfa;
  --indigo-glow:rgba(108,114,245,0.15);
  --indigo-glow2:rgba(108,114,245,0.08);

  /* Semantic */
  --red:#e05252;
  --red-bg:rgba(224,82,82,0.08);
  --red-border:rgba(224,82,82,0.2);
  --amber:#e8933a;
  --amber-bg:rgba(232,147,58,0.08);
  --amber-border:rgba(232,147,58,0.2);
  --green:#3dba8c;
  --green-bg:rgba(61,186,140,0.08);
  --green-border:rgba(61,186,140,0.2);
  --blue:#4a90d9;
  --blue-bg:rgba(74,144,217,0.08);
  --slate:#64748b;

  /* Typography */
  --font:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --mono:'JetBrains Mono','Fira Code',monospace;

  /* Geometry */
  --r:6px;
  --r2:10px;
  --r3:14px;
}}

/* ─── Reset & Base ──────────────────────────────────────────────────────── */
body{{
  font-family:var(--font);
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  overflow-x:hidden;
  font-size:13px;
  line-height:1.5;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}}
a{{color:var(--indigo2);text-decoration:none}}
a:hover{{color:var(--indigo3);text-decoration:underline}}
::selection{{background:var(--indigo-glow);color:var(--indigo3)}}

/* ─── Scrollbar ─────────────────────────────────────────────────────────── */
::-webkit-scrollbar{{width:4px;height:4px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:2px}}
::-webkit-scrollbar-thumb:hover{{background:var(--border3)}}

/* ─── Layout ────────────────────────────────────────────────────────────── */
.app{{
  display:grid;
  grid-template-columns:220px 1fr;
  grid-template-rows:52px 1fr;
  height:100vh;
  position:relative;
}}

/* Ambient background glow */
.app::before{{
  content:'';
  position:fixed;
  top:-200px;
  left:50%;
  transform:translateX(-50%);
  width:800px;
  height:400px;
  background:radial-gradient(ellipse,rgba(108,114,245,0.04) 0%,transparent 70%);
  pointer-events:none;
  z-index:0;
}}

/* ─── Topbar ────────────────────────────────────────────────────────────── */
.topbar{{
  grid-column:1/-1;
  display:flex;
  align-items:center;
  gap:0;
  padding:0;
  background:rgba(8,9,14,0.85);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
  z-index:100;
  position:relative;
}}

.topbar-logo{{
  display:flex;
  align-items:center;
  gap:10px;
  padding:0 16px;
  width:220px;
  border-right:1px solid var(--border);
  height:100%;
  flex-shrink:0;
}}

.logo-mark{{
  width:24px;height:24px;
  background:linear-gradient(135deg,var(--indigo) 0%,var(--indigo2) 100%);
  border-radius:6px;
  display:flex;align-items:center;justify-content:center;
  flex-shrink:0;
  box-shadow:0 0 12px rgba(108,114,245,0.3);
}}

.topbar-project{{
  display:flex;
  align-items:center;
  gap:8px;
  padding:0 16px;
  flex:1;
}}

.project-name{{
  font-size:13px;
  font-weight:500;
  color:var(--text);
  letter-spacing:-0.01em;
}}

.topbar-divider{{
  width:1px;
  height:16px;
  background:var(--border2);
}}

.chip{{
  display:inline-flex;
  align-items:center;
  padding:2px 7px;
  border-radius:4px;
  font-size:10px;
  font-weight:600;
  letter-spacing:0.02em;
  text-transform:uppercase;
}}

.chip-indigo{{background:var(--indigo-glow);color:var(--indigo2);border:1px solid rgba(108,114,245,0.25)}}
.chip-slate{{background:rgba(100,116,139,0.1);color:var(--text2);border:1px solid rgba(100,116,139,0.2)}}
.chip-red{{background:var(--red-bg);color:var(--red);border:1px solid var(--red-border)}}
.chip-amber{{background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-border)}}
.chip-green{{background:var(--green-bg);color:var(--green);border:1px solid var(--green-border)}}
.chip-blue{{background:var(--blue-bg);color:var(--blue);border:1px solid rgba(74,144,217,0.2)}}

/* Search */
.topbar-search{{
  margin-left:auto;
  padding:0 16px;
}}

.search-trigger{{
  display:flex;
  align-items:center;
  gap:8px;
  background:var(--bg3);
  border:1px solid var(--border2);
  border-radius:var(--r2);
  padding:6px 10px;
  width:220px;
  cursor:pointer;
  transition:all 0.15s;
}}
.search-trigger:hover{{border-color:var(--border3);background:var(--bg4)}}
.search-trigger input{{
  background:none;border:none;outline:none;
  color:var(--text);font-size:12px;width:100%;font-family:var(--font);
}}
.search-trigger input::placeholder{{color:var(--text3)}}
.search-trigger .kbd{{
  font-family:var(--mono);
  font-size:10px;
  color:var(--text3);
  background:var(--bg4);
  border:1px solid var(--border2);
  border-radius:3px;
  padding:0 4px;
  white-space:nowrap;
}}

/* ─── Sidebar ───────────────────────────────────────────────────────────── */
.sidebar{{
  background:var(--bg1);
  border-right:1px solid var(--border);
  overflow-y:auto;
  display:flex;
  flex-direction:column;
  position:relative;
  z-index:10;
}}

.sidebar-section{{
  padding:8px 8px 0;
}}
.sidebar-label{{
  font-size:10px;
  font-weight:600;
  color:var(--text4);
  text-transform:uppercase;
  letter-spacing:0.08em;
  padding:8px 8px 4px;
}}

.nav-item{{
  display:flex;
  align-items:center;
  gap:8px;
  padding:6px 8px;
  border-radius:var(--r);
  cursor:pointer;
  font-size:12px;
  font-weight:400;
  color:var(--text2);
  transition:all 0.12s;
  user-select:none;
  position:relative;
}}
.nav-item:hover{{
  background:var(--bg3);
  color:var(--text);
}}
.nav-item.active{{
  background:var(--indigo-glow2);
  color:var(--indigo3);
  border:1px solid rgba(108,114,245,0.12);
}}
.nav-item.active .nav-icon{{
  color:var(--indigo2);
}}
.nav-item.active::before{{
  content:'';
  position:absolute;
  left:0;top:50%;transform:translateY(-50%);
  width:2px;height:14px;
  background:var(--indigo);
  border-radius:0 2px 2px 0;
}}
.nav-icon{{
  width:14px;height:14px;
  opacity:0.6;
  flex-shrink:0;
  transition:opacity 0.12s;
}}
.nav-item:hover .nav-icon,.nav-item.active .nav-icon{{opacity:1}}

.nav-count{{
  margin-left:auto;
  font-size:10px;
  color:var(--text3);
  background:var(--bg4);
  border:1px solid var(--border);
  border-radius:3px;
  padding:0 5px;
  font-family:var(--mono);
}}

/* File tree */
.tree-section{{
  flex:1;
  overflow-y:auto;
  padding:8px;
  border-top:1px solid var(--border);
  margin-top:8px;
}}

.tree-node{{
  display:flex;align-items:center;gap:5px;
  padding:3px 6px;border-radius:5px;
  cursor:pointer;font-size:11px;color:var(--text2);
  transition:all 0.1s;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.tree-node:hover{{background:var(--bg3);color:var(--text)}}
.tree-node .dot{{width:5px;height:5px;border-radius:50%;flex-shrink:0}}
.tree-children{{padding-left:12px}}
.tree-folder{{
  font-size:11px;font-weight:500;color:var(--text);
  padding:3px 6px;cursor:pointer;
  display:flex;align-items:center;gap:5px;
  transition:all 0.1s;
}}
.tree-folder:hover{{background:var(--bg3);border-radius:5px}}

/* ─── Main ──────────────────────────────────────────────────────────────── */
.main{{
  overflow-y:auto;
  background:var(--bg);
  position:relative;
}}

.panel{{display:none;padding:24px;max-width:1100px;animation:fadeUp 0.2s ease-out}}
.panel.active{{display:block}}

@keyframes fadeUp{{
  from{{opacity:0;transform:translateY(6px)}}
  to{{opacity:1;transform:translateY(0)}}
}}

/* ─── Page header ───────────────────────────────────────────────────────── */
.page-header{{
  margin-bottom:24px;
}}
.page-title{{
  font-size:18px;
  font-weight:600;
  color:var(--text);
  letter-spacing:-0.025em;
  line-height:1.2;
}}
.page-subtitle{{
  font-size:12px;
  color:var(--text3);
  margin-top:4px;
}}

/* ─── Cards ─────────────────────────────────────────────────────────────── */
.card{{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:var(--r3);
  padding:20px;
  margin-bottom:14px;
  position:relative;
  overflow:hidden;
  transition:border-color 0.15s;
}}
.card:hover{{border-color:var(--border2)}}

.card-header{{
  display:flex;align-items:center;
  justify-content:space-between;
  margin-bottom:16px;
}}
.card-title{{
  font-size:12px;
  font-weight:600;
  color:var(--text2);
  text-transform:uppercase;
  letter-spacing:0.06em;
}}

/* ─── Stat grid ─────────────────────────────────────────────────────────── */
.stat-grid{{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
  gap:10px;
  margin-bottom:16px;
}}

.stat{{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:var(--r2);
  padding:16px;
  position:relative;
  overflow:hidden;
  transition:all 0.15s;
  cursor:default;
}}
.stat:hover{{border-color:var(--border2);background:var(--bg3)}}
.stat::after{{
  content:'';
  position:absolute;
  top:0;left:0;right:0;
  height:1px;
  background:linear-gradient(90deg,transparent,var(--indigo-glow),transparent);
}}
.stat .value{{
  font-size:26px;
  font-weight:600;
  color:var(--text);
  letter-spacing:-0.04em;
  font-variant-numeric:tabular-nums;
  line-height:1;
  margin-bottom:6px;
}}
.stat .label{{
  font-size:11px;
  color:var(--text3);
  font-weight:400;
  letter-spacing:0.01em;
}}
.stat .trend{{
  position:absolute;
  top:12px;right:12px;
  font-size:10px;
  color:var(--text4);
}}

/* ─── Charts row ────────────────────────────────────────────────────────── */
.charts-row{{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:12px;
  margin-bottom:14px;
}}
.chart-card{{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:var(--r3);
  padding:18px;
}}
.chart-card canvas{{max-height:180px}}
.chart-label{{
  font-size:11px;
  font-weight:600;
  color:var(--text3);
  text-transform:uppercase;
  letter-spacing:0.06em;
  margin-bottom:12px;
}}

/* ─── Stack info ────────────────────────────────────────────────────────── */
.stack-row{{
  display:flex;align-items:flex-start;gap:12px;
  padding:8px 0;
  border-bottom:1px solid var(--border);
}}
.stack-row:last-child{{border-bottom:none}}
.stack-row-label{{
  min-width:140px;
  font-size:11px;
  color:var(--text3);
  padding-top:2px;
}}

/* ─── Graph ─────────────────────────────────────────────────────────────── */
#graph-container{{
  width:100%;
  height:calc(100vh - 52px - 48px - 100px);
  min-height:500px;
  background:var(--bg2);
  border-radius:var(--r3);
  border:1px solid var(--border);
  overflow:hidden;
  position:relative;
}}

.graph-controls{{
  display:flex;gap:8px;margin-bottom:10px;align-items:center;
}}
.graph-btn{{
  display:flex;align-items:center;gap:6px;
  padding:5px 10px;
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:var(--r);
  color:var(--text2);
  font-size:11px;
  cursor:pointer;
  transition:all 0.12s;
  font-family:var(--font);
}}
.graph-btn:hover{{border-color:var(--border2);color:var(--text);background:var(--bg3)}}
.graph-btn.active{{background:var(--indigo-glow2);color:var(--indigo2);border-color:rgba(108,114,245,0.3)}}

.graph-legend{{display:flex;gap:14px;flex-wrap:wrap;margin-left:auto}}
.legend-item{{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--text3)}}
.legend-dot{{width:7px;height:7px;border-radius:50%}}

/* ─── Module list ───────────────────────────────────────────────────────── */
.module-search{{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:var(--r2);
  padding:10px 14px;
  margin-bottom:14px;
  position:relative;
}}
.module-search input{{
  width:100%;background:none;border:none;outline:none;
  color:var(--text);font-size:13px;font-family:var(--font);
}}
.module-search input::placeholder{{color:var(--text3)}}

.module-item{{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:var(--r2);
  padding:14px;
  margin-bottom:8px;
  transition:all 0.12s;
  position:relative;
}}
.module-item:hover{{border-color:var(--border2);background:var(--bg3)}}
.module-item-header{{
  display:flex;align-items:center;gap:8px;margin-bottom:8px;
}}
.module-path{{
  font-family:var(--mono);
  font-size:11px;
  color:var(--indigo2);
  flex:1;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}}
.module-desc{{
  font-size:11px;
  color:var(--text3);
  margin-top:6px;
  font-style:italic;
  line-height:1.5;
}}
.fn-list{{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}}
.fn-chip{{
  background:var(--bg);
  border:1px solid var(--border2);
  border-radius:4px;
  padding:1px 7px;
  font-family:var(--mono);
  font-size:10px;
  color:var(--text2);
  transition:all 0.1s;
}}
.fn-chip:hover{{border-color:var(--indigo);color:var(--indigo2)}}

.meta-tags{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px}}
.tag{{
  display:inline-flex;align-items:center;
  padding:1px 6px;border-radius:3px;
  font-size:10px;font-weight:500;
}}
.tag-class{{background:rgba(232,147,58,0.08);color:var(--amber);border:1px solid var(--amber-border)}}
.tag-deco{{background:rgba(100,116,139,0.08);color:var(--slate);border:1px solid rgba(100,116,139,0.15)}}
.tag-entry{{background:var(--green-bg);color:var(--green);border:1px solid var(--green-border)}}

/* ─── Risk badges ───────────────────────────────────────────────────────── */
.risk{{
  display:inline-flex;align-items:center;gap:4px;
  padding:2px 7px;border-radius:4px;
  font-size:10px;font-weight:600;
  letter-spacing:0.02em;
  text-transform:uppercase;
}}
.risk-critical{{background:var(--red-bg);color:var(--red);border:1px solid var(--red-border)}}
.risk-high{{background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-border)}}
.risk-medium{{background:var(--green-bg);color:var(--green);border:1px solid var(--green-border)}}
.risk-low{{background:rgba(100,116,139,0.08);color:var(--slate);border:1px solid rgba(100,116,139,0.15)}}

/* ─── Risk panel ────────────────────────────────────────────────────────── */
.risk-item{{
  display:flex;align-items:flex-start;gap:14px;
  padding:14px;
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:var(--r2);
  margin-bottom:8px;
  transition:all 0.12s;
  cursor:pointer;
}}
.risk-item:hover{{border-color:var(--border2);background:var(--bg3)}}
.risk-item-left{{
  display:flex;flex-direction:column;align-items:center;gap:6px;
  min-width:52px;
}}
.risk-score{{
  font-size:22px;
  font-weight:700;
  letter-spacing:-0.04em;
  line-height:1;
  font-variant-numeric:tabular-nums;
}}
.risk-score.critical{{color:var(--red)}}
.risk-score.high{{color:var(--amber)}}
.risk-score.medium{{color:var(--green)}}
.risk-score.low{{color:var(--slate)}}
.risk-item-path{{
  font-family:var(--mono);font-size:11px;color:var(--text);
  margin-bottom:4px;
  word-break:break-all;
}}
.risk-reasons{{
  font-size:11px;color:var(--text3);
  line-height:1.6;
}}

/* ─── Deps ──────────────────────────────────────────────────────────────── */
.dep-row{{
  display:flex;align-items:center;gap:10px;
  padding:9px 0;border-bottom:1px solid var(--border);
}}
.dep-row:last-child{{border-bottom:none}}
.dep-name{{font-family:var(--mono);font-size:11px;color:var(--indigo2);flex:1}}
.dep-bar{{
  width:80px;height:3px;
  background:var(--bg4);
  border-radius:2px;
  overflow:hidden;
}}
.dep-bar-fill{{height:100%;background:var(--indigo);border-radius:2px;transition:width 0.6s ease}}
.dep-count{{font-size:10px;color:var(--text3);font-variant-numeric:tabular-nums;min-width:30px;text-align:right}}

/* ─── Onboarding ────────────────────────────────────────────────────────── */
.step{{
  display:flex;gap:14px;
  padding:14px 0;
  border-bottom:1px solid var(--border);
}}
.step:last-child{{border-bottom:none}}
.step-num{{
  width:22px;height:22px;
  background:var(--indigo-glow);
  border:1px solid rgba(108,114,245,0.25);
  border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:600;color:var(--indigo2);
  flex-shrink:0;
  margin-top:1px;
}}
.step-text{{font-size:12px;color:var(--text2);line-height:1.6}}
code{{
  font-family:var(--mono);
  background:var(--bg4);
  border:1px solid var(--border2);
  padding:0 5px;border-radius:3px;
  font-size:10px;color:var(--indigo3);
}}

/* ─── Flow ──────────────────────────────────────────────────────────────── */
.flow-line{{
  font-family:var(--mono);font-size:11px;color:var(--text2);
  padding:8px 12px;
  background:var(--bg3);
  border-radius:var(--r);
  margin-bottom:6px;
  border-left:2px solid var(--indigo);
  transition:all 0.12s;
}}
.flow-line:hover{{background:var(--bg4);color:var(--text)}}

/* ─── Critical files ────────────────────────────────────────────────────── */
.critical-item{{
  display:flex;align-items:flex-start;gap:12px;
  padding:10px 12px;
  background:var(--bg3);
  border-radius:var(--r);
  margin-bottom:6px;
  border:1px solid transparent;
  transition:all 0.12s;
}}
.critical-item:hover{{border-color:var(--border2)}}

/* ─── Search ────────────────────────────────────────────────────────────── */
.search-overlay{{
  position:fixed;top:0;left:0;right:0;bottom:0;
  background:rgba(0,0,0,0.6);
  backdrop-filter:blur(4px);
  z-index:999;
  display:none;
  align-items:flex-start;justify-content:center;
  padding-top:100px;
}}
.search-overlay.open{{display:flex}}
.search-modal{{
  width:580px;
  background:var(--bg2);
  border:1px solid var(--border2);
  border-radius:var(--r3);
  overflow:hidden;
  box-shadow:0 32px 64px rgba(0,0,0,0.5),0 0 0 1px var(--border);
  animation:searchIn 0.18s cubic-bezier(0.16,1,0.3,1);
}}
@keyframes searchIn{{
  from{{opacity:0;transform:translateY(-8px) scale(0.98)}}
  to{{opacity:1;transform:translateY(0) scale(1)}}
}}
.search-modal-input{{
  display:flex;align-items:center;gap:10px;
  padding:14px 16px;
  border-bottom:1px solid var(--border);
}}
.search-modal-input input{{
  flex:1;background:none;border:none;outline:none;
  color:var(--text);font-size:14px;font-family:var(--font);
}}
.search-modal-input input::placeholder{{color:var(--text3)}}
.search-results{{max-height:400px;overflow-y:auto}}
.search-result{{
  display:flex;flex-direction:column;
  padding:10px 16px;
  cursor:pointer;
  transition:background 0.1s;
  border-bottom:1px solid var(--border);
}}
.search-result:last-child{{border-bottom:none}}
.search-result:hover,.search-result.focused{{background:var(--bg3)}}
.search-result .sr-path{{
  font-family:var(--mono);font-size:11px;color:var(--indigo2);
  margin-bottom:2px;
}}
.search-result .sr-detail{{font-size:11px;color:var(--text3)}}
.search-empty{{
  padding:32px;text-align:center;
  color:var(--text3);font-size:12px;
}}

/* ─── Tooltip ───────────────────────────────────────────────────────────── */
#tooltip{{
  position:fixed;pointer-events:none;
  background:var(--bg2);
  border:1px solid var(--border2);
  border-radius:var(--r2);
  padding:10px 14px;font-size:11px;max-width:260px;
  z-index:200;display:none;
  box-shadow:0 12px 32px rgba(0,0,0,0.5);
}}
#tooltip .t-path{{
  font-family:var(--mono);color:var(--indigo2);
  margin-bottom:6px;font-size:10px;
  word-break:break-all;
}}
#tooltip .t-row{{
  display:flex;justify-content:space-between;gap:16px;
  color:var(--text2);margin-top:3px;
}}
#tooltip .t-key{{color:var(--text3)}}

/* ─── Inline search panel (fallback) ───────────────────────────────────── */
#panel-search-panel .search-input-wrap{{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:var(--r2);padding:10px 14px;
  margin-bottom:14px;
}}
#panel-search-panel .search-input-wrap input{{
  width:100%;background:none;border:none;outline:none;
  color:var(--text);font-size:13px;font-family:var(--font);
}}

/* ─── Micro-interactions ────────────────────────────────────────────────── */
.reveal{{
  opacity:0;transform:translateY(8px);
  animation:reveal 0.25s ease-out forwards;
}}
@keyframes reveal{{
  to{{opacity:1;transform:translateY(0)}}
}}

/* Stagger children */
.stagger>*:nth-child(1){{animation-delay:0.02s}}
.stagger>*:nth-child(2){{animation-delay:0.04s}}
.stagger>*:nth-child(3){{animation-delay:0.06s}}
.stagger>*:nth-child(4){{animation-delay:0.08s}}
.stagger>*:nth-child(5){{animation-delay:0.10s}}
.stagger>*:nth-child(6){{animation-delay:0.12s}}

/* Pulse dot for "live" feel */
.pulse-dot{{
  width:6px;height:6px;border-radius:50%;background:var(--green);
  animation:pulse-dot 2s ease-in-out infinite;
}}
@keyframes pulse-dot{{
  0%,100%{{opacity:1;box-shadow:0 0 0 0 rgba(61,186,140,0.3)}}
  50%{{opacity:0.7;box-shadow:0 0 0 4px rgba(61,186,140,0)}}
}}

/* ─── Empty states ──────────────────────────────────────────────────────── */
.empty-state{{
  padding:48px 24px;text-align:center;
}}
.empty-icon{{
  width:36px;height:36px;
  margin:0 auto 12px;
  opacity:0.2;
}}
.empty-title{{font-size:13px;font-weight:500;color:var(--text2);margin-bottom:6px}}
.empty-desc{{font-size:11px;color:var(--text3)}}

/* ─── Graph SVG styles ──────────────────────────────────────────────────── */
.node-group circle{{cursor:pointer;transition:all 0.1s}}
.node-group:hover circle{{filter:brightness(1.15)}}
.link-line{{transition:stroke-opacity 0.15s}}
</style>
</head>
<body>
<div class="app">

<!-- ═══ TOPBAR ════════════════════════════════════════════════════════════ -->
<header class="topbar">
  <div class="topbar-logo">
    <div class="logo-mark">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <path d="M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2z" fill="white" opacity="0.9"/>
        <path d="M11.5 9v6M9 11.5h6" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </div>
    <span style="font-size:12px;font-weight:600;color:var(--text);letter-spacing:-0.01em">ArchViz</span>
  </div>

  <div class="topbar-project">
    <span class="project-name">{self.analysis.root_name}</span>
    <div class="topbar-divider"></div>
    <span class="chip chip-indigo">{stack.primary_language}</span>
    <span class="chip chip-slate">{stack.project_type}</span>
    <div style="display:flex;align-items:center;gap:6px;margin-left:8px">
      <div class="pulse-dot"></div>
      <span style="font-size:10px;color:var(--text3)">Analysed</span>
    </div>
  </div>

  <div class="topbar-search">
    <div class="search-trigger" onclick="openSearch()">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input type="text" placeholder="Quick search..." readonly id="topbar-search-fake">
      <span class="kbd">⌘K</span>
    </div>
  </div>
</header>

<!-- ═══ SIDEBAR ══════════════════════════════════════════════════════════ -->
<aside class="sidebar">
  <div class="sidebar-section">
    <div class="sidebar-label">Navigation</div>
    <nav>
      <div class="nav-item active" onclick="showPanel('overview')">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        Overview
      </div>
      <div class="nav-item" onclick="showPanel('graph')">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M12 7v5m-5.5 5.5 5.5-3 5.5 3"/></svg>
        Architecture
      </div>
      <div class="nav-item" onclick="showPanel('modules')" id="nav-modules">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="12" y2="16"/></svg>
        Modules
        <span class="nav-count" id="nav-modules-count">—</span>
      </div>
      <div class="nav-item" onclick="showPanel('risks')" id="nav-risks">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        Risk Analysis
      </div>
      <div class="nav-item" onclick="showPanel('deps')">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><path d="M6 9v12"/></svg>
        Dependencies
      </div>
      <div class="nav-item" onclick="showPanel('onboarding')">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
        Onboarding
      </div>
    </nav>
  </div>

  <div class="tree-section">
    <div class="sidebar-label">File Tree</div>
    <div id="file-tree"></div>
  </div>
</aside>

<!-- ═══ MAIN ══════════════════════════════════════════════════════════════ -->
<main class="main">

<!-- ── OVERVIEW ──────────────────────────────────────────────────────────── -->
<div id="panel-overview" class="panel active">
  <div class="page-header">
    <div class="page-title">{self.analysis.root_name}</div>
    <div class="page-subtitle">Architecture analysis · <span id="overview-date"></span></div>
  </div>

  <div class="stat-grid stagger" id="stat-grid"></div>

  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-label">Languages</div>
      <canvas id="lang-chart"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-label">Risk Distribution</div>
      <canvas id="risk-chart"></canvas>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">Technology Stack</span>
    </div>
    <div id="stack-info"></div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">System Flow</span>
    </div>
    <div id="flow-info"></div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">Critical Files</span>
      <span class="chip chip-red" id="critical-count-chip"></span>
    </div>
    <div id="critical-info"></div>
  </div>
</div>

<!-- ── ARCHITECTURE GRAPH ─────────────────────────────────────────────────── -->
<div id="panel-graph" class="panel">
  <div class="page-header">
    <div class="page-title">Architecture Graph</div>
    <div class="page-subtitle">Module dependency map · drag to explore · scroll to zoom</div>
  </div>
  <div class="graph-controls">
    <button class="graph-btn active" id="btn-force" onclick="setLayout('force')">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M3 12h4m10 0h4M12 3v4m0 10v4"/></svg>
      Force
    </button>
    <button class="graph-btn" id="btn-focus" onclick="setFocusMode()">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      Focus
    </button>
    <div class="graph-legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--red)"></div>Critical</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--amber)"></div>High</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div>Medium</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--slate)"></div>Low</div>
    </div>
  </div>
  <div id="graph-container"></div>
</div>

<!-- ── MODULES ────────────────────────────────────────────────────────────── -->
<div id="panel-modules" class="panel">
  <div class="page-header">
    <div class="page-title">Modules</div>
    <div class="page-subtitle" id="modules-subtitle">All Python modules</div>
  </div>
  <div class="module-search card" style="padding:0;margin-bottom:14px;display:flex;align-items:center;gap:8px;padding:10px 14px">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2" style="flex-shrink:0"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <input type="text" id="module-filter" placeholder="Filter by path, class, function…" style="flex:1;background:none;border:none;outline:none;color:var(--text);font-size:12px;font-family:var(--font)">
  </div>
  <div id="modules-list"></div>
</div>

<!-- ── RISKS ──────────────────────────────────────────────────────────────── -->
<div id="panel-risks" class="panel">
  <div class="page-header">
    <div class="page-title">Risk Analysis</div>
    <div class="page-subtitle">Files with highest cascade impact if modified incorrectly</div>
  </div>
  <div id="risks-list"></div>
</div>

<!-- ── DEPENDENCIES ──────────────────────────────────────────────────────── -->
<div id="panel-deps" class="panel">
  <div class="page-header">
    <div class="page-title">Dependencies</div>
    <div class="page-subtitle">External packages and internal references</div>
  </div>
  <div class="card">
    <div class="card-header"><span class="card-title">External Packages</span></div>
    <div id="ext-deps"></div>
  </div>
  <div class="card">
    <div class="card-header"><span class="card-title">Most Referenced Internally</span></div>
    <div id="int-refs"></div>
  </div>
</div>

<!-- ── ONBOARDING ────────────────────────────────────────────────────────── -->
<div id="panel-onboarding" class="panel">
  <div class="page-header">
    <div class="page-title">Onboarding Guide</div>
    <div class="page-subtitle">Getting started for new contributors</div>
  </div>
  <div class="card">
    <div id="onboarding-steps"></div>
  </div>
</div>

<!-- ── SEARCH FALLBACK PANEL ─────────────────────────────────────────────── -->
<div id="panel-search-panel" class="panel">
  <div class="page-header">
    <div class="page-title">Search</div>
  </div>
  <div class="card" style="padding:0">
    <div style="display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--border)">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input type="text" id="search-main" placeholder="Search files, functions, classes…" style="flex:1;background:none;border:none;outline:none;color:var(--text);font-size:13px;font-family:var(--font)">
    </div>
    <div id="search-results"></div>
  </div>
</div>

</main>
</div>

<!-- ═══ SEARCH OVERLAY ════════════════════════════════════════════════════ -->
<div class="search-overlay" id="search-overlay" onclick="closeSearch(event)">
  <div class="search-modal" id="search-modal">
    <div class="search-modal-input">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input type="text" id="search-overlay-input" placeholder="Search files, functions, classes, decorators…" autofocus>
      <span class="kbd" style="cursor:pointer" onclick="closeSearch()">Esc</span>
    </div>
    <div class="search-results" id="search-overlay-results">
      <div class="search-empty">Type to search across the entire project</div>
    </div>
  </div>
</div>

<!-- ═══ TOOLTIP ══════════════════════════════════════════════════════════ -->
<div id="tooltip"></div>

<script>
/* ── Data ──────────────────────────────────────────────────────────────── */
const GRAPH_DATA = {graph_json};
const TREE_DATA = {tree_json};
const RISKS_DATA = {risks_json};
const MODULES_DATA = {modules_json};
const FILES_DATA = {files_json};
const DEPS_DATA = {deps_json};
const LANG_LABELS = {languages_labels};
const LANG_DATA = {languages_data};
const ONBOARDING = {json.dumps(onboarding)};
const FLOW_DATA = {json.dumps(flow)};
const CRITICAL_DATA = {json.dumps(critical)};
const STACK = {{
  primary: {json.dumps(stack.primary_language)},
  frameworks: {json.dumps(stack.frameworks)},
  runtime: {json.dumps(stack.runtime)},
  pkg_mgr: {json.dumps(stack.package_manager)},
  dbs: {json.dumps(stack.database_hints)},
  apis: {json.dumps(stack.api_hints)},
  type: {json.dumps(stack.project_type)},
  test_fw: {json.dumps(stack.test_frameworks)},
  total_files: {self.analysis.structure.total_files},
  total_dirs: {self.analysis.structure.total_dirs},
  internal_edges: {json.dumps(deps["total_internal_edges"])},
}};

/* ── Panel navigation ──────────────────────────────────────────────────── */
function showPanel(id) {{
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const panel = document.getElementById('panel-' + id);
  if (panel) panel.classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => {{
    if (n.getAttribute('onclick') && n.getAttribute('onclick').includes("'" + id + "'"))
      n.classList.add('active');
  }});
  if (id === 'graph') setTimeout(initGraph, 50);
}}

/* ── Stats ─────────────────────────────────────────────────────────────── */
function initStats() {{
  document.getElementById('overview-date').textContent = new Date().toLocaleDateString('en-US', {{
    year:'numeric',month:'long',day:'numeric'
  }});

  const riskCounts = {{critical:0,high:0,medium:0,low:0}};
  FILES_DATA.forEach(f => riskCounts[f.risk_level] = (riskCounts[f.risk_level]||0)+1);

  const stats = [
    {{ value: STACK.total_files, label: 'Total Files', sub: 'in project' }},
    {{ value: STACK.total_dirs, label: 'Directories', sub: 'tree depth' }},
    {{ value: STACK.internal_edges, label: 'Connections', sub: 'internal edges' }},
    {{ value: MODULES_DATA.length, label: 'Modules', sub: 'Python files' }},
    {{ value: CRITICAL_DATA.length, label: 'Critical', sub: 'files flagged' }},
    {{ value: riskCounts.critical + riskCounts.high, label: 'High Risk', sub: 'needs attention' }},
  ];
  document.getElementById('stat-grid').innerHTML = stats.map((s,i) =>
    `<div class="stat reveal" style="animation-delay:${{i*0.04}}s">
       <div class="value">${{s.value}}</div>
       <div class="label">${{s.label}}</div>
     </div>`
  ).join('');

  document.getElementById('nav-modules-count').textContent = MODULES_DATA.length;
  document.getElementById('critical-count-chip').textContent = CRITICAL_DATA.length + ' files';
}}

/* ── Charts ────────────────────────────────────────────────────────────── */
function initCharts() {{
  Chart.defaults.color = '#4e5970';
  Chart.defaults.borderColor = '#1e2436';
  Chart.defaults.font.family = 'Inter, sans-serif';
  Chart.defaults.font.size = 11;

  new Chart(document.getElementById('lang-chart'), {{
    type: 'doughnut',
    data: {{
      labels: LANG_LABELS,
      datasets: [{{
        data: LANG_DATA,
        backgroundColor: ['#6c72f5','#3dba8c','#e8933a','#4a90d9','#e05252','#8b90f8'],
        borderColor: '#0f111a',
        borderWidth: 2,
        hoverBorderColor: '#13161f',
      }}]
    }},
    options: {{
      responsive:true,cutout:'70%',
      plugins:{{
        legend:{{
          position:'right',
          labels:{{boxWidth:8,boxHeight:8,borderRadius:2,padding:12,color:'#8892a8',font:{{size:11}}}}
        }},
        tooltip:{{
          backgroundColor:'#13161f',
          borderColor:'#1e2436',
          borderWidth:1,
          titleColor:'#e8eaf2',
          bodyColor:'#8892a8',
          padding:10,
        }}
      }},
      animation:{{duration:600,easing:'easeOutCubic'}},
    }},
  }});

  const riskCounts = {{critical:0,high:0,medium:0,low:0}};
  FILES_DATA.forEach(f => riskCounts[f.risk_level] = (riskCounts[f.risk_level]||0)+1);
  new Chart(document.getElementById('risk-chart'), {{
    type: 'bar',
    data: {{
      labels: ['Critical','High','Medium','Low'],
      datasets: [{{
        data: [riskCounts.critical,riskCounts.high,riskCounts.medium,riskCounts.low],
        backgroundColor: ['rgba(224,82,82,0.7)','rgba(232,147,58,0.7)','rgba(61,186,140,0.7)','rgba(100,116,139,0.5)'],
        borderColor: ['#e05252','#e8933a','#3dba8c','#64748b'],
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false,
      }}]
    }},
    options: {{
      responsive:true,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          backgroundColor:'#13161f',
          borderColor:'#1e2436',borderWidth:1,
          titleColor:'#e8eaf2',bodyColor:'#8892a8',padding:10,
        }}
      }},
      scales:{{
        x:{{ticks:{{color:'#4e5970'}},grid:{{color:'#1e2436',lineWidth:0.5}}}},
        y:{{ticks:{{color:'#4e5970'}},grid:{{color:'#1e2436',lineWidth:0.5}},beginAtZero:true}},
      }},
      animation:{{duration:600,easing:'easeOutCubic'}},
    }},
  }});
}}

/* ── Stack ─────────────────────────────────────────────────────────────── */
function initStack() {{
  const el = document.getElementById('stack-info');
  const rows = [
    ['Frameworks', STACK.frameworks, 'chip-indigo'],
    ['Runtime', STACK.runtime ? [STACK.runtime] : [], 'chip-slate'],
    ['Package Manager', STACK.pkg_mgr ? [STACK.pkg_mgr] : [], 'chip-slate'],
    ['Databases', STACK.dbs, 'chip-blue'],
    ['APIs Detected', STACK.apis, 'chip-slate'],
    ['Test Frameworks', STACK.test_fw, 'chip-slate'],
  ].filter(([,items]) => items && items.length);

  if (!rows.length) {{
    el.innerHTML = '<div class="empty-state"><div class="empty-title">No stack info detected</div></div>';
    return;
  }}
  el.innerHTML = rows.map(([label, items, cls]) =>
    `<div class="stack-row">
       <span class="stack-row-label">${{label}}</span>
       <div style="display:flex;flex-wrap:wrap;gap:5px">
         ${{items.map(i=>`<span class="chip ${{cls}}">${{i}}</span>`).join('')}}
       </div>
     </div>`
  ).join('');
}}

/* ── Flow ──────────────────────────────────────────────────────────────── */
function initFlow() {{
  const el = document.getElementById('flow-info');
  if (!FLOW_DATA.length) {{
    el.innerHTML = '<div class="empty-state"><div class="empty-title">No internal flows detected</div></div>';
    return;
  }}
  el.innerHTML = FLOW_DATA.map(f => `<div class="flow-line">${{f}}</div>`).join('');
}}

/* ── Critical ──────────────────────────────────────────────────────────── */
function initCritical() {{
  const el = document.getElementById('critical-info');
  if (!CRITICAL_DATA.length) {{
    el.innerHTML = '<div class="empty-state"><div class="empty-title">No critical files flagged</div></div>';
    return;
  }}
  el.innerHTML = CRITICAL_DATA.slice(0,8).map(f => {{
    const level = f.score >= 70 ? 'critical' : 'high';
    return `<div class="critical-item">
      <span class="risk risk-${{level}}" style="min-width:40px;justify-content:center">${{f.score}}</span>
      <div style="flex:1;min-width:0">
        <div style="font-family:var(--mono);font-size:11px;color:var(--indigo2);margin-bottom:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{f.path}}</div>
        <div style="font-size:10px;color:var(--text3)">${{f.reasons.join(' · ')}}</div>
      </div>
    </div>`;
  }}).join('');
}}

/* ── File tree ─────────────────────────────────────────────────────────── */
const RISK_COLORS = {{critical:'#e05252',high:'#e8933a',medium:'#3dba8c',low:'#4e5970'}};
function renderTree(node, container) {{
  if (node.children && node.children.length) {{
    node.children.forEach(child => {{
      const folder = document.createElement('div');
      folder.className = 'tree-folder';
      folder.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg><span style="color:var(--text2)">${{child.name}}</span>`;
      const children = document.createElement('div');
      children.className = 'tree-children';
      folder.onclick = e => {{ e.stopPropagation(); children.style.display = children.style.display==='none' ? '' : 'none'; }};
      container.appendChild(folder);
      renderTree(child, children);
      container.appendChild(children);
    }});
  }}
  if (node.files) {{
    node.files.forEach(f => {{
      const item = document.createElement('div');
      item.className = 'tree-node';
      const color = RISK_COLORS[f.risk] || '#4e5970';
      item.innerHTML = `<span class="dot" style="background:${{color}}"></span><span style="overflow:hidden;text-overflow:ellipsis">${{f.name}}</span>${{f.is_entry ? '<span style="margin-left:auto;font-size:9px;color:var(--green)">●</span>' : ''}}`;
      item.title = f.path;
      item.onclick = () => showFileDetail(f.path);
      container.appendChild(item);
    }});
  }}
}}

function showFileDetail(path) {{
  showPanel('modules');
  setTimeout(() => {{
    const el = document.querySelector(`[data-path="${{path}}"]`);
    if (el) el.scrollIntoView({{behavior:'smooth',block:'center'}});
  }}, 150);
}}

/* ── Modules ───────────────────────────────────────────────────────────── */
function initModules() {{
  const container = document.getElementById('modules-list');
  const subtitle = document.getElementById('modules-subtitle');
  function render(filter) {{
    const filtered = MODULES_DATA.filter(m =>
      !filter ||
      m.path.toLowerCase().includes(filter) ||
      m.functions.some(fn => fn.toLowerCase().includes(filter)) ||
      m.classes.some(c => c.toLowerCase().includes(filter))
    );
    subtitle.textContent = filter ? `${{filtered.length}} of ${{MODULES_DATA.length}} modules` : `${{MODULES_DATA.length}} Python modules`;
    if (!filtered.length) {{
      container.innerHTML = `<div class="empty-state">
        <div class="empty-title">No modules match "${{filter}}"</div>
        <div class="empty-desc">Try a different path or function name</div>
      </div>`;
      return;
    }}
    container.innerHTML = filtered.slice(0, 100).map(m => `
      <div class="module-item" data-path="${{m.path}}">
        <div class="module-item-header">
          <span class="module-path">${{m.path}}</span>
          <span class="risk risk-${{m.risk_level}}">${{m.risk_level}}</span>
          ${{m.has_main_guard ? '<span class="tag tag-entry">__main__</span>' : ''}}
        </div>
        ${{m.classes.length || m.decorators.length ? `<div class="meta-tags">
          ${{m.classes.map(c => `<span class="tag tag-class">class ${{c}}</span>`).join('')}}
          ${{m.decorators.map(d => `<span class="tag tag-deco">@${{d}}</span>`).join('')}}
        </div>` : ''}}
        ${{m.docstring ? `<div class="module-desc">"${{m.docstring.slice(0,120)}}${{m.docstring.length>120?'…':''}}"</div>` : ''}}
        ${{m.functions.length ? `<div class="fn-list">
          ${{m.functions.slice(0,14).map(fn => `<span class="fn-chip">${{fn}}()</span>`).join('')}}
          ${{m.functions.length>14 ? `<span class="fn-chip" style="color:var(--text3)">+${{m.functions.length-14}}</span>` : ''}}
        </div>` : ''}}
        ${{m.risk_reasons.length ? `<div style="font-size:10px;color:var(--text4);margin-top:6px">${{m.risk_reasons.join(' · ')}}</div>` : ''}}
      </div>
    `).join('');
  }}
  render('');
  document.getElementById('module-filter').addEventListener('input', e => render(e.target.value.toLowerCase().trim()));
}}

/* ── Risks ─────────────────────────────────────────────────────────────── */
function initRisks() {{
  const el = document.getElementById('risks-list');
  if (!RISKS_DATA.length) {{
    el.innerHTML = `<div class="empty-state">
      <div class="empty-title">No risks detected</div>
      <div class="empty-desc">The codebase appears to be in good shape</div>
    </div>`;
    return;
  }}
  el.innerHTML = RISKS_DATA.map(r => `
    <div class="risk-item" onclick="showFileDetail('${{r.path}}')">
      <div class="risk-item-left">
        <div class="risk-score ${{r.level}}">${{r.score}}</div>
        <span class="risk risk-${{r.level}}">${{r.level}}</span>
      </div>
      <div style="flex:1;min-width:0">
        <div class="risk-item-path">${{r.path}}</div>
        <div class="risk-reasons">${{r.reasons.join(' · ')}}</div>
      </div>
    </div>
  `).join('');
}}

/* ── Deps ──────────────────────────────────────────────────────────────── */
function initDeps() {{
  const extEl = document.getElementById('ext-deps');
  const intEl = document.getElementById('int-refs');
  const ext = DEPS_DATA.top_external_packages || [];
  const intRef = DEPS_DATA.most_referenced_files || [];
  const maxExt = ext.length ? Math.max(...ext.map(([,c]) => c)) : 1;
  const maxInt = intRef.length ? Math.max(...intRef.map(([,c]) => c)) : 1;

  extEl.innerHTML = ext.length ? ext.map(([pkg,cnt]) =>
    `<div class="dep-row">
       <span class="dep-name">${{pkg}}</span>
       <div class="dep-bar"><div class="dep-bar-fill" style="width:${{(cnt/maxExt*100).toFixed(0)}}%"></div></div>
       <span class="dep-count">${{cnt}} file${{cnt>1?'s':''}}</span>
     </div>`
  ).join('') : '<div class="empty-state"><div class="empty-title">No external dependencies detected</div></div>';

  intEl.innerHTML = intRef.length ? intRef.map(([path,cnt]) =>
    `<div class="dep-row">
       <span class="dep-name" style="font-size:10px">${{path}}</span>
       <div class="dep-bar"><div class="dep-bar-fill" style="width:${{(cnt/maxInt*100).toFixed(0)}}%"></div></div>
       <span class="dep-count">${{cnt}} ref${{cnt>1?'s':''}}</span>
     </div>`
  ).join('') : '<div class="empty-state"><div class="empty-title">No internal references detected</div></div>';

  setTimeout(() => {{
    document.querySelectorAll('.dep-bar-fill').forEach(el => {{
      const w = el.style.width;
      el.style.width = '0';
      requestAnimationFrame(() => {{
        el.style.transition = 'width 0.6s cubic-bezier(0.16,1,0.3,1)';
        el.style.width = w;
      }});
    }});
  }}, 100);
}}

/* ── Onboarding ────────────────────────────────────────────────────────── */
function initOnboarding() {{
  const el = document.getElementById('onboarding-steps');
  el.innerHTML = ONBOARDING.map((step, i) => {{
    const html = step
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.*?)`/g, '<code>$1</code>');
    return `<div class="step"><div class="step-num">${{i+1}}</div><div class="step-text">${{html}}</div></div>`;
  }}).join('');
}}

/* ── D3 Graph ──────────────────────────────────────────────────────────── */
let graphInited = false;
let focusMode = false;
let selectedNode = null;

function setLayout(type) {{
  document.getElementById('btn-force').classList.toggle('active', type==='force');
}}

function setFocusMode() {{
  focusMode = !focusMode;
  document.getElementById('btn-focus').classList.toggle('active', focusMode);
}}

function initGraph() {{
  if (graphInited) return;
  graphInited = true;
  const container = document.getElementById('graph-container');
  const W = container.offsetWidth;
  const H = container.offsetHeight;

  const svg = d3.select('#graph-container')
    .append('svg')
    .attr('width', W)
    .attr('height', H)
    .style('background', 'transparent');

  // Defs: arrow markers per risk level
  const defs = svg.append('defs');
  [['arrow-critical','#e05252'],['arrow-high','#e8933a'],['arrow-med','#3dba8c'],['arrow-low','#2e3650'],['arrow-default','#1e2436']].forEach(([id, color]) => {{
    defs.append('marker')
      .attr('id', id)
      .attr('viewBox','0 0 10 10').attr('refX',14).attr('refY',5)
      .attr('markerWidth',5).attr('markerHeight',5).attr('orient','auto-start-reverse')
      .append('path').attr('d','M2 1L8 5L2 9')
      .attr('fill','none').attr('stroke',color).attr('stroke-width',1.5);
  }});

  const g = svg.append('g');
  svg.call(
    d3.zoom().scaleExtent([0.15, 5])
      .on('zoom', e => g.attr('transform', e.transform))
  );

  const nodes = GRAPH_DATA.nodes.map(n => ({{...n}}));
  const links = GRAPH_DATA.links.map(l => ({{...l}}));

  const sim = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id((_, i) => i).distance(90).strength(0.25))
    .force('charge', d3.forceManyBody().strength(-220))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collide', d3.forceCollide(d => d.size + 6));

  const link = g.append('g')
    .selectAll('line').data(links).join('line')
    .attr('class', 'link-line')
    .attr('stroke', '#1e2436')
    .attr('stroke-width', 1)
    .attr('stroke-opacity', 0.5)
    .attr('marker-end', 'url(#arrow-default)');

  const nodeGroup = g.append('g')
    .selectAll('g').data(nodes).join('g')
    .attr('class', 'node-group')
    .attr('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (e,d) => {{ if(!e.active) sim.alphaTarget(0.3).restart(); d.fx=d.x;d.fy=d.y; }})
      .on('drag',  (e,d) => {{ d.fx=e.x;d.fy=e.y; }})
      .on('end',   (e,d) => {{ if(!e.active) sim.alphaTarget(0); d.fx=null;d.fy=null; }}));

  // Outer glow ring (for critical/high only)
  nodeGroup.filter(d => d.risk === 'critical' || d.risk === 'high')
    .append('circle')
    .attr('r', d => d.size + 5)
    .attr('fill', 'none')
    .attr('stroke', d => d.risk === 'critical' ? 'rgba(224,82,82,0.15)' : 'rgba(232,147,58,0.12)')
    .attr('stroke-width', 8);

  // Main circle
  nodeGroup.append('circle')
    .attr('r', d => d.size)
    .attr('fill', d => d.color + '22')
    .attr('stroke', d => d.risk_color || d.color)
    .attr('stroke-width', d => {{
      if (d.risk === 'critical') return 1.5;
      if (d.risk === 'high') return 1;
      return 0.5;
    }});

  // Entry point indicator
  nodeGroup.filter(d => d.is_entry)
    .append('circle')
    .attr('r', 3)
    .attr('fill', '#3dba8c')
    .attr('cy', d => -d.size - 6);

  // Labels
  nodeGroup.append('text')
    .text(d => d.label.length > 14 ? d.label.slice(0,12)+'…' : d.label)
    .attr('x', 0).attr('y', d => d.size + 12)
    .attr('text-anchor', 'middle')
    .attr('fill', '#4e5970')
    .attr('font-size', '10px')
    .attr('font-family', 'Inter, sans-serif');

  // Tooltip
  const tooltip = document.getElementById('tooltip');
  nodeGroup
    .on('mousemove', (e, d) => {{
      tooltip.style.display = 'block';
      tooltip.style.left = (e.clientX + 16) + 'px';
      tooltip.style.top = (e.clientY - 12) + 'px';
      const file = FILES_DATA.find(f => f.path === d.id);
      tooltip.innerHTML = `
        <div class="t-path">${{d.id}}</div>
        <div class="t-row"><span class="t-key">Risk</span><span class="risk risk-${{d.risk}}">${{d.risk}}</span></div>
        ${{file && file.classes.length ? `<div class="t-row"><span class="t-key">Classes</span><span>${{file.classes.slice(0,3).join(', ')}}</span></div>` : ''}}
        ${{file && file.functions.length ? `<div class="t-row"><span class="t-key">Functions</span><span>${{file.functions.slice(0,3).join(', ')}}</span></div>` : ''}}
        ${{d.is_entry ? `<div class="t-row" style="margin-top:4px"><span style="color:var(--green)">● Entry point</span></div>` : ''}}
      `;
    }})
    .on('mouseleave', () => {{ tooltip.style.display = 'none'; }})
    .on('click', (_, d) => {{
      showPanel('modules');
      setTimeout(() => {{
        const el = document.querySelector(`[data-path="${{d.id}}"]`);
        if (el) el.scrollIntoView({{behavior:'smooth',block:'center'}});
      }}, 150);
    }});

  sim.on('tick', () => {{
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    nodeGroup.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
  }});
}}

/* ── Search overlay ────────────────────────────────────────────────────── */
function openSearch() {{
  document.getElementById('search-overlay').classList.add('open');
  setTimeout(() => document.getElementById('search-overlay-input').focus(), 50);
}}
function closeSearch(e) {{
  if (e && e.target !== document.getElementById('search-overlay')) return;
  document.getElementById('search-overlay').classList.remove('open');
  document.getElementById('search-overlay-input').value = '';
  document.getElementById('search-overlay-results').innerHTML = '<div class="search-empty">Type to search across the entire project</div>';
}}

function doSearch(query, resultsEl) {{
  if (!query || query.length < 2) {{
    resultsEl.innerHTML = '<div class="search-empty">Type to search across the entire project</div>';
    return;
  }}
  const q = query.toLowerCase();
  const results = [];
  FILES_DATA.forEach(f => {{
    if (f.path.toLowerCase().includes(q))
      results.push({{path:f.path, detail:`File · ${{f.risk_level}} risk`, type:'file'}});
  }});
  MODULES_DATA.forEach(m => {{
    m.functions.forEach(fn => {{
      if (fn.toLowerCase().includes(q))
        results.push({{path:m.path, detail:`Function: ${{fn}}()`, type:'fn'}});
    }});
    m.classes.forEach(cls => {{
      if (cls.toLowerCase().includes(q))
        results.push({{path:m.path, detail:`Class: ${{cls}}`, type:'class'}});
    }});
  }});
  if (!results.length) {{
    resultsEl.innerHTML = '<div class="search-empty">No results found</div>';
    return;
  }}
  resultsEl.innerHTML = results.slice(0, 25).map(r =>
    `<div class="search-result" onclick="handleSearchClick('${{r.path.replace(/'/g,"\\'")}}')" tabindex="0">
       <div class="sr-path">${{r.path}}</div>
       <div class="sr-detail">${{r.detail}}</div>
     </div>`
  ).join('');
}}

function handleSearchClick(path) {{
  document.getElementById('search-overlay').classList.remove('open');
  showFileDetail(path);
}}

document.getElementById('search-overlay-input').addEventListener('input', e => {{
  doSearch(e.target.value, document.getElementById('search-overlay-results'));
}});
document.getElementById('search-main').addEventListener('input', e => {{
  doSearch(e.target.value, document.getElementById('search-results'));
}});

// Keyboard shortcut
document.addEventListener('keydown', e => {{
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {{ e.preventDefault(); openSearch(); }}
  if (e.key === 'Escape') document.getElementById('search-overlay').classList.remove('open');
}});

/* ── Bootstrap ─────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {{
  initStats();
  initCharts();
  initStack();
  initFlow();
  initCritical();
  initModules();
  initRisks();
  initDeps();
  initOnboarding();
  renderTree(TREE_DATA, document.getElementById('file-tree'));
}});
</script>
</body>
</html>"""