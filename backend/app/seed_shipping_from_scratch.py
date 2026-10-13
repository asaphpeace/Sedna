"""Seed the "Shipping from Scratch" learning path.

Source: Becki's "Shipping from Scratch · Sedna VMS Industry Knowledge" guide
(written with Nassia). One lesson per guide topic, grouped into four tiers in
the guide's order, plus the guide's glossary as a reference lesson. Each tier
ends in a short quiz.

Corrections applied to the source text, pending Becki's sign-off:
  - Panama Canal new locks take ~51.25m beam; "post-Panamax" refers to the old locks
  - "The flat" is the published WS 100 rate, not the agreed percentage
  - LR2 is 80–160k DWT (Aframax 80–120k) — the guide used both ranges
  - EU ETS covers methane and N2O from 2026, not 2024
  - The Mediterranean ECA has applied since 1 May 2025

Purely additive, like seed_onboarding.py: creates the path if missing and
adds any tier (by label) that doesn't exist yet. Safe to re-run.

Run once via:
    docker compose exec backend python -m app.seed_shipping_from_scratch
"""
import asyncio
from textwrap import dedent

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine, Base
from app.models import *  # noqa: F401,F403 — registers all models with Base


def md(text: str) -> str:
    return dedent(text).strip()


# ─────────────────────────────────────────────────────────────────────────
# TIER 1 — THE INDUSTRY (topics 01–05)
# ─────────────────────────────────────────────────────────────────────────

TIER1_MODULES = [
    {
        "title": "Shipping in Short: How Money Is Made and Where It Goes Wrong",
        "dur": 8,
        "description": "About 90% of internationally traded goods move by sea. How operators make money, and why it is so easy to lose.",
        "learn_items": [
            "The basic operator–charterer model and where revenue comes from",
            "The four levers of voyage profit",
            "The three ways voyages lose money, and the gap Sedna VMS closes",
        ],
        "rich_content": md("""
            About 90% of everything traded internationally moves by sea. The companies that move it run some of the most capital-intensive, operationally complex businesses in the world. Understanding how they make money — and why it's so easy to lose it — is the foundation for everything else in this path.

            ## The basic model

            A **ship operator** controls one or more vessels and uses them to transport cargo for customers called **charterers**. Revenue comes from freight — a rate agreed per tonne of cargo, or a daily hire rate for the use of the vessel. Against that revenue, the operator pays bunkers (fuel), port costs, canal dues, commissions, and — if they've hired the vessel from a third-party owner — daily hire.

            The gap between what a voyage earns and what it costs is the voyage profit. Multiply this across a fleet of 20, 50 or 100 vessels running continuously, and you begin to see the scale and complexity operators manage every day.

            ## How money is made

            Shipping profit is fundamentally about **margin management at volume**. A single voyage on a Capesize bulk carrier might generate $500,000 in freight revenue — and cost $450,000 to operate. That $50,000 margin sounds thin, but the vessel may complete 8–10 such voyages a year. Across a fleet of 20 vessels, those margins compound into significant annual profit — or loss.

            The key levers:

            - **Freight rates** — set by supply and demand in the market
            - **Bunker costs** — the largest controllable cost, typically 40–60% of voyage expenses
            - **Vessel utilisation** — minimising idle time and ballast legs
            - **Operational efficiency** — accurate estimates, fast turnarounds, correct invoicing

            ## Where it goes wrong

            **Market cycles.** Freight rates are highly volatile — driven by trade volumes, fleet capacity, geopolitics and seasonal demand. Rates can halve in months. Operators who fixed long-term TC-in contracts at market peaks can end up paying hire that exceeds what their voyages earn.

            **Operational errors.** Incorrect bunker calculations, missed laytime deadlines, disputed demurrage claims, misfiled port documentation — each one costs money directly. Across a fleet, small errors add up to significant losses.

            **Information gaps.** When commercial, operations and finance teams work in different systems — or spreadsheets — the estimates that get fixed don't match the actuals that get settled. The gap is often invisible until the voyage closes, when it's too late to act.

            > [!TIP]
            > This is the fundamental problem Sedna VMS solves: one connected system where the estimate, the voyage execution and the financial close are the same record — so the gap between expected and actual is visible in real time, not discovered at month end.
        """),
    },
    {
        "title": "The Four Vessel Segments: Dry Bulk, Tanker, Breakbulk, Gas",
        "dur": 7,
        "description": "Each segment has its own business model, pain points and buyer. The segment shapes everything else.",
        "learn_items": [
            "What each segment carries and how it is chartered",
            "The core pain in each segment",
            "Why you confirm the segment before building a demo",
        ],
        "rich_content": md("""
            Sedna VMS serves operators across four shipping segments. Each has a different business model, different operational complexity, and needs a different conversation. The segment shapes the pain, the personas and the product flows you prioritise.

            ## Dry bulk

            - Carries unpackaged commodities: iron ore, coal, grain, fertiliser, bauxite
            - Vessel sizes: Handysize, Supramax, Panamax, Capesize
            - Mostly voyage charters — freight per tonne
            - High fixture volume — commercial teams fix many voyages at once
            - **Core pain:** estimate accuracy, TCE visibility, voyage P&L vs actuals
            - **Primary persona:** Head of Chartering or Ops Manager

            ## Tanker

            - Crude tankers (VLCC, Suezmax, Aframax) carry unrefined oil
            - Product tankers (LR1, LR2, MR) carry refined products — jet fuel, gasoil, naphtha
            - Chemical tankers carry speciality chemicals in stainless steel tanks with strict segregation
            - Mix of voyage charters and TC-in fleets; parcelling is common on product tankers
            - **Core pain:** hire reconciliation, parcelling complexity, ECA bunker management
            - **Primary persona:** Finance Director or CFO

            ## Breakbulk and project cargo

            - Carries non-containerised goods: wind turbines, heavy industrial equipment, fabricated steel
            - Multi-parcel, multi-leg voyages; cargo configurations change mid-voyage
            - MPP (multi-purpose) vessels carry a mix of breakbulk and some bulk or containers
            - Often voyage charter, frequently with complex lump-sum freight
            - **Core pain:** cargo complexity, mid-voyage changes, P&L accuracy
            - **Primary persona:** Operations Director or Fleet Manager

            ## Gas carriers

            - LPG carriers move propane and butane in pressurised or refrigerated tanks
            - LNG carriers move liquefied natural gas at −163°C in cryogenic tanks — highly specialised
            - Sizes range from small pressurised and semi-refrigerated vessels to VLGCs (Very Large Gas Carriers)
            - Mostly long-term time charters; complex cargo handling
            - **Core pain:** fleet utilisation, TC management, cargo quantity calculations (boil-off)
            - **Primary persona:** Fleet Manager or Commercial Director

            > [!NOTE]
            > **Demo relevance.** Never demo a dry bulk voyage to a tanker operator or vice versa. A product tanker CFO watching a single-cargo iron ore voyage will disengage within ten minutes. Confirm the segment before building anything.
        """),
    },
    {
        "title": "The Parties in a Shipping Deal",
        "dur": 6,
        "description": "Owners, operators, charterers, brokers, port agents, P&I clubs and class societies — who they are and what they care about.",
        "learn_items": [
            "The seven parties around every voyage",
            "What each party cares about",
            "How a prospect's position in the chain changes the conversation",
        ],
        "rich_content": md("""
            Every shipping transaction involves several parties with different interests, risks and relationships to the voyage P&L. Knowing who each one is — and what they care about — matters when you map a customer's organisation or scope a demo.

            | Party | Who they are | What they care about |
            |---|---|---|
            | **Shipowner** | Owns the vessel and either operates it or charters it out for income. Can be a large corporation or a single-vessel company. | Vessel earnings, hire income, maintenance costs, asset value, charter duration |
            | **Operator / Charterer** | Controls the commercial and operational use of the vessel — as owner-operator or via TC-in. Fixes cargoes, runs voyages, closes accounts. Sedna VMS's primary user. | TCE, voyage P&L, fleet utilisation, operational efficiency, accurate financial close |
            | **Cargo charterer** | Contracts with the operator to carry its cargo — a commodity trader, industrial producer or energy company. Pays freight and bears demurrage risk. | Vessel availability, laycan performance, freight rate, demurrage exposure |
            | **Shipbroker** | Brings owner/operator and cargo charterer together and negotiates the charter party. Earns commission (typically 1.25% of freight). Not involved in operations. | Deal flow, fixture volume, commission, market intelligence |
            | **Port agent** | Local representative at each port: berth booking, customs, crew matters, cargo documents, and the Statement of Facts. Essential to laytime. | Timely instructions, accurate cargo information, prompt payment of port costs |
            | **P&I club** | Protection & Indemnity mutual insurer covering owner liability: cargo damage, pollution, collision, crew injury. The International Group clubs cover 90%+ of ocean-going tonnage. | Accurate incident reporting, rule compliance, fleet risk exposure |
            | **Classification society** | Sets and enforces technical standards for building and running vessels — Lloyd's Register, DNV, Bureau Veritas, ABS, ClassNK. Vessels must keep class to trade. | Survey schedules, condition reports, regulatory compliance |

            > [!TIP]
            > **Why this matters when scoping a customer.** Their role in this chain tells you who else is in the room and what each person cares about. An owner-operator has different priorities to a trading operator who TC-ins every vessel. An owner thinking about TC-out management needs different screens than an ops team running 40 voyages at once.
        """),
    },
    {
        "title": "Global Trade: Routes, Commodity Flows and Chokepoints",
        "dur": 7,
        "description": "The major dry bulk and tanker trade flows, and why disruption at a chokepoint moves rates worldwide.",
        "learn_items": [
            "The main dry bulk flows: iron ore, coal, grain, fertiliser",
            "The main tanker flows: crude, refined products, LPG",
            "Why Suez, Panama, Hormuz and Malacca matter to voyage costs",
        ],
        "rich_content": md("""
            Shipping is the physical infrastructure of global trade. Knowing the major flows helps you speak credibly with commercial and C-suite people who think about the market, not just individual voyages.

            ## Major dry bulk flows

            - **Iron ore:** Brazil (Tubarão) and Australia (Port Hedland, Dampier) → China. Capesize dominates. Chinese steel production drives Capesize demand — when Chinese mills slow, rates collapse.
            - **Coal:** Australia and Indonesia → China, Japan, South Korea, India. Metallurgical coal (steelmaking) and thermal coal (power). Panamax and Capesize.
            - **Grain:** US Gulf, Brazil, Argentina, Black Sea → Asia, Middle East, North Africa. Panamax and Supramax. Highly seasonal — harvests drive demand spikes.
            - **Fertilisers:** Middle East, Russia, North Africa → South and Southeast Asia, Americas. Handysize and Supramax.

            ## Major tanker flows

            - **Crude oil:** Middle East Gulf → China, South Korea, Japan, India on VLCCs. West Africa → Asia and the US. North Sea → global. VLCC economics dominate crude markets.
            - **Refined products:** ARA (Amsterdam–Rotterdam–Antwerp) → US East Coast and West Africa. US Gulf → Latin America. MR tankers dominate short-haul product trades.
            - **LPG:** Middle East → Japan, China, Korea. US Gulf → Asia since the shale gas boom. VLGC rates follow the US–Asia arbitrage.

            ## Chokepoints and why disruption matters

            - **Suez Canal** links Europe and Asia. Closure sends vessels round the Cape of Good Hope — 10–14 extra days and significant bunker cost per voyage. The 2021 Ever Given grounding and the 2024 Red Sea crisis both disrupted the market.
            - **Panama Canal** links Atlantic and Pacific. Drought-related draft restrictions in 2023–24 forced vessels to cut cargo intake or reroute, pushing up freight on affected trades.
            - **Strait of Hormuz** carries around a fifth of global oil supply. Tension there moves tanker rates worldwide within hours.
            - **Strait of Malacca** links the Indian Ocean and the South China Sea — critical for Middle East → Asia energy flows.

            > [!NOTE]
            > **Demo relevance.** When a customer mentions Red Sea rerouting, Panama restrictions or a sanctions-driven route change, you need to know immediately what that means for their voyage costs, ETAs and P&L. People respect consultants who understand the market, not just the features.
        """),
    },
    {
        "title": "How a Shipping Company Is Structured",
        "dur": 7,
        "description": "The departments inside an operator, what they do every day, and the pain each one has without a VMS.",
        "learn_items": [
            "The six core departments and their day-to-day work",
            "Each department's pain without a connected system",
            "The handoff problem between departments",
        ],
        "rich_content": md("""
            Most operators are organised around the same core functions, whatever their fleet size. Knowing who does what — and where the handoffs happen — is how you find the pain and talk to the right people.

            | Department | What they do day to day | Their pain without a VMS |
            |---|---|---|
            | **Chartering / Commercial** | Fix cargoes, build voyage estimates, negotiate rates with charterers and brokers, decide which voyages to take, manage COAs and spot fixtures. | Estimating in Excel or legacy tools. No real-time TCE. Estimate assumptions don't flow into ops. Fixture details re-keyed into several systems. |
            | **Operations** | Run voyages day to day: positions and ETAs, port calls, bunker orders, cargo operations, off-hire and mid-voyage changes. | Manual position updates. Bunker maths in spreadsheets. Laytime tracked offline. No live P&L. Disconnected from chartering and finance. |
            | **Finance / Accounting** | Invoice freight, raise demurrage claims, reconcile hire statements, manage disbursements, close voyage P&Ls, produce period-end reports. | Hire reconciliation in Excel. Invoices from manual data. No audit trail from voyage event to financial entry. Slow, error-prone close. |
            | **Post-fixture** | Bridge between commercial and ops: voyage instructions, charter party compliance, cargo claims, statements of facts and laytime. | SOF data kept offline. Laytime in spreadsheets. Disputes by email. Claims take weeks. |
            | **Technical / Fleet management** | Maintenance, drydock scheduling, class surveys, crewing, spares and insurance. | Maintenance in a separate system. Drydock off-hire not fed into hire reconciliation. |
            | **Management / C-suite** | Fleet P&L oversight, strategy, investor reporting, compliance governance. | Weekly Excel reports stitched together by hand. Fleet TCE only days after period close. |

            > [!TIP]
            > **The handoff problem.** The biggest pain in shipping sits between departments. Chartering fixes a deal and ops re-keys it. Ops updates are compiled by hand for finance. Finance reports don't match what ops sees. Sedna VMS removes these handoffs — one voyage record flows from estimate through execution to financial close without re-entry.
        """),
    },
]

