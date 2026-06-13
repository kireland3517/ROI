# User Flow

Synthesized from PRD v0.8 and Intake Question Strategy V1. **Conflicts between these sources are flagged explicitly** — do not merge them silently.

---

## Conflict: PRD vs. Intake Strategy — RESOLVED (D-V13-001)

| Topic | PRD v0.8 | Intake Question Strategy V1 |
|---|---|---|
| Starter questions | Address + user type + goal + sale timeline + target list date + **required** total monthly mortgage payment; many property facts from ATTOM | **Four** required questions: address, seller objective, target timing, spend comfort range |
| Budget | Budget and risk tolerance are **inferred outputs**, not primary user inputs | **Spend comfort range** is a required starter question |
| Mortgage balance | Optional but recommended in main intake; used for equity/net proceeds | **Rejected** from starter flow; belongs only in optional Net Proceeds module |
| Condition assessment | **Required** guided room-by-room photo flow with per-room finding confirmation | Optional **Condition Boost** after starter report (photos or issue picker) |
| Report before deep asks | Not specified — full intake precedes recommendations | **Starter report preview** before optional modules |

**Resolution status:** **Resolved by D-V13-001 (June 2026)** — the Intake Question Strategy V1 progressive flow is adopted. Four required starter inputs (address, objective, timing, spend comfort), Smarty confirmation gate retained from PRD §2.1, optional issue picker (Condition Boost lite) in the starter flow, starter report before any deep asks. The PRD's deep intake survives as optional unlock modules (Budget Refinement, Net Proceeds, Timeline Compression); the guided photo flow is deferred to a later slice. Mortgage/payment data is collected only inside the optional Net Proceeds / carrying-cost module. See `decisions-log.md` D-V13-001.

---

## PRD v0.8 flow (authoritative product requirements)

### 1. Address validation gate

1. User enters property address
2. Smarty standardizes address
3. User **must confirm** standardized address before any ATTOM or downstream query
4. If Smarty fails: block with "Address could not be validated"

### 2. Property facts

- Pull from ATTOM where available (beds, baths, sqft, year built, lot, AVM, etc.)
- User confirms or corrects on conflict
- MVP property type: single-family residential only
- HOA: user-confirmed yes/no; if yes, work may require HOA approval note

### 3. User intent and financial inputs (PRD)

| Field | Required? |
|---|---|
| user_type (homeowner / agent / investor) | Required |
| goal (sell / flip / refinance) | Required |
| sale_timeline | Required |
| target_list_date | Required |
| total_monthly_mortgage_payment | **Required** |
| hoa_dues | Required if HOA = yes |
| mortgage_balance | Optional (report notes reduced reliability if omitted) |
| utilities, maintenance, supplemental_insurance | Optional |

### 4. Condition assessment — guided photo flow (PRD v0.8)

Human-in-the-loop, room-by-room wizard:

**Room sequence:** Exterior front → exterior rear → living areas → kitchen → primary bath → additional baths → basement/crawl → attic (skippable where N/A)

**Per room:**
1. Wizard assigns room label **before** upload (not inferred by vision)
2. User uploads 1–3 photos (mobile camera or desktop file picker; compress to &lt;1MB)
3. Vision model returns structured findings
4. User reviews each finding: **Confirm** (enters pipeline), **Dismiss** (stored, excluded), or **Add** (user-known issue)
5. Severity is **not** assigned at vision time — recommendation engine assigns during tier classification
6. Re-upload available on confirmation screen

**After review:** User confirms overall condition (Excellent / Good / Fair / Poor). Conflicts with photo findings trigger reconciliation prompt.

### 5. Recommendation generation and report

- Engine produces Seller ROI Action Plan
- User reviews prioritized output (see `report-structure.md`)

### 6. Cross-device continuity (PRD)

- Server-side session persistence via UUID token
- Start on mobile, complete on desktop without data loss

---

## Intake Question Strategy V1 flow (draft alternative)

### Starter plan (4 required questions)

1. Property address — "What property are you planning around?"
2. Seller objective — sell soon / highest net / refinance / evaluate flip
3. Target timing — ideal list/sell/complete date
4. Spend comfort range — bands including "I'm not sure yet"

**Product rule:** Do not ask sensitive or high-effort input until the product explains what report section it improves, why it is needed, whether it is optional, and what happens if skipped.

### Starter report preview

Show value before deeper asks.

### Optional unlock modules

| Module | Trigger | Additional input | Classification |
|---|---|---|---|
| Condition Boost | "Make this plan more specific" | Photos or quick issue picker | MVP |
| Budget Refinement | "Build a phased plan" | Max spend, DIY willingness, must-do vs nice-to-have | MVP |
| Net Proceeds Scenario | "Estimate cash at closing" | Mortgage payoff, liens | Phase 2 unless proceeds core to launch |
| Timeline Compression | "I need to list very soon" | Listing date flexibility | MVP |
| Agent / Listing Strategy | Agent/pricing context | Expected list price, pricing posture | Phase 2 |

### Graceful degradation when optional modules skipped

| Missing input | Behavior |
|---|---|
| No photos/issues | Lower condition confidence; label assumptions |
| No exact budget | Spend-band scenario groupings |
| No mortgage payoff | Omit net proceeds; explain repair priorities don't require it |
| Conflicting property facts | Reconciliation prompt |

---

## Error and partial-failure UX (PRD)

Material API failures must not fail silently. Examples:

| Failure | Treatment |
|---|---|
| ATTOM property detail | Fall back to user-entered values + warning |
| ATTOM comps | Limited-data handling + broader benchmarks |
| Vision model | Skip automated condition; manual checklist |
| Redfin supply | Prior validated file + show data age |

---

## Source references

- `docs/product/raw/Property_ROI_Analysis_Tool_PRD_v0_8.docx` — §§2–3, 13
- `docs/product/raw/Intake Question Strategy — Low-Friction Progressive Disclosure Specification V1.docx`
