"""
EchoWorks — Sales Dashboard Report
=====================================
Generates a visual HTML dashboard with pipeline charts,
cadence performance, and activity history. Opens in browser.

Usage:
    python sell.py report            Generate + open in browser
    python sell.py report --file     Save to ~/Downloads/
"""

from __future__ import annotations

import json
import os
import tempfile
import webbrowser
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List

from aionos.sales.prospects import Pipeline
from aionos.sales.cadence import CadenceEngine, SEQUENCES
from aionos.sales.learner import SalesLearner

OFFER_PRICE = 5000


class DashboardReport:
    """Generate visual HTML sales dashboard."""

    def __init__(self) -> None:
        self._pipe = Pipeline()
        self._cadence = CadenceEngine()
        self._learner = SalesLearner()

    def _gather_data(self) -> dict:
        """Collect all data needed for the dashboard."""
        counts = self._pipe.count_by_stage()
        total = sum(counts.values())
        won = counts.get("closed_won", 0)
        lost = counts.get("closed_lost", 0)
        active = total - won - lost

        # Stage pipeline data
        stage_order = [
            "cold", "engaged", "demo_scheduled", "demo_completed",
            "proposal_sent", "negotiation", "closed_won", "closed_lost",
        ]
        stage_labels = {
            "cold": "Cold", "engaged": "Engaged",
            "demo_scheduled": "Demo Scheduled",
            "demo_completed": "Demo Completed",
            "proposal_sent": "Proposal Sent",
            "negotiation": "Negotiation",
            "closed_won": "Closed Won", "closed_lost": "Closed Lost",
        }
        pipeline_data = []
        for s in stage_order:
            c = counts.get(s, 0)
            if c > 0:
                pipeline_data.append({"stage": stage_labels.get(s, s), "count": c})

        # Cadence stats
        cadence_stats = self._cadence.cadence_stats()
        cadence_data = []
        for seq_name, data in cadence_stats.items():
            seq = SEQUENCES.get(seq_name, {})
            cadence_data.append({
                "name": seq.get("name", seq_name),
                "active": data.get("active", 0),
                "completed": data.get("completed", 0),
                "replied": data.get("replied", 0),
                "reply_rate": data.get("reply_rate", "0%"),
            })

        # Recent activity (last 7 days)
        recent = self._pipe.recent_actions(limit=100)
        activity_by_day = defaultdict(int)
        for a in recent:
            ts = a.get("timestamp", "")
            if ts:
                try:
                    d = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
                    activity_by_day[d.isoformat()] += 1
                except (ValueError, TypeError):
                    pass

        # Build 7-day activity chart
        today = date.today()
        activity_chart = []
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            activity_chart.append({"date": d, "actions": activity_by_day.get(d, 0)})

        # Hot prospects (proposal_sent, negotiation, demo_scheduled)
        all_p = self._pipe.list_all()
        hot = []
        for p in all_p:
            p = dict(p)
            if p["stage"] in ("proposal_sent", "negotiation", "demo_scheduled", "demo_completed"):
                enrollment = self._cadence.get_enrollment(p["id"])
                cadence_info = ""
                if enrollment:
                    cadence_info = f"Step {enrollment['current_step']}/{enrollment['total_steps']}"
                hot.append({
                    "id": p["id"],
                    "name": p["name"],
                    "company": p["company"],
                    "stage": p["stage"],
                    "cadence": cadence_info,
                })

        return {
            "date": today.isoformat(),
            "total": total,
            "active": active,
            "won": won,
            "lost": lost,
            "mrr": won * OFFER_PRICE,
            "pipeline_data": pipeline_data,
            "cadence_data": cadence_data,
            "activity_chart": activity_chart,
            "hot_prospects": hot,
        }

    def generate_html(self) -> str:
        """Generate the full dashboard HTML."""
        data = self._gather_data()
        pipeline_json = json.dumps(data["pipeline_data"])
        activity_json = json.dumps(data["activity_chart"])

        # Build cadence rows
        cadence_rows = ""
        for c in data["cadence_data"]:
            cadence_rows += f"""
            <tr>
                <td>{c['name']}</td>
                <td>{c['active']}</td>
                <td>{c['completed']}</td>
                <td>{c['replied']}</td>
                <td>{c['reply_rate']}</td>
            </tr>"""

        # Build hot prospects rows
        hot_rows = ""
        for h in data["hot_prospects"]:
            stage_color = {
                "negotiation": "#22c55e",
                "proposal_sent": "#3b82f6",
                "demo_completed": "#8b5cf6",
                "demo_scheduled": "#f59e0b",
            }.get(h["stage"], "#6b7280")
            hot_rows += f"""
            <tr>
                <td>#{h['id']}</td>
                <td><strong>{h['name']}</strong></td>
                <td>{h['company']}</td>
                <td><span style="color:{stage_color};font-weight:600">{h['stage']}</span></td>
                <td>{h['cadence']}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EchoWorks Sales Dashboard — {data['date']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e1a;
            color: #e2e8f0;
            padding: 32px;
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .header .subtitle {{
            color: #64748b;
            font-size: 0.95rem;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.04));
            border: 1px solid rgba(59,130,246,0.2);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -1px;
        }}
        .metric-label {{
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 4px;
        }}
        .metric-card.won .metric-value {{ color: #22c55e; }}
        .metric-card.mrr .metric-value {{ color: #3b82f6; }}
        .metric-card.active .metric-value {{ color: #8b5cf6; }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 40px;
        }}
        @media (max-width: 900px) {{
            .grid {{ grid-template-columns: 1fr; }}
        }}
        .card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 28px;
        }}
        .card h2 {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #94a3b8;
        }}
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .bar-row {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .bar-label {{
            width: 130px;
            font-size: 0.85rem;
            text-align: right;
            color: #94a3b8;
        }}
        .bar-track {{
            flex: 1;
            height: 28px;
            background: rgba(255,255,255,0.04);
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        }}
        .bar-fill {{
            height: 100%;
            border-radius: 8px;
            transition: width 0.8s ease;
            display: flex;
            align-items: center;
            padding-left: 10px;
            font-size: 0.8rem;
            font-weight: 600;
            color: white;
            min-width: 30px;
        }}
        .activity-chart {{
            display: flex;
            align-items: flex-end;
            gap: 8px;
            height: 140px;
            padding-top: 20px;
        }}
        .activity-bar {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }}
        .activity-bar-fill {{
            width: 100%;
            background: linear-gradient(180deg, #3b82f6, #8b5cf6);
            border-radius: 6px 6px 0 0;
            transition: height 0.6s ease;
            min-height: 4px;
        }}
        .activity-bar-label {{
            font-size: 0.7rem;
            color: #64748b;
        }}
        .activity-bar-count {{
            font-size: 0.75rem;
            font-weight: 600;
            color: #94a3b8;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }}
        th {{
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            color: #64748b;
            font-weight: 500;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}
        .footer {{
            text-align: center;
            color: #475569;
            font-size: 0.8rem;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.04);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EchoWorks Sales Dashboard</h1>
        <div class="subtitle">AION OS — $5,000/mo Retainer | Law Firms | {data['date']}</div>
    </div>

    <div class="metrics">
        <div class="metric-card active">
            <div class="metric-value">{data['active']}</div>
            <div class="metric-label">Active Prospects</div>
        </div>
        <div class="metric-card won">
            <div class="metric-value">{data['won']}</div>
            <div class="metric-label">Closed Won</div>
        </div>
        <div class="metric-card mrr">
            <div class="metric-value">${data['mrr']:,}</div>
            <div class="metric-label">Monthly Recurring Revenue</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color:#f59e0b">{data['total']}</div>
            <div class="metric-label">Total Pipeline</div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Pipeline by Stage</h2>
            <div class="bar-chart" id="pipeline-chart"></div>
        </div>
        <div class="card">
            <h2>Activity (Last 7 Days)</h2>
            <div class="activity-chart" id="activity-chart"></div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Cadence Performance</h2>
            <table>
                <thead>
                    <tr><th>Sequence</th><th>Active</th><th>Done</th><th>Replied</th><th>Rate</th></tr>
                </thead>
                <tbody>
                    {cadence_rows if cadence_rows else '<tr><td colspan="5" style="color:#64748b">No cadences active yet</td></tr>'}
                </tbody>
            </table>
        </div>
        <div class="card">
            <h2>Hot Prospects</h2>
            <table>
                <thead>
                    <tr><th>ID</th><th>Name</th><th>Company</th><th>Stage</th><th>Cadence</th></tr>
                </thead>
                <tbody>
                    {hot_rows if hot_rows else '<tr><td colspan="5" style="color:#64748b">No hot prospects — start selling!</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>

    <div class="footer">
        EchoWorks AI — EchoBlue Holdings LLC | Generated {data['date']}
    </div>

    <script>
        // Pipeline bar chart
        const pipelineData = {pipeline_json};
        const maxCount = Math.max(...pipelineData.map(d => d.count), 1);
        const colors = ['#3b82f6','#8b5cf6','#f59e0b','#f97316','#22c55e','#06b6d4','#10b981','#ef4444'];
        const chartEl = document.getElementById('pipeline-chart');
        pipelineData.forEach((d, i) => {{
            const pct = (d.count / maxCount * 100).toFixed(0);
            const color = colors[i % colors.length];
            chartEl.innerHTML += `
                <div class="bar-row">
                    <div class="bar-label">${{d.stage}}</div>
                    <div class="bar-track">
                        <div class="bar-fill" style="width:${{pct}}%;background:${{color}}">${{d.count}}</div>
                    </div>
                </div>`;
        }});

        // Activity chart
        const activityData = {activity_json};
        const maxActions = Math.max(...activityData.map(d => d.actions), 1);
        const actEl = document.getElementById('activity-chart');
        activityData.forEach(d => {{
            const h = (d.actions / maxActions * 120).toFixed(0);
            const dayLabel = d.date.slice(5);
            actEl.innerHTML += `
                <div class="activity-bar">
                    <div class="activity-bar-count">${{d.actions}}</div>
                    <div class="activity-bar-fill" style="height:${{h}}px"></div>
                    <div class="activity-bar-label">${{dayLabel}}</div>
                </div>`;
        }});
    </script>
</body>
</html>"""
        return html

    def open_in_browser(self) -> str:
        """Generate dashboard and open in browser. Returns file path."""
        html = self.generate_html()
        path = os.path.join(tempfile.gettempdir(), "echoworks_dashboard.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open(f"file:///{path}")
        return path

    def save(self, file_path: str) -> None:
        """Save dashboard HTML to file."""
        html = self.generate_html()
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Dashboard saved to {file_path}")


def main() -> None:
    import sys
    args = sys.argv[1:]

    report = DashboardReport()

    if "--file" in args:
        today = date.today().isoformat()
        path = os.path.join(os.path.expanduser("~"), "Downloads",
                            f"sales_dashboard_{today}.html")
        report.save(path)
        webbrowser.open(f"file:///{path}")
    else:
        path = report.open_in_browser()
        print(f"  Dashboard opened in browser: {path}")


if __name__ == "__main__":
    main()