TIER1_QUIZ = [
    {
        "q": "Roughly what share of total voyage expenses do bunkers typically make up?",
        "explanation": "Bunkers are the largest controllable cost — typically 40–60% of voyage expenses.",
        "options": [("5–10%", False), ("15–25%", False), ("40–60%", True), ("Over 80%", False)],
    },
    {
        "q": "Why do estimate-vs-actual gaps often go unnoticed until a voyage closes?",
        "explanation": "When commercial, operations and finance work in separate systems or spreadsheets, nobody sees the fixed estimate and the settled actuals side by side until month end.",
        "options": [
            ("Freight rates are only published once a month", False),
            ("Commercial, ops and finance work in different systems or spreadsheets", True),
            ("Charterers hide actual costs from operators", False),
            ("Port agents submit costs before the voyage starts", False),
        ],
    },
    {
        "q": "Which segment's core pain is hire reconciliation, parcelling and ECA bunker management?",
        "explanation": "Tanker fleets mix voyage charters with TC-in, and product tankers carry several parcels at once.",
        "options": [("Dry bulk", False), ("Tanker", True), ("Breakbulk", False), ("Gas carriers", False)],
    },
    {
        "q": "Who typically produces the Statement of Facts at a port call?",
        "explanation": "The port agent handles local formalities and produces the SOF, the main input to laytime calculations.",
        "options": [("The shipbroker", False), ("The P&I club", False), ("The port agent", True), ("The classification society", False)],
    },
    {
        "q": "What does a shipbroker typically earn on a fixture?",
        "explanation": "Brokers earn a commission, typically around 1.25% of freight, and are not involved in operations.",
        "options": [
            ("A daily hire rate", False),
            ("A commission of around 1.25% of freight", True),
            ("All demurrage on the voyage", False),
            ("A fixed fee from the port authority", False),
        ],
    },
    {
        "q": "A Suez Canal closure forces vessels round the Cape of Good Hope. What is the main effect on a voyage?",
        "explanation": "Rerouting adds roughly 10–14 days and significant bunker cost to each voyage.",
        "options": [
            ("Lower bunker costs because of calmer seas", False),
            ("Around 10–14 extra days and significant extra bunker cost", True),
            ("No effect — canal dues are simply refunded", False),
            ("The charter party is automatically cancelled", False),
        ],
    },
    {
        "q": "What is the 'handoff problem' that Sedna VMS removes?",
        "explanation": "Fixtures, ops updates and finance reports get re-keyed between departments; one shared voyage record removes the re-entry.",
        "options": [
            ("Vessels changing owner mid-voyage", False),
            ("Data re-keyed between chartering, operations and finance", True),
            ("Cargo transferred between two ships at sea", False),
            ("Crew changes at the discharge port", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# TIER 2 — CHARTERS & VOYAGE ECONOMICS (topics 06–08)
# ─────────────────────────────────────────────────────────────────────────

TIER2_MODULES = [
    {
        "title": "Charter Types: Voyage Charter, Time Charter and COA",
        "dur": 9,
        "description": "The charter type defines who pays what, who carries which risk, and how the voyage P&L is built.",
        "learn_items": [
            "Voyage charter, TC-in, TC-out and COA side by side",
            "Who earns and who pays under each",
            "The VMS pain each charter type creates",
        ],
        "rich_content": md("""
            The charter type defines the whole commercial relationship between operator and charterer — who pays what, who carries what risk, and how the voyage P&L is structured. It is the most fundamental concept in commercial shipping.

            ## Voyage charter (VC)

            The operator carries a specific cargo from port A to port B for a fixed freight rate, usually per metric tonne. **The operator pays all voyage costs:** bunkers, port dues, canal tolls, commissions. The charterer pays freight and bears demurrage risk if loading or discharging runs over.

            - **Key clauses:** laycan, laytime allowed, demurrage rate, freight rate, cargo description and quantity, load and discharge ports, exceptions
            - **Relationship:** the operator takes all the cost risk, so freight must cover costs and leave a profit. TCE is how operators judge whether the rate is good enough.
            - **Who uses it:** dry bulk, breakbulk, some tanker trades

            ## Time charter in (TC-in)

            The operator **hires a vessel from its owner** at a fixed daily rate, whatever the vessel is doing. The operator still pays bunkers and port costs and takes the commercial and operational risk — in return for full flexibility over deployment.

            - **Key clauses:** hire rate ($/day), period, delivery and redelivery ports, off-hire, speed and consumption warranty, trading limits, maintenance
            - **Relationship:** hire runs whether the vessel is laden, ballasting or idle. Profit depends on keeping it busy on voyages whose TCE beats the hire rate.
            - **Who uses it:** dominant in tanker fleets, and operators topping up owned tonnage

            ## Time charter out (TC-out)

            The operator **charters its own vessel to a third party** for daily hire. The charterer takes on voyage costs and decisions; the operator receives hire and manages redelivery. The P&L is simpler — hire income minus running costs — and is used to place surplus tonnage or lock in income in an uncertain market.

            ## COA — Contract of Affreightment

            A framework agreement to carry a defined quantity of cargo over several voyages in a period, without naming a vessel up front. The charterer nominates shipments; the operator nominates a vessel for each. It gives both sides volume certainty, and each shipment becomes its own voyage record in VMS. Used by large, regular shippers — miners, steel producers, grain traders.

            ## Side by side

            | Charter type | Operator earns | Operator pays | Key VMS pain |
            |---|---|---|---|
            | **Voyage charter** | Freight per tonne | Bunkers, ports, canal, commission | Estimate vs actuals; laytime and demurrage |
            | **TC-in** | Margin after hire and voyage costs | Daily hire, bunkers, ports | Hire reconciliation; off-hire tracking; TCE per vessel |
            | **TC-out** | Daily hire from the charterer | Vessel running costs | Hire invoicing; redelivery; fleet P&L |
            | **COA** | Freight per tonne per shipment | All voyage costs per shipment | Volume tracking; nominating and running each voyage |

            > [!NOTE]
            > **Demo relevance.** In Sedna VMS, TC-in hire flows from the TC contract into every linked voyage P&L. Showing the hire rate pulled from the contract without manual entry — and that changing the contract updates every linked voyage — is a real "aha" moment for any TC-in operator.
        """),
    },
    {
        "title": "How a Voyage Makes (or Loses) Money: The P&L and TCE",
        "dur": 9,
        "description": "Every line of the voyage P&L — where it comes from, who controls it — and how TCE turns it into one comparable number.",
        "learn_items": [
            "The revenue lines: freight, demurrage, hire income",
            "The cost lines: bunkers, port costs, canal dues, hire, commissions",
            "How to calculate TCE and why it's the first number checked",
        ],
        "rich_content": md("""
            Every voyage produces a P&L. Knowing each line — where it comes from, who controls it, and how it feeds TCE — is essential before you can show the estimator or the financial close with credibility.

            ## Revenue lines

            - **Freight revenue** — the main income on a voyage charter: freight rate × bill of lading quantity. Reduced by **address commission** (paid back to the charterer, typically 1.25–2.5%) and **broker commission** (typically 1.25%). Net freight = gross freight minus commissions.
            - **Demurrage income** — charged when the charterer takes longer than the allowed laytime. Extra revenue for the operator, but slow to collect and often disputed.
            - **Hire income (TC-out)** — daily hire × hire days, less any agreed off-hire.

            ## Cost lines

            - **Bunkers** — usually the largest voyage cost, 40–60% of the total. Sea consumption (tonnes/day) × sea days, plus port consumption × port days, × fuel price — split across grades (VLSFO, and MGO in ECA zones). Very sensitive to speed.
            - **Port costs / disbursements** — port dues, pilotage, towage, agency fees, mooring and other local charges, settled through the port agent's disbursement account.
            - **Canal dues** — Suez, Panama and others charge by vessel size (GT/NT) and cargo.
            - **Hire cost (TC-in)** — daily hire × voyage days. Runs from delivery to redelivery whether or not the vessel earns freight. Flows automatically from the TC contract in Sedna VMS.
            - **Commissions** — usually shown as a reduction of freight revenue rather than a separate cost line.

            ## TCE — Time Charter Equivalent

            ```
            TCE = (Freight revenue − Voyage costs) ÷ Voyage days

            Voyage costs = bunkers + ports + canal   (not hire, for TC-in)
            Voyage days  = laden days + ballast days
            ```

            TCE strips out variable costs and turns the result into a per-day rate, so voyages of different lengths and routes can be compared fairly. For a TC-in operator, TCE has to beat the daily hire rate just to break even. It is the first number checked on every estimate.

            > [!NOTE]
            > **The TCE reverse-calculation moment.** Enter a target TCE in Sedna VMS and it calculates the freight rate needed to hit it. Operators who do this in Excel call it a 20-minute exercise; in VMS it takes ten seconds. Don't explain it — just do it and stop talking.
        """),
    },
    {
        "title": "Worldscale: How Tanker Freight Rates Work",
        "dur": 6,
        "description": "Tanker freight is quoted as a percentage of a published flat rate. How Worldscale works, with a worked example.",
        "learn_items": [
            "What WS 100, the flat rate and 'WS 85' mean",
            "How to turn a Worldscale fixture into gross freight",
            "Lumpsum vs Worldscale",
        ],
        "rich_content": md("""
            Dry bulk freight is quoted in USD per metric tonne. Tanker freight uses a different system — Worldscale. If you talk to a tanker operator without understanding it, you'll lose credibility fast.

            ## What Worldscale is

            Worldscale is a standard table of tanker freight rates, published every year by the Worldscale Association. For each port pair (for example Ras Tanura → Rotterdam) it publishes a **flat rate** in USD per metric tonne. That flat rate is Worldscale 100 (WS 100) — often just called **"the flat"**.

            Actual freight is negotiated as a **percentage of the flat**. WS 85 means 85% of the flat rate for that route; WS 120 means 120%. That percentage is the Worldscale rate, or "WS points".

            ## Why it exists

            The flat rate is calculated so that a standard reference vessel earns the same fixed daily return on every route after costs. That lets charterers and operators compare rates across routes and vessel sizes on one basis. A specific vessel's real TCE still depends on its size, speed and consumption — but Worldscale gives every tanker negotiation a common reference point.

            ## Worked example

            The flat rate for Ras Tanura → Rotterdam is $18.00/MT and the fixture is agreed at WS 85.

            - Freight rate = $18.00 × 85% = **$15.30/MT**
            - The vessel loads 270,000 MT of crude
            - Gross freight = $15.30 × 270,000 = **$4,131,000**

            WS points move with the market — above WS 100 when it's strong, below when it's weak. The flat rates themselves are recalculated annually to reflect changes in standard voyage costs such as bunker prices and port costs.

            ## Lumpsum vs Worldscale

            Some tanker voyages — especially product trades and niche routes — are fixed at a **lumpsum**: one dollar amount for the whole voyage, whatever quantity is loaded. That shifts quantity risk to the operator. Sedna VMS supports both.

            > [!NOTE]
            > **Demo relevance.** Sedna VMS supports Worldscale rate rules in the voyage estimator. For a tanker scenario, enter freight as Worldscale rather than $/MT — it's what tanker charterers actually use, and getting it right signals credibility with an experienced tanker team.
        """),
    },
]

TIER2_QUIZ = [
    {
        "q": "Under a voyage charter, who pays bunkers, port dues and canal tolls?",
        "explanation": "On a voyage charter the operator carries all voyage costs; the charterer pays freight and bears demurrage risk.",
        "options": [("The charterer", False), ("The operator", True), ("The shipbroker", False), ("They're split 50/50 by law", False)],
    },
    {
        "q": "A TC-in vessel sits idle waiting for cargo. What happens to the hire?",
        "explanation": "TC-in hire is a fixed daily cost that runs from delivery to redelivery whatever the vessel is doing.",
        "options": [
            ("Hire stops until the next fixture", False),
            ("Hire keeps running — it's a fixed daily cost", True),
            ("The owner pays the operator for the idle days", False),
            ("Hire halves automatically", False),
        ],
    },
    {
        "q": "What is a COA?",
        "explanation": "A Contract of Affreightment commits to a quantity of cargo over several voyages without naming the vessel in advance.",
        "options": [
            ("A one-off charter for a named vessel", False),
            ("An agreement to carry a set quantity over several voyages, vessels nominated later", True),
            ("A certificate of class awarded to a vessel", False),
            ("A port agent's cost statement", False),
        ],
    },
    {
        "q": "How is TCE calculated?",
        "explanation": "TCE = (freight revenue − voyage costs) ÷ voyage days, where voyage costs exclude TC-in hire.",
        "options": [
            ("Freight revenue ÷ cargo tonnes", False),
            ("(Freight revenue − voyage costs) ÷ voyage days", True),
            ("Daily hire × voyage days", False),
            ("Demurrage − despatch", False),
        ],
    },
    {
        "q": "For a TC-in operator, what must TCE beat just to break even?",
        "explanation": "Hire isn't in the TCE voyage costs, so TCE must exceed the daily hire rate to cover it.",
        "options": [("The demurrage rate", False), ("The daily hire rate", True), ("The broker commission", False), ("The Worldscale flat", False)],
    },
    {
        "q": "A tanker is fixed at WS 85 on a route with a flat rate of $18.00/MT. What is the freight rate?",
        "explanation": "$18.00 × 85% = $15.30/MT.",
        "options": [("$15.30/MT", True), ("$18.85/MT", False), ("$21.18/MT", False), ("$85.00/MT", False)],
    },
    {
        "q": "In Worldscale, what is 'the flat'?",
        "explanation": "The flat is the published WS 100 rate for a route; fixtures are agreed as a percentage of it.",
        "options": [
            ("The negotiated percentage, e.g. WS 85", False),
            ("The published WS 100 rate for the route", True),
            ("A lumpsum freight for the whole voyage", False),
            ("The demurrage rate on a tanker charter", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# TIER 3 — VESSELS, OPERATIONS & FINANCE (topics 09–13)
# ─────────────────────────────────────────────────────────────────────────

TIER3_MODULES = [
    {
        "title": "Vessels and Cargo: Dimensions, Size Classes and Port Limits",
        "dur": 9,
        "description": "DWT, draft, LOA, beam and GT/NT; the dry bulk and tanker size classes; and the physical limits that shape every estimate.",
        "learn_items": [
            "The five key vessel dimensions and why each matters",
            "Dry bulk and tanker size classes",
            "Cargo compatibility, port facility types and draft restrictions",
        ],
        "rich_content": md("""
            A vessel's physical characteristics, and its cargo's, decide which routes are possible, how much can be loaded and what the voyage costs. These constraints come up constantly in estimating and ops conversations.

            ## Key vessel dimensions

            | Dimension | What it means | Why it matters |
            |---|---|---|
            | **DWT (deadweight tonnage)** | The most weight the vessel can carry: cargo, fuel, water and stores. | Sets cargo intake. A 180,000 DWT Capesize can't fill all of that with cargo — bunkers, water and stores take 5–10%. |
            | **Draft** | Depth from the waterline to the bottom of the hull. Increases as cargo loads. | Port draft limits are the most common planning constraint. A 14m port can't take a fully laden VLCC (20m+). |
            | **LOA (length overall)** | Total length from bow to stern. | Berth length limits — some ports can't take vessels over a certain length whatever their draft. |
            | **Beam** | Maximum width. | Canal limits: the Panama Canal's new locks take a beam of about 51m. "Post-Panamax" means too wide for the original locks (about 32m). |
            | **GT / NT (gross / net tonnage)** | A measure of volume, not weight. | Port dues and canal fees are charged on GT/NT, so a larger-GT vessel pays more at Suez and Panama. |

            ## Size classes — dry bulk

            | Class | DWT | Typical trades |
            |---|---|---|
            | **Handysize** | 10,000–40,000 | Minor bulks, grain, fertiliser, small ports |
            | **Handymax / Supramax** | 40,000–65,000 | Grain, coal, minor bulks, flexible deployment |
            | **Panamax** | 65,000–90,000 | Grain, coal; sized for the original Panama locks |
            | **Kamsarmax** | ~82,000 | Largest size for Kamsar, Guinea — a major bauxite port |
            | **Capesize** | 100,000–400,000 | Iron ore and coal on long-haul routes; can't use the Panama Canal |
            | **VLOC** | 300,000+ | Dedicated iron ore — Brazil/Australia to China |

            ## Size classes — tankers

            | Class | DWT | Typical trades |
            |---|---|---|
            | **MR (Medium Range)** | 25,000–55,000 | Clean products, regional trades; the most common product tanker |
            | **LR1** | 55,000–80,000 | Clean and dirty products, long-haul |
            | **Aframax / LR2** | Aframax 80,000–120,000; LR2 80,000–160,000 | Aframax crude in the North Sea and Black Sea; LR2 products long-haul |
            | **Suezmax** | 120,000–200,000 | Crude; the largest size for a laden Suez transit |
            | **VLCC** | 200,000–320,000 | Middle East–Asia long-haul crude |
            | **ULCC** | 320,000+ | Rare, with limited port access |

            ## Cargo compatibility and port facilities

            **Compatibility.** Not every vessel can carry every cargo. Chemicals need stainless steel or coated tanks, LNG needs cryogenic insulation, and grain needs clean holds free of previous cargo. Each cargo limits which vessels can be used.

            **Port facility types:**

            - **Terminal** — a dedicated facility for one cargo type (iron ore, oil)
            - **Anchorage** — where vessels wait offshore for a berth; whether that time counts as laytime depends on the charter party
            - **STS (ship-to-ship)** — cargo moved between vessels at sea, without a port
            - **Lightering** — taking cargo off a large vessel offshore so it can enter a shallow port

            **Draft restrictions in practice.** The Elbe limits tanker access to Hamburg. Ponta da Madeira in Brazil takes 400,000 DWT Valemaxes, but smaller Brazilian ports can't. Most ports publish a maximum inbound draft, and operators must check the laden vessel fits before confirming a fixture.
        """),
    },
    {
        "title": "Bunkers: Fuel Types, Consumption and the Cube Rule",
        "dur": 8,
        "description": "The largest variable cost on most voyages. Fuel grades, the speed–consumption relationship, and how VMS calculates bunkers.",
        "learn_items": [
            "HFO, VLSFO, MGO and LNG — and when each is used",
            "Why consumption rises with roughly the cube of speed",
            "How Sedna VMS builds a bunker estimate, and why vessel data quality matters",
        ],
        "rich_content": md("""
            Bunkers are the largest variable cost on most voyages — typically 40–60% of expenses. Small errors in the fuel calculation have big P&L consequences.

            ## Fuel types

            | Fuel | What it is | When it's used | Price |
            |---|---|---|---|
            | **HFO / IFO 380** | Heavy fuel oil, high sulphur (3.5%) | Outside ECAs on vessels with scrubbers; declining | Cheapest |
            | **VLSFO** | Very low sulphur fuel oil (0.5%), IMO 2020 compliant | Standard open-sea fuel since January 2020 for non-scrubber vessels | +15–25% vs HFO |
            | **MGO (DMA)** | Marine gas oil, distillate, 0.1% sulphur | Required in ECA zones; also at berth in some ports | +25–40% vs VLSFO |
            | **LNG (as fuel)** | Liquefied natural gas for propulsion | Dual-fuel newbuilds; almost no sulphur, lower CO₂ | Varies with LNG price |

            ## The speed–consumption relationship

            Fuel consumption rises roughly with the **cube** of speed — not in a straight line.

            ```
            Consumption ∝ Speed³

            10% slower → about 27% less fuel
            20% slower → about 49% less fuel
            ```

            A vessel burning 55 MT/day at 14 knots might burn only about 35 MT/day at 12 knots — a 36% saving. But the voyage takes more days, adding hire cost (for TC-in) and reducing utilisation. Operators make this trade-off all the time.

            ## How VMS calculates bunkers

            Each vessel in Sedna VMS has a **speed/consumption profile**: consumption at different laden and ballast speeds, plus port consumption at anchor and at berth. When a voyage is estimated:

            1. The port rotation is entered and distances fill in automatically
            2. The instructed speed gives the sea days
            3. Profile consumption × sea days = sea bunkers
            4. Port consumption × port days = port bunkers
            5. ECA segments are identified and switched to MGO
            6. Prices per grade give the total bunker cost

            > [!WARNING]
            > If the vessel profile is wrong, every estimate is wrong. That's why vessel data quality is a critical setup item during VMS onboarding.

            ## Bunker procurement

            Operators buy bunkers at load or discharge ports or at hubs such as Fujairah, Singapore, Rotterdam and Panama. Prices move daily, and larger TC-in positions may be hedged. The gap between the price paid and the price assumed in the estimate is a common source of P&L variance.

            For TC-in vessels the operator buys the bunkers. Quantities and prices are recorded in VMS and used in hire statement reconciliation — bunkers on delivery and redelivery are part of the TC settlement.
        """),
    },
    {
        "title": "Port Calls: NOR, SOF and the Laytime Clock",
        "dur": 8,
        "description": "What happens at a port call, how it's recorded, and the disputes that turn port time into money.",
        "learn_items": [
            "The key port-call terms: NOR, laycan, SOF, EOSP/COSP, arrived ship, free pratique",
            "The seven steps of a port call",
            "The five most common things that go wrong",
        ],
        "rich_content": md("""
            Every cargo voyage has at least one load port and one discharge port. What happens there — and how it's recorded — has direct financial consequences through laytime and demurrage. It's the workflow most ops teams manage worst without a VMS.

            ## Key terms

            - **NOR — Notice of Readiness.** The master's formal notice that the vessel has arrived and is ready in all respects to load or discharge. Tendering NOR usually starts the laytime clock.
            - **Laycan.** The date window in which the vessel must arrive at the load port. Too early and NOR may not be accepted; after the cancelling date the charterer may cancel.
            - **SOF — Statement of Facts.** A timestamped log of every significant port event: arrival, NOR, berthing, start and end of cargo operations, stoppages and their causes. Produced by the port agent; the main input to laytime.
            - **EOSP / COSP.** End and Commencement of Sea Passage — when the vessel switches between sea and port mode. Used for bunker accounting and voyage reporting.
            - **Arrived ship.** A vessel that has reached the position needed to tender valid NOR — port area, anchorage or berth, as the charter party defines. Whether a vessel waiting at anchorage has "arrived" is a frequent dispute.
            - **Free pratique.** Health clearance letting the crew deal freely with the shore. Some charter parties require it before laytime can start.

            ## The port call, step by step

            1. **Arrival** — the vessel reaches port limits, the ETA is updated and pre-arrival notices go to the agent.
            2. **NOR tendered** — the master sends NOR to the charterer, usually triggering laytime (if the vessel is at the contractual place and all conditions are met).
            3. **Waiting** — the vessel may wait at anchorage. Whether that counts depends on the wording: **WIBON** (whether in berth or not) means it does; **WIPON** (whether in port or not) is broader still.
            4. **Berthing** — the vessel moves to the berth.
            5. **Cargo operations** — loading or discharging. Every delay and stoppage goes in the SOF and must be classed as counting against laytime or as an exception (weather, breakdown, charterer's fault).
            6. **Completion** — operations finish, hoses disconnect, documents are exchanged (the bill of lading is signed). Laytime stops.
            7. **Departure** — the vessel sails; the agent finalises the SOF and submits the disbursement account.

            ## What goes wrong

            - **Disputed NOR** — the charterer argues the vessel wasn't truly ready, so the clock should start later.
            - **Anchorage time** — days at anchor; whether they count can be the difference between a large demurrage claim and none.
            - **SOF discrepancies** — operator and charterer record different times for the same events. Without one system of record, it's settled by long email chains.
            - **Exception disputes** — a stoppage happens and each side reads the charter party differently. The wording is all that matters, and applying it needs careful records.
            - **Late documentation** — SOFs arrive weeks late, so laytime is late, claims age and cash comes in slowly.
        """),
    },
    {
        "title": "Laytime and Demurrage",
        "dur": 9,
        "description": "The single most important financial concept in voyage chartering: time allowed, time used, and who pays for the difference.",
        "learn_items": [
            "Laytime allowed, demurrage and despatch",
            "Reversible vs non-reversible laytime",
            "SHINC, SHEX, WWDSHEX, WIBON, WIPON and 'once on demurrage'",
        ],
        "rich_content": md("""
            Laytime and demurrage touch every voyage charter. Calculating them correctly — and collecting demurrage quickly — is one of the most valuable things a VMS does. Get this wrong in front of a technical ops or finance audience and you'll lose them.

            ## The core idea

            The charter party gives the charterer a fixed amount of time to load and discharge — the **laytime allowed**. It may be a number of days ("5 weather working days") or a rate ("10,000 MT per weather working day").

            - If time used is **more** than allowed, the charterer pays **demurrage** to the operator at the agreed $/day rate, compensating for the vessel being held.
            - If time used is **less**, the operator may pay **despatch** to the charterer — usually half the demurrage rate — as a reward for speed.

            ```
            Demurrage = (Time used − Time allowed) × Demurrage rate

            Time used:    from laytime start to completion of cargo operations
            Time allowed: as set in the charter party
            Negative result → despatch (typically 50% of the demurrage rate)
            ```

            ## Reversible vs non-reversible

            - **Non-reversible** — each port has its own allowance. Time saved at the load port can't offset an overrun at discharge, so the operator can earn demurrage at discharge even after an early finish at load. Most common in dry bulk.
            - **Reversible (averaged)** — laytime is pooled across all ports, so time saved at one offsets overrun at another. Common in tankers, and better for charterers on multi-port voyages.

            ## Common exception terms

            | Term | Meaning |
            |---|---|
            | **SHINC** | Sundays and holidays included — they count against laytime |
            | **SHEX** | Sundays and holidays excluded — they don't count |
            | **WWDSHEX** | Weather working days, Sundays and holidays excluded — only working days in good weather count |
            | **WIBON** | Whether in berth or not — laytime counts from NOR even before berthing |
            | **WIPON** | Whether in port or not — laytime counts from NOR even outside the port area |
            | **Once on demurrage, always on demurrage** | Once laytime runs out, demurrage continues even through periods that would normally be exceptions |

            ## Why collection is painful without a VMS

            Demurrage is earned during the voyage but collected weeks or months later: receive the SOF → calculate laytime → prepare the claim → send it → receive a counter-claim → negotiate → agree → invoice → collect. Every step is manual, delayed and open to error or dispute.

            Large operators can have hundreds of open claims at once — significant cash tied up in receivables.

            > [!TIP]
            > Sedna VMS calculates laytime from SOF data, applies the charter party terms and exceptions, and produces an auditable claim — turning weeks of work into minutes.
        """),
    },
    {
        "title": "Hire Statements, Off-hire and Parcelling",
        "dur": 8,
        "description": "Why TC-in hire reconciliation is so painful, why off-hire is disputed, and how parcelling complicates tanker voyages.",
        "learn_items": [
            "What a hire statement contains",
            "Why off-hire dominates reconciliation disputes",
            "What parcelling is and why legacy systems struggle with it",
        ],
        "rich_content": md("""
            For operators running TC-in vessels, hire statement reconciliation is one of the most time-consuming, error-prone monthly jobs. Understanding it makes you credible with any finance person in a tanker or TC-heavy dry bulk conversation.

            ## What a hire statement contains

            The owner's invoice to the TC charterer, usually issued every 15 days in advance:

            - **Hire** — daily rate × days in the period
            - **Bunkers on delivery** — the value of fuel on board at delivery; a credit or debit depending on the agreed price vs actual quantity
            - **Off-hire deductions** — periods the vessel wasn't available: breakdown, drydock, crew changes
            - **Speed/performance adjustments** — if the vessel underperformed its warranted speed and consumption, the charterer may deduct the excess bunker cost
            - **Other adjustments** — cargo claims, vessel shortcomings, agreed credits

            Hire is paid in advance. If events in the period change what's owed, the difference goes onto the next statement.

            ## Why off-hire dominates disputes

            Off-hire is time the vessel isn't available, so hire isn't payable. The deduction is often disputed because:

            - Owners want to minimise off-hire — every day is lost income
            - Charterers want to maximise it — every day is saved cost
            - The cause is often contested — maintenance failure (owner) or operational incident (charterer)?
            - Without timestamped records in a shared system, each side works from its own logs

            ## Reconciling without a VMS

            A TC-in operator typically extracts the data by hand, compares it with their own records, works out their own off-hire figure, compares it with the owner's, finds the differences, disputes them by email, waits, and repeats. With 20 TC-in vessels each issuing statements every 15 days, that's 40+ reconciliations a month.

            > [!TIP]
            > Sedna VMS holds the TC contract (hire rate, period, delivery and redelivery terms) and feeds hire cost into every linked voyage P&L. Its hire statement matching compares owner invoices with your own records line by line and flags every discrepancy.

            ## Parcelling — the tanker complexity

            Product tankers often carry **several cargo parcels for different charterers on one voyage** — different grades in separate tanks, each with its own freight rate, laytime terms, demurrage rate and invoice.

            Each parcel is a separate commercial deal on one vessel movement. There's one fuel bill and one set of port costs, but they must be allocated across the parcels. Sedna VMS handles this natively through its sub-cargo structure; legacy systems need heavy manual workarounds.
        """),
    },
]

TIER3_QUIZ = [
    {
        "q": "Port dues and canal fees are charged on which measure?",
        "explanation": "GT/NT measure volume, and are the basis for port and canal charges — not DWT.",
        "options": [("DWT", False), ("LOA", False), ("GT/NT", True), ("Draft", False)],
    },
    {
        "q": "Which is the largest tanker size that can transit the Suez Canal laden?",
        "explanation": "Suezmax (120,000–200,000 DWT) is defined by the laden Suez transit limit.",
        "options": [("MR", False), ("Aframax", False), ("Suezmax", True), ("VLCC", False)],
    },
    {
        "q": "Roughly how much fuel does a vessel save by slowing down 10%?",
        "explanation": "Consumption rises with roughly the cube of speed, so 10% slower saves about 27%.",
        "options": [("About 10%", False), ("About 27%", True), ("About 50%", False), ("Nothing — consumption is fixed", False)],
    },
    {
        "q": "Which fuel must a vessel without a scrubber burn inside an ECA zone?",
        "explanation": "ECAs cap sulphur at 0.1%, so non-scrubber vessels switch to MGO (or 0.1% fuel).",
        "options": [("HFO", False), ("VLSFO", False), ("MGO", True), ("Any grade, if the voyage is short", False)],
    },
    {
        "q": "What usually starts the laytime clock?",
        "explanation": "Tendering a valid Notice of Readiness normally starts laytime, subject to the charter party.",
        "options": [
            ("The vessel leaving the previous port", False),
            ("Tendering a valid Notice of Readiness", True),
            ("The bill of lading being signed", False),
            ("The agent submitting the disbursement account", False),
        ],
    },
    {
        "q": "Allowed laytime is 5 days, the charterer uses 7, and the demurrage rate is $20,000/day. What is owed?",
        "explanation": "(7 − 5) × $20,000 = $40,000 demurrage, payable by the charterer to the operator.",
        "options": [
            ("$40,000 demurrage to the operator", True),
            ("$20,000 despatch to the charterer", False),
            ("$140,000 demurrage to the operator", False),
            ("Nothing — demurrage needs a 3-day overrun", False),
        ],
    },
    {
        "q": "Under reversible laytime, what happens to time saved at the load port?",
        "explanation": "Reversible laytime pools time across ports, so savings at one port offset overruns at another.",
        "options": [
            ("It's lost", False),
            ("It offsets an overrun at the discharge port", True),
            ("It's paid as double despatch", False),
            ("It extends the laycan", False),
        ],
    },
    {
        "q": "Why are off-hire deductions so often disputed?",
        "explanation": "Owners want less off-hire, charterers want more, the cause is contested, and each side works from its own logs.",
        "options": [
            ("Off-hire is set by the classification society", False),
            ("Owners and charterers have opposite incentives and keep separate records", True),
            ("Off-hire only applies to voyage charters", False),
            ("The P&I club decides the amount", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# TIER 4 — COMPLIANCE & REFERENCE (topics 14–16 + glossary)
# ─────────────────────────────────────────────────────────────────────────

TIER4_MODULES = [
    {
        "title": "EU ETS for Shipping",
        "dur": 8,
        "description": "How the EU Emissions Trading System covers shipping, what it costs operators, and how Sedna VMS handles it through Prosmar.",
        "learn_items": [
            "How cap-and-trade and EUAs work",
            "The 2024–2026 phase-in and which vessels and voyages are covered",
            "Who bears the cost, and the Prosmar integration",
        ],
        "rich_content": md("""
            Since January 2024, shipping has been part of the EU Emissions Trading System. It's one of the biggest new compliance costs for operators trading in Europe, and it comes up more and more in commercial and finance conversations.

            ## What EU ETS is

            A cap-and-trade scheme: covered companies must hold an **allowance (EUA)** for every tonne of CO₂ (or equivalent) they emit. Emit more than you hold and you buy EUAs on the market; emit less and you can sell the surplus. The cap falls over time, forcing emitters to cut emissions or pay. EUA prices have traded roughly between €40 and €100+ per tonne in recent years.

            ## How shipping is covered

            The phase-in:

            - **2024** — 40% of verified emissions must be covered by EUAs
            - **2025** — 70%
            - **2026 onwards** — 100%

            **Vessels:** 5,000 GT and above calling at EU ports, whatever their flag.

            **Voyages:** 100% of emissions on voyages between EU ports and at berth in EU ports; 50% on voyages between an EU and a non-EU port.

            **Gases:** CO₂ from 2024; methane (CH₄) and nitrous oxide (N₂O) from 2026.

            ## What it means commercially

            **A new voyage cost.** EUAs belong in the voyage P&L. A vessel burning 50 MT/day of VLSFO emits about 155 MT of CO₂ a day; on a 20-day EU voyage at €70/EUA and 100% coverage, that's around €217,000 for one voyage.

            **Who pays.** Under voyage charters the charter party must say — some operators pass ETS costs to charterers through an ETS clause, others absorb them. Under TC-in, the operator (as charterer) typically bears them as a voyage expense.

            **Compliance.** Operators monitor verified emissions per voyage under the MRV (monitoring, reporting and verification) rules, hold enough EUAs in their EU registry account, and surrender them by 30 September for the previous calendar year.

            ## How Sedna VMS handles it

            Sedna VMS integrates with **Prosmar**, a partner providing risk management and EU ETS/FuelEU compliance. Through it, operators can:

            - Track EU ETS exposure per voyage and across the fleet
            - Include EUA costs in estimates and actuals
            - Monitor verified emissions against obligations
            - Manage EUA surrender within the VMS workflow

            > [!WARNING]
            > Always describe EU ETS handling as the Prosmar integration. Don't present it as native VMS functionality unless that has been specifically confirmed.
        """),
    },
    {
        "title": "ECA Zones and Fuel Planning",
        "dur": 6,
        "description": "Where Emission Control Areas apply and why they change bunker grades, costs and voyage planning.",
        "learn_items": [
            "The 0.1% sulphur rule and how scrubbers change it",
            "Where ECA zones apply today",
            "Why ECAs affect bunker cost and planning",
        ],
        "rich_content": md("""
            Emission Control Areas are sea zones with strict limits on sulphur and other emissions from ships. They're a standard part of voyage planning — and a big reason bunker costs need a VMS rather than a spreadsheet.

            ## What an ECA is

            An ECA is designated under MARPOL Annex VI. Inside it, ships must burn fuel with at most **0.1% sulphur**, against the global 0.5% limit (VLSFO) outside. That means switching to MGO or a 0.1% fuel when entering. Vessels with approved scrubbers can keep burning HFO, because the scrubber removes sulphur oxides from the exhaust.

            ## Where ECAs apply

            | ECA | Coverage | Routes affected |
            |---|---|---|
            | **North Sea** | North Sea, English Channel | Rotterdam, Hamburg, Antwerp, UK ports, Scandinavia |
            | **Baltic Sea** | Baltic Sea and Gulf of Finland | Stockholm, Helsinki, Copenhagen, Baltic grain trades |
            | **North American** | 200 nautical miles off the US and Canadian coasts | All US and Canadian port approaches |
            | **US Caribbean** | Waters around Puerto Rico and the US Virgin Islands | Caribbean tanker trades |
            | **Mediterranean** | The whole Mediterranean Sea (since 1 May 2025) | All Mediterranean port approaches |
            | **Chinese domestic emission areas** | Coastal waters and major river deltas (national rules, not an IMO ECA) | All major Chinese port approaches |

            More areas are being designated, so check the latest list when planning.

            ## Why ECAs change voyage costs

            **Price premium.** Low-sulphur fuel costs considerably more than VLSFO — typically 20–40% per tonne. On a voyage with a lot of ECA steaming (say Rotterdam–Hamburg–Gothenburg–Helsinki), much of the sea bunkers must be priced at MGO rates.

            **Grade switching.** Vessels switch grade entering and leaving an ECA. That needs enough tank capacity for both grades and time to flush the fuel system, so ops must plan the switchover point.

            **Scrubber economics.** Scrubber vessels burn cheaper HFO everywhere, ECAs included. A scrubber (typically $3–6m) pays back through the HFO/VLSFO price spread — when the spread is low, the case is marginal.

            > [!NOTE]
            > **Demo relevance.** Sedna VMS detects ECA segments in the port rotation and switches the bunker grade automatically. Add a Rotterdam → Hamburg leg and watch it price the North Sea segment at MGO — a real "aha" moment for an ops team doing this in Excel.
        """),
    },
    {
        "title": "FuelEU Maritime and How It Differs from EU ETS",
        "dur": 7,
        "description": "The EU regulation on the carbon intensity of ship fuel: targets to 2050, pooling, and the key differences from EU ETS.",
        "learn_items": [
            "What FuelEU regulates and its reduction targets",
            "How compliance pooling, banking and borrowing work",
            "FuelEU vs EU ETS side by side",
        ],
        "rich_content": md("""
            FuelEU Maritime is a separate EU regulation from EU ETS, in force since January 2025. It targets the **carbon intensity of the energy ships use**, not the volume of emissions. Knowing the difference matters when customers raise compliance questions.

            ## What FuelEU is

            FuelEU Maritime (Regulation (EU) 2023/1805) sets tightening limits on the **greenhouse gas intensity** of energy used on board, measured in grams of CO₂ equivalent per megajoule (gCO₂eq/MJ). It pushes operators towards alternative fuels — LNG, methanol, ammonia, hydrogen — and renewable fuels of non-biological origin (RFNBOs).

            ## The targets

            | Period | Reduction vs 2020 baseline |
            |---|---|
            | 2025–2029 | 2% |
            | 2030–2034 | 6% |
            | 2035–2039 | 14.5% |
            | 2040–2044 | 31% |
            | 2045–2049 | 62% |
            | 2050 onwards | 80% |

            The 2025 target is reachable with VLSFO and modest efficiency gains. From 2030 it starts to need biofuel blending or alternative fuels; by 2050, only near-zero-emission fuels will do.

            ## Who's covered

            The same scope as EU ETS: vessels of 5,000 GT and above calling at EU ports, with the same 100% (intra-EU and at berth) and 50% (EU to non-EU) rule for counting energy.

            ## FuelEU vs EU ETS

            | | EU ETS | FuelEU Maritime |
            |---|---|---|
            | **Regulates** | Volume of emissions | Carbon intensity of fuel (gCO₂eq/MJ) |
            | **Mechanism** | Cap and trade — buy and sell EUAs | Pool compliance with others; bank or borrow surplus and deficit |
            | **Cost driver** | EUA price × tonnes emitted | Penalty above the limit; cost of lower-intensity fuel |
            | **Applies from** | 2024 (40% phase-in) | January 2025, full scope |
            | **Reporting** | Annual; surrender by 30 September | Annual; report by 31 January the following year |
            | **Penalty** | €100 per tonne of CO₂ not covered | €2,400 per tonne of VLSFO-equivalent non-compliant energy |

            ## Pooling

            Operators can **pool compliance** across vessels: one running below the limit creates a surplus that offsets another's deficit in the same pool. Surplus can be banked for later years, or compliance borrowed from future years within limits. That creates a market — an efficient fleet can sell surplus to operators with older vessels — and it needs fleet-level monitoring, not just voyage-by-voyage tracking.

            > [!WARNING]
            > As with EU ETS, FuelEU compliance in Sedna VMS is handled through the **Prosmar integration**. Don't present it as native VMS functionality.
        """),
    },
    {
        "title": "Shipping Glossary: 42 Key Terms",
        "dur": 10,
        "description": "A reference of key shipping terms across commercial, chartering, operations, finance, technical and tanker categories.",
        "learn_items": [
            "Commercial and chartering terms, from fixture to relet",
            "Operations, finance and technical terms",
            "Tanker-specific terms",
        ],
        "rich_content": md("""
            Keep this page as a reference alongside the lessons in this path.

            ## Commercial

            | Term | Meaning |
            |---|---|
            | **Fixture** | The confirmed agreement between owner/operator and charterer — vessel, cargo, rate and laycan all agreed. From fixture, the voyage moves from estimate to operational record. |
            | **Freight rate** | The price for carrying cargo: USD per metric tonne in dry bulk and breakbulk, or a Worldscale percentage in tankers. The main revenue input on a voyage charter estimate. |
            | **Worldscale (WS)** | The standard tanker freight system: a percentage of a published flat rate per route (WS 85 = 85% of the flat). Revised annually by the Worldscale Association. |
            | **Relet** | A charterer sub-charters the cargo space to a third party, earning freight from the sub-charterer while still paying the original owner. Creates an internal relet cargo structure in VMS. |

            ## Chartering

            | Term | Meaning |
            |---|---|
            | **Laycan** | Laydays/cancelling — the window in which the vessel must arrive at the load port. Too early and the charterer needn't load; after the cancelling date they may cancel. |
            | **COA — Contract of Affreightment** | An agreement to carry a set quantity over several voyages in a period, without naming the vessel. Each shipment is nominated and becomes a voyage record in VMS. |
            | **Nomination** | Designating a specific vessel for a voyage under a COA or charter. Once accepted, the voyage moves from estimate to active. |
            | **Address commission** | A discount on freight paid back to the charterer, typically 1.25–2.5%, deducted from freight revenue. Not the same as broker commission. |
            | **Broker commission** | The fee to the broker who arranged the charter, typically 1.25% of freight. Also deducted from gross freight. |
            | **Charter party (C/P)** | The contract governing a voyage or time charter: laytime, demurrage rate, freight, cargo and exceptions. The legal basis for the whole voyage P&L. |

            ## Operations

            | Term | Meaning |
            |---|---|
            | **Port rotation** | The sequence of ports on a voyage. Entering it in VMS fills in distances, sea days, ECA zones and ETAs, and recalculates the P&L. |
            | **Ballast leg** | Sailing without cargo to reposition for the next load port. Burns bunkers and time with no freight; included in TCE. |
            | **ETA — Estimated Time of Arrival** | When the vessel is expected at a port. Updates in VMS as actuals change; used to coordinate port and cargo readiness. |
            | **Off-hire** | Time on a time charter when the vessel isn't available (breakdown, drydock, crew change) and hire isn't payable. A frequent source of disputes. |
            | **Deviation** | Leaving the agreed route — to save life, for an emergency, or commercially. Unauthorised deviation can void insurance. In VMS it recalculates ETAs, bunkers and P&L. |
            | **Slow steaming** | Deliberately sailing below design speed to save fuel (10% slower ≈ 27% less fuel). Adds voyage days and lowers TCE. |
            | **Drydock** | Scheduled time out of service for inspection, hull cleaning, painting and repairs. Off-hire for TC vessels; a major planned cost. |
            | **Bill of lading (B/L)** | The carrier's receipt for cargo, document of title (cargo can be sold at sea by transferring it) and evidence of the contract of carriage. Essential for freight invoicing. |
            | **Stowage factor** | Cubic metres occupied by one tonne of cargo. Dense cargo (iron ore) makes a vessel weight-limited; light cargo (grain) makes it volume-limited. |
            | **Cargo intake** | The most of a given cargo a vessel can carry on a voyage, after deadweight, stowage factor, fuel, water and draft limits. Sets the billable quantity. |
            | **SOF — Statement of Facts** | The timestamped log of port events, produced by the agent and ship's officer. The main input to laytime and the evidence in demurrage disputes. |

            ## Finance

            | Term | Meaning |
            |---|---|
            | **TCE — Time Charter Equivalent** | (Freight revenue − voyage costs) ÷ voyage days. The daily profitability benchmark, and the first number checked on any estimate. |
            | **Voyage P&L** | Revenue minus voyage costs for one voyage. VMS keeps an estimated P&L (at fixing) and an actual one (during execution); the variance, traceable to transactions, is a core value for finance. |
            | **Accrual** | A cost or revenue incurred but not yet invoiced, booked at period end so the P&L reflects the true position. VMS supports accruals for open voyages. |
            | **Hire statement** | The owner's periodic invoice to a TC-in charterer, typically every 15 days: hire, bunker adjustments, off-hire and other items. A top finance pain point. |
            | **Freight invoice** | The operator's invoice to the charterer for freight, raised once the B/L quantity is confirmed. May include address commission, deadfreight and adjustments. |
            | **Deadfreight** | Freight on booked space that wasn't used — if the charterer loads less than the contracted minimum without a valid excuse. |
            | **Despatch** | Paid by the operator to the charterer when cargo work finishes inside laytime, usually at half the demurrage rate. Some charter parties are "demurrage only". |

            ## Technical

            | Term | Meaning |
            |---|---|
            | **DWT — Deadweight tonnage** | Total weight a vessel can carry — cargo, fuel, water, stores, crew — in metric tonnes. The basis for size classes. |
            | **Draft** | Depth from the waterline to the bottom of the hull. Decides which ports and canals a vessel can use and affects intake. |
            | **Bulk carrier classes** | Handysize (10–40k DWT), Handymax/Supramax (40–65k), Panamax (65–90k), Capesize (100k+, too big for the Panama Canal). |
            | **IMO** | The UN body regulating international shipping: MARPOL (pollution), SOLAS (safety) and sulphur limits. IMO 2020 brought the global switch to VLSFO or scrubbers. |
            | **IMO number** | A permanent seven-digit vessel identifier that never changes, even if the vessel is renamed or reflagged. The authoritative identifier in VMS. |
            | **Flag state** | The country where a vessel is registered and whose law applies on board. Common open registries include Panama, Liberia and the Marshall Islands. |
            | **Classification society** | Sets and enforces technical standards — Lloyd's Register, DNV, Bureau Veritas, ABS, ClassNK. Losing class voids insurance. |
            | **P&I club** | Protection and Indemnity mutual insurer for owner liabilities hull insurance doesn't cover: cargo damage, pollution, collision, crew injury. |

            ## Tanker

            | Term | Meaning |
            |---|---|
            | **MR (Medium Range)** | Product tanker of 25,000–55,000 DWT carrying gasoline, jet fuel, gasoil and naphtha. Segregated tanks allow several grades at once. |
            | **LR1 / LR2 (Large Range)** | LR1 is 55,000–80,000 DWT; LR2 is 80,000–160,000 DWT. They carry clean or dirty products long-haul; LR2s often trade as Aframax crude carriers. |
            | **Clean vs dirty** | Clean tankers carry refined products; dirty tankers carry crude or fuel oil. Switching from dirty to clean needs expensive tank cleaning. |
            | **COW — Crude oil washing** | Washing cargo tanks with the crude itself during discharge. Required by MARPOL on larger crude tankers; reduces cargo left in tanks and improves outturn. |
            | **Outturn** | The quantity actually discharged, measured by the receiving terminal and compared with the B/L to find loss or gain in transit. |
            | **STS — Ship-to-ship transfer** | Moving cargo between two vessels alongside at sea. Used for lightering and consolidation; adds port-call events to the voyage. |
        """),
    },
]

TIER4_QUIZ = [
    {
        "q": "From 2026, what share of verified emissions must shipping companies cover with EUAs?",
        "explanation": "The phase-in runs 40% (2024), 70% (2025) and 100% from 2026.",
        "options": [("40%", False), ("70%", False), ("100%", True), ("50%", False)],
    },
    {
        "q": "For a voyage between an EU port and a non-EU port, what share of emissions falls under EU ETS?",
        "explanation": "Voyages between EU ports are covered 100%; EU to non-EU voyages are covered 50%.",
        "options": [("0%", False), ("50%", True), ("100%", False), ("It depends on the flag state", False)],
    },
    {
        "q": "How should you describe EU ETS and FuelEU support in Sedna VMS?",
        "explanation": "Both are handled through the Prosmar integration and shouldn't be presented as native VMS functionality.",
        "options": [
            ("As a native VMS module", False),
            ("Through the Prosmar integration", True),
            ("Not supported at all", False),
            ("Handled by the customer's P&I club", False),
        ],
    },
    {
        "q": "What is the maximum fuel sulphur content inside an ECA?",
        "explanation": "ECAs cap sulphur at 0.1%, against the 0.5% global limit.",
        "options": [("3.5%", False), ("0.5%", False), ("0.1%", True), ("0%", False)],
    },
    {
        "q": "What does FuelEU Maritime regulate?",
        "explanation": "FuelEU limits the greenhouse gas intensity of energy used on board, in gCO₂eq/MJ — EU ETS covers emission volume.",
        "options": [
            ("The total volume of CO₂ emitted", False),
            ("The GHG intensity of the energy used on board", True),
            ("Sulphur content in ECA zones", False),
            ("Ballast water treatment", False),
        ],
    },
    {
        "q": "Which mechanism belongs to FuelEU rather than EU ETS?",
        "explanation": "FuelEU lets operators pool compliance across vessels and bank or borrow surplus; EU ETS is cap and trade with EUAs.",
        "options": [
            ("Buying and selling EUAs", False),
            ("Pooling compliance across vessels", True),
            ("Surrendering allowances by 30 September", False),
            ("Paying €100 per tonne of uncovered CO₂", False),
        ],
    },
]


ROLE_DATA = {
    "name": "Shipping from Scratch",
    "description": (
        "The commercial shipping industry from the ground up: how money is made, where it goes wrong, "
        "and how Sedna VMS fits in. Based on Becki's industry knowledge guide."
    ),
    "icon": "ti-ship", "color": "blue", "audience": "internal",
    "products": ["vms"], "sort_order": 1,
    "tiers": [
        {"label": "The Industry", "name": "The Industry", "cert_name": "Shipping from Scratch — The Industry", "modules": TIER1_MODULES, "quiz": TIER1_QUIZ},
        {"label": "Charters & Voyage Economics", "name": "Charters & Voyage Economics", "cert_name": "Shipping from Scratch — Charters & Voyage Economics", "modules": TIER2_MODULES, "quiz": TIER2_QUIZ},
        {"label": "Vessels, Operations & Finance", "name": "Vessels, Operations & Finance", "cert_name": "Shipping from Scratch — Vessels, Operations & Finance", "modules": TIER3_MODULES, "quiz": TIER3_QUIZ},
        {"label": "Compliance & Reference", "name": "Compliance & Reference", "cert_name": "Shipping from Scratch — Compliance & Reference", "modules": TIER4_MODULES, "quiz": TIER4_QUIZ},
    ],
}


async def seed(db: AsyncSession):
    result = await db.execute(select(LearningRole).where(LearningRole.name == ROLE_DATA["name"]))
    role = result.scalar_one_or_none()
    if role is None:
        role = LearningRole(
            name=ROLE_DATA["name"], description=ROLE_DATA["description"], icon=ROLE_DATA["icon"],
            color=ROLE_DATA["color"], audience=ROLE_DATA["audience"], products=ROLE_DATA["products"],
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
        tier = Tier(role_id=role.id, label=td["label"], name=td["name"], cert_name=td["cert_name"], sort_order=t_sort)
        db.add(tier)
        await db.flush()
        # The tier quiz sits on the last topic lesson, not on the glossary
        quiz_module = None
        for m_sort, md_ in enumerate(td["modules"]):
            module = Module(
                tier_id=tier.id, title=md_["title"], module_type="a",
                duration_mins=md_["dur"], product="vms", sort_order=m_sort,
                description=md_["description"], learn_items=md_["learn_items"],
                rich_content=md_["rich_content"],
            )
            db.add(module)
            await db.flush()
            if not md_["title"].startswith("Shipping Glossary"):
                quiz_module = module
        for q_sort, qd in enumerate(td["quiz"]):
            question = QuizQuestion(
                module_id=quiz_module.id, question_text=qd["q"],
                explanation=qd.get("explanation", ""), sort_order=q_sort,
            )
            db.add(question)
            await db.flush()
            for o_sort, (text, correct) in enumerate(qd["options"]):
                db.add(QuizOption(question_id=question.id, text=text, is_correct=correct, sort_order=o_sort))
        print(f"  Added tier '{td['label']}' with {len(td['modules'])} lessons and {len(td['quiz'])} quiz questions.")
        added_tiers += 1
    await db.commit()
    print(f"✓ Done — {added_tiers} new tier(s) added this run.")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
