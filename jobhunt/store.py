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
        result: list[Job] = []

        for job in jobs:
            # Job has never been seen before.
            if job.job_id not in self.data:
                result.append(job)
                continue

            record = self.data[job.job_id]

            # Do not re-check jobs that have already been applied to.
            if record.get("applied"):
                continue

            # Prefer last_checked for re-check scheduling.
            # Fall back to first_seen for older records.
            checked_at = record.get("last_checked") or record.get("first_seen")

            if not checked_at:
                result.append(job)
                continue

            try:
                checked_time = datetime.fromisoformat(checked_at)

                # Handle old timestamps without timezone information.
                if checked_time.tzinfo is None:
                    checked_time = checked_time.replace(tzinfo=timezone.utc)

                age_days = (now - checked_time).days

            except (ValueError, TypeError):
                # If the stored timestamp is invalid, check the job again.
                result.append(job)
                continue

            # Job is due for another screening.
            if age_days >= recheck_after_days:
                result.append(job)

        return result

    def record(self, jobs: list[Job], emailed: bool) -> None:
        """Record jobs and update their latest screening information."""

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        for job in jobs:
            record = self.data.setdefault(
                job.job_id,
                {
                    "first_seen": now,
                    "company": job.company,
                    "title": job.title,
                    "location": job.location,
                    "url": job.url,
                    "score": job.score,
                    "reason": job.reason,
                    "emailed": emailed,
                    "applied": False,
                    "applied_on": None,
                },
            )

            # Record when this job was last checked.
            record["last_checked"] = now

            # Keep the latest screening result.
            record["score"] = job.score
            record["reason"] = job.reason

            # Once emailed, keep the emailed status as True.
            if emailed:
                record["emailed"] = True

        self.save()

    def mark_applied(self, job_id: str) -> bool:
        """Mark a tracked job as applied."""

        if job_id not in self.data:
            return False

        self.data[job_id]["applied"] = True
        self.data[job_id]["applied_on"] = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

        self.save()
        return True

    def stats(self) -> dict:
        """Return tracker statistics."""

        return {
            "tracked": len(self.data),
            "emailed": sum(1 for value in self.data.values() if value.get("emailed")),
            "applied": sum(1 for value in self.data.values() if value.get("applied")),
        }

    def export_csv(self, path: str | Path = "out/tracker.csv") -> Path:
        """Export the application tracker to CSV."""

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
            writer = csv.DictWriter(
                fh,
                fieldnames=["job_id"] + cols,
                extrasaction="ignore",
            )

            writer.writeheader()

            for job_id, row in sorted(
                self.data.items(),
                key=lambda item: item[1].get("first_seen", ""),
                reverse=True,
            ):
                writer.writerow({"job_id": job_id, **row})

        return path

    def save(self) -> None:
        """Persist tracker data to seen.json."""

        self.path.write_text(
            json.dumps(
                self.data,
                indent=2,
                ensure_ascii=False,
            )
        )
