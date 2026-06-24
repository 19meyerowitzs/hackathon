"""
HTML Generator for the Reputation Intelligence Cockpit.
Takes the structured report JSON and renders a fully styled HTML dashboard.
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reputation Intelligence Cockpit · {period} · {company}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    :root {{
      --pink: #EB3C8C; --blue: #5A6EFF; --green: #47FF8A; --yellow: #E8FF47;
      --orange: #FF9F47; --red: #FF4747; --purple: #C47BFF; --teal: #47FFE0;
      --font-headline: 'IBM Plex Sans', sans-serif;
      --font-body: 'Inter', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font-body); font-size: 15px; line-height: 1.55; color: #fff;
      background: radial-gradient(800px 500px at 12% 28%, rgba(235,60,140,0.40), transparent 65%),
                  radial-gradient(700px 600px at 88% 18%, rgba(90,110,255,0.40), transparent 60%),
                  linear-gradient(135deg, #080b14 0%, #0b1530 45%, #070a12 100%);
      background-attachment: fixed; min-height: 100vh;
    }}
    h1,h2,h3,h4 {{ font-family: var(--font-headline); line-height: 1.15; letter-spacing: -0.015em; font-weight: 600; }}
    .s-header {{
      background: rgba(8,11,20,0.65); backdrop-filter: blur(24px);
      border-bottom: 1px solid rgba(255,255,255,0.09);
      padding: 22px 32px 18px; display: flex; justify-content: space-between;
      align-items: flex-end; flex-wrap: wrap; gap: 16px;
    }}
    .h-eyebrow {{ font-size: 9px; letter-spacing: 4px; font-family: var(--font-mono); color: rgba(255,255,255,0.25); text-transform: uppercase; margin-bottom: 8px; }}
    .s-header h1 {{ font-size: 26px; font-weight: 300; color: #fff; letter-spacing: -0.5px; }}
    .pill {{ display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; font-size: 9px; letter-spacing: 2px; font-family: var(--font-mono); text-transform: uppercase; }}
    .pill-green {{ background: rgba(71,255,138,0.12); border: 1px solid rgba(71,255,138,0.28); color: var(--green); }}
    .pill-pink {{ background: rgba(235,60,140,0.14); border: 1px solid rgba(235,60,140,0.30); color: var(--pink); }}
    .page-wrap {{ padding: 36px 32px; max-width: 1180px; margin: 0 auto; }}
    .section-label {{
      font-size: 9px; letter-spacing: 3px; font-family: var(--font-mono);
      color: rgba(255,255,255,0.32); text-transform: uppercase;
      padding-bottom: 10px; margin-bottom: 18px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
      display: flex; justify-content: space-between; align-items: center;
    }}
    .section-label .meta {{ color: rgba(255,255,255,0.25); font-weight: 400; }}
    .section-block {{ margin-top: 36px; }}

    /* North Star */
    .northstar {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 1px; background: rgba(255,255,255,0.07); margin-bottom: 32px; }}
    .ns-main {{ background: linear-gradient(135deg, rgba(235,60,140,0.10) 0%, rgba(90,110,255,0.08) 100%); padding: 32px 36px; position: relative; }}
    .ns-main::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, var(--pink), var(--blue)); }}
    .ns-label {{ font-size: 9px; letter-spacing: 3px; font-family: var(--font-mono); color: rgba(255,255,255,0.4); text-transform: uppercase; margin-bottom: 16px; }}
    .ns-score-row {{ display: flex; align-items: baseline; gap: 16px; margin-bottom: 8px; }}
    .ns-score {{ font-family: var(--font-headline); font-size: 72px; font-weight: 800; letter-spacing: -0.04em; line-height: 1; color: #fff; }}
    .ns-max {{ font-size: 22px; color: rgba(255,255,255,0.3); font-family: var(--font-mono); }}
    .ns-delta {{ display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; font-family: var(--font-mono); font-size: 11px; background: rgba(71,255,138,0.12); border: 1px solid rgba(71,255,138,0.28); color: var(--green); }}
    .ns-meta {{ font-size: 13px; color: rgba(255,255,255,0.55); margin-top: 14px; line-height: 1.6; }}
    .ns-formula {{ background: rgba(0,0,0,0.30); padding: 24px 28px; }}
    .ns-formula-label {{ font-size: 9px; letter-spacing: 3px; font-family: var(--font-mono); color: rgba(255,255,255,0.3); margin-bottom: 14px; }}
    .ns-comp-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }}
    .ns-comp-row:last-child {{ border-bottom: none; }}
    .ns-comp-label {{ font-size: 12px; color: rgba(255,255,255,0.55); }}
    .ns-comp-val {{ font-family: var(--font-mono); font-size: 12px; color: #fff; }}
    .delta-pos {{ color: var(--green); }}
    .delta-neg {{ color: var(--red); }}
    .delta-flat {{ color: rgba(255,255,255,0.4); }}

    /* KPI Grid */
    .kpi-grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; background: rgba(255,255,255,0.07); }}
    .kpi-cell {{ background: rgba(8,11,20,0.85); padding: 22px 24px; }}
    .kpi-cell .label {{ font-size: 9px; letter-spacing: 2px; font-family: var(--font-mono); color: rgba(255,255,255,0.35); text-transform: uppercase; margin-bottom: 12px; }}
    .kpi-cell .val {{ font-size: 28px; font-weight: 300; letter-spacing: -0.5px; line-height: 1; margin-bottom: 8px; color: #fff; }}
    .kpi-cell .val .unit {{ font-size: 13px; color: rgba(255,255,255,0.45); margin-left: 4px; font-weight: 400; }}
    .kpi-cell .delta-row {{ display: flex; align-items: center; gap: 8px; }}
    .kpi-cell .delta {{ font-family: var(--font-mono); font-size: 10px; padding: 2px 6px; }}
    .kpi-cell .ctx {{ font-size: 11px; color: rgba(255,255,255,0.4); }}
    .delta-up {{ background: rgba(71,255,138,0.12); color: var(--green); border: 1px solid rgba(71,255,138,0.25); }}
    .delta-down {{ background: rgba(255,71,71,0.12); color: var(--red); border: 1px solid rgba(255,71,71,0.25); }}
    .delta-up-good {{ background: rgba(71,255,138,0.12); color: var(--green); border: 1px solid rgba(71,255,138,0.25); }}
    .delta-down-good {{ background: rgba(71,255,138,0.12); color: var(--green); border: 1px solid rgba(71,255,138,0.25); }}

    /* Strategic Issues */
    .issue-stack {{ display: flex; flex-direction: column; gap: 10px; }}
    .issue-card {{ background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.09); padding: 22px 24px; }}
    .issue-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 18px; }}
    .issue-rank-block {{ display: flex; gap: 14px; align-items: flex-start; flex: 1; }}
    .issue-rank {{ width: 36px; height: 36px; flex-shrink: 0; background: rgba(255,255,255,0.07); display: flex; align-items: center; justify-content: center; font-family: var(--font-headline); font-size: 14px; font-weight: 700; }}
    .issue-title {{ font-size: 15px; font-weight: 600; margin-bottom: 6px; color: #fff; }}
    .issue-meta {{ font-size: 11px; font-family: var(--font-mono); color: rgba(255,255,255,0.4); }}
    .issue-verdict {{ padding: 6px 14px; font-size: 10px; letter-spacing: 2px; font-family: var(--font-mono); text-transform: uppercase; font-weight: 700; flex-shrink: 0; }}
    .verdict-opportunity, .verdict-win {{ background: rgba(71,255,138,0.15); color: var(--green); border: 1px solid rgba(71,255,138,0.3); }}
    .verdict-risk {{ background: rgba(255,159,71,0.15); color: var(--orange); border: 1px solid rgba(255,159,71,0.3); }}
    .verdict-watch {{ background: rgba(232,255,71,0.12); color: var(--yellow); border: 1px solid rgba(232,255,71,0.28); }}
    .impact-bars {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 14px; }}
    .impact-bar-head {{ font-size: 9px; letter-spacing: 1.5px; font-family: var(--font-mono); color: rgba(255,255,255,0.4); margin-bottom: 6px; text-transform: uppercase; }}
    .impact-bar-track {{ height: 5px; background: rgba(255,255,255,0.08); position: relative; }}
    .impact-bar-fill {{ height: 100%; }}
    .impact-bar-val {{ font-family: var(--font-mono); font-size: 11px; margin-top: 5px; color: rgba(255,255,255,0.7); }}
    .issue-summary {{ font-size: 13px; color: rgba(255,255,255,0.6); line-height: 1.7; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.07); }}

    /* Coverage */
    .coverage-strip {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .coverage-pill {{ display: inline-flex; align-items: center; gap: 8px; padding: 7px 14px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.09); font-size: 13px; color: rgba(255,255,255,0.75); }}
    .coverage-pill .num {{ font-family: var(--font-mono); font-size: 11px; background: rgba(255,255,255,0.08); padding: 1px 7px; color: rgba(255,255,255,0.5); }}

    /* SoV */
    .sov-grid {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 1px; background: rgba(255,255,255,0.07); margin-bottom: 30px; }}
    .sov-bars {{ background: rgba(8,11,20,0.85); padding: 26px 28px; }}
    .sov-row {{ display: grid; grid-template-columns: 130px 1fr 80px 60px; gap: 14px; align-items: center; padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .sov-row:last-child {{ border-bottom: none; }}
    .sov-name {{ font-size: 13px; }}
    .sov-name.us {{ color: var(--pink); font-weight: 700; }}
    .sov-bar-track {{ height: 6px; background: rgba(255,255,255,0.08); }}
    .sov-bar-fill {{ height: 100%; }}
    .sov-pct {{ font-family: var(--font-mono); font-size: 12px; text-align: right; color: rgba(255,255,255,0.85); }}
    .sov-delta {{ font-family: var(--font-mono); font-size: 10px; padding: 2px 6px; text-align: center; }}
    .sov-context {{ background: rgba(0,0,0,0.30); padding: 26px 28px; }}
    .sov-context-row {{ padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }}
    .sov-context-row:last-child {{ border-bottom: none; }}
    .sov-context-label {{ font-size: 9px; letter-spacing: 2px; font-family: var(--font-mono); color: rgba(255,255,255,0.35); margin-bottom: 4px; text-transform: uppercase; }}
    .sov-context-val {{ font-size: 14px; font-weight: 600; color: #fff; }}
    .sov-context-sub {{ font-size: 11px; color: rgba(255,255,255,0.45); margin-top: 2px; }}

    /* Ownership */
    .ownership-table {{ width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); }}
    .ownership-table th, .ownership-table td {{ padding: 12px 14px; text-align: center; border: 1px solid rgba(255,255,255,0.05); font-size: 12px; }}
    .ownership-table th {{ background: rgba(0,0,0,0.35); font-family: var(--font-mono); font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(255,255,255,0.55); font-weight: 500; }}
    .ownership-table td:first-child {{ text-align: left; color: rgba(255,255,255,0.7); font-weight: 500; }}
    .own-lead {{ color: var(--green); font-size: 18px; font-weight: 700; }}
    .own-mid {{ color: var(--yellow); font-size: 18px; }}
    .own-low {{ color: rgba(255,255,255,0.18); font-size: 18px; }}

    /* Speaker Race */
    .speaker-bar-row {{ display: grid; grid-template-columns: 200px 60px 1fr 80px; gap: 14px; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .speaker-bar-row.us {{ background: rgba(235,60,140,0.04); margin: 0 -16px; padding: 10px 16px; }}
    .speaker-name {{ font-size: 13px; }}
    .speaker-name.us {{ color: var(--pink); font-weight: 600; }}
    .speaker-cite-count {{ font-family: var(--font-mono); font-size: 12px; color: rgba(255,255,255,0.7); text-align: right; }}
    .speaker-bar-track {{ height: 6px; background: rgba(255,255,255,0.08); }}
    .speaker-trend {{ font-family: var(--font-mono); font-size: 11px; text-align: right; }}

    /* Speed to Media */
    .speed-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }}
    .speed-card {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 20px; }}
    .speed-topic {{ font-size: 12px; font-weight: 600; margin-bottom: 8px; color: #fff; }}
    .speed-result {{ font-family: var(--font-headline); font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }}
    .speed-result.lead {{ color: var(--green); }}
    .speed-result.lag {{ color: var(--red); }}
    .speed-result.opp {{ color: var(--yellow); }}
    .speed-detail {{ font-size: 11px; color: rgba(255,255,255,0.45); line-height: 1.5; }}

    /* Cluster */
    .cluster-card {{ background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.09); padding: 24px 26px; margin-bottom: 12px; position: relative; }}
    .cluster-card::before {{ content: ''; position: absolute; top: 0; left: 0; bottom: 0; width: 3px; }}
    .cluster-card.controlled::before {{ background: var(--blue); }}
    .cluster-card.positive::before {{ background: var(--green); }}
    .cluster-card.gap::before {{ background: var(--orange); }}
    .cluster-card.risk::before {{ background: var(--red); }}
    .cluster-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 16px; }}
    .cluster-name {{ font-size: 17px; font-weight: 600; margin-bottom: 4px; }}
    .cluster-tagline {{ font-size: 12px; color: rgba(255,255,255,0.5); font-style: italic; }}
    .cluster-status {{ padding: 5px 12px; font-size: 9px; letter-spacing: 2px; font-family: var(--font-mono); text-transform: uppercase; font-weight: 700; flex-shrink: 0; }}
    .status-controlled {{ background: rgba(90,110,255,0.15); color: var(--blue); border: 1px solid rgba(90,110,255,0.3); }}
    .status-positive {{ background: rgba(71,255,138,0.15); color: var(--green); border: 1px solid rgba(71,255,138,0.3); }}
    .status-gap {{ background: rgba(255,159,71,0.15); color: var(--orange); border: 1px solid rgba(255,159,71,0.3); }}
    .status-risk {{ background: rgba(255,71,71,0.15); color: var(--red); border: 1px solid rgba(255,71,71,0.3); }}
    .cluster-stories {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }}
    .cluster-chip {{ padding: 5px 10px; font-size: 11px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); color: rgba(255,255,255,0.65); font-family: var(--font-mono); }}
    .cluster-metrics {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.07); }}
    .cluster-metric-label {{ font-size: 9px; letter-spacing: 2px; font-family: var(--font-mono); color: rgba(255,255,255,0.4); text-transform: uppercase; margin-bottom: 4px; }}
    .cluster-metric-val {{ font-size: 14px; font-weight: 500; color: #fff; font-family: var(--font-mono); }}
    .cluster-insight {{ margin-top: 14px; padding: 12px 14px; background: rgba(0,0,0,0.30); border-left: 2px solid rgba(255,255,255,0.2); font-size: 12px; color: rgba(255,255,255,0.6); line-height: 1.6; }}

    /* Momentum */
    .momentum-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
    .momentum-card {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); padding: 18px 20px; }}
    .momentum-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
    .momentum-topic {{ font-size: 13px; font-weight: 600; }}
    .momentum-arrow {{ font-family: var(--font-mono); font-size: 14px; }}
    .arrow-rising-strong {{ color: var(--green); }}
    .arrow-rising {{ color: var(--teal); }}
    .arrow-flat {{ color: rgba(255,255,255,0.4); }}
    .arrow-falling {{ color: var(--orange); }}
    .arrow-falling-strong {{ color: var(--red); }}
    .momentum-detail {{ font-size: 11px; color: rgba(255,255,255,0.5); line-height: 1.6; }}

    /* Risk Matrix */
    .risk-matrix-wrap {{ display: grid; grid-template-columns: 40px 1fr; grid-template-rows: 1fr 40px; gap: 8px; margin-bottom: 32px; }}
    .risk-matrix-y-axis {{ writing-mode: vertical-rl; transform: rotate(180deg); display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: 10px; letter-spacing: 3px; color: rgba(255,255,255,0.4); text-transform: uppercase; }}
    .risk-matrix {{ display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 1px; background: rgba(255,255,255,0.08); min-height: 320px; }}
    .risk-quadrant {{ background: rgba(8,11,20,0.85); padding: 16px; position: relative; }}
    .risk-quadrant.q-critical {{ background: rgba(255,71,71,0.06); }}
    .risk-quadrant.q-mitigate {{ background: rgba(255,159,71,0.06); }}
    .risk-quadrant.q-monitor {{ background: rgba(232,255,71,0.04); }}
    .risk-quadrant.q-accept {{ background: rgba(90,110,255,0.04); }}
    .quadrant-label {{ position: absolute; top: 10px; right: 12px; font-family: var(--font-mono); font-size: 9px; letter-spacing: 2px; text-transform: uppercase; }}
    .q-critical .quadrant-label {{ color: var(--red); }}
    .q-mitigate .quadrant-label {{ color: var(--orange); }}
    .q-monitor .quadrant-label {{ color: var(--yellow); }}
    .q-accept .quadrant-label {{ color: var(--blue); }}
    .risk-dot {{ display: inline-flex; flex-direction: column; gap: 4px; padding: 8px 10px; margin: 4px; max-width: calc(100% - 8px); background: rgba(0,0,0,0.4); border-left: 2px solid; font-size: 11px; }}
    .risk-dot.severity-high {{ border-color: var(--red); }}
    .risk-dot.severity-mid {{ border-color: var(--orange); }}
    .risk-dot.severity-low {{ border-color: var(--blue); }}
    .risk-dot-name {{ font-weight: 600; color: #fff; }}
    .risk-dot-meta {{ font-family: var(--font-mono); font-size: 10px; color: rgba(255,255,255,0.5); }}
    .risk-dot-trend {{ display: inline-block; font-family: var(--font-mono); font-size: 9px; padding: 1px 5px; margin-top: 2px; align-self: flex-start; }}
    .risk-matrix-x-axis {{ grid-column: 2; display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: 10px; letter-spacing: 3px; color: rgba(255,255,255,0.4); text-transform: uppercase; }}

    /* Risk Table */
    .risk-table {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); }}
    .risk-table-head, .risk-table-row {{ display: grid; grid-template-columns: 50px 2.2fr 90px 90px 110px 100px 80px; gap: 12px; padding: 12px 16px; align-items: center; }}
    .risk-table-head {{ background: rgba(0,0,0,0.4); font-family: var(--font-mono); font-size: 9px; letter-spacing: 2px; color: rgba(255,255,255,0.4); text-transform: uppercase; }}
    .risk-table-row {{ border-top: 1px solid rgba(255,255,255,0.05); font-size: 12px; }}
    .risk-id {{ font-family: var(--font-mono); color: rgba(255,255,255,0.4); }}
    .risk-num-cell {{ font-family: var(--font-mono); text-align: center; }}
    .severity-pill {{ display: inline-block; padding: 3px 9px; font-family: var(--font-mono); font-size: 10px; font-weight: 700; text-align: center; min-width: 70px; }}
    .sev-critical {{ background: rgba(255,71,71,0.15); color: var(--red); border: 1px solid rgba(255,71,71,0.3); }}
    .sev-high {{ background: rgba(255,159,71,0.15); color: var(--orange); border: 1px solid rgba(255,159,71,0.3); }}
    .sev-medium {{ background: rgba(232,255,71,0.12); color: var(--yellow); border: 1px solid rgba(232,255,71,0.28); }}
    .sev-low {{ background: rgba(90,110,255,0.15); color: var(--blue); border: 1px solid rgba(90,110,255,0.3); }}

    /* Action Center */
    .action-section {{ margin-bottom: 24px; }}
    .action-section-head {{ display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }}
    .priority-badge {{ padding: 4px 10px; font-family: var(--font-mono); font-size: 9px; letter-spacing: 2px; text-transform: uppercase; font-weight: 700; }}
    .priority-p0 {{ background: rgba(255,71,71,0.15); color: var(--red); border: 1px solid rgba(255,71,71,0.3); }}
    .priority-p1 {{ background: rgba(255,159,71,0.15); color: var(--orange); border: 1px solid rgba(255,159,71,0.3); }}
    .priority-p2 {{ background: rgba(90,110,255,0.15); color: var(--blue); border: 1px solid rgba(90,110,255,0.3); }}
    .action-cards {{ display: flex; flex-direction: column; gap: 8px; }}
    .action-card {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); padding: 18px 20px; display: grid; grid-template-columns: 1fr auto; gap: 16px; align-items: start; }}
    .action-title {{ font-size: 14px; font-weight: 600; color: #fff; margin-bottom: 8px; }}
    .action-meta {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: 11px; color: rgba(255,255,255,0.45); }}
    .action-meta .meta-item {{ font-family: var(--font-mono); }}
    .action-meta .meta-label {{ color: rgba(255,255,255,0.25); margin-right: 4px; }}
    .action-impact {{ font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 6px; font-style: italic; }}
    .action-link {{ font-size: 10px; font-family: var(--font-mono); color: rgba(255,255,255,0.3); margin-top: 4px; }}
    .action-status {{ padding: 5px 12px; font-size: 9px; letter-spacing: 2px; font-family: var(--font-mono); text-transform: uppercase; font-weight: 700; white-space: nowrap; align-self: flex-start; }}
    .action-stat-progress {{ background: rgba(90,110,255,0.15); color: var(--blue); border: 1px solid rgba(90,110,255,0.3); }}
    .action-stat-todo {{ background: rgba(255,159,71,0.12); color: var(--orange); border: 1px solid rgba(255,159,71,0.25); }}
    .action-stat-done {{ background: rgba(71,255,138,0.12); color: var(--green); border: 1px solid rgba(71,255,138,0.25); }}

    /* Tab navigation */
    .s-tabs {{ background: rgba(8,11,20,0.55); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; overflow-x: auto; }}
    .tab-btn {{ border: none; padding: 14px 22px; cursor: pointer; font-size: 12px; font-weight: 500; letter-spacing: 0.3px; white-space: nowrap; border-right: 1px solid rgba(255,255,255,0.07); color: rgba(255,255,255,0.45); background: transparent; font-family: var(--font-body); display: flex; align-items: center; gap: 8px; transition: all 0.15s; }}
    .tab-btn:hover {{ color: rgba(255,255,255,0.85); background: rgba(255,255,255,0.04); }}
    .tab-btn.active {{ font-weight: 700; color: #fff; }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    @media (max-width: 900px) {{
      .kpi-grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
      .northstar {{ grid-template-columns: 1fr; }}
      .sov-grid {{ grid-template-columns: 1fr; }}
      .impact-bars {{ grid-template-columns: repeat(3, 1fr); }}
      .speed-grid {{ grid-template-columns: 1fr; }}
      .momentum-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
  </style>
</head>
<body>
  <header class="s-header">
    <div>
      <div class="h-eyebrow">⬢ Reputation Intelligence Cockpit</div>
      <h1>{period} · {company}</h1>
    </div>
    <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
      <span class="pill pill-green">● Live Report</span>
      <span class="pill pill-pink">AI-generiert</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:rgba(255,255,255,0.3);">Generiert: {generated_at}</span>
    </div>
  </header>

  <nav class="s-tabs">
    <button class="tab-btn active" onclick="showTab('command-center')">⬢ Command Center</button>
    <button class="tab-btn" onclick="showTab('competitive')">⚡ Competitive Intel</button>
    <button class="tab-btn" onclick="showTab('narrative')">◎ Narrative &amp; Momentum</button>
    <button class="tab-btn" onclick="showTab('risk')">⚠ Risk Radar</button>
    <button class="tab-btn" onclick="showTab('actions')">→ Action Center</button>
  </nav>

  <!-- TAB: Command Center -->
  <div id="tab-command-center" class="tab-content active">
    <div class="page-wrap">
      <!-- North Star -->
      <div class="northstar">
        <div class="ns-main">
          <div class="ns-label">⬢ Reputation Health Index · {period}</div>
          <div class="ns-score-row">
            <div class="ns-score">{ns_score}</div>
            <div class="ns-max">/ 100</div>
            <div class="ns-delta">▲ {ns_delta} vs. Vormonat</div>
          </div>
          <div class="ns-meta">{ns_verdict}</div>
        </div>
        <div class="ns-formula">
          <div class="ns-formula-label">Composite-Komponenten</div>
          {ns_components_html}
        </div>
      </div>

      <!-- Primary KPIs -->
      <div class="section-label"><span>Primäre KPIs · {period}</span><span class="meta">{total_articles} Abdrucke gesamt</span></div>
      <div class="kpi-grid-4">
        {kpi_cells_html}
      </div>

      <!-- Strategic Issues -->
      <div class="section-block">
        <div class="section-label">
          <span>Strategische Themen · Executive Impact Scorecard</span>
          <span class="meta">{strategic_count} priorisiert</span>
        </div>
        <div class="issue-stack">
          {issues_html}
        </div>
      </div>

      <!-- Coverage Footprint -->
      <div class="section-block">
        <div class="section-label"><span>Coverage Footprint</span><span class="meta">{total_articles} Abdrucke gesamt</span></div>
        <div class="coverage-strip">
          {coverage_html}
        </div>
      </div>
    </div>
  </div>

  <!-- TAB: Competitive -->
  <div id="tab-competitive" class="tab-content">
    <div class="page-wrap">
      <div class="section-label"><span>Share of Voice · Wettbewerb</span></div>
      <div class="sov-grid">
        <div class="sov-bars">
          {sov_bars_html}
        </div>
        <div class="sov-context">
          {sov_context_html}
        </div>
      </div>

      <!-- Topic Ownership -->
      <div class="section-block">
        <div class="section-label"><span>Topic Ownership Matrix</span></div>
        {ownership_html}
      </div>

      <!-- Speaker Race -->
      <div class="section-block">
        <div class="section-label"><span>Executive Visibility · Speaker Race</span></div>
        {speaker_html}
      </div>

      <!-- Speed to Media -->
      <div class="section-block">
        <div class="section-label"><span>Speed-to-Media · Reaktionszeit-Analyse</span></div>
        <div class="speed-grid">
          {speed_html}
        </div>
      </div>
    </div>
  </div>

  <!-- TAB: Narrative -->
  <div id="tab-narrative" class="tab-content">
    <div class="page-wrap">
      <div class="section-label"><span>Narrative Cluster-Analyse</span><span class="meta">{cluster_count} Cluster identifiziert</span></div>
      {clusters_html}

      <div class="section-block">
        <div class="section-label"><span>Topic Momentum</span></div>
        <div class="momentum-grid">
          {momentum_html}
        </div>
      </div>
    </div>
  </div>

  <!-- TAB: Risk -->
  <div id="tab-risk" class="tab-content">
    <div class="page-wrap">
      <div class="section-label"><span>Risk Matrix · Probability × Impact</span></div>
      <div class="risk-matrix-wrap">
        <div class="risk-matrix-y-axis">Wahrscheinlichkeit</div>
        <div class="risk-matrix">
          <div class="risk-quadrant q-critical">
            <div class="quadrant-label">Critical</div>
            {risk_critical_html}
          </div>
          <div class="risk-quadrant q-mitigate">
            <div class="quadrant-label">Mitigate</div>
            {risk_mitigate_html}
          </div>
          <div class="risk-quadrant q-monitor">
            <div class="quadrant-label">Monitor</div>
            {risk_monitor_html}
          </div>
          <div class="risk-quadrant q-accept">
            <div class="quadrant-label">Accept</div>
            {risk_accept_html}
          </div>
        </div>
        <div></div>
        <div class="risk-matrix-x-axis">Impact</div>
      </div>

      <!-- Risk Register -->
      <div class="section-label"><span>Risk Register</span></div>
      <div class="risk-table">
        <div class="risk-table-head">
          <div>ID</div><div>Risiko</div><div>Prob. %</div><div>Impact /10</div>
          <div>Severity</div><div>Owner</div><div>Status</div>
        </div>
        {risk_register_html}
      </div>
    </div>
  </div>

  <!-- TAB: Actions -->
  <div id="tab-actions" class="tab-content">
    <div class="page-wrap">
      <div class="section-label"><span>Action Center · Priorisierte Maßnahmen</span></div>
      {actions_html}
    </div>
  </div>

  <script>
    function showTab(name) {{
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + name).classList.add('active');
      event.currentTarget.classList.add('active');
    }}
  </script>
</body>
</html>"""


