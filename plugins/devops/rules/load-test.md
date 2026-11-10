---
paths:
  - "**/load/**/*.{js,ts}"
  - "**/k6/**/*.{js,ts}"
---

# Load test rules (k6, one run per milestone)

Claims cite grafana.com/docs/k6 (read 2026-11-10).

## What a run proves

- Each target in the spec's non-functional section becomes a k6 threshold that fails the run, for example `http_req_duration: ['p(95)<300']` for "open a conversation in under 300 ms" ([thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/)). A target with no threshold was not tested.
- Model the real shape: an arrival rate (`constant-arrival-rate` or `ramping-arrival-rate`) for request traffic, and `ramping-vus` for the number of people connected at once ([executors](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/)). The peak is the expected online count (for example 200 of 300 people), not a guess.
- Realtime is tested end to end: sockets with `k6/websockets` (the experimental module is deprecated, [WebSockets](https://grafana.com/docs/k6/latest/using-k6/protocols/websockets/)), one virtual user sends, others record the time until they receive it, and that latency is its own threshold.
- The data is at full size first: seed the target volume (for example 5 million messages) in staging before the run, so search and paging are measured where they are slow.

## Where and when

- Runs hit staging, never production, and never a shared third-party project at a rate its owner did not agree to. Seeding a Firestore collection follows the 500/50/5 ramp (backend pack's `rules/firestore.md`, if installed).
- One run at the end of every milestone, scripts committed under `load/`, results (thresholds, p95, errors, cost seen on the bill) saved in the milestone's notes. A failed threshold blocks the milestone like a failed test.
