"""
Loads the "Veson University" curriculum (115 courses across 10 roles) as
learning-path structure only: paths, tiers, and module titles/descriptions.
No lesson content (video/article body) is attached — every module is created
with is_placeholder=True so it shows up in the catalog and admin Content
panel for authoring, but does NOT count toward certificate completion or
analytics until an admin fills in real content and un-flags it.

Idempotent — safe to re-run. Skips any role whose name already exists.

Run once after deploying:
    docker compose -f docker-compose.prod.yml exec backend python -m app.seed_veson_catalog
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import *  # noqa: F401,F403 — registers all models with Base
from app.models.content import LearningRole, Module, Tier

TIER_LABELS = {1: "Foundation", 2: "Core", 3: "Advanced"}

# (code, title, description, tier_number)
CoursesByRole: dict[str, list[tuple[str, str, str, int]]] = {
    "Foundations": [
        ("F01", "The shipping industry in short", "How it works and how money is made", 1),
        ("F02", "The four vessel segments", "Dry bulk, tanker, breakbulk, gas", 1),
        ("F03", "The parties in a shipping deal", "Owners, charterers, brokers, agents, P&I", 1),
        ("F04", "Charter types", "Voyage charter, time charter, COA", 1),
        ("F05", "How a voyage makes money", "Freight, hire, bunkers, port costs, TCE", 1),
        ("F06", "Laytime and demurrage", "The most important financial concept", 1),
        ("F07", "Bunker fuel", "Types, consumption, speed relationship", 1),
        ("F08", "Port calls", "NOR, SOF, and what goes wrong", 1),
        ("F09", "EU ETS and FuelEU", "The two regulations and how they differ", 1),
        ("F10", "Worldscale for tankers", "How tanker freight rates work", 1),
        ("F11", "Vessels and cargo in depth", "Dimensions, compatibility, port facilities", 1),
        ("F12", "Sedna VMS — what it is and how it connects", "Module orientation for new users", 1),
        ("F13", "Shipping glossary", "40 terms every team member must know", 1),
    ],
    "Chartering manager": [
        ("CM01", "The chartering module", "Navigation, views, and the voyages list", 2),
        ("CM02", "TC-in contracts — creating and configuring", "Fields, duration, rates, commissions", 2),
        ("CM03", "Building a voyage estimate", "Inputs, structure, full screen view", 2),
        ("CM04", "Reading a voyage estimate", "TCE, sensitivity analysis, break-even workaround", 2),
        ("CM05", "Port costs, routing, and canal transits", "Mandatory fields, routing points, pilot distances", 2),
        ("CM06", "Comparing estimates and templates", "Side-by-side comparison, template workflow", 2),
        ("CM07", "Cargo management", "Spot cargoes, cargo status, the cargo list", 2),
        ("CM08", "Nominating a voyage", "Validation errors, warnings, handover to ops", 2),
        ("CM09", "COA contracts — full workflow", "Scheduled voyages, cascade limitation", 2),
        ("CM10", "Multiple cargoes and parceling", "Port rotation, per-port quantity, performance cargo", 2),
        ("CM11", "TC-out voyages", "Economics, bunker P&L, revalue checkbox", 3),
        ("CM12", "Index-based rates and time automation", "Baltic index, forward curve, payment cycle", 3),
    ],
    "Operator": [
        ("OP01", "Operations module — orientation", "Voyage statuses, the operator's view", 2),
        ("OP02", "The Nominated → Operational handover", "Responsible operator, field review", 2),
        ("OP03", "Port call management", "Arrival, NOR, cargo events, departure", 2),
        ("OP04", "The agent and service order distinction", "Why both are required; DA desk connection", 2),
        ("OP05", "Bunker tracking — ROB, orders, deliveries", "FIFO valuation, grade tracking", 2),
        ("OP06", "Off-hire recording", "Downtime tab, start/end, hire deduction", 2),
        ("OP07", "B/L quantity — triggering the freight receivable", "The critical handoff from ops to finance", 2),
        ("OP08", "Reading the voyage P&L", "Estimate vs actual, all figures positive", 2),
        ("OP09", "Operations worked example", "One voyage port to port — complete walkthrough", 2),
        ("OP10", "EU ETS in operations", "Emissions per voyage leg tracking", 3),
        ("OP11", "Tasks and alerts configuration", "Automated reminders, deadline notifications", 3),
    ],
    "Laytime desk": [
        ("LT01", "The laytime module — overview", "Connection to voyage P&L, status lifecycle", 2),
        ("LT02", "SOF entry — logging port events", "Arrival, NOR, cargo ops, stoppages, departure", 2),
        ("LT03", "Laytime calculation — allowed time", "Tons/day, fixed days, reversible vs non-reversible", 2),
        ("LT04", "Deductions — time not to count", "SHINC/SHEX, Reasons for Stoppage config", 2),
        ("LT05", "Demurrage and despatch", "Calculated vs fixed, Settled status, invoicing", 2),
        ("LT06", "The 90-day claim deadline", "The single most commercially important deadline", 2),
        ("LT07", "Laytime worked example", "Dry bulk, SHINC, one load and discharge port", 2),
        ("LT08", "SHINC/SHEX/WWDSHEX edge cases", "Configuration and calculation impact", 3),
        ("LT09", "Reversible vs non-reversible — config", "System behaviour and claim implications", 3),
        ("LT10", "Proration across charterers", "Splitting time used by cargo quantity", 3),
        ("LT11", "Tiered demurrage rates", "Rate changes after threshold", 3),
    ],
    "Marine accountant": [
        ("MA01", "Finance in Sedna VMS — orientation", "Two user types, where VMS stops", 2),
        ("MA02", "The invoice workflow — four stages", "Pending, Assembled, Ready, Posted", 2),
        ("MA03", "General assembly procedure", "Step-by-step from pending to posted", 2),
        ("MA04", "Freight receivables", "BL quantity trigger, prepaid percentages", 2),
        ("MA05", "Laytime and demurrage invoicing", "From Settled status to invoice", 2),
        ("MA06", "Hire payable — the TC-in payment cycle", "15-day default, off-hire deductions, step rates", 2),
        ("MA07", "Port cost payables — DA desk to FDA", "PDA vs FDA, item category and GL risk", 2),
        ("MA08", "Bunker payables", "Delivered status trigger, quantity lock after posting", 2),
        ("MA09", "Commission handling", "Credit vs non-credit charter, Base Freight Only", 2),
        ("MA10", "Reversals — when to reverse and when not to", "The critical distinction; delta invoicing instead", 2),
        ("MA11", "Statements of account", "Running ledger, including unposted items", 2),
        ("MA12", "Finance worked example", "Freight + hire + demurrage across one voyage", 2),
        ("MA13", "Dead freight and overage", "Tolerance setting, separate pending lines", 3),
        ("MA14", "EU ETS invoicing to charterers", "Manual various revenue workaround", 3),
        ("MA15", "TC incremental invoicing", "Adjustments, corrections, period reconciliation", 3),
    ],
    "Business control": [
        ("BC01", "Period-close work — what Business Control owns", "The two finance user types in practice", 2),
        ("BC02", "What accruals are and why they matter", "The shipping-specific timing problem", 2),
        ("BC03", "Time correction", "What it is, when to run it, why order matters", 2),
        ("BC04", "Generating accruals", "Calculation, snapshot, integration dependency", 2),
        ("BC05", "The three accrual scenarios", "PDA timing, bunker delivery, IFRS %", 2),
        ("BC06", "Bunker transactions — the consumption posting", "Separate from supply invoice; post at voyage close", 2),
        ("BC07", "Month-end close — the full sequence", "Correct order of operations, every step", 2),
        ("BC08", "Common accruals mistakes", "Five errors and how to prevent them", 2),
        ("BC09", "Reporting for Business Control", "Accrual, AP/AR, voyage result domains", 2),
        ("BC10", "IFRS percentage-of-completion", "When to use it, how it differs from days-based", 3),
        ("BC11", "Bunker stock accruals", "When ROB exceeds invoiced quantity", 3),
        ("BC12", "Explaining month-end close to a CFO", "The conversation a CS needs to be ready for", 3),
    ],
    "System administrator": [
        ("SA01", "What is master data", "The reference library and why accuracy matters", 2),
        ("SA02", "The configuration sequence", "Right order, dependencies, and why it matters", 2),
        ("SA03", "Companies and business units", "Profit centres, high-risk to change post go-live", 2),
        ("SA04", "Vessel Type and Vessels", "Mandatory prerequisite, speed/consumption config", 2),
        ("SA05", "Business Partners", "Types, financial tab, finance partner code gotcha", 2),
        ("SA06", "Financial master data", "Accounts, Banks, Payment Terms, Baseline Terms", 2),
        ("SA07", "GL mapping and service items", "What maps to what; the change risk", 2),
        ("SA08", "Laytime event types and stoppage reasons", "Must configure before laytime module used", 2),
        ("SA09", "User roles and permissions", "Security groups, predefined roles, access control", 2),
        ("SA10", "Pre-loaded data — what Sedna manages", "Ports, distances, laytime terms, GHG limits", 2),
        ("SA11", "Reporting in Sedna VMS — the BI module", "Domains, ad hoc views, scheduled reports", 2),
        ("SA12", "Data migration strategy", "API vs manual, quality checks, common risks", 3),
        ("SA13", "Various Cost and Revenue items", "Calculation rules, GL mapping, use cases", 3),
        ("SA14", "API and integration overview", "What the open API can do; common patterns", 3),
    ],
    "Solution consultant": [
        ("SC01", "Sedna VMS — the two-minute pitch", "For any audience, any entry point", 2),
        ("SC02", "Module-by-module orientation", "What each module does and how they connect", 2),
        ("SC03", "Discovery question bank", "What to ask before any demo", 2),
        ("SC04", "Persona value maps", "What each buyer cares about; how VMS answers", 2),
        ("SC05", "Demo script — Informed Product Overview", "Nordvik scenario, multi pain point flow", 2),
        ("SC06", "Demo script — Tailored Voyage Walkthrough", "Meridian scenario, finance persona anchor", 2),
        ("SC07", "Objection handling guide", "10 most common pushbacks with responses", 2),
        ("SC08", "Sedna VMS editions", "Bulk, Breakbulk, Broker, TC, Estimate, Scheduler", 2),
        ("SC09", "Competitive positioning", "How Sedna VMS compares to alternatives", 2),
        ("SC10", "Laytime demo — opening with the pain", "The 90-day deadline as the demo hook", 3),
        ("SC11", "Finance persona anchor", "Hire reconciliation spreadsheet vs VMS story", 3),
        ("SC12", "SC onboarding checklist", "What to learn and do in your first 30 days", 2),
    ],
    "Implementation": [
        ("IM01", "Implementation overview", "Phases, timeline, what success looks like", 2),
        ("IM02", "Discovery and scoping workbook", "Questions to ask before configuration begins", 2),
        ("IM03", "Configuration sequence walkthrough", "Full guided tour with gotchas at each step", 2),
        ("IM04", "Go-live checklist by module", "Sign-off criteria before each module goes live", 2),
        ("IM05", "Common implementation failure modes", "Data quality, scope creep, adoption, integration", 2),
        ("IM06", "Hypercare — first 30 days post go-live", "What to monitor, early issues, user confidence", 2),
        ("IM07", "Finance superuser training delivery", "Guide for leading Business Control sessions", 2),
        ("IM08", "Operator training delivery", "Guide for leading Operator onboarding sessions", 2),
        ("IM09", "SAP integration guide", "Architecture, field mapping, error handling", 2),
        ("IM10", "Data migration deep-dive", "Strategy, format requirements, quality checks", 3),
    ],
    "Customer success": [
        ("CS01", "CS onboarding checklist", "What to learn and do in your first 30 days", 2),
        ("CS02", "Customer health indicators", "Healthy adoption vs at-risk patterns by module", 2),
        ("CS03", "Escalation guide", "CS vs Implementation vs Product — clear lines", 2),
        ("CS04", "Module adoption conversations", "What good usage looks like, module by module", 2),
        ("CS05", "Explaining accruals to a finance contact", "The conversation CS needs to be ready for", 2),
    ],
}

ROLE_META = {
    "Foundations": {
        "description": "Core shipping industry concepts every Sedna VMS user should know before specializing.",
        "icon": "ti-anchor", "color": "purple", "audience": "customer",
    },
    "Chartering manager": {
        "description": "Run fixture negotiations, build voyage estimates, and manage the chartering book in Sedna VMS.",
        "icon": "ti-briefcase", "color": "purple", "audience": "customer",
    },
    "Operator": {
        "description": "Run day-to-day voyage execution — port calls, bunkers, off-hire — from nomination to close.",
        "icon": "ti-ship", "color": "purple", "audience": "customer",
    },
    "Laytime desk": {
        "description": "Calculate laytime and demurrage, manage claim deadlines, and handle SOF entry end to end.",
        "icon": "ti-hourglass", "color": "purple", "audience": "customer",
    },
    "Marine accountant": {
        "description": "Handle the full invoice lifecycle — freight, hire, demurrage, bunkers, and commissions.",
        "icon": "ti-calculator", "color": "purple", "audience": "customer",
    },
    "Business control": {
        "description": "Own the month-end close — accruals, time correction, and reporting for the finance domain.",
        "icon": "ti-report-money", "color": "purple", "audience": "customer",
    },
    "System administrator": {
        "description": "Configure and maintain Sedna VMS — master data, security roles, GL mapping, and integrations.",
        "icon": "ti-settings", "color": "purple", "audience": "customer",
    },
    "Solution consultant": {
        "description": "Pitch, demo, and position Sedna VMS — personas, objection handling, and competitive context.",
        "icon": "ti-presentation", "color": "purple", "audience": "internal",
    },
    "Implementation": {
        "description": "Deliver customer go-lives — discovery, configuration, training delivery, and hypercare.",
        "icon": "ti-rocket", "color": "purple", "audience": "internal",
    },
    "Customer success": {
        "description": "Drive adoption post go-live — health indicators, escalation paths, and renewal conversations.",
        "icon": "ti-heart-handshake", "color": "purple", "audience": "internal",
    },
}


def _cert_name(role_name: str, tier_num: int) -> str:
    label = TIER_LABELS[tier_num]
    if role_name == "Foundations":
        return "VMS Foundations"
    return f"VMS {role_name} {label}"


async def load_catalog(db: AsyncSession) -> None:
    for sort, (role_name, courses) in enumerate(CoursesByRole.items()):
        existing = await db.execute(select(LearningRole).where(LearningRole.name == role_name))
        if existing.scalar_one_or_none():
            print(f"Skipping '{role_name}' — already exists.")
            continue

        meta = ROLE_META[role_name]
        role = LearningRole(
            name=role_name, description=meta["description"],
            icon=meta["icon"], color=meta["color"],
            audience=meta["audience"], products=["vms"],
            sort_order=sort,
        )
        db.add(role)
        await db.flush()

        # Group this role's courses by tier number, preserving catalog order.
        tier_numbers = sorted({c[3] for c in courses})
        for t_sort, tier_num in enumerate(tier_numbers):
            label = TIER_LABELS[tier_num]
            tier = Tier(
                role_id=role.id, label=label,
                name=role_name if role_name == "Foundations" else f"{role_name} {label}",
                cert_name=_cert_name(role_name, tier_num),
                sort_order=t_sort,
            )
            db.add(tier)
            await db.flush()

            tier_courses = [c for c in courses if c[3] == tier_num]
            for m_sort, (code, title, description, _) in enumerate(tier_courses):
                db.add(Module(
                    tier_id=tier.id,
                    title=f"{code} · {title}",
                    module_type="a",
                    duration_mins=0,
                    product="vms",
                    is_placeholder=True,
                    sort_order=m_sort,
                    description=description,
                ))

        print(f"Loaded '{role_name}' — {len(courses)} courses across {len(tier_numbers)} tier(s).")

    await db.commit()


async def main():
    async with AsyncSessionLocal() as db:
        await load_catalog(db)


if __name__ == "__main__":
    asyncio.run(main())
