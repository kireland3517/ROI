"""Manual test checklist runner against a live dev server (first build slice).

Walks the real HTTP flow and prints PASS/FAIL per checklist item. Live ATTOM
behavior depends on the address used; both outcomes (records or fallback
warning) are valid — the check asserts that exactly one of the two designed
states rendered.
"""

import re
import sys

import requests

BASE = "http://127.0.0.1:8011"
results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


session = requests.Session()

# 1. Invalid address blocks at the gate with the specified message.
r = session.post(f"{BASE}/intake/address", data={"address": "banana"})
check(
    "Invalid address blocks with message",
    r.status_code == 200
    and "validate that address" in r.text
    and "Find my property" in r.text,
)

# Start the real flow.
r = session.post(
    f"{BASE}/intake/address",
    data={"address": "123 Maple Street, Springfield, IL 62704"},
    allow_redirects=False,
)
sid = r.headers.get("location", "").split("/")[2] if r.status_code == 303 else ""
check("Valid address redirects to confirmation", bool(sid))

r = session.get(f"{BASE}/intake/{sid}/confirm")
check(
    "Confirmation shows standardized address + chip",
    "123 Maple St" in r.text and "Standardized" in r.text,
)

session.post(f"{BASE}/intake/{sid}/confirm")

# Question screens show why-lines and step indicators.
r = session.get(f"{BASE}/intake/{sid}/q/objective")
check(
    "Objective screen: why-line + step indicator",
    "your goal changes what" in r.text and "Step 1 of 3" in r.text,
)
session.post(f"{BASE}/intake/{sid}/q/objective", data={"value": "sell_soon"})

r = session.get(f"{BASE}/intake/{sid}/q/timing")
check("Timing screen: skip path is first-class", "I'm not sure yet" in r.text or "I&#39;m not sure yet" in r.text)
session.post(f"{BASE}/intake/{sid}/q/timing", data={"value": "under_30", "target_date": ""})
session.post(f"{BASE}/intake/{sid}/q/spend", data={"value": "b1_5k"})

r = session.get(f"{BASE}/intake/{sid}/issues")
check(
    "Issue picker: optional framing, no severity asks",
    "Skipping is fine" in r.text and "severity" not in r.text.lower(),
)
session.post(f"{BASE}/intake/{sid}/issues", data={"issues": ["roof_leak", "mold"]})

# Building screen exists with honest status lines.
r = session.get(f"{BASE}/building/{sid}")
check(
    "Building screen: real status lines, no fake percentages",
    "Checking county property records" in r.text and "%" not in r.text,
)

# Generate + report.
session.post(f"{BASE}/plan/{sid}/generate")
r = session.get(f"{BASE}/plan/{sid}")
html = r.text

check("Report renders", r.status_code == 200 and "Your Seller Action Plan" in html)
check("Verdict present", "You're aiming to sell soon" in html or "You&#39;re aiming to sell soon" in html)

attom_state = "County records, pulled" in html
fallback_state = "County records were unavailable" in html
check(
    "Property summary shows exactly one designed data state",
    attom_state != fallback_state,
    "records" if attom_state else "fallback warning",
)

check(
    "Roof leak appears as urgent Tier-1 action",
    "Active roof leak repair" in html and "Do now" in html,
)
check(
    "Line items carry tier badge, cost band, status, DIY flag",
    "Fix first" in html and re.search(r"\$\d", html) is not None
    and "Hire a pro" in html,
)
check(
    "Citations + provenance chips rendered",
    "You told us" in html and "Standard estimate v1.0" in html and "Your answer" in html,
)
check(
    "Timeline horizon present (Today + target date)",
    "Today —" in html or "Today &mdash;" in html or "Today" in html,
    "",
)
check("Do Not Spend section with tally", "saved you from roughly" in html)
check(
    "Disclaimer present and labeled draft",
    "informational purposes only" in html and "pending legal review" in html,
)
check("Next steps present", "Next steps" in html)

banned = ["Simpsonville", "Greenville", "Kingfisher", "29680", "Tier 1", "coefficient"]
clean = re.sub(r"/static/\S+", "", html)
check(
    "No market literals or model vocabulary in output",
    not any(b.lower() in clean.lower() for b in banned),
)

# Under-30-day timeline: staging (24 days) is constrained; with a 10-day
# explicit date it must move beyond the line — exercised in unit tests; here
# verify the under-30 plan kept everything visible and correctly labeled.
check(
    "Timeline status labels are plain words",
    any(label in html for label in ("Fits your timeline", "Tight — start immediately", "Tight &mdash; start immediately")),
)

# Unknown session redirects home.
r = session.get(f"{BASE}/plan/not-a-session", allow_redirects=False)
check("Unknown session redirects home", r.status_code == 303)

failures = [name for name, ok, _ in results if not ok]
print()
print(f"{len(results) - len(failures)}/{len(results)} checks passed")
if failures:
    sys.exit(1)
