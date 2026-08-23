# JobHunt

A personal AI-assisted job-search agent for finding relevant software roles without applying on your behalf.

JobHunt reads public ATS job boards, filters obvious mismatches before using an LLM, scores the remaining jobs against your profile, drafts an application kit for the strongest matches, and emails the digest.

> **It never submits an application.** You review the job, edit the generated material, and apply yourself.

```text
ATS job boards
      ↓
deterministic title/location/freshness filter
      ↓
LLM screening against profile.json
      ↓
score + rank
      ↓
draft application kit for the best matches
      ↓
HTML digest → Gmail
```

The deterministic filter runs before the LLM so irrelevant jobs are removed without spending model calls.

---

## This repository's setup

This repository is configured for an entry-level software-engineering job search:

- B.Tech CSE student graduating in 2027
- Internship, graduate, trainee, junior and entry-level roles
- Java, Spring Boot, REST APIs and PostgreSQL focused
- Backend-first, with relevant full-stack opportunities
- India-focused locations with remote roles allowed
- Google Gemini for screening and drafting
- GitHub Actions for weekday automation

The exact company targets and job filters are configured in `companies.yaml` and `config.yaml`.

---

## Run it locally without an API key

```bash
git clone https://github.com/vivekkushwahaofficial/JobHunt.git
cd JobHunt

python -m venv .venv

# Git Bash on Windows
source .venv/Scripts/activate

# PowerShell on Windows
# .venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

python -m pip install -r requirements.txt

python -m jobhunt run --mock --scorer keyword
```

`--mock` uses bundled fixtures through the real parsers and does not access the network.

`--scorer keyword` uses a development-only token-overlap scorer, so no API key is required.

Open:

```text
out/digest.html
```

to inspect the generated digest.

> The keyword scorer is **development-only**. It does not understand seniority, experience, skills, or job meaning like the LLM scorer.

---

## Set it up for a real job search

### 1. Companies

Edit `companies.yaml` to choose the ATS boards you want to poll.

Supported ATS sources:

| ATS        | Public board format                   |
| ---------- | ------------------------------------- |
| Greenhouse | `https://boards.greenhouse.io/<slug>` |
| Lever      | `https://jobs.lever.co/<slug>`        |
| Ashby      | `https://jobs.ashbyhq.com/<slug>`     |

Start with a small, curated list of companies you would realistically join.

Always verify that the current ATS board and slug are valid because companies can migrate ATS providers.

JobHunt does not scrape LinkedIn or Naukri. It uses public ATS endpoints instead.

---

### 2. Filters

`config.yaml` contains the deterministic gate that runs **before** any LLM call.

The current configuration is tuned for a 2027 entry-level candidate and includes roles such as:

- Software Engineer / Software Developer
- SDE / SDE-1
- Backend Engineer / Backend Developer
- Java Engineer / Java Developer
- Full-Stack Engineer / Developer
- Associate Engineer / Associate Developer
- Graduate / Graduate Engineer Trainee
- Junior / Entry-level roles
- Software and engineering internships

It excludes clearly senior, management, unrelated and incompatible roles.

Example settings:

```yaml
filters:
  locations:
    - india
    - bangalore
    - bengaluru
    - hyderabad

  allow_remote: true
  max_age_days: 30

score_threshold: 7.0
max_per_digest: 5
```

> `sde` does not match `Software Development Engineer`. Use `\bsde\b` for the acronym and list spelled-out variants separately.

---

### 3. Build your profile

Put your resume locally in the project directory.

For example:

```text
Vivek_Kumar_Resume.pdf
```

Then run:

```bash
python -m jobhunt profile --resume Vivek_Kumar_Resume.pdf
```

This creates:

```text
profile.json
```

Review `profile.json` carefully and correct anything the model misunderstood.

`profile.json` is gitignored and should remain private.

---

### 4. Run the pipeline

Build the digest:

```bash
python -m jobhunt run
```

Build and send the digest by email:

```bash
python -m jobhunt run --send
```

Limit the number of jobs during testing:

```bash
python -m jobhunt run --limit 10
```

Skip application-material drafting:

```bash
python -m jobhunt run --no-draft
```

---

## Gemini configuration

This repository currently uses Google Gemini for both LLM stages.

```text
LLM_PROVIDER=gemini
SCREEN_MODEL=gemini-3.5-flash-lite
DRAFT_MODEL=gemini-3.6-flash
```

The two stages have different responsibilities:

```text
SCREEN_MODEL
    ↓
Screen many filtered jobs

DRAFT_MODEL
    ↓
Generate application material
for the strongest matches
```

Required local environment variable:

```text
GEMINI_API_KEY=your-key-here
```

Never commit `.env` or share your API key.

The codebase has a provider abstraction, so other providers can be configured if needed, but Gemini is the documented setup for this repository.

---

## Gmail email setup

JobHunt sends the digest through Gmail SMTP.

