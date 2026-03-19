"""
Sales Engine — Message Personalization
========================================
Generates ready-to-paste cold emails, LinkedIn messages,
and follow-up sequences by merging prospect data with
vertical-specific templates, pain points, and stats.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from aionos.sales.engine import SalesEngine
from aionos.sales.models import BuyerPersona, VerticalID


class MessageGenerator:
    """
    Feed in a prospect → get ready-to-paste messages for every channel.

    Usage:
        gen = MessageGenerator()
        msgs = gen.generate(
            name="Sarah Chen",
            company="Baker McKenzie",
            title="Managing Partner",
            vertical="legal",
        )
        print(msgs["cold_email"])
        print(msgs["linkedin_request"])
        print(msgs["follow_up_1"])
    """

    def __init__(self, engine: Optional[SalesEngine] = None) -> None:
        self._engine = engine or SalesEngine()

    def _match_persona(
        self, vertical_id: str, title: str
    ) -> BuyerPersona:
        """Find the best matching persona for a prospect's title."""
        personas = self._engine.get_personas(vertical_id)
        title_lower = title.lower()
        # exact-ish match
        for p in personas:
            if p.title.lower() in title_lower or title_lower in p.title.lower():
                return p
        # role words
        role_hints = {
            "partner": "decision_maker",
            "director": "technical",
            "cio": "technical",
            "ciso": "technical",
            "cto": "technical",
            "counsel": "influencer",
            "compliance": "influencer",
            "president": "decision_maker",
            "vp": "influencer",
            "manager": "influencer",
            "officer": "influencer",
        }
        for hint, role in role_hints.items():
            if hint in title_lower:
                matches = self._engine.get_personas(vertical_id, role=role)
                if matches:
                    return matches[0]
        # fallback: decision maker
        dm = self._engine.get_decision_maker(vertical_id)
        return dm or personas[0]

    def generate(
        self,
        name: str,
        company: str,
        title: str = "",
        vertical: str = "legal",
        sender_name: str = "EchoBlue Holdings",
        sender_email: str = "echoworksaillc@gmail.com",
    ) -> Dict[str, str]:
        """
        Generate all outbound messages for a prospect.

        Returns dict with keys:
          - cold_email (subject + body)
          - linkedin_request (300 char)
          - follow_up_1 (day 3-4)
          - follow_up_2 (day 7)
          - follow_up_3 (day 14, breakup)
          - objection_dlp (if they mention existing tools)
          - objection_budget
          - objection_cloud
        """
        v = self._engine.get_vertical(vertical)
        persona = self._match_persona(vertical, title or "Partner")
        scenarios = v.threat_scenarios
        top_scenario = scenarios[0]
        regs = v.regulatory_hooks
        stats = v.stats
        first_name = name.split()[0] if name else "there"

        # ── Cold Email ─────────────────────────────────────
        cold_email = self._build_cold_email(
            first_name, company, persona, top_scenario, regs,
            stats, sender_name, sender_email, v.display_name,
        )

        # ── LinkedIn Request (300 char max) ────────────────
        linkedin_request = self._build_linkedin_request(
            first_name, persona, top_scenario, v.display_name,
        )

        # ── Follow-ups ────────────────────────────────────
        follow_up_1 = self._build_follow_up(
            first_name, company, persona, top_scenario, 1,
            sender_name, sender_email,
        )
        follow_up_2 = self._build_follow_up(
            first_name, company, persona, top_scenario, 2,
            sender_name, sender_email,
        )
        follow_up_3 = self._build_breakup(
            first_name, company, persona, sender_name, sender_email,
        )

        # ── Objection handlers ────────────────────────────
        objections = {}
        for obj in v.objections:
            key = obj.objection[:30].lower().replace(" ", "_")
            objections[f"objection_{key}"] = (
                f"If they say: \"{obj.objection}\"\n\n"
                f"Response: {obj.response}"
                + (f"\n\nProof: {obj.proof_point}" if obj.proof_point else "")
            )

        result = {
            "cold_email": cold_email,
            "linkedin_request": linkedin_request,
            "follow_up_1": follow_up_1,
            "follow_up_2": follow_up_2,
            "follow_up_3": follow_up_3,
        }
        result.update(objections)
        return result

    def _build_cold_email(
        self, first_name, company, persona, scenario, regs,
        stats, sender_name, sender_email, vertical_name,
    ) -> str:
        subject = persona.email_subject
        pain = persona.pain_points[0] if persona.pain_points else ""
        reg_name = regs[0].name if regs else ""
        reg_penalty = regs[0].penalty_range if regs else ""
        chain = " -> ".join(scenario.event_chain[:3])
        speed = scenario.detection_speed
        impact = scenario.financial_impact

        return (
            f"Subject: {subject}\n\n"
            f"{first_name},\n\n"
            f"{persona.opening_line}\n\n"
            f"The attack chain is always the same: {chain}. "
            f"By the time it's discovered, the damage is done -- "
            f"{impact}.\n\n"
            f"We built a detection engine that catches this pattern "
            f"in {speed} -- before anyone knows it's happening. "
            f"It runs entirely on-premise. No data leaves {company}'s "
            f"network.\n\n"
            f"The regulatory exposure is real: {reg_name} "
            f"({reg_penalty}). Our system provides litigation-ready "
            f"evidence chains that hold up in proceedings.\n\n"
            f"I have a 3-minute recording of the system running "
            f"through a full {scenario.name.lower()} scenario — "
            f"detection, containment, evidence preservation. "
            f"Happy to send it over if useful.\n\n"
            f"Best,\n"
            f"{sender_name}\n"
            f"{sender_email}"
        )

    def _build_linkedin_request(
        self, first_name, persona, scenario, vertical_name,
    ) -> str:
        pain = persona.pain_points[0] if persona.pain_points else ""
        speed = scenario.detection_speed
        # Hard cap at 300 chars for LinkedIn
        msg = (
            f"Hi {first_name} -- quick question: {pain.lower().rstrip('.')}? "
            f"We built a system that detects {scenario.name.lower()} "
            f"in {speed}, runs 100% on-premise. "
            f"3-min demo recording available if relevant."
        )
        return msg[:300]

    def _build_follow_up(
        self, first_name, company, persona, scenario, num,
        sender_name, sender_email,
    ) -> str:
        if num == 1:
            subject = f"Re: {persona.email_subject}"
            body = (
                f"{first_name},\n\n"
                f"Following up on my note about {scenario.name.lower()} "
                f"detection at {company}.\n\n"
                f"The 3-minute recording shows:\n"
                f"  • Real-time event ingestion\n"
                f"  • Pattern detection in {scenario.detection_speed}\n"
                f"  • Full NIST incident response automation\n"
                f"  • Everything running on-premise, no cloud\n\n"
                f"Want me to send the recording?\n\n"
                f"Best,\n{sender_name}\n{sender_email}"
            )
        else:
            trigger = persona.trigger_events[0] if persona.trigger_events else ""
            subject = f"Quick question for {company}"
            body = (
                f"{first_name},\n\n"
                f"Curious — has {company} dealt with "
                f"{trigger.lower().rstrip('.')}?\n\n"
                f"If so, we can show you exactly how our system would "
                f"have caught it. 20-minute screen share, no slides.\n\n"
                f"Best,\n{sender_name}\n{sender_email}"
            )
        return f"Subject: {subject}\n\n{body}"

    def _build_breakup(
        self, first_name, company, persona, sender_name, sender_email,
    ) -> str:
        subject = f"Closing the loop — {company}"
        body = (
            f"{first_name},\n\n"
            f"I've reached out a few times about insider threat "
            f"detection for {company}. I know timing matters.\n\n"
            f"If this isn't a priority right now, no worries -- "
            f"I'll stop following up. But if something changes "
            f"(a departure incident, a compliance audit, a client "
            f"security requirement), we're here.\n\n"
            f"The 3-minute demo recording is always available: "
            f"{sender_email}\n\n"
            f"Best,\n{sender_name}\n{sender_email}"
        )
        return f"Subject: {subject}\n\n{body}"

    def batch_generate(
        self, prospects: List[Dict], sender_name: str = "EchoBlue Holdings",
    ) -> List[Dict]:
        """
        Generate messages for a batch of prospects.

        Each prospect dict must have: name, company, vertical.
        Optional: title, email, linkedin.

        Returns list of dicts with prospect info + all messages.
        """
        results = []
        for p in prospects:
            msgs = self.generate(
                name=p["name"],
                company=p["company"],
                title=p.get("title", ""),
                vertical=p.get("vertical", "legal"),
                sender_name=sender_name,
            )
            results.append({
                "prospect": p,
                "messages": msgs,
            })
        return results

    def daily_batch(
        self, pipeline, date: str = None, sender_name: str = "EchoBlue Holdings",
    ) -> List[Dict]:
        """
        Pull today's action queue from the pipeline,
        generate personalized messages for each.

        Returns list of {prospect, messages, recommended_channel, recommended_action}.
        """
        from aionos.sales.engine import SalesEngine
        queue = pipeline.daily_queue(date)
        results = []
        for p in queue:
            msgs = self.generate(
                name=p["name"],
                company=p["company"],
                title=p.get("title", ""),
                vertical=p.get("vertical", "legal"),
                sender_name=sender_name,
            )
            # Get recommended next action from sequence
            seq_day = p.get("sequence_day", 0)
            next_action = self._engine.get_next_action(
                p["vertical"], seq_day
            )
            results.append({
                "prospect_id": p["id"],
                "name": p["name"],
                "company": p["company"],
                "vertical": p["vertical"],
                "stage": p["stage"],
                "messages": msgs,
                "recommended_channel": next_action.channel if next_action else "email",
                "recommended_action": next_action.action if next_action else "Follow up",
            })
        return results
