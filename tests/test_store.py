from datetime import datetime, timedelta, timezone

from jobhunt.fetch import Job
from jobhunt.store import Store


def make_job(job_id="job-1"):
    """Create a small test job."""
    return Job(
        job_id=job_id,
        company="Test Company",
        title="Software Engineer",
        location="India",
        url="https://example.com/job",
        ats="test",
        description="Backend software engineering role.",
    )


def test_new_job_is_returned(tmp_path):
    """A job that has never been seen should be returned."""
    store = Store(tmp_path / "seen.json")

    job = make_job()

    result = store.unseen([job], recheck_after_days=7)

    assert result == [job]


def test_job_seen_less_than_7_days_ago_is_not_returned(tmp_path):
    """A previously checked job should wait until 7 days have passed."""
    store = Store(tmp_path / "seen.json")

    job = make_job()

    six_days_ago = (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()

    store.data[job.job_id] = {
        "first_seen": six_days_ago,
        "last_checked": six_days_ago,
        "applied": False,
    }

    result = store.unseen([job], recheck_after_days=7)

    assert result == []


def test_job_seen_7_days_ago_is_returned(tmp_path):
    """A previously checked job should be rechecked after 7 days."""
    store = Store(tmp_path / "seen.json")

    job = make_job()

    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    store.data[job.job_id] = {
        "first_seen": seven_days_ago,
        "last_checked": seven_days_ago,
        "applied": False,
    }

    result = store.unseen([job], recheck_after_days=7)

    assert result == [job]


def test_applied_job_is_not_rechecked(tmp_path):
    """Applied jobs should never be returned for re-checking."""
    store = Store(tmp_path / "seen.json")

    job = make_job()

    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    store.data[job.job_id] = {
        "first_seen": seven_days_ago,
        "last_checked": seven_days_ago,
        "applied": True,
    }

    result = store.unseen([job], recheck_after_days=7)

    assert result == []
