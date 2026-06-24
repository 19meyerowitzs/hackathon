"""
HTML Generator for the MoM Comparison Report.
"""

COMPARISON_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>MoM Vergleich · {period_current} vs {period_previous} · {company}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    :root{{--pink:#EB3C8C;--blue:#5A6EFF;--green:#47FF8A;--yellow:#E8FF47;--orange:#FF9F47;--red:#FF4747;--teal:#47FFE0;
           --font-headline:'IBM Plex Sans',sans-serif;--font-body:'Inter',sans-serif;--font-mono:'JetBrains Mono',monospace;}}
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:var(--font-body);font-size:15px;line-height:1.55;color:#fff;
      background:radial-gradient(800px 500px at 12% 28%,rgba(235,60,140,0.40),transparent 65%),
                 radial-gradient(700px 600px at 88% 18%,rgba(90,110,255,0.40),transparent 60%),
                 linear-gradient(135deg,#080b14 0%,#0b1530 45%,#070a12 100%);
      background-attachment:fixed;min-height:100vh;}}
    h1,h2,h3,h4{{font-family:var(--font-headline);line-height:1.15;letter-spacing:-0.015em;font-weight:600;}}
    .header{{background:rgba(8,11,20,0.65);backdrop-filter:blur(24px);border-bottom:1px solid rgba(255,255,255,0.09);
             padding:22px 32px;display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:16px;}}
    .eyebrow{{font-size:9px;letter-spacing:4px;font-family:var(--font-mono);color:rgba(255,255,255,0.25);text-transform:uppercase;margin-bottom:8px;}}
    .header h1{{font-size:26px;font-weight:300;color:#fff;letter-spacing:-0.5px;}}
    .pill{{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;font-size:9px;letter-spacing:2px;font-family:var(--font-mono);text-transform:uppercase;}}
    .pill-teal{{background:rgba(71,255,224,0.12);border:1px solid rgba(71,255,224,0.28);color:var(--teal);}}
    .page{{padding:36px 32px;max-width:1180px;margin:0 auto;}}
    .section-label{{font-size:9px;letter-spacing:3px;font-family:var(--font-mono);color:rgba(255,255,255,0.32);text-transform:uppercase;
                    padding-bottom:10px;margin-bottom:18px;border-bottom:1px solid rgba(255,255,255,0.07);
                    display:flex;justify-content:space-between;align-items:center;}}
    .section-block{{margin-top:36px;}}
    /* Score comparison */
    .score-compare{{display:grid;grid-template-columns:1fr 80px 1fr;gap:1px;background:rgba(255,255,255,0.07);margin-bottom:32px;}}
    .score-cell{{background:rgba(8,11,20,0.85);padding:28px 32px;}}
    .score-cell.current{{background:linear-gradient(135deg,rgba(235,60,140,0.10),rgba(90,110,255,0.08));position:relative;}}
    .score-cell.current::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--pink),var(--blue));}}
    .score-period{{font-size:9px;letter-spacing:3px;font-family:var(--font-mono);color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:12px;}}
    .score-num{{font-family:var(--font-headline);font-size:64px;font-weight:800;letter-spacing:-0.04em;line-height:1;margin-bottom:8px;}}
    .score-num.current-score{{color:#fff;}}
    .score-num.prev-score{{color:rgba(255,255,255,0.4);}}
    .score-interp{{font-size:13px;color:rgba(255,255,255,0.5);line-height:1.6;}}
    .delta-center{{background:rgba(0,0,0,0.4);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;}}
    .delta-big{{font-family:var(--font-headline);font-size:28px;font-weight:800;}}
    .delta-label{{font-size:9px;letter-spacing:2px;font-family:var(--font-mono);text-transform:uppercase;}}
    .delta-pos{{color:var(--green);}} .delta-neg{{color:var(--red);}} .delta-flat{{color:rgba(255,255,255,0.4);}}
    /* KPI deltas */
    .kpi-delta-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:rgba(255,255,255,0.07);}}
    .kpi-delta-cell{{background:rgba(8,11,20,0.85);padding:20px 22px;}}
    .kd-label{{font-size:9px;letter-spacing:2px;font-family:var(--font-mono);color:rgba(255,255,255,0.35);text-transform:uppercase;margin-bottom:10px;}}
    .kd-values{{display:flex;align-items:baseline;gap:12px;margin-bottom:6px;}}
    .kd-curr{{font-size:22px;font-weight:300;color:#fff;}}
    .kd-prev{{font-size:13px;color:rgba(255,255,255,0.3);}}
    .kd-delta{{font-family:var(--font-mono);font-size:11px;padding:2px 8px;}}
    .delta-tag-pos{{background:rgba(71,255,138,0.12);color:var(--green);border:1px solid rgba(71,255,138,0.25);}}
    .delta-tag-neg{{background:rgba(255,71,71,0.12);color:var(--red);border:1px solid rgba(255,71,71,0.25);}}
    .delta-tag-flat{{background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.4);border:1px solid rgba(255,255,255,0.1);}}
    .kd-interp{{font-size:11px;color:rgba(255,255,255,0.4);line-height:1.5;}}
    /* Issues */
    .issue-row{{display:flex;gap:16px;}}
    .issue-col{{flex:1;}}
    .issue-col-label{{font-size:9px;letter-spacing:3px;font-family:var(--font-mono);text-transform:uppercase;margin-bottom:12px;}}
    .issue-col-label.new-col{{color:var(--green);}} .issue-col-label.resolved-col{{color:rgba(255,255,255,0.3);}}
    .mini-card{{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);padding:14px 16px;margin-bottom:8px;}}
    .mini-title{{font-size:13px;font-weight:600;margin-bottom:4px;}}
    .mini-summary{{font-size:11px;color:rgba(255,255,255,0.5);line-height:1.5;}}
    .verdict-tag{{display:inline-block;padding:3px 8px;font-size:9px;letter-spacing:1.5px;font-family:var(--font-mono);text-transform:uppercase;font-weight:700;margin-bottom:6px;}}
    .verdict-opportunity,.verdict-win{{background:rgba(71,255,138,0.15);color:var(--green);border:1px solid rgba(71,255,138,0.3);}}
    .verdict-risk{{background:rgba(255,159,71,0.15);color:var(--orange);border:1px solid rgba(255,159,71,0.3);}}
    .verdict-watch{{background:rgba(232,255,71,0.12);color:var(--yellow);border:1px solid rgba(232,255,71,0.28);}}
    /* SoV movement */
    .sov-move-row{{display:grid;grid-template-columns:160px 60px 1fr 60px 1fr 80px;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);}}
    .sov-move-row:last-child{{border-bottom:none;}}
    .sov-co-name{{font-size:13px;}} .sov-co-name.us{{color:var(--pink);font-weight:600;}}
    .sov-pct{{font-family:var(--font-mono);font-size:12px;text-align:center;color:rgba(255,255,255,0.7);}}
    .sov-bar-track{{height:6px;background:rgba(255,255,255,0.08);}}
    .sov-bar-fill{{height:100%;}}
    .sov-delta-tag{{font-family:var(--font-mono);font-size:10px;padding:2px 6px;text-align:center;}}
    /* Risk changes */
    .risk-section{{margin-bottom:20px;}}
    .risk-section-label{{font-size:9px;letter-spacing:2px;font-family:var(--font-mono);text-transform:uppercase;color:rgba(255,255,255,0.35);margin-bottom:10px;}}
    .risk-change-row{{display:flex;gap:12px;align-items:flex-start;padding:10px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);margin-bottom:6px;}}
    .risk-change-id{{font-family:var(--font-mono);font-size:10px;color:rgba(255,255,255,0.3);flex-shrink:0;padding-top:2px;}}
    .risk-change-title{{font-size:13px;font-weight:500;margin-bottom:3px;}}
    .risk-change-comment{{font-size:11px;color:rgba(255,255,255,0.45);}}
    .sev-pill{{display:inline-block;padding:2px 8px;font-family:var(--font-mono);font-size:9px;font-weight:700;margin-left:8px;}}
    .sev-critical{{background:rgba(255,71,71,0.15);color:var(--red);border:1px solid rgba(255,71,71,0.3);}}
    .sev-high{{background:rgba(255,159,71,0.15);color:var(--orange);border:1px solid rgba(255,159,71,0.3);}}
    .sev-medium{{background:rgba(232,255,71,0.12);color:var(--yellow);border:1px solid rgba(232,255,71,0.28);}}
    /* Momentum shifts */
    .momentum-shift-row{{display:grid;grid-template-columns:200px 60px 20px 60px 1fr;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);}}
    .momentum-topic{{font-size:13px;}}
    .m-arrow{{font-family:var(--font-mono);font-size:14px;text-align:center;}}
    .m-arrow-icon{{font-family:var(--font-mono);font-size:10px;color:rgba(255,255,255,0.3);text-align:center;}}
    .m-comment{{font-size:11px;color:rgba(255,255,255,0.45);}}
    /* Actions summary */
    .action-summary-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:rgba(255,255,255,0.07);}}
    .as-cell{{background:rgba(8,11,20,0.85);padding:22px 24px;}}
    .as-label{{font-size:9px;letter-spacing:2px;font-family:var(--font-mono);color:rgba(255,255,255,0.35);text-transform:uppercase;margin-bottom:10px;}}
    .as-val{{font-size:32px;font-weight:300;color:#fff;}}
    /* Reco */
    .reco-card{{background:rgba(255,255,255,0.045);border:1px solid rgba(255,255,255,0.09);padding:20px 22px;margin-bottom:10px;display:flex;gap:16px;align-items:flex-start;}}
    .reco-prio{{padding:4px 10px;font-family:var(--font-mono);font-size:9px;letter-spacing:2px;text-transform:uppercase;font-weight:700;flex-shrink:0;}}
    .p0-badge{{background:rgba(255,71,71,0.15);color:var(--red);border:1px solid rgba(255,71,71,0.3);}}
    .p1-badge{{background:rgba(255,159,71,0.15);color:var(--orange);border:1px solid rgba(255,159,71,0.3);}}
    .p2-badge{{background:rgba(90,110,255,0.15);color:var(--blue);border:1px solid rgba(90,110,255,0.3);}}
    .reco-title{{font-size:14px;font-weight:600;margin-bottom:4px;}}
    .reco-rationale{{font-size:12px;color:rgba(255,255,255,0.5);line-height:1.6;}}
    /* Key items */
    .key-list{{display:flex;flex-direction:column;gap:8px;}}
    .key-item{{display:flex;gap:10px;align-items:flex-start;padding:12px 16px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);}}
    .key-item.win::before{{content:'✓';color:var(--green);font-weight:700;flex-shrink:0;}}
    .key-item.risk-item::before{{content:'⚠';color:var(--orange);flex-shrink:0;}}
    .key-item-text{{font-size:13px;color:rgba(255,255,255,0.7);}}
    /* Exec summary */
    .exec-summary{{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-left:3px solid var(--teal);padding:22px 26px;margin-bottom:32px;font-size:15px;line-height:1.7;color:rgba(255,255,255,0.8);}}
  </style>
</head>
<body>
  <header class="header">
    <div>
      <div class="eyebrow">⬢ Month-over-Month Vergleich · Reputation Intelligence</div>
      <h1>{period_current} vs. {period_previous} · {company}</h1>
    </div>
    <div style="display:flex;gap:10px;align-items:center;">
      <span class="pill pill-teal">◎ Trend-Analyse</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:rgba(255,255,255,0.3);">Generiert: {generated_at}</span>
    </div>
  </header>

  <div class="page">
    <!-- Executive Summary -->
    <div class="exec-summary">{executive_summary}</div>

    <!-- Score Comparison -->
    <div class="section-label"><span>Reputation Health Index · Vergleich</span></div>
    <div class="score-compare">
      <div class="score-cell">
        <div class="score-period">{period_previous}</div>
        <div class="score-num prev-score">{score_prev}</div>
        <div class="score-interp">Vormonat Baseline</div>
      </div>
      <div class="delta-center">
        <div class="delta-big {delta_cls}">{score_delta_sign}{score_delta}</div>
        <div class="delta-label {delta_cls}">Punkte</div>
      </div>
      <div class="score-cell current">
        <div class="score-period">{period_current}</div>
        <div class="score-num current-score">{score_curr}</div>
        <div class="score-interp">{score_interpretation}</div>
      </div>
    </div>

    <!-- KPI Deltas -->
    <div class="section-block">
      <div class="section-label"><span>KPI Entwicklung</span></div>
      <div class="kpi-delta-grid">
        {kpi_deltas_html}
      </div>
    </div>

    <!-- New / Resolved Issues -->
    <div class="section-block">
      <div class="section-label"><span>Strategische Themen · Veränderungen</span></div>
      <div class="issue-row">
        <div class="issue-col">
          <div class="issue-col-label new-col">▲ Neu im {period_current}</div>
          {new_issues_html}
        </div>
        <div class="issue-col">
          <div class="issue-col-label resolved-col">✓ Abgeschlossen / nicht mehr relevant</div>
          {resolved_issues_html}
        </div>
      </div>
    </div>

    <!-- SoV Movement -->
    <div class="section-block">
      <div class="section-label"><span>Share of Voice · Bewegung</span></div>
      {sov_movement_html}
    </div>

    <!-- Topic Ownership Changes -->
    <div class="section-block">
      <div class="section-label"><span>Topic Ownership · Veränderungen</span></div>
      {ownership_changes_html}
    </div>

    <!-- Risk Changes -->
    <div class="section-block">
      <div class="section-label"><span>Risiko-Register · Veränderungen</span></div>
      {risk_changes_html}
    </div>

    <!-- Momentum Shifts -->
    <div class="section-block">
      <div class="section-label"><span>Topic Momentum · Trendverschiebungen</span></div>
      {momentum_shifts_html}
    </div>

    <!-- Action Completion -->
    <div class="section-block">
      <div class="section-label"><span>Action Center · Fortschritt</span></div>
      <div class="action-summary-grid">
        <div class="as-cell"><div class="as-label">Abgeschlossen</div><div class="as-val" style="color:var(--green);">{ac_completed}</div></div>
        <div class="as-cell"><div class="as-label">In Progress</div><div class="as-val" style="color:var(--blue);">{ac_in_progress}</div></div>
        <div class="as-cell"><div class="as-label">Neu</div><div class="as-val" style="color:var(--orange);">{ac_new}</div></div>
        <div class="as-cell"><div class="as-label">Completion Rate</div><div class="as-val">{ac_rate}</div></div>
      </div>
    </div>

    <!-- Key Wins + Risks Forward -->
    <div class="section-block">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">
        <div>
          <div class="section-label"><span>Key Wins · {period_current}</span></div>
          <div class="key-list">{key_wins_html}</div>
        </div>
        <div>
          <div class="section-label"><span>Risiken Vorschau · {period_next}</span></div>
          <div class="key-list">{key_risks_html}</div>
        </div>
      </div>
    </div>

    <!-- Recommendations -->
    <div class="section-block">
      <div class="section-label"><span>Empfehlungen · basierend auf MoM-Analyse</span></div>
      {recommendations_html}
    </div>
  </div>
</body>
</html>"""


def _own_change(change: str) -> str:
    cls = "delta-pos" if "VERBESSERT" in change else ("delta-neg" if "VERSCHLECHTERT" in change else "delta-flat")
    return f'<span class="{cls}">{change}</span>'


def _sev_pill(severity: str, sev_cls: str) -> str:
    return f'<span class="sev-pill {sev_cls}">{severity}</span>'


def generate_comparison_html(report: dict) -> str:
    meta = report.get("meta", {})
    ns = report.get("northstar_comparison", {})
    kpi_deltas = report.get("kpi_deltas", [])
    new_issues = report.get("new_strategic_issues", [])
    resolved = report.get("resolved_issues", [])
    sov = report.get("sov_movement", [])
    ownership = report.get("topic_ownership_changes", [])
    risks = report.get("risk_changes", {})
    momentum = report.get("momentum_shifts", [])
    ac = report.get("action_completion", {})
    wins = report.get("key_wins", [])
    fwd_risks = report.get("key_risks_forward", [])
    recos = report.get("recommendations", [])

    delta = ns.get("delta", 0)
    delta_cls = ns.get("delta_cls", "delta-flat")
    delta_sign = "+" if delta > 0 else ""

    # KPI deltas
    kpi_html = ""
    for k in kpi_deltas:
        tag_cls = "delta-tag-pos" if "pos" in k.get("delta_cls", "") else ("delta-tag-neg" if "neg" in k.get("delta_cls", "") else "delta-tag-flat")
        kpi_html += f"""<div class="kpi-delta-cell">
      <div class="kd-label">{k.get('label','')}</div>
      <div class="kd-values">
        <span class="kd-curr">{k.get('current_val','')}</span>
        <span class="kd-prev">vs. {k.get('previous_val','')}</span>
        <span class="kd-delta {tag_cls}">{k.get('delta','')}</span>
      </div>
      <div class="kd-interp">{k.get('interpretation','')}</div>
    </div>"""

    # New issues
    new_html = ""
    for i in new_issues:
        new_html += f"""<div class="mini-card">
      <div class="verdict-tag {i.get('verdictCls','')}">{i.get('verdict','')}</div>
      <div class="mini-title">{i.get('title','')}</div>
      <div class="mini-summary">{i.get('summary','')}</div>
    </div>"""
    if not new_html:
        new_html = '<div style="font-size:12px;color:rgba(255,255,255,0.3);padding:12px;">Keine neuen Themen</div>'

    # Resolved
    resolved_html = ""
    for r in resolved:
        resolved_html += f"""<div class="mini-card" style="opacity:0.6;">
      <div class="mini-title">{r.get('title','')}</div>
      <div class="mini-summary">{r.get('summary','')}</div>
    </div>"""
    if not resolved_html:
        resolved_html = '<div style="font-size:12px;color:rgba(255,255,255,0.3);padding:12px;">Keine abgeschlossenen Themen</div>'

    # SoV movement
    sov_html = ""
    max_pct = max((max(s.get("prev_pct", 0), s.get("curr_pct", 0)) for s in sov), default=1)
    for s in sov:
        us = s.get("us", False)
        color = "var(--pink)" if us else "rgba(255,255,255,0.3)"
        prev_w = int(s.get("prev_pct", 0) / max_pct * 100)
        curr_w = int(s.get("curr_pct", 0) / max_pct * 100)
        tag_cls = "delta-tag-pos" if "good" in s.get("delta_cls", "") or "up" in s.get("delta_cls", "") else "delta-tag-neg" if "down" in s.get("delta_cls", "") and "good" not in s.get("delta_cls", "") else "delta-tag-flat"
        sov_html += f"""<div class="sov-move-row">
      <div class="sov-co-name {'us' if us else ''}">{s.get('name','')}</div>
      <div class="sov-pct">{s.get('prev_pct',0)}%</div>
      <div class="sov-bar-track"><div class="sov-bar-fill" style="width:{prev_w}%;background:rgba(255,255,255,0.2)"></div></div>
      <div class="sov-pct">{s.get('curr_pct',0)}%</div>
      <div class="sov-bar-track"><div class="sov-bar-fill" style="width:{curr_w}%;background:{color}"></div></div>
      <div class="sov-delta-tag {tag_cls}">{s.get('delta','')}</div>
    </div>"""

    # Ownership changes
    own_html = ""
    if ownership:
        own_rows = ""
        for o in ownership:
            cls = "delta-pos" if "VERBESSERT" in o.get("change", "") else ("delta-neg" if "VERSCHLECHTERT" in o.get("change", "") else "delta-flat")
            own_rows += f"""<div style="display:grid;grid-template-columns:180px 80px 40px 80px 1fr;gap:12px;align-items:center;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
          <div style="font-size:13px;">{o.get('topic','')}</div>
          <div style="font-family:var(--font-mono);font-size:11px;color:rgba(255,255,255,0.4);text-align:center;">{o.get('previous','')}</div>
          <div style="font-family:var(--font-mono);font-size:11px;color:rgba(255,255,255,0.3);text-align:center;">→</div>
          <div style="font-family:var(--font-mono);font-size:11px;color:rgba(255,255,255,0.7);text-align:center;">{o.get('current','')}</div>
          <div class="{cls}" style="font-size:11px;font-family:var(--font-mono);">{o.get('change','')}</div>
        </div>"""
        own_html = f"""<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);padding:16px 20px;">
      <div style="display:grid;grid-template-columns:180px 80px 40px 80px 1fr;gap:12px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.07);font-size:9px;letter-spacing:2px;font-family:var(--font-mono);color:rgba(255,255,255,0.3);text-transform:uppercase;">
        <div>Topic</div><div style="text-align:center;">Vormonat</div><div></div><div style="text-align:center;">Aktuell</div><div>Änderung</div>
      </div>
      {own_rows}
    </div>"""
    else:
        own_html = '<div style="font-size:12px;color:rgba(255,255,255,0.3);padding:12px;">Keine Änderungen in Topic Ownership</div>'

    # Risk changes
    risk_html = ""
    escalated = risks.get("escalated", [])
    resolved_risks = risks.get("resolved", [])
    new_risks = risks.get("new", [])
    if escalated:
        rows = "".join(f"""<div class="risk-change-row" style="border-left:2px solid var(--red);">
      <div class="risk-change-id">{r.get('id','')}</div>
      <div><div class="risk-change-title">{r.get('title','')} {_sev_pill(r.get('prev_severity',''), 'sev-medium')} → {_sev_pill(r.get('curr_severity',''), 'sev-high')}</div>
      <div class="risk-change-comment">{r.get('comment','')}</div></div>
    </div>""" for r in escalated)
        risk_html += f'<div class="risk-section"><div class="risk-section-label" style="color:var(--red);">▲ Eskaliert</div>{rows}</div>'
    if new_risks:
        rows = "".join(f"""<div class="risk-change-row" style="border-left:2px solid var(--orange);">
      <div class="risk-change-id">{r.get('id','')}</div>
      <div><div class="risk-change-title">{r.get('title','')} {_sev_pill(r.get('severity',''), r.get('sevCls','sev-medium'))}</div>
      <div class="risk-change-comment">{r.get('comment','')}</div></div>
    </div>""" for r in new_risks)
        risk_html += f'<div class="risk-section"><div class="risk-section-label" style="color:var(--orange);">+ Neu identifiziert</div>{rows}</div>'
    if resolved_risks:
        rows = "".join(f"""<div class="risk-change-row" style="border-left:2px solid var(--green);opacity:0.6;">
      <div class="risk-change-id">{r.get('id','')}</div>
      <div><div class="risk-change-title">{r.get('title','')}</div>
      <div class="risk-change-comment">{r.get('comment','')}</div></div>
    </div>""" for r in resolved_risks)
        risk_html += f'<div class="risk-section"><div class="risk-section-label" style="color:var(--green);">✓ Aufgelöst</div>{rows}</div>'
    if not risk_html:
        risk_html = '<div style="font-size:12px;color:rgba(255,255,255,0.3);padding:12px;">Keine signifikanten Risikoänderungen</div>'

    # Momentum shifts
    mom_html = ""
    if momentum:
        mom_rows = "".join(f"""<div class="momentum-shift-row">
      <div class="momentum-topic">{m.get('topic','')}</div>
      <div class="m-arrow" style="color:rgba(255,255,255,0.4);">{m.get('prev_arrow','')}</div>
      <div class="m-arrow-icon">→</div>
      <div class="m-arrow">{m.get('curr_arrow','')}</div>
      <div class="m-comment">{m.get('change','')} · {m.get('comment','')}</div>
    </div>""" for m in momentum)
        mom_html = f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);padding:8px 16px;">{mom_rows}</div>'
    else:
        mom_html = '<div style="font-size:12px;color:rgba(255,255,255,0.3);padding:12px;">Keine signifikanten Momentum-Verschiebungen</div>'

    # Key wins / risks
    wins_html = "".join(f'<div class="key-item win"><div class="key-item-text">{w}</div></div>' for w in wins)
    risks_fwd_html = "".join(f'<div class="key-item risk-item"><div class="key-item-text">{r}</div></div>' for r in fwd_risks)

    # Recommendations
    prio_cls = {"P0": "p0-badge", "P1": "p1-badge", "P2": "p2-badge"}
    reco_html = "".join(f"""<div class="reco-card">
      <div class="reco-prio {prio_cls.get(r.get('priority','P2'), 'p2-badge')}">{r.get('priority','')}</div>
      <div>
        <div class="reco-title">{r.get('title','')}</div>
        <div class="reco-rationale">{r.get('rationale','')}</div>
      </div>
    </div>""" for r in recos)

    # Next month label
    import re as _re
    curr_period = meta.get("period_current", "")
    month_map = {"Januar": "Februar", "Februar": "März", "März": "April", "April": "Mai",
                 "Mai": "Juni", "Juni": "Juli", "Juli": "August", "August": "September",
                 "September": "Oktober", "Oktober": "November", "November": "Dezember", "Dezember": "Januar"}
    next_period = curr_period
    for m, nxt in month_map.items():
        if m in curr_period:
            next_period = curr_period.replace(m, nxt)
            break

    return COMPARISON_HTML.format(
        period_current=meta.get("period_current", ""),
        period_previous=meta.get("period_previous", ""),
        period_next=next_period,
        company=meta.get("company", "OMG Germany"),
        generated_at=__import__('datetime').datetime.now().strftime("%d.%m.%Y %H:%M"),
        executive_summary=report.get("executive_summary", ""),
        score_prev=ns.get("previous", "—"),
        score_curr=ns.get("current", "—"),
        score_delta=abs(delta),
        score_delta_sign=delta_sign,
        delta_cls=delta_cls,
        score_interpretation=ns.get("interpretation", ""),
        kpi_deltas_html=kpi_html,
        new_issues_html=new_html,
        resolved_issues_html=resolved_html,
        sov_movement_html=sov_html,
        ownership_changes_html=own_html,
        risk_changes_html=risk_html,
        momentum_shifts_html=mom_html,
        ac_completed=ac.get("completed", 0),
        ac_in_progress=ac.get("in_progress", 0),
        ac_new=ac.get("new", 0),
        ac_rate=ac.get("completion_rate", "—"),
        key_wins_html=wins_html,
        key_risks_html=risks_fwd_html,
        recommendations_html=reco_html,
    )
