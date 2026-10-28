import asyncio
import sys

from app.service.EmailDispatcherService import EmailDispatcherService


async def main() -> None:
    to_email = sys.argv[1] if len(sys.argv) > 1 else "akhtar.ramadhan01@gmail.com"
    print(f"[*] Pre-flight testing email dispatch to: {to_email}")

    service = EmailDispatcherService()
    print(f"[*] SMTP Host: {service.host}:{service.port} (SSL={service.use_ssl})")
    print(f"[*] SMTP User: {service.user}")

    citations = [
        {
            "ref_code": "[cal-budi-santoso]",
            "title": "Kalender Budi Santoso",
            "detail": "Slot terverifikasi kosong pukul 10:00 WIB tanpa bentrok jadwal.",
        },
        {
            "ref_code": "[rule-jumatan]",
            "title": "Aturan Operasional Kantor",
            "detail": "Di luar jendela Sholat Jumat (11:30 - 13:00 WIB).",
        },
        {
            "ref_code": "[cand-ats-akhtar]",
            "title": "Preferensi Kandidat",
            "detail": "Posisi: Lead AI Engineer / Fullstack Developer.",
        },
    ]

    res = await service.send_interview_email(
        to_email=to_email,
        recipient_name="Akhtar Ramadhan",
        recipient_role="Candidate",
        subject="[Heketon Live Test] Undangan User Technical Interview: Akhtar Ramadhan",
        content="Selamat! Berdasarkan hasil evaluasi resume dan kualifikasi teknis, kami mengundang Anda ke sesi User Technical Interview untuk membahas arsitektur AI Orchestrator.",
        slot_wib="Rabu, 29 Oktober 2026, 10:00 - 11:00 WIB",
        meeting_link="https://meet.google.com/hkt-ops-2026",
        citations=citations,
    )

    print("\n[+] Result:", res)
    if res.get("success"):
        print(f"\nSUCCESS! Real email sent to {to_email}! Message-ID: {res.get('message_id')}")
        sys.exit(0)
    else:
        print(f"\nFAILED! Error: {res.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
