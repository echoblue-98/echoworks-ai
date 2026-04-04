"""
EchoWorks — Saturday Batch: 10 LinkedIn DMs
============================================
Generated April 4, 2026

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
    {
        "id": 85,
        "name": "Emmanuel Dressie",
        "firm": "Dressie Law Firm",
        "dm": (
            "Hey Emmanuel — saw you're running Dressie Law Firm out of Atlanta. "
            "Quick question: do you have visibility into what happens with client "
            "files when an attorney transitions out of your firm?\n\n"
            "It's the #1 blind spot we're seeing at firms your size right now. "
            "Happy to share what we're finding if it's useful."
        ),
    },
    {
        "id": 86,
        "name": "Michael Day",
        "firm": "Michael D Law Firm",
        "dm": (
            "Hey Michael — curious: if one of your attorneys gave notice tomorrow, "
            "would you know what client files they accessed in the last 30 days?\n\n"
            "Most firms we talk to can't answer that. We built something that solves it. "
            "Happy to show you if it's relevant."
        ),
    },
    {
        "id": 87,
        "name": "David Danda",
        "firm": "David Danda P.C.",
        "dm": (
            "Hey David — I work with law firms on insider threat detection. "
            "One pattern we keep seeing: attorneys stage files 2-4 weeks before "
            "a resignation letter. By the time the firm notices, it's too late.\n\n"
            "Worth a quick conversation? No pitch — just sharing what we're seeing."
        ),
    },
    {
        "id": 88,
        "name": "Shannon Pawley",
        "firm": "The Estate & Asset Protection Law Firm",
        "dm": (
            "Hey Shannon — estate and asset protection means your firm handles "
            "some of the most sensitive financial data in legal. Quick question: "
            "what happens to that data when someone leaves your team?\n\n"
            "We're helping firms answer that question before it becomes a crisis. "
            "Happy to share more if it's useful."
        ),
    },
    {
        "id": 89,
        "name": "Jessica Tehlirian",
        "firm": "Tehlirian Law Group",
        "dm": (
            "Hey Jessica — I saw you're leading Tehlirian Law Group in Atlanta. "
            "We work with law firms on a problem most don't think about until it "
            "hits them: data walking out the door when attorneys leave.\n\n"
            "Average detection time? 77 days. By then, the damage is done. "
            "Worth a 10-minute conversation?"
        ),
    },
    {
        "id": 91,
        "name": "Gerard Briceno",
        "firm": "Bridger Law Group",
        "dm": (
            "Hey Gerard — quick question for you: if an attorney at Bridger Law "
            "started downloading client files before giving notice, would your "
            "current systems flag it?\n\n"
            "Most firms we talk to say no. That's the gap we close. "
            "Happy to share how if it's on your radar."
        ),
    },
    {
        "id": 92,
        "name": "Lorena Saedi",
        "firm": "Saedi Law Group",
        "dm": (
            "Hey Lorena — I work with Atlanta law firms on a specific problem: "
            "protecting client data when attorneys transition. Did you know the "
            "average firm takes 77 days to discover insider data theft?\n\n"
            "We cut that to under 3 seconds. No cloud. Everything stays on your "
            "servers. Worth a quick look?"
        ),
    },
    {
        "id": 93,
        "name": "Donald P. Edwards",
        "firm": "The Law Office of Don Edwards",
        "dm": (
            "Hey Don — I noticed your practice in Atlanta. Quick question that "
            "keeps coming up with managing partners: what's your plan if an "
            "attorney leaves and takes client contacts with them?\n\n"
            "It's the most common insider threat in legal and the least monitored. "
            "Happy to share what we're building to solve it."
        ),
    },
    {
        "id": 95,
        "name": "Ronan Doherty",
        "firm": "Bondurant Mixson & Elmore",
        "dm": (
            "Hey Ronan — Bondurant handles some of the highest-value litigation "
            "in Atlanta. That means your case files are exactly what competitors "
            "want when an attorney makes a lateral move.\n\n"
            "We help firms like yours detect data staging before the resignation "
            "letter arrives. Worth a conversation?"
        ),
    },
    {
        "id": 96,
        "name": "Henry Warnock",
        "firm": "FordHarrison LLP",
        "dm": (
            "Hey Henry — FordHarrison has 200+ attorneys across multiple offices. "
            "That's a lot of endpoints and a lot of lateral movement in employment "
            "law.\n\n"
            "Question: do you have real-time visibility into attorney file access "
            "patterns? When someone gives notice, do you know what they touched?\n\n"
            "That's what we solve. Happy to show you."
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
