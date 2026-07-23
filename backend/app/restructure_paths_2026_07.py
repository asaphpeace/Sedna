"""
One-time data restructuring (July 2026):

1. Split "Support Engineer" (role id 6 — mixed VMS/Stream/cross content)
   into two single-product paths: "VMS Support Engineer" and "Sedna
   Support Engineer". Existing UserModuleProgress rows carry over
   untouched since module ids never change, only which tier/role they
   belong to.

2. Merge the two "Chartering Manager" paths (role id 2, real authored
   content; role id 9, placeholder Veson-catalog content) into one path,
   keeping the real content's tiers ahead of the placeholder ones:
   Foundation -> Practitioner -> Core -> Advanced.

Both operations were confirmed safe before writing this script: zero
certificates exist against any of the affected tiers, and only two
UserModuleProgress rows exist against the Support Engineer modules (both
of which resolve correctly through the new tiers automatically, since
progress is keyed on module_id, never on tier_id/role_id).

Idempotent — safe to re-run. Skips each half of the work if it looks
already applied (checked by role name existence).

Run once after deploying:
    docker compose -f docker-compose.prod.yml exec backend python -m app.restructure_paths_2026_07
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import *  # noqa: F401,F403 — registers all models with Base
from app.models.content import LearningRole, Module, Tier


async def _get_role_by_name(db: AsyncSession, name: str) -> LearningRole | None:
    result = await db.execute(select(LearningRole).where(LearningRole.name == name))
    return result.scalar_one_or_none()


async def split_support_engineer(db: AsyncSession) -> None:
    old_role = await _get_role_by_name(db, "Support Engineer")
    if not old_role:
        print("Support Engineer already split (or never existed) — skipping.")
        return

    vms_role = LearningRole(
        name="VMS Support Engineer",
        description="Diagnose and resolve customer issues in Dataloy VMS — from first response to escalation.",
        icon="ti-headset", color="purple", audience="internal", products=["vms"], sort_order=old_role.sort_order,
    )
    stream_role = LearningRole(
        name="Sedna Support Engineer",
        description="Diagnose and resolve customer issues in Sedna Stream — from first response to escalation.",
        icon="ti-headset", color="purple", audience="internal", products=["stream"], sort_order=old_role.sort_order + 1,
    )
    db.add_all([vms_role, stream_role])
    await db.flush()

    vms_tiers = {
        "Foundation": Tier(role_id=vms_role.id, label="Foundation", name="VMS Support Engineer Foundation",
                            cert_name="VMS Support Engineer Foundation", sort_order=0),
        "Practitioner": Tier(role_id=vms_role.id, label="Practitioner", name="VMS Support Engineer Practitioner",
                              cert_name="VMS Support Engineer Practitioner", sort_order=1),
        "Professional": Tier(role_id=vms_role.id, label="Professional", name="VMS Support Engineer Professional",
                              cert_name="VMS Support Engineer Professional", sort_order=2),
    }
    stream_tier = Tier(role_id=stream_role.id, label="Foundation", name="Sedna Support Engineer Foundation",
                        cert_name="Sedna Support Engineer Foundation", sort_order=0)
    db.add_all([*vms_tiers.values(), stream_tier])
    await db.flush()

    # module title (unique enough to match reliably) -> new tier + optional product fix
    module_moves = {
        "Support workflow: ticket lifecycle and SLAs": (vms_tiers["Foundation"], "vms"),
        "VMS architecture overview for support": (vms_tiers["Foundation"], None),
        "Reading VMS logs: where to look first": (vms_tiers["Foundation"], None),
        "Bunker discrepancy diagnostic playbook": (vms_tiers["Practitioner"], None),
        "Invoice posting failure: root cause tree": (vms_tiers["Practitioner"], None),
        "VMS security model deep dive for troubleshooting": (vms_tiers["Practitioner"], None),
        "Escalation paths: Engineering vs. DevOps vs. Product": (vms_tiers["Practitioner"], "vms"),
        "API authentication: OAuth2, M2M — common failure modes": (vms_tiers["Practitioner"], None),
        "Performance triage: slow voyage load and query profiling": (vms_tiers["Professional"], None),
        "Sedna Stream architecture overview for support": (stream_tier, None),
        "Deep-dive: Sedna Stream email delivery pipeline": (stream_tier, None),
    }

    old_modules_result = await db.execute(select(Module).where(Module.tier_id.in_([t.id for t in await _old_tiers(db, old_role.id)])))
    old_modules = old_modules_result.scalars().all()
    moved_titles = set()
    for mod in old_modules:
        move = module_moves.get(mod.title)
        if not move:
            print(f"  WARNING: no mapping for module '{mod.title}' (id={mod.id}) — leaving in place.")
            continue
        new_tier, new_product = move
        mod.tier_id = new_tier.id
        if new_product:
            mod.product = new_product
        moved_titles.add(mod.title)

    await db.flush()

    # Old tiers should now be empty; delete them, then the old role.
    for old_tier in await _old_tiers(db, old_role.id):
        await db.delete(old_tier)
    await db.delete(old_role)
    await db.commit()
    print(f"Split Support Engineer -> VMS Support Engineer ({len(vms_tiers)} tiers) + "
          f"Sedna Support Engineer (1 tier). Moved {len(moved_titles)}/{len(old_modules)} modules.")


async def _old_tiers(db: AsyncSession, role_id: int) -> list[Tier]:
    result = await db.execute(select(Tier).where(Tier.role_id == role_id))
    return list(result.scalars().all())


async def merge_chartering_manager(db: AsyncSession) -> None:
    old_role = await _get_role_by_name(db, "Chartering Manager")
    veson_role = await _get_role_by_name(db, "Chartering manager")
    if not old_role or not veson_role:
        print("Chartering Manager already merged (or one side missing) — skipping.")
        return

    veson_role.name = "Chartering Manager"

    old_tiers = await _old_tiers(db, old_role.id)
    veson_tiers = await _old_tiers(db, veson_role.id)

    # Renumber: real-content tiers first (Foundation, Practitioner), then
    # the placeholder Veson tiers (Core, Advanced).
    for i, tier in enumerate(sorted(old_tiers, key=lambda t: t.sort_order)):
        tier.role_id = veson_role.id
        tier.sort_order = i
    offset = len(old_tiers)
    for i, tier in enumerate(sorted(veson_tiers, key=lambda t: t.sort_order)):
        tier.sort_order = offset + i
        tier.name = tier.name.replace("Chartering manager", "Chartering Manager")
        tier.cert_name = tier.cert_name.replace("Chartering manager", "Chartering Manager")

    await db.flush()
    await db.delete(old_role)  # now has zero tiers
    await db.commit()
    print(f"Merged Chartering Manager: {len(old_tiers)} real-content tiers + "
          f"{len(veson_tiers)} placeholder tiers under one path.")


async def main():
    async with AsyncSessionLocal() as db:
        await split_support_engineer(db)
        await merge_chartering_manager(db)


if __name__ == "__main__":
    asyncio.run(main())
