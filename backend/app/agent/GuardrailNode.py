import re
from typing import Any

from app.agent.AgentState import OrchestratorAgentState

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions?",
    r"abort\s+(all\s+)?(security|rules?|policies)",
    r"system\s+(override|prompt|directive)",
    r"bypass\s+(all\s+)?(guardrails?|checks?|approval)",
    r"send\s+salary\s+(100m|direct|immediately|\d+)",
    r"approve\s+(directly|without\s+human|immediately)",
    r"disregard\s+(the\s+)?(rules?|restrictions?)",
    r"you\s+are\s+now\s+(in\s+developer\s+mode|dan\s+mode|unrestricted)",
    r"gaji\s+100\s*juta",
    r"abaikan\s+(seluruh|semua)\s+aturan",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


class GuardrailNode:
    """Node 1: Prompt Injection & Security Scanner (Pilar PERMISSIONS & RECORD).

    Examines incoming natural language instructions, candidate WhatsApp messages,
    and interview notes for directive overrides, unauthorized elevation attempts,
    or prompt injections.
    """

    @classmethod
    def scan_text(cls, text: str) -> tuple[bool, str]:
        """Scans input text; returns (is_safe, notes)."""
        clean_text = text.strip().lower()
        if not clean_text:
            return True, "Input kosong atau aman."

        for pattern in COMPILED_PATTERNS:
            if pattern.search(clean_text):
                return False, (
                    "Guardrail Alert: Terdeteksi indikasi prompt injection / instruksi adversarial liar. "
                    "Instruksi diisolasi untuk mencegah pelanggaran pilar PERMISSIONS."
                )

        # Keyword heuristics
        suspicious_keywords = ["bypass", "system prompt", "abort all", "ignore previous", "override policy"]
        if any(kw in clean_text for kw in suspicious_keywords):
            return False, "Guardrail Alert: Pola teks berisiko tinggi terdeteksi dan diblokir."

        return True, "Instruksi terverifikasi aman bebas prompt injection."

    @classmethod
    async def run(cls, state: OrchestratorAgentState) -> dict[str, Any]:
        """LangGraph node execution."""
        command = state.get("command", "")
        is_safe, notes = cls.scan_text(command)

        updates: dict[str, Any] = {
            "guardrail_passed": is_safe,
            "guardrail_notes": notes,
            "injection_detected": not is_safe,
        }

        if not is_safe:
            audit_entry = {
                "event_type": "GUARDRAIL_BLOCKED",
                "actor": state.get("sender_role", "USER"),
                "actor_type": "AGENT",
                "title": "Adversarial Prompt Injection Blocked",
                "description": notes,
                "metadata": {"raw_command": command, "is_injection": True},
            }
            existing_audits = state.get("audit_entries", [])
            updates["audit_entries"] = [*existing_audits, audit_entry]

        return updates