def _own_symbol(level: str) -> str:
    if level == "lead":
        return '<span class="own-lead">●</span>'
    if level == "mid":
        return '<span class="own-mid">◐</span>'
    return '<span class="own-low">○</span>'


def _risk_dot(risk: dict) -> str:
    severity = "high" if risk.get("trend", "").startswith("▲") else "mid"
    return f"""<div class="risk-dot severity-{severity}">
      <div class="risk-dot-name">{risk.get('name', '')}</div>
      <div class="risk-dot-trend {risk.get('trendCls', '')}">{risk.get('trend', '')}</div>
    </div>"""


def _action_cards(actions: list) -> str:
    out = []
    for a in actions:
        out.append(f"""<div class="action-card">
      <div>
        <div class="action-title">{a.get('title', '')}</div>
        <div class="action-meta">
          <span class="meta-item"><span class="meta-label">Owner</span>{a.get('owner', '')}</span>
          <span class="meta-item"><span class="meta-label">Deadline</span>{a.get('deadline', '')}</span>
          <span class="meta-item"><span class="meta-label">Aufwand</span>{a.get('effort', '')}</span>
        </div>
        <div class="action-impact">{a.get('impact', '')}</div>
        <div class="action-link">{a.get('link', '')}</div>
      </div>
      <div class="action-status {a.get('statusCls', '')}">{a.get('status', '')}</div>
    </div>""")
    return "\n".join(out)


