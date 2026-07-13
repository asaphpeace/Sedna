"""Seed the database with the Sedna Academy sample data extracted from the standalone app."""
import asyncio
import random
import string
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models import *  # noqa: F401,F403 — registers all models with Base
from app.database import Base
from app.services.auth import hash_password


def rand_cred():
    return "SA-" + "".join(random.choices(string.digits, k=8))


ROLES_DATA = [
    # ── Customer paths ──
    {
        "name": "Voyage Operator",
        "description": "Master the day-to-day voyage execution workflow in Dataloy VMS — from fixture to final port call.",
        "icon": "ti-ship",
        "color": "purple",
        "audience": "customer",
        "products": ["vms"],
        "tiers": [
            {
                "label": "Foundation",
                "name": "Voyage Operator Foundation",
                "cert_name": "VMS Voyage Operator Foundation",
                "modules": [
                    {"title": "VMS overview: what it does and how it's structured", "type": "v", "dur": 10, "prod": "vms"},
                    {"title": "Navigating the VMS interface: menus, panels and shortcuts", "type": "v", "dur": 8, "prod": "vms"},
                    {"title": "Creating a voyage estimate from a fixture", "type": "v", "dur": 12, "prod": "vms"},
                    {"title": "Adding cargo, ports and freight rates to an estimate", "type": "v", "dur": 12, "prod": "vms"},
                    {"title": "Reading TCE and understanding the Lock TCE feature", "type": "a", "dur": 8, "prod": "vms"},
                    {"title": "Comparing two estimates side by side", "type": "v", "dur": 9, "prod": "vms"},
                ],
            },
            {
                "label": "Practitioner",
                "name": "Voyage Operator Practitioner",
                "cert_name": "VMS Voyage Operator Practitioner",
                "modules": [
                    {"title": "Opening a voyage from a fixture and setting up port calls", "type": "v", "dur": 14, "prod": "vms"},
                    {"title": "Bunker consumption calculation: how VMS calculates it", "type": "v", "dur": 14, "prod": "vms"},
                    {"title": "Laytime calculation and Statement of Facts entry", "type": "v", "dur": 16, "prod": "vms"},
                    {"title": "Port disbursement accounts: entry and reconciliation", "type": "a", "dur": 11, "prod": "vms"},
                    {"title": "Multi-port loading: allocating freight across load ports", "type": "v", "dur": 13, "prod": "vms"},
                    {"title": "Closing a voyage: checklist and final figures", "type": "a", "dur": 9, "prod": "vms"},
                ],
            },
            {
                "label": "Professional",
                "name": "Voyage Operator Professional",
                "cert_name": "VMS Voyage Operator Professional",
                "modules": [
                    {"title": "APS and TCE calculation deep dive", "type": "v", "dur": 18, "prod": "vms"},
                    {"title": "Voyage P&L analysis and adjustments", "type": "v", "dur": 15, "prod": "vms"},
                    {"title": "EU ETS and FuelEU cost configuration", "type": "a", "dur": 14, "prod": "vms"},
                    {"title": "Splitting voyages and handling partial fixtures", "type": "v", "dur": 12, "prod": "vms"},
                ],
            },
        ],
    },
    {
        "name": "Chartering Manager",
        "description": "Run fixture negotiations, track open positions and manage the chartering book in VMS.",
        "icon": "ti-briefcase",
        "color": "orange",
        "audience": "customer",
        "products": ["vms"],
        "tiers": [
            {
                "label": "Foundation",
                "name": "Chartering Manager Foundation",
                "cert_name": "VMS Chartering Foundation",
                "modules": [
                    {"title": "The chartering workflow in VMS end-to-end", "type": "v", "dur": 11, "prod": "vms"},
                    {"title": "Creating and managing fixtures", "type": "v", "dur": 13, "prod": "vms"},
                    {"title": "Open position list and vessel scheduling", "type": "v", "dur": 10, "prod": "vms"},
                    {"title": "APS calculation: ballast fuel costs", "type": "a", "dur": 9, "prod": "vms"},
                ],
            },
            {
                "label": "Practitioner",
                "name": "Chartering Manager Practitioner",
                "cert_name": "VMS Chartering Practitioner",
                "modules": [
                    {"title": "COA voyages and cargo scheduling", "type": "v", "dur": 14, "prod": "vms"},
                    {"title": "Freight market benchmarking in VMS", "type": "a", "dur": 10, "prod": "vms"},
                    {"title": "Laytime recalculation warning on invoiced voyages", "type": "v", "dur": 12, "prod": "vms"},
                ],
            },
        ],
    },
    {
        "name": "Finance Manager",
        "description": "Handle invoice lifecycle, freight billing, and financial reconciliation in VMS.",
        "icon": "ti-chart-bar",
        "color": "green",
        "audience": "customer",
        "products": ["vms"],
        "tiers": [
            {
                "label": "Foundation",
                "name": "Finance Manager Foundation",
                "cert_name": "VMS Finance Foundation",
                "modules": [
                    {"title": "Invoice lifecycle: assemble → post → reverse → credit note", "type": "v", "dur": 15, "prod": "vms"},
                    {"title": "Credit notes: bank account requirement", "type": "a", "dur": 7, "prod": "vms"},
                    {"title": "Freight invoice creation and PDF export", "type": "v", "dur": 12, "prod": "vms"},
                    {"title": "Demurrage and despatch invoicing", "type": "v", "dur": 13, "prod": "vms"},
                ],
            },
            {
                "label": "Practitioner",
                "name": "Finance Manager Practitioner",
                "cert_name": "VMS Finance Practitioner",
                "modules": [
                    {"title": "EU ETS and FuelEU cost configuration and calculation", "type": "a", "dur": 14, "prod": "vms"},
                    {"title": "Port cost accruals and variance reporting", "type": "v", "dur": 11, "prod": "vms"},
                    {"title": "Bunker hedging entries in VMS", "type": "a", "dur": 9, "prod": "vms"},
                ],
            },
        ],
    },
    {
        "name": "VMS Administrator",
        "description": "Configure and maintain Dataloy VMS — users, roles, vessel master data, and system settings.",
        "icon": "ti-settings",
        "color": "blue",
        "audience": "customer",
        "products": ["vms"],
        "tiers": [
            {
                "label": "Foundation",
                "name": "VMS Administration Foundation",
                "cert_name": "VMS Administration Foundation",
                "modules": [
                    {"title": "VMS security model: roles, permissions and data scope", "type": "v", "dur": 14, "prod": "vms"},
                    {"title": "User and role management", "type": "v", "dur": 11, "prod": "vms"},
                    {"title": "Vessel master data: setup and maintenance", "type": "v", "dur": 12, "prod": "vms"},
                    {"title": "Port and distance table management", "type": "a", "dur": 9, "prod": "vms"},
                ],
            },
            {
                "label": "Practitioner",
                "name": "VMS Administration Practitioner",
                "cert_name": "VMS Administration Practitioner",
                "modules": [
                    {"title": "Bunker price management and hedging configuration", "type": "v", "dur": 13, "prod": "vms"},
                    {"title": "System audit log: what's tracked and how to read it", "type": "a", "dur": 8, "prod": "vms"},
                    {"title": "Backup, restore and environment management", "type": "v", "dur": 10, "prod": "vms"},
                ],
            },
            {
                "label": "Professional",
                "name": "VMS Administration Professional",
                "cert_name": "VMS Administration Professional",
                "modules": [
                    {"title": "VMS security model deep dive for troubleshooting", "type": "v", "dur": 18, "prod": "vms"},
                    {"title": "Performance tuning and database maintenance", "type": "a", "dur": 12, "prod": "vms"},
                ],
            },
        ],
    },
    {
        "name": "IT Manager / Integration",
        "description": "Connect Dataloy VMS to third-party systems via the API — authentication, endpoints, and data flows.",
        "icon": "ti-plug",
        "color": "indigo",
        "audience": "customer",
        "products": ["vms"],
        "tiers": [
            {
                "label": "Foundation",
                "name": "VMS Integration Foundation",
                "cert_name": "VMS Integration Foundation",
                "modules": [
                    {"title": "API authentication: Basic Auth, OAuth2, M2M credentials", "type": "a", "dur": 12, "prod": "vms"},
                    {"title": "Core API endpoints: voyages, fixtures, vessels", "type": "v", "dur": 14, "prod": "vms"},
                    {"title": "Webhook configuration and event types", "type": "a", "dur": 10, "prod": "vms"},
                ],
            },
            {
                "label": "Practitioner",
                "name": "VMS Integration Practitioner",
                "cert_name": "VMS Integration Practitioner",
                "modules": [
                    {"title": "Reading the audit-log API for sync diagnostics", "type": "a", "dur": 11, "prod": "vms"},
                    {"title": "Error handling and retry patterns for VMS integrations", "type": "v", "dur": 13, "prod": "vms"},
                    {"title": "Sedna Stream + VMS: job tag sync and voyage email linking", "type": "v", "dur": 12, "prod": "stream"},
                ],
            },
        ],
    },
    # ── Internal paths ──
    {
        "name": "Support Engineer",
        "description": "Diagnose and resolve customer issues across VMS and Sedna Stream — from first response to escalation.",
        "icon": "ti-headset",
        "color": "purple",
        "audience": "internal",
        "products": ["vms", "stream", "cross"],
        "tiers": [
            {
                "label": "Foundation",
                "name": "Support Engineer Foundation",
                "cert_name": "Support Engineer Foundation",
                "modules": [
                    {"title": "Support workflow: ticket lifecycle and SLAs", "type": "a", "dur": 9, "prod": "cross"},
                    {"title": "VMS architecture overview for support", "type": "v", "dur": 14, "prod": "vms"},
                    {"title": "Sedna Stream architecture overview for support", "type": "v", "dur": 11, "prod": "stream"},
                    {"title": "Reading VMS logs: where to look first", "type": "a", "dur": 10, "prod": "vms"},
                ],
            },
            {
                "label": "Practitioner",
                "name": "Support Engineer Practitioner",
                "cert_name": "Support Engineer Practitioner",
                "modules": [
                    {"title": "Bunker discrepancy diagnostic playbook", "type": "a", "dur": 12, "prod": "vms"},
                    {"title": "Invoice posting failure: root cause tree", "type": "a", "dur": 11, "prod": "vms"},
                    {"title": "VMS security model deep dive for troubleshooting", "type": "v", "dur": 18, "prod": "vms"},
                    {"title": "Escalation paths: Engineering vs. DevOps vs. Product", "type": "a", "dur": 10, "prod": "cross"},
                    {"title": "API authentication: OAuth2, M2M — common failure modes", "type": "a", "dur": 12, "prod": "vms"},
                ],
            },
            {
                "label": "Professional",
                "name": "Support Engineer Professional",
                "cert_name": "Support Engineer Professional",
                "modules": [
                    {"title": "Deep-dive: Sedna Stream email delivery pipeline", "type": "v", "dur": 16, "prod": "stream"},
                    {"title": "Performance triage: slow voyage load and query profiling", "type": "a", "dur": 14, "prod": "vms"},
                ],
            },
        ],
    },
    {
        "name": "Communication Manager / Stream Admin",
        "description": "Set up and maintain Sedna Stream — shared mailboxes, teams, signatures, and mailing-list migration.",
        "icon": "ti-mail",
        "color": "teal",
        "audience": "internal",
        "products": ["stream"],
        "tiers": [
            {
                "label": "Foundation",
                "name": "Stream Foundation",
                "cert_name": "Sedna Stream Foundation",
                "modules": [
                    {"title": "Sedna Stream setup: shared mailboxes vs. personal email", "type": "v", "dur": 12, "prod": "stream"},
                    {"title": "Teams, members and permissions in Stream", "type": "v", "dur": 10, "prod": "stream"},
                    {"title": "Email signatures: org-level and personal", "type": "a", "dur": 8, "prod": "stream"},
                    {"title": "Job tag sync delay: what changed in the latest release", "type": "a", "dur": 6, "prod": "stream"},
                ],
            },
            {
                "label": "Practitioner",
                "name": "Stream Practitioner",
                "cert_name": "Sedna Stream Practitioner",
                "modules": [
                    {"title": "Forwarding address configuration: three-step guided flow", "type": "v", "dur": 11, "prod": "stream"},
                    {"title": "Mailing list migration: planning and execution", "type": "a", "dur": 13, "prod": "stream"},
                    {"title": "Stream + VMS: linking emails to voyage records", "type": "v", "dur": 12, "prod": "stream"},
                ],
            },
        ],
    },
]

