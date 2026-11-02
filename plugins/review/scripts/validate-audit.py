#!/usr/bin/env python3
"""validate-audit.py — checks specs/audit/coverage-ledger.json and findings.json against references/audit-ledger.md.

Usage: python3 -I validate-audit.py [DIR] [--summary]   (DIR defaults to specs/audit)
Prints every error as `file:record-id: message`; exits 2 on any error, 0 otherwise. --summary prints counts
per verdict and per unit status. Stdlib only: the audited repo may have no node or jsonschema installed.
Adapted from cloudflare/security-audit-skill validate-findings.cjs and validate-coverage-ledger.cjs.
"""
import json
import os
import re
import sys

LEDGER, FINDINGS = "coverage-ledger.json", "findings.json"
AXES = ("bug", "risk", "scale", "missing_test", "speed", "lean")
VERDICTS = ("confirmed", "needs_validation", "rejected")
SEVERITIES = ("must", "should", "nice")
UNIT_STATUSES = ("unaudited", "audited", "stale")
UNIT_KINDS = ("folder", "entry_point", "trust_boundary")
SHA = re.compile(r"^[0-9a-f]{40}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Stable across runs and safe in a shell or a URL, as upstream's fingerprint pattern.
FINDING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]*$")
PATH_LINE = re.compile(r"^[^\s:]+:[1-9]\d*$")
# Which fields each verdict must carry (required) and must not carry (forbidden), per audit-ledger.md.
VERDICT_FIELDS = {
    "confirmed": ({"severity", "fix", "cost_of_skipping"}, {"missing_fact", "refuted_by"}),
    "needs_validation": ({"missing_fact"}, {"severity", "refuted_by"}),
    "rejected": ({"refuted_by"}, {"severity", "missing_fact"}),
}
FINDING_BASE = ("id", "verdict", "axis", "path", "line", "case", "commit", "run_id")
UNIT_FIELDS = ("id", "kind", "path", "status", "last_commit", "axes_checked", "run_id")
RUN_FIELDS = ("run_id", "date", "commit", "units_audited")


class Errors:
    def __init__(self):
        self.lines = []

    def add(self, file, record, message):
        self.lines.append(f"{file}:{record}: {message}")


def load(directory, name, errors):
    path = os.path.join(directory, name)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        errors.add(name, "-", "file is missing")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        errors.add(name, "-", f"not valid JSON — {e}")
    return None


def nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


def positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def check_fields(file, record_id, record, required, forbidden, errors):
    for key in sorted(required):
        if key not in record:
            errors.add(file, record_id, f"missing field '{key}'")
    for key in sorted(forbidden):
        if key in record:
            errors.add(file, record_id, f"field '{key}' is not allowed with verdict '{record.get('verdict')}'")


def check_runs(ledger, errors):
    run_ids = set()
    runs = ledger.get("runs")
    if not isinstance(runs, list):
        errors.add(LEDGER, "runs", "must be a list")
        return run_ids
    for index, run in enumerate(runs, 1):
        rid = f"run {index}"
        if not isinstance(run, dict):
            errors.add(LEDGER, rid, "must be an object")
            continue
        check_fields(LEDGER, rid, run, set(RUN_FIELDS), set(), errors)
        if run.get("run_id") != index:
            errors.add(LEDGER, rid, f"run_id must be {index} (runs are numbered in order), got {run.get('run_id')!r}")
        if not (isinstance(run.get("date"), str) and DATE.match(run["date"])):
            errors.add(LEDGER, rid, "date must be YYYY-MM-DD")
        if not (isinstance(run.get("commit"), str) and SHA.match(run["commit"])):
            errors.add(LEDGER, rid, "commit must be a 40-hex git sha")
        units = run.get("units_audited")
        if not (isinstance(units, int) and not isinstance(units, bool) and units >= 0):
            errors.add(LEDGER, rid, "units_audited must be an integer >= 0")
        if positive_int(run.get("run_id")):
            run_ids.add(run["run_id"])
    return run_ids


def check_unit(unit, index, run_ids, seen, errors):
    uid = unit.get("id") if nonempty_str(unit.get("id")) else f"unit {index}"
    check_fields(LEDGER, uid, unit, set(UNIT_FIELDS), set(), errors)
    if uid in seen:
        errors.add(LEDGER, uid, "duplicate unit id")
    seen.add(uid)
    if unit.get("kind") not in UNIT_KINDS:
        errors.add(LEDGER, uid, f"kind must be one of {', '.join(UNIT_KINDS)}")
    if not nonempty_str(unit.get("path")):
        errors.add(LEDGER, uid, "path must be a non-empty repo-relative path")
    status = unit.get("status")
    if status not in UNIT_STATUSES:
        errors.add(LEDGER, uid, f"status must be one of {', '.join(UNIT_STATUSES)}")
        return
    axes = unit.get("axes_checked", [])
    axes_ok = isinstance(axes, list) and all(a in AXES for a in axes) and len(set(axes)) == len(axes)
    if not axes_ok:
        errors.add(LEDGER, uid, f"axes_checked must list distinct axes from {', '.join(AXES)}")
    if status == "unaudited":
        if unit.get("last_commit") is not None or unit.get("run_id") is not None or (axes_ok and axes):
            errors.add(LEDGER, uid, "an unaudited unit has last_commit null, run_id null and no axes_checked")
        return
    # audited or stale: it was read once, so it must say when, on which commit and on which axes.
    if not (isinstance(unit.get("last_commit"), str) and SHA.match(unit["last_commit"])):
        errors.add(LEDGER, uid, f"a {status} unit needs last_commit as a 40-hex git sha")
    if axes_ok and not axes and "axes_checked" in unit:
        errors.add(LEDGER, uid, f"a {status} unit needs at least one axis in axes_checked")
    if unit.get("run_id") not in run_ids:
        errors.add(LEDGER, uid, f"run_id {unit.get('run_id')!r} is not in runs")


