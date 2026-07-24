"""Seed the VMS Support learning path...

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
# PRACTITIONER TIER
# ─────────────────────────────────────────────────────────────────────────

PRACTITIONER_MODULES = [
    {
        "title": "The ticket lifecycle (7 steps)",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "Triage, confirm done, search first, resolve, capture notes, escalate, document.",
        "learn_items": [
            "The 7-step flow every ticket should follow",
            "Why the problem statement is written before investigation starts",
            "What 'document the solution' actually requires",
        ],
        "rich_content": (
            "Every VMS ticket should move through the same seven steps, regardless of how it started. Step one, "
            "triage and classify, happens within the first response window: gather customer and domain, the "
            "affected vessel/voyage/component if the customer hasn't already given it, urgency and impact, "
            "ticket type (Education, Task, or Problem/Bug), and — critically — a one-sentence problem statement "
            "in the form \"Customer X in domain Y cannot do Z; expected behavior is A, actual is B.\" If you "
            "cannot write that sentence clearly, pause and ask the customer for clarification before "
            "investigating further.\n\n"
            "Step two confirms what \"done\" looks like — the customer's success criteria and the deadline "
            "implied by severity — and writes it into the ticket. Step three is searching before escalating: "
            "prior VMS tickets, Jira internal notes, Slack history, and the support docs, always logging what "
            "you found and your working hypothesis so a future person does not repeat the same search.\n\n"
            "Step four is resolution: either solve it end to end and move to documentation, or continue to step "
            "five. Step five captures investigation notes as you go — what you checked, what you tried, "
            "reproduction steps, and evidence — so someone else could pick the ticket up without starting over. "
            "Step six is escalation with full context: tag the right person, explain the exact ask, and include "
            "everything from step five. The bar here is concrete — if the person you escalate to has to ask "
            "\"what did you try?\", the escalation was not complete.\n\n"
            "Step seven, mandatory regardless of who solved it, is documenting the resolution in Jira's internal "
            "notes: the final steps, any decision points worth remembering (\"if A, do B\"), and reusable "
            "customer-facing wording. The standard this is held to is simple: a future support team member should "
            "be able to solve the same issue using the internal note alone, without redoing the investigation."
        ),
    },
    {
        "title": "Jira/DSD mechanics",
        "type": "a", "dur": 12, "prod": "vms",
        "description": "Required vs. context fields, the Team Responsibility sheet, and the most common triage mistakes.",
        "learn_items": [
            "The five required fields vs. the three context fields",
            "Where the Team Responsibility sheet fits into assignment",
            "The four most common triage mistakes",
        ],
        "rich_content": (
            "Triage in the strict, mechanical sense means categorizing, prioritizing, and assigning a ticket — "
            "before it ever reaches whoever will actually solve it. The required fields that must be filled at "
            "L1 are Assignee, Request Type (usually automated), Customer, and Fix Versions (add a new version "
            "via \"create new version\" if it is not already in the dropdown). Two fields are explicitly not "
            "updated by L1: Billable and Time Remaining.\n\n"
            "A second set of context fields — URL, Affected Vessel/Voyage, and Components — are not mandatory "
            "but genuinely helpful: URL is usually the direct link to the page the customer was on, Affected "
            "Vessel/Voyage names the specific record, and Components lists what parts of VMS the issue touches.\n\n"
            "Once those fields are set, check the Team Responsibility sheet to see who owns that area of the "
            "system, and assign accordingly — that person then reassigns within their own team to whoever has "
            "capacity. Depending on severity, you either respond to the customer immediately to acknowledge "
            "receipt, or leave it for the assigned person if urgency does not demand an instant reply. Jira "
            "distinguishes \"add internal note\" (visible only internally, supports tagging colleagues) from "
            "\"reply to customer\" (which flips the ticket status to \"waiting for customer,\" then back to "
            "\"waiting for support\" once they reply).\n\n"
            "The four mistakes worth watching for, because they are the ones that actually cause rework "
            "downstream: not assigning the ticket correctly, not updating the request type (which routes it to "
            "the wrong queue entirely), missing customer context like version, and overfilling fields that are "
            "not required at L1. If a ticket looks like a duplicate of, or mergeable with, another one, Jira "
            "supports linking the two and tagging the reason — worth doing rather than letting duplicates pile "
            "up silently."
        ),
    },
    {
        "title": "Escalation: who to call",
        "type": "a", "dur": 8, "prod": "vms",
        "description": "The five escalation targets and the standard checklist every escalation should carry.",
        "learn_items": [
            "Which team owns which category of issue",
            "The six items every escalation needs",
        ],
        "rich_content": (
            "Five escalation targets cover almost everything: the Infrastructure team for VMS down (SYS-01), VMS "
            "slow (SYS-02), or a server restart; the Development team for commit exceptions (SYS-05), data "
            "corruption, or specific bug codes like BNK-04 and INV-03; the Dataloy distance team for wrong "
            "distances (ROU-01), canal route errors (ROU-02), ECA routing (ROU-03), or port additions (MDT-01); "
            "the customer's own IT/Azure AD team for SSO or Entra ID login issues (SYS-03); and the DA Desk team "
            "for webhook payload issues (INV-10).\n\n"
            "Every escalation, regardless of target, should carry the same standard checklist: customer name and "
            "environment (PROD or UAT, plus any recent change like an upgrade or config edit); what broke, stated "
            "as expected versus actual in one or two sentences; key identifiers — voyage key, fixture key, cargo "
            "key, invoice or service order ID, port call ID, whichever apply; scope — one record or many, one "
            "user or many, and the time range affected; evidence — screenshots, exact error text, timestamps, "
            "and steps to reproduce; and finally what you already checked, listed as completed steps with their "
            "outcomes. Filling all six in before you escalate is what separates an escalation that gets acted on "
            "immediately from one that bounces back with \"what did you try?\""
        ),
    },
    {
        "title": "SLA & response times",
        "type": "a", "dur": 5, "prod": "vms",
        "description": "Blocked — see the note below before this module is drafted for real.",
        "learn_items": [],
        "rich_content": (
            "This module is intentionally left as a placeholder. During the knowledge-base audit, three "
            "different links purporting to be \"our SLA\" were found across the Support Notion space — two "
            "identical links under different labels on the team home page, and a third, different document "
            "linked from inside the ticket-handling guide. Writing a real SLA module before that is resolved "
            "would mean teaching an active ambiguity as if it were settled fact, which is worse than leaving the "
            "module empty.\n\n"
            "Once a single canonical SLA source is confirmed, this module should state: the response-time "
            "target per severity level, what counts as an \"outage\" versus routine severity, and where the "
            "authoritative document lives so nobody has to guess between the three links again."
        ),
    },
    {
        "title": "Common Jira/DSD workflows",
        "type": "a", "dur": 12, "prod": "vms",
        "description": "Adding a customer to Jira DSD, adding a service desk user, and the small-vs-standard upgrade booking process.",
        "learn_items": [
            "What qualifies as a 'small' upgrade vs. one needing standard planning",
            "The current booking process for small upgrades",
            "Why the 'standard planning process' page needs a fix before it's usable",
        ],
        "rich_content": (
            "Two everyday Jira Service Desk administrative tasks come up often enough to be worth their own "
            "reference: adding a new customer to Jira DSD, and adding an individual user to the service desk so "
            "they can raise tickets. Both are quick, guided flows in Jira's own admin screens — the Support "
            "Notion space keeps a short quick-guide for each.\n\n"
            "Upgrade scheduling is the more nuanced workflow. A small upgrade is defined as any upgrade from an "
            "environment already running version 8.17.0 or later. For a small upgrade, the current process is "
            "self-service: add a calendar invite to Martin or Elias in one of their available slots — Monday, "
            "Wednesday, or Friday at 10:30 UK / 11:30 Norway, or Tuesday/Thursday at 08:30 UK / 09:30 Norway — "
            "and include the Jira ticket number, customer name, and environment (Test or Prod) in the invite, "
            "making sure the Jira ticket itself states the target version number. If the upgrade turns out not "
            "to be needed after all, delete the calendar entry — leaving it in place means the upgrade proceeds "
            "regardless.\n\n"
            "Anything that does not qualify as small — an upgrade from version 8.16 or earlier, an on-prem "
            "environment, an upgrade involving Java changes, or one that must run out-of-office-hours — has to "
            "go through \"the standard planning process\" instead. This is the one genuine gap worth flagging "
            "here directly: the page that is supposed to document that standard process is, as of this writing, "
            "an unfilled template — every step is an empty checkbox, sourced from a Google Doc whose sharing "
            "permissions were never actually opened up for import. Until that page has real content, a complex "
            "or legacy-version upgrade request should be routed to whoever currently owns that process by asking "
            "directly, not by trusting the linked page to explain it."
        ),
    },
    {
        "title": "Fleet plans & scheduling boards",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "The Gantt board, Open Positions board, and Cargo Management board — what each shows and how they connect.",
        "learn_items": [
            "What each of the three main planning boards is for",
            "How to compare two scenarios on the Gantt board",
            "The color coding for early/late timing on the Cargo Management board",
        ],
        "rich_content": (
            "Three boards make up most of day-to-day fleet planning. The Gantt board lays voyages out on a "
            "timeline with vessels as rows and dates as columns, with a red vertical line marking today. It "
            "splits into Commitments at the top (unallocated voyages, shown with charterer, laycan, and "
            "commodity) and Schedule at the bottom (allocated or nominated voyages, with reference number, "
            "status, and port information — hovering a bar reveals TCE and quantity). A genuinely useful feature "
            "here is scenario comparison: selecting a second scenario doubles each vessel's row, with blue bars "
            "for the primary scenario and grey for the comparison, and clicking any bar opens the full voyage "
            "drawer.\n\n"
            "The Open Positions board organizes around vessel availability rather than a timeline. Each vessel "
            "column starts with a yellow Vessel Open Position card showing where that ship's schedule begins — "
            "clickable to edit the port and date, except inside a MASTER scenario, where it is read-only. "
            "Unallocated Voyage cards sit in a separate Voyage Commitments column with charterer, ports, "
            "commodity, laydays, and quantity; allocated cards show a port-call timeline (minimum three ports "
            "visible at once) with cumulative cargo weight after each call; and a Last Port Call card marks when "
            "a vessel becomes free again after its final scheduled voyage.\n\n"
            "The Cargo Management board is organized around cargo rather than vessels or positions. Unallocated "
            "Cargo Commitments sit in the left column with charterer, cargo reference, booking status, trade, "
            "ports, commodity, laydays, and quantity; the remaining columns show voyages with their allocated "
            "cargoes, and cargoes can be dragged and dropped between voyages within the same trade. Vertical "
            "blue spans track which port calls a cargo covers, and a color system flags timing at a glance: blue "
            "for early, red for late, and normal coloring for on-time — worth knowing when a customer asks why a "
            "particular cargo bar looks a certain color."
        ),
    },
    {
        "title": "Scenarios & budgets",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "The MASTER scenario, comparing scenarios, and the four building blocks of the Budgets module.",
        "learn_items": [
            "Why the MASTER scenario is read-only",
            "The four building blocks of a budget",
            "Why budgeted voyages never show up in operational voyage lists",
        ],
        "rich_content": (
            "Scenarios maintain a list of every planning scenario and its associated budget. One scenario is "
            "always designated MASTER — shown in capital letters and permanently read-only, protecting the live "
            "configuration from accidental edits made while exploring alternatives. Any other scenario can be "
            "duplicated, renamed, or reviewed for its voyage, cargo, and vessel content, and a Comparing "
            "Scenarios feature lets several be evaluated side by side — useful when weighing different fleet "
            "strategies before committing.\n\n"
            "Budgets sit one level up from day-to-day scenarios, built for annual fleet planning rather than "
            "live operations. Four things make up a budget: a Budget Scenario (a named plan for a specific year, "
            "displayed as \"Budget Year Scenario Name\" — for example \"2027 Base Case\"); Template Voyages "
            "(reusable definitions of route, cargo, and financial assumptions for a voyage type the fleet "
            "expects to run repeatedly); Budgeted Voyages (lightweight entries that place a template's "
            "occurrences on the timeline using start dates and laycans, inheriting everything else from the "
            "template); and supporting data — bunker prices, exchange rates, and port information that feed the "
            "P&L math underneath it all.\n\n"
            "Multiple scenarios can run in parallel for genuine comparison — a conservative freight outlook "
            "alongside an optimistic one, or an originally-approved budget kept next to a revised mid-year "
            "forecast. Access requires the Budget Viewer or Administrator role, and a detail worth remembering "
            "when a customer asks why a budgeted voyage isn't showing up somewhere unexpected: template and "
            "budgeted voyages exist only inside the Budgets module and are deliberately invisible to every "
            "operational voyage list — they are not real voyages until someone converts a budget into an actual "
            "voyage."
        ),
    },
    {
        "title": "Bunker orders & service orders",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "The bunker order status workflow, ROB calculation logic, and the draft-status safety net on service orders.",
        "learn_items": [
            "The five bunker order statuses and which transitions are allowed",
            "How the system calculates bunkered quantity from min/max figures",
            "Why service orders start in Draft status",
        ],
        "rich_content": (
            "Bunker orders can be created from a port call drawer directly, or from scratch in the dedicated "
            "Bunker Order module — useful to know since a customer describing \"creating a bunker order\" might "
            "mean either starting point. They move through five statuses with specific rules: Draft and "
            "Requirement can transition to any other status freely; Stemmed (after a supplier is selected) can "
            "only move to Delivered; Delivered (which requires a completed bunkering date and shore quantity on "
            "every line) can only move to Cancelled; and Cancelled is terminal, though deletion remains possible "
            "from there.\n\n"
            "The bunkered quantity itself follows a hierarchy: if only a minimum quantity was entered, that "
            "figure is used as the bunkered amount; if both minimum and maximum are specified, the bunkered "
            "quantity defaults to the average of the two; a shore-measured quantity, once entered, always "
            "overrides either calculated estimate; and separately, the vessel's own figure is tracked in its own "
            "information field rather than blended into the calculation. Registering an actual delivery requires "
            "supplier details, at least one order line with fuel type/quantity/unit price, and the bunkered date "
            "— users in the Vessel security group submit this via Register Delivery in the action menu, "
            "optionally attaching the bunker delivery note itself.\n\n"
            "Service orders follow a simpler pattern: created either from the Operations menu (useful for "
            "entering several port costs across multiple port calls at once) or directly from a Port Call "
            "drawer's Service Orders tab, requiring only the standard fields plus at least one order line. Every "
            "service order created this way starts in Draft status specifically so it can be amended freely "
            "without impacting any other calculation until someone is ready to finalize it — a useful thing to "
            "tell a customer worried about \"locking in\" a service order too early."
        ),
    },
    {
        "title": "Laytime calculations & demurrage/despatch",
        "type": "a", "dur": 20, "prod": "vms",
        "description": "Tiered demurrage/despatch math, canal laytime as its own reversible calculation, and where the laytime drawer's fields live.",
        "learn_items": [
            "How tiered demurrage and despatch rates are actually calculated",
            "How canal laytime differs from regular port laytime",
            "Where to find the printable laytime statement",
        ],
        "rich_content": (
            "Tiered demurrage and despatch rates replace a single flat rate with progressive bands — demurrage "
            "tiers charge more as time exceeds laytime, despatch tiers credit more as cargo clears early. For a "
            "reversible laytime calculation, tiers apply across the total laytime for all cargo ports combined; "
            "for a non-reversible calculation, they apply separately per cargo port. A worked example makes the "
            "math concrete: with 4 days of demurrage split across two tiers — days 0–2 at 8,000 USD/day and days "
            "2–4 at 12,000 USD/day — the total comes to 16,000 plus 24,000, or 40,000 USD. The system enforces "
            "that the first tier always starts at zero and the last always ends at infinity, and adjusting one "
            "tier boundary automatically shifts the adjacent one.\n\n"
            "Canal laytime, available since release 8.10, is its own separate calculation layered on top of "
            "regular port laytime — time allowed and deductions registered for a canal passage do not affect "
            "laytime at any other port in the same voyage. Creating one requires selecting the canal plus at "
            "least one port before and after it (Suez between Bergen and Singapore, for instance); once added, "
            "the whole calculation becomes reversible, and the aggregation type cannot be changed again until "
            "every canal entry is removed. Time deductions inside a canal entry are added via the blue plus-icon "
            "in the timesheet's corner, including a dedicated days field for faster entry.\n\n"
            "For the calculation as a whole: opening a laytime record (new or existing) shows a details drawer "
            "whose Overview tab covers both the calculation itself and its cargo ports, and the laytime "
            "statement itself can be printed directly from the PDF icon in the top right of that drawer — the "
            "fastest way to hand a customer a document rather than walk them through the screen."
        ),
    },
    {
        "title": "Bill of lading & downtime (offhire)",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "How a BL pulls consignee/notify data from sub-cargo, and the two-tab shape of a downtime record.",
        "learn_items": [
            "Where a bill of lading's consignee and notify party actually come from",
            "The two tabs inside a downtime (offhire) record",
        ],
        "rich_content": (
            "Creating a bill of lading starts from the create icon on the Bills of Lading screen, then proceeds "
            "through vessel selection (typeahead, filters everything after), port call selection (the system "
            "shows discharge ports and the voyage reference for that vessel), and party information. The detail "
            "worth remembering here: Consignee and Notify Party are not typed fresh on the BL itself — they are "
            "pulled from sub-cargo-level data, meaning a wrong consignee on a printed BL is very often actually "
            "a wrong or missing value on the underlying sub-cargo record, not a BL-specific bug. Once the right "
            "sub-cargo entries are selected from the table, confirming in the modal creates the document.\n\n"
            "Downtime — the current name for what used to be called Offhire, since release 8.5 — follows the "
            "same drawer pattern as most VMS records: finding or creating one opens a details panel with two "
            "tabs. Overview handles the downtime record itself and its bunker consumption tracking; Various "
            "Cost/Revenue records whatever financial impact the downtime period carries. Status management, "
            "field-level detail, and deletion all live behind this same drawer, so a customer describing "
            "\"editing an offhire\" and one describing \"editing a downtime\" mean exactly the same screen."
        ),
    },
    {
        "title": "Vessel reports & the voyage analysis dashboard",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "The six vessel report types, and how the analysis dashboard's color coding flags deviation.",
        "learn_items": [
            "The six vessel report types and where they're created from",
            "What red, blue, and black mean on the analysis dashboard",
        ],
        "rich_content": (
            "Six report types cover a vessel's operational reporting: Arrival, Departure, Berth, and Unberth "
            "registrations mark specific port-call events; Noon Report is the standard daily operational report; "
            "and In Port Report covers reporting while a vessel remains in port. All six are created from the "
            "relevant port call maintenance screen rather than a single central form, so \"where do I create a "
            "noon report\" and \"where do I create an arrival report\" have the same answer: open the port call "
            "in question and pick the report type from there.\n\n"
            "The Voyage Analysis Dashboard exists specifically for senior managers and chartering staff who need "
            "day-to-day oversight across many voyages at once, rather than one voyage at a time. It generates "
            "daily snapshots automatically for active voyages and lets ship owners keep an early-warning eye on "
            "selected voyages across different operators. Its main display surfaces voyage figures and their "
            "deviations for voyages still awaiting operational closure, using a simple three-color system: red "
            "means the deviation has hurt the voyage result, blue means it has helped, and black means no "
            "impact either way — a quick visual triage tool worth pointing an operations-focused customer "
            "toward if they are manually checking voyages one by one for problems."
        ),
    },
    {
        "title": "Invoicing workflow",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "Assembling an invoice, why refreshing voyage data wipes manual edits, and how reversal works.",
        "learn_items": [
            "Why editing a document line before refreshing voyage data can lose your changes",
            "What blocks an invoice from being assembled or reversed",
            "The Document Assemble and Document Reverse permissions",
        ],
        "rich_content": (
            "Invoice assembly starts by editing individual document lines through a modal — changing a line's "
            "currency automatically fetches the current exchange rate for it. One behavior worth remembering "
            "before troubleshooting a \"my edits disappeared\" ticket: refreshing the underlying voyage or "
            "vessel data deletes every existing document line and regenerates them from scratch, wiping out any "
            "manual edits made beforehand. If a customer refreshed data after editing lines, that is very likely "
            "the explanation, not a bug.\n\n"
            "Assembling itself requires the Document Assemble permission: select the desired lines, click "
            "Assemble, and complete the pre-filled modal's mandatory fields. Two constraints apply — invoices "
            "cannot be assembled for voyages with Closed status at all, and posting dates earlier than the "
            "previous accounting month require an extra confirmation step. If the \"Autofill of External "
            "Document No in Assemble Modal\" setting is on and a Service Order is involved, that field "
            "auto-populates from the Service Order's own External Reference No.\n\n"
            "Reversing an assembled invoice needs the Document Reverse permission: open the invoice, click "
            "Reverse in the drawer's top right, enter a reason and posting date, and save. The reversal document "
            "generates automatically and moves straight to Ready for Posting — if the organisation has finance "
            "system integration enabled, it posts automatically from there. Two things block a reversal outright: "
            "an invoice already in \"Assembled\" or \"Pending\" type, or one tied to a voyage marked Closed."
        ),
    },
    {
        "title": "Accruals, bunker transactions & period-end closing",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "What generates an accrual, what excludes one, and how bunker transactions move between VMS and accounting.",
        "learn_items": [
            "The four conditions that exclude an accrual from being generated",
            "The three fields every accrual reversal carries",
            "How pending bunker transactions get posted",
        ],
        "rich_content": (
            "Accruals align a cost or revenue to the accounting period it was actually earned or incurred in, "
            "rather than the period it happened to be paid in. Generating them uses the Generate button on the "
            "Accruals table, opening a modal for month/year, company and business unit (at least one required, "
            "multiple allowed), vessel and voyage, and three checkboxes: Write All, Keep Estimates, and Create "
            "Voyage Snapshot. Every generated accrual is dated to the last day of the period, with a matching "
            "reversal entry dated the first day of the next period.\n\n"
            "Four conditions specifically exclude an accrual from generating at all, worth checking first "
            "whenever a customer expects one and does not see it: the voyage's progress status is Closed; "
            "\"Write All (Include Zero Accruals)\" is unchecked and the estimated amount equals the actual "
            "amount; the account's fulfillment level is zero; or the account is mapped to another account whose "
            "mapping has since been deleted. Accruals are also only ever generated for open voyages in the first "
            "place.\n\n"
            "Bunker Transactions run a parallel workflow for bunker-specific accounting, automating the transfer "
            "of accounting data whenever a bunker transaction posts. A Posted tab shows everything marked Posted "
            "or Ready For Posting; a Pending tab groups pending transactions by voyage, with expandable cards "
            "and multi-select posting via a confirmation dialog. Reversing a Ready for Posting or Posted "
            "transaction follows the now-familiar pattern: open the drawer, click reverse, give a reason and "
            "posting date, confirm the extra validation step if the date falls before the previous accounting "
            "month, and save to create the reversed record."
        ),
    },
    {
        "title": "Alerts & webhook subscriptions",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "How notifications get enabled, what an alert script actually needs, and what the AI Alert Generator does differently.",
        "learn_items": [
            "Why notifications are disabled until a user turns them on",
            "The three things every alert script must define",
            "The two output modes of the AI Alert Generator",
        ],
        "rich_content": (
            "Notifications are opt-in, not automatic — a user has to open their avatar menu, go to Account > "
            "Notification Settings, and pick at least one delivery channel (push, email, or both) before "
            "anything arrives. Worth remembering when a customer reports \"I'm not getting alerts\": the first "
            "check is whether they ever turned notifications on in the first place, not whether an alert script "
            "is broken. Once enabled, notifications collect in a bell-icon panel visible from any module, with "
            "an unread count and per-item read/unread marking.\n\n"
            "Alert scripts are the underlying automation, written in Groovy. Every script needs three things "
            "defined: an identity (name, unique code, description of what it monitors), a trigger (an object "
            "type like Voyage plus an event type like Update — multiple triggers can combine), and logic that "
            "reads the current object state via `dlpObject` and the previous state via `oldDlpObject`, always "
            "returning a boolean to say whether the alert condition is met. Good practice is to check the "
            "object's type early — something like `if (dlpObject instanceof Voyage)` — so the script fails "
            "gracefully rather than erroring when data is not what it expects. Beyond the boolean logic, a "
            "script also configures its message: subject line, output format (String, XML, or JSON), and whether "
            "the notification body is generated dynamically in the script or drawn from a fixed template.\n\n"
            "The Alert Generator is a newer, AI-assisted layer on top of all this: instead of writing Groovy "
            "directly, a user describes the condition they want in plain language, and the generator produces "
            "either just the script, or the script wired up as a complete Webhook Alert in one step. This is "
            "worth mentioning to a customer who finds writing conditional logic intimidating — they do not need "
            "to learn Groovy to get a working alert script anymore."
        ),
    },
    {
        "title": "Users, roles & security setup",
        "type": "a", "dur": 20, "prod": "vms",
        "description": "MFA options, how permissions/roles/groups relate, and the Data Control module's four-field structure.",
        "learn_items": [
            "The two MFA options VMS supports",
            "The relationship between security permissions, roles, and groups",
            "The four fields that define a Data Control",
        ],
        "rich_content": (
            "Two MFA paths exist for customers: integrating with their own Active Directory server, or using "
            "Auth0's Guardian app. Neither is VMS-native — both lean on infrastructure the customer already runs "
            "or a third-party provider, which is useful context when an MFA ticket is really an AD or Auth0 "
            "configuration question rather than a VMS bug.\n\n"
            "Security Permissions, Security Roles, and Security Groups form a layered access model. A Security "
            "Permission itself can be edited directly in its drawer's Main Details section, and a linked "
            "Security Roles tab shows which roles reference it — genuinely useful before deleting one, since "
            "the documentation explicitly warns that deleting a permission can strip access to pages or "
            "functions for whoever depended on it. Security Groups sit one level up: a group's drawer shows "
            "which Users carry that group and which Permissions it contains, and a group can be duplicated "
            "wholesale via a copy icon rather than rebuilt from scratch — useful when a new team needs "
            "\"almost exactly\" an existing group's access.\n\n"
            "Data Controls are a separate, more targeted mechanism for restricting which specific records a role "
            "can see, not just which pages. Configuring one means specifying four things: the Object being "
            "controlled (e.g. Voyage), the Attribute on that object that links it to a user, the Matcher Target "
            "(almost always User), and the Matcher Attribute Target — the field on the user being compared "
            "against. A documented example: a MASTER_ONLINE_VESSEL role restriction that lets a vessel's Master "
            "see only voyages assigned to them. Because a misconfigured Data Control can silently over- or "
            "under-restrict what a whole role of users sees, the documentation is explicit that new controls "
            "should be tested in a non-production environment before deploying to a live one — worth repeating "
            "to anyone asking to set one up directly on production.\n\n"
            "System Settings, finally, holds global defaults every user inherits: things like automatic pilot "
            "stations, percent extra at sea, whether future dates lock once modified, whether other users can "
            "edit an estimate voyage they did not create, and the EU ETS defaults (compliance penalty price, "
            "default currency) covered in more depth in the EU ETS module in Professional tier."
        ),
    },
    {
        "title": "Master data essentials",
        "type": "a", "dur": 20, "prod": "vms",
        "description": "Business partners with multiple types, company-level invoice preferences, EU ETS percentage tables, and the six various-item rules.",
        "learn_items": [
            "Why a business partner no longer needs duplicate records for multiple roles",
            "The two-step process to fully remove a business partner or company",
            "The six various-item calculation rules and what each applies to",
        ],
        "rich_content": (
            "Business Partners are created via the list's top-right create icon, requiring Business Partner "
            "Types, Name, Short Name, and Code before confirming. Since release 8.11, a single partner can carry "
            "multiple type assignments at once — a partner marked both Charterer and Agent now appears "
            "correctly in both selector categories without needing a duplicate record for each role, and the "
            "system actively prevents that same partner showing up twice in a list because of the double "
            "assignment. The Financial tab holds payment terms, baseline terms, default accounts, bank account "
            "management, and outstanding invoices. Removing a partner is deliberately two steps: disable it "
            "first via the options menu, then delete it in a second pass — a safeguard against accidental "
            "one-click removal.\n\n"
            "Companies follow a similar shape: created via a top-right icon requiring name and code, with an "
            "Overview tab covering registration number, VAT number, currencies, business units, and a Default "
            "Signee for electronic invoice signing. Company-level Invoice Preferences mostly affect the legacy "
            "invoice template — toggles for logo, header, and body sections controlling whether company name, "
            "address, external document numbers, IMO, and VAT numbers print on invoices. A company can only be "
            "deleted once disabled and once no voyages reference it — if voyages are still linked, the delete "
            "option is simply unavailable rather than throwing an error.\n\n"
            "EU ETS Compliance master data has two tables: a Compliance Percentage table for permanent tax "
            "percentages with a start date and an EU/EEA flag, and a Phase-In Period table for temporary "
            "percentages during the years before the regulation reaches full effect. Getting a customer's "
            "compliance number wrong on a specific voyage often traces back to one of these two tables rather "
            "than the voyage's own emissions calculation.\n\n"
            "Various Costs and Revenues follow a simple base formula — Amount = Quantity × Rate — applied "
            "through six distinct rules, each valid for different record types: Lumpsum (Voyage, Cargo, Downtime, "
            "Port Call), Cargo Quantity Based (Cargo only — recently renamed from \"Rate Based\"), Fixed Quantity "
            "(Voyage, Cargo, Downtime), Onhire Days (Voyage only), Per Day (Voyage, Cargo, Downtime, Port Call), "
            "and Percentage on Freight (Cargo only — recently renamed from plain \"Percentage\"). Knowing which "
            "rule a customer's various item uses is usually the fastest way to explain why its calculated amount "
            "looks the way it does."
        ),
    },
]

PRACTITIONER_QUIZ = [
    {
        "q": "In the 7-step ticket lifecycle, what should you write before starting investigation?",
        "explanation": "A one-sentence problem statement (\"Customer X cannot do Z; expected A, actual B\") is written during triage, before investigating.",
        "options": [
            ("The final resolution", False), ("A one-sentence problem statement", True),
            ("The escalation target", False), ("The invoice number", False),
        ],
    },
    {
        "q": "Which two fields are explicitly NOT updated by L1 during triage?",
        "explanation": "Billable and Time Remaining are excluded from L1 triage fields.",
        "options": [
            ("Assignee and Customer", False), ("Billable and Time Remaining", True),
            ("Request Type and Fix Versions", False), ("URL and Components", False),
        ],
    },
    {
        "q": "A customer's Azure AD login is failing (SSO/Entra ID issue). Who should this escalate to?",
        "explanation": "SSO/Entra ID login issues (SYS-03) escalate to the customer's own IT/Azure AD team.",
        "options": [
            ("The Infrastructure team", False), ("The customer's IT/Azure AD team", True),
            ("The Dataloy distance team", False), ("The DA Desk team", False),
        ],
    },
    {
        "q": "Why is the SLA & response times module currently just a placeholder?",
        "explanation": "Three conflicting SLA links exist in the Support space with no confirmed canonical source — teaching one would mean teaching an unresolved ambiguity.",
        "options": [
            ("VMS has no SLA", False),
            ("Three conflicting SLA sources exist and haven't been reconciled yet", True),
            ("SLAs vary too much by customer to document", False),
            ("It's covered fully in the Foundation tier already", False),
        ],
    },
    {
        "q": "What version threshold defines a 'small' upgrade eligible for self-service booking?",
        "explanation": "A small upgrade is any upgrade from an environment already on 8.17.0 or later.",
        "options": [
            ("8.0 or later", False), ("8.17.0 or later", True), ("8.25 or later", False), ("Any version", False),
        ],
    },
    {
        "q": "On the Cargo Management board, what does a blue timing indicator mean?",
        "explanation": "Blue indicates early timing; red indicates late; normal coloring means on-time.",
        "options": [
            ("Late", False), ("Early", True), ("Cancelled", False), ("On-time", False),
        ],
    },
    {
        "q": "Where do budgeted and template voyages appear in operational voyage lists?",
        "explanation": "They are deliberately invisible to operational voyage lists — they exist only within the Budgets module.",
        "options": [
            ("In the main Voyages list, flagged as budget", False),
            ("Nowhere — they're invisible to operational lists", True),
            ("Only in the FAS board", False),
            ("Only for Administrators", False),
        ],
    },
    {
        "q": "If shore-measured bunker quantity is entered, what happens to the calculated min/max estimate?",
        "explanation": "A shore-measured quantity always overrides the calculated min/max estimate.",
        "options": [
            ("It's averaged with the estimate", False), ("It overrides the calculated estimate", True),
            ("Both are kept and shown side by side", False), ("The order is rejected", False),
        ],
    },
    {
        "q": "What happens to manually edited document lines when voyage data is refreshed before assembly?",
        "explanation": "Refreshing voyage or vessel data deletes all existing document lines and regenerates them, wiping manual edits.",
        "options": [
            ("They're preserved automatically", False), ("They're deleted and regenerated from scratch", True),
            ("They're locked from further edits", False), ("Only the currency field resets", False),
        ],
    },
    {
        "q": "A bill of lading shows the wrong consignee. Where does that field actually come from?",
        "explanation": "Consignee and Notify Party are pulled from sub-cargo-level data, not entered directly on the BL.",
        "options": [
            ("Typed directly on the BL", False), ("Sub-cargo level data", True),
            ("The vessel record", False), ("The port call record", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# PROFESSIONAL TIER
# ─────────────────────────────────────────────────────────────────────────

PROFESSIONAL_MODULES = [
    {
        "title": "🚢 VOY — Voyage / CoA / Cargo Issues",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "The Training Hub playbook for voyage, CoA, and cargo diagnostics — CoA template propagation is the pattern that explains most of these.",
        "learn_items": [
            "Why a CoA template edit breaks more than one voyage at once",
            "How to fix cargo data that came from a template without breaking every other voyage",
            "When a VOY issue needs Development vs. when it's pure workflow education",
        ],
        "rich_content": (
            "The single idea that explains most VOY tickets: a Contract of Affreightment template and a voyage "
            "are not the same thing, and editing the template propagates to every voyage allocated from it. "
            "VOY-01 (cargo data incorrect or missing) and VOY-12/VOY-05 (CoA propagation issues) are really the "
            "same root cause wearing different symptoms — wrong cargo quantities, cargo not matching the fixture, "
            "or a customer saying \"I only wanted to change one voyage and now they've all changed.\" The fix in "
            "every case is the same: detach the voyage from the template (or convert it to standalone) before "
            "editing it, rather than editing the template itself when only one voyage should change.\n\n"
            "A second common VOY-01 cause worth checking early: a missing or incorrect Business Partner code on "
            "the charterer means the cargo simply won't show on the correct AR line, and one user unable to see "
            "cargo others can see is very often a Cargoes/Charterers security-group gap, not a data problem at "
            "all.\n\n"
            "VOY-13 covers schedule and ETA issues — dates not recalculating after adding or removing a canal, "
            "or after a speed change. The first thing to check is always whether the ETA/ETD fields are locked "
            "or manually overridden, since a locked date simply will not recalculate no matter what changes "
            "upstream. If the schedule looks structurally broken after a reschedule (duplicated or orphaned port "
            "calls), that is a Development escalation, not something to keep trying to fix by hand.\n\n"
            "VOY-06 (data corrupted after a vessel swap) is the one VOY scenario that always escalates, no "
            "exceptions: stop editing immediately, use Find Voyages with all filters cleared to locate what's "
            "actually there, and hand Development both voyage keys, both vessel keys, and the timestamp of the "
            "swap. Everything else in this playbook — reference number issues, port deletion blocks from linked "
            "service orders or laytime, validation errors on voyage creation — is workflow education first, "
            "escalation only if the documented resolution steps genuinely don't apply."
        ),
    },
    {
        "title": "⚙️ SYS — System Performance & Availability",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "The golden rule is check infrastructure first — and the one code (SYS-05) that always escalates immediately.",
        "learn_items": [
            "The difference in handling single-user vs. multi-user SYS issues",
            "Why SYS-05 always escalates with no support-side fix attempted",
            "What to check before blaming VMS for a login failure",
        ],
        "rich_content": (
            "For every SYS ticket, the first move is the same: check known infrastructure events before doing "
            "any client-side troubleshooting. If there's an active event, acknowledge the customer and share an "
            "ETA rather than spending time on browser-level fixes that won't touch the real cause.\n\n"
            "SYS-01 (VMS down or unresponsive) and SYS-02 (VMS slow) both hinge on scope: is this one user, or "
            "everyone on the instance? A single affected user usually resolves with client-side steps — hard "
            "refresh, clear cache and cookies, a different browser, disabling VPN or switching networks, and "
            "confirming they're on the correct (not an old bookmarked) instance URL. Multi-user or persistent "
            "issues go straight to Infrastructure with the instance name, timestamp, and number of users "
            "affected. For SYS-02 specifically, also check whether a large export or report is currently "
            "running, since that alone can make an entire instance feel sluggish without anything actually being "
            "broken.\n\n"
            "SYS-03 (login/authentication failure) is frequently not a VMS problem at all. A recently changed "
            "phone or reinstalled authenticator app means MFA re-enrolment, not a bug; repeated failed attempts "
            "trigger an account lockout fixable from the admin panel; and SSO/Entra ID redirect failures need "
            "the customer's own IT team to check Azure AD group membership — that escalation goes outward to the "
            "customer, not inward to Dataloy.\n\n"
            "SYS-05 (commit exception or application crash) is the one code in this entire playbook with no "
            "support-side resolution path at all: capture the full error text, the exact action that triggered "
            "it, and whether another user had the record open concurrently, then escalate to Development "
            "immediately. Do not attempt workarounds or repeat the action hoping it resolves itself — this "
            "category is, by design, not support-resolvable.\n\n"
            "SYS-04 (a single page or module stuck loading while the rest of VMS works fine) is usually a large "
            "dataset timing out — applying filters before the page loads, or clearing cache and trying another "
            "browser, resolves most cases. If one specific record reliably triggers the failure every time, that "
            "record's key is what makes the escalation actionable."
        ),
    },
    {
        "title": "🧾 INV — Invoicing, Service Orders & DA Integration",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "The core pattern (un-assemble, fix source, re-assemble), plus the two 'index out of bounds' codes that always escalate.",
        "learn_items": [
            "The un-assemble / fix source / re-assemble pattern for wrong invoice amounts",
            "Why 'Index out of bounds' errors should never be retried",
            "The four conditions that block accruals from generating",
        ],
        "rich_content": (
            "Most \"wrong amount\" invoicing tickets (INV-02) resolve with the same three-step pattern: "
            "un-assemble the invoice, fix whatever changed at the source (freight, various items, laytime), then "
            "re-assemble. The most common trap is a source edit made after assembly — the invoice keeps its "
            "stale figures until re-assembled, so \"I fixed the freight and the invoice still shows the old "
            "number\" almost always means the re-assemble step hasn't happened yet.\n\n"
            "INV-01 (accrual or time correction issues) has four specific conditions that will silently prevent "
            "an accrual from generating, all worth checking before assuming a bug: the voyage status is Closed "
            "(accruals only generate for Open voyages); an offhire record isn't marked \"Deduct Against Owner\"; "
            "estimated equals actual and \"Write All\" isn't enabled, so the accrual is correctly skipped as "
            "zero; or the relevant period is frozen, in which case regenerating won't touch it until it's "
            "unfrozen.\n\n"
            "INV-03 and BNK-04 (in the Bunker playbook) share the same underlying failure mode: an \"Index out of "
            "bounds\" error on service order or bunker order creation, almost always caused by a partial deletion "
            "sequence or a credit note/reversal that didn't fully complete, leaving an orphaned reference behind. "
            "The rule here is absolute: do not retry the creation, since it will not resolve an inconsistent "
            "backend state — capture the full sequence of what was attempted and escalate to Development for a "
            "direct repair.\n\n"
            "INV-10 covers DA Desk and webhook integration failures — a service order not syncing, a webhook not "
            "firing post-upgrade, or a status transition being blocked. Check the webhook subscription is active "
            "with the correct endpoint first, then get the actual failed payload from DA Desk to verify required "
            "fields are present, since a missing field in the payload is a more common cause than the webhook "
            "infrastructure itself being broken. Payload-specific problems escalate to the DA Desk team; systemic "
            "webhook or credential failures escalate to Development/Integration owners instead.\n\n"
            "Smaller, single-checklist codes round out the playbook: INV-04 (invoice stuck at Ready for Posting — "
            "check voyage status and the \"restrict self-assembled\" preference), INV-05 (filter problems — "
            "confirm which date field is actually being filtered on), INV-06 (PDF won't print — check popup "
            "permissions and that the invoice is actually assembled), INV-08 (missing bank details on a printed "
            "invoice — check the company/BP bank account setup), and INV-09 (a service order not reflecting on "
            "its port call — check it's above Draft status and linked to the right port call)."
        ),
    },
    {
        "title": "⛽ BNK — Bunker, ROB & Fuel Management",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "The golden rule — trace the chain to its earliest break — and the FIFO pricing behavior customers most often mistake for a bug.",
        "learn_items": [
            "Why bunker costs 'change' without anyone editing anything (FIFO)",
            "How to trace a ROB mismatch back to its actual source voyage",
            "Which BNK code always escalates immediately, and why",
        ],
        "rich_content": (
            "The golden rule for every BNK ticket: these are chain issues almost without exception, so the fix is "
            "tracing back to the earliest point where the ROB or delivery sequence actually broke, not treating "
            "each symptom independently. BNK-03 (ROB mismatch between one voyage's end and the next voyage's "
            "start) makes this explicit: work backwards voyage by voyage until you find the first one where the "
            "figures actually diverge, confirm that prior voyage is Fixed (the chain only connects through fixed "
            "voyages), and fix voyages in order from that earliest break forward — fixing a downstream voyage "
            "before the upstream one is fixed just recreates the same mismatch.\n\n"
            "BNK-02 (bunker price or cost looking wrong) is frequently not wrong at all — it's FIFO pricing "
            "working as designed, consuming the oldest delivery's price first. Before treating this as a defect, "
            "verify the order's currency is correct, explain FIFO consumption order to the customer if that's "
            "genuinely the explanation, and check for a vessel-level bunker category change (which, as covered "
            "in Foundation, retroactively affects every open voyage for that vessel).\n\n"
            "BNK-01 (consumption calculated incorrectly) usually traces to one of: the wrong consumption source "
            "selected (vessel default vs. TC In vs. a manual override), stale Speed & Consumption data on the "
            "vessel record, or a locked/overridden port call date blocking recalculation entirely.\n\n"
            "BNK-05 (bunker stock on redelivery incorrect) is commercially sensitive — a wrong redelivery ROB "
            "affects real money changing hands between owner and charterer — so trace the ROB chain from the "
            "prior voyage, confirm debunkering was actually recorded at the last port, and check for a bunker "
            "category naming mismatch (VLSFO vs. LSFO is a genuinely common one) before assuming the figure is "
            "simply wrong.\n\n"
            "BNK-04 (bunker order creation failing with \"Index out of bounds\") follows the same rule as its "
            "invoicing counterpart INV-03: never retry, capture the full order/invoice/credit-note/deletion "
            "sequence that led to it, and escalate to Development immediately for backend repair."
        ),
    },
    {
        "title": "📋 TC — Time Charter Hire, SOA & Off-Hire",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "Validate hire period dates and 'Deduct Against Owner' before recalculating anything — that single check resolves most of this playbook.",
        "learn_items": [
            "Why off-hire not reducing hire payable is almost always one checkbox",
            "What actually causes a blank Statement of Account PDF",
            "How to fix a hire statement that won't balance",
        ],
        "rich_content": (
            "The golden rule for this whole category: validate hire period dates and the offhire \"Deduct "
            "Against Owner\" flag before attempting any recalculation. TC-01 (off-hire calculation wrong or "
            "duplicated) is the clearest example — if hire isn't being reduced as expected, the first and most "
            "common cause is simply that \"Deduct Against Owner\" was never ticked on the downtime record. Beyond "
            "that single checkbox, check for a duplicate entry (manual plus imported), a date overlap with "
            "adjacent port calls, or incorrect TC hire period dates, then regenerate Time Correction after any "
            "fix.\n\n"
            "TC-03 (hire adjustment / hire payable issues, including a final statement that won't balance) "
            "extends the same logic: verify the TC contract's Duration and Rates periods and dates first, "
            "confirm offhire records fall in the correct period and carry the Deduct Against Owner flag, check "
            "that the actual redelivery date (not an estimated one) is what's driving the calculation, and if "
            "the owner changed mid-contract, confirm the Business Partner routing updated at the correct "
            "effective date rather than applying retroactively or too late.\n\n"
            "TC-02 (Statement of Account won't generate, or generates blank) has a short, mechanical checklist: "
            "confirm there are actually linked documents to include, set Currency in the print dialog (it's "
            "mandatory and easy to skip), and check that popups/downloads aren't blocked by the browser. A "
            "Statement showing both positive and negative demurrage/despatch lines is expected behavior, not a "
            "bug — the two post separately and only the net figure needs to reconcile.\n\n"
            "TC-04 (redelivery date wrong in the contract) is a short fix: update the date directly in the "
            "contract's Duration and Rates, verify the final voyage is actually configured as the Last TC "
            "Voyage, and regenerate both the hire statement and SOA afterward so they reflect the corrected date."
        ),
    },
    {
        "title": "⏱️ LAY — Laytime & Demurrage",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "If the laytime output is wrong, the cause is always in the inputs — terms, timestamps, rates, or deductions.",
        "learn_items": [
            "The four input categories to check before doubting a laytime calculation",
            "Why positive and negative AR lines for demurrage/despatch are expected",
        ],
        "rich_content": (
            "The golden rule here is worth repeating to every customer who reports a wrong laytime number: the "
            "calculation engine is not the problem, the inputs are. LAY-02 (laytime or despatch calculated "
            "incorrectly) breaks down into four things to check in order — laytime terms actually matching the "
            "charter party (SHINC, SHEX, and so on), the key timestamps being correct (NOR tendered, "
            "commencement, completion), each deduction entry being correctly typed and time-bounded (rain, "
            "waiting, shifting), and the demurrage rate itself matching the charter party rather than a stale "
            "override. For multi-port voyages specifically, also confirm whether the calculation is set up as "
            "reversible or non-reversible in line with the charter party terms — using the wrong one changes the "
            "math entirely.\n\n"
            "LAY-01 (demurrage rate incorrect) is the narrowest version of the same problem: check the rate on "
            "the cargo drawer's Main Details against the charter party, check for a calculation-level override "
            "sitting on top of it, and regenerate after correcting.\n\n"
            "LAY-03 covers a specific customer confusion rather than a real defect: demurrage posts to AR as a "
            "positive figure and despatch posts as negative, by design, so seeing both signs on the same "
            "statement is expected. The only thing worth verifying is that the net of the two matches the "
            "laytime calculation's own output — if it doesn't, the actual problem lives back in LAY-02's input "
            "checklist, not in how AR is displaying the sign.\n\n"
            "LAY-04 is a narrow UI quirk — a duplicated \"Laytime Commenced\" line in the timesheet — fixed by "
            "deleting the duplicate and keeping the correct timestamp; if it reappears, it's worth capturing the "
            "VMS version and raising it as a genuine bug rather than continuing to delete it manually each time."
        ),
    },
    {
        "title": "💰 FIN — Freight, Commission & P&L",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "The golden rule: percentage-based rules return zero when their base (usually freight) is zero or not yet entered.",
        "learn_items": [
            "Why commission or brokerage can be entirely missing from a P&L",
            "How to tell a real freight discrepancy from an unrefreshed screen",
        ],
        "rich_content": (
            "One rule explains the majority of FIN tickets: any percentage-based various item rule returns zero "
            "if its base — almost always freight — is itself zero or hasn't been entered yet. FIN-03 (brokerage "
            "percentage issues) and FIN-01 (commission missing or wrong on P&L) both start from the same "
            "checklist: confirm freight has actually been entered and is non-zero before assuming the brokerage "
            "or commission rule itself is broken. Beyond that, check the Various Rule's percentage and base are "
            "configured correctly, that a cargo-level rule's cargo is actually assigned to the voyage in "
            "question, that the broker's Business Partner code is correct if payments are posting to the wrong "
            "counterpart, and that there isn't a duplicate rule active for the same voyage type — duplicate "
            "rules are the most common cause of commission appearing to double.\n\n"
            "FIN-02 (freight amount or currency appearing to change on its own) usually has one of three "
            "explanations: an exchange rate update genuinely changed the converted value, the cargo's freight "
            "basis itself changed (flat rate to per-MT, for instance), or — the most common of the three — the "
            "screen simply hasn't been refreshed since a recalculation happened elsewhere. Checking exchange "
            "rate history and the cargo's freight basis first, then refreshing the page, resolves most of these "
            "without ever touching underlying data."
        ),
    },
    {
        "title": "🗺️ ROU — Routing & Distance",
        "type": "a", "dur": 12, "prod": "vms",
        "description": "The golden rule: distance data problems belong to the Dataloy distance team, not support — this playbook is mostly about triage, not fixing.",
        "learn_items": [
            "Why support can verify but not fix underlying distance data",
            "What to gather before escalating a routing issue",
        ],
        "rich_content": (
            "Every code in this playbook shares the same boundary: support can verify configuration and "
            "reproduce a problem, but cannot fix the underlying Distance API data itself — that always belongs "
            "to the Dataloy distance team. ROU-01 (wrong distance, or the distance table not loading at all) "
            "starts with verifying both ports' UNLOCODEs and confirming the route preferences (ECA avoidance, "
            "canal choices) match what's expected. If the distance itself looks wrong, the escalation package is "
            "specific and mechanical: the port pair by UNLOCODE, the distance the system actually returned, the "
            "distance expected, and the route preference settings in effect — without all four, the distance "
            "team can't reproduce the issue.\n\n"
            "ROU-02 (a canal addition or removal not updating downstream ETAs) is usually a locking problem "
            "rather than a distance-data problem: unlock any overridden ETA/ETD dates blocking recalculation, "
            "verify the canal port call's transit time, and trigger recalculation by saving or reloading the "
            "schedule. Only if distances are still wrong after that does it become a genuine data escalation.\n\n"
            "ROU-03 (ECA avoidance enabled but the route still crosses an ECA zone) has a short first check: "
            "confirm the ECA avoidance toggle is actually enabled on the specific legs in question before "
            "assuming the routing engine itself is at fault — a surprising number of these tickets resolve "
            "because the toggle was never turned on for that leg in the first place.\n\n"
            "For port additions or corrections (MDT-01, technically its own code but routing-adjacent), the same "
            "distance-team boundary applies: verify the UNLOCODE against an official source, search master data "
            "by partial name in case it exists under different spelling, and if it's genuinely missing, submit a "
            "request to the distance team with port name, UNLOCODE, country, and coordinates rather than trying "
            "to work around the gap."
        ),
    },
    {
        "title": "🌍 ENV/MDT/ACC — Compliance, Master Data & Access",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "Three different categories sharing one page: EU compliance calculations, port master data, and access/permission problems.",
        "learn_items": [
            "The four checks for a missing or incorrect EU ETS/FuelEU cost",
            "The one Data Control check for 'this user can't see voyages others can'",
            "Who owns port additions and UNLOCODE corrections",
        ],
        "rich_content": (
            "This playbook covers three genuinely different problem categories under one page. ENV-01 (FuelEU or "
            "EU ETS costs missing or wrong on a voyage) has four things to check in order: whether EU ETS is "
            "actually enabled and correctly flagged for that vessel/voyage's trading area; whether the cargo is "
            "classified into the correct FuelEU category; whether the ports involved are correctly marked EU "
            "versus non-EU, since that classification drives whether 50% or 100% of the obligation applies; and, "
            "for voyages crossing a year boundary, whether the customer's VMS version actually supports the "
            "correct statement logic across that boundary. If costs are missing at the pool level specifically, "
            "check that an Emission Pool exists and that the voyage in question has actually been included in "
            "it.\n\n"
            "MDT-01 (a port missing from the system, or showing the wrong UNLOCODE) starts with verifying the "
            "UNLOCODE against an authoritative external source and searching master data by partial name in case "
            "it exists under a different spelling than expected. Genuinely missing ports and UNLOCODE corrections "
            "escalate to the Dataloy distance team with name, UNLOCODE, country, and coordinates — but terminals "
            "and berths under an already-existing parent port can often be added directly by the customer's own "
            "admin, no escalation required.\n\n"
            "ACC-01 (a user can log in but can't see voyages, business partners, or whole modules that others "
            "can) is almost always a security configuration gap rather than a bug: check the user's assigned "
            "security group(s) first, then verify that group actually has permission to the relevant module or "
            "dataset, then check whether a Business Unit filter on the user is unintentionally excluding the "
            "records in question. For an urgent go-live blocker, the documented approach is to temporarily widen "
            "permissions to unblock the user immediately, then tighten them back down correctly afterward rather "
            "than leaving the fix half-done under time pressure."
        ),
    },
    {
        "title": "EU ETS & FuelEU compliance, in depth",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "The full multi-year regulatory arc, and where the two compliance master-data tables actually live.",
        "learn_items": [
            "The full EU ETS/FuelEU feature timeline from 6.28 to 8.29",
            "The two master-data tables that drive compliance percentages",
            "Why 'actual' vs. 'estimated' FuelEU values matter as of release 8.25",
        ],
        "rich_content": (
            "This is the single clearest multi-year feature arc in VMS's history, and worth knowing end to end "
            "since almost every EU ETS support ticket touches some part of it. It began with basic EU ETS "
            "compliance-percentage tracking at release 6.28, extended to port-call-level emissions calculation "
            "at 6.29, gained an automatic 5% ICE-class discount at 7.5, and reached full FuelEU GHG-intensity "
            "tracking integrated directly into voyage P&L at 8.3. An actual-values settlement tab arrived at "
            "8.23, the ability to override actual FuelEU costs while still retaining the original estimate for "
            "comparison came at 8.25, API access to the compliance balance followed at 8.26, and the most recent "
            "step — live emission-allowance pricing linked automatically to a voyage based on its start date — "
            "landed at 8.29.\n\n"
            "The master data behind all of this lives in two tables. The Compliance Percentage table holds "
            "permanent tax percentages, each with a start date and a flag for whether it applies inside the "
            "EU/EEA. The Phase-In Period table holds temporary percentages that step up year by year until the "
            "regulation reaches full effect (100%). A customer's compliance number looking wrong on a specific "
            "voyage traces back to one of these two tables far more often than to the voyage's own emissions "
            "math — check the tables before assuming the calculation itself is broken.\n\n"
            "The distinction introduced at 8.25 — actual FuelEU values now driving P&L, with the original "
            "estimated values retained only for reference — is the single most important recent change to "
            "understand, since it directly affects integrations like Prosmar and explains why a voyage's "
            "emissions cost can genuinely differ from what an earlier estimate showed. This is expected "
            "post-8.25 behavior, not a data inconsistency, and is worth explaining in exactly those terms to a "
            "customer comparing an old estimate against a current invoice."
        ),
    },
    {
        "title": "Claims management",
        "type": "a", "dur": 12, "prod": "vms",
        "description": "Where claims live in the module structure, and how creation connects to the drawer.",
        "learn_items": [
            "Where the Claim module sits and what its list supports",
            "The two-step creation flow: modal, then drawer",
        ],
        "rich_content": (
            "Claims live in their own dedicated module in the sidebar, listing every available claim with the "
            "same grid functionality as everywhere else in VMS — sorting, filtering, aggregation, column "
            "resizing. Creating a claim starts with the create icon in the top right, which opens a modal for "
            "the claim's essential fields (both required and optional); once that initial submission completes, "
            "the full Claim drawer opens for everything beyond the basics — cause, nature, related invoicing, "
            "and time-bar tracking.\n\n"
            "This module was introduced as a whole at release 8.8, alongside dedicated master data for claim "
            "types, causes, and natures, an Insurance Policies module for tracking P&I policies and "
            "deductibles, and claim-related invoicing that flows through the same AP/AR mechanisms as other "
            "financial documents. A claim question that seems to be about \"why can't I categorize this claim "
            "correctly\" is very often really a master-data question — whether the right claim cause or nature "
            "exists yet in the Claims master data setup, rather than something wrong with the claim record "
            "itself."
        ),
    },
    {
        "title": "Financial derivatives & OPEX",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "Two of the most recently added business modules — bunker hedges/FFAs, and end-to-end operating expenditure.",
        "learn_items": [
            "What a derivative represents in VMS, and the three types it supports",
            "How OPEX inherits from vessel type down to voyage",
        ],
        "rich_content": (
            "Financial Derivatives, introduced at release 8.26, let a customer create, copy, and manage "
            "derivative contracts — bunker hedges, Forward Freight Agreements, and emission allowances — "
            "directly inside VMS rather than tracking them in a separate spreadsheet. Voyages can be linked to a "
            "specific derivative period, which is what makes risk tracking meaningful: a customer can see which "
            "actual voyages a given hedge or FFA is meant to be covering, rather than treating the derivative as "
            "a standalone financial instrument disconnected from operations.\n\n"
            "OPEX (covered at data-model level in Foundation tier) gets its full end-to-end treatment at release "
            "8.27: automatic calculation based on voyage duration, with values inheriting down a clear chain from "
            "Vessel Type, to an individual Vessel's own override list, to the specific Voyage's stamped copy. "
            "Deductions during offhire periods, dedicated accounting transactions, and a full voyage-analysis "
            "breakdown of OPEX are all part of this same release. A ticket asking why a voyage's OPEX figure "
            "doesn't match expectations should be traced up this same inheritance chain — vessel type default, "
            "then vessel-level override, then whatever was stamped onto the voyage itself — exactly the same "
            "diagnostic pattern used everywhere else in VMS where a value can be set at multiple levels."
        ),
    },
    {
        "title": "Dataloy Distance Table (DDT) & routing",
        "type": "a", "dur": 12, "prod": "vms",
        "description": "The scale of the distance database, and the six-step process for adding a custom routing point.",
        "learn_items": [
            "The scale of DDT's port and route-segment coverage",
            "The six-step process for adding a routing point to a route",
            "Where to send a request for a genuinely missing port or routing point",
        ],
        "rich_content": (
            "Dataloy Distances covers roughly 11,000 ports and maritime locations, with distances derived from "
            "analysis of over a million route segments, and automatically routes around Emission Controlled "
            "Areas and High-Risk Areas by default — updated daily. By default it calculates the shortest "
            "commercially viable route, but since vessel sizes and voyage requirements vary, that default route "
            "can be customized by adding intermediate ports, inserting specific routing points, choosing "
            "particular canals, or entering custom latitude/longitude coordinates directly.\n\n"
            "Adding a routing point follows a consistent six-step flow: search by name or use the interactive "
            "map, click Show Ports to reveal routing points visible at the current zoom level, hover or click "
            "the point of interest to see its info popup (name, code, details), select it from the dropdown that "
            "appears when typing its name or code, confirm with Add or Enter, then drag the newly added point "
            "into its correct position in the route sequence. Forty standard routing points ship with the "
            "system already — the major canals (Panama, Suez, Kiel), key straits (Singapore, Torres, Bering), "
            "and passages specifically used to route around piracy zones, conflict areas, and ECAs.\n\n"
            "For genuinely missing ports, irregular routing that doesn't match expectations, or requests for new "
            "routing points entirely, the documented contact is ddt@dataloy.com directly — this is squarely "
            "outside what support can configure or fix from within VMS itself, consistent with the ROU playbook's "
            "boundary that distance data issues belong to the distance team, not support."
        ),
    },
    {
        "title": "Fleet Allocation & Scheduling (FAS) module",
        "type": "a", "dur": 12, "prod": "vms",
        "description": "What makes a voyage or vessel eligible to appear in FAS, and how a commitment gets created from the Java client.",
        "learn_items": [
            "The two conditions a vessel must meet to be schedulable in FAS",
            "The three FAS planning board views",
            "How a commitment is created via Booking and Operations",
        ],
        "rich_content": (
            "FAS lets schedulers work with voyages still in a planning phase and assign them to vessels before "
            "they become firm commitments. Eligible voyages must be Scheduled (Unallocated), Scheduled "
            "(Allocated), or Nominated, and must be ongoing or lie in the future — anything already closed out "
            "simply won't appear. Vessels have their own eligibility rule: a vessel must be flagged Schedulable "
            "in its master data and carry either an empty FleetExitDate or one still in the future. A vessel "
            "meeting both conditions but without any scheduled voyages yet stays available for allocation and "
            "scenario planning, even though it won't necessarily show up in every board view.\n\n"
            "The three planning boards covered in Practitioner tier — Open Positions, Cargo Management, and the "
            "Gantt-style Scheduler — all live under this same Fleet Plans umbrella, and all read from whichever "
            "scenario is currently selected. The MASTER scenario specifically reflects the live, current fleet "
            "plan and integrates directly with the rest of VMS; any other scenario is a sandbox for exploring "
            "alternatives before they're implemented for real.\n\n"
            "A commitment — the FAS term for an unallocated voyage sitting in the planning pipeline — is created "
            "from the older Java client (JVMS) rather than the web app: Booking and Operations module, then "
            "Voyage → New → Unallocated Voyage, specifying the vessel, trade pattern, and ports for the "
            "itinerary. Once created, it surfaces as a commitment inside FAS and can also be found back in the "
            "Booking and Operations module's Unallocated section — worth knowing since a customer who can't find "
            "where they created a commitment is very likely looking in the web app rather than JVMS, where the "
            "creation flow itself actually lives."
        ),
    },
    {
        "title": "API fundamentals",
        "type": "a", "dur": 20, "prod": "vms",
        "description": "What the API is for, OAuth 2.0 authentication, filtering syntax, and pagination.",
        "learn_items": [
            "Why the API exists — the integration problem it solves",
            "The exact OAuth 2.0 token request/response shape",
            "The filter syntax and its 16 operators",
            "How pagination and the noCount performance flag work together",
        ],
        "rich_content": (
            "The Dataloy REST API exists to solve a specific, common problem: most organisations run several "
            "applications that don't naturally talk to each other, and the API lets those systems exchange data "
            "with VMS — retrieving, updating, and creating records — rather than requiring manual re-entry "
            "between disconnected tools. It follows standard REST principles specifically so it's straightforward "
            "to write against and simple to test.\n\n"
            "Authentication uses OAuth 2.0. A client requests an access token via a POST carrying client_id, "
            "client_secret, audience, and grant_type set to \"client_credentials\" — the audience value differs "
            "by environment: https://dataloy for production, https://dataloy.dev for test/development. A "
            "successful response returns a JWT access_token, token_type \"Bearer\", and an expires_in typically "
            "of 86400 seconds. That token then travels as an Authorization: Bearer header on every subsequent "
            "call. Clients should reuse a valid token rather than fetching a new one per request; once a token "
            "expires, the server responds with HTTP 401 and the message \"Token expired,\" which is the client's "
            "cue to request a fresh one.\n\n"
            "Filtering uses a uniform syntax across every resource: ?filter=<property>(OPERATOR)<value>, for "
            "example Currency?filter=currencyCode(EQ)USD. Sixteen operators are supported, covering equality "
            "(EQ, NE), numeric/date comparison (GT, GTE, LT, LTE), set membership (IN, NOTIN), pattern matching "
            "(LK, LKIC, NLK, NLKIC), and null checks (NULL, NOTNULL). Numbers use a dot for decimals, dates "
            "follow yyyy-MM-ddTHH:mm:ss, strings only need quotes if they contain spaces, and booleans are "
            "expressed as 0/1. Multiple filters chain with additional &filter= parameters, and nested properties "
            "are reachable via dot notation like commodity.commodityCode(EQ)10000. Filtering is not available on "
            "the self or remarks properties, plus a handful of resource-specific exceptions.\n\n"
            "Pagination uses pageNumber and limit query parameters — ?pageNumber=1&limit=10 returns the first "
            "page of up to 10 records — and every response carries a totalObjectsNumber header with the full "
            "matching count across all pages. Since release 5.18, sending the header noCount = YES skips that "
            "total-count calculation entirely, which is worth knowing as a straightforward performance win for "
            "any integration that doesn't actually need the total, especially against a large result set."
        ),
    },
    {
        "title": "Webhooks, master data objects & audit log",
        "type": "a", "dur": 15, "prod": "vms",
        "description": "How webhook event types are structured, when a subscription gets auto-deactivated, and how master data soft-deletes.",
        "learn_items": [
            "The event-type naming pattern and what triggers auto-deactivation",
            "Why Remarks changes never generate a webhook",
            "How isObjectActive controls master data visibility",
        ],
        "rich_content": (
            "A webhook subscription targets an event type built from resource name, operation, and an optional "
            "object key — Cargo.C for any cargo creation, or Voyage.U.793628 for updates specifically on that one "
            "voyage. When a matching change happens, Dataloy POSTs the event to the subscriber's endpoint, which "
            "must respond with a 200-level status; if the subscriber is unreachable or too slow, the server "
            "retries five times at one-minute intervals before deactivating the subscription permanently — it "
            "cannot be reactivated afterward, only recreated. One limitation worth remembering when a customer "
            "asks why they're not getting notified of a Remarks change specifically: Remarks are explicitly "
            "excluded from the webhook process entirely, by design, not as a bug.\n\n"
            "Several version-gated refinements are worth knowing when troubleshooting an older integration: "
            "email delivery via a channelInfo/EMAIL channel type and JSON payload trimming both arrived at API "
            "3.16 alongside onlyMainObject (restricting notifications to only the primary subscribed object); "
            "rawObject (sending the object unencrypted, without its usual envelope) came at 5.23; XSL "
            "transformation support (Enterprise API only) at 5.24; and notSendMyChanges, which stops a user "
            "receiving notifications for their own edits, at 6.44. The REST interface for subscriptions supports "
            "the full set of GET/POST/PUT/DELETE, with authentication via webhookUsername and webhookPassword.\n\n"
            "Master Data objects use a soft-delete pattern built around the isObjectActive property: sending a "
            "PUT with {\"isObjectActive\": false} deactivates a record, and Master Data objects must be "
            "deactivated before they can be deleted at all. Deactivated records disappear from a standard list "
            "query by default, but remain fully retrievable two ways — filtering the list explicitly with "
            "isObjectActive(EQ)false, or fetching the specific object directly by its key regardless of active "
            "status. This is the mechanism behind \"why can't I find this business partner in the list anymore\" "
            "— it almost always means the record was deactivated, not deleted, and is still there if queried "
            "directly."
        ),
    },
    {
        "title": "Accounting Integration API",
        "type": "a", "dur": 18, "prod": "vms",
        "description": "What flows automatically in each direction between VMS and an accounting system, and the four-step autopost-invoice sequence.",
        "learn_items": [
            "What transfers from VMS to accounting vs. accounting back to VMS",
            "The exact four API calls needed to post an invoice end to end",
        ],
        "rich_content": (
            "The accounting integration exists to remove manual re-entry between VMS and a customer's finance "
            "system, and it moves data in both directions. From VMS outward: sales and purchase invoices "
            "transfer automatically upon posting, bunker transactions transfer once posted, vessel/voyage data "
            "can be scheduled to transfer ahead of either of those, and accruals move across specifically during "
            "period-end closing. From accounting back into VMS: receipts and payments arrive either on user "
            "trigger or a scheduled task, exchange rates update the same way, and actuals data comes back as "
            "part of the same period-end-closing process.\n\n"
            "Posting an invoice programmatically is a specific four-call sequence. First, generate invoice "
            "lines by posting a refresh request using voyage keys obtained via GET on PortCall, ServiceOrder, or "
            "BunkerOrder — this generates the actual document lines for accounts payable. Second, optionally "
            "query the invoiceDefaults endpoint to pre-fill fields like bank account and issuing company, "
            "skippable if that data is already known by the caller. Third, submit an assemble request; the "
            "mandatory fields here are documentText, documentDate, issuingCompany, bankAccount, baseLineDate, "
            "baseLineTerms, dueDate, paymentTerms, and percentage — with the rule that a single payment term "
            "entry is required whenever percentage equals 100%, and that baseline/payment terms codes must "
            "match whatever the specific customer's agreement actually specifies. This step returns a Document "
            "key. Fourth and finally, a PUT request sets invoicingStatus to \"RFP\" (Ready For Posting), which "
            "triggers the accounting-system transfer described above. Skipping or misordering any of these four "
            "steps is the most common cause of an integration silently failing to produce a usable invoice on "
            "the accounting side."
        ),
    },
    {
        "title": "Other integration APIs",
        "type": "a", "dur": 20, "prod": "vms",
        "description": "The Schedule API's voyage/cargo/port-call endpoints, and the Market Index API's two-entity structure.",
        "learn_items": [
            "The core Schedule API operations for voyages, cargo, and port calls",
            "Why only TC Rate indices support automatic calculation via the Market Index API",
        ],
        "rich_content": (
            "The Schedule API is built around three resources. POSTing to /Voyage with vessel, ballast port, and "
            "cargo information creates a new voyage, which the system assigns Estimated (EST) status by default. "
            "POSTing to /Cargo establishes a shipment with load/discharge ports, quantity, freight rate, and "
            "commodity, and a PUT to /Cargo/{KEY} adds further load or discharge ports to an existing shipment "
            "rather than requiring it be recreated. Port calls carry EventLogDates for arrival, berthing, "
            "unberthing, and departure, and a PUT to /EventLog/{KEY} is how a historical date gets corrected "
            "after the fact. A documented worked example — nominating an estimate voyage — shows the actual "
            "pattern: first retrieve the vessel's fleet plan to get the latest sequence number, then PUT an "
            "incremented sequence value along with isEstimate and a status change from EST to NOM.\n\n"
            "The Market Index Integration API solves a narrower problem: feeding continuously updated market "
            "rates into VMS so hire calculations update automatically instead of requiring manual entry. As of "
            "now, only TC Rate type indices actually drive automatic calculation — every other index type is "
            "informational only, which is worth setting expectations on if a customer expects an integration to "
            "auto-calculate against a non-TC-Rate index. The data model is simple: a MarketIndex holds a name, a "
            "unique code, and a collection of MarketIndexValues, where each value carries a validity date range, "
            "a current-or-archived status, and the numeric rate itself.\n\n"
            "The Bunker Order Integration API and Service Order Integration API and Vessel Report integration "
            "guides follow the same general integration shape as the others covered here — resource-specific "
            "create/update endpoints layered on the same REST conventions (auth, filtering, pagination) already "
            "covered in API fundamentals — but at time of writing carry less standalone documented detail than "
            "Schedule or Market Index; when a genuinely detailed question comes in about one of these "
            "specifically, it's worth checking the live docs.dataloy.com page directly rather than relying on "
            "secondhand notes, since the page itself is fairly thin as an index rather than a full spec."
        ),
    },
    {
        "title": "Enterprise functionality & advanced queries",
        "type": "a", "dur": 25, "prod": "vms",
        "description": "Endpoint/field-level access control, alert scripts, bulk update via API, websockets, and aggregate functions.",
        "learn_items": [
            "How endpoint access control works at both the endpoint and field level",
            "The bulk-update endpoint's key-list and expression-based modes",
            "The six aggregate functions and their constraints",
        ],
        "rich_content": (
            "Enterprise Functionality covers the deeper, integration-focused half of the API that most customer "
            "questions never touch, but which explains a lot of \"why does this API call get rejected\" "
            "tickets. Endpoint Access Control works at two levels: a user must belong to a Security Role holding "
            "a Security Permission for the endpoint itself (something like Vessel.GET), and even with endpoint "
            "access granted, requesting a field the role isn't authorized for triggers an HTTP 401 on that field "
            "specifically — some \"minimal view\" fields like vesselName typically stay accessible regardless. "
            "Webhook subscriptions inherit this same restriction: a user can only subscribe to an object type if "
            "they can already access its endpoint. Configuring this from scratch means POSTing an Endpoint "
            "(resourceName, path, httpMethodType), a SecurityPermission linked to it, a SecurityRole, then "
            "wiring permissions to roles and roles to users via their own linking endpoints.\n\n"
            "Alert Scripts at the Enterprise level are pseudo-Java programs evaluated at runtime, returning true "
            "to trigger a webhook/websocket message or false to suppress it, comparing old and new object state "
            "and populating message parameters as ?1, ?2, and so on. Several are effectively pre-built and worth "
            "recognizing by name: Bunker Price and Bunker Quantity scripts watch for unit-price or quantity "
            "changes on bunker order lines; Bunker Date watches delivery date changes; Offhire Start Date "
            "validates that offhire periods fall within voyage boundaries, timezone-aware; Days in Port Updated "
            "fires when a port duration shifts by more than a day; and ETA Outside Laycan flags cargo arrivals "
            "deviating from the laycan window, reporting whether the deviation is early or late.\n\n"
            "Bulk Update via the API uses PUT to /ws/rest/{Resource}/bulkUpdate?key={key1}&key={key2}... with the "
            "changes in the request body, returning 204 on success with no content — and can equally target "
            "records by an expression (?expression=ballastPort.isCanal=true) instead of an explicit key list, "
            "letting a single call modify every record matching a condition rather than requiring the caller to "
            "already know each key. This works against effectively any object in the data model.\n\n"
            "Websockets mirror webhook functionality for real-time, connection-based updates rather than "
            "callback POSTs — one endpoint per object type/event/key subscription, another for subscribing "
            "directly to a named Alert Script's true/false result — and support the same JSON field "
            "customization as webhooks, with an empty {} resetting back to default fields.\n\n"
            "Aggregate Functions let a caller get statistics without pulling every record: POST to "
            "/ws/rest/{Resource}/aggregate with avg, sum, min, or max (numeric fields only), count (any field, "
            "or * for all records), or list (unique values as an array, any field). Standard filters and "
            "expressions apply before the aggregation runs, letting a caller scope the calculation precisely — "
            "though date fields specifically are not supported for min/max, and numeric operations naturally "
            "reject text fields with an HTTP 400."
        ),
    },
    {
        "title": "Case study: tracing a real ticket end-to-end",
        "type": "a", "dur": 25, "prod": "vms",
        "description": "A composite ticket that touches ticket process, the Fixtures/relet data model, bunker chain tracing, and API-level root cause.",
        "learn_items": [
            "How the ticket lifecycle, escalation checklist, and playbooks combine on a real ticket",
            "Why the fixture/relet architecture matters even for a 'simple' bunker discrepancy",
        ],
        "rich_content": (
            "A customer reports: \"Voyage V-20458's redelivery bunker figure doesn't match what we agreed with "
            "the owner, and it's affecting a relet cargo on the same voyage.\" Walking this through every layer "
            "covered across this course shows how the pieces actually connect in practice.\n\n"
            "Triage (Practitioner tier, ticket lifecycle step 1) starts with the problem statement: \"Customer X "
            "expects redelivery ROB of Y on voyage V-20458; actual shown is Z.\" Step 3, search first, turns up "
            "nothing similar in prior tickets, so this moves to genuine investigation.\n\n"
            "This is a BNK-05 scenario (Professional tier, BNK playbook): bunker stock on redelivery incorrect. "
            "Per that playbook's checklist, the fix starts by tracing the ROB chain backward through prior fixed "
            "voyages, not by editing the figure directly on this voyage. Applying BNK-03's broader chain-tracing "
            "rule, the actual break turns out to be two voyages earlier, where a debunkering event was never "
            "recorded at the final port before redelivery.\n\n"
            "Here's where the Fixtures & relet module (Foundation tier) becomes directly relevant rather than "
            "background trivia: because this voyage carries a relet cargo, and relet cargoes automatically "
            "sync certain fields with their original cargo (a behavior built on the 7.1 fixture data model), "
            "correcting the bunker figure on the original voyage needs to be checked against the relet cargo "
            "afterward to confirm the sync actually propagated the fix rather than leaving the relet side "
            "stale.\n\n"
            "Once the missing debunkering entry is added and the chain is re-verified forward voyage by voyage, "
            "the investigation notes (ticket lifecycle step 5) record exactly this: which voyage broke the "
            "chain, what was missing, and that the relet cargo's synced fields were confirmed correct afterward. "
            "No escalation was needed here — this resolved entirely within the BNK-05 checklist — but had the "
            "chain looked structurally broken rather than simply missing one entry, this would have escalated "
            "to Development per BNK-04's \"never retry, capture the sequence\" rule instead.\n\n"
            "Step 7, documentation, captures the reusable pattern for the next person: \"redelivery ROB mismatch "
            "on a voyage with an active relet — check the debunkering trail first, then verify the relet cargo's "
            "synced fields after any correction.\" That one sentence, sitting in Jira's internal notes, is what "
            "turns a 45-minute investigation into a 5-minute one the next time this exact pattern shows up."
        ),
    },
]

PROFESSIONAL_QUIZ = [
    {
        "q": "A customer says editing one voyage from a CoA template changed several other voyages too. What's the fix?",
        "explanation": "CoA template edits propagate to all allocated voyages by design; detach/convert the one voyage to standalone before editing it alone.",
        "options": [
            ("This is a bug — escalate immediately", False),
            ("Detach the voyage from the template before editing it", True),
            ("Delete and recreate the CoA", False),
            ("Nothing can be done — this is permanent", False),
        ],
    },
    {
        "q": "Which SYS code always escalates to Development with no support-side fix attempted?",
        "explanation": "SYS-05 (commit exception/application crash) is explicitly not support-resolvable — capture details and escalate immediately.",
        "options": [
            ("SYS-01 (VMS down)", False), ("SYS-02 (VMS slow)", False),
            ("SYS-05 (commit exception)", True), ("SYS-03 (login failure)", False),
        ],
    },
    {
        "q": "An 'Index out of bounds' error appears when creating a bunker order or service order. What should you do?",
        "explanation": "Never retry — this indicates an inconsistent backend state (often from an incomplete deletion/credit-note sequence) and needs Development repair.",
        "options": [
            ("Retry the creation a few times", False), ("Never retry — capture the sequence and escalate to Development", True),
            ("Delete the voyage and recreate it", False), ("Wait 24 hours and try again", False),
        ],
    },
    {
        "q": "Why might brokerage or commission show as zero on a voyage P&L even with a correctly configured rule?",
        "explanation": "Percentage-based various item rules return zero if their base (usually freight) is zero or not yet entered.",
        "options": [
            ("The rule is always broken in this case", False),
            ("Freight (the rule's base) hasn't been entered yet", True),
            ("Commission rules don't work on P&L", False),
            ("It only shows after period-end closing", False),
        ],
    },
    {
        "q": "Off-hire isn't reducing hire payable on a TC voyage. What's the first thing to check?",
        "explanation": "The most common cause is the 'Deduct Against Owner' flag not being ticked on the downtime record.",
        "options": [
            ("The TC contract's rate", False), ("Whether 'Deduct Against Owner' is ticked on the downtime record", True),
            ("The vessel's speed and consumption data", False), ("The invoice currency", False),
        ],
    },
    {
        "q": "Who owns fixing genuinely wrong distance data between two ports?",
        "explanation": "Distance API data issues always belong to the Dataloy distance team — support can verify but not fix the underlying data.",
        "options": [
            ("Support fixes it directly in master data", False), ("The Dataloy distance team", True),
            ("The Development team", False), ("The customer's IT team", False),
        ],
    },
    {
        "q": "What data-model change did release 7.1 introduce that the Fixtures module covers?",
        "explanation": "7.1 introduced a dedicated fixture table with a direct cargo-to-fixture link.",
        "options": [
            ("The claims module", False), ("A dedicated fixture table with direct cargo-to-fixture linking", True),
            ("EU ETS compliance", False), ("The OPEX hierarchy", False),
        ],
    },
    {
        "q": "As of release 8.25, what actually drives a voyage's FuelEU cost in P&L?",
        "explanation": "Actual (not estimated) FuelEU values now drive P&L as of 8.25, with the original estimate retained only for reference.",
        "options": [
            ("Only the original estimated value", False), ("Actual values, with the estimate kept for reference", True),
            ("Whichever value is higher", False), ("An average of estimate and actual", False),
        ],
    },
    {
        "q": "In the Dataloy REST API, what does sending the header 'noCount = YES' do?",
        "explanation": "Available since release 5.18, it skips the total-object-count calculation for a performance improvement.",
        "options": [
            ("Disables pagination entirely", False), ("Skips calculating the total object count for performance", True),
            ("Returns only inactive objects", False), ("Doubles the page size", False),
        ],
    },
    {
        "q": "Why does a webhook subscription never fire for a change to an object's Remarks field?",
        "explanation": "Remarks are explicitly excluded from the webhook process by design — this is not a bug.",
        "options": [
            ("It's a bug that needs escalating", False), ("Remarks are explicitly excluded from webhooks by design", True),
            ("Remarks require a separate subscription type", False), ("Only Enterprise API supports this", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# ROLE ASSEMBLY
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
        {
            "label": "Practitioner",
            "name": "VMS Support Practitioner",
            "cert_name": "VMS Support — Practitioner",
            "modules": PRACTITIONER_MODULES,
            "quiz": PRACTITIONER_QUIZ,
        },
        {
            "label": "Professional",
            "name": "VMS Support Professional",
            "cert_name": "VMS Support — Professional",
            "modules": PROFESSIONAL_MODULES,
            "quiz": PROFESSIONAL_QUIZ,
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
