"""
EchoWorks — Connection Request Batch #3
==========================================
Generated April 6, 2026

STATUS: All previous LinkedIn connections exhausted.
        This batch is for NEW connection requests.

STRATEGY:
  - These are NOT DMs. These are connection requests (300 char limit).
  - Pain-first. No product pitch. Just the hook.
  - Goal: get them to ACCEPT. Then DM after acceptance.

WORKFLOW:
  1. Search each firm name on LinkedIn
  2. Find the Managing Partner, IT Director, or CIO
  3. Update the prospect name in pipeline: python sell.py update <id> --name "Real Name"
  4. Send connection request with the message below
  5. After they accept → send the full DM (use Batch 2 style)

15 targets — do 10 today, 5 tomorrow.
After tomorrow, repeat with the next 15 firms.
=================================================================
"""

# ─── TIER 1: Atlanta-based firms (your backyard) ─────────────────

BATCH = [
    {
        "id": 37,
        "firm": "Morris Manning & Martin",
        "title_to_find": "Managing Partner",
        "why": "Atlanta boutique, 70+ attorneys. Right size for $5K/mo.",
        "request": (
            "Hi {first_name} — I work with Atlanta law firms on a problem most "
            "don't realize they have: departing attorneys staging client files weeks "
            "before they resign. Would love to connect."
        ),
    },
    {
        "id": 39,
        "firm": "Chamberlain Hrdlicka",
        "title_to_find": "Managing Partner",
        "why": "Atlanta + Houston, tax & litigation. ~200 attorneys.",
        "request": (
            "Hi {first_name} — quick question: if a partner in your Atlanta office "
            "downloaded 200 client files this week, would anyone know? That's the "
            "gap we close. Would love to connect."
        ),
    },
    {
        "id": 40,
        "firm": "FordHarrison",
        "title_to_find": "IT Director",
        "why": "Atlanta HQ, labor & employment. 200+ attorneys across 30 offices.",
        "request": (
            "Hi {first_name} — FordHarrison has attorneys in 30 offices with access "
            "to sensitive employment data. We help firms detect when that data moves "
            "in unusual patterns. Worth connecting?"
        ),
    },
    {
        "id": 43,
        "firm": "Hall Booth Smith",
        "title_to_find": "Managing Partner",
        "why": "Atlanta HQ, 350+ attorneys. Insurance defense = high-volume docs.",
        "request": (
            "Hi {first_name} — Hall Booth Smith handles a massive volume of "
            "litigation files. If an attorney left tomorrow, would you know what "
            "they took? We solve that problem. Let's connect."
        ),
    },
    {
        "id": 44,
        "firm": "Weinberg Wheeler Hudgins",
        "title_to_find": "IT Director",
        "why": "Atlanta trial firm. ~100 attorneys. Perfect size.",
        "request": (
            "Hi {first_name} — trial firms move fast, and so does data when someone "
            "leaves. We help firms like Weinberg Wheeler catch insider data movement "
            "before it becomes a problem. Let's connect."
        ),
    },
    {
        "id": 46,
        "firm": "Swift Currie McGhee & Hiers",
        "title_to_find": "CIO",
        "why": "Atlanta insurance defense. ~150 attorneys.",
        "request": (
            "Hi {first_name} — insurance defense firms handle some of the most "
            "sensitive litigation data in the city. We built an on-premise system "
            "that detects unusual file access patterns. Worth a conversation?"
        ),
    },
    {
        "id": 45,
        "firm": "Constangy Brooks Smith & Prophete",
        "title_to_find": "Managing Partner",
        "why": "Atlanta HQ, labor & employment. 150+ attorneys.",
        "request": (
            "Hi {first_name} — employment law firms deal with sensitive HR data "
            "every day, but most don't monitor how that data moves internally. "
            "We fix that. Would love to connect."
        ),
    },

    # ─── TIER 2: Southeast regional (close to Atlanta) ────────────

    {
        "id": 42,
        "firm": "Burr & Forman",
        "title_to_find": "CIO",
        "why": "Birmingham HQ, strong Atlanta presence. 350+ attorneys.",
        "request": (
            "Hi {first_name} — multi-office firms like Burr & Forman have a unique "
            "challenge: data moving between offices when someone departs. We detect "
            "that in real time. Let's connect."
        ),
    },
    {
        "id": 41,
        "firm": "Womble Bond Dickinson",
        "title_to_find": "Managing Partner",
        "why": "Charlotte + Atlanta. 1,000+ attorneys. Big enough to care.",
        "request": (
            "Hi {first_name} — at Womble's scale, a departing partner has access "
            "to thousands of matters. We help firms detect file staging before the "
            "resignation letter arrives. Worth connecting?"
        ),
    },
    {
        "id": 50,
        "firm": "Bradley Arant Boult Cummings",
        "title_to_find": "Managing Partner",
        "why": "Birmingham + Atlanta. 500+ attorneys.",
        "request": (
            "Hi {first_name} — managing lateral risk across offices like Bradley "
            "Arant's is a data problem, not just a people problem. We built a "
            "system that catches it. Would love to connect."
        ),
    },

    # ─── TIER 3: Named Atlanta firms (engaged vertical) ───────────

    {
        "id": 80,
        "firm": "Rogers & Hardin",
        "title_to_find": "IT Director",
        "why": "Atlanta litigation boutique. ~50 attorneys. Ideal size.",
        "request": (
            "Hi {first_name} — boutique litigation firms are the most exposed to "
            "insider data risk because every attorney has access to everything. "
            "We solve that. Let's connect."
        ),
    },
    {
        "id": 79,
        "firm": "Finch McCranie",
        "title_to_find": "Managing Partner",
        "why": "Atlanta white collar defense. Small firm, high-value cases.",
        "request": (
            "Hi {first_name} — white collar defense firms handle the most sensitive "
            "data in the legal industry. If a departing attorney took files, would "
            "you know? We make sure you do. Let's connect."
        ),
    },
    {
        "id": 78,
        "firm": "Krevolin & Horst",
        "title_to_find": "CIO",
        "why": "Atlanta corporate + litigation. ~30 attorneys.",
        "request": (
            "Hi {first_name} — smaller firms often think insider threats are a "
            "big firm problem. But the data shows it hits mid-size firms hardest "
            "because there are fewer controls. We fix that. Let's connect."
        ),
    },
    {
        "id": 81,
        "firm": "Hawkins Parnell & Young",
        "title_to_find": "Managing Partner",
        "why": "Atlanta product liability. ~100 attorneys.",
        "request": (
            "Hi {first_name} — product liability cases generate massive document "
            "sets. If someone leaves your firm, that data is at risk. We detect "
            "unusual access in real time. Worth connecting?"
        ),
    },
    {
        "id": 36,
        "firm": "Freeman Mathis & Gary",
        "title_to_find": "IT Director",
        "why": "Atlanta, 500+ attorneys. Already have 2 contacts there (Ben Mathis, Paul Nolette).",
        "request": (
            "Hi {first_name} — I've been talking to a few people at Freeman Mathis "
            "about insider threat detection. At 500+ attorneys, the file access "
            "surface is massive. Would love to connect."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════
#  QUICK REFERENCE: CONNECTION REQUEST → DM SEQUENCE
# ═══════════════════════════════════════════════════════════════
#
#  Day 0:  Send connection request (messages above)
#  Day 1-3: They accept (or they don't — move on after 7 days)
#  Day 1 after accept: Send DM (pain-first, 3-sentence max):
#
#     "Thanks for connecting, {first_name}. Quick question —
#      if an attorney gave notice tomorrow, would your firm
#      know what files they accessed this week?
#
#      We built a system that detects it in under 3 seconds,
#      runs 100% on your hardware. I have a 3-minute recording
#      if you want to see it in action."
#
#  Day 3 after accept: Follow up if no reply:
#
#     "{first_name} — just bumping this up. The 3-min recording
#      shows real-time detection of file staging, bulk exports,
#      and after-hours access. Happy to send it over."
#
#  Day 7 after accept: Final follow up:
#
#     "Last note on this — we're running a 90-day pilot with
#      a few Atlanta firms. No contract, money-back guarantee.
#      If it's not relevant I won't follow up again."
# ═══════════════════════════════════════════════════════════════