RELEASES_DATA = [
    {
        "product": "vms", "tag": "VMS 8.26.3",
        "title": "Multi-port loading fix now live",
        "description": "Voyages with three or more load ports now allocate freight correctly. Update your voyage templates to pick up the change.",
        "published_at": datetime(2026, 6, 19, ), "module_count": 2,
    },
    {
        "product": "stream", "tag": "Sedna Stream",
        "title": "Job tag sync delay reduced from 90s to under 10s",
        "description": "Emails tagged to a Dataloy voyage now appear on the voyage record almost instantly, closing a long-standing operator pain point.",
        "published_at": datetime(2026, 6, 14, ), "module_count": 1,
    },
    {
        "product": "academy", "tag": "Academy",
        "title": "New path launched: Communication Manager / Stream Admin",
        "description": "A full Sedna Stream administration path covering shared mailboxes, teams, signatures, and mailing-list migration.",
        "published_at": datetime(2026, 6, 10, ), "module_count": 6,
    },
    {
        "product": "vms", "tag": "VMS 8.26.2",
        "title": "EU ETS calculation engine updated",
        "description": "FuelEU Maritime factors now sit alongside the revised EU ETS phase-in percentages for the 2026 compliance year.",
        "published_at": datetime(2026, 6, 2, ), "module_count": 1,
    },
    {
        "product": "academy", "tag": "Academy",
        "title": "12 troubleshooting articles added to the Support Engineer path",
        "description": "Diagnostic playbooks for bunker discrepancies, invoice posting failures, and reading the audit-log API.",
        "published_at": datetime(2026, 5, 28, ), "module_count": 12,
    },
    {
        "product": "stream", "tag": "Sedna Stream",
        "title": "Forwarding address configuration redesigned",
        "description": "Setting up forwarding addresses is now a guided three-step flow with validation at each step.",
        "published_at": datetime(2026, 5, 21, ), "module_count": 1,
    },
    {
        "product": "vms", "tag": "VMS 8.26.1",
        "title": "Laytime recalculation warning on invoiced voyages",
        "description": "VMS now warns before recalculating laytime on a voyage that has already been invoiced, preventing silent commission drift.",
        "published_at": datetime(2026, 5, 12, ), "module_count": 2,
    },
]


