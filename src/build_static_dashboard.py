from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "processed"
TABLE_DIR = REPO_ROOT / "output" / "tables"
DOCS_DIR = REPO_ROOT / "docs"

INDUSTRY_EN = {
    "医药生物": "Healthcare",
    "电子": "Electronics",
    "电力设备": "Electrical Equipment",
    "非银金融": "Non-bank Financials",
    "交通运输": "Transportation",
    "基础化工": "Basic Chemicals",
    "房地产": "Real Estate",
    "有色金属": "Non-ferrous Metals",
    "机械设备": "Machinery",
    "公用事业": "Utilities",
    "计算机": "Computer",
    "食品饮料": "Food & Beverage",
    "汽车": "Automobile",
    "银行": "Banks",
    "国防军工": "Defense",
    "钢铁": "Steel",
    "传媒": "Media",
    "商贸零售": "Retail",
    "煤炭": "Coal",
    "农林牧渔": "Agriculture",
    "家用电器": "Home Appliances",
    "美容护理": "Beauty Care",
    "轻工制造": "Light Manufacturing",
    "纺织服饰": "Textile & Apparel",
}


def records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records", force_ascii=False))


def load_payload() -> dict:
    firm = pd.read_csv(DATA_DIR / "firm_panel_selected_years.csv")
    eps = pd.read_csv(DATA_DIR / "eps_timeseries.csv")
    regression = pd.read_csv(TABLE_DIR / "panel_regression_summary.csv")

    firm["industry_label"] = firm["industry"].map(INDUSTRY_EN).fillna(firm["industry"])
    firm["market_cap_billion"] = firm["market_cap"] / 1e9
    firm["assets_billion"] = firm["total_assets"] / 1e9
    firm["eps_asset_scaled"] = firm["eps_asset"] * 1e12

    keep_firm = [
        "year",
        "index_group",
        "ticker",
        "company_name",
        "industry_label",
        "eps",
        "market_cap_billion",
        "assets_billion",
        "eps_asset_scaled",
        "log_market_cap",
    ]
    keep_reg = [
        "model",
        "dependent_variable",
        "sample",
        "n_observations",
        "n_firms",
        "r_squared",
        "log_market_cap_coef",
        "log_market_cap_se",
        "log_market_cap_sig",
        "is_csi500_coef",
        "is_csi500_sig",
    ]

    return {
        "firm": records(firm[keep_firm].round(6)),
        "eps": records(eps.round(6)),
        "regression": records(regression[keep_reg].round(6)),
        "years": sorted(firm["year"].dropna().astype(int).unique().tolist()),
        "groups": sorted(firm["index_group"].dropna().unique().tolist()),
        "industries": sorted(firm["industry_label"].dropna().unique().tolist()),
    }


