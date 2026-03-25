# Learner Submission Guidelines

This document explains, how to prepare and submit a project for automated evaluation. It focuses on practical steps, common pitfalls, and debugging tips so you can reliably pass the automated tests.

---

## Quick Summary

- Package your project as a ZIP containing exactly one top-level folder (your project folder).
- Include a `docker-compose.yml` at the top level of that folder that builds and starts your service.
- The evaluator expects your service to expose a working HTTP API and a `/health` endpoint that returns HTTP 200.
- Implement the endpoints and response shapes asserted in the provided `.feature` file exactly.
- Upload via the web UI; evaluation runs in the background and produces downloadable artifacts and an HTML Karate report.

---

## 1. Before You Start: checklist for local readiness

- Your app runs locally with `docker compose up --build`.
- `GET /health` returns 200 within a few seconds of startup.
- Confirm the endpoints and response bodies used by the problem's Karate `.feature` file are implemented.

---

## 2. ZIP file structure (required)

Your ZIP must have exactly one top-level folder. The evaluator rejects zips that:

- Contain files at the ZIP root (e.g., `docker-compose.yml` must be inside the single top-level folder).
- Contain multiple top-level folders.
- Nest `docker-compose.yml` too deep (it must be directly inside the top-level folder).

Example accepted layout:

```
my-submission.zip
└── my-submission/
    ├── docker-compose.yml
    ├── src/
    ├── Dockerfile (optional)
    └── README.md
```

Notes:
- macOS may add `__MACOSX/` entries; these are ignored.
- Keep ZIP size under the size limit (check contest instructions; default 50 MB).

---

## 3. Docker Compose: make your service start reliably

- Expose the container port your app listens on via `ports:` (host-side port may be remapped by the evaluator).
- Ensure any dependent services (databases, caches) are declared in the same `docker-compose.yml`.
- The evaluator waits up to 90 seconds for your `GET /health` to become OK — aim for faster startup.

Tips:
- Add readiness logic to your app (don't return 200 from `/health` until DB migrations are done).
- If your app seeds data at startup (e.g., create user `testing`), ensure seeding finishes before `/health` returns 200.

---

## 4. Required runtime behaviour

### 4.1 `/health`
- Must return HTTP 200 without authentication.
- Response body can be any valid JSON (e.g., `{ "status": "ok" }`).

### 4.3 Problem-specific endpoints (Karate)
- For Karate-based problems, the provided `.feature` file is the contract. Implement exactly what it asserts.
- Many Karate assertions check deep equality. A single missing field or wrong field name will fail the scenario.
- Your code should not require file uploads from participants unless stated in the problem; if a puzzle image or asset is pre-bundled, your code must read it from within the container at the expected path.

---

## 5. How evaluation runs (what you will see)

1. The submission is accepted and queued (you get a `jobId`).
2. The evaluator extracts the ZIP into a versioned folder and runs `docker compose up --build`.
3. It polls `GET /health` until it returns 200 (90s timeout).
4. The evaluator runs the supplied Karate `.feature` file against your running service.
5. Karate writes a report; the evaluator parses the summary and computes your score = (scenarios passed / total) × 100.
7. You can download `evaluation-result.json` and view the interactive Karate HTML report from the UI.

What this means for you:
- Focus on making the scenarios in the feature file pass — that directly determines your score.
- Use the Karate HTML report to see which assertions failed and why.

---

## 6. Scoring rules (practical)

- Each Karate scenario is a scoring unit. The final score = percentage of Karate scenarios that passed.
- A scenario passes only if every assertion in it succeeds and the expected HTTP status code matches.
- The health check and Docker startup gates must succeed for testing to begin but do not count as scored scenarios.

---

## 7. Debugging and common failures

- `docker compose up` fails: check `docker-compose.yml` syntax and build contexts; run locally and fix build errors first.
- `/health` never returns 200: ensure your app finishes startup tasks (migrations, seeding) before reporting healthy.
- Karate scenario failures: open the Karate HTML report (UI) to see the failing step, the expected value, and the actual response. Fix the response shape or status code.
- Score shows 0: verify Karate wrote `karate-summary-json.txt`; if the summary is missing or unparseable, the evaluator sets score to 0.

---

## 9. Submission checklist

- [ ] ZIP contains exactly one top-level folder
- [ ] `docker-compose.yml` is directly inside that top-level folder
- [ ] `docker compose up --build` starts without errors locally
- [ ] `GET /health` returns 200 within 90s
- [ ] Endpoints asserted in the Karate `.feature` file are implemented and return exact shapes
- [ ] Any required assets (images, seed data) are bundled in your project where your code expects them
- [ ] ZIP size is below the contest limit

---

## 10. FAQs

Q: My feature file asserts exact JSON and my service returns extra fields — will it fail?
A: Yes — Karate deep equality checks will fail if extra fields are present when the assertion uses exact equality. Make sure to return only the fields the feature expects, or modify the feature if allowed by problem instructions.

Q: Can I change the feature file?
A: No. The feature file distributed with the problem is the contract for evaluation.

Q: Where do I see detailed failures?
A: After evaluation, open the **View Karate Test Report** link in the UI. It shows per-scenario failures, request/response artifacts, and exact assertion diffs.

---