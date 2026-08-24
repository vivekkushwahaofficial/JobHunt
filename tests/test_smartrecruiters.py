from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jobhunt.smartrecruiters import parse_smartrecruiters


def _posting(
    *,
    posting_id: str = "12345",
    country: str = "in",
    city: str = "Pune",
    remote: bool = False,
    full_location: str | None = None,
):
    return {
        "id": posting_id,
        "uuid": "uuid-123",
        "name": "Software Engineer - Java",
        "location": {
            "city": city,
            "region": "Maharashtra" if country == "in" else "",
            "country": country,
            "remote": remote,
            "hybrid": False,
            "fullLocation": (
                full_location
                if full_location is not None
                else (
                    f"{city}, Maharashtra, India"
                    if country == "in"
                    else f"{city}, France"
                )
            ),
        },
        "releasedDate": "2026-08-24T10:00:00Z",
        "ref": f"https://jobs.example.com/job/{posting_id}",
        "jobAd": {
            "sections": {
                "jobDescription": {
                    "text": "<p>Build Java backend services.</p>"
                }
            }
        },
    }


def test_parse_smartrecruiters_maps_basic_posting():
    jobs = parse_smartrecruiters(
        "example-company",
        "Example Company",
        {"content": [_posting()]},
    )

    assert len(jobs) == 1

    job = jobs[0]

    assert job.job_id == "smartrecruiters:example-company:12345"
    assert job.ats == "smartrecruiters"
    assert job.company == "Example Company"
    assert job.title == "Software Engineer - Java"
    assert job.location == "Pune, Maharashtra, in"
    assert job.url == "https://jobs.example.com/job/12345"
    assert job.posted_at == "2026-08-24T10:00:00Z"
    assert "Build Java backend services." in job.description


def test_parse_empty_response():
    assert parse_smartrecruiters(
        "example",
        "Example",
        {},
    ) == []


def test_missing_id_is_skipped():
    body = {"content": [{"name": "Missing ID"}]}

    assert parse_smartrecruiters(
        "example",
        "Example",
        body,
    ) == []


def test_job_id_is_namespaced():
    jobs = parse_smartrecruiters(
        "nagarro",
        "Nagarro",
        {"content": [_posting(posting_id="123")]},
    )

    assert jobs[0].job_id == "smartrecruiters:nagarro:123"


def test_india_mode_keeps_india_only():
    body = {
        "content": [
            _posting(posting_id="india-1", country="in"),
            _posting(
                posting_id="france-1",
                country="fr",
                city="Paris",
                full_location="Paris, France",
            ),
        ]
    }

    jobs = parse_smartrecruiters(
        "example",
        "Example",
        body,
        location_mode="india",
    )

    assert len(jobs) == 1
    assert jobs[0].job_id.endswith(":india-1")


def test_india_or_remote_keeps_india_and_global_remote():
    body = {
        "content": [
            _posting(posting_id="india-1", country="in"),
            _posting(
                posting_id="remote-global",
                country="",
                city="Remote",
                remote=True,
                full_location="Remote - Global",
            ),
            _posting(
                posting_id="germany-remote",
                country="de",
                city="Remote",
                remote=True,
                full_location="Remote, Germany",
            ),
            _posting(
                posting_id="france-1",
                country="fr",
                city="Paris",
                remote=False,
                full_location="Paris, France",
            ),
        ]
    }

    jobs = parse_smartrecruiters(
        "example",
        "Example",
        body,
        location_mode="india_or_remote",
    )

    ids = {job.job_id for job in jobs}

    assert ids == {
        "smartrecruiters:example:india-1",
        "smartrecruiters:example:remote-global",
    }


def test_remote_global_keeps_only_unrestricted_remote():
    body = {
        "content": [
            _posting(
                posting_id="remote-global",
                country="",
                city="Remote",
                remote=True,
                full_location="Remote - Anywhere",
            ),
            _posting(
                posting_id="remote-germany",
                country="de",
                city="Remote",
                remote=True,
                full_location="Remote, Germany",
            ),
            _posting(
                posting_id="onsite",
                country="us",
                remote=False,
                full_location="New York, United States",
            ),
        ]
    }

    jobs = parse_smartrecruiters(
        "example",
        "Example",
        body,
        location_mode="remote_global",
    )

    assert len(jobs) == 1
    assert jobs[0].job_id.endswith(":remote-global")


def test_all_mode_keeps_every_posting():
    body = {
        "content": [
            _posting(posting_id="india", country="in"),
            _posting(posting_id="france", country="fr", city="Paris"),
        ]
    }

    jobs = parse_smartrecruiters(
        "example",
        "Example",
        body,
        location_mode="all",
    )

    assert len(jobs) == 2
