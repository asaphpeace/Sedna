"""Seed the Employee Onboarding learning path.

Unlike seed.py (which TRUNCATEs every table before reseeding), this script
is purely additive: it checks whether an "Employee Onboarding" LearningRole
already exists and, if so, only adds whatever tiers don't already exist
under it by label. Safe to re-run.

This is a first pass covering the 19 modules for which real source content
(Employee Wiki pages) was available at authoring time. Several pages are
still pending (Our Products, Where We Work — 5 of 6 offices, Learn About
Our Industries, Product Hierarchy, Learn to Use HiBob, Learn to Use Slack)
and are deliberately left out rather than guessed at. They can be appended
to their respective TIER*_MODULES lists once that content arrives — the
seed() function's tier-level idempotency means existing tiers are currently
skipped wholesale on a second run, so adding modules to an *existing* tier
will need a follow-up module-level check (see NOTE in seed() below).

Run once via:
    docker compose -f docker-compose.prod.yml exec backend python -m app.seed_onboarding
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine, Base
from app.models import *  # noqa: F401,F403 — registers all models with Base


# ─────────────────────────────────────────────────────────────────────────
# TIER 1 — WELCOME TO SEDNA
# ─────────────────────────────────────────────────────────────────────────

TIER1_MODULES = [
    {
        "title": "Behind the Name",
        "type": "a", "dur": 7, "prod": "general",
        "description": "Why a shipping and email company is named after a sea goddess — and why that story doesn't end once you've heard it.",
        "learn_items": [
            "Where the name Sedna actually comes from",
            "The two sources Bill drew from: a dwarf planet and an Inuit sea goddess",
            "Why this is an ongoing conversation, not a one-time trivia fact",
        ],
        "rich_content": (
            "Sedna is not an acronym and not a play on words. Our founder and CEO, Bill, chose it deliberately, "
            "drawing on two very different sources that ended up pointing at the same idea.\n\n"
            "The first was 90377 Sedna, a dwarf planet out at the edge of our solar system — a piece of "
            "astronomical trivia that stuck with Bill during the search for a name. The second came from an "
            "unrelated trip through Vancouver International Airport, where an art display called the Lorne "
            "Balshine Collection introduced him to Sedna, the goddess of the sea in Inuit culture and histories. "
            "In Inuit oral tradition, Sedna is the mother of sea creatures — sometimes an angry or vengeful "
            "spirit who stirs up ocean storms, calmed only when spiritual leaders visit her undersea dwelling to "
            "comb her tangled hair. The stories vary by region, since Inuit oral histories are dynamic and "
            "carried down rather than fixed in a single text, but the core of who Sedna is and how she came to "
            "be is widely shared.\n\n"
            "Once Bill learned about the sea goddess, the pieces clicked together: the connection to the ocean "
            "and to maritime business, his admiration for the art and culture behind it, the fact that \"Sedna\" "
            "sounds a little like \"send,\" and the dwarf planet's vast, overwhelming distance echoing how email "
            "itself can feel — an unstructured, endless expanse you're trying to bring order to.\n\n"
            "That's also why this isn't just a fun-fact page. As a company, we operate within a colonial system "
            "whether we acknowledge it or not, and naming ourselves after a word that holds real significance "
            "for Indigenous peoples comes with an obligation to keep learning rather than treat the story as "
            "settled. As new team members join, that conversation continues — understanding the land we live "
            "and work on, its histories, and why self-education here matters. If you want to go deeper, the "
            "full page includes primary sources: an Indigenous-voiced retelling of the Sedna story, academic "
            "references on Inuit history, and further reading on Indigenous land acknowledgement — worth a look "
            "beyond this summary."
        ),
    },
    {
        "title": "Our Mission & Where We're Heading",
        "type": "a", "dur": 8, "prod": "general",
        "description": "Why Sedna exists, what we actually build, and what 'one world-class SaaS company' means as our current focus.",
        "learn_items": [
            "The problem Sedna exists to solve",
            "The three product pillars: Email, Trade, Build",
            "What operating as 'one world-class SaaS company' actually requires",
        ],
        "rich_content": (
            "Shipping underpins global trade, energy, and food. When decisions in that industry are unclear or "
            "slow, the impact is real — and shipping has historically been underserved by software built for "
            "other industries. That's the gap Sedna exists to close: we build and operate software that helps "
            "shipping professionals make the right decisions, quickly.\n\n"
            "The shorthand for where we're heading is \"The Operating System for Shipping.\" The industry runs "
            "on conversation — email has become what's sometimes called its accidental operating system — but "
            "conversation alone doesn't give you structure, and structured systems alone don't capture how the "
            "industry actually talks. Our platform is built around three pillars that together try to close "
            "that gap: Sedna Email turns unstructured inbox chaos into organised, searchable context, connecting "
            "chartering, operations, and finance directly to where the conversation already happens. Sedna Trade "
            "brings commercial and operational intelligence — voyage estimates, fixture tracking, settlement — "
            "into that same connected picture, so decisions aren't made in the dark. Sedna Build is the open, "
            "API-first layer underneath both: integrations, automations, and custom actions that mean your "
            "workflows aren't held hostage to a vendor's roadmap.\n\n"
            "As a company, our current focus is deliberately narrow: becoming one world-class SaaS company. That "
            "means three things have to be true at once. We need world-class SaaS performance — running "
            "efficiently, reaching profitability, and making sure customers feel the difference in day-to-day "
            "use. We need to become the industry's choice — winning new customers and expanding with existing "
            "ones by delivering the capabilities the market actually values. And we need to operate as one "
            "company — one unified brand and narrative, one source of truth, one standard for how we work "
            "together, rather than a patchwork of teams and tools that happen to share a logo.\n\n"
            "None of that is automatic. It depends on the choices we make about what to prioritise, what to "
            "invest in, and — just as deliberately — what to say no to. As you settle into your role, you'll "
            "see this focus show up in very concrete ways: what gets built next, what gets simplified, and what "
            "gets left alone on purpose."
        ),
    },
]

TIER1_QUIZ = [
    {
        "q": "Which two sources did Bill draw on when naming the company Sedna?",
        "explanation": "The dwarf planet 90377 Sedna, and the Inuit sea goddess Sedna encountered via the Lorne Balshine Collection at YVR.",
        "options": [
            ("A Greek myth and a constellation", False),
            ("A dwarf planet and an Inuit sea goddess", True),
            ("A founder's family name and a coastal town", False),
            ("An acronym for the founding team", False),
        ],
    },
    {
        "q": "Why does Sedna treat the story of its name as an ongoing conversation rather than a settled fact?",
        "explanation": "Because the name holds real significance for Indigenous peoples, and the company operates within a colonial system that deserves continued reflection, not a one-time acknowledgement.",
        "options": [
            ("Because the story keeps changing for legal reasons", False),
            ("Because it's an active learning and reconciliation process, not a trivia fact", True),
            ("Because the name might change again soon", False),
            ("It doesn't — it's considered fully settled", False),
        ],
    },
    {
        "q": "What problem does Sedna exist to solve?",
        "explanation": "Shipping underpins global trade, energy, and food, and unclear or slow decisions in the industry have real impact — Sedna exists to help make those decisions better.",
        "options": [
            ("Slow decision-making in global shipping", True),
            ("A shortage of licensed ship brokers", False),
            ("Port congestion during peak season", False),
            ("Currency conversion for freight invoices", False),
        ],
    },
    {
        "q": "What are Sedna's three product pillars?",
        "explanation": "Sedna Email, Sedna Trade, and Sedna Build together make up 'The Operating System for Shipping.'",
        "options": [
            ("Email, Trade, Build", True),
            ("Chartering, Claims, Finance", False),
            ("VMS, CRM, ERP", False),
            ("Inbox, Ledger, API", False),
        ],
    },
    {
        "q": "What three things does 'becoming one world-class SaaS company' require, according to our current focus?",
        "explanation": "World-class SaaS performance, becoming the industry's choice, and operating as one company.",
        "options": [
            ("Lower prices, more features, faster hiring", False),
            ("World-class SaaS performance, industry's choice, one company", True),
            ("A new logo, a new office, a new CEO", False),
            ("More products, more regions, more headcount", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# TIER 2 — GETTING STARTED
# ─────────────────────────────────────────────────────────────────────────

TIER2_MODULES = [
    {
        "title": "Your Onboarding Journey",
        "type": "a", "dur": 10, "prod": "general",
        "description": "The tool checklist, the three objectives, and how Sedna structures your first weeks.",
        "learn_items": [
            "The tool provisioning checklist for day one",
            "The three objectives your onboarding is built around",
            "The named risks and how Sedna plans to handle them",
        ],
        "rich_content": (
            "You're joining a company that delivers cloud-based solutions to shipping professionals worldwide, "
            "and this first stretch is designed to get you oriented quickly without burying you.\n\n"
            "On day one, you should already have access to a set of standard tools: a MacBook, Mobile Device "
            "Management (MDM) enrolment, Google, HiBob, 1Password, Slack, Sedna Email, and Claude. If anything "
            "on that list is missing, that's a People Team question, not something to quietly work around.\n\n"
            "Onboarding is built around three objectives: getting familiar with Sedna's culture, values, brand, "
            "and mission; equipping you with the knowledge to actually do your job well; and helping you feel "
            "connected to your team and the wider company. To get there, the programme leans on four tactics — "
            "collaborative learning experiences where you learn alongside other new starters, a buddy who's "
            "there to answer questions and just be someone to talk to, a feedback loop so you can flag what's "
            "working or not, and continuous learning that carries on well past your first weeks.\n\n"
            "By the end of onboarding, you'll have been through orientation sessions covering key people, "
            "departments, and company OKRs; role-specific training on the products, tools, and workflows you'll "
            "actually use; a personal performance plan; shadowing time with experienced team members; and "
            "regular check-ins with your manager. None of that happens by accident — it's tracked.\n\n"
            "We're also upfront about where onboarding tends to go wrong. Feeling overwhelmed by information is "
            "handled by breaking training into smaller chunks and layering support around you — your buddy, "
            "retrospectives, a dedicated Slack channel. Adjusting to a new environment is where your buddy and "
            "team activities matter most. And technical access issues — a login that doesn't work, a tool you "
            "can't reach — go to dedicated IT support, with your buddy as a second line of help. If any of "
            "these risks show up for you in practice, that's expected, not a sign something's gone wrong."
        ),
    },
    {
        "title": "Understanding Your Probation",
        "type": "a", "dur": 8, "prod": "general",
        "description": "The 6-month probation journey managed in Bob, month by month — and the shorter Denmark track.",
        "learn_items": [
            "The standard 6-month timeline vs. the 3-month Denmark track",
            "What happens at each Bob-triggered check-in",
            "What happens if expectations aren't being met",
        ],
        "rich_content": (
            "Every new Sedna employee goes through a probation period, managed almost entirely through Bob "
            "(HiBob) — tasks and check-ins trigger automatically off your start date, so you shouldn't need to "
            "chase anything. The standard length is 6 months; Denmark runs a legally-compliant 3-month version "
            "instead. Three groups are involved throughout: you (participating in check-ins and any required "
            "self-assessments), your manager (leading check-ins and completing reviews), and the People Team "
            "(overseeing consistency and confirming outcomes).\n\n"
            "On the standard 6-month track, Month 1 is a straightforward 1:1 to check how onboarding is going "
            "and make sure your role and expectations are clear. Month 2 shifts to early performance and "
            "feedback, and aligning on priorities for the coming weeks. Month 3 is the Midpoint Review — you "
            "complete a short self-assessment, your manager completes their own, and you meet to compare notes, "
            "agree focus areas, and confirm what \"on track\" looks like. Month 5 is a progress check where your "
            "manager reviews progress since the midpoint and you both confirm whether things are on track for a "
            "positive outcome. Month 6 is the outcome itself: your manager submits a recommendation in Bob, the "
            "People Team reviews and confirms it, and the final decision is shared with you as probation closes.\n\n"
            "Denmark's 3-month version follows the same spirit on a shorter clock: a Month 1 check-in, a "
            "Midpoint Review (self-assessment plus manager assessment), and then the outcome stage, which adds a "
            "Manager | HR Pre-Probation Closure Discussion before the People Team confirms and shares the final "
            "decision.\n\n"
            "If performance isn't yet at the required level but improvement looks achievable, the option isn't "
            "simply to let probation lapse badly — managers follow the Probation Extension guide, which exists "
            "specifically to make sure any extension is handled fairly, consistently, and on time rather than as "
            "a last-minute surprise."
        ),
    },
]

TIER2_QUIZ = [
    {
        "q": "Which tool is NOT on the standard day-one provisioning checklist?",
        "explanation": "The checklist covers MacBook, MDM, Google, HiBob, 1Password, Slack, Sedna Email, and Claude — not a generic project management tool.",
        "options": [
            ("1Password", False), ("HiBob", False),
            ("A generic project management tool", True), ("Claude", False),
        ],
    },
    {
        "q": "What are the three objectives Sedna's onboarding programme is built around?",
        "explanation": "Understanding culture/values/brand/mission, building job-specific knowledge, and feeling connected to team and company.",
        "options": [
            ("Speed, cost, compliance", False),
            ("Culture & mission, job knowledge, connection to team/company", True),
            ("Sales targets, retention, promotion readiness", False),
            ("Tool access, payroll setup, badge issuance", False),
        ],
    },
    {
        "q": "How long is the standard probation period, and what's the exception?",
        "explanation": "6 months standard; Denmark runs a legally-compliant 3-month version instead.",
        "options": [
            ("3 months everywhere", False),
            ("6 months standard, 3 months in Denmark", True),
            ("12 months everywhere", False),
            ("6 months everywhere, no exceptions", False),
        ],
    },
    {
        "q": "What happens during the Month 3 Midpoint Review?",
        "explanation": "You complete a self-assessment, your manager completes their own, and you meet to compare views and agree focus areas.",
        "options": [
            ("Only your manager completes an assessment", False),
            ("You and your manager each complete an assessment, then meet to compare", True),
            ("The People Team makes the final call without a meeting", False),
            ("Nothing — Month 3 has no scheduled activity", False),
        ],
    },
    {
        "q": "If a manager believes performance isn't yet at the required level but improvement is possible, what should they do?",
        "explanation": "Follow the Probation Extension – Manager Guide, so the process is handled fairly, consistently, and on time.",
        "options": [
            ("Let probation lapse without further action", False),
            ("Follow the Probation Extension – Manager Guide", True),
            ("Immediately terminate employment", False),
            ("Skip straight to the Month 6 outcome form", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# TIER 3 — POLICIES & COMPLIANCE
# ─────────────────────────────────────────────────────────────────────────

TIER3_MODULES = [
    {
        "title": "Code of Conduct Essentials",
        "type": "a", "dur": 14, "prod": "general",
        "description": "The ethical foundation every Sedna employee, contractor, and third party is expected to uphold.",
        "learn_items": [
            "Who this Code applies to, and where local law takes precedence",
            "The 7 core ethical principles and how conflicts of interest get handled",
            "How to report a concern, and what protection you have for doing so",
        ],
        "rich_content": (
            "Sedna's Global Code of Conduct sets the ethical foundation for how we work, communicate, and make "
            "decisions across every region and role — permanent staff, contractors, freelancers, directors, and "
            "interns alike. It applies wherever work happens: on premises, remote, at a client site, on a plane, "
            "or in a Slack thread. Because Sedna operates internationally, local law always takes precedence "
            "where it conflicts with the Code, and country-specific addenda exist for the UK, Norway, Denmark, "
            "Greece, South Africa, and Singapore.\n\n"
            "Seven core principles run through the whole Code: act with integrity, exercise professionalism, "
            "comply with laws and policies, respect people, take accountability, use authority responsibly, and "
            "make ethical decisions. Leaders carry an elevated version of this — modelling the behaviour, "
            "addressing misconduct promptly, and making sure their teams actually understand their obligations, "
            "not just sign off on reading them.\n\n"
            "Conflicts of interest get particular attention because they're common and easy to miss. A conflict "
            "is anything — a relationship, a financial interest, an outside commitment — that interferes, or "
            "could reasonably appear to interfere, with acting in Sedna's best interest. The expectation isn't "
            "that conflicts never happen; it's that they're disclosed immediately, to your manager or the People "
            "team, rather than concealed. A useful test: would someone reasonably question your impartiality "
            "here? If the answer is yes or even unsure, disclose. The same logic extends to bribery and "
            "corruption, where Sedna holds a strict zero-tolerance line — no bribes, kickbacks, or facilitation "
            "payments, ever, even where a small payment might be locally customary, and particular care applies "
            "around government officials and gifts/hospitality.\n\n"
            "The Code also covers fair treatment and inclusion (discrimination and harassment are strictly "
            "prohibited), health and safety (including psychological safety — use your leave, watch out for "
            "colleagues' workloads), confidentiality and data security, and acceptable use of company assets and "
            "social media. If you ever see something that looks inconsistent with any of this, you're expected "
            "to raise it — to your manager, the People team, the CFO, the CEO, or a designated whistleblowing "
            "channel — and retaliation against anyone who raises a concern in good faith is strictly prohibited. "
            "Violations, when they do happen, are investigated fairly and confidentially, with consequences "
            "ranging from coaching up to termination depending on severity."
        ),
    },
    {
        "title": "Using AI Tools Responsibly",
        "type": "a", "dur": 12, "prod": "general",
        "description": "The single distinction that governs everything: Product Data (never shared with AI) vs. Business Data (permitted with care).",
        "learn_items": [
            "Product Data vs. Business Data, and why the distinction matters more than which system data lives in",
            "What's approved, what's prohibited, and why screenshots count the same as pasted text",
            "What to do if you accidentally share something you shouldn't have",
        ],
        "rich_content": (
            "Sedna's AI Tools Usage Policy exists to let you actually use AI productively — Gemini, Claude, and "
            "similar tools — while keeping us ISO 27001 compliant and protecting the data our customers trust us "
            "with. Everything in the policy comes down to one distinction. Product Data is customer email "
            "content, metadata, voyage data, vessel data, financial data, and logs that we process on our "
            "customers' behalf — this is confidential and must never go into an AI tool. Business Data is our "
            "own internal operational data — Salesforce records, product performance data, redacted support "
            "tickets, billing information — which is permitted, with care.\n\n"
            "That distinction depends on content, not source. A Salesforce record that happens to contain "
            "forwarded customer email content is still Product Data, regardless of which system it's sitting "
            "in. The same caution applies to describing customer behaviour in enough detail that they could be "
            "identified, and to any system connected to an AI tool via integrations (Slack, Drive, etc.) — if "
            "Product Data ends up in a connected system, it's exposed even if you never typed it into an AI tool "
            "directly.\n\n"
            "In practice, this means things like analysing Salesforce or Sage data, drafting customer "
            "communications, reviewing code, and building internal reports are all fine. What's never acceptable "
            "is putting in actual customer email content, email metadata, delivery logs, voyage or vessel data, "
            "customer financial information, or any credentials — and this holds regardless of format. A "
            "screenshot of a customer email, a PDF export of logs, or an attached spreadsheet of metadata is "
            "treated identically to pasting the raw text; the method of sharing doesn't change what's prohibited.\n\n"
            "A few safeguards back this up: only Sedna-provided enterprise versions of approved tools may be "
            "used for anything touching business data (never free/consumer versions), AI-capable browser "
            "extensions like agentic browsing tools are off-limits, and any new integration between an AI tool "
            "and an internal system needs formal approval before it's switched on. If you're ever unsure whether "
            "something is safe to share, the rule is simple: sanitise it or ask first — don't guess. And if you "
            "do accidentally input something you shouldn't have, stop the session immediately, document what was "
            "shared and where, and report it to privacy@sedna.com within the hour. Reported mistakes are "
            "investigated proportionately and treated as a learning moment; the policy's goal is to enable safe "
            "AI use, not to make people afraid to speak up."
        ),
    },
    {
        "title": "Information Privacy & Security",
        "type": "a", "dur": 10, "prod": "general",
        "description": "How Sedna's ISO 27001/27701-based Information Privacy and Security Management System actually works, and where you fit into it.",
        "learn_items": [
            "What the IPSMS is for, and who it applies to",
            "The three tiers of responsibility: IPSSC, managers, individuals",
            "What to do if something doesn't fit the policy as written",
        ],
        "rich_content": (
            "Sedna's Information Privacy and Security Policy sets the guidelines for protecting every piece of "
            "information Sedna controls or processes — every device, network, application, and system, and "
            "every employee, contractor, and temporary staff member who touches them. The whole framework is "
            "built on ISO 27001 and ISO 27701, and its objectives are straightforward: protect confidentiality, "
            "integrity, and availability of company information (including personal data under GDPR), catch and "
            "respond to incidents quickly, manage third-party supplier risk, and build a genuine culture of "
            "security through training rather than a once-a-year checkbox.\n\n"
            "Responsibility runs in three tiers. The Information and Privacy Security Steering Committee "
            "(IPSSC) coordinates and monitors the whole management system, oversees risk assessments, and "
            "approves policy. Managers are responsible for making sure their own teams actually comply, and for "
            "escalating risks or incidents rather than sitting on them. And every individual — that's you — is "
            "responsible for protecting the information assets you touch day to day and reporting anything that "
            "looks like a suspected or actual security incident, promptly.\n\n"
            "Compliance isn't just assumed; it's actively monitored, through the IPSSC, department managers, and "
            "periodic independent audits (both internal and external), with performance metrics feeding back "
            "into continuous improvement of the system. Security also isn't bolted on after the fact — every "
            "project, regardless of type, is expected to carry a documented information security risk "
            "assessment from the start.\n\n"
            "Sometimes a policy genuinely can't be followed for a specific technical or logistical reason — "
            "that's what the exemption/exception process is for. Rather than quietly working around a control, "
            "you'd submit a written request to the IPSSC stating the specific requirement, the business "
            "justification, the risk, and a proposed mitigation with a monitoring plan and timeline. Failing to "
            "comply with information security policy without going through that process can result in "
            "disciplinary and legal action, up to dismissal, contract cancellation, or in serious cases, "
            "criminal or civil consequences — which is exactly why raising a concern or requesting an exception "
            "early is always the better path."
        ),
    },
]

TIER3_QUIZ = [
    {
        "q": "What's the core distinction in Sedna's AI Tools Usage Policy?",
        "explanation": "Product Data (customer email content, metadata, voyage/vessel data — never shared with AI) vs. Business Data (internal operational data — permitted with care).",
        "options": [
            ("Free tools vs. paid tools", False),
            ("Product Data vs. Business Data", True),
            ("Text input vs. file upload", False),
            ("Internal staff vs. contractors", False),
        ],
    },
    {
        "q": "You want to share a screenshot of a customer's email dashboard with an AI tool instead of pasting the text. Is that allowed?",
        "explanation": "No — screenshots, PDFs, and attachments are treated identically to pasted text. If the content is prohibited, the format doesn't matter.",
        "options": [
            ("Yes, screenshots are treated differently from text", False),
            ("No — the prohibition applies regardless of format", True),
            ("Only if it's a free AI tool", False),
            ("Only if the customer has approved it", False),
        ],
    },
    {
        "q": "If you accidentally paste customer data into an AI tool, what's the first thing you should do?",
        "explanation": "Stop the session immediately, then document what was shared and report it to privacy@sedna.com within an hour.",
        "options": [
            ("Try to delete or unsend the message", False),
            ("Stop the session immediately and report it", True),
            ("Wait to see if it causes a problem before reporting", False),
            ("Only report it if a customer notices", False),
        ],
    },
    {
        "q": "A conflict of interest exists at Sedna. What does the Code of Conduct expect you to do?",
        "explanation": "Disclose it immediately — conflicts aren't prohibited outright, but concealing one is.",
        "options": [
            ("Handle it quietly on your own", False),
            ("Disclose it immediately to your manager or the People team", True),
            ("Wait until asked directly", False),
            ("Only disclose if it involves money", False),
        ],
    },
    {
        "q": "Which of these is one of Sedna's 7 core ethical principles?",
        "explanation": "The 7 principles are: integrity, professionalism, legal/policy compliance, respect for people, accountability, responsible use of authority, and ethical decision-making.",
        "options": [
            ("Maximise quarterly revenue", False),
            ("Act with integrity", True),
            ("Always agree with your manager", False),
            ("Prioritise speed over accuracy", False),
        ],
    },
    {
        "q": "What ISO standards is Sedna's Information Privacy and Security Management System (IPSMS) built on?",
        "explanation": "ISO 27001 (information security) and ISO 27701 (privacy information management).",
        "options": [
            ("ISO 9001 and ISO 14001", False),
            ("ISO 27001 and ISO 27701", True),
            ("SOC 1 and SOC 2 only", False),
            ("PCI-DSS and HIPAA", False),
        ],
    },
    {
        "q": "Who is responsible for reporting suspected security incidents at Sedna?",
        "explanation": "Every individual — protecting information assets and reporting incidents is not limited to IT or the IPSSC.",
        "options": [
            ("Only the IT department", False),
            ("Every individual, regardless of role", True),
            ("Only people managers", False),
            ("Only the IPSSC", False),
        ],
    },
    {
        "q": "What should you do if a security policy genuinely can't be followed for a technical reason?",
        "explanation": "Submit a written exemption/exception request to the IPSSC with justification, risk, and a mitigation plan — rather than quietly working around it.",
        "options": [
            ("Quietly work around it and move on", False),
            ("Submit a written exemption request to the IPSSC", True),
            ("Ignore it since it's a one-time issue", False),
            ("Escalate directly to a regulator", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# TIER 4 — GROWTH & PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────

TIER4_MODULES = [
    {
        "title": "Our Levelling Framework",
        "type": "a", "dur": 10, "prod": "general",
        "description": "The IC and M tracks, the level matrix, and why role levels at Sedna are rarely as clean-cut as they look on paper.",
        "learn_items": [
            "The Individual Contributor (IC) track vs. the People Manager (M) track",
            "How level placement actually gets decided",
            "Why responsibilities at Sedna's size are often 'fluid' rather than clean-cut",
        ],
        "rich_content": (
            "Sedna's career levelling framework gives a standardised way to categorise roles by scope, impact, "
            "seniority, and skill — and it exists to bring consistency to four things: what success looks like "
            "and how it's evaluated, how career growth and promotion criteria work, how compensation gets "
            "benchmarked fairly against the market, and how hiring stays consistent as the company grows. It's "
            "meant to evolve over time, not to be read as an exhaustive checklist — think of it as a foundation "
            "for performance and development conversations, not the final word.\n\n"
            "There are two distinct tracks. The Individual Contributor (IC) track is about deep technical "
            "mastery and high-impact execution as an individual; the People Manager (M) track is about "
            "providing support, leadership, and growth to people on the IC track. About 90% of IC roles "
            "sit within IC1–IC3, and IC5/IC6 are genuinely rare — IC6 in particular is reserved for deep "
            "experts, the kind of role a shipping-industry veteran might hold advising leadership on global "
            "trends. On the M track, not every department fills every level (an M5 Head-of might lead ICs "
            "directly with no M4 in between), and M4–M6 are split into sub-levels specifically so growth is "
            "possible even when the underlying role doesn't change shape.\n\n"
            "Level placement isn't purely mechanical — it factors in a real combination of experience, "
            "knowledge, and role expectations. A first-time people lead, for instance, typically lands at M4 "
            "even if they're already running a full function, simply because the managerial track itself is "
            "new for them. And because Sedna is still growing and reshaping itself, responsibilities often "
            "aren't clean-cut: an IC2 might already be coaching new joiners, or an M4 might be running a full "
            "function on their own. That overlap is expected, not a sign the framework is broken.\n\n"
            "Some departments layer more detail on top of the general framework in the form of a specialised "
            "Job Architecture or Competency Map — while your overall Level (say, IC3 or M4) sets your general "
            "seniority and impact expectations, your department's own map might spell out exactly what that "
            "looks like in your day-to-day work. If you're ever unsure which applies to you, that's a "
            "reasonable thing to ask your manager directly."
        ),
    },
    {
        "title": "How Performance Works at Sedna",
        "type": "a", "dur": 10, "prod": "general",
        "description": "Why performance at Sedna is a continuous conversation, not an annual event — and the three things it's actually measured on.",
        "learn_items": [
            "The company's responsibilities to you vs. your responsibilities to the company",
            "The three measurement pillars: Deliverables, Skills, Values",
            "Who's eligible for the full Growth & Performance Review, and when",
        ],
        "rich_content": (
            "Sedna doesn't treat performance as something that happens once or twice a year in a single review "
            "meeting. The intent is a continuous performance culture — regular conversations that drive clarity, "
            "growth, and impact, so nobody is surprised by feedback that could have surfaced months earlier. "
            "Performance itself just means how well you deliver against the expectations set for your role — a "
            "shared journey between you, your manager, and the company, not something done to you.\n\n"
            "That shared journey runs in both directions. Sedna's responsibility to you is clarity on your "
            "role, clear goals, clear behavioural expectations, real-time feedback on how you're doing, and "
            "ongoing support from your manager and the People team when something needs to get back on track. "
            "Your responsibility back is to stay accountable for your core duties, aim to be genuinely on track "
            "against your goals, live the culture, take ownership of your own growth, and — importantly — raise "
            "your hand early if you need support rather than waiting for a formal review to surface it.\n\n"
            "Performance is measured across three things: Deliverables (what you actually delivered relative to "
            "expectations and goals), Skills (how effectively you deliver it, given the knowledge, experience, "
            "and responsibility expected at your level), and Values (how well you demonstrate and role-model "
            "Sedna's expected behaviours day to day). None of this works without roles, goals, and values being "
            "clearly defined in the first place — if you're ever unclear on any of the three from where you "
            "stand, that's a conversation for your manager, not something to guess at.\n\n"
            "The formal Growth & Performance Review is the flagship moment in that broader cycle, but it's not "
            "available to everyone at every point — you're only eligible once you've passed probation and are "
            "in a permanent role (not a project contractor, fixed-term hire, or intern). Reviews are scored "
            "using labels rather than numbers, specifically so conversations stay human rather than reducing to "
            "a single digit — most team members are expected to land at \"Right on Track,\" which is meant as "
            "a genuinely solid outcome, not a middling one."
        ),
    },
    {
        "title": "Completing Your Review",
        "type": "a", "dur": 15, "prod": "general",
        "description": "A practical walkthrough of the four review sections: Deliverables, Skills, Values, and Development.",
        "learn_items": [
            "How to write a strong Deliverables section, whatever kind of role you're in",
            "The difference between Skills (capability) and Deliverables (outcomes)",
            "Why the Development section isn't about having it all figured out",
        ],
        "rich_content": (
            "When your first full review cycle arrives, it breaks into four sections, and each one is asking a "
            "genuinely different question.\n\n"
            "Deliverables asks: what have I delivered that mattered? How you answer depends on your role type — "
            "KPI-driven roles (Sales, Marketing) should speak to targets and standout results; project-based "
            "roles (Engineering, Product) should speak to what they led, co-owned, or supported and whether it "
            "landed on time and in scope; goal-focused or operational roles (People, Finance) should speak to "
            "process improvements and efficiency unlocked. Whatever the role, a strong answer describes real "
            "outcomes with specific examples, not a bullet-point list of everything you touched — a short, "
            "honest paragraph beats an exhaustive inventory.\n\n"
            "Skills is a different question entirely: not what you delivered, but how confidently and "
            "independently you're showing the knowledge, experience, and responsibility expected at your level. "
            "Use your actual level (IC3, M1, whatever it is) as the benchmark, and be honest about where you're "
            "confident and where you'd like to stretch — this section rewards self-awareness, not a claim that "
            "everything is already mastered.\n\n"
            "Values asks how you've demonstrated Sedna's values in your actual decisions and behaviour, scored "
            "against the Values Assessment Criteria. The bar here is specificity: \"I regularly bring in customer "
            "data to inform decisions\" is a real reflection; a generic one-liner isn't enough to give your "
            "manager a real picture of where you shine.\n\n"
            "Development is the forward-looking piece: where do you want to grow in the next six months? It "
            "isn't a polished development plan — it's an honest reflection connecting what came up in the other "
            "three sections to where you want to stretch next, whether that's a technical skill, more confidence "
            "presenting to stakeholders, or exposure to a new part of the product. The more specific you are "
            "here, the easier it is for your manager to actually shape support around it — vague answers get "
            "vague support back."
        ),
    },
    {
        "title": "Your First Reflection & Development Check-In",
        "type": "a", "dur": 8, "prod": "general",
        "description": "The early-stage, informal check-in designed for people who've just passed probation and aren't yet in the full review cycle.",
        "learn_items": [
            "Who this check-in is for, and why it isn't a formal review",
            "The five things it asks you to reflect on",
            "What 'good' looks like when you fill it out"
        ],
        "rich_content": (
            "Before you're eligible for the full Growth & Performance Review, there's a lighter-touch check-in "
            "built specifically for two groups: new joiners who've just passed probation but aren't yet in the "
            "full review cycle, and team members from newly acquired businesses still finding their footing at "
            "Sedna. It's explicitly not a formal review — it's a moment to pause and reflect on how your time "
            "here has started, what's working, and what would help you thrive.\n\n"
            "The form walks through five things. First, how things are going so far — what's felt rewarding, "
            "what still feels unclear, whether the team and ways of working are landing well. Second, what "
            "you're enjoying or proud of — where you feel you're already adding value and when you feel at your "
            "best. Third, what's been challenging or unclear — genuinely useful territory, since this is where "
            "onboarding gaps or unclear ownership tend to surface. Fourth, what you want to grow or develop over "
            "the next 3–6 months. And fifth, what support you might need to get there — coaching, clearer "
            "goals, more regular check-ins, or just better access to information.\n\n"
            "You don't need to write an essay. The goal is to capture what's working well, be honest about "
            "what's unclear or missing, show curiosity about your own development, and give your manager enough "
            "to actually support your next chapter — not to arrive with a polished, fully-resolved account of "
            "your first months. Vague answers here just mean your manager has less to work with; specific, "
            "honest ones are what make this actually useful rather than a box-ticking exercise."
        ),
    },
]

TIER4_QUIZ = [
    {
        "q": "What are Sedna's two career tracks?",
        "explanation": "Individual Contributor (IC) — deep technical mastery and execution — and People Manager (M) — leadership and team growth.",
        "options": [
            ("Junior and Senior", False),
            ("Individual Contributor (IC) and People Manager (M)", True),
            ("Technical and Non-Technical", False),
            ("Permanent and Contract", False),
        ],
    },
    {
        "q": "Roughly what proportion of IC roles at Sedna sit within IC1–IC3?",
        "explanation": "About 90% of IC roles sit within IC1 to IC3 — IC5 and IC6 are genuinely rare.",
        "options": [
            ("About 50%", False), ("About 90%", True),
            ("Nearly 100%, IC4+ barely exists", False), ("About 25%", False),
        ],
    },
    {
        "q": "A first-time people manager is placed at M4 even though they already run a full function. Why?",
        "explanation": "Level placement considers experience and role expectations together — being new to the managerial track itself is a factor, even with a full function underneath it.",
        "options": [
            ("It's a data entry mistake", False),
            ("Placement factors in that the managerial track itself is new for them", True),
            ("M4 is always the ceiling for team leads", False),
            ("They must have failed a review", False),
        ],
    },
    {
        "q": "What three things is performance measured on at Sedna?",
        "explanation": "Deliverables, Skills, and Values.",
        "options": [
            ("Deliverables, Skills, Values", True),
            ("Attendance, Output, Tenure", False),
            ("Revenue, Retention, Referrals", False),
            ("Speed, Quality, Cost", False),
        ],
    },
    {
        "q": "Who is eligible for the full Growth & Performance Review?",
        "explanation": "Employees who've passed probation and are in a permanent role — not project contractors, fixed-term hires, or interns.",
        "options": [
            ("Everyone, from day one", False),
            ("Permanent employees who've passed probation", True),
            ("Only People Managers", False),
            ("Only employees above IC3", False),
        ],
    },
    {
        "q": "In the Deliverables section of a review, what should a strong answer include?",
        "explanation": "Real outcomes with specific examples, tailored to your role type — not a bullet list of every task touched.",
        "options": [
            ("A complete list of every task completed", False),
            ("Real outcomes with specific examples, relevant to your role type", True),
            ("Just a numeric self-score", False),
            ("A comparison against a colleague's output", False),
        ],
    },
    {
        "q": "What's the difference between the Skills and Deliverables sections of a review?",
        "explanation": "Deliverables is about outcomes (what you delivered); Skills is about underlying capability (how confidently and independently you operate at your level).",
        "options": [
            ("There's no real difference", False),
            ("Deliverables = outcomes; Skills = underlying capability at your level", True),
            ("Skills covers technical roles only", False),
            ("Deliverables is scored, Skills isn't", False),
        ],
    },
    {
        "q": "Who is the 'Reflection & Development Check-In' specifically designed for?",
        "explanation": "New joiners who've just passed probation but aren't yet in the full review cycle, and team members from newly acquired businesses.",
        "options": [
            ("Everyone, every quarter", False),
            ("New joiners post-probation and staff from newly acquired businesses", True),
            ("Only People Managers", False),
            ("Only employees under formal performance improvement plans", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# TIER 5 — SHIPPING & INDUSTRY FUNDAMENTALS
# ─────────────────────────────────────────────────────────────────────────

TIER5_MODULES = [
    {
        "title": "Maritime 101: Who's Who in Shipping",
        "type": "a", "dur": 25, "prod": "general",
        "description": "The customer roles, vessel types, and fixture lifecycle behind almost everything Sedna builds.",
        "learn_items": [
            "The core customer categories: Cargo Owners, Vessel Owners, Brokers, Agents, Charterers, Operators",
            "The three charter types: Voyage, Time, and Bareboat",
            "The Pre-Fixture → Fixture → Post-Fixture lifecycle",
        ],
        "rich_content": (
            "The movement of goods by sea makes up the vast majority of international trade, and the pain "
            "traditional email causes in that process is exactly why Sedna's main customer base sits in "
            "shipping. Customers broadly fall into four categories — Cargo Owners, Vessel Owners, Brokers, and "
            "Agents — though several other teams orbit around them.\n\n"
            "Cargo Owners (Cargill, Bunge, Glencore/Viterra, Rio Tinto, Fortescue) have an economic interest in "
            "the goods being moved — cargo is what makes vessels sail in the first place. Vessel Owners "
            "(Norden, Clipper, Fednav, Swire Bulk) have an economic interest in the transport itself, selling "
            "capacity rather than owning the goods, though some companies play both roles at once. Brokers "
            "(Ifchor, Affinity, Worldwide Shipping & Chartering) specialise in negotiation, connecting cargo and "
            "vessel owners for a commission. Port Agents (Monson, Transmarine, Wallem) are local representatives "
            "who arrange tugs, pilots, crew changes, and cash for the master, and who account for a port call's "
            "costs — called port disbursements — settling them against a pre-payment once the call is complete.\n\n"
            "Charterers (also called traders) are the dealmakers — they negotiate with brokers to \"fix\" a "
            "ship, aiming to source the optimal shipping solution. That deal takes one of three shapes. A "
            "Voyage Charter hires a vessel and crew for a single voyage between a load and discharge port, "
            "billed per ton or lump sum, with the owner covering port/fuel/crew costs; run over laytime and the "
            "charterer owes demurrage, come in under and the owner may owe despatch. A Time Charter hires the "
            "vessel for a period, with the owner supplying vessel and crew but the charterer choosing ports, "
            "route, and speed, paying fuel, port charges, and daily hire. A Bareboat Charter goes further still "
            "— the charterer takes the hull and machinery and hires their own crew or management company "
            "entirely.\n\n"
            "Beyond the deal itself, Operators (Oldendorff, Bunge, G2Ocean) manage the voyage from shore once a "
            "ship is fixed — bunker quality and pricing, routing, keeping the ship earning at every stage. "
            "Managers handle technical or full ship management on the owner's or charterer's behalf, sometimes "
            "including commercial and financial administration too. Commodity Traders (Cargill, Rio Tinto, "
            "Glencore) buy and sell the physical goods themselves, often driven by expected market moves. "
            "Freight Forwarders package the whole logistics chain for a shipper without moving the goods "
            "themselves, and a Bunkers team focuses purely on securing the best fuel deals in the right places.\n\n"
            "Vessels themselves get grouped by what they carry and how big they are: dry bulk (Handy/Handymax, "
            "Panamax, Capesize), wet bulk/tankers (crude, clean products), specialty (break bulk, Ro-Ro car "
            "carriers), and container vessels, whose capacity is measured in TEU (twenty-foot-equivalent units) "
            "— newer ships can carry 18,000+ TEU, roughly 9,000 containers.\n\n"
            "Trade execution splits into Domestic (managing import/export across the water without operating "
            "the vessel — closer to a supply-chain function) and International (managing delivery to the "
            "customer by land, including warehousing and inland transport). And the deal itself moves through "
            "three stages. Pre-Fixture is where a broker gathers everything needed before going to market — "
            "cargo type and quantity, load/discharge ports and rates, laycan, commission — and checks the "
            "charterer's reputation and recent shipment history. Fixture is the negotiation itself: an initial "
            "rate offer, full terms and conditions, back-and-forth revisions, and finally a signed Charter "
            "Party once all subjects are lifted. Post-Fixture covers execution — nominating agents at each port, "
            "monitoring loading or discharge daily, checking Notice of Readiness and Statement of Facts for any "
            "demurrage, and settling freight and commission once the voyage completes."
        ),
    },
    {
        "title": "The Cargo Movement Process",
        "type": "v", "dur": 8, "prod": "general",
        "description": "A video walkthrough of how cargo actually moves from origin to destination.",
        "learn_items": ["The end-to-end cargo movement process, visually walked through"],
        "video_url": "https://drive.google.com/file/d/1S3noZyMkYJ85zDhXTeuClHoS_rGobnp5/view?usp=drive_link",
    },
    {
        "title": "An Introduction to Companies Involved in the Process",
        "type": "v", "dur": 13, "prod": "general",
        "description": "A video introduction to the companies and roles that make up the shipping industry.",
        "learn_items": ["The company types introduced in Maritime 101, shown in context"],
        "video_url": "https://drive.google.com/file/d/1x_42Mn12Nmlsbs5WV-sp9WLdWF60wIMZ/view?usp=drive_link",
    },
    {
        "title": "Chartering Managers",
        "type": "v", "dur": 4, "prod": "general",
        "description": "A short video on the Chartering Manager persona.",
        "learn_items": ["What a Chartering Manager does day to day"],
        "video_url": "https://drive.google.com/file/d/14GPEk9uTQvwYo1StFK__HtDPKl-qW_ck/view?usp=drive_link",
    },
    {
        "title": "Ship Brokers",
        "type": "v", "dur": 3, "prod": "general",
        "description": "A short video on the Ship Broker persona.",
        "learn_items": ["What a Ship Broker does day to day"],
        "video_url": "https://drive.google.com/file/d/1sD1GwHfG6fgnJqUtiF7qfW9w1SGWZjE2/view?usp=drive_link",
    },
    {
        "title": "Port Agents",
        "type": "v", "dur": 2, "prod": "general",
        "description": "A short video on the Port Agent persona.",
        "learn_items": ["What a Port Agent does day to day"],
        "video_url": "https://drive.google.com/file/d/16csZMO5eV8xtW5xK3rX-xITbi1da6Lwb/view?usp=drive_link",
    },
    {
        "title": "IT Managers",
        "type": "v", "dur": 3, "prod": "general",
        "description": "A short video on the IT Manager persona within a shipping customer organisation.",
        "learn_items": ["What an IT Manager does day to day in a shipping company"],
        "video_url": "https://drive.google.com/file/d/1jIJdRd3bT-LF3W0S2Yomb2VvZCipRGPS/view?usp=drive_link",
    },
    {
        "title": "Operation Managers",
        "type": "v", "dur": 2, "prod": "general",
        "description": "A short video on the Operation Manager persona.",
        "learn_items": ["What an Operation Manager does day to day"],
        "video_url": "https://drive.google.com/file/d/1Cb3ZRl1_jhFKVcfQuiNkNlA_Co8lqZDg/view?usp=drive_link",
    },
]

TIER5_QUIZ = [
    {
        "q": "What is the key difference between a Cargo Owner and a Vessel Owner?",
        "explanation": "Cargo Owners have an economic interest in the goods being transported; Vessel Owners have an economic interest in the transportation itself, selling capacity.",
        "options": [
            ("There is no real difference", False),
            ("Cargo Owners own the goods; Vessel Owners sell transport capacity", True),
            ("Vessel Owners always also own the cargo", False),
            ("Cargo Owners never interact with vessels directly", False),
        ],
    },
    {
        "q": "In a Voyage Charter, who typically pays the port costs, fuel, and crew costs?",
        "explanation": "In a Voyage Charter, the owner pays port costs (excluding stevedoring), fuel, and crew — the charterer pays per ton or lump sum for the voyage itself.",
        "options": [
            ("The charterer", False), ("The owner", True),
            ("The port agent", False), ("Split 50/50 by default", False),
        ],
    },
    {
        "q": "What happens if a charterer exceeds laytime under a Voyage Charter?",
        "explanation": "If laytime is exceeded, the charterer must pay demurrage; if laytime is saved, the owner may pay despatch.",
        "options": [
            ("Nothing — laytime is only a guideline", False),
            ("The charterer must pay demurrage", True),
            ("The owner automatically pays a penalty", False),
            ("The voyage is cancelled", False),
        ],
    },
    {
        "q": "What distinguishes a Bareboat Charter from a Time Charter?",
        "explanation": "In a Bareboat Charter, the charterer gets the ship, hull, and machinery and must supply their own crew or management company — unlike a Time Charter, where the owner provides a ready-to-go vessel with crew.",
        "options": [
            ("There is no real difference", False),
            ("Bareboat: charterer supplies their own crew/management; Time: owner supplies a ready-to-go vessel", True),
            ("Bareboat charters are always shorter than Time Charters", False),
            ("Time Charters never involve a crew", False),
        ],
    },
    {
        "q": "What does an Operator do once a ship has been fixed?",
        "explanation": "Operators manage the voyage from shore — vessel performance, bunker quality/quantity/pricing, and routing — keeping the ship earning throughout.",
        "options": [
            ("They negotiate the original charter deal", False),
            ("They manage the voyage from shore end to end", True),
            ("They only handle insurance claims", False),
            ("They own the cargo being shipped", False),
        ],
    },
    {
        "q": "What does TEU measure, and roughly how many can an 18,000+ TEU vessel carry?",
        "explanation": "TEU = twenty-foot-equivalent unit, a standard container capacity measure; an 18,000+ TEU vessel holds roughly 9,000 containers.",
        "options": [
            ("Vessel speed; about 18 knots", False),
            ("Container capacity; roughly 9,000 containers", True),
            ("Crew size; about 18,000 people", False),
            ("Fuel consumption; 18,000 tons per voyage", False),
        ],
    },
    {
        "q": "What's the difference between Domestic and International trade execution?",
        "explanation": "Domestic manages export/import across the water without operating the vessel (like a supply-chain function); International manages delivery to the customer by land.",
        "options": [
            ("Domestic covers land delivery; International covers the vessel", False),
            ("Domestic manages the water crossing; International manages land delivery to the customer", True),
            ("There is no meaningful difference", False),
            ("International only applies to container shipping", False),
        ],
    },
    {
        "q": "What happens during the Pre-Fixture stage?",
        "explanation": "The broker gathers cargo details, ports, rates, laycan, and commission info, and checks the charterer's reputation and recent shipment history before going to market.",
        "options": [
            ("The Charter Party is signed", False),
            ("The broker gathers key details and checks the charterer's background before going to market", True),
            ("The vessel begins loading", False),
            ("Freight invoices are settled", False),
        ],
    },
    {
        "q": "What confirms that a Fixture negotiation is fully complete?",
        "explanation": "The Charter Party is signed by both parties once all subjects are lifted and the fixture recap is confirmed.",
        "options": [
            ("A verbal agreement over the phone", False),
            ("The signed Charter Party, once all subjects are lifted", True),
            ("The vessel arriving at the load port", False),
            ("The broker sending an initial rate offer", False),
        ],
    },
    {
        "q": "During Post-Fixture loading, what determines whether demurrage occurred?",
        "explanation": "The Notice of Readiness (NOR) and Statement of Facts (SOF) are checked on completion of loading to determine if demurrage occurred.",
        "options": [
            ("The broker's personal judgement", False),
            ("Checking the Notice of Readiness (NOR) and Statement of Facts (SOF)", True),
            ("The charterer's mood at delivery", False),
            ("A random spot audit", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# ROLE ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────

ROLE_DATA = {
    "name": "Employee Onboarding",
    "description": (
        "The universal path for every new Sedna hire — company context, practical setup, policy essentials, "
        "performance expectations, and shipping-industry fundamentals."
    ),
    "icon": "ti-anchor", "color": "orange", "audience": "internal",
    "products": ["vms", "stream", "bridgelabs"], "sort_order": 0,
    "tiers": [
        {"label": "Welcome to Sedna", "name": "Welcome to Sedna", "cert_name": "Employee Onboarding — Welcome to Sedna", "modules": TIER1_MODULES, "quiz": TIER1_QUIZ},
        {"label": "Getting Started", "name": "Getting Started", "cert_name": "Employee Onboarding — Getting Started", "modules": TIER2_MODULES, "quiz": TIER2_QUIZ},
        {"label": "Policies & Compliance", "name": "Policies & Compliance", "cert_name": "Employee Onboarding — Policies & Compliance", "modules": TIER3_MODULES, "quiz": TIER3_QUIZ},
        {"label": "Growth & Performance", "name": "Growth & Performance", "cert_name": "Employee Onboarding — Growth & Performance", "modules": TIER4_MODULES, "quiz": TIER4_QUIZ},
        {"label": "Shipping & Industry Fundamentals", "name": "Shipping & Industry Fundamentals", "cert_name": "Employee Onboarding — Shipping & Industry Fundamentals", "modules": TIER5_MODULES, "quiz": TIER5_QUIZ},
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

    # NOTE: idempotency here is tier-level only, same as seed_vms_support.py.
    # If a future run needs to add new modules to a tier that already exists
    # (e.g. once Our Products / Where We Work content lands), this loop will
    # skip that tier entirely rather than appending to it — that'll need a
    # module-level existence check (by title) added at that point.
    added_tiers = 0
    for t_sort, td in enumerate(ROLE_DATA["tiers"]):
        if td["label"] in existing_labels:
            print(f"  Tier '{td['label']}' already exists — skipping.")
            continue
        tier = Tier(role_id=role.id, label=td["label"], name=td["name"], cert_name=td["cert_name"], sort_order=t_sort)
        db.add(tier)
        await db.flush()
        for m_sort, md in enumerate(td["modules"]):
            module = Module(
                tier_id=tier.id, title=md["title"], module_type=md["type"],
                duration_mins=md["dur"], product=md.get("prod", "general"),
                sort_order=m_sort, description=md.get("description", ""),
                learn_items=md.get("learn_items", []),
                rich_content=md.get("rich_content"),
                video_url=md.get("video_url"),
            )
            db.add(module)
            await db.flush()
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


if __name__ == "__main__":
    asyncio.run(main())
