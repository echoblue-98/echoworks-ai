"""Quick audit: who's already been contacted."""
from aionos.sales.prospects import Pipeline

p = Pipeline()
conn = p._conn

rows = conn.execute(
    "SELECT DISTINCT a.prospect_id, p.name, p.company, a.action, a.channel "
    "FROM activity_log a JOIN prospects p ON a.prospect_id = p.id "
    "ORDER BY a.prospect_id"
).fetchall()

contacted_ids = set()
print("All logged outreach activity:")
for r in rows:
    contacted_ids.add(r[0])
    print(f"  #{r[0]} {r[1]} - {r[2]} | {r[3]} | {r[4]}")

print(f"\nTotal prospects with activity: {len(contacted_ids)}")

engaged = conn.execute(
    "SELECT id, name, company, stage FROM prospects WHERE stage != 'cold' ORDER BY id"
).fetchall()

print("\nNon-cold prospects (already advanced):")
for r in engaged:
    print(f"  #{r[0]} {r[1]} - {r[2]} ({r[3]})")

# Cross-reference with the sheet
cold_with_activity = conn.execute(
    "SELECT DISTINCT p.id, p.name, p.company FROM prospects p "
    "JOIN activity_log a ON p.id = a.id WHERE p.stage = 'cold' "
    "ORDER BY p.id"
).fetchall()

# Better: just find cold prospects who have any activity logged
cold_contacted = conn.execute(
    "SELECT DISTINCT p.id, p.name, p.company "
    "FROM prospects p "
    "JOIN activity_log a ON p.id = a.prospect_id "
    "WHERE p.stage = 'cold' "
    "ORDER BY p.id"
).fetchall()

print(f"\nCold prospects WITH prior outreach (should be excluded from sheet):")
for r in cold_contacted:
    print(f"  #{r[0]} {r[1]} - {r[2]}")
print(f"Total: {len(cold_contacted)}")
