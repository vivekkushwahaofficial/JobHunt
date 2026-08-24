"""SmartRecruiters public Posting API adapter."""

from __future__ import annotations

from typing import Any

import requests

from .fetch import Job, strip_html

BASE_URL = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
TIMEOUT = 20
PAGE_SIZE = 100
UA = {"User-Agent": "jobhunt/1.0 (personal job search agent)"}


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        for key in ("text", "label", "name", "value"):
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item.strip()

    return ""


def _location(posting: dict[str, Any]) -> str:
    location = posting.get("location") or {}

    if isinstance(location, dict):
        parts = [
            _text(location.get("city")),
            _text(location.get("region")),
            _text(location.get("country")),
        ]
        return ", ".join(part for part in parts if part)

    return _text(location)


def _description(posting: dict[str, Any]) -> str:
    job_ad = posting.get("jobAd")

    if not isinstance(job_ad, dict):
        return ""

    sections = job_ad.get("sections") or {}

    if not isinstance(sections, dict):
        return ""

    description = sections.get("jobDescription")

    if isinstance(description, dict):
        description = (
            description.get("text")
            or description.get("content")
            or ""
        )

    return strip_html(str(description or ""))


def _is_india(posting: dict[str, Any]) -> bool:
    location = posting.get("location") or {}

    if not isinstance(location, dict):
        return False

    country = str(location.get("country") or "").strip().lower()

    if country == "in":
        return True

    full_location = str(location.get("fullLocation") or "").lower()
    return "india" in full_location


def _is_remote_global(posting: dict[str, Any]) -> bool:
    location = posting.get("location") or {}

    if not isinstance(location, dict) or not bool(location.get("remote")):
        return False

    country = str(location.get("country") or "").strip().lower()
    full_location = str(location.get("fullLocation") or "").strip().lower()

    global_markers = (
        "remote - global",
        "remote - anywhere",
        "remote global",
        "remote anywhere",
        "work from anywhere",
        "location anywhere",
        "worldwide",
        "global remote",
    )

    return not country or any(marker in full_location for marker in global_markers)


def _keep_location(posting: dict[str, Any], mode: str) -> bool:
    """Decide whether a posting belongs in the configured location scope."""
    if mode == "all":
        return True

    india = _is_india(posting)
    remote_global = _is_remote_global(posting)

    if mode == "india":
        return india

    if mode == "remote_global":
        return remote_global

    if mode == "india_or_remote":
        return india or remote_global

    raise ValueError(
        "location_mode must be one of: "
        "india, india_or_remote, remote_global, all"
    )


def parse_smartrecruiters(
    company_slug: str,
    company: str,
    body: Any,
    *,
    location_mode: str = "india_or_remote",
) -> list[Job]:
    """Parse SmartRecruiters postings into Job objects."""
    out: list[Job] = []

    content = (
        (body or {}).get("content", [])
        if isinstance(body, dict)
        else []
    )

    for posting in content:
        if not isinstance(posting, dict):
            continue

        if not _keep_location(posting, location_mode):
            continue

        posting_id = posting.get("id") or posting.get("uuid")

        if posting_id is None:
            continue

        job_url = (
            posting.get("ref")
            or posting.get("postingUrl")
            or ""
        )

        out.append(
            Job(
                job_id=f"smartrecruiters:{company_slug}:{posting_id}",
                ats="smartrecruiters",
                company=company,
                title=_text(posting.get("name")),
                location=_location(posting),
                url=job_url,
                description=_description(posting),
                posted_at=posting.get("releasedDate"),
                salary=None,
            )
        )

    return out


def fetch_smartrecruiters(
    company_slug: str,
    company: str,
    *,
    location_mode: str = "india_or_remote",
    session: requests.Session | None = None,
) -> list[Job]:
    """Fetch all public postings for one SmartRecruiters company."""
    sess = session or requests.Session()

    jobs: list[Job] = []
    offset = 0

    while True:
        params = {
            "limit": PAGE_SIZE,
            "offset": offset,
        }

        try:
            response = sess.get(
                BASE_URL.format(company=company_slug),
                params=params,
                headers=UA,
                timeout=TIMEOUT,
            )

            if response.status_code != 200:
                print(
                    f"  ! smartrecruiters/{company_slug}"
                    f" -> HTTP {response.status_code}"
                )
                return jobs

            body = response.json()

        except Exception as exc:
            print(
                f"  ! smartrecruiters/{company_slug}"
                f" -> {type(exc).__name__}: {exc}"
            )
            return jobs

        jobs.extend(
            parse_smartrecruiters(
                company_slug,
                company,
                body,
                location_mode=location_mode,
            )
        )

        total_found = int(body.get("totalFound") or 0)
        received = len(body.get("content") or [])

        if received == 0:
            break

        offset += received

        if offset >= total_found:
            break

    return jobs


def fetch_smartrecruiters_all(
    companies: list[dict[str, Any]],
    *,
    location_mode: str = "india_or_remote",
    session: requests.Session | None = None,
) -> list[Job]:
    """Fetch all configured SmartRecruiters boards."""
    sess = session or requests.Session()
    jobs: list[Job] = []

    for company in companies:
        got = fetch_smartrecruiters(
            company["slug"],
            company.get("name") or company["slug"],
            location_mode=location_mode,
            session=sess,
        )

        if got:
            print(
                f"  {company.get('name') or company['slug']:<28}"
                f" {len(got):>4} jobs  (smartrecruiters)"
            )

        jobs.extend(got)

    return jobs
