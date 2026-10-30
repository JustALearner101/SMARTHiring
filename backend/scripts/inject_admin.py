import asyncio
import sys
from datetime import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import select

from app.core.AppSecurity import get_password_hash
from app.db.DatabaseSession import AsyncSessionLocal
from app.model.CalendarModel import WorkCalendar
from app.model.UserModel import Permission, User


async def inject_admin_users() -> None:
    """Inject baseline administrative users, work calendar, and RBAC permissions."""
    print("=" * 60)
    print(" Menginjeksi Akun Admin & Kebijakan Dasar (Heketon)")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # 1. WorkCalendar
        existing_cal = (
            await session.execute(
                select(WorkCalendar).where(WorkCalendar.voffice_code == "JKT-HQ")
            )
        ).scalars().first()

        if not existing_cal:
            cal = WorkCalendar(
                voffice_code="JKT-HQ",
                vtimezone="WIB",
                twork_start=time(9, 0),
                twork_end=time(17, 0),
                tfriday_prayer_start=time(11, 30),
                tfriday_prayer_end=time(13, 0),
                nmax_negotiation_rounds=3,
                nbuffer_minutes=15,
                binjection_guardrail_enabled=True,
            )
            session.add(cal)
            print("  [OK] Kebijakan operasional kantor JKT-HQ dibuat.")
        else:
            print("  [OK] Kebijakan operasional kantor JKT-HQ sudah ada.")

        # 2. Admin Users
        default_password_hash = get_password_hash("password123")

        admin_users = [
            {
                "vuserid": "EMP-HR-001",
                "vname": "Siti Rahma (HR Lead)",
                "vusername": "hr.admin",
                "vemail": "siti.rahma@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+628111222333",
                "vposition": "Talent Acquisition Manager",
                "vdepartment": "Human Resources",
                "vrole": "HR",
                "vtimezone": "WIB",
                "vworking_hours": "09:00 - 17:00",
                "vstatus": "ACTIVE",
            },
            {
                "vuserid": "EMP-AUD-001",
                "vname": "Hendra Wijaya (System Admin)",
                "vusername": "auditor.it",
                "vemail": "hendra.wijaya@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+6281333334444",
                "vposition": "IT & AI Governance Administrator",
                "vdepartment": "Internal Audit",
                "vrole": "ADMIN",
                "vtimezone": "WIB",
                "vworking_hours": "09:00 - 17:00",
                "vstatus": "ACTIVE",
            },
        ]

        for u in admin_users:
            existing_user = (
                await session.execute(
                    select(User).where(User.vusername == u["vusername"])
                )
            ).scalars().first()

            if not existing_user:
                session.add(User(**u))
                print(f"  [OK] User {u['vname']} ({u['vusername']}) berhasil diinjeksi.")
            else:
                existing_user.vpassword_hash = default_password_hash
                existing_user.vname = u["vname"]
                existing_user.vrole = u["vrole"]
                existing_user.vposition = u["vposition"]
                existing_user.vdepartment = u["vdepartment"]
                existing_user.vstatus = "ACTIVE"
                print(f"  [OK] User {u['vname']} ({u['vusername']}) sudah ada, kredensial disinkronkan.")

        await session.flush()

        # 3. RBAC Permissions Matrix
        permissions_matrix = [
            ("HR", "GENERAL", "WRITE"),
            ("HR", "HR_ONLY", "WRITE"),
            ("HR", "SALARY", "READ"),
            ("HR", "SENSITIVE_FLAG", "READ"),
            ("HR", "AUDIT_LOG", "NONE"),
            ("ADMIN", "AUDIT_LOG", "READ"),
            ("ADMIN", "GENERAL", "WRITE"),
            ("ADMIN", "HR_ONLY", "WRITE"),
            ("ADMIN", "SALARY", "READ"),
            ("ADMIN", "SENSITIVE_FLAG", "READ"),
            ("INTERVIEWER", "GENERAL", "READ"),
            ("INTERVIEWER", "HR_ONLY", "NONE"),
            ("INTERVIEWER", "SALARY", "NONE"),
            ("INTERVIEWER", "SENSITIVE_FLAG", "NONE"),
            ("INTERVIEWER", "AUDIT_LOG", "NONE"),
        ]

        for role, vis_class, level in permissions_matrix:
            perm_exists = (
                await session.execute(
                    select(Permission).where(
                        Permission.vrole == role,
                        Permission.vvisibility_class == vis_class,
                    )
                )
            ).scalars().first()

            if not perm_exists:
                session.add(
                    Permission(
                        vrole=role,
                        vvisibility_class=vis_class,
                        vaccess_level=level,
                    )
                )
            else:
                perm_exists.vaccess_level = level

        print("  [OK] Matriks hak akses RBAC berhasil diselaraskan.")

        await session.commit()
        print("\n[SUCCESS] Akun admin berhasil diinjeksi ke database!")


def main() -> None:
    asyncio.run(inject_admin_users())


if __name__ == "__main__":
    main()
