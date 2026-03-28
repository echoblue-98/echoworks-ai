"""Generate LinkedIn outreach sheet — run once to create the file."""
from collections import defaultdict
from aionos.sales.prospects import Pipeline
from aionos.sales.messages import MessageGenerator

pipe = Pipeline()
gen = MessageGenerator()

cold = [dict(p) for p in pipe.list_all(stage="cold")]

# Filter out placeholder names (seed data with role-only names)
PLACEHOLDER_NAMES = {
    "managing partner", "it director", "cio", "ciso",
    "general counsel", "chief compliance officer",
}

# Filter out prospects already contacted (have activity log entries)
conn = pipe._conn
contacted_ids = set(
    r[0] for r in conn.execute(
        "SELECT DISTINCT prospect_id FROM activity_log"
    ).fetchall()
)

by_vert = defaultdict(list)
for p in cold:
    name_lower = p["name"].strip().lower()
    if name_lower in PLACEHOLDER_NAMES:
        continue  # Skip placeholders — can't send to "Managing Partner"
    if p["id"] in contacted_ids:
        continue  # Already contacted — don't double-send
    by_vert[p["vertical"]].append(p)

vert_labels = {
    "legal": "LAW FIRMS & LEGAL SERVICES",
    "healthcare": "HEALTHCARE & COMPLIANCE",
    "realestate": "TITLE, BROKERAGE & REAL ESTATE",
}

lines = []
lines.append("=" * 70)
lines.append("  AION OS  —  LINKEDIN OUTREACH SHEET")
lines.append("  Generated: 2026-03-26")
lines.append("  Find each person on LinkedIn. Paste message. Send.")
lines.append("  Mark [X] when sent.")
lines.append("=" * 70)
lines.append("")

total = 0
for vert in ("legal", "healthcare", "realestate"):
    prospects = by_vert.get(vert, [])
    if not prospects:
        continue

    lines.append("")
    lines.append("━" * 70)
    label = vert_labels.get(vert, vert)
    lines.append("  {}  ({} prospects)".format(label, len(prospects)))
    lines.append("━" * 70)
    lines.append("")

    for p in prospects:
        pid = p["id"]
        name = p["name"]
        company = p["company"]
        title = p.get("title", "") or ""
        linkedin = p.get("linkedin", "") or ""

        try:
            msgs = gen.generate(
                name=name, company=company,
                title=title or "Partner", vertical=vert,
            )
            msg = msgs.get("linkedin_request", "")
        except Exception:
            msg = ""

        lines.append("[ ] #{}  {}".format(pid, name))
        lines.append("    {}  |  {}".format(company, title or "No title"))
        if linkedin:
            lines.append("    LinkedIn: linkedin.com/in/{}".format(linkedin))
        lines.append("    ---")
        if msg:
            # Wrap message for readability
            for mline in msg.split("\n"):
                lines.append("    " + mline)
        lines.append("    ---")
        lines.append("")
        total += 1

lines.append("")
lines.append("Total: {} prospects".format(total))
lines.append("")

with open("LINKEDIN_OUTREACH_SHEET.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Generated: LINKEDIN_OUTREACH_SHEET.txt ({} prospects)".format(total))
