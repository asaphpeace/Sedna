"""Seed the Sedna Email and Sedna Email Support learning paths.

Purely additive, same pattern as seed_vms_support.py and seed_onboarding.py:
checks whether each role already exists and, if so, only adds tiers that
don't already exist under it by label. Safe to re-run.

Source: the Sedna Email Product Hierarchy sheet (Pillar/Product/Category/
Feature/What is it/Value Proposition), pasted in full — no external docs
were fetched for this one. The "Adjacent Platform Context" tier planned for
Sedna Email Support (4 videos: Sedna Build, two Pre-fixture sessions, TC
hire in/out) is deliberately left out of this file until their share links
are confirmed — appending it later is just adding a new tier, which the
tier-aware seed() below already handles safely.

Run once via:
    docker compose -f docker-compose.prod.yml exec backend python -m app.seed_sedna_email
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine, Base
from app.models import *  # noqa: F401,F403 — registers all models with Base


# ─────────────────────────────────────────────────────────────────────────
# ROLE 1 — SEDNA EMAIL (general)
# ─────────────────────────────────────────────────────────────────────────

# Tier 1: Email Fundamentals
TIER_EMAIL_1_MODULES = [
    {
        "title": "Core Email",
        "type": "a", "dur": 10, "prod": "stream",
        "description": "Team and Solo Inboxes, Instant Search, Offline access, mobile apps, and Calendar.",
        "learn_items": [
            "The difference between a Team Inbox and a Solo Inbox",
            "What Instant Search actually indexes",
            "How Offline access and sync work",
            "What Calendar syncs with, and what it enables",
        ],
        "rich_content": (
            "Sedna Email starts from two inbox shapes. A Team Inbox is a shared email address that gives "
            "multiple users simultaneous access to incoming and outgoing mail, without the mess of forwarding, "
            "CC chains, or duplicated copies sitting in everyone's personal mailbox. A Solo Inbox is the "
            "individual counterpart — a personal address for a single user — but it carries the same "
            "structured, searchable experience as a team inbox rather than feeling like a stripped-down "
            "version.\n\n"
            "Instant Search runs full-text search across every message, attachment, and piece of metadata, "
            "returning results in real time — so finding a specific email doesn't depend on remembering exactly "
            "who sent it or when.\n\n"
            "Offline access means you can still open your inbox and recent messages without an active internet "
            "connection, with anything you do syncing automatically once connectivity returns — useful on a "
            "flight, at sea, or anywhere connectivity is unreliable. The iOS and Android mobile apps carry the "
            "full Sedna Email experience onto phones and tablets, so triage, tagging, and team collaboration "
            "aren't limited to a desktop.\n\n"
            "Calendar is a separate app, synced with Microsoft Outlook today (Google is coming), that lets a "
            "user RSVP directly from a scan card inside Sedna Email — one more example of the platform pulling "
            "related context into the inbox rather than sending you elsewhere to act on it.\n\n"
            "Team Inboxes in particular solve a problem every operational team eventually runs into: what "
            "happens when someone is out of office. A traditional auto-reply just tells a counterpart to wait — "
            "in an industry where, as one Sedna customer put it, thirty seconds can be the difference in a "
            "deal, that's a real cost, not a minor inconvenience. Because a Team Inbox gives colleagues genuine "
            "shared visibility rather than a personal mailbox nobody else can see into, 69% of Sedna customers "
            "report worrying less about taking holiday, since colleagues can pick up the work seamlessly "
            "instead of everything stalling until one person is back online."
        ),
    },
    {
        "title": "Contacts & Messages",
        "type": "a", "dur": 14, "prod": "stream",
        "description": "The Contacts 2.0 directory, distribution lists, and the collaboration tools that live on every message.",
        "learn_items": [
            "What Contacts 2.0 actually connects, beyond a name and email address",
            "How Advanced Distribution Lists differ from a plain mailing list",
            "The five ways multiple people can work on the same message",
            "What a Message Scan Card surfaces, and where the data comes from",
        ],
        "rich_content": (
            "Contacts 2.0 is a centralised directory of people and companies within Sedna, with enriched "
            "profiles that connect a contact to the messages and jobs they're actually involved in — not just a "
            "name and email address sitting in isolation. That same directory is fully available on the iOS and "
            "Android apps, so it travels with you rather than staying desktop-only. On top of the directory, "
            "Advanced Distribution Lists & Mail Merge let a user save a group of recipients for bulk sending, "
            "with personalised field substitution per recipient — so a single send can still feel individually "
            "addressed.\n\n"
            "A message itself is built to be worked on by more than one person. Message Collaboration lets "
            "multiple users act on the same message at once — assignment, internal notes, shared visibility of "
            "what's already been done — so nobody duplicates work or replies twice by accident. Message "
            "Commenting adds internal notes to a thread that are visible to teammates but never sent externally, "
            "and Message Deduplication automatically detects and suppresses duplicate incoming copies so the "
            "same email doesn't clutter a team inbox multiple times.\n\n"
            "Two features surface context directly alongside a message. The Message Context Panel is a side "
            "panel that pulls in related information — linked voyages, counterparty history, tags, and activity "
            "— without leaving the inbox. Message Scan Cards go further, extracting structured data from a "
            "message's content (vessel, cargo, port, dates) and displaying it alongside live data pulled from "
            "integrated systems, so the key facts of an email are visible before you've even opened the full "
            "thread. Underneath all of this, the Message Activity & Audit Log keeps a full record of every "
            "action taken on a message — who read it, replied, tagged, assigned, or commented, and when."
        ),
    },
    {
        "title": "Tagging System",
        "type": "a", "dur": 14, "prod": "stream",
        "description": "How messages get organised at Sedna — job references, categories, people, and the AI that can do it automatically.",
        "learn_items": [
            "The four tag types: Job Reference, Category, Private, and People",
            "What Augur actually automates",
            "Where tag configuration itself gets managed",
        ],
        "rich_content": (
            "Tags are how Sedna Email turns a flood of incoming mail into something organised and retrievable. "
            "Job Reference Tags link a message to a specific job, voyage, or fixture, so it can be pulled up "
            "later by that reference from anywhere in the platform. Category Tags are user-defined labels for "
            "type, topic, or status, enabling filtering and consistent workflows across a team. Private Tags sit "
            "underneath both — visible only to the individual who applied them, for personal organisation "
            "without affecting what a shared inbox looks like to everyone else. People Tags (Assignment) route a "
            "message to a specific person or team, creating real accountability rather than leaving ownership "
            "ambiguous.\n\n"
            "Behind these four tag types sit the tools that manage them. The Vessel/Voyage Job Tag Manager is a "
            "centralised place to create, edit, and manage job reference tags across the whole organisation, "
            "while the Attribute Manager configures the custom attributes attached to tags, so each job can "
            "carry richer, more specific data than a label alone. Unified Tag Management brings all of this — "
            "job references, categories, people, and attributes — into a single interface rather than several "
            "disconnected screens.\n\n"
            "The most automated piece is Augur, an AI model that automatically suggests and applies the correct "
            "job reference tag to an incoming message based on its content and context — meaning a well-tuned "
            "inbox increasingly tags itself, rather than depending on someone remembering to do it manually on "
            "every single email.\n\n"
            "The numbers behind this in practice are large. Monson Agencies, a bulk shipping agency handling "
            "1.8 million emails a month, cut that volume by 90% — down to roughly 180,000 — after moving "
            "vessel scheduling onto AI-powered tagging by vessel, voyage, customer, and priority. Viterra's "
            "chartering operators, who were manually filing over 1,300 emails a day before automated tagging, "
            "saw manual filing effort drop by 99% and total email volume by 95%, freeing operators to actually "
            "focus on chartering decisions instead of inbox admin. Tagging isn't a nice-to-have layered on top "
            "of email at that scale — it's what makes an inbox usable at all."
        ),
    },
]

TIER_EMAIL_1_QUIZ = [
    {
        "q": "What's the key difference between a Team Inbox and a Solo Inbox?",
        "explanation": "A Team Inbox is a shared address giving multiple users simultaneous access; a Solo Inbox is a personal address, but with the same structured, searchable experience.",
        "options": [
            ("Solo Inboxes have fewer features", False),
            ("Team Inboxes are shared and used simultaneously by multiple users; Solo Inboxes are personal", True),
            ("There's no real difference", False),
            ("Team Inboxes require forwarding rules to work", False),
        ],
    },
    {
        "q": "What does Instant Search cover?",
        "explanation": "Full-text search across all messages, attachments, and metadata, with real-time results.",
        "options": [
            ("Only email subject lines", False),
            ("Full-text search across messages, attachments, and metadata", True),
            ("Only messages from the last 30 days", False),
            ("Only messages you personally sent", False),
        ],
    },
    {
        "q": "What does Contacts 2.0 add beyond a basic name-and-email entry?",
        "explanation": "Enriched profiles that connect a contact to the relevant messages and jobs they're involved in.",
        "options": [
            ("Nothing — it's the same as a standard address book", False),
            ("Enriched profiles connecting contacts to relevant messages and jobs", True),
            ("Only phone numbers, not email data", False),
            ("It only works on mobile, not desktop", False),
        ],
    },
    {
        "q": "What does Message Deduplication do?",
        "explanation": "Automatically detects and suppresses duplicate incoming messages so the same email doesn't appear multiple times in team inboxes.",
        "options": [
            ("Deletes old messages automatically", False),
            ("Detects and suppresses duplicate incoming messages", True),
            ("Merges multiple threads into one", False),
            ("Removes attachments to save space", False),
        ],
    },
    {
        "q": "What is a Message Scan Card?",
        "explanation": "A structured data card extracted from message content, showing key fields (vessel, cargo, port, dates) alongside live data from integrated systems.",
        "options": [
            ("A printable summary of a message", False),
            ("Structured data extracted from a message, shown with live data from integrated systems", True),
            ("A spam-detection flag", False),
            ("A calendar invite generated from an email", False),
        ],
    },
    {
        "q": "What does Augur automate?",
        "explanation": "Augur is an AI model that automatically suggests and applies the correct job reference tag to incoming messages based on content and context.",
        "options": [
            ("Automatically replying to customer emails", False),
            ("Automatically suggesting and applying job reference tags", True),
            ("Automatically deleting spam messages", False),
            ("Automatically translating messages", False),
        ],
    },
]

# Tier 2: AI & Productivity
TIER_EMAIL_2_MODULES = [
    {
        "title": "AI Assist Features",
        "type": "a", "dur": 14, "prod": "stream",
        "description": "The seven AI Assist capabilities built directly into the inbox — from entity extraction to conversational search.",
        "learn_items": [
            "What AI Entity Extraction identifies inside a message",
            "The four AI Assist writing/reading tools: drafting, summarisation, translation",
            "The two conversational AI Assist modes: search and context vs. conversation",
        ],
        "rich_content": (
            "AI runs through Sedna Email as a set of distinct, purpose-built tools rather than one generic "
            "assistant bolted on top. AI Entity Extraction & Comprehension is the foundation — automatic "
            "identification and structuring of key entities within an email's content, such as vessel names, "
            "ports, dates, and cargo quantities, turning free-text prose into data the rest of the platform can "
            "actually use.\n\n"
            "On top of that foundation sit several AI Assist tools aimed at reading and writing mail faster. "
            "Reply Drafting generates a draft response based on the content and context of an incoming message, "
            "ready for review and editing before it's sent — the AI proposes, the user still decides. "
            "Summarisation produces a concise summary of a whole thread, capturing key points and actions "
            "without requiring the full thread to be read start to finish. Translation works in both "
            "directions, translating incoming or outgoing message content between languages directly inside the "
            "inbox, without a separate tool.\n\n"
            "A further set of AI Assist modes are conversational rather than transformational. Search lets a "
            "user find messages, jobs, and contacts using natural language instead of exact keyword matching. "
            "Context surfaces relevant information — linked voyages, counterparties, documents — for whatever "
            "message or job is currently in view. And Conversation goes furthest: a full conversational "
            "interface for interacting with Sedna data and taking actions through natural language, without "
            "navigating away from the current screen at all.\n\n"
            "None of this is positioned as replacing human judgement — it's positioned as removing the grunt "
            "work around it. Sedna's own research points to teams recovering up to four hours a day simply by "
            "routing emails to the right person or team automatically, through the same intelligent "
            "prioritisation and contextual tagging described above. That framing matters across the wider "
            "platform too, not just Email in isolation: Sedna Email handles inbox organisation and message "
            "prioritisation, Sedna Pre-Fixture consolidates scattered market information into unified views, "
            "and Sedna VMS manages execution — three connected tools addressing the same underlying pressure "
            "shipping has always had: too much unstructured communication and not enough structured time to "
            "act on it."
        ),
    },
    {
        "title": "Composer & Workflows",
        "type": "a", "dur": 12, "prod": "stream",
        "description": "Writing emails faster, and the automation layer that acts on them without manual intervention.",
        "learn_items": [
            "What Composer Improvements covers",
            "The difference between Agentic Tagging and Rule-Based Workflows",
            "What ToDo adds on top of a regular task list",
        ],
        "rich_content": (
            "Composer Improvements is an ongoing thread of enhancements to the actual writing experience — "
            "formatting, template access, and generally making it easier to get an email sent without fighting "
            "the editor. Template UX Improvements builds on that specifically for reusable content, reducing "
            "friction in high-volume or repetitive communication where the same message shape gets sent again "
            "and again.\n\n"
            "Beyond writing, three layers of automation act on mail without someone clicking through each step "
            "manually. Rule-Based Workflows trigger automated actions off configurable conditions — sender, "
            "subject, tag, or content — applied consistently across all incoming mail. API-Based Workflows open "
            "the same idea up to external systems, letting custom logic and integrations trigger actions inside "
            "the inbox via the Sedna API. And Agentic Tagging, Categorisation & Workflows goes a step further "
            "still — AI-driven automation that applies tags, categories, and workflow actions based on learned "
            "patterns rather than a fixed rule someone had to write out in advance.\n\n"
            "ToDo sits alongside all of this as a task list linked directly to messages and jobs, letting users "
            "create, assign, and track action items without leaving the inbox to manage them somewhere else — "
            "the task and the email that generated it stay connected."
        ),
    },
]

TIER_EMAIL_2_QUIZ = [
    {
        "q": "What does AI Entity Extraction & Comprehension do?",
        "explanation": "It automatically identifies and structures key entities in email content — vessel names, ports, dates, cargo quantities.",
        "options": [
            ("Blocks spam messages automatically", False),
            ("Identifies and structures key entities like vessel names, ports, and dates", True),
            ("Translates messages into other languages", False),
            ("Deletes messages after a retention period", False),
        ],
    },
    {
        "q": "With AI Assist Reply Drafting, who has the final say before a reply is sent?",
        "explanation": "The AI generates a draft, but it's ready for review and editing before sending — the user still decides.",
        "options": [
            ("The AI sends replies automatically", False),
            ("The user reviews and edits the draft before sending", True),
            ("The customer approves it first", False),
            ("A manager must approve every AI-drafted reply", False),
        ],
    },
    {
        "q": "What's the difference between AI Assist 'Search' and AI Assist 'Conversation'?",
        "explanation": "Search finds messages/jobs/contacts via natural language; Conversation is a full conversational interface for interacting with data and taking actions without leaving the current view.",
        "options": [
            ("They're the same feature with two names", False),
            ("Search finds things via natural language; Conversation lets you interact and take actions conversationally", True),
            ("Conversation only works on mobile", False),
            ("Search requires exact keyword matches; Conversation doesn't exist yet", False),
        ],
    },
    {
        "q": "What triggers a Rule-Based Workflow?",
        "explanation": "Configurable conditions such as sender, subject, tag, or content, applied consistently across incoming mail.",
        "options": [
            ("Manual review by an administrator every time", False),
            ("Configurable conditions like sender, subject, tag, or content", True),
            ("A monthly scheduled batch job only", False),
            ("Only messages marked as spam", False),
        ],
    },
    {
        "q": "How does Agentic Tagging differ from a Rule-Based Workflow?",
        "explanation": "Agentic Tagging is AI-driven, applying tags/categories/actions based on learned patterns; Rule-Based Workflows follow fixed conditions someone configured in advance.",
        "options": [
            ("There's no difference between them", False),
            ("Agentic Tagging uses AI-learned patterns; Rule-Based Workflows follow fixed configured conditions", True),
            ("Rule-Based Workflows are newer than Agentic Tagging", False),
            ("Agentic Tagging only works for outbound mail", False),
        ],
    },
]

# Tier 3: Shipping-Specific Features
TIER_EMAIL_3_MODULES = [
    {
        "title": "Shipping Workflows",
        "type": "a", "dur": 16, "prod": "stream",
        "description": "Where Sedna Email plugs directly into voyage, claims, and operational data.",
        "learn_items": [
            "The two ways messages file directly against operational records",
            "What Sedna Email automatically extracts from operational documents",
            "How RFQ Quote Management works inside the inbox",
        ],
        "rich_content": (
            "This is where Sedna Email stops being a general inbox and starts acting like part of the shipping "
            "operation itself. Vessel & Voyage Filing lets a message be filed directly to a vessel or voyage "
            "record, keeping all relevant correspondence organised and accessible from the job rather than "
            "buried in someone's personal mailbox. Claims Filing works the same way for claims — messages and "
            "documents attach to a specific claims record, maintaining a complete, structured correspondence "
            "trail for each one. Vessel Certificates Management goes further still, capturing and tracking "
            "certificate documents and their expiry dates, surfaced directly within the relevant email threads "
            "rather than in a separate system someone has to remember to check.\n\n"
            "A cluster of features focus on extracting structured data automatically from operational documents "
            "that arrive by email. Itinerary Identification & Update to VMS detects itinerary data in incoming "
            "messages and can push updates straight to the connected VMS. Noon Report Capture & Analysis pulls "
            "noon report data out of incoming email and structures it into a consistent format for review. SOF "
            "Extraction & Analysis does the same for Statement of Facts data, structured specifically for "
            "demurrage and operational review, and Customs Extraction & Processing extracts customs "
            "documentation data for downstream processing.\n\n"
            "Finally, RFQ Quote Management is a full workflow for requests for quotation — capturing, tracking, "
            "and comparing incoming quotes from suppliers or counterparties without leaving the inbox to manage "
            "the comparison in a separate spreadsheet.\n\n"
            "Customs Extraction & Processing in particular has a concrete customer story behind it. Casper "
            "Customs, a six-person post-Brexit customs clearance operation processing around 6,000 declarations "
            "a month, used automated customs data extraction to cut declaration processing time by over 80% — "
            "from around 45 minutes down to under 10 — giving a six-person team the effective capacity of 20 or "
            "more manual specialists. And on the vessel/voyage side, NORDEN connected Sedna Email to their "
            "existing Veson IMOS system via API, linking emails directly to voyage records and cutting internal "
            "email volume by 50% — a good example of Shipping Workflows features paying off specifically "
            "because they connect to a system already in place, not because they replace it."
        ),
    },
    {
        "title": "Document Management",
        "type": "a", "dur": 8, "prod": "stream",
        "description": "Filing attachments to the right place, connecting to SharePoint, and getting a thread out as a PDF.",
        "learn_items": [
            "What Document Filing connects to",
            "What the SharePoint Integration actually does",
        ],
        "rich_content": (
            "Document Filing lets a user save email attachments and documents directly to a linked job, voyage, "
            "or record within Sedna or a connected system, rather than downloading a file locally and hoping it "
            "ends up in the right folder. The SharePoint Integration extends this using Microsoft's Graph API, "
            "allowing documents to be filed to, retrieved from, or linked directly to SharePoint libraries "
            "without leaving the inbox — genuinely useful for organisations whose document-of-record already "
            "lives in SharePoint rather than inside Sedna itself.\n\n"
            "PDF Export & Print rounds this out with the simpler, more everyday need: exporting an email thread "
            "or message to a PDF file for download, printing, or archiving, whenever a plain digital record "
            "isn't enough and something needs to exist as a standalone document.\n\n"
            "Casper Shipping, the UK's leading independent port agency, is a good illustration of what Document "
            "Filing looks like at scale: before Sedna, staff were copy-pasting data out of PDFs into customs "
            "paperwork by hand and printing emails as standard practice. Automated extraction and filing "
            "recovered 37.5 hours a week for the team — and, in their own words, the system learned their "
            "processes within a single week of going live."
        ),
    },
]

TIER_EMAIL_3_QUIZ = [
    {
        "q": "What does Vessel & Voyage Filing do?",
        "explanation": "It lets a message be filed directly to a vessel or voyage record, keeping correspondence organised and accessible from the job.",
        "options": [
            ("Automatically deletes old vessel-related emails", False),
            ("Files a message directly to a vessel or voyage record", True),
            ("Creates a new voyage record from an email", False),
            ("Sends a copy of the message to the vessel's crew", False),
        ],
    },
    {
        "q": "What does SOF Extraction & Analysis extract, and what is it used for?",
        "explanation": "It extracts Statement of Facts data from incoming messages, structured for demurrage and operational review.",
        "options": [
            ("Crew certification data, for HR review", False),
            ("Statement of Facts data, for demurrage and operational review", True),
            ("Customs paperwork, for import clearance", False),
            ("Bunker prices, for cost forecasting", False),
        ],
    },
    {
        "q": "What does RFQ Quote Management help with?",
        "explanation": "Capturing, tracking, and comparing incoming quotes from suppliers or counterparties within the inbox.",
        "options": [
            ("Generating invoices automatically", False),
            ("Capturing, tracking, and comparing incoming supplier/counterparty quotes", True),
            ("Filing crew certificates", False),
            ("Translating quotes into other currencies", False),
        ],
    },
    {
        "q": "What API does the SharePoint Integration use?",
        "explanation": "Microsoft's Graph API, allowing documents to be filed to, retrieved from, or linked to SharePoint libraries from the inbox.",
        "options": [
            ("Google Drive API", False), ("Microsoft Graph API", True),
            ("A custom Sedna-built API only", False), ("Dropbox API", False),
        ],
    },
    {
        "q": "What does Itinerary Identification & Update to VMS do?",
        "explanation": "Detects itinerary data in incoming messages and can push updates directly to the connected VMS.",
        "options": [
            ("Prints a copy of the itinerary", False),
            ("Detects itinerary data in messages and pushes updates to the connected VMS", True),
            ("Creates a new vessel record", False),
            ("Sends a reminder email about upcoming port calls", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# ROLE 2 — SEDNA EMAIL SUPPORT
# ─────────────────────────────────────────────────────────────────────────

# Tier 1: Security, Privacy & Access
TIER_SUPPORT_1_MODULES = [
    {
        "title": "Privacy & Compliance",
        "type": "a", "dur": 12, "prod": "stream",
        "description": "Legal export, PII protection, retention, and blocking unwanted senders.",
        "learn_items": [
            "What Legal Export and Legal Hold each do, and how they differ",
            "What Usage Analytics reports on, and who can see it",
            "How Message Retention Management and Spam/Phishing blocking work",
        ],
        "rich_content": (
            "Legal Export lets an admin export a defined set of messages, threads, or accounts in a structured "
            "format suitable for legal discovery or regulatory submission — the mechanism for actually producing "
            "records when they're formally requested. Legal Hold is the preventive counterpart: it places a hold "
            "on specific messages, accounts, or data sets, preventing deletion or modification for the duration "
            "of a legal or compliance process, so nothing relevant can disappear while a matter is still open.\n\n"
            "Advanced Data Privacy & Protection (PII) gives controls for identifying, managing, and restricting "
            "personally identifiable information within Sedna, in line with data protection requirements — "
            "important groundwork given how much of an inbox's content is, by nature, personal. Message "
            "Retention Management defines how long messages are retained before being archived or deleted, "
            "matching organisational or regulatory policy rather than keeping everything indefinitely by "
            "default.\n\n"
            "Usage Analytics gives administrators reporting on how the platform is actually being used — inbox "
            "activity, response times, user engagement — useful for spotting where a team might be "
            "overwhelmed or underusing a feature. And Spam/Phishing: Block Email lets an administrator block "
            "specific senders or domains outright, stopping their messages from reaching user inboxes at all.\n\n"
            "The reason these controls matter isn't abstract: shipping email is genuinely full of personal "
            "data by nature — crew documents, payroll details, visa confirmations — and industry-wide, over "
            "80% of enterprise data is unstructured, meaning that information sits buried in attachments and "
            "PDFs that are nearly impossible to track by hand. Retention limits and legal holds exist "
            "specifically because the failure mode here is rarely malicious; it's ordinary human error — "
            "forwarding the wrong document, missing a redaction, keeping a crew list longer than necessary — "
            "at a scale where GDPR and equivalent regimes elsewhere (LGPD, PDPA, CCPA) make that error "
            "expensive rather than just embarrassing."
        ),
    },
    {
        "title": "Personal Data Redaction",
        "type": "a", "dur": 12, "prod": "stream",
        "description": "How Sedna automatically detects and redacts personal data in shipping email — the technical architecture behind it.",
        "learn_items": [
            "The three-layer detection approach: ML/NER, pattern matching, severity scoring",
            "Why the feature is self-hosted rather than sent to an external processor",
            "The real-world scenario that shows why this matters: a Rotterdam port agent's crew list",
        ],
        "rich_content": (
            "Operational inboxes in shipping routinely receive genuinely sensitive documents — passport scans, "
            "medical certificates, crew lists, immigration paperwork — flowing across forwarded threads, shared "
            "inboxes, and between port agents, crewing managers, and charterers, usually with no systematic "
            "control over where any of it ends up. Personal Data Redaction exists specifically to close that "
            "gap without adding friction to how people already work.\n\n"
            "Detection runs on three layers. Machine learning, specifically Named Entity Recognition, "
            "understands context well enough to distinguish an actual person's name in a crew list from a "
            "company name or vessel reference — a distinction that matters a lot given how much shipping "
            "terminology looks name-like out of context. Pattern matching handles the more structured cases — "
            "passport numbers, IBANs — using rule-based logic built for high precision. And a severity scoring "
            "layer assigns each finding a risk level (critical, high, low), so a team can configure exactly "
            "which thresholds should trigger automatic redaction rather than treating every match identically.\n\n"
            "The platform scans over 400 file formats, including OCR processing for scanned documents — so a "
            "photographed passport page is just as coverable as a native PDF. Crucially, Personal Data "
            "Redaction is self-hosted within the Sedna environment: no external processor ever touches the "
            "data, which matters a great deal for a feature whose entire purpose is data protection. Redaction "
            "and deletion also operate independently of each other, with configurable visibility windows, so "
            "the feature protects data without disrupting the operational workflow built around that inbox.\n\n"
            "A real scenario makes the risk concrete: a Rotterdam port agent forwards a crew list that "
            "unknowingly includes scanned medical certificates with health details and ID numbers. That single "
            "document then circulates through six inboxes across company boundaries — triggering GDPR "
            "exposure, required crew notifications, and real operational disruption, all from one ordinary, "
            "well-intentioned forward. With GDPR fines reaching up to €20 million or 4% of global revenue, and "
            "over €5 billion in cumulative penalties since 2018 across the industry more broadly, this isn't a "
            "theoretical risk — and deployment for the feature itself typically takes under two weeks, with "
            "minimal ongoing administration once it's live."
        ),
    },
    {
        "title": "Enterprise Security",
        "type": "a", "dur": 12, "prod": "stream",
        "description": "How Sedna Email defends against phishing and impersonation, and the routing options built for scale.",
        "learn_items": [
            "What Verified by Sedna actually verifies",
            "Why an organisation might need an Alternative Mail In/Out route",
            "What disabling attachment links changes for outbound mail",
        ],
        "rich_content": (
            "Message Phishing Identification automatically detects and flags incoming messages that show "
            "characteristics of a phishing attempt, surfacing a warning to the recipient rather than leaving "
            "them to spot it unaided. Verified by Sedna (Secure Email) is a Sedna-native authentication layer "
            "that verifies a sender's identity, reducing the risk of impersonation and spoofing — a structural "
            "defence rather than just a warning label.\n\n"
            "Disable Attachments as Links is a setting that stops outbound attachments from being converted into "
            "shareable links, keeping file sharing inside controlled channels rather than letting it leak out "
            "through link-based sharing services. On the delivery side, Graph Mail API (MS O365) for Mail "
            "In/Out routes mail through Microsoft's Graph API, giving reliable and compliant delivery for "
            "organisations already running Office 365. For very high message volumes, Alternative Mail In/Out "
            "provides a secondary routing option with extra capacity and resilience beyond a standard setup, and "
            "an Alternative SMTP Gateway offers a second SMTP configuration for cases where a specific security, "
            "compliance, or deliverability requirement calls for routing through a different gateway entirely.\n\n"
            "Western Bulk, operating around 150 dry bulk vessels, is a direct example of Verified by Sedna in "
            "practice — alongside automatic tagging and fast search, it gave their chartering managers better "
            "visibility into which communications could actually be trusted, contributing to a 70–80% "
            "reduction in email volume and 2–4 hours recovered per person daily, with fewer phishing attempts "
            "slipping through unnoticed."
        ),
    },
    {
        "title": "Single Sign-On",
        "type": "a", "dur": 8, "prod": "stream",
        "description": "The five identity providers Sedna Email supports for enterprise login.",
        "learn_items": [
            "The five supported SSO providers",
            "What SAML support means for identity providers not explicitly listed",
        ],
        "rich_content": (
            "Sedna Email supports single sign-on through five paths. Microsoft Entra SSO (formerly Azure AD) "
            "and Google SSO let users log in with their existing Microsoft or Google Workspace credentials "
            "respectively — the two most common cases. Okta SSO and Ping SSO extend the same idea to "
            "organisations managing identity through those platforms instead.\n\n"
            "Underneath all of them sits SAML for Enterprise SSO — support for SAML 2.0-based single sign-on, "
            "which is what actually makes integration possible with any compatible enterprise identity provider, "
            "not just the four named above. If a customer's identity provider isn't Entra, Google, Okta, or "
            "Ping specifically, SAML compatibility is the thing worth checking before assuming SSO isn't "
            "possible at all."
        ),
    },
    {
        "title": "Permissions & Administration",
        "type": "a", "dur": 6, "prod": "stream",
        "description": "Letting customers manage themselves, and giving view-only access where full access isn't appropriate.",
        "learn_items": [
            "What Self-Service & Customer Autonomy actually lets an org do without Sedna support",
            "What Read-Only at Team Level restricts",
        ],
        "rich_content": (
            "Self-Service & Customer Autonomy covers the admin tools that let an organisation manage its own "
            "users, inboxes, tags, and settings without needing to go through Sedna support for routine changes "
            "— the more of this an org can do itself, the less friction there is for everyday administrative "
            "requests.\n\n"
            "Read-Only at Team Level is a narrower, specific control: the ability to grant a user view-only "
            "access to a team inbox, so they can see what's there without being able to send, tag, or take any "
            "action on messages — useful for oversight or auditing roles that need visibility but shouldn't be "
            "acting on a team's behalf."
        ),
    },
]

TIER_SUPPORT_1_QUIZ = [
    {
        "q": "What's the difference between Legal Export and Legal Hold?",
        "explanation": "Legal Export produces records in a structured format for discovery/regulatory submission; Legal Hold prevents deletion or modification of data during an open legal/compliance process.",
        "options": [
            ("They're the same feature under two names", False),
            ("Legal Export produces records for submission; Legal Hold prevents deletion during a legal process", True),
            ("Legal Hold is only for customer-facing exports", False),
            ("Legal Export is automatic; Legal Hold requires a court order", False),
        ],
    },
    {
        "q": "Who can see Usage Analytics reporting?",
        "explanation": "It's available to administrators, covering inbox activity, response times, and user engagement.",
        "options": [
            ("Every user, by default", False), ("Administrators", True),
            ("Only external auditors", False), ("Nobody — it's for internal Sedna use only", False),
        ],
    },
    {
        "q": "What does Verified by Sedna (Secure Email) protect against?",
        "explanation": "It's a Sedna-native authentication layer that verifies sender identity, reducing impersonation and spoofing risk.",
        "options": [
            ("Slow email delivery", False), ("Impersonation and spoofing", True),
            ("Storage overuse", False), ("Duplicate messages", False),
        ],
    },
    {
        "q": "What does Disable Attachments as Links change?",
        "explanation": "It prevents outbound attachments from being converted into shareable links, keeping file sharing within controlled channels.",
        "options": [
            ("It blocks all attachments outright", False),
            ("It stops outbound attachments from becoming shareable links", True),
            ("It compresses attachments automatically", False),
            ("It only affects inbound attachments", False),
        ],
    },
    {
        "q": "Which SSO feature enables compatibility with identity providers beyond the four named ones (Entra, Google, Okta, Ping)?",
        "explanation": "SAML for Enterprise SSO — SAML 2.0 support is what enables integration with any compatible enterprise identity provider.",
        "options": [
            ("A custom API integration only", False), ("SAML for Enterprise SSO", True),
            ("Read-Only at Team Level", False), ("Alternative SMTP Gateway", False),
        ],
    },
    {
        "q": "What does Read-Only at Team Level allow a user to do?",
        "explanation": "View a team inbox without being able to send, tag, or take action on messages.",
        "options": [
            ("Send messages but not tag them", False),
            ("View a team inbox without sending, tagging, or acting on messages", True),
            ("Only read messages older than 30 days", False),
            ("Access billing information only", False),
        ],
    },
    {
        "q": "What are the three detection layers behind Personal Data Redaction?",
        "explanation": "Machine learning (Named Entity Recognition), pattern matching, and severity scoring.",
        "options": [
            ("Keyword blocklist, manual review, and encryption", False),
            ("Machine learning (NER), pattern matching, and severity scoring", True),
            ("OCR, spam filtering, and virus scanning", False),
            ("Firewalls, VPN, and two-factor authentication", False),
        ],
    },
    {
        "q": "Why does it matter that Personal Data Redaction is self-hosted within the Sedna environment?",
        "explanation": "No external processor ever touches the data — critical for a feature whose whole purpose is data protection.",
        "options": [
            ("It makes the feature faster to deploy", False),
            ("No external processor touches the data being protected", True),
            ("It's required for the feature to scan PDFs", False),
            ("It reduces Sedna's own hosting costs", False),
        ],
    },
]

# Tier 2: Infrastructure & Data
TIER_SUPPORT_2_MODULES = [
    {
        "title": "Infrastructure & Deployment",
        "type": "a", "dur": 10, "prod": "stream",
        "description": "Shared vs. private clusters, region selection, and dedicated compute for enterprise scale.",
        "learn_items": [
            "The difference between Shared and Private Cluster deployment",
            "What Region Selection is used for",
            "What Dedicated Compute Resources guarantees",
        ],
        "rich_content": (
            "Sedna Email can run on a Shared Cluster on AWS, where resources are allocated across multiple "
            "tenants on common cloud infrastructure, or on a Private Cluster on AWS, a dedicated environment "
            "isolated from other tenants for organisations that need enhanced security and performance "
            "guarantees a shared environment can't offer.\n\n"
            "Region Selection lets a customer choose the geographic region — US East, EU West, or AP Southeast "
            "— where their data is stored and processed, which matters directly for meeting data residency "
            "requirements that some organisations and jurisdictions impose. Dedicated Compute Resources reserves "
            "processing capacity exclusively for a single tenant, so performance stays consistent regardless of "
            "how busy the wider platform gets elsewhere. Enterprise Scaling & Security is the broader "
            "infrastructure configuration built for genuinely high-volume, enterprise-grade deployments, "
            "including enhanced scaling limits and security controls beyond the standard setup."
        ),
    },
    {
        "title": "Historical Import & Storage",
        "type": "a", "dur": 8, "prod": "stream",
        "description": "The three historical mail import options, and the three storage tiers behind them.",
        "learn_items": [
            "The three historical mail import options and their time ranges",
            "The three storage tiers and roughly how many emails each holds",
        ],
        "rich_content": (
            "When an organisation onboards onto Sedna Email, existing mail history doesn't have to stay behind "
            "in the old system. One Year Historical Mail Import migrates up to 12 months of email data from an "
            "existing mail system. Five Years Historical Mail Import extends that to five years of history, and "
            "Unlimited Historical Mail Import migrates the complete historical archive with no date restriction "
            "at all — the right choice depends entirely on how much of an organisation's institutional memory "
            "needs to actually be searchable inside Sedna from day one.\n\n"
            "Storage scales alongside that import volume in three tiers: 10TB, supporting roughly 40 million "
            "emails; 30TB, supporting roughly 120 million; and 100TB, supporting roughly 400 million. These "
            "numbers are naturally a rough guide rather than an exact ceiling, since actual email size varies, "
            "but they give a useful sense of scale when sizing a deployment against an organisation's mail "
            "volume.\n\n"
            "Norvic Shipping's migration is a useful reference point for what a historical import actually "
            "looks like end to end: moving off costly on-premise servers onto Sedna's cloud infrastructure "
            "while preserving 2 million historical emails, with operators previously receiving up to 2,000 "
            "emails a day. The result was teams working roughly 20% faster overall and around 8 hours a week "
            "recovered per operator — while keeping full access to years of prior correspondence rather than "
            "starting from a blank inbox on day one."
        ),
    },
    {
        "title": "Support Tiers",
        "type": "a", "dur": 6, "prod": "stream",
        "description": "The three support packages available, from round-the-clock coverage to WhatsApp.",
        "learn_items": [
            "What's included at each of the three support tiers",
        ],
        "rich_content": (
            "Support itself comes in three tiers, each building on the one below it. 24/7/365 Support gives "
            "round-the-clock access to the Sedna support team through standard channels, every day of the year "
            "— the baseline every customer can rely on. 24/7/365 Support + In-App Chat adds a live chat widget "
            "accessible directly from within the Sedna platform, so a customer doesn't need to leave the product "
            "to reach someone. The top tier, 24/7/365 Support + In-App Chat + WhatsApp, adds the option to reach "
            "the support team over WhatsApp on top of everything else — useful for customers who live in "
            "WhatsApp for day-to-day communication already and want support to meet them there rather than "
            "requiring a channel switch."
        ),
    },
]

TIER_SUPPORT_2_QUIZ = [
    {
        "q": "What's the key difference between a Shared Cluster and a Private Cluster on AWS?",
        "explanation": "Shared Cluster allocates resources across multiple tenants; Private Cluster is a dedicated, isolated environment for a single tenant.",
        "options": [
            ("Private Cluster is cheaper", False),
            ("Shared Cluster serves multiple tenants; Private Cluster is dedicated to one", True),
            ("Shared Cluster is only available in the US", False),
            ("There's no real difference", False),
        ],
    },
    {
        "q": "Why would a customer care about Region Selection?",
        "explanation": "It lets them choose where their data is stored and processed, to meet data residency requirements.",
        "options": [
            ("It changes the product's pricing tier", False),
            ("It meets data residency requirements by choosing where data is stored/processed", True),
            ("It determines which language the UI displays in", False),
            ("It's only relevant for support ticket routing", False),
        ],
    },
    {
        "q": "Roughly how many emails does the 30TB storage tier support?",
        "explanation": "Approximately 120 million emails.",
        "options": [
            ("About 40 million", False), ("About 120 million", True),
            ("About 400 million", False), ("Unlimited", False),
        ],
    },
    {
        "q": "What's the maximum historical mail import range Sedna Email offers?",
        "explanation": "Unlimited Historical Mail Import — the complete archive, with no date restriction.",
        "options": [
            ("One year", False), ("Five years", False),
            ("Unlimited, no date restriction", True), ("Ten years", False),
        ],
    },
    {
        "q": "What does the top support tier add on top of 24/7/365 Support + In-App Chat?",
        "explanation": "The option to reach the support team via WhatsApp.",
        "options": [
            ("A dedicated account manager", False), ("WhatsApp support", True),
            ("Faster response SLAs only", False), ("Phone support", False),
        ],
    },
]


# Tier 4: Real-World Impact
TIER_EMAIL_4_MODULES = [
    {
        "title": "Customer Stories: Sedna Email in Action",
        "type": "a", "dur": 16, "prod": "stream",
        "description": "Ten real customers, ten different problems, one recurring shape: email overload turned back into structured, fast, collaborative work.",
        "learn_items": [
            "The four customers who cut total email volume by 50% or more",
            "The four customers measured on hours recovered per person",
            "How Sedna Email connects outward to the rest of the platform",
        ],
        "rich_content": (
            "Every customer story behind Sedna Email starts from roughly the same place: an operation drowning "
            "in volume, using a system built for personal correspondence rather than high-stakes team "
            "coordination. What differs is the shape of the fix, and the size of the number that comes out the "
            "other end.\n\n"
            "Four customers measured the impact directly in email volume. Monson Agencies, a bulk shipping "
            "agent handling 1.8 million emails a month, cut that down by 90% — to roughly 180,000 — after "
            "moving vessel scheduling onto a shared inbox with AI-powered tagging. Viterra's chartering "
            "operators, previously filing over 1,300 emails a day by hand, saw volume drop 95% and manual "
            "filing effort drop 99%. NORDEN cut internal emails across operations and finance by 50% after "
            "connecting Sedna to their existing Veson IMOS system. And Western Bulk, running roughly 150 dry "
            "bulk vessels, saw a 70–80% reduction for their chartering managers specifically, alongside better "
            "phishing visibility through Verified by Sedna.\n\n"
            "Four more customers measured the impact in hours recovered per person, which tells a slightly "
            "different story — not just less noise, but real time given back. Ardmore Shipping's chartering "
            "team had been spending up to three hours every morning just deleting emails before they could "
            "start real work; automated tagging and search gave back two hours a day per team member. Nova "
            "Marine, managing over 100 vessels and 12,000 emails a day, recovered more than an hour per person "
            "daily through faster search and API-enriched context. Western Bulk's operators separately gained "
            "2–4 hours a day. And Norvic Shipping, migrating off costly on-premise servers while keeping 2 "
            "million historical emails intact, saw operators work roughly 20% faster and recover about 8 hours "
            "a week each.\n\n"
            "Two further stories show what happens when Email connects into a specific operational workflow "
            "rather than just organising the inbox itself. Casper Customs, a six-person post-Brexit customs "
            "clearance operation, used automated customs data extraction to cut declaration processing time by "
            "over 80%, giving a six-person team the effective throughput of twenty or more manual specialists. "
            "Casper Shipping automated document extraction from attachments entirely, recovering 37.5 hours a "
            "week previously spent copy-pasting data out of PDFs by hand. And Bunge, a 24,000-employee "
            "agribusiness operating in 40+ countries, used inbox prioritisation and tagging/commenting to "
            "replace forwarding chains with a single shared source of truth — in their own words, no longer "
            "needing to \"sift through every single email\" to find what mattered.\n\n"
            "Sedna Email doesn't operate in isolation from the rest of the platform, either. Sedna Pre-Fixture "
            "(formerly Pulse) builds map-first context directly into commercial workflows — Mini Maps let a "
            "chartering team click any vessel in a Tonnage List to see live AIS position data without leaving "
            "the screen, and Custom Regions let a team define geofences around the specific basins or routes "
            "they actually work (West Africa, US Gulf to Europe, and so on) rather than scrolling a global map. "
            "It's a different product, but the same underlying idea as everything above: bring the context to "
            "where the decision is actually being made, instead of making someone go find it."
        ),
    },
]

TIER_EMAIL_4_QUIZ = [
    {
        "q": "Which customer cut chartering-operator email volume by 95%, with manual filing dropping 99%?",
        "explanation": "Viterra — chartering operators previously filed over 1,300 emails a day by hand before automated tagging.",
        "options": [
            ("Monson Agencies", False), ("Viterra", True),
            ("NORDEN", False), ("Bunge", False),
        ],
    },
    {
        "q": "What specifically did NORDEN connect Sedna Email to, in order to cut internal email by 50%?",
        "explanation": "Their existing Veson IMOS system, via API, linking emails directly to voyage records.",
        "options": [
            ("A customs clearance system", False), ("Their existing Veson IMOS system via API", True),
            ("A new CRM platform", False), ("A weather routing service", False),
        ],
    },
    {
        "q": "Ardmore's chartering team used to spend up to how long each morning just deleting emails?",
        "explanation": "Up to three hours a day, before automated tagging and search gave back roughly two hours a day per person.",
        "options": [
            ("30 minutes", False), ("One hour", False),
            ("Up to three hours", True), ("A full working day", False),
        ],
    },
    {
        "q": "What made Casper Customs able to process 6,000 declarations a month with only six staff?",
        "explanation": "Automated customs data extraction cut processing time by over 80%, giving the team the effective throughput of 20+ manual specialists.",
        "options": [
            ("Outsourcing to a larger firm", False),
            ("Automated customs data extraction cutting processing time by 80%+", True),
            ("Hiring 20 additional specialists", False),
            ("Reducing their client base", False),
        ],
    },
    {
        "q": "What did Norvic Shipping preserve while migrating off on-premise servers onto Sedna's cloud infrastructure?",
        "explanation": "2 million historical emails, while gaining roughly 20% faster operation and 8 hours/week recovered per operator.",
        "options": [
            ("Nothing — historical email was discarded", False),
            ("2 million historical emails", True),
            ("Only the last 12 months of email", False),
            ("Only emails tagged as high-priority", False),
        ],
    },
    {
        "q": "What does Sedna Pre-Fixture's 'Custom Regions' feature let a chartering team do?",
        "explanation": "Define geofences around the specific basins or routes they actually work, rather than viewing the entire world map.",
        "options": [
            ("Restrict which vessels appear on a global map to specific basins/routes they define", True),
            ("Automatically fix vessels to a route", False),
            ("Block emails from outside a specific region", False),
            ("Convert currencies by region", False),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────
# ROLE ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────

ROLE_DATA_EMAIL = {
    "name": "Sedna Email",
    "description": (
        "General product literacy for the Sedna Email Stream team — what each feature area is and why it "
        "matters, drawn directly from the Product Hierarchy."
    ),
    "icon": "ti-mail", "color": "blue", "audience": "internal",
    "products": ["stream"], "sort_order": 50,
    "tiers": [
        {"label": "Email Fundamentals", "name": "Email Fundamentals", "cert_name": "Sedna Email — Fundamentals", "modules": TIER_EMAIL_1_MODULES, "quiz": TIER_EMAIL_1_QUIZ},
        {"label": "AI & Productivity", "name": "AI & Productivity", "cert_name": "Sedna Email — AI & Productivity", "modules": TIER_EMAIL_2_MODULES, "quiz": TIER_EMAIL_2_QUIZ},
        {"label": "Shipping-Specific Features", "name": "Shipping-Specific Features", "cert_name": "Sedna Email — Shipping Features", "modules": TIER_EMAIL_3_MODULES, "quiz": TIER_EMAIL_3_QUIZ},
        {"label": "Real-World Impact", "name": "Real-World Impact", "cert_name": "Sedna Email — Real-World Impact", "modules": TIER_EMAIL_4_MODULES, "quiz": TIER_EMAIL_4_QUIZ},
    ],
}

ROLE_DATA_EMAIL_SUPPORT = {
    "name": "Sedna Email Support",
    "description": (
        "Deeper, admin-facing Sedna Email knowledge — security, compliance, SSO, and infrastructure — for "
        "people supporting Sedna Email customers."
    ),
    "icon": "ti-headset", "color": "teal", "audience": "internal",
    "products": ["stream"], "sort_order": 150,
    "tiers": [
        {"label": "Security, Privacy & Access", "name": "Security, Privacy & Access", "cert_name": "Sedna Email Support — Security & Access", "modules": TIER_SUPPORT_1_MODULES, "quiz": TIER_SUPPORT_1_QUIZ},
        {"label": "Infrastructure & Data", "name": "Infrastructure & Data", "cert_name": "Sedna Email Support — Infrastructure & Data", "modules": TIER_SUPPORT_2_MODULES, "quiz": TIER_SUPPORT_2_QUIZ},
        # "Adjacent Platform Context" (4 videos) intentionally omitted until share links are confirmed.
    ],
}

ALL_ROLES = [ROLE_DATA_EMAIL, ROLE_DATA_EMAIL_SUPPORT]


async def seed_role(db: AsyncSession, role_data: dict):
    result = await db.execute(select(LearningRole).where(LearningRole.name == role_data["name"]))
    role = result.scalar_one_or_none()
    if role is None:
        role = LearningRole(
            name=role_data["name"], description=role_data["description"], icon=role_data["icon"],
            color=role_data["color"], audience=role_data["audience"], products=role_data["products"],
            sort_order=role_data["sort_order"],
        )
        db.add(role)
        await db.flush()
        print(f"Created role: {role.name}")
    else:
        print(f"Role '{role.name}' already exists — adding any missing tiers under it.")

    existing_tiers = await db.execute(select(Tier).where(Tier.role_id == role.id))
    existing_labels = {t.label for t in existing_tiers.scalars().all()}

    added_tiers = 0
    for t_sort, td in enumerate(role_data["tiers"]):
        if td["label"] in existing_labels:
            print(f"  Tier '{td['label']}' already exists — skipping.")
            continue
        tier = Tier(role_id=role.id, label=td["label"], name=td["name"], cert_name=td["cert_name"], sort_order=t_sort)
        db.add(tier)
        await db.flush()
        for m_sort, md in enumerate(td["modules"]):
            module = Module(
                tier_id=tier.id, title=md["title"], module_type=md["type"],
                duration_mins=md["dur"], product=md.get("prod", "stream"),
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
    print(f"✓ {role_data['name']}: {added_tiers} new tier(s) added this run.")


async def seed(db: AsyncSession):
    for role_data in ALL_ROLES:
        await seed_role(db, role_data)


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
