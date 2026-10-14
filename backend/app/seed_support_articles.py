"""Seed sample Knowledge Base and Help Center articles for Sedna VMS.

Drafted in Oct 2026 from the support insight pack: the most frequent VMS
support themes, what support has actually explained to customers in Jira
cases, and the public product documentation (docs.dataloy.com). Every article
is published as a *sample* (is_sample=True) so readers see it is under review
until Education or Support has checked it.

Purely additive: articles that already exist (by slug) are left alone, so
edits made in the app are never overwritten. Safe to re-run.

    docker compose exec backend python -m app.seed_support_articles
"""
import asyncio
from textwrap import dedent

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import *  # noqa: F401,F403 — registers all models with Base
from app.models.content import Article, LearningRole

VMS_PORTAL = "https://dataloy-cloud.atlassian.net/servicedesk/customer/portal/5"


def md(text: str) -> str:
    return dedent(text).strip()


ARTICLES = [
    # ── Help Center: troubleshooting and support processes ──
    {
        "slug": "still-pending-after-invoicing",
        "title": "Freight or costs still show as pending after invoicing",
        "summary": "You've invoiced a voyage, but items still appear under Pending Receivable or Pending Payable.",
        "section": "help-center", "kind": "Troubleshooting", "topic": "Invoicing", "sort_order": 1,
        "body": md("""
            Pending lists show document lines that haven't been assembled into an invoice yet. **Pending Receivable** holds money owed to you (freight and other receivables), **Pending Payable** holds costs you owe (except hire), and **Pending Hire Payable** holds time charter hire. When something stays pending after you've invoiced, it's usually one of the reasons below.

            ## Check these first

            1. **Only some lines were assembled.** Assembling picks the lines you select. Lines left out, such as a balance freight or a commission, stay pending until they're assembled too. Try viewing the pending list grouped by voyage, by vessel or by business partner to see what's left.
            2. **Something changed after the invoice.** If the quantity, freight rate, bunkers or laytime changed after you assembled the invoice, the difference can appear as a new pending line rather than altering the posted invoice.
            3. **The invoice was reversed.** Reversing an invoice turns it into a credit note and the lines it covered can become pending again.
            4. **Commissions are separate.** Address commission is deducted on the freight invoice, but broker commission is payable to the broker, so it appears under Pending Payable on its own.
            5. **The voyage status doesn't allow invoicing.** Invoices can only be assembled for voyages that aren't closed and are at status Nominated or higher.

            > [!TIP]
            > Compare the pending line's amount with the invoice it should belong to. A small amount usually means a change after invoicing; the full amount usually means the line was never assembled.

            ## Before you log a case

            Log a case with the voyage number, the invoice number, a screenshot of the pending line and the amount you expected.
        """),
    },
    {
        "slug": "negative-rob",
        "title": "Why ROB goes negative, and how to correct it",
        "summary": "A voyage shows negative remaining-on-board (ROB) bunkers, or ROB at the end of one voyage doesn't match the start of the next.",
        "section": "help-center", "kind": "Troubleshooting", "topic": "Bunkers", "sort_order": 2,
        "related": "Shipping from Scratch",
        "body": md("""
            ROB is worked out from the opening balance, what was bunkered and what was consumed. A negative ROB means the system has used more fuel than it believes was on board, so one of those three figures is out of line.

            ## Common causes

            - **Opening balances don't match.** The ROB at the start of a voyage should equal the ROB at the end of the previous one. A mismatch here carries into every later figure.
            - **Bunkering is recorded later than the consumption that used it**, or at a different port call, so for a stretch of the voyage the stock runs below zero.
            - **Stock is price-driven.** Bunker stock is held in price layers, so the order in which fuel is received and consumed matters. Debunkering at a price different from the stock can't be matched automatically.

            ## How to correct it

            1. Check the end ROB of the previous voyage against the start ROB of this one, grade by grade.
            2. Check bunkering quantities and their port calls are on the right dates.
            3. Where needed, fix the start date of the next voyage and align its opening balances by hand. Once stocks are aligned and negative balances are no longer passed on, the figures correct themselves.

            > [!NOTE]
            > Small differences can come from decimals. Values are stored with more decimals than the screen shows, so a figure that looks identical can still differ slightly.

            ## Before you log a case

            Log a case with the vessel, both voyage numbers, the fuel grade and screenshots of the ROB at the end and start.
        """),
    },
    {
        "slug": "report-an-issue",
        "title": "How to report an issue so it's fixed fast",
        "summary": "You're about to log a support case and want it resolved without a round of follow-up questions.",
        "section": "help-center", "kind": "Process", "topic": "Getting help", "sort_order": 3,
        "body": md(f"""
            The quickest cases are the ones support can reproduce straight away. A title like "Dataloy problem" or "URGENT" means the first reply has to ask what happened, which adds a day.

            ## Include these in every case

            1. **A specific title**: what and where, for example "Freight still pending after invoicing, voyage 2604".
            2. **The record**: voyage number, vessel, invoice or contract number.
            3. **The environment**: live or test, and the version if you know it.
            4. **What you did and what happened**: the steps, and the error message word for word.
            5. **What you expected instead.**
            6. **A screenshot** of the whole screen, including any error.
            7. **Who is affected**: one user, a team, or everyone.

            ## How urgent is it?

            Say so in the case, not only in the title: is work stopped, is there a deadline such as month-end, or is there a workaround?

            [Log a VMS support case]({VMS_PORTAL})
        """),
    },
    {
        "slug": "vms-feels-slow",
        "title": "VMS feels slow: what to check and what to tell us",
        "summary": "Screens take a long time to open or save, or VMS isn't responding.",
        "section": "help-center", "kind": "Troubleshooting", "topic": "Performance", "sort_order": 4,
        "body": md(f"""
            Slowness has very different causes depending on who it affects, so the first job is to find out how widespread it is.

            ## Check first

            1. **Is it just you?** Ask a colleague to open the same screen. If only you are affected, try another browser, clear the cache, or close other heavy tabs.
            2. **Is it one screen or everything?** A single slow screen, such as one voyage or one report, usually points to that record or report. Everything slow points to the system.
            3. **Is it test or live?** Test environments are often smaller and slower by design.

            ## When you log a case, tell us

            - Live or test, and roughly when it started
            - Which screens, and how long they take (for example, "opening a voyage takes 40 seconds")
            - How many users are affected
            - Whether it's constant or comes and goes

            If everyone is affected and work has stopped, say so clearly in the case so it's treated as urgent.

            [Log a VMS support case]({VMS_PORTAL})
        """),
    },
    {
        "slug": "request-port-terminal-berth",
        "title": "Request a new port, terminal, berth or UN/LOCODE",
        "summary": "A port, terminal or berth you need is missing from VMS, or its UN/LOCODE is wrong.",
        "section": "help-center", "kind": "Process", "topic": "Master data", "sort_order": 5,
        "body": md(f"""
            Ports, terminals and berths are master data. When one is missing, send a request with everything below in one go; requests without these details need a follow-up before they can be added.

            ## What to include

            - **Port name** and **country**
            - **UN/LOCODE** if the port has one (five characters, for example NOOSL)
            - For a terminal or berth: the **port it belongs to** and its **name as used in your charter parties**
            - The **voyage or estimate** you need it for, if it's holding up work
            - For a correction: what's wrong now and what it should be, with a source if you have one

            > [!TIP]
            > Check the port isn't already in VMS under a different spelling or its UN/LOCODE before requesting it.

            [Log a VMS support case]({VMS_PORTAL})
        """),
    },

    # ── Knowledge Base: how-tos and explainers ──
    {
        "slug": "bunkers-on-delivery-redelivery",
        "title": "Bunkers on delivery and redelivery in time charters",
        "summary": "You're settling bunkers on delivery or redelivery on a time charter and the figures don't match the contract.",
        "section": "knowledge-base", "kind": "How-to", "topic": "Bunkers", "sort_order": 1,
        "related": "Shipping from Scratch",
        "body": md("""
            On a time charter, the charterer pays for the bunkers on board at delivery and the owner pays for those on board at redelivery, at the prices agreed in the contract. In VMS these come from the contract's delivery and redelivery terms and the ROB recorded at the delivery and redelivery port calls.

            ## How the amounts are worked out

            - **Quantity**: the ROB recorded at the delivery or redelivery port call, per fuel grade.
            - **Price**: the delivery or redelivery price from the time charter contract.
            - The resulting lines are settled through the hire statement and appear on the statement of account.

            ## When the figures don't match the contract

            1. **Check the ROB at the port call.** Document lines use the actual ROB value, which can have more decimals than the screen shows. A contract figure of 1180.926 and a recorded ROB of 1180.9261999 look the same but give different amounts. Set the ROB to the exact contract figure if that's what was agreed.
            2. **Check which port call is the delivery or redelivery.** If the wrong port call is used, the ROB comes from the wrong place.
            3. **Bunkers paid by the charterer on the owners' behalf** need recording on the owners' account so they appear correctly on the statement of account.

            > [!NOTE]
            > Bunkers on delivery and redelivery are part of the time charter settlement, so changes after hire has been invoiced can affect later hire statements.
        """),
    },
    {
        "slug": "laytime-terms-and-precision",
        "title": "Laytime terms and precision: why results can differ",
        "summary": "Laytime results changed after a recalculation, or weekend and holiday terms don't seem to be applied as you expect.",
        "section": "knowledge-base", "kind": "Explainer", "topic": "Laytime and demurrage", "sort_order": 2,
        "related": "Shipping from Scratch",
        "body": md("""
            Laytime is the time allowed in the charter party for loading and discharging. Going over it earns demurrage; finishing early may earn despatch. Two things often explain results that look wrong.

            ## Results changed after recalculating

            Since version 8.22, laytime is calculated to the second rather than with rounded values. Before, each cargo port's time allowed was rounded on its own, which could add up to about 30 seconds of difference per cargo port. Recalculating an older laytime with the newer version can therefore change the result slightly. The new figure is the more precise one.

            ## Weekend and holiday terms in estimates

            Laytime terms and correction factors (for example Saturdays, Sundays and holidays excluded) are applied across the whole week at the estimation stage. An estimate doesn't know which days the vessel will actually load or discharge, so it won't show the idle days you'd expect over a weekend. In the laytime calculation for the actual port call, the real dates are used.

            > [!TIP]
            > When quoting, allow for idle days in the estimate yourself if the timing over a weekend matters to the freight.

            ## Reversible laytime

            With reversible laytime, the time allowed is shared across load and discharge ports, so time saved at one port can offset time used at another. With non-reversible laytime, each port is calculated on its own.
        """),
    },
    {
        "slug": "accruals-and-your-accounting-system",
        "title": "Accruals and your accounting system: avoiding double counts",
        "summary": "Accrued amounts, such as demurrage, appear twice in your results, or accruals don't match your accounting system.",
        "section": "knowledge-base", "kind": "Explainer", "topic": "Accounting", "sort_order": 3,
        "body": md("""
            Accruals match a voyage's costs and revenue to the period they were earned or incurred, before every invoice is in. For each account, voyage and period, VMS records the difference between estimate and actual, and creates a reversal in the following period. Accruals move from Pending to Ready for Posting to Posted.

            ## Why amounts can be counted twice

            VMS already includes accruals when it calculates the actual result. If your accounting system then sends the same accrual back into VMS as an **actual** amount, it is counted twice.

            To avoid this:

            1. Send back only real invoices and payments as actuals, not accrual postings.
            2. Check the sign of what comes back: revenue such as demurrage should come back as positive.
            3. Agree with Sedna which of the ways of generating accruals your setup uses, so both systems follow the same rule.

            > [!NOTE]
            > Accruals cover open voyages and are part of period-end closing. Reversals in the next period are expected, not an error.
        """),
    },
    {
        "slug": "assembling-an-invoice",
        "title": "Assembling an invoice: when Create is unavailable",
        "summary": "You're trying to create an invoice from pending lines, but the Create button is greyed out or the invoice can't be assembled.",
        "section": "knowledge-base", "kind": "How-to", "topic": "Invoicing", "sort_order": 4,
        "body": md("""
            An invoice is made by selecting pending document lines and assembling them. If you can't create the invoice, check these in order.

            ## Checklist

            1. **Voyage status.** Invoices can only be assembled for voyages that aren't closed and are at status Nominated or higher. An estimate can't be invoiced.
            2. **Lines selected.** Select at least one pending line. Lines for different business partners go on separate invoices.
            3. **Bank details and payment terms.** Missing bank details or payment terms are a common reason an invoice comes out incomplete. Check them on the business partner and on your own company.
            4. **Outdated lines.** A message about outdated document lines means the voyage changed after the lines were created. Note what changed; if the lines don't update, log a case with the voyage number.

            > [!TIP]
            > Group the pending list by business partner to see which lines can go on one invoice.

            ## Before you log a case

            Log a case with the voyage number, the lines you selected and a screenshot of the screen with the Create button.
        """),
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        existing = set((await db.execute(select(Article.slug))).scalars().all())
        paths = {r.name: r.id for r in (await db.execute(select(LearningRole))).scalars().all()}
        added = 0
        for a in ARTICLES:
            if a["slug"] in existing:
                continue
            data = {k: v for k, v in a.items() if k != "related"}
            db.add(Article(**data, product="vms", is_published=True, is_sample=True,
                           related_path_id=paths.get(a.get("related", ""))))
            added += 1
        await db.commit()
    print(f"✓ {added} sample article(s) added, {len(ARTICLES) - added} already there.")


if __name__ == "__main__":
    asyncio.run(seed())