Local `.env`:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-google-app-password
MAIL_TO=your-email@gmail.com
```

`SMTP_PASS` must be a Google **App Password**, not your normal Gmail password.

For the first setup, `SMTP_USER` and `MAIL_TO` can be the same Gmail address.

---

## Tracking and deduplication

`seen.json` stores jobs that have already been processed so the same posting is not repeatedly shown.

It is gitignored because it is personal state.

Useful commands:

```bash
python -m jobhunt applied "greenhouse:stripe:5501001"
python -m jobhunt stats
```

The tracker is also exported to:

```text
out/tracker.csv
```

---

## GitHub Actions automation

The repository includes:

```text
.github/workflows/daily.yml
```

The workflow runs automatically at:

**06:00 IST, Monday-Friday**

The cloud workflow is:

```text
06:00 IST
    ↓
GitHub Actions
    ↓
restore seen.json cache
    ↓
install dependencies
    ↓
create profile.json from GitHub secret
    ↓
fetch jobs
    ↓
deterministic filtering
    ↓
Gemini screening
    ↓
draft strongest matches
    ↓
send Gmail digest
```

You can also run it manually from:

**GitHub → Actions → daily job digest → Run workflow**

For a safe test, enable:

```text
dry_run = true
```

This generates the digest without sending the email.

---

### GitHub Actions secrets

Configure these under:

**Settings → Secrets and variables → Actions → Secrets**

| Secret           | Value                                     |
| ---------------- | ----------------------------------------- |
| `GEMINI_API_KEY` | Your Gemini API key                       |
| `PROFILE_JSON`   | Complete contents of local `profile.json` |
| `SMTP_HOST`      | `smtp.gmail.com`                          |
| `SMTP_PORT`      | `587`                                     |
| `SMTP_USER`      | Gmail address used to send the digest     |
| `SMTP_PASS`      | Gmail App Password                        |
| `MAIL_TO`        | Destination email address                 |

### GitHub Actions variables

Configure these under:

**Settings → Secrets and variables → Actions → Variables**

```text
LLM_PROVIDER=gemini
SCREEN_MODEL=gemini-3.5-flash-lite
DRAFT_MODEL=gemini-3.6-flash
```

Do not commit any of the following:

```text
.env
profile.json
seen.json
Vivek_Kumar_Resume.pdf
.venv/
out/
```

---

## Tracking state in GitHub Actions

The scheduled workflow keeps `seen.json` in the GitHub Actions cache instead of committing it.

This allows scheduled runs to remember previously processed jobs while keeping personal tracking state out of the repository.

---

## Project layout

```text
jobhunt/
  fetch.py       Job model, HTML cleanup and ATS parsers
  prefilter.py   title/location/freshness gate
  providers.py   swappable LLM provider interface
  llm.py         screening, drafting, profile generation and keyword stub
  digest.py      HTML digest generation
  mailer.py      SMTP email delivery
  store.py       seen.json dedupe + tracker + CSV export
  mock.py        ATS-shaped fixtures
  cli.py         profile / run / applied / stats commands

config.yaml      filters, thresholds and paths
companies.yaml   ATS boards to poll
tests/           parser and LLM tests

.github/
  workflows/
    daily.yml    weekday GitHub Actions automation
```

HTTP fetching is separated from parsing so the mock tests exercise the same parser logic used for real ATS responses.

Each job receives a structured ID:

```text
{ats}:{slug}:{id}
```

This keeps job tracking consistent across runs.

---

## ATS parser details

### Greenhouse

Greenhouse job content can contain HTML entities and HTML markup.

The parser normalizes the content before sending it to the LLM.

### Lever

Lever timestamps are handled as epoch milliseconds.

The parser combines the relevant description fields so that important requirements are not lost.

### Ashby

Unlisted postings with:

```text
isListed: false
```

are skipped.

---

## Tests

Run:

```bash
python -m pytest tests -q
```

The test suite covers:

- ATS parsers
- deterministic filtering
- freshness rules
- location filtering
- the `\bsde\b` regex behavior
- LLM batching
- JD truncation
- JSON parsing
- out-of-order results
- failed batches
- application-kit structure

Tests do not require network access or an API key.

---

## Cost control

The main cost-control mechanism is the deterministic prefilter.

Jobs that fail title, location or freshness checks never reach the LLM screening stage.

While tuning filters, use:

```bash
python -m jobhunt run --limit 10
```

The goal is **high precision rather than maximum application volume**.

A small number of genuinely relevant opportunities is more useful than a large list of weak matches.

---

## Important safety rule

JobHunt is an **assistive job-search tool**, not an auto-apply bot.

It:

```text
Finds jobs
   ↓
Filters jobs
   ↓
Ranks jobs
   ↓
Drafts application material
   ↓
Emails you
```

It does **not**:

```text
Automatically submit applications
```

You remain responsible for reviewing the job description, checking eligibility, editing generated material, and submitting the application yourself.
