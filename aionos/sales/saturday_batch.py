"""
EchoWorks — Saturday Batch #2: 10 LinkedIn DMs
================================================
Generated April 4, 2026

Batch 1 (85-96) already sent.
Batch 2: Remaining LinkedIn connections + engaged law firm partners

Framework: PAIN opens → don't pitch sovereignty or compliance yet.
Goal: Get a response. That's it.

Instructions:
  1. Open LinkedIn
  2. Go to each person's profile
  3. Copy-paste the DM
  4. Send
  5. Mark done in pipeline: python sell.py sent <id>

After sending all 10, run: python sell.py report
"""

BATCH = [
    # ─── Remaining LinkedIn connections (not yet DM'd) ─────────
    {
        "id": 97,
        "name": "Sean Fogarty",
        "firm": "Arnall Golden Gregory",
        "dm": (
            "Hey Sean — Arnall Golden Gregory has a strong healthcare and real estate "
            "practice. That means sensitive deal data moving through a lot of hands.\n\n"
            "Quick question: if an attorney in one of those groups left tomorrow, "
            "would you know what files they accessed this month?\n\n"
            "That's the exact problem we solve for firms like yours. Worth a quick chat?"
        ),
    },
    {
        "id": 98,
        "name": "Anuj Desai",
        "firm": "Trusted Counsel",
        "dm": (
            "Hey Anuj — the name Trusted Counsel says it all. Trust is the product.\n\n"
            "So here's a question: what happens to that trust when an attorney "
            "leaves and client data walks out with them? Most firms find out 2 months "
            "too late.\n\n"
            "We built a system that catches it in real time. All on-premise — no "
            "data leaves your network. Want to see it?"
        ),
    },
    {
        "id": 99,
        "name": "Ben Mathis",
        "firm": "Freeman Mathis & Gary",
        "dm": (
            "Hey Ben — Freeman Mathis has 200+ attorneys and rapid growth. "
            "That's great for the business — but growth also means more lateral "
            "movement and more data exposure.\n\n"
            "Are you monitoring what attorneys access in the weeks before "
            "a departure? That's the window where data walks out.\n\n"
            "Happy to share what we're seeing at firms your size."
        ),
    },
    {
        "id": 100,
        "name": "Paul Nolette",
        "firm": "Freeman Mathis & Gary",
        "dm": (
            "Hey Paul — as Director of IT at a 200+ attorney firm, you probably "
            "see the gap firsthand: tons of data moving through endpoints, but "
            "limited visibility into who's accessing what before they give notice.\n\n"
            "We built insider threat detection specifically for law firms. "
            "On-premise, no client data leaves your servers. Would that be worth "
            "a 10-minute look?"
        ),
    },
    {
        "id": 101,
        "name": "Lance Edwards",
        "firm": "Arnall Golden Gregory LLP",
        "dm": (
            "Hey Lance — as CAO you're looking at both the operational and risk "
            "side. Quick question: what's the current protocol when an attorney "
            "gives notice? Do you have visibility into their file access history?\n\n"
            "We're helping firms close that gap before it becomes a malpractice "
            "issue. Happy to walk you through what we've built."
        ),
    },
    # ─── Engaged law firm partners (warm — they already know you) ─────
    {
        "id": 3,
        "name": "Charlie Peeler",
        "firm": "Troutman Pepper Locke",
        "dm": (
            "Hey Charlie — wanted to circle back. I've been working with Atlanta "
            "firms on insider threat detection. Specifically, catching when attorneys "
            "stage client files before a departure.\n\n"
            "Given the size of Troutman Pepper, I'd imagine lateral movement is "
            "constant. Would it be worth a quick conversation about what we're seeing?"
        ),
    },
    {
        "id": 4,
        "name": "Michael Hollingsworth II",
        "firm": "Nelson Mullins",
        "dm": (
            "Hey Michael — quick question for you at Nelson Mullins: do you have "
            "real-time visibility into attorney file access patterns? Specifically "
            "around the notice period?\n\n"
            "We keep hearing from managing partners that this is the biggest blind "
            "spot. Built something that solves it. Worth a look?"
        ),
    },
    {
        "id": 5,
        "name": "Burleigh Singleton",
        "firm": "Kilpatrick Townsend",
        "dm": (
            "Hey Burleigh — Kilpatrick Townsend has major IP and tech practices. "
            "That means your case files are high-value targets when attorneys "
            "make lateral moves.\n\n"
            "We detect file staging behavior in real time — before the resignation "
            "letter. Everything runs on-premise. Would it be useful to see how it works?"
        ),
    },
    {
        "id": 6,
        "name": "Jenny Lambert",
        "firm": "Eversheds Sutherland",
        "dm": (
            "Hey Jenny — given your focus on AI, cybersecurity and data privacy, "
            "you'd probably appreciate this: we built insider threat detection "
            "specifically for law firms. 117 behavioral patterns tuned to how "
            "attorneys actually exfiltrate data.\n\n"
            "All on-premise. No client data leaves the firm's network. "
            "Would love your take on it."
        ),
    },
    {
        "id": 90,
        "name": "Tunde Ezekiel",
        "firm": "The Ezekiel Law Firm",
        "dm": (
            "Hey Tunde — wanted to follow up. I'm working with Atlanta law firms "
            "on a problem that keeps flying under the radar: data walking out "
            "the door when attorneys leave.\n\n"
            "77 days is the average detection time. We cut it to 3 seconds. "
            "Worth a quick 10-minute demo? No pressure — just want to show you "
            "what we've built."
        ),
    },
]

# ─── Quick preview ────────────────────────────────────────────

if __name__ == "__main__":
    for i, msg in enumerate(BATCH, 1):
        print(f"\n{'='*60}")
        print(f"  DM {i}/10 — #{msg['id']} {msg['name']} @ {msg['firm']}")
        print(f"{'='*60}")
        print(f"\n{msg['dm']}\n")

    print("\n" + "="*60)
    print("  10 DMs ready. Open LinkedIn → Send → Mark sent.")
    print("="*60)