def generate_html(report: dict) -> str:
    """
    Generate a fully styled HTML dashboard from the structured report JSON.
    """
    meta = report.get("meta", {})
    northstar = report.get("northstar", {})
    primary_kpis = report.get("primary_kpis", [])
    strategic_issues = report.get("strategic_issues", [])
    coverage = report.get("coverage_footprint", [])
    sov_data = report.get("sov_data", [])
    sov_context = report.get("sov_context", [])
    topic_ownership = report.get("topic_ownership", {})
    speaker_race = report.get("speaker_race", [])
    speed_events = report.get("speed_events", [])
    clusters = report.get("clusters", [])
    momentum = report.get("momentum", [])
    risks_matrix = report.get("risks_matrix", {})
    risk_register = report.get("risk_register", [])
    actions = report.get("actions", {})

    # ── North Star components
    ns_components_html = ""
    for c in northstar.get("components", []):
        ns_components_html += f"""<div class="ns-comp-row">
      <div class="ns-comp-label">{c.get('label', '')}</div>
      <div class="ns-comp-val">{c.get('val', '')} <span class="{c.get('cls', '')}">{c.get('delta', '')}</span></div>
    </div>"""

    # ── KPI cells
    kpi_cells_html = ""
    for k in primary_kpis:
        kpi_cells_html += f"""<div class="kpi-cell">
      <div class="label">{k.get('label', '')}</div>
      <div class="val">{k.get('val', '')}<span class="unit">{k.get('unit', '')}</span></div>
      <div class="delta-row">
        <span class="delta {k.get('deltaClass', '')}">{k.get('delta', '')}</span>
        <span class="ctx">{k.get('ctx', '')}</span>
      </div>
    </div>"""

    # ── Strategic Issues
    dims = [("reputation", "Reputation"), ("revenue", "Revenue"), ("talent", "Talent"), ("investor", "Investor"), ("political", "Political")]
    issues_html = ""
    for iss in strategic_issues:
        bars = ""
        for key, label in dims:
            imp = iss.get("impact", {}).get(key, {"val": 0, "color": "rgba(255,255,255,0.3)"})
            bars += f"""<div class="impact-bar">
          <div class="impact-bar-head">{label}</div>
          <div class="impact-bar-track"><div class="impact-bar-fill" style="width:{imp.get('val',0)*10}%;background:{imp.get('color','rgba(255,255,255,0.3)}')}"></div></div>
          <div class="impact-bar-val">{imp.get('val', 0)}/10</div>
        </div>"""
        issues_html += f"""<div class="issue-card">
      <div class="issue-head">
        <div class="issue-rank-block">
          <div class="issue-rank">#{iss.get('rank', '')}</div>
          <div>
            <div class="issue-title">{iss.get('title', '')}</div>
            <div class="issue-meta">{iss.get('meta', '')}</div>
          </div>
        </div>
        <div class="issue-verdict {iss.get('verdictCls', '')}">{iss.get('verdict', '')}</div>
      </div>
      <div class="impact-bars">{bars}</div>
      <div class="issue-summary">{iss.get('summary', '')}</div>
    </div>"""

    # ── Coverage
    coverage_html = "".join(
        f'<div class="coverage-pill">{c.get("source", "")}<span class="num">{c.get("count", "")}</span></div>'
        for c in coverage
    )

    # ── SoV bars
    sov_bars_html = ""
    for s in sov_data:
        name_cls = "us" if s.get("us") else ""
        sov_bars_html += f"""<div class="sov-row">
      <div class="sov-name {name_cls}">{s.get('name', '')}</div>
      <div class="sov-bar-track"><div class="sov-bar-fill" style="width:{s.get('pct',0)}%;background:{s.get('color','rgba(255,255,255,0.4)')}"></div></div>
      <div class="sov-pct">{s.get('pct', 0)}%</div>
      <div class="sov-delta {s.get('cls', '')}">{s.get('delta', '')}</div>
    </div>"""

    sov_context_html = "".join(
        f"""<div class="sov-context-row">
      <div class="sov-context-label">{c.get('label', '')}</div>
      <div class="sov-context-val">{c.get('val', '')}</div>
      <div class="sov-context-sub">{c.get('sub', '')}</div>
    </div>"""
        for c in sov_context
    )

    # ── Topic Ownership table
    topics = topic_ownership.get("topics", [])
    companies = topic_ownership.get("companies", {})
    ownership_html = ""
    if topics and companies:
        header_cells = "".join(f"<th>{t}</th>" for t in topics)
        rows = ""
        for company_name, levels in companies.items():
            cells = "".join(f"<td>{_own_symbol(l)}</td>" for l in levels)
            rows += f"<tr><td>{company_name}</td>{cells}</tr>"
        ownership_html = f"""<table class="ownership-table">
      <thead><tr><th>Company</th>{header_cells}</tr></thead>
      <tbody>{rows}</tbody>
    </table>"""

    # ── Speaker Race
    speaker_html = ""
    max_count = max((s.get("count", 1) for s in speaker_race), default=1)
    for s in speaker_race:
        us = s.get("us", False)
        bar_w = int((s.get("count", 0) / max_count) * 100)
        speaker_html += f"""<div class="speaker-bar-row {'us' if us else ''}">
      <div class="speaker-name {'us' if us else ''}">{s.get('name', '')}</div>
      <div class="speaker-cite-count">{s.get('count', 0)}</div>
      <div class="speaker-bar-track"><div class="sov-bar-fill" style="width:{bar_w}%;background:{'var(--pink)' if us else 'rgba(255,255,255,0.3)'}"></div></div>
      <div class="speaker-trend {s.get('trendCls', '')}">{s.get('trend', '')}</div>
    </div>"""

    # ── Speed to Media
    speed_html = "".join(
        f"""<div class="speed-card">
      <div class="speed-topic">{e.get('topic', '')}</div>
      <div class="speed-result {e.get('resultCls', '')}">{e.get('result', '')}</div>
      <div class="speed-detail">{e.get('detail', '')}</div>
    </div>"""
        for e in speed_events
    )

    # ── Clusters
    clusters_html = ""
    for c in clusters:
        chips = "".join(f'<div class="cluster-chip">{s}</div>' for s in c.get("stories", []))
        clusters_html += f"""<div class="cluster-card {c.get('cls', '')}">
      <div class="cluster-head">
        <div>
          <div class="cluster-name">{c.get('name', '')}</div>
          <div class="cluster-tagline">{c.get('tagline', '')}</div>
        </div>
        <div class="cluster-status {c.get('statusCls', '')}">{c.get('status', '')}</div>
      </div>
      <div class="cluster-stories">{chips}</div>
      <div class="cluster-metrics">
        <div><div class="cluster-metric-label">Sentiment</div><div class="cluster-metric-val">{c.get('sentiment', '')}</div></div>
        <div><div class="cluster-metric-label">Co-Occurrence</div><div class="cluster-metric-val">{c.get('coOccurrence', '')}</div></div>
        <div><div class="cluster-metric-label">Risk Level</div><div class="cluster-metric-val">{c.get('risk', '')}</div></div>
      </div>
      <div class="cluster-insight">{c.get('insight', '')}</div>
    </div>"""

    # ── Momentum
    momentum_html = "".join(
        f"""<div class="momentum-card">
      <div class="momentum-head">
        <div class="momentum-topic">{m.get('topic', '')}</div>
        <div class="momentum-arrow {m.get('arrowCls', '')}">{m.get('arrow', '')}</div>
      </div>
      <div class="momentum-detail">{m.get('detail', '')}</div>
    </div>"""
        for m in momentum
    )

    # ── Risk Matrix quadrants
    risk_critical_html = "".join(_risk_dot(r) for r in risks_matrix.get("critical", []))
    risk_mitigate_html = "".join(_risk_dot(r) for r in risks_matrix.get("mitigate", []))
    risk_monitor_html = "".join(_risk_dot(r) for r in risks_matrix.get("monitor", []))
    risk_accept_html = "".join(_risk_dot(r) for r in risks_matrix.get("accept", []))

    # ── Risk Register rows
    risk_register_html = ""
    for r in risk_register:
        risk_register_html += f"""<div class="risk-table-row">
      <div class="risk-id">{r.get('id', '')}</div>
      <div>{r.get('title', '')}</div>
      <div class="risk-num-cell">{r.get('prob', '')}%</div>
      <div class="risk-num-cell">{r.get('impact', '')}/10</div>
      <div><span class="severity-pill {r.get('sevCls', '')}">{r.get('severity', '')}</span></div>
      <div style="font-size:11px;color:rgba(255,255,255,0.6);">{r.get('owner', '')}</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.5);">{r.get('status', '')}</div>
    </div>"""

    # ── Actions
    priority_labels = {"p0": ("P0 — Sofort", "priority-p0"), "p1": ("P1 — Diese Woche", "priority-p1"), "p2": ("P2 — Diesen Monat", "priority-p2")}
    actions_html = ""
    for prio, (label, cls) in priority_labels.items():
        items = actions.get(prio, [])
        if not items:
            continue
        actions_html += f"""<div class="action-section">
      <div class="action-section-head">
        <span class="priority-badge {cls}">{label}</span>
        <span style="font-size:11px;color:rgba(255,255,255,0.35);font-family:var(--font-mono);">{len(items)} Maßnahmen</span>
      </div>
      <div class="action-cards">{_action_cards(items)}</div>
    </div>"""

    return HTML_TEMPLATE.format(
        period=meta.get("period", ""),
        company=meta.get("company", "OMG Germany"),
        generated_at=__import__('datetime').datetime.now().strftime("%d.%m.%Y %H:%M"),
        ns_score=northstar.get("score", "—"),
        ns_delta=northstar.get("delta", "0"),
        ns_verdict=northstar.get("verdict", ""),
        ns_components_html=ns_components_html,
        total_articles=meta.get("total_articles", "—"),
        kpi_cells_html=kpi_cells_html,
        strategic_count=len(strategic_issues),
        issues_html=issues_html,
        coverage_html=coverage_html,
        sov_bars_html=sov_bars_html,
        sov_context_html=sov_context_html,
        ownership_html=ownership_html,
        speaker_html=speaker_html,
        speed_html=speed_html,
        cluster_count=len(clusters),
        clusters_html=clusters_html,
        momentum_html=momentum_html,
        risk_critical_html=risk_critical_html,
        risk_mitigate_html=risk_mitigate_html,
        risk_monitor_html=risk_monitor_html,
        risk_accept_html=risk_accept_html,
        risk_register_html=risk_register_html,
        actions_html=actions_html,
    )
