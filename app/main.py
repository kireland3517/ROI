"""FastAPI routes: progressive intake -> building -> starter Seller Action Plan."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import engine, flow, market_context, sessions
from app.adapters import attom_property
from app.adapters.smarty import (
    AddressValidationError,
    MissingCredentialsError,
    get_adapter,
)
from app.seeds import load_issue_picker, load_issue_picker_groups

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Property ROI Analysis Tool")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _friendly_date(iso_value: str) -> str:
    try:
        from datetime import date

        value = date.fromisoformat(str(iso_value))
    except (TypeError, ValueError):
        return str(iso_value)
    return f"{value.strftime('%b')} {value.day}, {value.year}"


templates.env.filters["friendly_date"] = _friendly_date


def _session_or_home(session_id: str):
    session = sessions.get_session(session_id)
    if session is None:
        return None, RedirectResponse("/", status_code=303)
    return session, None


def _building_context(session: dict) -> dict:
    """Plain-language summary for the building screen — display only."""
    from app.seeds import issue_labels

    address = session.get("address") or {}
    answers = session.get("answers") or {}
    labels = issue_labels()
    issues = session.get("issues") or []
    custom = (session.get("custom_issue") or "").strip()
    market = market_context.build_market_context(
        address.get("state", ""), address.get("zip", "")
    )

    return {
        "address_display": address.get("display", ""),
        "address_verified": address.get("provider") == "smarty",
        "objective_label": flow.answer_label("objective", answers.get("objective", "")),
        "timing_label": flow.answer_label("timing", answers.get("timing_band", "")),
        "spend_label": flow.answer_label("spend", answers.get("spend_band", "")),
        "target_date": (answers.get("target_date") or "").strip() or None,
        "issue_count": len(issues),
        "issue_preview": [labels[k] for k in issues[:2]],
        "has_custom_issue": bool(custom),
        "issues_skipped": bool(session.get("issues_submitted")) and not issues and not custom,
        "market_available": bool(market.get("available")),
    }


# ---------------------------------------------------------------- intake


@app.get("/", response_class=HTMLResponse)
def address_entry(request: Request):
    return templates.TemplateResponse(
        request, "intake/address.html", {"error": None, "address_value": ""}
    )


@app.get("/api/address-suggestions")
def address_suggestions(q: str = ""):
    """Server-side typeahead proxy: Smarty credentials never reach the browser.

    Best-effort by design — any failure returns an empty list. Strict
    validation still happens at submit time, so suggestions are never a
    substitute for the gate.
    """
    query = q.strip()
    if len(query) < 4:
        return JSONResponse({"suggestions": []})
    try:
        adapter = get_adapter()
    except MissingCredentialsError:
        # A typeahead miss must not 500; the submit path still fails clearly.
        return JSONResponse({"suggestions": []})
    return JSONResponse(
        {"suggestions": [{"display": s.display} for s in adapter.suggest(query)]}
    )


@app.post("/intake/address")
def submit_address(request: Request, address: str = Form("")):
    adapter = get_adapter()
    try:
        standardized = adapter.validate(address)
    except AddressValidationError as exc:
        return templates.TemplateResponse(
            request,
            "intake/address.html",
            {"error": exc.user_message, "address_value": address},
            status_code=200,
        )

    session_id = sessions.create_session()
    session = sessions.get_session(session_id)
    session["address"] = {
        "line1": standardized.line1,
        "line2": standardized.line2,
        "display": standardized.display,
        "city": standardized.city,
        "state": standardized.state,
        "zip": standardized.zip_code,
        "provider": standardized.provider,
        "raw": address,
    }
    return RedirectResponse(f"/intake/{session_id}/confirm", status_code=303)


@app.get("/intake/{session_id}/confirm", response_class=HTMLResponse)
def confirm_address(request: Request, session_id: str):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request,
        "intake/confirm.html",
        {"session_id": session_id, "address": session["address"]},
    )


@app.post("/intake/{session_id}/confirm")
def address_confirmed(session_id: str):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect
    return RedirectResponse(f"/intake/{session_id}/q/objective", status_code=303)


@app.get("/intake/{session_id}/q/{step}", response_class=HTMLResponse)
def question(request: Request, session_id: str, step: str):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect
    config = flow.QUESTIONS.get(step)
    if config is None:
        return RedirectResponse(f"/intake/{session_id}/q/objective", status_code=303)
    return templates.TemplateResponse(
        request,
        "intake/question.html",
        {
            "session_id": session_id,
            "step_key": step,
            "q": config,
            "total_steps": len(flow.QUESTION_ORDER),
            "current_value": session["answers"].get(config["field"], ""),
            "current_date": session["answers"].get("target_date", ""),
        },
    )


@app.post("/intake/{session_id}/q/{step}")
def answer_question(
    session_id: str,
    step: str,
    value: str = Form(""),
    target_date: str = Form(""),
):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect
    config = flow.QUESTIONS.get(step)
    if config is None:
        return RedirectResponse(f"/intake/{session_id}/q/objective", status_code=303)

    valid_values = {opt["value"] for opt in config["options"]}
    if config.get("skippable"):
        valid_values.add(config["skip_value"])
    if value not in valid_values:
        return RedirectResponse(f"/intake/{session_id}/q/{step}", status_code=303)

    session["answers"][config["field"]] = value
    if step == "timing":
        session["answers"]["target_date"] = target_date.strip()
    sessions.reset_plan(session_id)

    following = flow.next_step(step)
    if following:
        return RedirectResponse(f"/intake/{session_id}/q/{following}", status_code=303)
    return RedirectResponse(f"/intake/{session_id}/issues", status_code=303)


@app.get("/intake/{session_id}/issues", response_class=HTMLResponse)
def issue_picker(request: Request, session_id: str):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request,
        "intake/issues.html",
        {
            "session_id": session_id,
            "issue_groups": load_issue_picker_groups(),
            "selected": set(session["issues"]),
            "custom_issue": session.get("custom_issue", ""),
        },
    )


@app.post("/intake/{session_id}/issues")
async def submit_issues(request: Request, session_id: str):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect
    form = await request.form()
    if form.get("skip") != "1":
        valid_keys = {opt.issue_key for opt in load_issue_picker()}
        session["issues"] = [k for k in form.getlist("issues") if k in valid_keys]
        session["custom_issue"] = (form.get("custom_issue") or "").strip()
    else:
        session["issues"] = []
        session["custom_issue"] = ""
    session["issues_submitted"] = True
    sessions.reset_plan(session_id)
    return RedirectResponse(f"/building/{session_id}", status_code=303)


# ---------------------------------------------------------------- plan


@app.get("/building/{session_id}", response_class=HTMLResponse)
def building(request: Request, session_id: str):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request, "intake/building.html", {
            "session_id": session_id,
            "building": _building_context(session),
        }
    )


def _debug_plan_facts(event: str, **fields) -> None:
    if os.getenv("DEBUG_PROPERTY_FACTS", "").strip().lower() not in {
        "1", "true", "yes", "on",
    }:
        return
    logger.info("property_facts.%s %s", event, fields)


def _generate_plan(session: dict) -> None:
    address = session["address"] or {}
    facts = None
    facts_partial = False
    if session.get("facts") and session["facts"].get("source") == "user_confirmed":
        facts = session["facts"]
        facts_fallback = bool(facts.get("fallback_origin", False))
        _debug_plan_facts(
            "use_user_confirmed",
            facts=facts,
            skipped_attom=True,
        )
    else:
        fetched = attom_property.fetch_property_facts(
            address.get("line1", ""), address.get("line2", "")
        )
        if fetched is not None:
            facts = {
                "beds": fetched.beds,
                "baths": fetched.baths,
                "sqft": fetched.sqft,
                "year_built": fetched.year_built,
                "lot_acres": fetched.lot_acres,
                "source": fetched.source,
                "pulled_at": fetched.pulled_at,
            }
            facts_fallback = False
            facts_partial = attom_property.facts_are_partial(fetched)
        else:
            facts = session.get("facts") or {"source": "user"}
            facts_fallback = True
        session["facts"] = dict(
            facts,
            fallback_origin=facts_fallback,
            partial_origin=facts_partial,
        )
        _debug_plan_facts(
            "session_facts",
            address_line1=address.get("line1"),
            address_line2=address.get("line2"),
            facts=facts,
            facts_fallback=facts_fallback,
            facts_partial=facts_partial,
        )

    answers = dict(session["answers"])
    answers["issues"] = session["issues"]
    answers["custom_issue"] = session.get("custom_issue", "")
    session["plan"] = engine.build_plan(
        answers, facts, facts_fallback, facts_partial=facts_partial
    )
    # Presentation-layer context only — computed after the plan and never
    # fed into the engine. Out-of-market subjects get "unavailable".
    session["market_context"] = market_context.build_market_context(
        address.get("state", ""), address.get("zip", "")
    )


@app.post("/plan/{session_id}/generate")
def generate_plan(session_id: str):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return JSONResponse({"ok": False}, status_code=404)
    _generate_plan(session)
    return JSONResponse({"ok": True})


@app.get("/plan/{session_id}", response_class=HTMLResponse)
def view_plan(request: Request, session_id: str):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect
    if not session["answers"].get("objective"):
        return RedirectResponse(f"/intake/{session_id}/q/objective", status_code=303)
    if session["plan"] is None:
        _generate_plan(session)  # no-JS fallback
    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "session_id": session_id,
            "address": session["address"],
            "plan": session["plan"],
            "facts": session.get("facts") or {},
            "market_context": session.get("market_context")
            or market_context.unavailable("not_computed"),
        },
    )


@app.post("/plan/{session_id}/facts")
def correct_facts(
    session_id: str,
    beds: str = Form(""),
    baths: str = Form(""),
    sqft: str = Form(""),
    year_built: str = Form(""),
):
    session, redirect = _session_or_home(session_id)
    if redirect:
        return redirect

    def parse(value: str, cast):
        try:
            number = cast(value)
            return number if number > 0 else None
        except (TypeError, ValueError):
            return None

    previous = session.get("facts") or {}
    session["facts"] = {
        "beds": parse(beds, int),
        "baths": parse(baths, float),
        "sqft": parse(sqft, int),
        "year_built": parse(year_built, int),
        "lot_acres": previous.get("lot_acres"),
        "source": "user_confirmed",
        "pulled_at": previous.get("pulled_at", ""),
        "fallback_origin": bool(previous.get("fallback_origin", False)),
        "partial_origin": False,
    }
    _generate_plan(session)
    return RedirectResponse(f"/plan/{session_id}", status_code=303)
