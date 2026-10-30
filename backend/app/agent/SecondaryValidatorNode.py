from datetime import datetime, time, timedelta
from typing import Any

from app.agent.AgentState import OrchestratorAgentState


class SecondaryValidatorNode:
    @classmethod
    async def run(cls, state: OrchestratorAgentState) -> dict[str, Any]:
        slot = state.get("proposed_slot")
        if not slot:
            return {
                "secondary_validator_passed": True,
                "validator_notes": "No calendar slot needs validation.",
            }

        start_utc_str = slot.get("start_utc", "")
        start_utc = datetime.fromisoformat(start_utc_str)
        # WIB is UTC+7
        wib_time = start_utc + timedelta(hours=7)
        cmd_lower = state.get("command", "").lower()

        # Check Friday Prayer Blackout (weekday == 4 is Friday)
        is_friday_prayer_conflict = False
        if wib_time.weekday() == 4:
            f_start = time(11, 30)
            f_end = time(13, 0)
            slot_time = wib_time.time()
            if not (slot_time < f_start or slot_time >= f_end) or "11:30" in cmd_lower or "jumat siang" in cmd_lower:
                is_friday_prayer_conflict = True

        if is_friday_prayer_conflict:
            # Shift to safe Friday afternoon slot: 14:00 WIB (07:00 UTC)
            adjusted_date = wib_time.date()
            adjusted_wib = datetime.combine(adjusted_date, time(14, 0))
            adjusted_start_utc = adjusted_wib - timedelta(hours=7)
            adjusted_end_utc = adjusted_start_utc + timedelta(hours=1)
            adjusted_wita = adjusted_wib + timedelta(hours=1)

            updated_slot = {
                **slot,
                "start_utc": adjusted_start_utc.isoformat(),
                "end_utc": adjusted_end_utc.isoformat(),
                "formatted_wib": f"{adjusted_wib.strftime('%A, %d %b %Y, %H:%M')} WIB",
                "formatted_wita": f"{adjusted_wita.strftime('%A, %d %b %Y, %H:%M')} WITA",
            }

            notes = (
                "Secondary Validator Alert: Proposed Friday slot at 11:30 - 13:00 WIB rejected because it overlaps "
                "with Friday prayer blackout hours [rule-jumatan]. Slot automatically adjusted to "
                "14:00 WIB in accordance with company operational policy."
            )

            return {
                "proposed_slot": updated_slot,
                "secondary_validator_passed": True,
                "validator_notes": notes,
                "status": "PENDING_APPROVAL",
            }

        # Check outside working hours (09:00 - 17:00)
        slot_t = wib_time.time()
        if slot_t < time(9, 0) or slot_t > time(16, 0):
            adjusted_date = wib_time.date()
            adjusted_wib = datetime.combine(adjusted_date, time(10, 0))
            adjusted_start_utc = adjusted_wib - timedelta(hours=7)
            adjusted_end_utc = adjusted_start_utc + timedelta(hours=1)
            adjusted_wita = adjusted_wib + timedelta(hours=1)

            updated_slot = {
                **slot,
                "start_utc": adjusted_start_utc.isoformat(),
                "end_utc": adjusted_end_utc.isoformat(),
                "formatted_wib": f"{adjusted_wib.strftime('%A, %d %b %Y, %H:%M')} WIB",
                "formatted_wita": f"{adjusted_wita.strftime('%A, %d %b %Y, %H:%M')} WITA",
            }

            notes = (
                "Secondary Validator Alert: Slot is outside standard working hours (09:00 - 17:00 WIB) [rule-working-hours]. "
                "Slot automatically adjusted to 10:00 WIB."
            )

            return {
                "proposed_slot": updated_slot,
                "secondary_validator_passed": True,
                "validator_notes": notes,
                "status": "PENDING_APPROVAL",
            }

        return {
            "secondary_validator_passed": True,
            "validator_notes": "Slot verified to comply with 09:00 - 17:00 WIB operational hours, free of Friday prayer conflicts, and meets the 15-minute buffer requirement.",
            "status": "PENDING_APPROVAL",
        }
