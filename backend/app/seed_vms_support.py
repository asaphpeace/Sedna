"""Seed the VMS Support learning path.

Unlike seed.py (which TRUNCATEs every table before reseeding), this script
is purely additive: it checks whether a "VMS Support" LearningRole already
exists and, if so, does nothing. Safe to re-run.

Run once via:
    docker compose -f docker-compose.prod.yml exec backend python -m app.seed_vms_support
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine, Base
from app.models import *  # noqa: F401,F403 — registers all models with Base


# ─────────────────────────────────────────────────────────────────────────
# FOUNDATION TIER
# ─────────────────────────────────────────────────────────────────────────

FOUNDATION_MODULES = [
    {
        "title": "What is Dataloy VMS?",
        "type": "a", "dur": 8, "prod": "vms",
        "description": "The unification story behind the platform you support.",
        "learn_items": [
            "Why VMS, JVMS, the API, and FAS used to version separately",
            "What changed at release 5.0",
            "Why this history still matters when reading tickets",
        ],
        "rich_content": (
            "Before release 5.0, Dataloy's platform was really four separate products moving at their own pace: "
            "the web application (VMSWEB), the older Java client (JVMS), the REST API, and the Fleet Allocation "
            "and Scheduling module (FAS). Each shipped its own version number. A release note from that era might "
            "read \"VMS 3.26 / API 3.15\" — two different numbers for what a customer experienced as one system.\n\n"
            "Release 5.0 changed that on purpose. From that point on, all four sub-products share a single version "
            "number and are released together. That is why every release note you will ever read for VMS refers to "
            "one number, not four — and why a ticket referencing a customer's version tells you about the whole "
            "platform state, not just one part of it.\n\n"
            "This matters for support in a very practical way: when a customer says \"we're on 8.24,\" that number "
            "carries information about their API behavior, their web UI, and their FAS scheduling boards all at "
            "once. You do not need to ask which sub-product version they mean — there is only one answer."
        ),
    },
    {
        "title": "Where to look things up",
        "type": "a", "dur": 6, "prod": "vms",
        "description": "The three reference sites and what each one is actually for.",
        "learn_items": [
            "What docs.dataloy.com covers",
            "What api.dataloy.com covers",
            "Where release history lives",
        ],
        "rich_content": (
            "Three external sites hold almost everything you need outside of Notion.\n\n"
            "docs.dataloy.com is the VMS Knowledge Base — the step-by-step, feature-by-feature guide to using the "
            "web application. When a customer asks \"how do I do X in the UI,\" this is where the answer lives.\n\n"
            "api.dataloy.com documents the REST API — authentication, the data model, filtering and pagination, "
            "webhooks, and the integration guides for accounting, scheduling, bunker orders, service orders, and "
            "market indices. When a question is about an integration or a script talking to VMS rather than a "
            "human clicking through it, this is the site to search.\n\n"
            "releasenotes.dataloy.com carries the full release history, one page per version, going back years. "
            "This is the fastest way to answer \"did something change recently that would explain this\" — search "
            "for the customer's current version and read what shipped in and around it.\n\n"
            "All three sites are GitBook-hosted, which means every page is also available as plain Markdown by "
            "appending .md to its URL — useful if you ever want to paste a page's raw content somewhere, like an "
            "internal note or a script."
        ),
    },
    {
        "title": "Vessels & vessel master data",
        "type": "a", "dur": 16, "prod": "vms",
        "description": "How vessels are found, filtered, and configured — speed, consumption, and load/discharge rates.",
        "learn_items": [
            "The Operative / All / Map vessel list tabs",
            "How ballast and laden speed categories work",
            "Why bunker category changes affect all open voyages",
            "The difference between port rates and vessel capacity ratings",
        ],
        "rich_content": (
            "The Vessels module is reached from the Core Menu in the top left. The vessel list has three tabs: "
            "Operative shows only vessels with no fleet-exit date (or one still in the future) that have at least "
            "one voyage at Nominated status or beyond, but not Closed — in other words, vessels actually doing "
            "something right now. All shows every enabled vessel in the system, with extra filters for archived "
            "or disabled ones. Map gives a geographic view. A \"My Vessels\" quick filter narrows the list to "
            "vessels where the logged-in user holds a specific role — Master User, Responsible Accountant, "
            "Operator, or Claims Operator.\n\n"
            "Inside a vessel's record, the Speed & Consumption tab is where a customer defines how the vessel "
            "burns fuel. Separate cards exist for ballast and laden passages, and each can carry multiple named "
            "speed categories — ECO, WTR, FULL are typical examples — each with its own consumption rate per "
            "bunker type. These are defaults; a specific voyage can still override them. A second section covers "
            "boilers and generators: port idle consumption, working consumption, tank cleaning, cargo heating, "
            "and at-sea additional consumption for FO and MGO.\n\n"
            "The Bunker Categories section lets a customer choose which fuel types a vessel uses and in what "
            "priority order — the system picks the highest-priority category available in whatever geographic "
            "area the vessel is in. This is worth knowing for diagnosing bunker tickets: the documentation "
            "explicitly warns that changing a vessel's bunker categories affects every open voyage for that "
            "vessel, not just new ones.\n\n"
            "Load & Discharge Rates, found under its own tab in the vessel drawer, covers port- and "
            "terminal-specific handling rates. This is a common point of confusion worth remembering: these "
            "rates are not the vessel's own maximum load/discharge capacity — they are a separate, port-side "
            "figure, maintained in a table under the vessel record purely for reference during voyage planning."
        ),
    },
    {
        "title": "Trades",
        "type": "a", "dur": 10, "prod": "vms",
        "description": "What a trade is, and the three places a voyage gets assigned to one.",
        "learn_items": [
            "The Route-Trade-Pattern hierarchy",
            "The three places a voyage's trade gets set",
            "Why changing a voyage's trade triggers a warning",
        ],
        "rich_content": (
            "A trade groups voyages by the commercial lane they belong to — think of it as a tag that lets a "
            "customer report on, filter, and plan around a recurring shipping pattern rather than a single "
            "voyage. Trades sit in a hierarchy: a Trade dropdown showing one item means Trade only; two items "
            "means a Trade-Pattern or Route-Trade pairing; three items means the full Route-Trade-Pattern "
            "combination.\n\n"
            "A voyage's trade can be set in three different places, and it is worth knowing all three since a "
            "ticket might mention any of them: the Organisational Data tab inside the voyage drawer (Trade is "
            "the second field there); the Create Voyage Charterer and Create Time Charter Out modals, where the "
            "Trade dropdown sits in the lower right corner; and the Create Voyage From Template (CoA) flow.\n\n"
            "One behavior worth flagging to a confused customer: changing the trade on an already-created voyage "
            "in the voyage drawer triggers a warning, because doing so reassigns the trade for every cargo "
            "attached to that voyage, not just the voyage record itself. If a customer reports cargoes suddenly "
            "showing an unexpected trade, this is one of the first places to check."
        ),
    },
    {
        "title": "Voyages I: creating & finding voyages",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "The voyage creation paths, search fields, and the default status a new voyage gets.",
        "learn_items": [
            "The three voyage creation entry points",
            "What status a brand-new voyage starts in",
            "What fields the voyage search actually matches",
        ],
        "rich_content": (
            "The Voyages module lists every voyage type — unallocated, estimate, allocated, nominated, and "
            "beyond — with filtering and sorting to narrow it down. New voyages default to Voyage Progress "
            "\"Estimate\" and Voyage Status \"T\" (template/tentative), which is worth remembering: a customer "
            "who says \"I created a voyage and it's not showing where I expected\" may simply be looking in the "
            "wrong status filter.\n\n"
            "There are three distinct ways a voyage gets created, each its own guided flow: Create Voyage "
            "Charterer, for a standard voyage-charter voyage; Create Time Charter Out, for TC-out business; and "
            "Create Voyage From Template (CoA), which pulls structure from an existing Contract of Affreightment. "
            "Each of these has its own Trade dropdown and its own set of required fields, so \"how do I create a "
            "voyage\" is really three different answers depending on which of these three the customer means.\n\n"
            "Finding an existing voyage uses a single search bar at the top of the list, which matches against "
            "voyage reference number, vessel name, counterpart/charterer, port name, and cargo reference or "
            "trade — the list narrows live as you type. Beyond the search bar, column sort arrows and quick "
            "filters refine further, and columns like Cargo Operator, Freight Rate, and Laycan dates are hidden "
            "by default but can be turned on."
        ),
    },
    {
        "title": "Voyages II: the voyage drawer",
        "type": "a", "dur": 25, "prod": "vms",
        "description": "The drawer's tabs, the interactive schedule timeline, and what secondary actions live behind the menu.",
        "learn_items": [
            "The main drawer tabs and how TC voyages differ",
            "How the interactive schedule timeline works",
            "What lives in the secondary actions menu",
        ],
        "rich_content": (
            "The voyage drawer is the single screen most support tickets end up referencing, so it is worth "
            "knowing its shape cold. It splits into tabs: Vessel, Cargo List, Cargo (Performance Cargo), "
            "Schedule, Profit/Loss Summary, and Speed & Consumption. Time Charter voyages swap the Cargo tab for "
            "a Time Charter Contract tab instead — a useful tell when a customer's screenshot looks slightly "
            "different from what you expect.\n\n"
            "On the left side of the drawer sit the vessel name (clickable through to the vessel record), the "
            "voyage reference number, and an editable status dropdown. If a trade is attached, a chip shows the "
            "trade code with a link to the trade drawer. The right-side toolbar carries the primary actions: "
            "delete, duplicate, compare, print, voyage analysis, expand, and close.\n\n"
            "The Schedule tab deserves particular attention because it is genuinely interactive, not just a "
            "table. Each port call renders as a draggable block; reordering blocks changes the port call "
            "sequence for any port that is not fixed. Small \"chips\" inside each block show Days at Sea + Extra "
            "Days at Sea, Actual Speed, and Distance between Ports, and each of those is itself clickable to edit "
            "the underlying sea passage. Hovering over a port call reveals a toolbar for viewing/maintaining port "
            "costs, creating a new port call before or after, editing via a pencil icon, or deleting. Port "
            "selection in the edit modal is restricted once Arrival, Berthed, or Departure dates are fixed — only "
            "terminals already available at that port will show.\n\n"
            "The Profit/Loss Summary tab breaks down every cost and revenue item tied to the voyage, with "
            "different calculations depending on whether it is a voyage charter or time charter estimate. Because "
            "figures in a different currency than the voyage currency get converted using an average of the rate "
            "used in each invoice, P&L numbers can shift slightly until final invoicing locks them in — this is "
            "normal, not a bug, and worth explaining to a customer who notices the number moving. A TCE checkbox "
            "lets a user override either the TCE or the Result value directly, and the system back-calculates the "
            "freight rate or TC rate required to hit that target.\n\n"
            "Finally, the secondary actions menu (behind the toolbar's overflow icon) holds operations that do "
            "not belong on the main toolbar: swap vessel, edit the voyage reference number, convert to template, "
            "print statement of account, open a preliminary voyage, mark the voyage as optional, view the audit "
            "log, and upload or download attachments."
        ),
    },
    {
        "title": "Voyages III: bunkers, opex & various cost/revenue",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "Opening balances, the OPEX inheritance hierarchy, and how offhire interacts with both.",
        "learn_items": [
            "Where a voyage's opening bunker balance comes from",
            "The three-level OPEX hierarchy: vessel type, vessel, voyage",
            "Why OPEX keeps accruing during offhire unless flagged otherwise",
        ],
        "rich_content": (
            "The Bunkers tab on a voyage has three parts. Bunker Indices show benchmark fuel prices for FO and LS "
            "MGO, even for types not actually consumed, and can be adjusted when expanded. Bunker Stock Summary "
            "gives a card-based overview of consumed fuel types and their derived cost. Bunker Details lists "
            "every entry in filterable tables, split between consumption and bunkering events.\n\n"
            "Opening balances — the fuel on board at voyage start — are generated automatically from the "
            "previous fixed voyage, but stay editable while the voyage is Estimate or Unallocated, or whenever "
            "the voyage start date itself is fixed. For Time Charter In contracts specifically, opening balances "
            "stay synchronized with the contract's delivery bunkers on the first voyage — editing one edits the "
            "other for nominated voyages and beyond, which is a common source of \"why did this number change on "
            "its own\" tickets.\n\n"
            "OPEX (Operating Expenditure) covers a vessel's day-to-day running costs — crew wages, lube oil, "
            "insurance, retrofitting — and reduces final profitability without touching TCE or TC Result. It "
            "exists at three levels: Vessel Type sets a baseline rate for every vessel of that category; an "
            "individual Vessel can maintain its own OPEX list that overrides the type default; and a Voyage "
            "receives a stamped copy of whichever list applies, editable on that one voyage without touching the "
            "master record above it. The system computes total OPEX as daily rate multiplied by voyage days, "
            "summed across all active lines, and recalculates automatically whenever the vessel, voyage length, "
            "offhire days, or the OPEX lines themselves change.\n\n"
            "OPEX keeps accruing through offhire periods by default — a vessel still needs paying for and "
            "insuring even when it is not earning. If an offhire record carries the \"Deduct from Operational "
            "Cost\" flag, only then does the corresponding OPEX get pulled out of the relevant cost account. This "
            "is a useful thing to check when a customer disputes an OPEX figure on a voyage that had offhire."
        ),
    },
    {
        "title": "Voyages IV: secondary actions & lifecycle",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "Converting, swapping, and deleting voyages — and the rules that stop a deletion from going wrong.",
        "learn_items": [
            "The six secondary voyage actions",
            "Which voyage statuses can be deleted",
            "Why deleting a template voyage can be blocked",
        ],
        "rich_content": (
            "Beyond day-to-day editing, a voyage supports six secondary actions: converting to a Template "
            "Voyage; converting to TC Out; changing status directly; swapping the assigned vessel; marking a "
            "voyage as the Last TC Voyage; and updating the voyage's reference number, voyage number, or starting "
            "year. Each of these is its own guided flow rather than a plain field edit, which is why a customer "
            "asking \"how do I change the vessel on a voyage\" needs pointing at Swap Vessel specifically, not a "
            "generic edit screen.\n\n"
            "Deletion has real guardrails. Only voyages with Estimate or Unallocated status can be deleted "
            "directly — anything further along the lifecycle needs its status changed back first. Because "
            "voyages can be connected to cargoes, offhires, or (for template voyages) other scheduled voyages, "
            "deleting one deletes its connected entities too, and the confirmation modal lists exactly what will "
            "go with it before you commit.\n\n"
            "Template voyages get an extra layer of protection: attempting to delete a template voyage that has "
            "scheduled voyages at Nominated status or later produces an error instead of a deletion, specifically "
            "to stop an accidental deletion from cascading into voyages that are already commercially committed. "
            "If a customer reports being unable to delete a template, this restriction is the first thing to "
            "check, not a bug report.\n\n"
            "Two related features round out the lifecycle picture. Voyage Comparisons let a user save a named, "
            "commented comparison against a chosen base voyage, accessible both from a dedicated Comparisons tab "
            "in the Voyages module and via a Find Comparison button inside a specific voyage's drawer. TC "
            "Voyages, meanwhile, swap the Cargo tab for a Time Charter Contract tab, pull Delivery/Redelivery "
            "Port fields from the linked port calls, disable the Duration and Rate fields whenever the underlying "
            "contract has multiple durations or rates, and expose a Calculate Profit/Loss checkbox only while the "
            "voyage is still in Estimate status."
        ),
    },
    {
        "title": "Cargoes I: creating & allocating",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "The five ways to create a cargo, and the Allocated/Unallocated/Sub-cargoes list structure.",
        "learn_items": [
            "The five cargo creation methods",
            "The difference between allocated, unallocated, and sub-cargoes",
            "Where sub-cargoes display differently from regular cargoes",
        ],
        "rich_content": (
            "Cargo creation supports five distinct paths: a standard from-scratch entry; creation from a "
            "Contract of Affreightment template; creation directly on a Time Charter voyage; bulk creation via "
            "Excel import; and duplication from an existing cargo record. Each addresses a different real-world "
            "scenario, and knowing which one a customer used often explains an otherwise-confusing field state — "
            "a cargo created from a CoA template, for instance, will carry pre-populated values a from-scratch "
            "cargo never would.\n\n"
            "The Cargoes module organizes records into three lists. Allocated Cargoes holds anything created on, "
            "or later moved to, a voyage — a single voyage can carry several cargoes at once, and clicking one "
            "opens its drawer. Unallocated Cargoes holds newly created cargoes not yet tied to any voyage; the "
            "cargo drawer from here is where a user allocates it. Sub-cargoes is a separate list of cargoes "
            "linked beneath a parent cargo — multiple sub-cargoes can attach to one parent — and importantly, "
            "sub-cargoes open in a modal dialog rather than the standard drawer, which is a small but real UI "
            "difference worth knowing before you tell a customer to \"open the drawer\" for one."
        ),
    },
    {
        "title": "Cargoes II: the cargo drawer & actions",
        "type": "a", "dur": 20, "prod": "vms",
        "description": "Freight rate tiers, and the relet/transship/preship family of secondary actions.",
        "learn_items": [
            "Tiered pricing vs. volume pricing on freight rate tiers",
            "What a relet actually creates behind the scenes",
            "The field difference between transshipment and preshipment",
        ],
        "rich_content": (
            "Freight Rate Tiers let a cargo carry more than one price point instead of a single flat rate, in "
            "one of two models. Tiered pricing charges successive rate bands as quantity climbs — an 8,000 MT "
            "cargo might cost 11 USD/MT for the first 4,999 MT and 12 USD/MT for the remaining 3,001 MT, shown "
            "as a weighted average. Volume pricing instead applies one single rate to the whole quantity, chosen "
            "by whichever bracket the total quantity falls into — the same 8,000 MT cargo might simply be billed "
            "at 12 USD/MT across the board. Adding any tier locks the main Freight Rate and Rule fields on the "
            "cargo, and the Rule field's label itself changes to Rate as a visual cue that tiering is active.\n\n"
            "Relet, transshipment, and preshipment are related but distinct actions, all reached from the More "
            "menu on a cargo and all appearing together afterward under \"Relets and Transhipments\" in the cargo "
            "drawer. A plain relet sub-charters the cargo to a different owner for the full voyage; the system "
            "creates a duplicate cargo record with its financial treatment flipped from freight revenue to "
            "freight cost, reflecting that this owner is now paying for carriage rather than earning from it. "
            "Transshipment is a relet variant where cargo moves to an intermediate destination on one vessel "
            "before continuing on another — its From Port must be a discharge port from the original booking, "
            "and its To Port auto-populates the cargo's Final Destination. Preshipment is the mirror case: cargo "
            "travels from an originating location to the load port already specified in an existing booking, so "
            "its From Port sets Place of Origin and its To Port must be a load port from that original booking.\n\n"
            "A detail worth remembering for reconciliation questions: certain fields stay synchronized between an "
            "original cargo and its relet — changing cargo quantity, measurement unit, commodity, or planned BL "
            "date on either side automatically updates the other to match."
        ),
    },
    {
        "title": "Port calls",
        "type": "a", "dur": 20, "prod": "vms",
        "description": "The port call drawer's structure, registering arrival, and how pilot stations change voyage calculations.",
        "learn_items": [
            "What the port call drawer consolidates",
            "What locks after registering an arrival",
            "How a pilot station changes speed, distance, and consumption",
        ],
        "rich_content": (
            "The port call drawer is a genuine hub — it consolidates bunker tracking (remaining-on-board fuel, "
            "per-leg consumption, debunkering, and establishing bunker requirements), cost management (entering "
            "port costs directly or pulling handling charges from service orders, with automation available for "
            "both), and documentation (service orders, bunker orders, and vessel reports including noon reports "
            "all surface here). Overview and Bunkers is the entry point, branching out into the more specialized "
            "subsections.\n\n"
            "Registering an arrival is done from the port call's menu icon by selecting Register Arrival, which "
            "opens a dialog scoped only to the bunker categories actually used during that voyage. Two locking "
            "behaviors matter here: registering an arrival with a past date locks the arrival date on that port "
            "call permanently, and any ROB (Remaining on Board) values entered at that point become locked as "
            "Arrival ROBs. If a customer needs to correct a figure after this point, the fix has to go through a "
            "different path than simply re-editing the field — worth knowing before promising a quick correction.\n\n"
            "Pilot station handling routes a voyage through an additional point at a port, and the system "
            "recalculates distance, dates, and fuel consumption around it. A pilot leg performance factor "
            "(typically 80 percent of sea speed, though 100 percent disables the reduction entirely) applies to "
            "both speed and consumption for that leg. Distance for each leg displays separately, flagged with an "
            "icon, and diversions show on the voyage map. Pilot stations also generate their own event set — "
            "Arrival at the station, Berth at the port, Unberth, and Departure back through the station — and "
            "consecutive voyages account for this: a voyage ending at a pilot station passes that point on as "
            "the next voyage's ballast coordinate. Pilot stations can be added manually via flag icons in the "
            "voyage fullscreen or port call views, or inserted automatically through system settings."
        ),
    },
    {
        "title": "Chartering: CoA & Time Charter contracts",
        "type": "a", "dur": 22, "prod": "vms",
        "description": "What a CoA and a TC contract each govern, and how durations work inside a TC contract.",
        "learn_items": [
            "The CoA / CoA line / template cargo hierarchy",
            "What a TC contract's Duration actually represents",
            "How TC In and TC Out contracts can link internally",
        ],
        "rich_content": (
            "A Contract of Affreightment (CoA) is a standing agreement to carry a defined volume of cargo over "
            "time, rather than a single voyage's terms. Its structure nests three levels deep: the CoA itself, "
            "one or more CoA Lines beneath it, and Template Cargoes beneath each line — each level has its own "
            "find/create/maintain guide, and a support question about a CoA often really turns out to be about "
            "one specific line or template cargo underneath it, not the top-level contract record.\n\n"
            "A Time Charter Contract governs the terms for hiring a vessel over a defined period, and unlike a "
            "CoA, it is built around one or more Durations — each Duration is its own period with its own terms, "
            "during which the vessel is employed under that contract. A contract can carry multiple durations "
            "over its life, each with its own rate, and the system tracks index-based hire-rate adjustments, "
            "notice provisions, commission structure, payment terms, and vessel speed/consumption data at this "
            "level. Both TC In (hiring a vessel) and TC Out (chartering one out) exist, and the two can be linked "
            "internally through TC Relet Creation when both sit inside the same organisation — useful context "
            "when a ticket describes hire flowing between what look like two separate contracts but are actually "
            "connected.\n\n"
            "Broker Commissions and Market Indices sit alongside contract management rather than inside it. "
            "Market Indices split into standard Market Indices and Custom Indices, created via a dialog reached "
            "from a top-right button; a Market Index Code must be unique and uppercase-only, and a \"Protected\" "
            "option only appears for users holding the Protected Market Index Contributor security role — a good "
            "thing to check first if a customer reports not seeing that option at all."
        ),
    },
    {
        "title": "Fixtures & relet — why cargo links the way it does",
        "type": "a", "dur": 10, "prod": "vms",
        "description": "The 7.1 architecture shift that introduced fixtures, and how it shaped everything relet-related that followed.",
        "learn_items": [
            "What changed structurally at release 7.1",
            "Why relet cargo behaves the way it does",
            "How this ties into the multi-company P&L work at 8.27",
        ],
        "rich_content": (
            "Before release 7.1, cargo and charter-party data were connected more loosely than they are today. "
            "7.1 introduced a dedicated fixture table and a direct link from cargo to fixture — a genuine "
            "database-level change, not just a UI feature. Every release note from 7.0 onward explicitly frames "
            "that whole 7.x series as \"a significant jump from 6.46,\" and this is the concrete reason why: the "
            "underlying data model, not just the screens on top of it, changed shape.\n\n"
            "Everything relet-related that support deals with today is built on that foundation. The relet, "
            "transshipment, and preshipment actions covered in the Cargoes module rely on cargo's direct "
            "connection to its fixture to know what it is a variant of. Internal cargo relet management — where "
            "the system automatically generates a linked cargo and keeps key fields synchronized between "
            "original and relet — arrived in releases 8.15 and 8.16, built directly on the 7.1 foundation rather "
            "than as a separate feature.\n\n"
            "The most recent extension of this thread is the multi-company profit-and-loss view introduced at "
            "release 8.27, which lets a voyage's P&L be viewed separately by each company involved in an "
            "internal relet. None of that would be possible without the fixture-centric data model 7.1 "
            "established — which is exactly the kind of \"why does the system work like this\" context that "
            "turns a confusing relet ticket into a straightforward one."
        ),
    },
    {
        "title": "Working the UI: grids, views & bulk update",
        "type": "a", "dur": 12, "prod": "vms",
        "description": "Data grid mechanics, saved views, bulk update math, and the comment/attachment basics that show up in almost every ticket.",
        "learn_items": [
            "Data grid keyboard shortcuts and column controls",
            "The three types of saved view and who can create them",
            "The four bulk-update modes, including percentage and value change",
        ],
        "rich_content": (
            "Most lists in VMS are data grids, and they share a common set of controls: Customise Columns to "
            "choose visible fields, Show Filters, a Density toggle, Export, and Expand for more rows. Column "
            "headers carry their own menu (the vertical-ellipsis icon) for sorting, pinning, and repositioning; "
            "columns resize by dragging the header boundary or auto-fit with a double-click. Keyboard shortcuts "
            "are genuinely fast once learned: typing directly overwrites a highlighted cell, Enter opens edit "
            "mode, Escape cancels, and Ctrl/Cmd+Enter opens a column's menu without touching the mouse. Enter "
            "toggles single-column sort; Shift+Enter adds a second sort column.\n\n"
            "Custom Views save a specific combination of columns, filters, and sorting for reuse, in one of "
            "three scopes: Private (visible only to the creator), Group (visible to selected security groups), "
            "or Company (visible to everyone). Only users holding the Views Contributor role can create Group or "
            "Company views — anyone can create a Private one. If no view has been chosen, the system defaults to "
            "the first available Group view, and \"System Default\" always resets a list back to its original "
            "configuration.\n\n"
            "Bulk Update lets a user change one field across many selected rows at once, with four modes per "
            "field: Keep Existing (no change), Set New Value (identical value everywhere), Change by Percentage "
            "(proportional adjustment — increasing 50 by 10 percent gives 55), and Change by Value (a fixed "
            "addition or subtraction — adding 10 to 50 gives 60). Bulk Delete works the same selection-first "
            "pattern, though status rules still apply underneath it — for voyages, only Estimate, Allocated, or "
            "Unallocated records can be deleted, and any non-deletable row simply stays selected and unaffected "
            "when the rest proceed.\n\n"
            "Two smaller features round out daily UI use. Attachments open from the secondary actions button in "
            "any drawer, support drag-and-drop upload, and require files from an email to be downloaded locally "
            "first before they can be attached. Comments live on their own tab in every drawer, are visible to "
            "anyone with access to that module, support @mentions with a notification to the mentioned user, and "
            "can be edited or deleted by their author — administrators can additionally delete anyone's comment."
        ),
    },
]

FOUNDATION_QUIZ = [
    {
        "q": "Before release 5.0, how many separately-versioned sub-products made up what is now called VMS?",
        "explanation": "VMSWEB, JVMS, the API, and FAS each carried their own version number until 5.0 unified them.",
        "options": [
            ("Two", False), ("Three", False), ("Four", True), ("Five", False),
        ],
    },
    {
        "q": "A customer wants to know how to authenticate a script against the VMS REST API. Which site should you point them to?",
        "explanation": "api.dataloy.com is the REST API reference, covering authentication, the data model, and integration guides.",
        "options": [
            ("docs.dataloy.com", False), ("api.dataloy.com", True),
            ("releasenotes.dataloy.com", False), ("The VMS release notes changelog", False),
        ],
    },
    {
        "q": "What status does a brand-new voyage default to?",
        "explanation": "New voyages default to Voyage Progress \"Estimate\" and Voyage Status \"T\".",
        "options": [
            ("Nominated", False), ("Allocated", False), ("Estimate", True), ("Closed", False),
        ],
    },
    {
        "q": "Which tab does a Time Charter voyage show in the voyage drawer instead of the regular Cargo tab?",
        "explanation": "TC voyages replace the Cargo tab with a Time Charter Contract tab.",
        "options": [
            ("Speed & Consumption", False), ("Time Charter Contract", True),
            ("Profit/Loss Summary", False), ("Schedule", False),
        ],
    },
    {
        "q": "A customer says they changed a vessel's bunker categories and now all of that vessel's open voyages look different. Is this expected?",
        "explanation": "The documentation explicitly warns that bunker category changes affect all open voyages for that vessel, not just new ones.",
        "options": [
            ("Yes — this is documented behavior", True), ("No — this is always a bug", False),
            ("Only if the vessel is on a Time Charter", False), ("Only for tankers", False),
        ],
    },
    {
        "q": "OPEX exists at which three levels?",
        "explanation": "OPEX is defined at Vessel Type, Vessel, and Voyage level, each able to override the level above it.",
        "options": [
            ("Company, Vessel, Port", False), ("Vessel Type, Vessel, Voyage", True),
            ("Voyage, Cargo, Port Call", False), ("Organisation, Business Unit, Voyage", False),
        ],
    },
    {
        "q": "Which voyage statuses can be deleted directly, without first changing status?",
        "explanation": "Only Estimate or Unallocated voyages can be deleted directly.",
        "options": [
            ("Nominated or Allocated", False), ("Estimate or Unallocated", True),
            ("Any status", False), ("Closed only", False),
        ],
    },
    {
        "q": "What financial change happens when a cargo is relet to another owner?",
        "explanation": "The relet duplicate cargo has a freight cost instead of a freight revenue — the new owner pays for carriage rather than earning from it.",
        "options": [
            ("Nothing changes financially", False),
            ("The relet cargo shows freight cost instead of freight revenue", True),
            ("The original cargo is deleted", False),
            ("The freight rate is doubled", False),
        ],
    },
    {
        "q": "What happens once you register a past-dated arrival on a port call?",
        "explanation": "The arrival date locks, and any ROB values entered at that point lock as Arrival ROBs.",
        "options": [
            ("Nothing locks", False),
            ("The arrival date and any entered ROB values lock", True),
            ("Only the vessel name locks", False),
            ("The whole voyage locks", False),
        ],
    },
    {
        "q": "What architectural change did release 7.1 introduce that later relet features are built on?",
        "explanation": "7.1 introduced a dedicated fixture table with a direct cargo-to-fixture link — a genuine data-model change.",
        "options": [
            ("A new invoicing engine", False), ("The fixture table and cargo-to-fixture link", True),
            ("EU ETS compliance tracking", False), ("The claims management module", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# ROLE ASSEMBLY (Practitioner and Professional tiers appended below as they
# are authored — see PRACTITIONER_MODULES / PROFESSIONAL_MODULES further
# down this file once complete)
# ─────────────────────────────────────────────────────────────────────────

ROLE_DATA = {
    "name": "VMS Support",
    "description": "Diagnose and resolve customer issues in Dataloy VMS — from the core data model through ticket handling to API-level root cause.",
    "icon": "ti-headset",
    "color": "purple",
    "audience": "internal",
    "products": ["vms"],
    "sort_order": 100,
    "tiers": [
        {
            "label": "Foundation",
            "name": "VMS Support Foundation",
            "cert_name": "VMS Support — Foundation",
            "modules": FOUNDATION_MODULES,
            "quiz": FOUNDATION_QUIZ,
        },
    ],
}


async def seed(db: AsyncSession):
    """Get-or-create the role, then get-or-create each tier by label.

    This is tier-aware on purpose: as more tiers get added to ROLE_DATA in
    later revisions of this file, re-running the script will add only the
    tiers that don't exist yet under the VMS Support role — it will never
    duplicate a tier (or the role) that's already there. Safe to run today
    with Foundation only, and safe to re-run once Practitioner and
    Professional are appended below.
    """
    result = await db.execute(select(LearningRole).where(LearningRole.name == ROLE_DATA["name"]))
    role = result.scalar_one_or_none()
    if role is None:
        role = LearningRole(
            name=ROLE_DATA["name"], description=ROLE_DATA["description"],
            icon=ROLE_DATA["icon"], color=ROLE_DATA["color"],
            audience=ROLE_DATA["audience"], products=ROLE_DATA["products"],
            sort_order=ROLE_DATA["sort_order"],
        )
        db.add(role)
        await db.flush()
        print(f"Created role: {role.name}")
    else:
        print(f"Role '{role.name}' already exists — adding any missing tiers under it.")

    existing_tiers = await db.execute(select(Tier).where(Tier.role_id == role.id))
    existing_labels = {t.label for t in existing_tiers.scalars().all()}

    added_tiers = 0
    for t_sort, td in enumerate(ROLE_DATA["tiers"]):
        if td["label"] in existing_labels:
            print(f"  Tier '{td['label']}' already exists — skipping.")
            continue

        tier = Tier(
            role_id=role.id, label=td["label"], name=td["name"],
            cert_name=td["cert_name"], sort_order=t_sort,
        )
        db.add(tier)
        await db.flush()

        for m_sort, md in enumerate(td["modules"]):
            module = Module(
                tier_id=tier.id, title=md["title"], module_type=md["type"],
                duration_mins=md["dur"], product=md["prod"], sort_order=m_sort,
                description=md.get("description", ""), learn_items=md.get("learn_items", []),
                rich_content=md.get("rich_content"),
            )
            db.add(module)
            await db.flush()

        # Quiz attached to the tier's final module (matches app convention of
        # a quiz gating tier completion)
        if td.get("quiz") and td["modules"]:
            last_module_result = await db.execute(
                select(Module).where(Module.tier_id == tier.id).order_by(Module.sort_order.desc()).limit(1)
            )
            quiz_module = last_module_result.scalar_one()
            for q_sort, qd in enumerate(td["quiz"]):
                question = QuizQuestion(
                    module_id=quiz_module.id, question_text=qd["q"],
                    explanation=qd.get("explanation", ""), sort_order=q_sort,
                )
                db.add(question)
                await db.flush()
                for o_sort, (text, correct) in enumerate(qd["options"]):
                    db.add(QuizOption(question_id=question.id, text=text, is_correct=correct, sort_order=o_sort))

        print(f"  Added tier '{td['label']}' with {len(td['modules'])} modules.")
        added_tiers += 1

    await db.commit()
    print(f"✓ Done — {added_tiers} new tier(s) added this run.")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
