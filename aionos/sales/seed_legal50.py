"""
Seed 50 Law Firm Prospects — Targeted Outreach List
=====================================================
ICP: Mid-to-large law firms where attorney departure theft
is a real, expensive, recurring problem.

Selection criteria:
  1. AmLaw 200 firms with Atlanta presence (local first)
  2. Firms with known lateral partner activity (2024-2026)
  3. Mid-size firms (50-500 attorneys) — big enough to pay,
     small enough to lack enterprise SIEM
  4. Litigation/IP/corporate boutiques (high-value data)
  5. Firms with recent mergers, dissolutions, or poaching incidents

Buyer personas targeted:
  - Managing Partner (decision maker)
  - IT Director / CIO (technical buyer)
  - General Counsel / Ethics Partner (influencer)

Run:
    python -m aionos.sales.seed_legal50
"""

from __future__ import annotations

from aionos.sales.prospects import Pipeline


# ── 50 Law Firm Targets ──────────────────────────────────────
# Organized by tier:
#   Tier A (1-15):  Atlanta-based, highest conversion probability
#   Tier B (16-30): Southeast regional, warm market
#   Tier C (31-40): AmLaw 200 national, high lateral activity
#   Tier D (41-50): Litigation/IP boutiques, data-heavy practices

LEGAL_PROSPECTS = [
    # ── TIER A: Atlanta-Based Firms ──────────────────────────
    # These are local — you can do in-person demos
    {"name": "Managing Partner", "company": "Bondurant Mixson & Elmore", "title": "Managing Partner",
     "notes": "Tier A. Atlanta litigation boutique. High-value case files. 40+ attorneys."},
    {"name": "IT Director", "company": "Freeman Mathis & Gary", "title": "IT Director",
     "notes": "Tier A. Atlanta. 200+ attorneys, rapid growth. Insurance defense. High lateral activity."},
    {"name": "Managing Partner", "company": "Morris Manning & Martin", "title": "Managing Partner",
     "notes": "Tier A. Atlanta. Tech + corporate. IP-heavy practice. 100+ attorneys."},
    {"name": "CIO", "company": "Arnall Golden Gregory", "title": "CIO",
     "notes": "Tier A. Atlanta. Healthcare + real estate practice groups. 150+ attorneys."},
    {"name": "Managing Partner", "company": "Chamberlain Hrdlicka", "title": "Managing Partner",
     "notes": "Tier A. Atlanta + Houston. Tax litigation. Sensitive financial data."},
    {"name": "IT Director", "company": "FordHarrison", "title": "IT Director",
     "notes": "Tier A. Atlanta HQ. Labor & employment. 200+ attorneys across 30 offices."},
    {"name": "Managing Partner", "company": "Womble Bond Dickinson", "title": "Managing Partner",
     "notes": "Tier A. Atlanta office. Transatlantic firm. 1000+ attorneys. Enterprise buyer."},
    {"name": "CIO", "company": "Burr & Forman", "title": "CIO",
     "notes": "Tier A. Atlanta + Southeast. 350+ attorneys. Commercial litigation."},
    {"name": "Managing Partner", "company": "Hall Booth Smith", "title": "Managing Partner",
     "notes": "Tier A. Atlanta HQ. Litigation-heavy. 200+ attorneys. Insurance defense."},
    {"name": "IT Director", "company": "Weinberg Wheeler Hudgins", "title": "IT Director",
     "notes": "Tier A. Atlanta. Trial firm. Highly confidential case data."},
    {"name": "Managing Partner", "company": "Constangy Brooks Smith & Prophete", "title": "Managing Partner",
     "notes": "Tier A. Atlanta HQ. Employment law. 180+ attorneys. Multi-office."},
    {"name": "CIO", "company": "Swift Currie McGhee & Hiers", "title": "CIO",
     "notes": "Tier A. Atlanta. Insurance defense + litigation. 150+ attorneys."},
    {"name": "IT Director", "company": "Greenberg Traurig (Atlanta)", "title": "IT Director",
     "notes": "Tier A. Atlanta office of AmLaw 50. 2500+ attorneys globally. Local IT decision."},
    {"name": "Managing Partner", "company": "Bryan Cave Leighton Paisner (Atlanta)", "title": "Managing Partner",
     "notes": "Tier A. Atlanta office. Global firm. Known lateral activity."},
    {"name": "CIO", "company": "Seyfarth Shaw (Atlanta)", "title": "CIO",
     "notes": "Tier A. Atlanta office. Labor & employment leader. Tech-forward firm."},

    # ── TIER B: Southeast Regional ───────────────────────────
    # Drive/flight distance. Second wave after Atlanta saturated.
    {"name": "Managing Partner", "company": "Bradley Arant Boult Cummings", "title": "Managing Partner",
     "notes": "Tier B. Birmingham/Nashville. 500+ attorneys. Frequent lateral moves."},
    {"name": "IT Director", "company": "Balch & Bingham", "title": "IT Director",
     "notes": "Tier B. Birmingham. Energy + litigation. 250+ attorneys."},
    {"name": "Managing Partner", "company": "Bass Berry & Sims", "title": "Managing Partner",
     "notes": "Tier B. Nashville. Healthcare + corporate. 300+ attorneys."},
    {"name": "CIO", "company": "Butler Snow", "title": "CIO",
     "notes": "Tier B. Mississippi/Tennessee. 350+ attorneys. Rapid growth."},
    {"name": "IT Director", "company": "Smith Anderson", "title": "IT Director",
     "notes": "Tier B. Raleigh. Full-service. 130+ attorneys. Growing tech practice."},
    {"name": "Managing Partner", "company": "Maynard Nexsen", "title": "Managing Partner",
     "notes": "Tier B. Charlotte/Columbia. Recently merged (2023). Post-merger = departure risk."},
    {"name": "CIO", "company": "Parker Poe Adams & Bernstein", "title": "CIO",
     "notes": "Tier B. Charlotte. 200+ attorneys. Strong real estate + litigation."},
    {"name": "IT Director", "company": "Adams and Reese", "title": "IT Director",
     "notes": "Tier B. New Orleans + Southeast. 300+ attorneys. Energy + maritime."},
    {"name": "Managing Partner", "company": "Phelps Dunbar", "title": "Managing Partner",
     "notes": "Tier B. New Orleans/Gulf Coast. 300+ attorneys. Admiralty + energy."},
    {"name": "CIO", "company": "Lightfoot Franklin & White", "title": "CIO",
     "notes": "Tier B. Birmingham. Trial firm. Extremely sensitive case data."},
    {"name": "IT Director", "company": "Nexsen Pruet", "title": "IT Director",
     "notes": "Tier B. Carolinas + Southeast. 200+ attorneys. Post-merger integration."},
    {"name": "Managing Partner", "company": "Waller Lansden Dortch & Davis", "title": "Managing Partner",
     "notes": "Tier B. Nashville. Healthcare + finance. 200+ attorneys."},
    {"name": "CIO", "company": "Stites & Harbison", "title": "CIO",
     "notes": "Tier B. Kentucky + Southeast. 250+ attorneys. Multi-office."},
    {"name": "IT Director", "company": "McGuireWoods (Charlotte)", "title": "IT Director",
     "notes": "Tier B. Charlotte office. AmLaw 100. 1100+ attorneys. Local IT buyer."},
    {"name": "Managing Partner", "company": "Williams Mullen", "title": "Managing Partner",
     "notes": "Tier B. Virginia + Carolinas. 250+ attorneys. Corporate + litigation."},

    # ── TIER C: AmLaw 200 National — High Lateral Activity ───
    # Known for partner movement. Attorney departure = active problem.
    {"name": "IT Director", "company": "Blank Rome", "title": "IT Director",
     "notes": "Tier C. National. 600+ attorneys. Known for lateral hiring. High churn."},
    {"name": "CIO", "company": "Duane Morris", "title": "CIO",
     "notes": "Tier C. National. 800+ attorneys. Multi-practice. Active lateral market."},
    {"name": "IT Director", "company": "Cozen O'Connor", "title": "IT Director",
     "notes": "Tier C. National. 700+ attorneys. Insurance + commercial lit. High volume."},
    {"name": "Managing Partner", "company": "Fox Rothschild", "title": "Managing Partner",
     "notes": "Tier C. National. 950+ attorneys. Aggressive lateral hiring = departure risk."},
    {"name": "CIO", "company": "Lewis Brisbois", "title": "CIO",
     "notes": "Tier C. National. 1500+ attorneys. Massive scale. Insurance defense."},
    {"name": "IT Director", "company": "Jackson Lewis", "title": "IT Director",
     "notes": "Tier C. National. 950+ attorneys. Workplace law. Data-heavy HR matters."},
    {"name": "Managing Partner", "company": "Littler Mendelson", "title": "Managing Partner",
     "notes": "Tier C. National. 1800+ attorneys. Employment law giant. Compliance-sensitive."},
    {"name": "CIO", "company": "Ogletree Deakins", "title": "CIO",
     "notes": "Tier C. National. 950+ attorneys. Workplace law. Atlanta-adjacent."},
    {"name": "IT Director", "company": "Fisher Phillips", "title": "IT Director",
     "notes": "Tier C. Atlanta-founded. National. 500+ attorneys. Labor & employment."},
    {"name": "Managing Partner", "company": "Hunton Andrews Kurth", "title": "Managing Partner",
     "notes": "Tier C. Post-merger (2018). High lateral activity. 750+ attorneys."},

    # ── TIER D: Litigation/IP Boutiques — Data-Heavy ─────────
    # Smaller firms with extremely valuable case data.
    # Higher conversion if managing partner is reachable.
    {"name": "Managing Partner", "company": "Quinn Emanuel (Atlanta)", "title": "Managing Partner",
     "notes": "Tier D. Elite litigation boutique. Highest-value case data in the market."},
    {"name": "IT Director", "company": "Wachtell Lipton Rosen & Katz", "title": "IT Director",
     "notes": "Tier D. NYC. Elite M&A. Extreme data sensitivity. Premium buyer."},
    {"name": "Managing Partner", "company": "Susman Godfrey", "title": "Managing Partner",
     "notes": "Tier D. Litigation boutique. Houston/LA/NY/Seattle. 150+ attorneys."},
    {"name": "CIO", "company": "Krevolin & Horst", "title": "CIO",
     "notes": "Tier D. Atlanta boutique. Business litigation. Small but data-sensitive."},
    {"name": "Managing Partner", "company": "Finch McCranie", "title": "Managing Partner",
     "notes": "Tier D. Atlanta. Criminal defense + white collar. Ultra-sensitive data."},
    {"name": "IT Director", "company": "Rogers & Hardin", "title": "IT Director",
     "notes": "Tier D. Atlanta. Litigation boutique. 50+ attorneys. High-value matters."},
    {"name": "Managing Partner", "company": "Hawkins Parnell & Young", "title": "Managing Partner",
     "notes": "Tier D. Atlanta. Product liability + mass tort. Document-heavy."},
    {"name": "CIO", "company": "Boies Schiller Flexner", "title": "CIO",
     "notes": "Tier D. National litigation boutique. Known departures. 250+ attorneys."},
    {"name": "IT Director", "company": "Kasowitz Benson Torres", "title": "IT Director",
     "notes": "Tier D. NYC litigation boutique. Complex commercial + real estate."},
    {"name": "Managing Partner", "company": "Cadwalader Wickersham & Taft", "title": "Managing Partner",
     "notes": "Tier D. NYSE. Finance + restructuring. 400+ attorneys. Data-heavy."},
]


def seed_legal_50() -> int:
    """Load 50 law firm prospects into the pipeline. Returns count added."""
    pipe = Pipeline()
    existing = {
        (p["company"].lower().strip())
        for p in pipe.list_all(vertical="legal")
    }

    added = 0
    for prospect in LEGAL_PROSPECTS:
        company = prospect["company"].strip()
        if company.lower() in existing:
            continue

        pipe.add(
            name=prospect["name"],
            company=company,
            title=prospect.get("title", ""),
            vertical="legal",
            notes=prospect.get("notes", ""),
            source="icp_seed",
        )
        added += 1

    pipe.close()
    return added


if __name__ == "__main__":
    count = seed_legal_50()
    print(f"  Seeded {count} new law firm prospects (skipped existing).")

    pipe = Pipeline()
    total = len(pipe.list_all(vertical="legal"))
    pipe.close()
    print(f"  Total legal prospects in pipeline: {total}")