async def seed(db: AsyncSession):
    from sqlalchemy import text
    await db.execute(text("TRUNCATE organisations, users, learning_roles, tiers, modules, releases, notification_settings RESTART IDENTITY CASCADE"))

    # Organisation
    org = Organisation(name="Oceanic Shipping", slug="oceanic")
    db.add(org)
    await db.flush()

    # Admin user (you)
    admin = User(
        org_id=org.id, email="asaphpeace@gmail.com", name="Asaph Bell",
        initial="A", color="#6E2BF0", role="Support Engineer",
        status="active", is_admin=True,
        password_hash=hash_password("sedna123"),
    )
    db.add(admin)

    # Sample team
    team_data = [
        ("gisele.moreau@oceanic.co", "Gisele Moreau", "G", "#0E9E6E", "Super User"),
        ("fatima.z@oceanic.co", "Fatima Zahra", "F", "#B26A00", "Chartering Manager"),
        ("kim.n@oceanic.co", "Kim Nguyen", "K", "#6E2BF0", "Implementation Mgr"),
        ("d.santos@oceanic.co", "Diego Santos", "D", "#0B8FB0", "Voyage Operator"),
        ("priya.a@oceanic.co", "Priya Anand", "P", "#4338CA", "Finance Manager"),
        ("j.eriksson@oceanic.co", "Johan Eriksson", "J", "#0E9E6E", "IT Manager"),
    ]
    for email, name, initial, color, role in team_data:
        db.add(User(
            org_id=org.id, email=email, name=name, initial=initial,
            color=color, role=role, status="active",
            password_hash=hash_password("sedna123"),
        ))
    await db.flush()

    # Learning roles + tiers + modules
    for sort, rd in enumerate(ROLES_DATA):
        role = LearningRole(
            name=rd["name"], description=rd["description"],
            icon=rd["icon"], color=rd["color"],
            audience=rd["audience"], products=rd["products"],
            sort_order=sort,
        )
        db.add(role)
        await db.flush()
        for t_sort, td in enumerate(rd["tiers"]):
            tier = Tier(
                role_id=role.id, label=td["label"],
                name=td["name"], cert_name=td["cert_name"],
                sort_order=t_sort,
            )
            db.add(tier)
            await db.flush()
            for m_sort, md in enumerate(td["modules"]):
                db.add(Module(
                    tier_id=tier.id, title=md["title"],
                    module_type=md["type"], duration_mins=md["dur"],
                    product=md["prod"], sort_order=m_sort,
                ))

    # Releases
    for rd in RELEASES_DATA:
        db.add(Release(**rd))

    # Notification settings for admin
    db.add(NotificationSettings(
        user_id=admin.id,
        weekly_digest=True, new_modules=True, cert_reminders=True,
        product_releases=True, team_activity=False, marketing_emails=False,
    ))

    # Badges
    badges_data = [
        {"slug": "first_module", "name": "First Step", "description": "Complete your first module", "icon": "ti-player-play", "color": "#fff", "bg_color": "#6E2BF0"},
        {"slug": "ten_modules", "name": "On a Roll", "description": "Complete 10 modules", "icon": "ti-flame", "color": "#fff", "bg_color": "#B26A00"},
        {"slug": "fifty_modules", "name": "Knowledge Seeker", "description": "Complete 50 modules", "icon": "ti-star", "color": "#fff", "bg_color": "#0E9E6E"},
        {"slug": "streak_7", "name": "Week Warrior", "description": "Maintain a 7-day learning streak", "icon": "ti-bolt", "color": "#fff", "bg_color": "#F59E0B"},
        {"slug": "streak_30", "name": "Unstoppable", "description": "Maintain a 30-day learning streak", "icon": "ti-crown", "color": "#fff", "bg_color": "#EF4444"},
        {"slug": "first_cert", "name": "Certified", "description": "Earn your first certificate", "icon": "ti-certificate", "color": "#fff", "bg_color": "#0B8FB0"},
        {"slug": "five_certs", "name": "Master Learner", "description": "Earn 5 certificates", "icon": "ti-award", "color": "#fff", "bg_color": "#4338CA"},
        {"slug": "explorer", "name": "Explorer", "description": "Complete modules from 3 different learning paths", "icon": "ti-compass", "color": "#fff", "bg_color": "#10B981"},
    ]
    for bd in badges_data:
        db.add(Badge(**bd))

    await db.flush()

    # Quiz questions for the first module of Voyage Operator Foundation
    from sqlalchemy import select as sa_select
    first_module_result = await db.execute(sa_select(Module).order_by(Module.id).limit(1))
    first_module = first_module_result.scalar_one_or_none()

    if first_module:
        q1 = QuizQuestion(
            module_id=first_module.id,
            question_text="What is the primary purpose of a Voyage Management System (VMS)?",
            explanation="A VMS centralises voyage planning, execution, and financial settlement in one platform.",
            sort_order=0,
        )
        db.add(q1)
        await db.flush()
        db.add(QuizOption(question_id=q1.id, text="To manage crew HR records", is_correct=False, sort_order=0))
        db.add(QuizOption(question_id=q1.id, text="To plan, execute and settle voyages end-to-end", is_correct=True, sort_order=1))
        db.add(QuizOption(question_id=q1.id, text="To track container weights at port", is_correct=False, sort_order=2))
        db.add(QuizOption(question_id=q1.id, text="To file regulatory customs paperwork", is_correct=False, sort_order=3))

        q2 = QuizQuestion(
            module_id=first_module.id,
            question_text="Which of the following best describes a 'fixture' in shipping?",
            explanation="A fixture is the confirmed contract between a shipowner and charterer specifying the voyage terms.",
            sort_order=1,
        )
        db.add(q2)
        await db.flush()
        db.add(QuizOption(question_id=q2.id, text="A technical fault logged by the engineer", is_correct=False, sort_order=0))
        db.add(QuizOption(question_id=q2.id, text="A confirmed charter contract between owner and charterer", is_correct=True, sort_order=1))
        db.add(QuizOption(question_id=q2.id, text="A port authority berthing document", is_correct=False, sort_order=2))
        db.add(QuizOption(question_id=q2.id, text="An insurance policy for the cargo", is_correct=False, sort_order=3))

        q3 = QuizQuestion(
            module_id=first_module.id,
            question_text="TCE stands for:",
            explanation="Time Charter Equivalent is the daily earnings metric used to compare voyages across different charter types.",
            sort_order=2,
        )
        db.add(q3)
        await db.flush()
        db.add(QuizOption(question_id=q3.id, text="Total Cargo Estimate", is_correct=False, sort_order=0))
        db.add(QuizOption(question_id=q3.id, text="Terminal Cost Entry", is_correct=False, sort_order=1))
        db.add(QuizOption(question_id=q3.id, text="Time Charter Equivalent", is_correct=True, sort_order=2))
        db.add(QuizOption(question_id=q3.id, text="Tonnage Correction Exponent", is_correct=False, sort_order=3))

    await db.commit()
    print("✓ Database seeded")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