def build_html(payload: dict) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>A-Share Firm Size and Profitability Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #5d6d7e;
      --line: #d7dbdd;
      --panel: #ffffff;
      --bg: #f6f8fb;
      --blue: #476fb3;
      --orange: #d88455;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }}
    header {{
      padding: 28px 36px 18px;
      background: #fff;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.15;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 20px;
      letter-spacing: 0;
    }}
    p {{ color: var(--muted); margin: 0; max-width: 980px; }}
    main {{
      display: grid;
      grid-template-columns: 300px 1fr;
      gap: 20px;
      padding: 20px;
    }}
    aside, section, .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    aside {{
      padding: 18px;
      height: fit-content;
      position: sticky;
      top: 16px;
    }}
    label {{
      display: block;
      margin: 14px 0 6px;
      font-size: 13px;
      font-weight: 650;
      color: #34495e;
    }}
    select, input {{
      width: 100%;
      min-height: 38px;
      border: 1px solid #ccd1d1;
      border-radius: 6px;
      background: #fff;
      padding: 7px;
      font: inherit;
    }}
    select[multiple] {{ min-height: 132px; }}
    .content {{
      display: grid;
      gap: 20px;
      min-width: 0;
    }}
    section {{ padding: 18px; min-width: 0; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(5, minmax(130px, 1fr));
      gap: 12px;
    }}
    .metric {{
      padding: 14px;
      background: #fbfcfd;
      border: 1px solid #e5e8e8;
      border-radius: 8px;
    }}
    .metric span {{
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    .metric strong {{
      font-size: 22px;
      line-height: 1.1;
    }}
    .grid2 {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .chart {{ width: 100%; height: 420px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid #eaeded;
      text-align: left;
      white-space: nowrap;
    }}
    th {{ background: #f4f6f7; position: sticky; top: 0; }}
    .table-wrap {{ max-height: 420px; overflow: auto; border: 1px solid #eaeded; border-radius: 8px; }}
    .note {{ font-size: 13px; color: var(--muted); margin-top: 10px; }}
    @media (max-width: 980px) {{
      main {{ grid-template-columns: 1fr; }}
      aside {{ position: static; }}
      .grid2, .metrics {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Firm Size and Profitability in China's A-Share Market</h1>
    <p>Interactive static dashboard for CSI 300 and CSI 500 constituent analysis. Data is embedded in this HTML file for GitHub Pages preview.</p>
  </header>
  <main>
    <aside>
      <h2>Filters</h2>
      <label for="yearSelect">Year</label>
      <select id="yearSelect" multiple></select>
      <label for="groupSelect">Index group</label>
      <select id="groupSelect" multiple></select>
      <label for="industrySelect">Industry</label>
      <select id="industrySelect" multiple></select>
      <label for="capMin">Market cap min, RMB bn</label>
      <input id="capMin" type="number" step="1" />
      <label for="capMax">Market cap max, RMB bn</label>
      <input id="capMax" type="number" step="1" />
      <p class="note">Use Cmd/Ctrl or Shift to select multiple values. ROA requires net income, which is not available in the current raw exports.</p>
    </aside>
    <div class="content">
      <section>
        <h2>Filtered Sample</h2>
        <div id="metrics" class="metrics"></div>
      </section>
      <section>
        <h2>Market Overview</h2>
        <div class="grid2">
          <div id="epsTrend" class="chart"></div>
          <div id="epsGrowth" class="chart"></div>
        </div>
      </section>
      <section>
        <h2>Firm Size and Profitability</h2>
        <div id="scatter" class="chart"></div>
      </section>
      <section>
        <h2>Industry Comparison</h2>
        <div class="grid2">
          <div id="industryBar" class="chart"></div>
          <div id="industryScatter" class="chart"></div>
        </div>
      </section>
      <section>
        <h2>Panel Regression Summary</h2>
        <div id="regChart" class="chart"></div>
        <div class="table-wrap"><table id="regTable"></table></div>
      </section>
      <section>
        <h2>Company Table</h2>
        <div class="table-wrap"><table id="firmTable"></table></div>
      </section>
    </div>
  </main>

  <script>
    const payload = {payload_json};
    const colors = {{"CSI 300": "#476fb3", "CSI 500": "#d88455"}};

    function fmt(value, digits = 2) {{
      if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
      return Number(value).toLocaleString(undefined, {{maximumFractionDigits: digits, minimumFractionDigits: digits}});
    }}
    function selectedValues(id) {{
      return Array.from(document.getElementById(id).selectedOptions).map(o => o.value);
    }}
    function fillSelect(id, values) {{
      const el = document.getElementById(id);
      el.innerHTML = "";
      values.forEach(v => {{
        const option = document.createElement("option");
        option.value = String(v);
        option.textContent = String(v);
        option.selected = true;
        el.appendChild(option);
      }});
    }}
    function median(values) {{
      const nums = values.filter(v => Number.isFinite(v)).sort((a, b) => a - b);
      if (!nums.length) return NaN;
      const mid = Math.floor(nums.length / 2);
      return nums.length % 2 ? nums[mid] : (nums[mid - 1] + nums[mid]) / 2;
    }}
    function mean(values) {{
      const nums = values.filter(v => Number.isFinite(v));
      return nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : NaN;
    }}
    function groupBy(rows, keys) {{
      const map = new Map();
      rows.forEach(row => {{
        const key = keys.map(k => row[k]).join("||");
        if (!map.has(key)) map.set(key, []);
        map.get(key).push(row);
      }});
      return Array.from(map.entries()).map(([key, items]) => {{
        const obj = {{}};
        keys.forEach((k, i) => obj[k] = key.split("||")[i]);
        obj.items = items;
        return obj;
      }});
    }}
    function currentRows() {{
      const years = selectedValues("yearSelect").map(Number);
      const groups = selectedValues("groupSelect");
      const industries = selectedValues("industrySelect");
      const capMin = Number(document.getElementById("capMin").value);
      const capMax = Number(document.getElementById("capMax").value);
      return payload.firm.filter(row =>
        years.includes(Number(row.year)) &&
        groups.includes(row.index_group) &&
        industries.includes(row.industry_label) &&
        Number(row.market_cap_billion) >= capMin &&
        Number(row.market_cap_billion) <= capMax
      );
    }}
    function renderMetrics(rows) {{
      const uniqueFirms = new Set(rows.map(r => r.ticker)).size;
      const html = [
        ["Firm observations", rows.length.toLocaleString()],
        ["Unique firms", uniqueFirms.toLocaleString()],
        ["Average EPS", fmt(mean(rows.map(r => Number(r.eps))))],
        ["Median market cap", fmt(median(rows.map(r => Number(r.market_cap_billion)))) + " bn"],
        ["Median assets", fmt(median(rows.map(r => Number(r.assets_billion)))) + " bn"],
      ].map(([label, value]) => `<div class="metric"><span>${{label}}</span><strong>${{value}}</strong></div>`).join("");
      document.getElementById("metrics").innerHTML = html;
    }}
    function renderMarket() {{
      Plotly.newPlot("epsTrend", [
        {{x: payload.eps.map(r => r.year), y: payload.eps.map(r => r.csi300_eps), mode: "lines+markers", name: "CSI 300", line: {{color: colors["CSI 300"]}}}},
        {{x: payload.eps.map(r => r.year), y: payload.eps.map(r => r.csi500_eps), mode: "lines+markers", name: "CSI 500", line: {{color: colors["CSI 500"]}}}},
      ], {{title: "EPS Trend", xaxis: {{title: "Year"}}, yaxis: {{title: "EPS"}}, margin: {{t: 45, l: 50, r: 20, b: 45}}}}, {{responsive: true}});

      Plotly.newPlot("epsGrowth", [
        {{x: payload.eps.slice(1).map(r => r.year), y: payload.eps.slice(1).map(r => r.csi300_eps_growth), type: "bar", name: "CSI 300", marker: {{color: colors["CSI 300"]}}}},
        {{x: payload.eps.slice(1).map(r => r.year), y: payload.eps.slice(1).map(r => r.csi500_eps_growth), type: "bar", name: "CSI 500", marker: {{color: colors["CSI 500"]}}}},
      ], {{title: "Annual EPS Growth", barmode: "group", xaxis: {{title: "Year"}}, yaxis: {{title: "Growth"}}, margin: {{t: 45, l: 50, r: 20, b: 45}}}}, {{responsive: true}});
    }}
    function renderScatter(rows) {{
      const traces = payload.groups.map(group => {{
        const part = rows.filter(r => r.index_group === group);
        return {{
          x: part.map(r => r.market_cap_billion),
          y: part.map(r => r.eps),
          text: part.map(r => `${{r.ticker}} ${{r.company_name}}<br>${{r.industry_label}}<br>Year: ${{r.year}}`),
          mode: "markers",
          type: "scatter",
          name: group,
          marker: {{color: colors[group], opacity: 0.68, size: 8}},
          hovertemplate: "%{{text}}<br>Market cap: %{{x:.2f}} bn<br>EPS: %{{y:.2f}}<extra></extra>",
        }};
      }});
      Plotly.newPlot("scatter", traces, {{
        title: "Market Capitalization vs EPS",
        xaxis: {{title: "Market cap, RMB billion", type: "log"}},
        yaxis: {{title: "EPS"}},
        margin: {{t: 45, l: 55, r: 20, b: 50}},
      }}, {{responsive: true}});
    }}
    function renderIndustry(rows) {{
      const grouped = groupBy(rows, ["year", "index_group", "industry_label"]).map(g => ({{
        year: Number(g.year),
        index_group: g.index_group,
        industry_label: g.industry_label,
        firms: new Set(g.items.map(r => r.ticker)).size,
        avg_eps: mean(g.items.map(r => Number(r.eps))),
        median_market_cap: median(g.items.map(r => Number(r.market_cap_billion))),
      }})).filter(r => Number.isFinite(r.avg_eps));
      const top = grouped.slice().sort((a, b) => b.avg_eps - a.avg_eps).slice(0, 24).reverse();
      Plotly.newPlot("industryBar", payload.groups.map(group => {{
        const part = top.filter(r => r.index_group === group);
        return {{x: part.map(r => r.avg_eps), y: part.map(r => `${{r.industry_label}} (${{r.year}})`), type: "bar", orientation: "h", name: group, marker: {{color: colors[group]}}}};
      }}), {{title: "Top Industry-Year Average EPS", xaxis: {{title: "Average EPS"}}, margin: {{t: 45, l: 155, r: 20, b: 45}}}}, {{responsive: true}});

      Plotly.newPlot("industryScatter", payload.groups.map(group => {{
        const part = grouped.filter(r => r.index_group === group);
        return {{
          x: part.map(r => r.median_market_cap),
          y: part.map(r => r.avg_eps),
          text: part.map(r => `${{r.industry_label}}<br>Year: ${{r.year}}<br>Firms: ${{r.firms}}`),
          mode: "markers",
          type: "scatter",
          name: group,
          marker: {{color: colors[group], size: part.map(r => Math.max(7, Math.sqrt(r.firms) * 2)), opacity: 0.72}},
          hovertemplate: "%{{text}}<br>Median market cap: %{{x:.2f}} bn<br>Avg EPS: %{{y:.2f}}<extra></extra>",
        }};
      }}), {{title: "Industry Size and Profitability", xaxis: {{title: "Median market cap, RMB billion", type: "log"}}, yaxis: {{title: "Average EPS"}}, margin: {{t: 45, l: 55, r: 20, b: 50}}}}, {{responsive: true}});
    }}
    function renderRegression() {{
      Plotly.newPlot("regChart", [{{
        x: payload.regression.map(r => r.model),
        y: payload.regression.map(r => r.log_market_cap_coef),
        error_y: {{type: "data", array: payload.regression.map(r => r.log_market_cap_se), visible: true}},
        type: "bar",
        marker: {{color: "#476fb3"}},
      }}], {{title: "Market Capitalization Coefficient Across Models", xaxis: {{title: "Model"}}, yaxis: {{title: "Coefficient"}}, margin: {{t: 45, l: 55, r: 20, b: 80}}}}, {{responsive: true}});

      const cols = ["model", "dependent_variable", "n_observations", "n_firms", "r_squared", "log_market_cap_coef", "log_market_cap_sig", "is_csi500_coef", "is_csi500_sig"];
      renderTable("regTable", payload.regression, cols, 20);
    }}
    function renderTable(id, rows, cols, limit) {{
      const limited = rows.slice(0, limit);
      const head = `<thead><tr>${{cols.map(c => `<th>${{c}}</th>`).join("")}}</tr></thead>`;
      const body = `<tbody>${{limited.map(row => `<tr>${{cols.map(c => `<td>${{typeof row[c] === "number" ? fmt(row[c], 3) : (row[c] ?? "")}}</td>`).join("")}}</tr>`).join("")}}</tbody>`;
      document.getElementById(id).innerHTML = head + body;
    }}
    function update() {{
      const rows = currentRows();
      renderMetrics(rows);
      renderScatter(rows);
      renderIndustry(rows);
      renderRegression();
      const cols = ["year", "index_group", "ticker", "company_name", "industry_label", "eps", "market_cap_billion", "assets_billion", "eps_asset_scaled"];
      const sorted = rows.slice().sort((a, b) => b.market_cap_billion - a.market_cap_billion);
      renderTable("firmTable", sorted, cols, 120);
    }}
    function init() {{
      fillSelect("yearSelect", payload.years);
      fillSelect("groupSelect", payload.groups);
      fillSelect("industrySelect", payload.industries);
      const caps = payload.firm.map(r => Number(r.market_cap_billion)).filter(Number.isFinite);
      document.getElementById("capMin").value = Math.floor(Math.min(...caps));
      document.getElementById("capMax").value = Math.ceil(Math.max(...caps));
      ["yearSelect", "groupSelect", "industrySelect", "capMin", "capMax"].forEach(id => document.getElementById(id).addEventListener("change", update));
      renderMarket();
      update();
    }}
    init();
  </script>
</body>
</html>
"""


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    payload = load_payload()
    output = DOCS_DIR / "index.html"
    output.write_text(build_html(payload), encoding="utf-8")
    print(f"Static dashboard saved to: {output}")


if __name__ == "__main__":
    main()
