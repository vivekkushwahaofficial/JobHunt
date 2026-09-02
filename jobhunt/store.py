"""seen.json doubles as the dedupe index AND the application tracker."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .fetch import Job


class Store:
    def __init__(self, path: str | Path = "seen.json"):
        self.path = Path(path)
        self.data: dict[str, dict] = {}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                print(f"  ! {self.path} corrupt, starting fresh")


def unseen(
    self,
    jobs: list[Job],
    recheck_after_days: int = 7,
) -> list[Job]:
    """Return new jobs and jobs due for re-checking."""
    now = datetime.now(timezone.utc)
    result = []

    for job in jobs:
        # Always include jobs that have never been seen.
        if job.job_id not in self.data:
            result.append(job)
            continue

        record = self.data[job.job_id]

        # Use last_checked for new records.
        # Fall back to first_seen for existing records.
        last_checked = record.get("last_checked") or record.get("first_seen")

        # Re-check if there is no valid timestamp.
        if not last_checked:
            result.append(job)
            continue

        try:
            checked_at = datetime.fromisoformat(last_checked.replace("Z", "+00:00"))
        except ValueError:
            result.append(job)
            continue

        # Include the job when it is at least N days old.
        age_days = (now - checked_at).days

        if age_days >= recheck_after_days:
            result.append(job)

    return result

    def record(self, jobs: list[Job], emailed: bool) -> None:
        now = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    for j in jobs:
        self.data.setdefault(
            j.job_id,
            {
                "first_seen": now,
                "company": j.company,
                "title": j.title,
                "location": j.location,
                "url": j.url,
                "score": j.score,
                "reason": j.reason,
                "emailed": emailed,
                "applied": False,
                "applied_on": None,
            },
        )

        # Store when this job was last checked.
        self.data[j.job_id]["last_checked"] = now

        # Keep the latest screening result.
        self.data[j.job_id]["score"] = j.score
        self.data[j.job_id]["reason"] = j.reason

        # Never change True back to False.
        if emailed:
            self.data[j.job_id]["emailed"] = True

    self.save()

    def mark_applied(self, job_id: str) -> bool:
        if job_id not in self.data:
            return False
        self.data[job_id]["applied"] = True
        self.data[job_id]["applied_on"] = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )
        self.save()
        return True

    def stats(self) -> dict:
        return {
            "tracked": len(self.data),
            "emailed": sum(1 for v in self.data.values() if v.get("emailed")),
            "applied": sum(1 for v in self.data.values() if v.get("applied")),
        }

    def export_csv(self, path: str | Path = "out/tracker.csv") -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cols = [
            "first_seen",
            "company",
            "title",
            "location",
            "score",
            "reason",
            "applied",
            "applied_on",
            "url",
        ]
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["job_id"] + cols, extrasaction="ignore")
            w.writeheader()
            for jid, row in sorted(
                self.data.items(),
                key=lambda kv: kv[1].get("first_seen", ""),
                reverse=True,
            ):
                w.writerow({"job_id": jid, **row})
        return path

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))
