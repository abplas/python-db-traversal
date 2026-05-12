from __future__ import annotations

import json
from pathlib import Path

from traversal.grid import Point


BLOCKED_COLOR = "#d9dde3"
TRAFFIC_COLOR = "#fde68a"
STOPLIGHT_COLOR = "#fb7185"
PATH_COLOR = "#d97706"
START_COLOR = "#16a34a"
GOAL_COLOR = "#dc2626"
GRID_LINE_COLOR = "#4b5563"
PAGE_BACKGROUND = "#f5f5f4"
PANEL_BACKGROUND = "#ffffff"
TEXT_COLOR = "#111827"
MUTED_TEXT = "#6b7280"


def launch_demo_ui(grid: list[list[int]], start: Point, goal: Point) -> Path:
    """Build a browser-based demo page and return its file path."""
    output_dir = Path.cwd() / "demo_output"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "traversal_demo.html"
    output_path.write_text(build_demo_html(grid, start, goal), encoding="utf-8")
    return output_path


def build_demo_html(grid: list[list[int]], start: Point, goal: Point) -> str:
    initial_state = {
        "grid": grid,
        "start": {"row": start.row, "col": start.col},
        "goal": {"row": goal.row, "col": goal.col},
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Traversal Demo</title>
  <style>
    :root {{
      --bg: {PAGE_BACKGROUND};
      --panel: {PANEL_BACKGROUND};
      --text: {TEXT_COLOR};
      --muted: {MUTED_TEXT};
      --line: {GRID_LINE_COLOR};
      --blocked: {BLOCKED_COLOR};
      --traffic: {TRAFFIC_COLOR};
      --stoplight: {STOPLIGHT_COLOR};
      --path: {PATH_COLOR};
      --route-bfs: #2563eb;
      --route-dfs: #9333ea;
      --route-astar: #d97706;
      --route-dijkstra: #0f766e;
      --route-greedy: #db2777;
      --route-weighted-astar: #7c3aed;
      --route-shared: #7c3aed;
      --start: {START_COLOR};
      --goal: {GOAL_COLOR};
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      padding: 28px 20px 40px;
      background: var(--bg);
      color: var(--text);
      font-family: "Helvetica Neue", "Avenir Next", sans-serif;
    }}

    .layout {{
      max-width: 1120px;
      margin: 0 auto;
    }}

    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      margin-bottom: 18px;
    }}

    h1 {{
      margin: 0 0 6px;
      font-size: 1.9rem;
      line-height: 1.05;
      letter-spacing: -0.03em;
    }}

    p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }}

    .meta {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .chip {{
      padding: 8px 12px;
      border: 1px solid #d1d5db;
      background: #fafaf9;
      border-radius: 999px;
      font-size: 0.95rem;
      color: var(--muted);
    }}

    .panel {{
      background: var(--panel);
      border: 1px solid #d1d5db;
      padding: 16px;
    }}

    .panel h2 {{
      margin: 0 0 14px;
      font-size: 1rem;
      letter-spacing: 0.01em;
    }}

    .controls {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }}

    .field {{
      display: grid;
      gap: 8px;
    }}

    .field label {{
      font-size: 0.9rem;
      color: var(--muted);
    }}

    .field output {{
      font-weight: 700;
      color: var(--text);
    }}

    input[type="range"],
    button {{
      width: 100%;
      font: inherit;
    }}

    button {{
      padding: 10px 12px;
      border: 1px solid #d1d5db;
      background: #ffffff;
      color: var(--text);
    }}

    button {{
      cursor: pointer;
      text-align: left;
    }}

    button.primary {{
      background: #111827;
      color: #ffffff;
      border-color: #111827;
    }}

    .hint {{
      font-size: 0.88rem;
      color: var(--muted);
      line-height: 1.45;
    }}

    .figure {{
      background: var(--panel);
      border: 1px solid #d1d5db;
      padding: 18px;
      overflow-x: auto;
    }}

    svg {{
      display: block;
      margin: 0 auto;
      max-width: 100%;
      height: auto;
    }}

    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }}

    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      background: #fafaf9;
      border: 1px solid #e5e7eb;
      border-radius: 999px;
      color: var(--muted);
      font-size: 0.9rem;
    }}

    .swatch {{
      width: 14px;
      height: 14px;
      border-radius: 999px;
      border: 1px solid rgba(17, 24, 39, 0.18);
    }}

    .route {{
      margin-top: 16px;
      padding: 14px 16px;
      background: #ffffff;
      border: 1px solid #d1d5db;
      color: #374151;
      font-family: "SFMono-Regular", "Menlo", monospace;
      font-size: 0.92rem;
      overflow-x: auto;
      white-space: nowrap;
    }}

    .grid-line {{
      stroke: var(--line);
      stroke-width: 1.4;
    }}

    .axis-label {{
      fill: var(--muted);
      font-size: 13px;
      font-family: "SFMono-Regular", "Menlo", monospace;
    }}

    .marker-label {{
      fill: #111827;
      font-size: 16px;
      font-weight: 700;
      font-family: "Helvetica Neue", "Avenir Next", sans-serif;
      pointer-events: none;
    }}

    .click-zone {{
      fill: transparent;
      cursor: pointer;
    }}

    .status {{
      margin-top: 12px;
      padding: 10px 12px;
      background: #fafaf9;
      border: 1px solid #e5e7eb;
      color: var(--muted);
      font-size: 0.9rem;
    }}

    .status.active {{
      color: var(--text);
      border-color: #86efac;
      background: #f0fdf4;
    }}

    .status.error {{
      color: #991b1b;
      border-color: #fca5a5;
      background: #fef2f2;
    }}

    .status.info {{
      color: #1d4ed8;
      border-color: #93c5fd;
      background: #eff6ff;
    }}

    .bottom-panel {{
      margin-top: 18px;
    }}

    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
    }}

    .actions button {{
      width: auto;
      min-width: 180px;
      text-align: center;
    }}

    .stack {{
      display: grid;
      gap: 14px;
      margin-top: 14px;
    }}

    .algorithm-options {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .checkbox-chip {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border: 1px solid #d1d5db;
      background: #ffffff;
      border-radius: 12px;
      color: var(--text);
    }}

    .checkbox-chip input {{
      width: auto;
      margin: 0;
    }}

    .api-note {{
      padding: 12px 14px;
      border: 1px solid #dbeafe;
      background: #f8fbff;
      color: #1e3a8a;
      font-size: 0.9rem;
      line-height: 1.5;
    }}

    .comparison-panel {{
      margin-top: 18px;
    }}

    .comparison-panel table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }}

    .comparison-panel th,
    .comparison-panel td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
    }}

    .comparison-panel th {{
      color: var(--muted);
      font-weight: 600;
    }}

    .comparison-empty {{
      color: var(--muted);
      font-size: 0.92rem;
    }}

    @media (max-width: 860px) {{
      .topbar {{
        align-items: start;
        flex-direction: column;
      }}
    }}
  </style>