def check_ledger(ledger, errors):
    """Returns the set of run ids, which findings must reference."""
    if not isinstance(ledger, dict):
        errors.add(LEDGER, "-", "top level must be an object with scope, runs and units")
        return set()
    if not nonempty_str(ledger.get("scope")):
        errors.add(LEDGER, "scope", "must be a non-empty repo-relative path ('.' for the whole repo)")
    run_ids = check_runs(ledger, errors)
    units = ledger.get("units")
    if not isinstance(units, list):
        errors.add(LEDGER, "units", "must be a list")
        return run_ids
    seen = set()
    for index, unit in enumerate(units, 1):
        if isinstance(unit, dict):
            check_unit(unit, index, run_ids, seen, errors)
        else:
            errors.add(LEDGER, f"unit {index}", "must be an object")
    return run_ids


def check_finding(finding, index, run_ids, seen, errors):
    fid = finding.get("id") if nonempty_str(finding.get("id")) else f"finding {index}"
    if fid in seen:
        errors.add(FINDINGS, fid, "duplicate finding id")
    seen.add(fid)
    if not (isinstance(finding.get("id"), str) and FINDING_ID.match(finding["id"])):
        errors.add(FINDINGS, fid, f"id must match {FINDING_ID.pattern}")
    verdict = finding.get("verdict")
    if verdict not in VERDICTS:
        errors.add(FINDINGS, fid, f"verdict must be one of {', '.join(VERDICTS)}")
        check_fields(FINDINGS, fid, finding, set(FINDING_BASE), set(), errors)
        return
    required, forbidden = VERDICT_FIELDS[verdict]
    check_fields(FINDINGS, fid, finding, set(FINDING_BASE) | required, forbidden, errors)
    if finding.get("axis") not in AXES:
        errors.add(FINDINGS, fid, f"axis must be one of {', '.join(AXES)}")
    if "severity" in finding and finding["severity"] not in SEVERITIES:
        errors.add(FINDINGS, fid, f"severity must be one of {', '.join(SEVERITIES)}")
    for key in ("path", "case", "fix", "cost_of_skipping", "missing_fact"):
        if key in finding and not nonempty_str(finding[key]):
            errors.add(FINDINGS, fid, f"{key} must be a non-empty string")
    if "line" in finding and not positive_int(finding["line"]):
        errors.add(FINDINGS, fid, "line must be an integer >= 1")
    if "refuted_by" in finding and not (isinstance(finding["refuted_by"], str) and PATH_LINE.match(finding["refuted_by"])):
        errors.add(FINDINGS, fid, "refuted_by must be path:line")
    if "commit" in finding and not (isinstance(finding["commit"], str) and SHA.match(finding["commit"])):
        errors.add(FINDINGS, fid, "commit must be a 40-hex git sha")
    if "run_id" in finding and finding["run_id"] not in run_ids:
        errors.add(FINDINGS, fid, f"run_id {finding['run_id']!r} is not in the ledger's runs")


def check_findings(findings, run_ids, errors):
    if not isinstance(findings, list):
        errors.add(FINDINGS, "-", "top level must be a list of findings")
        return
    seen = set()
    for index, finding in enumerate(findings, 1):
        if isinstance(finding, dict):
            check_finding(finding, index, run_ids, seen, errors)
        else:
            errors.add(FINDINGS, f"finding {index}", "must be an object")


def counts(items, key, order):
    tally = {k: 0 for k in order}
    for item in items:
        if isinstance(item, dict) and item.get(key) in tally:
            tally[item.get(key)] += 1
    return ", ".join(f"{k} {v}" for k, v in tally.items())


def summary(ledger, findings):
    units = ledger.get("units", []) if isinstance(ledger, dict) else []
    runs = ledger.get("runs", []) if isinstance(ledger, dict) else []
    findings = findings if isinstance(findings, list) else []
    covered = sum(1 for u in units if isinstance(u, dict) and u.get("status") == "audited")
    last = runs[-1] if runs and isinstance(runs[-1], dict) else {}
    return "\n".join([
        f"findings: {counts(findings, 'verdict', VERDICTS)} ({len(findings)} total)",
        f"units: {counts(units, 'status', UNIT_STATUSES)} ({len(units)} total); covered {covered}/{len(units)}",
        f"runs: {len(runs)}" + (f" (last run {last.get('run_id')} on {last.get('date')})" if last else ""),
    ])


def main(argv):
    args = [a for a in argv if a != "--summary"]
    directory = args[0] if args else os.path.join("specs", "audit")
    errors = Errors()
    ledger = load(directory, LEDGER, errors)
    findings = load(directory, FINDINGS, errors)
    run_ids = check_ledger(ledger, errors) if ledger is not None else set()
    if findings is not None:
        check_findings(findings, run_ids, errors)
    for line in errors.lines:
        print(line)
    if "--summary" in argv:
        print(summary(ledger, findings))
    return 2 if errors.lines else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
