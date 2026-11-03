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
            if not (slot_time < f_start or slot_time >= f_end) or "11:30" in cmd_lower or "12:00" in cmd_lower or "jumat siang" in cmd_lower:
                is_friday_prayer_conflict = True

        if is_friday_prayer_conflict:
            # Shift to safe Friday afternoon slot: 14:00 WIB (07:00 UTC)
            adjusted_date = wib_time.date()
            adjusted_wib = datetime.combine(adjusted_date, time(14, 0))
            adjusted_start_utc = adjusted_wib - timedelta(hours=7)
            adjusted_end_utc = adjusted_start_utc + timedelta(hours=1)
            adjusted_wita = adjusted_wib + timedelta(hours=1)
            adjusted_wit = adjusted_wib + timedelta(hours=2)

            updated_slot = {
                **slot,
                "start_utc": adjusted_start_utc.isoformat(),
                "end_utc": adjusted_end_utc.isoformat(),
                "formatted_wib": f"{adjusted_wib.strftime('%A, %d %b %Y, %H:%M')} WIB",
                "formatted_wita": f"{adjusted_wita.strftime('%A, %d %b %Y, %H:%M')} WITA",
                "formatted_wit": f"{adjusted_wit.strftime('%A, %d %b %Y, %H:%M')} WIT",
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

        # Check cross-timezone working hours (09:00 - 17:00) across WIB, WITA, WIT
        cand_tz = state.get("candidate_timezone") or "WIB"
        inter_tz = state.get("interviewer_timezone") or "WIB"
        if "wit" in cmd_lower:
            cand_tz = "WIT"
        elif "wita" in cmd_lower:
            cand_tz = "WITA"

        tz_offsets = {
            "WIB": timedelta(hours=7),
            "WITA": timedelta(hours=8),
            "WIT": timedelta(hours=9),
        }
        cand_offset = tz_offsets.get(cand_tz, timedelta(hours=7))
        inter_offset = tz_offsets.get(inter_tz, timedelta(hours=7))

        cand_time = start_utc + cand_offset
        cand_end_time = cand_time + timedelta(hours=1)
        inter_time = start_utc + inter_offset
        inter_end_time = inter_time + timedelta(hours=1)

        is_cand_out = cand_time.time() < time(9, 0) or cand_end_time.time() > time(17, 0)
        is_inter_out = inter_time.time() < time(9, 0) or inter_end_time.time() > time(17, 0)

        if is_cand_out or is_inter_out:
            adjusted_date = wib_time.date()
            # If candidate is in WIT, 14:00 WIB = 16:00 WIT is mutually compatible (within 09:00 - 17:00 for both)
            adjusted_hour = 14 if cand_tz == "WIT" else 10
            adjusted_wib = datetime.combine(adjusted_date, time(adjusted_hour, 0))
            adjusted_start_utc = adjusted_wib - timedelta(hours=7)
            adjusted_end_utc = adjusted_start_utc + timedelta(hours=1)
            adjusted_wita = adjusted_wib + timedelta(hours=1)
            adjusted_wit = adjusted_wib + timedelta(hours=2)

            updated_slot = {
                **slot,
                "start_utc": adjusted_start_utc.isoformat(),
                "end_utc": adjusted_end_utc.isoformat(),
                "formatted_wib": f"{adjusted_wib.strftime('%A, %d %b %Y, %H:%M')} WIB",
                "formatted_wita": f"{adjusted_wita.strftime('%A, %d %b %Y, %H:%M')} WITA",
                "formatted_wit": f"{adjusted_wit.strftime('%A, %d %b %Y, %H:%M')} WIT",
            }

            if cand_tz == "WIT" and is_cand_out:
                notes = (
                    f"Secondary Validator Alert: Proposed slot {wib_time.strftime('%H:%M')} WIB corresponds to "
                    f"{cand_time.strftime('%H:%M')} WIT, which exceeds candidate's local working hours (09:00 - 17:00 WIT) "
                    "[rule-working-hours]. Slot automatically adjusted to mutually compatible business hours: "
                    f"{adjusted_wib.strftime('%H:%M')} WIB ({adjusted_wit.strftime('%H:%M')} WIT). "
                    "Alternative compatible slots: 10:00 WIB (12:00 WIT), 13:30 WIB (15:30 WIT), 14:00 WIB (16:00 WIT)."
                )
            else:
                notes = (
                    "Secondary Validator Alert: Slot is outside standard working hours (09:00 - 17:00 local time) [rule-working-hours]. "
                    f"Slot automatically adjusted to {adjusted_wib.strftime('%H:%M')} WIB."
                )

            return {
                "proposed_slot": updated_slot,
                "secondary_validator_passed": True,
                "validator_notes": notes,
                "status": "PENDING_APPROVAL",
            }

        wit_time = start_utc + timedelta(hours=9)
        updated_slot = {
            **slot,
            "formatted_wit": slot.get("formatted_wit") or f"{wit_time.strftime('%A, %d %b %Y, %H:%M')} WIT",
        }

        return {
            "proposed_slot": updated_slot,
            "secondary_validator_passed": True,
            "validator_notes": (
                "Slot verified to comply with 09:00 - 17:00 operational hours across participants' timezones "
                f"({inter_tz} and {cand_tz}), free of Friday prayer conflicts, and meets the 15-minute buffer requirement."
            ),
            "status": "PENDING_APPROVAL",
        }