</head>
<body>
  <main class="layout">
    <section class="topbar">
      <div>
        <h1>Traversal Grid</h1>
        <p>Pick points, regenerate roadblocks, and trace new Manhattan-style routes.</p>
      </div>
      <div class="meta">
        <div class="chip" id="start-chip">A: (0, 0)</div>
        <div class="chip" id="goal-chip">B: (0, 0)</div>
        <div class="chip" id="moves-chip">Moves: 0</div>
        <div class="chip" id="traffic-chip">Traffic: Off</div>
        <div class="chip" id="stoplight-chip">Stoplights: 0</div>
      </div>
    </section>

    <div class="figure">
      <svg id="grid-svg" role="img" aria-label="Traversal grid"></svg>
    </div>

    <section class="legend">
      <div class="legend-item"><span class="swatch" style="background:{START_COLOR};"></span>Point A</div>
      <div class="legend-item"><span class="swatch" style="background:{GOAL_COLOR};"></span>Point B</div>
      <div class="legend-item"><span class="swatch" style="background:{PATH_COLOR};"></span>Route</div>
      <div class="legend-item"><span class="swatch" style="background:var(--route-bfs);"></span>BFS route</div>
      <div class="legend-item"><span class="swatch" style="background:var(--route-dfs);"></span>DFS route</div>
      <div class="legend-item"><span class="swatch" style="background:var(--route-astar);"></span>A* route</div>
      <div class="legend-item"><span class="swatch" style="background:var(--route-dijkstra);"></span>Dijkstra route</div>
      <div class="legend-item"><span class="swatch" style="background:var(--route-greedy);"></span>Greedy route</div>
      <div class="legend-item"><span class="swatch" style="background:var(--route-weighted-astar);"></span>Weighted A* route</div>
      <div class="legend-item"><span class="swatch" style="background:var(--route-shared);"></span>Shared segment</div>
      <div class="legend-item"><span class="swatch" style="background:{TRAFFIC_COLOR};"></span>Directional traffic</div>
      <div class="legend-item"><span class="swatch" style="background:{STOPLIGHT_COLOR};"></span>Stoplight delay</div>
      <div class="legend-item"><span class="swatch" style="background:{BLOCKED_COLOR};"></span>Blocked</div>
    </section>

    <section class="route" id="route-text">Route will appear here.</section>

    <section class="panel bottom-panel">
      <h2>Controls</h2>
      <div class="controls">
        <div class="field">
          <label for="density">Roadblock Density: <output id="density-value">30%</output></label>
          <input id="density" type="range" min="5" max="65" value="30" />
        </div>

        <div class="field">
          <label for="rows">Rows: <output id="rows-value">30</output></label>
          <input id="rows" type="range" min="4" max="30" value="30" />
        </div>

        <div class="field">
          <label for="cols">Columns: <output id="cols-value">40</output></label>
          <input id="cols" type="range" min="4" max="40" value="40" />
        </div>

        <div class="field">
          <label for="stoplight-density">Stoplight Density: <output id="stoplight-density-value">22%</output></label>
          <input id="stoplight-density" type="range" min="0" max="60" value="22" />
        </div>
      </div>

      <div class="stack">
        <div class="field">
          <label>Algorithms</label>
          <div class="algorithm-options">
            <label class="checkbox-chip">
              <input type="checkbox" id="algorithm-bfs" name="algorithm" value="bfs" />
              <span>BFS</span>
            </label>
            <label class="checkbox-chip">
              <input type="checkbox" id="algorithm-dfs" name="algorithm" value="dfs" />
              <span>DFS</span>
            </label>
            <label class="checkbox-chip">
              <input type="checkbox" id="algorithm-astar" name="algorithm" value="astar" checked />
              <span>A*</span>
            </label>
            <label class="checkbox-chip">
              <input type="checkbox" id="algorithm-dijkstra" name="algorithm" value="dijkstra" />
              <span>Dijkstra</span>
            </label>
            <label class="checkbox-chip">
              <input type="checkbox" id="algorithm-greedy-best-first" name="algorithm" value="greedy_best_first" />
              <span>Greedy Best-First</span>
            </label>
            <label class="checkbox-chip">
              <input type="checkbox" id="algorithm-weighted-astar" name="algorithm" value="weighted_astar" />
              <span>Weighted A*</span>
            </label>
            <label class="checkbox-chip">
              <input type="checkbox" id="algorithm-all" name="algorithm-all" value="all" />
              <span>Run all</span>
            </label>
          </div>
        </div>

        <div class="api-note">
          To use backend algorithm comparison, start the API server first:
          <code>PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload</code>
        </div>
      </div>

      <div class="actions">
        <button class="primary" id="find-route">Run selected algorithms</button>
        <button id="generate-grid">Generate new grid</button>
        <button id="toggle-traffic">Directional traffic: Off</button>
        <button id="randomize-traffic">Randomize traffic flow</button>
        <button id="randomize-stoplights">Randomize stoplights</button>
        <button id="toggle-stoplight-mode">Stoplight edit: Off</button>
        <button id="toggle-block-mode">Roadblock edit: Off</button>
        <button id="clear-blocks">Clear roadblocks</button>
      </div>

      <div class="hint">
        Click A or B once to select it, then click a new grid intersection to move it and recalculate the route.
        Turn on roadblock edit if you want to click cell squares to add or remove blockers.
        Turn on stoplight edit if you want to click intersections and add a default 15-second delay.
      </div>
      <div class="status" id="status-text">Ready.</div>
      <div class="status info" id="api-status-text">Backend status: waiting to run.</div>
    </section>

    <section class="panel comparison-panel">
      <h2>Algorithm comparison</h2>
      <div class="comparison-empty" id="comparison-empty">
        Run the backend comparison to see BFS, A*, Dijkstra, Greedy Best-First, Weighted A*, or all registered algorithms side by side.
      </div>
      <table id="comparison-table" hidden>
        <thead>
          <tr>
            <th>Algorithm</th>
            <th>Category</th>
            <th>Path Found</th>
            <th>Moves</th>
            <th>Total Cost</th>
            <th>Runtime ms</th>
            <th>Visited</th>
            <th>Expanded</th>
            <th>Stoplights Crossed</th>
            <th>Stoplight Delay</th>
            <th>Traffic Cost</th>
            <th>Reliability / Tradeoff</th>
          </tr>
        </thead>
        <tbody id="comparison-body"></tbody>
      </table>
    </section>
  </main>

  <script>
    const INITIAL_STATE = {json.dumps(initial_state)};
    const API_URL = "http://127.0.0.1:8000/run-pathfinding";
    const CELL_SIZE = 48;
    const MARGIN = 56;
    const SVG_NS = "http://www.w3.org/2000/svg";

    const state = {{
      grid: structuredClone(INITIAL_STATE.grid),
      start: {{ ...INITIAL_STATE.start }},
      goal: {{ ...INITIAL_STATE.goal }},
      path: [],
      pathCost: 0,
      results: [],
      trafficEnabled: false,
      traffic: null,
      stoplights: {{}},
    }};

    const svg = document.getElementById("grid-svg");
    const densityInput = document.getElementById("density");
    const rowsInput = document.getElementById("rows");
    const colsInput = document.getElementById("cols");
    const stoplightDensityInput = document.getElementById("stoplight-density");
    const densityValue = document.getElementById("density-value");
    const rowsValue = document.getElementById("rows-value");
    const colsValue = document.getElementById("cols-value");
    const stoplightDensityValue = document.getElementById("stoplight-density-value");
    const routeText = document.getElementById("route-text");
    const statusText = document.getElementById("status-text");
    const apiStatusText = document.getElementById("api-status-text");
    const startChip = document.getElementById("start-chip");
    const goalChip = document.getElementById("goal-chip");
    const movesChip = document.getElementById("moves-chip");
    const trafficChip = document.getElementById("traffic-chip");
    const stoplightChip = document.getElementById("stoplight-chip");
    const blockModeButton = document.getElementById("toggle-block-mode");
    const trafficButton = document.getElementById("toggle-traffic");
    const stoplightModeButton = document.getElementById("toggle-stoplight-mode");
    const comparisonTable = document.getElementById("comparison-table");
    const comparisonBody = document.getElementById("comparison-body");
    const comparisonEmpty = document.getElementById("comparison-empty");
    const runAllCheckbox = document.getElementById("algorithm-all");
    const individualAlgorithmCheckboxes = [
      document.getElementById("algorithm-bfs"),
      document.getElementById("algorithm-dfs"),
      document.getElementById("algorithm-astar"),
      document.getElementById("algorithm-dijkstra"),
      document.getElementById("algorithm-greedy-best-first"),
      document.getElementById("algorithm-weighted-astar"),
    ];

    let activeMarker = null;
    let blockMode = false;
    let stoplightMode = false;
    const DEFAULT_STOPLIGHT_DELAY = 15;
    const DEFAULT_STOPLIGHT_CYCLE = 60;

    rowsInput.value = state.grid.length;
    colsInput.value = state.grid[0].length;
    rowsValue.textContent = rowsInput.value;
    colsValue.textContent = colsInput.value;
    densityValue.textContent = densityInput.value + "%";
    stoplightDensityValue.textContent = stoplightDensityInput.value + "%";

    function pointKey(point) {{
      return `${{point.row}},${{point.col}}`;
    }}

    function serializeStoplights() {{
      return Object.values(state.stoplights);
    }}

    function stoplightDelay(point) {{
      const stoplight = state.stoplights[pointKey(point)];
      if (!stoplight || stoplight.has_stoplight === false) {{
        return 0;
      }}
      return Number(stoplight.average_wait_seconds ?? 0);
    }}

    function inBounds(point) {{
      return (
        point.row >= 0 &&
        point.row < state.grid.length &&
        point.col >= 0 &&
        point.col < state.grid[0].length
      );
    }}

    function isRoad(point) {{
      return inBounds(point) && state.grid[point.row][point.col] === 1;
    }}

    function neighbors(point) {{
      const options = [
        {{ row: point.row - 1, col: point.col }},
        {{ row: point.row + 1, col: point.col }},
        {{ row: point.row, col: point.col - 1 }},
        {{ row: point.row, col: point.col + 1 }},
      ];
      return options.filter(isRoad);
    }}

    function manhattan(a, b) {{
      return Math.abs(a.row - b.row) + Math.abs(a.col - b.col);
    }}

    function setApiStatus(message, tone = "info") {{
      apiStatusText.textContent = message;
      apiStatusText.classList.remove("info", "active", "error");
      apiStatusText.classList.add(tone);
    }}

    function clearComparisonResults(message = "Run the backend comparison to see BFS, A*, Dijkstra, Greedy Best-First, Weighted A*, or all registered algorithms side by side.") {{
      state.results = [];
      comparisonBody.innerHTML = "";
      comparisonTable.hidden = true;
      comparisonEmpty.hidden = false;
      comparisonEmpty.textContent = message;
    }}

    function renderComparisonResults(results) {{
      state.results = results;
      comparisonBody.innerHTML = "";

      for (const result of results) {{
        const detailParts = [];
        if (result.comparison_label) {{
          detailParts.push(result.comparison_label);
        }}
        if (result.metadata?.tradeoff) {{
          detailParts.push(result.metadata.tradeoff);
        }}
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${{result.metadata?.display_name ?? result.algorithm_name}}</td>
          <td>${{formatLabel(result.metadata?.reliability_category)}}</td>
          <td>${{result.path_found ? "Yes" : "No"}}</td>
          <td>${{result.moves}}</td>
          <td>${{formatCost(result.path_cost)}}</td>
          <td>${{result.runtime_ms}}</td>
          <td>${{result.visited_count}}</td>
          <td>${{result.expanded_count}}</td>
          <td>${{result.metadata?.stoplights_crossed ?? 0}}</td>
          <td>${{formatCost(result.metadata?.stoplight_delay_total)}}</td>
          <td>${{formatCost(result.metadata?.traffic_cost_total)}}</td>
          <td>${{detailParts.map(formatLabel).join(" | ") || "N/A"}}</td>
        `;
        comparisonBody.appendChild(row);
      }}

      comparisonEmpty.hidden = true;
      comparisonTable.hidden = false;
    }}

    function getDisplayedRoutes() {{
      const backendRoutes = state.results
        .filter(result => result.path_found && Array.isArray(result.path) && result.path.length > 0)
        .map((result, index) => ({{
          algorithm: result.algorithm_name,
          path: result.path,
          cost: result.path_cost ?? 0,
          index,
        }}));

      if (backendRoutes.length > 0) {{
        return backendRoutes;
      }}

      if (state.path.length > 0) {{
        return [{{
          algorithm: "browser",
          path: state.path,
          cost: state.pathCost,
          index: 0,
        }}];
      }}

      return [];
    }}

    function getRouteColor(algorithmName, index) {{
      const normalized = String(algorithmName).toLowerCase();
      if (normalized === "bfs") return "var(--route-bfs)";
      if (normalized === "dfs") return "var(--route-dfs)";
      if (normalized === "astar") return "var(--route-astar)";
      if (normalized === "dijkstra") return "var(--route-dijkstra)";
      if (normalized === "greedy_best_first") return "var(--route-greedy)";
      if (normalized === "weighted_astar") return "var(--route-weighted-astar)";

      const fallbackColors = [
        "var(--route-bfs)",
        "var(--route-dfs)",
        "var(--route-astar)",
        "var(--route-dijkstra)",
        "var(--route-greedy)",
        "var(--route-weighted-astar)",
      ];
      return fallbackColors[index % fallbackColors.length];
    }}

    function segmentKey(a, b) {{
      const first = pointKey(a);
      const second = pointKey(b);
      return first < second ? `${{first}}|${{second}}` : `${{second}}|${{first}}`;
    }}

    function renderRoutes(svg, routes) {{
      if (routes.length === 0) {{
        return;
      }}

      const segmentUsage = new Map();
      for (const route of routes) {{
        for (let index = 0; index < route.path.length - 1; index += 1) {{
          const start = route.path[index];
          const end = route.path[index + 1];
          const key = segmentKey(start, end);
          const segments = segmentUsage.get(key) ?? [];
          segments.push(route);
          segmentUsage.set(key, segments);
        }}
      }}

      for (const route of routes) {{
        const stroke = getRouteColor(route.algorithm, route.index);

        for (let index = 0; index < route.path.length - 1; index += 1) {{
          const start = route.path[index];
          const end = route.path[index + 1];
          const key = segmentKey(start, end);
          const sharedRoutes = segmentUsage.get(key) ?? [route];
          const sharedIndex = sharedRoutes.findIndex(candidate => candidate.algorithm === route.algorithm);
          const overlapCount = sharedRoutes.length;
          const x1 = MARGIN + start.col * CELL_SIZE;
          const y1 = MARGIN + start.row * CELL_SIZE;
          const x2 = MARGIN + end.col * CELL_SIZE;
          const y2 = MARGIN + end.row * CELL_SIZE;
          let offsetX = 0;
          let offsetY = 0;

          if (overlapCount > 1) {{
            const spacing = 4.5;
            const centeredOffset = (sharedIndex - (overlapCount - 1) / 2) * spacing;
            if (start.row === end.row) {{
              offsetY = centeredOffset;
            }} else {{
              offsetX = centeredOffset;
            }}

            const sharedBase = document.createElementNS(SVG_NS, "line");
            sharedBase.setAttribute("x1", String(x1));
            sharedBase.setAttribute("y1", String(y1));
            sharedBase.setAttribute("x2", String(x2));
            sharedBase.setAttribute("y2", String(y2));
            sharedBase.setAttribute("stroke", "var(--route-shared)");
            sharedBase.setAttribute("stroke-width", "10");
            sharedBase.setAttribute("stroke-linecap", "round");
            sharedBase.setAttribute("opacity", "0.2");
            svg.appendChild(sharedBase);
          }}

          const line = document.createElementNS(SVG_NS, "line");
          line.setAttribute("x1", String(x1 + offsetX));
          line.setAttribute("y1", String(y1 + offsetY));
          line.setAttribute("x2", String(x2 + offsetX));
          line.setAttribute("y2", String(y2 + offsetY));
          line.setAttribute("stroke", stroke);
          line.setAttribute("stroke-width", overlapCount > 1 ? "4" : "7");
          line.setAttribute("stroke-linecap", "round");
          line.setAttribute("opacity", overlapCount > 1 ? "0.95" : "0.9");
          svg.appendChild(line);
        }}

        for (const point of route.path) {{
          const key = pointKey(point);
          const sharedPointCount = routes.filter(candidate =>
            candidate.path.some(candidatePoint => pointKey(candidatePoint) === key)
          ).length;

          const node = document.createElementNS(SVG_NS, "circle");
          node.setAttribute("cx", String(MARGIN + point.col * CELL_SIZE));
          node.setAttribute("cy", String(MARGIN + point.row * CELL_SIZE));
          node.setAttribute("r", sharedPointCount > 1 ? "6.5" : "7.5");
          node.setAttribute("fill", sharedPointCount > 1 ? "var(--route-shared)" : stroke);
          node.setAttribute("stroke", "#ffffff");
          node.setAttribute("stroke-width", sharedPointCount > 1 ? "2.5" : "2");
          svg.appendChild(node);
        }}
      }}
    }}

    function formatCost(value) {{
      return value === null || value === undefined ? "N/A" : Number(value).toFixed(2).replace(/[.]00$/, "");
    }}

    function formatLabel(value) {{
      if (value === null || value === undefined || value === "") {{
        return "N/A";
      }}
      return String(value).replace(/_/g, " ");
    }}

    function createNeutralTraffic(rows, cols) {{
      const directions = ["north", "south", "east", "west"];
      return Object.fromEntries(
        directions.map(direction => [
          direction,
          Array.from({{ length: rows }}, () => Array.from({{ length: cols }}, () => 1))
        ])
      );
    }}

    function createDirectionalTraffic(rows, cols) {{
      const traffic = createNeutralTraffic(rows, cols);
      for (let row = 0; row < rows; row += 1) {{
        for (let col = 0; col < cols; col += 1) {{
          const eastBias = 1 + (col / Math.max(cols - 1, 1)) * 1.2;
          const westBias = 1 + ((cols - 1 - col) / Math.max(cols - 1, 1)) * 1.2;
          const southBias = 1 + (row / Math.max(rows - 1, 1)) * 0.9;
          const northBias = 1 + ((rows - 1 - row) / Math.max(rows - 1, 1)) * 0.9;
          traffic.east[row][col] = Number((eastBias + Math.random() * 0.35).toFixed(2));
          traffic.west[row][col] = Number((westBias + Math.random() * 0.35).toFixed(2));
          traffic.south[row][col] = Number((southBias + Math.random() * 0.35).toFixed(2));
          traffic.north[row][col] = Number((northBias + Math.random() * 0.35).toFixed(2));
        }}
      }}
      return traffic;
    }}

    function ensureTraffic() {{
      const rows = state.grid.length;
      const cols = state.grid[0].length;
      if (!state.traffic) {{
        state.traffic = createDirectionalTraffic(rows, cols);
      }}
    }}

    function directionBetween(current, neighbor) {{
      if (neighbor.row === current.row - 1 && neighbor.col === current.col) return "north";
      if (neighbor.row === current.row + 1 && neighbor.col === current.col) return "south";
      if (neighbor.row === current.row && neighbor.col === current.col + 1) return "east";
      if (neighbor.row === current.row && neighbor.col === current.col - 1) return "west";
      throw new Error("Only non-diagonal neighbors have traffic direction.");
    }}

    function movementCost(current, neighbor) {{
      const trafficCost = (() => {{
        if (!state.trafficEnabled) {{
          return 1;
        }}
        ensureTraffic();
        return state.traffic[directionBetween(current, neighbor)][current.row][current.col];
      }})();
      return trafficCost + stoplightDelay(neighbor);
    }}

    function getSelectedAlgorithms() {{
      if (runAllCheckbox.checked) {{
        return "all";
      }}

      const selected = individualAlgorithmCheckboxes
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);

      return selected.length > 0 ? selected : null;
    }}

    function findPathInBrowser() {{
      if (!isRoad(state.start) || !isRoad(state.goal)) {{
        state.path = [];
        updateStatus("Point A and point B must both be on open intersections.");
        render();
        return null;
      }}

      const frontier = [{{ point: state.start, priority: 0 }}];
      const cameFrom = new Map();
      const costSoFar = new Map([[pointKey(state.start), 0]]);

      while (frontier.length > 0) {{
        frontier.sort((a, b) => a.priority - b.priority);
        const current = frontier.shift().point;

        if (current.row === state.goal.row && current.col === state.goal.col) {{
          state.path = reconstructPath(cameFrom, current);
          state.pathCost = costSoFar.get(pointKey(current));
          updateStatus(`Route found with ${{state.path.length - 1}} moves and cost ${{formatCost(state.pathCost)}}.`);
          render();
          return state.path;
        }}

        for (const neighbor of neighbors(current)) {{
          const currentCost = costSoFar.get(pointKey(current));
          const newCost = currentCost + movementCost(current, neighbor);
          const neighborKey = pointKey(neighbor);

          if (!costSoFar.has(neighborKey) || newCost < costSoFar.get(neighborKey)) {{
            costSoFar.set(neighborKey, newCost);
            const priority = newCost + manhattan(neighbor, state.goal);
            frontier.push({{ point: neighbor, priority }});
            cameFrom.set(neighborKey, current);
          }}
        }}
      }}

      state.path = [];
      state.pathCost = 0;
      updateStatus("No route is available with the current roadblocks.");
      render();
      return null;
    }}

    function reconstructPath(cameFrom, current) {{
      const path = [current];
      let cursor = current;

      while (cameFrom.has(pointKey(cursor))) {{
        cursor = cameFrom.get(pointKey(cursor));
        path.push(cursor);
      }}

      return path.reverse();
    }}

    function isFourWayIntersection(point) {{
      return isRoad(point) && neighbors(point).length === 4;
    }}

    function findFourWayIntersections() {{
      const intersections = [];
      for (let row = 0; row < state.grid.length; row += 1) {{
        for (let col = 0; col < state.grid[0].length; col += 1) {{
          const point = {{ row, col }};
          if (isFourWayIntersection(point)) {{
            intersections.push(point);
          }}
        }}
      }}
      return intersections;
    }}

    function generateRandomStoplights() {{
      const density = Number(stoplightDensityInput.value) / 100;
      const intersections = findFourWayIntersections().filter(point => {{
        return !(
          (point.row === state.start.row && point.col === state.start.col) ||
          (point.row === state.goal.row && point.col === state.goal.col)
        );
      }});

      state.stoplights = {{}};
      for (const point of intersections) {{
        if (Math.random() > density) {{
          continue;
        }}
        state.stoplights[pointKey(point)] = {{
          row: point.row,
          col: point.col,
          average_wait_seconds: [8, 12, 15, 20][Math.floor(Math.random() * 4)],
          light_cycle_seconds: [45, 60, 75][Math.floor(Math.random() * 3)],
          has_stoplight: true,
          metadata: {{}},
        }};
      }}
    }}

    function buildStreetGrid(rows, cols, density) {{
      const rowGapOptions = [3, 4, 5];
      const colGapOptions = [3, 4, 5];
      const rowGap = rowGapOptions[Math.floor(Math.random() * rowGapOptions.length)];
      const colGap = colGapOptions[Math.floor(Math.random() * colGapOptions.length)];
      const majorRows = new Set(Array.from({{ length: Math.ceil(rows / rowGap) }}, (_, index) => index * rowGap));
      const majorCols = new Set(Array.from({{ length: Math.ceil(cols / colGap) }}, (_, index) => index * colGap));
      return Array.from({{ length: rows }}, (_, row) =>
        Array.from({{ length: cols }}, (_, col) => {{
          const onMajorCorridor = majorRows.has(row) || majorCols.has(col) || col === 0 || col === cols - 1;
          const blockProbability = Math.min(onMajorCorridor ? density * 0.15 : density * 1.25, 0.82);
          return Math.random() < blockProbability ? 0 : 1;
        }})
      );
    }}

    function generateRandomGrid(rows, cols, density, attempts = 40) {{
      for (let attempt = 0; attempt < attempts; attempt += 1) {{
        const grid = buildStreetGrid(rows, cols, density);

        const start = {{ row: Math.floor(Math.random() * rows), col: 0 }};
        const goal = {{ row: Math.floor(Math.random() * rows), col: cols - 1 }};
        grid[start.row][start.col] = 1;
        grid[goal.row][goal.col] = 1;

        state.grid = grid;
        state.start = start;
        state.goal = goal;
        state.path = [];
        state.pathCost = 0;
        state.traffic = state.trafficEnabled ? createDirectionalTraffic(rows, cols) : null;
        state.stoplights = {{}};

        if (pathExists()) {{
          generateRandomStoplights();
          return true;
        }}
      }}

      return false;
    }}

    function pathExists() {{
      const queue = [state.start];
      const visited = new Set([pointKey(state.start)]);

      while (queue.length > 0) {{
        const current = queue.shift();
        if (current.row === state.goal.row && current.col === state.goal.col) {{
          return true;
        }}

        for (const neighbor of neighbors(current)) {{
          const key = pointKey(neighbor);
          if (!visited.has(key)) {{
            visited.add(key);
            queue.push(neighbor);
          }}
        }}
      }}

      return false;
    }}

    function setIntersection(row, col) {{
      if (stoplightMode) {{
        toggleStoplight(row, col);
        return;
      }}

      if (!activeMarker) {{
        updateStatus("Click A or B first, then click a new grid intersection.");
        return;
      }}

      const point = {{ row, col }};
      state.grid[row][col] = 1;

      if (activeMarker === "start") {{
        state.start = point;
        updateStatus(`Point A moved to (${{row}}, ${{col}}).`);
      }} else if (activeMarker === "goal") {{
        state.goal = point;
        updateStatus(`Point B moved to (${{row}}, ${{col}}).`);
      }}

      delete state.stoplights[pointKey(point)];

      activeMarker = null;
      syncStatusAppearance();
      clearComparisonResults("Grid changed. Run the backend comparison again to refresh the table.");
      findPathInBrowser();
    }}

    function toggleCell(row, col) {{
      if (!blockMode) {{
        return;
      }}

      const protectedStart = state.start.row === row && state.start.col === col;
      const protectedGoal = state.goal.row === row && state.goal.col === col;
      if (protectedStart || protectedGoal) {{
        updateStatus("Point A and point B cannot be blocked.");
        return;
      }}

      state.grid[row][col] = state.grid[row][col] === 1 ? 0 : 1;
      if (state.grid[row][col] === 0) {{
        delete state.stoplights[pointKey({{ row, col }})];
      }}
      clearComparisonResults("Grid changed. Run the backend comparison again to refresh the table.");
      findPathInBrowser();
    }}

    function toggleStoplight(row, col) {{
      const point = {{ row, col }};
      const key = pointKey(point);

      if (!isRoad(point)) {{
        updateStatus("Stoplights must be placed on traversable intersections.");
        return;
      }}

      if (!isFourWayIntersection(point)) {{
        updateStatus("Stoplights should only be placed on four-way intersections.");
        return;
      }}

      if ((state.start.row === row && state.start.col === col) || (state.goal.row === row && state.goal.col === col)) {{
        updateStatus("Start and goal points cannot also be stoplights.");
        return;
      }}

      if (state.stoplights[key]) {{
        delete state.stoplights[key];
        updateStatus(`Removed stoplight at (${{row}}, ${{col}}).`);
      }} else {{
        state.stoplights[key] = {{
          row,
          col,
          average_wait_seconds: DEFAULT_STOPLIGHT_DELAY,
          light_cycle_seconds: DEFAULT_STOPLIGHT_CYCLE,
          has_stoplight: true,
          metadata: {{}},
        }};
        updateStatus(`Added a ${{DEFAULT_STOPLIGHT_DELAY}}-second stoplight delay at (${{row}}, ${{col}}).`);
      }}

      clearComparisonResults("Stoplights changed. Run the backend comparison again to refresh the table.");
      findPathInBrowser();
    }}

    function updateStatus(message) {{
      statusText.textContent = message;
    }}

    function syncStatusAppearance() {{
      if (activeMarker) {{
        statusText.classList.add("active");
      }} else {{
        statusText.classList.remove("active");
      }}
    }}

    function selectMarker(markerName) {{
      activeMarker = markerName;
      blockMode = false;
      stoplightMode = false;
      blockModeButton.textContent = "Roadblock edit: Off";
      stoplightModeButton.textContent = "Stoplight edit: Off";
      const label = markerName === "start" ? "A" : "B";
      updateStatus(`Point ${{label}} selected. Click a new grid intersection to move it.`);
      syncStatusAppearance();
      render();
    }}

    function clearRoadblocks() {{
      state.grid = state.grid.map(row => row.map(() => 1));
      state.grid[state.start.row][state.start.col] = 1;
      state.grid[state.goal.row][state.goal.col] = 1;
      updateStatus("All roadblocks cleared.");
      clearComparisonResults("Roadblocks changed. Run the backend comparison again to refresh the table.");
      findPathInBrowser();
    }}

    async function runBackendPathfinding() {{
      const selectedAlgorithms = getSelectedAlgorithms();

      if (!selectedAlgorithms) {{
        setApiStatus("Select at least one algorithm or choose Run all before sending the backend request.", "error");
        return;
      }}

      setApiStatus("Backend request running...", "active");

      try {{
        const response = await fetch(API_URL, {{
          method: "POST",
          headers: {{
            "Content-Type": "application/json",
          }},
          body: JSON.stringify({{
            grid: state.grid,
            start: state.start,
            goal: state.goal,
            algorithms: selectedAlgorithms,
            traffic: state.trafficEnabled ? state.traffic : null,
            stoplights: serializeStoplights(),
          }}),
        }});

        const payload = await response.json();

        if (!response.ok) {{
          const detail = payload.detail || "The backend request failed.";
          throw new Error(detail);
        }}

        renderComparisonResults(payload.results);

        const firstSuccessfulResult = payload.results.find(result => result.path_found);
        if (firstSuccessfulResult) {{
          state.path = firstSuccessfulResult.path;
          state.pathCost = firstSuccessfulResult.path_cost ?? 0;
          const successfulAlgorithms = payload.results
            .filter(result => result.path_found)
            .map(result => result.metadata?.display_name ?? result.algorithm_name)
            .join(", ");
          updateStatus(`Showing backend routes for: ${{successfulAlgorithms}}.`);
        }} else {{
          state.path = [];
          state.pathCost = 0;
          updateStatus("The backend ran successfully, but no algorithm found a route.");
        }}

        render();
        setApiStatus("Backend request succeeded.", "active");
      }} catch (error) {{
        clearComparisonResults("No backend comparison results are available yet.");
        findPathInBrowser();
        setApiStatus(
          "Could not reach the FastAPI server. Start it with: PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload",
          "error"
        );
      }}
    }}

    function render() {{
      const rows = state.grid.length;
      const cols = state.grid[0].length;
      const boardWidth = (cols - 1) * CELL_SIZE;
      const boardHeight = (rows - 1) * CELL_SIZE;
      const svgWidth = boardWidth + MARGIN * 2;
      const svgHeight = boardHeight + MARGIN * 2;

      svg.setAttribute("viewBox", `0 0 ${{svgWidth}} ${{svgHeight}}`);
      svg.innerHTML = "";

      const background = document.createElementNS(SVG_NS, "rect");
      background.setAttribute("x", "0");
      background.setAttribute("y", "0");
      background.setAttribute("width", String(svgWidth));
      background.setAttribute("height", String(svgHeight));
      background.setAttribute("fill", "#ffffff");
      svg.appendChild(background);

      if (state.trafficEnabled) {{
        ensureTraffic();
        for (let row = 0; row < rows; row += 1) {{
          for (let col = 0; col < cols; col += 1) {{
            if (state.grid[row][col] !== 1) continue;
            const x = MARGIN + col * CELL_SIZE;
            const y = MARGIN + row * CELL_SIZE;
            const avgTraffic = (
              state.traffic.north[row][col] +
              state.traffic.south[row][col] +
              state.traffic.east[row][col] +
              state.traffic.west[row][col]
            ) / 4;
            if (avgTraffic <= 1.25) continue;
            const marker = document.createElementNS(SVG_NS, "rect");
            marker.setAttribute("x", String(x - CELL_SIZE * 0.28));
            marker.setAttribute("y", String(y - CELL_SIZE * 0.28));
            marker.setAttribute("width", String(CELL_SIZE * 0.56));
            marker.setAttribute("height", String(CELL_SIZE * 0.56));
            marker.setAttribute("rx", "6");
            marker.setAttribute("fill", "var(--traffic)");
            marker.setAttribute("opacity", String(Math.min(0.7, 0.18 + (avgTraffic - 1) / 3)));
            svg.appendChild(marker);
          }}
        }}
      }}

      for (const stoplight of serializeStoplights()) {{
        const x = MARGIN + stoplight.col * CELL_SIZE;
        const y = MARGIN + stoplight.row * CELL_SIZE;
        const marker = document.createElementNS(SVG_NS, "circle");
        marker.setAttribute("cx", String(x));
        marker.setAttribute("cy", String(y));
        marker.setAttribute("r", "10");
        marker.setAttribute("fill", "var(--stoplight)");
        marker.setAttribute("opacity", "0.9");
        marker.setAttribute("stroke", "#ffffff");
        marker.setAttribute("stroke-width", "2");
        svg.appendChild(marker);
      }}

      for (let row = 0; row < rows; row += 1) {{
        for (let col = 0; col < cols; col += 1) {{
          if (state.grid[row][col] === 0) {{
            const x = MARGIN + col * CELL_SIZE;
            const y = MARGIN + row * CELL_SIZE;
            const blocked = document.createElementNS(SVG_NS, "rect");
            blocked.setAttribute("x", String(x - CELL_SIZE * 0.36));
            blocked.setAttribute("y", String(y - CELL_SIZE * 0.36));
            blocked.setAttribute("width", String(CELL_SIZE * 0.72));
            blocked.setAttribute("height", String(CELL_SIZE * 0.72));
            blocked.setAttribute("rx", "8");
            blocked.setAttribute("fill", "var(--blocked)");
            blocked.setAttribute("opacity", "0.9");
            svg.appendChild(blocked);
          }}
        }}
      }}

      for (let col = 0; col < cols; col += 1) {{
        const x = MARGIN + col * CELL_SIZE;
        const line = document.createElementNS(SVG_NS, "line");
        line.setAttribute("x1", String(x));
        line.setAttribute("y1", String(MARGIN));
        line.setAttribute("x2", String(x));
        line.setAttribute("y2", String(MARGIN + boardHeight));
        line.setAttribute("class", "grid-line");
        svg.appendChild(line);
      }}

      for (let row = 0; row < rows; row += 1) {{
        const y = MARGIN + row * CELL_SIZE;
        const line = document.createElementNS(SVG_NS, "line");
        line.setAttribute("x1", String(MARGIN));
        line.setAttribute("y1", String(y));
        line.setAttribute("x2", String(MARGIN + boardWidth));
        line.setAttribute("y2", String(y));
        line.setAttribute("class", "grid-line");
        svg.appendChild(line);
      }}

      renderRoutes(svg, getDisplayedRoutes());

      for (let row = 0; row < rows; row += 1) {{
        const y = MARGIN + row * CELL_SIZE;
        const label = document.createElementNS(SVG_NS, "text");
        label.setAttribute("x", String(MARGIN - 22));
        label.setAttribute("y", String(y + 5));
        label.setAttribute("class", "axis-label");
        label.textContent = String(row);
        svg.appendChild(label);
      }}

      for (let col = 0; col < cols; col += 1) {{
        const x = MARGIN + col * CELL_SIZE;
        const label = document.createElementNS(SVG_NS, "text");
        label.setAttribute("x", String(x));
        label.setAttribute("y", String(MARGIN - 18));
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("class", "axis-label");
        label.textContent = String(col);
        svg.appendChild(label);
      }}

      for (let row = 0; row < rows; row += 1) {{
        for (let col = 0; col < cols; col += 1) {{
          const x = MARGIN + col * CELL_SIZE;
          const y = MARGIN + row * CELL_SIZE;

          const cellZone = document.createElementNS(SVG_NS, "rect");
          cellZone.setAttribute("x", String(x - CELL_SIZE * 0.34));
          cellZone.setAttribute("y", String(y - CELL_SIZE * 0.34));
          cellZone.setAttribute("width", String(CELL_SIZE * 0.68));
          cellZone.setAttribute("height", String(CELL_SIZE * 0.68));
          cellZone.setAttribute("rx", "8");
          cellZone.setAttribute("class", "click-zone");
          cellZone.addEventListener("click", () => toggleCell(row, col));
          svg.appendChild(cellZone);

          const intersectionZone = document.createElementNS(SVG_NS, "circle");
          intersectionZone.setAttribute("cx", String(x));
          intersectionZone.setAttribute("cy", String(y));
          intersectionZone.setAttribute("r", "18");
          intersectionZone.setAttribute("class", "click-zone");
          intersectionZone.addEventListener("click", () => {{
            if (blockMode) {{
              toggleCell(row, col);
              return;
            }}
            setIntersection(row, col);
          }});
          svg.appendChild(intersectionZone);
        }}
      }}

      drawMarker(state.start, "A", "var(--start)", "start");
      drawMarker(state.goal, "B", "var(--goal)", "goal");

      startChip.textContent = `A: (${{state.start.row}}, ${{state.start.col}})`;
      goalChip.textContent = `B: (${{state.goal.row}}, ${{state.goal.col}})`;
      movesChip.textContent = `Moves: ${{Math.max(state.path.length - 1, 0)}}`;
      trafficChip.textContent = `Traffic: ${{state.trafficEnabled ? "On" : "Off"}}`;
      stoplightChip.textContent = `Stoplights: ${{serializeStoplights().length}}`;
      const displayedRoutes = getDisplayedRoutes();
      routeText.textContent = displayedRoutes.length > 0
        ? displayedRoutes
            .map(route => `${{formatLabel(route.algorithm)}}: ${{route.path.map(point => `(${{point.row}}, ${{point.col}})`).join(" -> ")}} | cost ${{formatCost(route.cost)}}`)
            .join(" || ")
        : "No route found for the current layout.";
    }}

    function drawMarker(point, labelText, fill, markerName) {{
      const x = MARGIN + point.col * CELL_SIZE;
      const y = MARGIN + point.row * CELL_SIZE;

      const marker = document.createElementNS(SVG_NS, "circle");
      marker.setAttribute("cx", String(x));
      marker.setAttribute("cy", String(y));
      marker.setAttribute("r", "16");
      marker.setAttribute("fill", fill);
      marker.setAttribute("stroke", "#ffffff");
      marker.setAttribute("stroke-width", activeMarker === markerName ? "5" : "3");
      marker.style.cursor = "pointer";
      marker.addEventListener("click", (event) => {{
        event.stopPropagation();
        selectMarker(markerName);
      }});
      svg.appendChild(marker);

      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", String(x));
      label.setAttribute("y", String(y + 6));
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("class", "marker-label");
      label.textContent = labelText;
      label.style.cursor = "pointer";
      label.addEventListener("click", (event) => {{
        event.stopPropagation();
        selectMarker(markerName);
      }});
      svg.appendChild(label);
    }}

    densityInput.addEventListener("input", () => {{
      densityValue.textContent = densityInput.value + "%";
    }});

    rowsInput.addEventListener("input", () => {{
      rowsValue.textContent = rowsInput.value;
    }});

    colsInput.addEventListener("input", () => {{
      colsValue.textContent = colsInput.value;
    }});

    stoplightDensityInput.addEventListener("input", () => {{
      stoplightDensityValue.textContent = stoplightDensityInput.value + "%";
    }});

    runAllCheckbox.addEventListener("change", () => {{
      if (runAllCheckbox.checked) {{
        individualAlgorithmCheckboxes.forEach(checkbox => {{
          checkbox.checked = false;
        }});
      }}
    }});

    individualAlgorithmCheckboxes.forEach(checkbox => {{
      checkbox.addEventListener("change", () => {{
        if (checkbox.checked) {{
          runAllCheckbox.checked = false;
        }}
      }});
    }});

    document.getElementById("find-route").addEventListener("click", runBackendPathfinding);

    document.getElementById("generate-grid").addEventListener("click", () => {{
      const rows = Number(rowsInput.value);
      const cols = Number(colsInput.value);
      const density = Number(densityInput.value) / 100;
      const success = generateRandomGrid(rows, cols, density);

      if (success) {{
        updateStatus("Generated a new grid and found a valid route.");
        clearComparisonResults("Grid changed. Run the backend comparison again to refresh the table.");
        findPathInBrowser();
      }} else {{
        updateStatus("Could not generate a connected grid with that density. Try lowering it.");
        render();
      }}
    }});

    document.getElementById("clear-blocks").addEventListener("click", clearRoadblocks);

    trafficButton.addEventListener("click", () => {{
      state.trafficEnabled = !state.trafficEnabled;
      if (state.trafficEnabled) {{
        ensureTraffic();
      }}
      stoplightMode = false;
      stoplightModeButton.textContent = "Stoplight edit: Off";
      trafficButton.textContent = `Directional traffic: ${{state.trafficEnabled ? "On" : "Off"}}`;
      clearComparisonResults("Traffic flow changed. Run the backend comparison again to refresh the table.");
      findPathInBrowser();
    }});

    document.getElementById("randomize-traffic").addEventListener("click", () => {{
      state.trafficEnabled = true;
      state.traffic = createDirectionalTraffic(state.grid.length, state.grid[0].length);
      trafficButton.textContent = "Directional traffic: On";
      updateStatus("Generated direction-based traffic flow for the current grid.");
      clearComparisonResults("Traffic flow changed. Run the backend comparison again to refresh the table.");
      findPathInBrowser();
    }});

    document.getElementById("randomize-stoplights").addEventListener("click", () => {{
      generateRandomStoplights();
      updateStatus("Generated stoplights on available four-way intersections.");
      clearComparisonResults("Stoplights changed. Run the backend comparison again to refresh the table.");
      findPathInBrowser();
    }});

    stoplightModeButton.addEventListener("click", () => {{
      stoplightMode = !stoplightMode;
      blockMode = false;
      activeMarker = null;
      blockModeButton.textContent = "Roadblock edit: Off";
      stoplightModeButton.textContent = `Stoplight edit: ${{stoplightMode ? "On" : "Off"}}`;
      updateStatus(
        stoplightMode
          ? "Stoplight edit is on. Click an intersection to add or remove a default 15-second delay."
          : "Stoplight edit is off."
      );
      syncStatusAppearance();
      render();
    }});

    blockModeButton.addEventListener("click", () => {{
      blockMode = !blockMode;
      stoplightMode = false;
      activeMarker = null;
      stoplightModeButton.textContent = "Stoplight edit: Off";
      blockModeButton.textContent = `Roadblock edit: ${{blockMode ? "On" : "Off"}}`;
      updateStatus(
        blockMode
          ? "Roadblock edit is on. Click a cell square to add or remove blockers."
          : "Roadblock edit is off."
      );
      syncStatusAppearance();
      render();
    }});

    clearComparisonResults();
    if (!generateRandomGrid(Number(rowsInput.value), Number(colsInput.value), Number(densityInput.value) / 100)) {{
      updateStatus("Could not generate the initial grid. Try refreshing or lowering roadblock density.");
      findPathInBrowser();
    }} else {{
      updateStatus("Generated a fresh grid with random start and goal points.");
      findPathInBrowser();
    }}
  </script>
</body>
</html>
"""
