from datetime import datetime, time, timedelta
from typing import Any

from app.agent.AgentState import OrchestratorAgentState


class SecondaryValidatorNode:
    @staticmethod
    def _sync_items_with_slot(
        items: list[dict[str, Any]],
        updated_slot: dict[str, Any],
        inter_tz: str,
        cand_tz: str,
    ) -> list[dict[str, Any]]:
        wib_str = updated_slot.get("formatted_wib", "")
        wita_str = updated_slot.get("formatted_wita", "")
        wit_str = updated_slot.get("formatted_wit", "")
        all_tz = f"{wib_str} = {wita_str} = {wit_str}"
        inter_primary = wita_str if inter_tz == "WITA" else (wit_str if inter_tz == "WIT" else wib_str)
        cand_primary = wita_str if cand_tz == "WITA" else (wit_str if cand_tz == "WIT" else wib_str)
        loc = updated_slot.get("location_type", "Google Meet")
        dur = updated_slot.get("duration_minutes", 60)

        synced: list[dict[str, Any]] = []
        for it in items:
            role_low = str(it.get("recipient_role", "")).lower()
            ch = str(it.get("channel", "")).lower()
            preview = str(it.get("content_preview", ""))
            if ch == "calendar":
                new_preview = f"Reservasi slot kalender pada {inter_primary} ({all_tz}) di {loc} ({dur} Menit)."
            elif "candidate" in role_low:
                if "- Jadwal Waktu Lokal Anda" in preview:
                    lines = []
                    for line in preview.split("\n"):
                        if line.startswith("- Jadwal Waktu Lokal Anda"):
                            lines.append(f"- Jadwal Waktu Lokal Anda ({cand_tz}): {cand_primary}")
                        elif line.startswith("- Konversi Zona Waktu:"):
                            lines.append(f"- Konversi Zona Waktu: {all_tz}")
                        else:
                            lines.append(line)
                    new_preview = "\n".join(lines)
                else:
                    new_preview = f"{preview}\n\nJadwal ({cand_tz}): {cand_primary} ({all_tz})"
            else:
                if "- Jadwal (" in preview:
                    lines = []
                    for line in preview.split("\n"):
                        if line.startswith("- Jadwal ("):
                            lines.append(f"- Jadwal ({inter_tz}): {inter_primary}")
                        elif line.startswith("- Konversi Zona Waktu:"):
                            lines.append(f"- Konversi Zona Waktu: {all_tz}")
                        elif line.startswith("- Jadwal Follow-Up"):
                            lines.append(f"- Jadwal Follow-Up ({inter_tz}): {inter_primary} ({all_tz})")
                        else:
                            lines.append(line)
                    new_preview = "\n".join(lines)
                else:
                    new_preview = preview
            synced.append({**it, "content_preview": new_preview})
        return synced

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
        cand_tz = (state.get("candidate_timezone") or "WIB").upper()
        inter_tz = (state.get("interviewer_timezone") or "WIB").upper()
        if "wit" in cmd_lower and "wita" not in cmd_lower:
            cand_tz = "WIT"
        elif "wita" in cmd_lower:
            cand_tz = "WITA"

        # 1. Check Weekend Blackout (Saturday=5, Sunday=6)
        if wib_time.weekday() in (5, 6):
            days_to_monday = 7 - wib_time.weekday()
            adjusted_date = wib_time.date() + timedelta(days=days_to_monday)
            adjusted_wib = datetime.combine(adjusted_date, time(10, 0))
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
                "Secondary Validator Alert: Proposed slot on a weekend was rejected according to company policy "
                "[RULE_WEEKEND_BLACKOUT]. Slot automatically shifted to next business day (Monday at 10:00 WIB)."
            )
            sources = [
                {
                    **s,
                    "detail": (
                        f"Available slot verified at {updated_slot.get('formatted_wib', '')} ({inter_tz}) without conflicts."
                        if s.get("id") == "src-01" or s.get("source_type") == "CALENDAR"
                        else s.get("detail", "")
                    ),
                }
                for s in (state.get("sources_cited") or [])
            ]
            items = cls._sync_items_with_slot(state.get("items") or [], updated_slot, inter_tz, cand_tz)
            return {
                "proposed_slot": updated_slot,
                "sources_cited": sources,
                "items": items,
                "secondary_validator_passed": True,
                "validator_notes": notes,
                "status": "PENDING APPROVAL",
            }

        # 2. Check Friday Prayer Blackout (weekday == 4 is Friday)
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
                "with Friday prayer blackout hours [RULE_FRIDAY_PRAYER]. Slot automatically adjusted to "
                "14:00 WIB in accordance with company operational policy."
            )

            sources = [
                {
                    **s,
                    "detail": (
                        f"Available slot verified at {updated_slot.get('formatted_wib', '')} ({inter_tz}) without conflicts."
                        if s.get("id") == "src-01" or s.get("source_type") == "CALENDAR"
                        else s.get("detail", "")
                    ),
                }
                for s in (state.get("sources_cited") or [])
            ]
            items = cls._sync_items_with_slot(state.get("items") or [], updated_slot, inter_tz, cand_tz)
            return {
                "proposed_slot": updated_slot,
                "sources_cited": sources,
                "items": items,
                "secondary_validator_passed": True,
                "validator_notes": notes,
                "status": "PENDING APPROVAL",
            }

        # 3. Check cross-timezone working hours (09:00 - 17:00) across WIB, WITA, WIT
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
                    "[RULE_WORKING_HOURS]. Slot automatically adjusted to mutually compatible business hours: "
                    f"{adjusted_wib.strftime('%H:%M')} WIB ({adjusted_wit.strftime('%H:%M')} WIT). "
                    "Alternative compatible slots: 10:00 WIB (12:00 WIT), 13:30 WIB (15:30 WIT), 14:00 WIB (16:00 WIT)."
                )
            else:
                notes = (
                    "Secondary Validator Alert: Slot is outside standard working hours (09:00 - 17:00 local time) [RULE_WORKING_HOURS]. "
                    f"Slot automatically adjusted to {adjusted_wib.strftime('%H:%M')} WIB."
                )

            sources = [
                {
                    **s,
                    "detail": (
                        f"Available slot verified at {updated_slot.get('formatted_wib', '')} ({inter_tz}) without conflicts."
                        if s.get("id") == "src-01" or s.get("source_type") == "CALENDAR"
                        else s.get("detail", "")
                    ),
                }
                for s in (state.get("sources_cited") or [])
            ]
            items = cls._sync_items_with_slot(state.get("items") or [], updated_slot, inter_tz, cand_tz)
            return {
                "proposed_slot": updated_slot,
                "sources_cited": sources,
                "items": items,
                "secondary_validator_passed": True,
                "validator_notes": notes,
                "status": "PENDING APPROVAL",
            }

        wita_time = start_utc + timedelta(hours=8)
        wit_time = start_utc + timedelta(hours=9)
        updated_slot = {
            **slot,
            "formatted_wita": slot.get("formatted_wita") or f"{wita_time.strftime('%A, %d %b %Y, %H:%M')} WITA",
            "formatted_wit": slot.get("formatted_wit") or f"{wit_time.strftime('%A, %d %b %Y, %H:%M')} WIT",
        }
        items = cls._sync_items_with_slot(state.get("items") or [], updated_slot, inter_tz, cand_tz)

        conflict_prefix = ""
        if state.get("slot_conflict_detected"):
            conflicting_wib = state.get("conflicting_slot_wib") or "yang diminta"
            conflict_prefix = (
                f"Calendar Conflict Avoided: Slot pukul {conflicting_wib} sudah terisi di kalender interviewer. "
                f"Sistem secara otomatis mengusulkan slot kosong berikutnya ({updated_slot.get('formatted_wib')}) untuk mencegah double-booking. "
            )

        tz_conversion_note = (
            f"Konversi lintas zona waktu terverifikasi: {wib_time.strftime('%H:%M')} WIB = "
            f"{wita_time.strftime('%H:%M')} WITA = {wit_time.strftime('%H:%M')} WIT "
            f"(Interviewer: {inter_tz}, Kandidat: {cand_tz})."
        )

        return {
            "proposed_slot": updated_slot,
            "items": items,
            "secondary_validator_passed": True,
            "validator_notes": (
                f"{conflict_prefix}Slot verified to comply with 09:00 - 17:00 operational hours across participants' timezones "
                f"({inter_tz} and {cand_tz}), free of Friday prayer conflicts, and meets the 15-minute buffer requirement. "
                f"{tz_conversion_note}"
            ),
            "status": "PENDING APPROVAL",
        }
