#!/usr/bin/env python3
"""Create Microsoft Forms from a survey-spec JSON via the Forms web API.

Auth uses MSAL public-client interactive / device-code against
https://forms.office.com/.default (same audience the Forms UI uses).
There is no official Graph Forms-create API.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

FORMS_SCOPE = ["https://forms.office.com/.default"]
FORMS_API_ROOT = "https://forms.office.com/formapi/api"
# Microsoft Office public client — works for interactive delegated Forms access
# in most work/school tenants without a custom app registration.
DEFAULT_CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"
AUTHORITY_COMMON = "https://login.microsoftonline.com/organizations"

TOKEN_CACHE_DIR = Path.home() / ".cache" / "vixxo-ms-forms"
TOKEN_CACHE_PATH = TOKEN_CACHE_DIR / "msal_token_cache.json"


def _die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def _require_deps() -> tuple[Any, Any]:
    try:
        import msal  # type: ignore
        import requests  # type: ignore
    except ImportError:
        _die(
            "Missing deps. Install with: py -3 -m pip install msal requests"
        )
    return msal, requests


def _load_cache(msal: Any) -> Any:
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
    return cache


def _save_cache(cache: Any) -> None:
    if cache.has_state_changed:
        TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE_PATH.write_text(cache.serialize(), encoding="utf-8")


def _claims_from_jwt(token: str) -> dict[str, Any] | None:
    """Best-effort JWT payload decode (Forms access tokens are often opaque)."""
    import base64

    parts = token.split(".")
    if len(parts) < 2:
        return None
    try:
        payload = parts[1]
        padding = "=" * (-len(payload) % 4)
        raw = base64.urlsafe_b64decode(payload + padding)
        return json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _claims_from_auth(
    result: dict[str, Any], accounts: list[dict[str, Any]]
) -> dict[str, str]:
    """Resolve tenant/user ids from MSAL id_token claims, account, or JWT."""
    data: dict[str, Any] = {}
    id_claims = result.get("id_token_claims") or {}
    if isinstance(id_claims, dict):
        data.update(id_claims)

    if accounts:
        acct = accounts[0]
        data.setdefault("preferred_username", acct.get("username") or "")
        home = acct.get("home_account_id") or ""
        # home_account_id is typically "{oid}.{tid}"
        if "." in home:
            oid, tid = home.split(".", 1)
            data.setdefault("oid", oid)
            data.setdefault("tid", tid)

    if not data.get("tid") or not data.get("oid"):
        jwt_claims = _claims_from_jwt(result.get("access_token") or "")
        if jwt_claims:
            data.update(jwt_claims)

    tid = data.get("tid") or data.get("tenantId")
    oid = data.get("oid") or data.get("sub")
    if not tid or not oid:
        _die(
            "Could not resolve tenant/user ids from sign-in. "
            "Try auth again, or pass identity via a fresh device-code login."
        )
    return {
        "tenant_id": str(tid),
        "user_id": str(oid),
        "name": str(data.get("name") or ""),
        "upn": str(
            data.get("preferred_username") or data.get("upn") or ""
        ),
    }


def acquire_token(interactive: bool = True) -> tuple[str, dict[str, str]]:
    msal, _ = _require_deps()
    cache = _load_cache(msal)
    app = msal.PublicClientApplication(
        DEFAULT_CLIENT_ID,
        authority=AUTHORITY_COMMON,
        token_cache=cache,
    )
    result: dict[str, Any] | None = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(FORMS_SCOPE, account=accounts[0])

    if not result:
        if interactive:
            # Prefer browser; fall back to device code if interactive fails.
            try:
                result = app.acquire_token_interactive(scopes=FORMS_SCOPE)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"Interactive auth failed ({exc}); trying device code…",
                    file=sys.stderr,
                )
                flow = app.initiate_device_flow(scopes=FORMS_SCOPE)
                if "user_code" not in flow:
                    _die(f"Device flow failed: {json.dumps(flow, indent=2)}")
                print(flow["message"], flush=True)
                result = app.acquire_token_by_device_flow(flow)
        else:
            flow = app.initiate_device_flow(scopes=FORMS_SCOPE)
            if "user_code" not in flow:
                _die(f"Device flow failed: {json.dumps(flow, indent=2)}")
            print(flow["message"], flush=True)
            result = app.acquire_token_by_device_flow(flow)

    _save_cache(cache)

    if not result or "access_token" not in result:
        err = (result or {}).get("error_description") or (result or {}).get(
            "error"
        ) or "unknown"
        _die(f"Auth failed: {err}")

    # Refresh account list after interactive/device login.
    accounts = app.get_accounts() or accounts
    claims = _claims_from_auth(result, accounts)
    return result["access_token"], claims


class FormsClient:
    def __init__(self, token: str, tenant_id: str, user_id: str) -> None:
        _, requests = _require_deps()
        self._requests = requests
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        self.base = f"{FORMS_API_ROOT}/{tenant_id}/users/{user_id}"

    def _request(
        self, method: str, url: str, *, json_body: Any | None = None
    ) -> Any:
        resp = self.session.request(method, url, json=json_body, timeout=60)
        if resp.status_code >= 400:
            _die(
                f"{method} {url} -> {resp.status_code}\n{resp.text[:2000]}"
            )
        if not resp.content:
            return None
        ctype = resp.headers.get("Content-Type", "")
        if "json" in ctype or resp.text[:1] in "{[":
            return resp.json()
        return resp.text

    def create_form(self, title: str, description: str = "") -> dict[str, Any]:
        body: dict[str, Any] = {"title": title}
        if description:
            body["description"] = description
        data = self._request("POST", f"{self.base}/forms", json_body=body)
        if not isinstance(data, dict) or not data.get("id"):
            _die(f"Unexpected create response: {data!r}")
        return data

    def add_question(
        self, form_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.base}/forms('{form_id}')/questions"
        data = self._request("POST", url, json_body=payload)
        if not isinstance(data, dict):
            _die(f"Unexpected question response: {data!r}")
        return data

    def get_form(self, form_id: str) -> dict[str, Any]:
        url = (
            f"{self.base}/forms('{form_id}')"
            "?$select=id,title,description,status,createdDate,modifiedDate"
        )
        data = self._request("GET", url)
        if not isinstance(data, dict):
            _die(f"Unexpected get response: {data!r}")
        return data


def _stringify_info(info: dict[str, Any]) -> str:
    return json.dumps(info, separators=(",", ":"))


def _new_question_id() -> str:
    """Forms API requires question ids that start with 'r'."""
    return "r" + uuid.uuid4().hex


def build_question_payload(
    question: dict[str, Any], order: int
) -> dict[str, Any] | None:
    qtype = (question.get("type") or "").strip().lower()
    title = (question.get("title") or "").strip()
    if not title:
        _die(f"Question missing title: {question!r}")
    if qtype == "manual":
        return None

    required = bool(question.get("required", False))
    base = {
        "title": title,
        "id": _new_question_id(),
        "order": order,
        "isQuiz": False,
        "required": required,
    }

    if qtype == "choice":
        choices = question.get("choices") or []
        if not choices:
            _die(f"Choice question needs choices: {title!r}")
        choice_objs = [
            {"Description": str(c), "IsGenerated": True} for c in choices
        ]
        multi = bool(question.get("multi", False))
        info = {
            "Choices": choice_objs,
            "ChoiceType": 2 if multi else 1,
            "AllowOtherAnswer": bool(question.get("allow_other", False)),
            "OptionDisplayStyle": "ListAll",
            "ChoiceRestrictionType": "None",
            "ShowRatingLabel": False,
        }
        return {**base, "type": "Question.Choice", "questionInfo": _stringify_info(info)}

    if qtype == "text":
        info = {
            "Multiline": bool(question.get("multiline", False)),
            "ShowRatingLabel": False,
        }
        return {
            **base,
            "type": "Question.TextField",
            "questionInfo": _stringify_info(info),
        }

    if qtype == "rating":
        length = int(question.get("length") or 5)
        shape = question.get("shape") or "Star"
        info = {
            "Length": length,
            "RatingShape": shape,
            "LeftDescription": question.get("left") or "",
            "RightDescription": question.get("right") or "",
            "MinRating": 1,
            "ShuffleOptions": False,
            "ShowRatingLabel": False,
            "IsMathQuiz": False,
        }
        return {
            **base,
            "type": "Question.Rating",
            "questionInfo": _stringify_info(info),
        }

    if qtype == "date":
        info = {
            "Date": True,
            "Time": bool(question.get("include_time", False)),
            "ShuffleOptions": False,
            "ShowRatingLabel": False,
            "IsMathQuiz": False,
        }
        return {
            **base,
            "type": "Question.DateTime",
            "questionInfo": _stringify_info(info),
        }

    if qtype == "nps":
        info = {
            "LeftDescription": question.get("left") or "Not at all likely",
            "RightDescription": question.get("right") or "Extremely likely",
            "ShuffleOptions": False,
            "ShowRatingLabel": False,
            "IsMathQuiz": False,
        }
        return {
            **base,
            "type": "Question.NPS",
            "questionInfo": _stringify_info(info),
        }

    if qtype == "file":
        info = {
            "HasSpecificFileType": False,
            "FileTypes": {
                "Word": True,
                "Excel": True,
                "PowerPoint": True,
                "PDF": True,
                "Image": True,
                "Video": True,
                "Audio": True,
            },
            "MaxFileCount": int(question.get("max_files") or 1),
            "MaxFileSize": int(question.get("max_mb") or 10),
            "ShuffleOptions": False,
            "ShowRatingLabel": False,
            "IsMathQuiz": False,
        }
        return {
            **base,
            "type": "Question.FileUpload",
            "questionInfo": _stringify_info(info),
        }

    _die(
        f"Unsupported question type {qtype!r}. "
        "Use choice|text|rating|date|nps|file|manual."
    )
    return None


def designer_url(form_id: str) -> str:
    return (
        "https://forms.cloud.microsoft/Pages/DesignPageV2.aspx"
        f"?origin=shell&subpage=design&id={form_id}"
    )


def respond_url(form_id: str, form: dict[str, Any] | None = None) -> str:
    if form:
        for key in (
            "responderUri",
            "respondUri",
            "responseUrl",
            "shareUrl",
            "publicUrl",
        ):
            val = form.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val
    return f"https://forms.office.com/r/{form_id}"


def cmd_auth(args: argparse.Namespace) -> None:
    token, claims = acquire_token(interactive=not args.device_code)
    print("Authenticated.")
    print(f"  user:   {claims.get('upn') or claims.get('name') or claims['user_id']}")
    print(f"  tenant: {claims['tenant_id']}")
    print(f"  cache:  {TOKEN_CACHE_PATH}")
    # Touch Forms API lightly to prove the token works.
    client = FormsClient(token, claims["tenant_id"], claims["user_id"])
    # List endpoint varies; a create+delete is too heavy — just GET light forms.
    _, requests = _require_deps()
    url = f"{client.base}/light/forms?$top=1"
    resp = client.session.get(url, timeout=60)
    if resp.status_code >= 400:
        print(
            f"Warning: Forms list probe returned {resp.status_code}. "
            "Create may still work.",
            file=sys.stderr,
        )
    else:
        print("Forms API reachable.")


def cmd_whoami(_: argparse.Namespace) -> None:
    token, claims = acquire_token(interactive=True)
    print(json.dumps(claims, indent=2))


def _load_spec(spec_path: Path) -> dict[str, Any]:
    if not spec_path.exists():
        _die(f"Spec not found: {spec_path}")
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _die(f"Invalid JSON in {spec_path}: {exc}")
    title = (spec.get("title") or "").strip()
    if not title:
        _die("Spec missing title")
    questions = spec.get("questions") or []
    if not isinstance(questions, list) or not questions:
        _die("Spec needs a non-empty questions array")
    return spec


def _plan_questions(
    questions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (auto_payloads, manual_questions) with assigned order values."""
    auto: list[dict[str, Any]] = []
    manual: list[dict[str, Any]] = []
    order = 1_000_000
    for q in questions:
        payload = build_question_payload(q, order)
        if payload is None:
            manual.append(q)
            continue
        auto.append(payload)
        order += 1_000_000
    return auto, manual


