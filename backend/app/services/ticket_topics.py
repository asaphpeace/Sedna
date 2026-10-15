"""Sort a support case into a topic from its title.

The same rules as the support insight pack (Oct 2026), so the dashboard's
topics match the pack. Jira's root-cause field is almost never filled in, so
the title is the best signal there is. First match wins; order matters.
"""
import re

_RULES: list[tuple[str, str]] = [
    ("Laytime and demurrage", r"laytime|demurrage|despatch|\bsof\b|statement of fact"),
    ("Bunkers", r"bunker|fuel|scrubber|consumption|\brob\b|lsmgo|vlsfo"),
    ("Emissions and EU ETS", r"\bets\b|\beua|emission|co2|fueleu|\bcii\b|\bmrv"),
    ("Hire, TC and statements of account", r"hire|\bsoa\b|statement of account|off.?hire|\btc\b|time charter|owners|redeliver"),
    ("Invoicing, costs and accounting", r"invoice|invoic|credit note|kreditfaktura|posting|post |accrual|ledger|\bgl\b|accounting|payment|freight|commission|balance|various cost|port cost|\bcosts?\b|pending|receivable|payable|counterpart statement|pay to"),
    ("Reports, BI and printouts", r"report|jasper|\bbi\b|printout|print|dashboard|widget|export|excel"),
    ("Cargo, COA and documents", r"cargo|\bcoa\b|contract of aff|nomination|parcel|bills? of lading|\bb/?l\b|claims?|stowage|tolerance|cancelled cp|charter party"),
    ("Estimates and voyage P&L", r"estimate|calculation|\btce\b|p&l|result"),
    ("Master data: ports, currencies, time zones", r"unlocode|locode|new port|missing port|port name|master data|offices|timezone|time zone|pilot station|exchange rate|currenc|\bmap\b|missing terminal"),
    ("Voyages and port calls", r"voyage|port call|itinerary|eta|start date|vessel|position|distance|route|berth|terminal|speed|ballast|delivery time|discharg|loading|port log|\bdays\b"),
    ("Users, sign-in and access", r"user|login|log in|access|password|permission|role|sso|single sign|account|licen|authenticator|whitelist|\bip\b"),
    ("Upgrades, environments and performance", r"upgrade|environment|test env|release|version|install|server|slow|performance|down|outage|error 5|timeout"),
    ("Integrations and data import", r"integration|api|m2m|interface|import|upload|sync|edi|webhook"),
    ("Sedna Email", r"email|stream|inbox|mail|tag"),
    ("Vague: system or error, no detail", r"dataloy problem|not working|urgent|error message|http error|\b50[0-9]\b|quick help|issue with all|failure message|repeated error"),
]
_COMPILED = [(name, re.compile(pattern)) for name, pattern in _RULES]


def topic_for(title: str) -> str:
    text = (title or "").lower()
    for name, pattern in _COMPILED:
        if pattern.search(text):
            return name
    return "Other"