def cmd_create(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    title = (spec.get("title") or "").strip()
    description = (spec.get("description") or "").strip()
    questions = spec.get("questions") or []
    auto_payloads, manual = _plan_questions(questions)

    if args.dry_run:
        plan = {
            "dry_run": True,
            "title": title,
            "description": description,
            "create_body": {"title": title, **({"description": description} if description else {})},
            "questions": auto_payloads,
            "manual_questions": [
                {"title": m.get("title"), "note": m.get("note")} for m in manual
            ],
            "settings_hint": spec.get("settings") or {},
        }
        print(json.dumps(plan, indent=2))
        return

    token, claims = acquire_token(interactive=not args.device_code)
    client = FormsClient(token, claims["tenant_id"], claims["user_id"])

    form_id = (args.form_id or "").strip()
    form: dict[str, Any]
    if form_id:
        print(f"Adding questions to existing form: {form_id}")
        try:
            form = client.get_form(form_id)
        except SystemExit:
            form = {"id": form_id, "title": title}
    else:
        print(f"Creating form: {title}")
        form = client.create_form(title, description)
        form_id = form["id"]
        print(f"  form id: {form_id}")

    created = 0
    for payload in auto_payloads:
        client.add_question(form_id, payload)
        created += 1
        # Gentle pacing — Forms API is undocumented and rate-sensitive.
        time.sleep(0.15)

    # Refresh metadata if possible
    try:
        form = client.get_form(form_id)
    except SystemExit:
        pass

    out = {
        "id": form_id,
        "title": form.get("title") or title,
        "designer_url": designer_url(form_id),
        "respond_url": respond_url(form_id, form),
        "questions_created": created,
        "manual_questions": [
            {"title": m.get("title"), "note": m.get("note")} for m in manual
        ],
        "settings_hint": spec.get("settings") or {},
    }
    print(json.dumps(out, indent=2))
    print()
    print("Open designer:")
    print(out["designer_url"])
    if out["manual_questions"]:
        print("\nAdd these manually in the designer:")
        for m in out["manual_questions"]:
            note = m.get("note") or "manual question type"
            print(f"  - {m.get('title')} ({note})")


def cmd_validate(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    title = (spec.get("title") or "").strip()
    auto_payloads, manual = _plan_questions(spec.get("questions") or [])
    print(
        json.dumps(
            {
                "ok": True,
                "title": title,
                "auto_create": len(auto_payloads),
                "manual": len(manual),
            },
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Microsoft Forms survey create client (undocumented Forms API)"
    )
    sub = p.add_subparsers(dest="command", required=True)

    auth = sub.add_parser("auth", help="Sign in and cache a Forms token")
    auth.add_argument(
        "--device-code",
        action="store_true",
        help="Force device-code flow instead of interactive browser",
    )
    auth.set_defaults(func=cmd_auth)

    who = sub.add_parser("whoami", help="Show token claims")
    who.set_defaults(func=cmd_whoami)

    create = sub.add_parser("create", help="Create a form from a survey spec JSON")
    create.add_argument("--spec", required=True, help="Path to survey-spec JSON")
    create.add_argument(
        "--device-code",
        action="store_true",
        help="Force device-code flow for auth",
    )
    create.add_argument(
        "--dry-run",
        action="store_true",
        help="Print create + question payloads without calling Forms or signing in",
    )
    create.add_argument(
        "--form-id",
        default="",
        help="Add questions to an existing form id instead of creating a new form",
    )
    create.set_defaults(func=cmd_create)

    validate = sub.add_parser("validate", help="Validate a survey spec without creating")
    validate.add_argument("--spec", required=True)
    validate.set_defaults(func=cmd_validate)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
