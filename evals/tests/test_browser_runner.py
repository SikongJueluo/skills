"""Offline tests for the case-6 browser runner.

No network, Podman or model call: the Playwright import lives inside the render
path, so the pure gate helpers run anywhere. ``EVENT_RECORDS`` and ``CONTROLS``
below are saved literals of what ``EXTRACT_SNAPSHOT_JS`` returns for the fixed
dashboard fixture in a real headless Chromium; the fixture itself is checked as
the source of truth for that data, and when a Chromium binary is installed the
browser-side regressions execute the real extraction scripts (they skip
otherwise).

Run with: `uv run --locked python -m pytest evals/tests -q`
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from evals import browser_runner as R  # noqa: E402

FIXTURE = (
    REPO_ROOT / "skills/refactor-ui/evals/fixtures/dense-dashboard/index.html"
)
CHECK_NAMES = [
    "page_loads",
    "body_visible",
    "metrics_preserved",
    "event_records_preserved",
    "filter_labels_visible",
    "filter_controls_available",
    "primary_action_enabled",
]

# Saved literal: the ten event rows the fixture renders, as the browser reports
# their visible cell text (row order as authored; the gate itself is
# order-insensitive).
EVENT_RECORDS = [
    ["14:32", "CRIT", "checkout", "us-east-1", "5xx spike on payment authorization", "M. Chen", "Investigating"],
    ["14:28", "WARN", "search", "us-east-1", "P95 latency above 300 ms", "A. Okafor", "Monitoring"],
    ["14:11", "INFO", "payments", "eu-west-1", "Canary deploy reached 100%", "J. Ruiz", "Complete"],
    ["13:58", "WARN", "checkout", "us-east-1", "DB connection pool above 80%", "M. Chen", "Investigating"],
    ["13:40", "INFO", "search", "eu-west-1", "Index rebuild finished", "A. Okafor", "Complete"],
    ["13:22", "CRIT", "payments", "us-east-1", "Provider timeout rate above 2%", "J. Ruiz", "Mitigated"],
    ["13:05", "WARN", "search", "us-east-1", "Queue depth growing for 18 min", "A. Okafor", "Monitoring"],
    ["12:47", "INFO", "checkout", "eu-west-1", "Feature flag checkout_v3 enabled", "M. Chen", "Complete"],
    ["12:30", "INFO", "infra", "us-east-1", "Node pool scaled 12 → 15", "J. Ruiz", "Complete"],
    ["12:14", "WARN", "payments", "eu-west-1", "Retry backlog above threshold", "J. Ruiz", "Mitigated"],
]

# Saved literal: the fixture's five render-time controls, with the label
# association and option list the browser extraction reports.
CONTROLS = [
    {"tag": "select", "label": "", "options": ["Production", "Staging"]},
    {"tag": "select", "label": "Region", "options": ["All regions", "us-east-1", "eu-west-1"]},
    {"tag": "select", "label": "Service", "options": ["All services", "checkout", "payments", "search"]},
    {"tag": "select", "label": "Severity", "options": ["All severities", "Critical", "Warning", "Info"]},
    {"tag": "select", "label": "", "options": ["Last 24 hours", "Last 7 days"]},
]

FILTER_OPTIONS = {
    control["label"]: control["options"] for control in CONTROLS if control["label"]
}


def dashboard_snapshot() -> dict:
    """Saved literal: the fixed fixture as the browser snapshot would report it."""
    containers = [
        {"tag": "div", "text": f"{label.upper()} {value} ▲ 4.2%"} for label, value in R.METRICS.items()
    ]
    containers += [
        {"tag": "label", "text": "Region"},
        {"tag": "label", "text": "Service"},
        {"tag": "label", "text": "Severity"},
        # A column header is not a filter label; the label check must ignore it.
        {"tag": "th", "text": "TIME SEVERITY SERVICE REGION EVENT OWNER STATUS", "inHeader": True},
        {"tag": "th", "text": "REGION", "inHeader": True},
    ]
    return {
        "readyState": "complete",
        "title": "Northwind Ops — Overview",
        "body": {"visible": True, "width": 1440, "height": 3812, "textLength": 5120},
        "containers": containers,
        "tables": [
            {
                "tag": "table",
                "visible": True,
                "dataRows": len(EVENT_RECORDS),
                "headerCells": 7,
                "records": [list(row) for row in EVENT_RECORDS],
            }
        ],
        "controls": [
            {
                "tag": control["tag"],
                "label": control["label"],
                "options": list(control["options"]),
                "visible": True,
                "enabled": True,
            }
            for control in CONTROLS
        ],
        "actions": [
            {"tag": "button", "text": "New incident", "visible": True, "enabled": True}
        ],
    }


def blank_snapshot() -> dict:
    """Saved literal: an empty document that parsed but rendered nothing."""
    return {
        "readyState": "complete",
        "title": "",
        "body": {"visible": False, "width": 1440, "height": 0, "textLength": 0},
        "containers": [],
        "tables": [],
        "controls": [],
        "actions": [],
    }


def anchor_of(snapshot: dict | None = None) -> dict:
    """The baseline-derived data contract used to grade a candidate."""
    return R.derive_anchor(snapshot or dashboard_snapshot())


def with_records(records) -> dict:
    snapshot = dashboard_snapshot()
    snapshot["tables"][0]["records"] = [list(row) for row in records]
    return snapshot


def control(snapshot: dict, label: str) -> dict:
    return next(entry for entry in snapshot["controls"] if entry["label"] == label)


def check(page: dict, name: str) -> dict:
    return next(entry for entry in page["checks"] if entry["name"] == name)


def test_fixed_render_contract():
    assert (R.VIEWPORT_WIDTH, R.VIEWPORT_HEIGHT) == (1440, 1100)
    assert R.DEVICE_SCALE_FACTOR == 1
    assert R.LOCALE == "en-US"
    assert R.TIMEZONE_ID == "UTC"


def test_expected_metrics_match_the_fixture_source():
    source = FIXTURE.read_text(encoding="utf-8")

    assert len(R.METRICS) == 12
    assert source.count('<div class="metric">') == 12
    for label, value in R.METRICS.items():
        assert label in source, f"metric label not in fixture: {label}"
        assert value in source, f"metric value not in fixture: {value}"


def test_expected_controls_match_the_fixture_source():
    source = FIXTURE.read_text(encoding="utf-8")

    for label in R.FILTER_LABELS:
        assert f"<label>{label}</label>" in source, f"filter label not in fixture: {label}"
    for entry in CONTROLS:
        for option in entry["options"]:
            assert f"<option>{option}</option>" in source, f"option not in fixture: {option}"
    assert '<button class="btn">New incident</button>' in source


def test_expected_event_records_match_the_fixture_source():
    source = FIXTURE.read_text(encoding="utf-8")

    parsed = []
    for row in re.findall(r"<tr>(.*?)</tr>", source, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if not cells:
            continue
        parsed.append([re.sub(r"<[^>]+>", "", cell).strip() for cell in cells])
    assert parsed == EVENT_RECORDS
    assert len(EVENT_RECORDS) == R.EVENT_TABLE_MIN_ROWS == 10


def test_snapshot_literal_keeps_the_anchor_derivation_stable():
    anchor = anchor_of()

    assert len(anchor["records"]) == 10
    assert anchor["controls"]["Region"] == ("All regions", "us-east-1", "eu-west-1")
    assert anchor["controls"]["Service"] == ("All services", "checkout", "payments", "search")
    assert anchor["controls"]["Severity"] == ("All severities", "Critical", "Warning", "Info")
    # The unlabelled daily controls are not filter controls.
    assert "" not in anchor["controls"]


def test_fixture_wide_snapshot_passes_every_check():
    page = R.evaluate_page(dashboard_snapshot(), loads=True)

    assert page["passed"] is True, page["checks"]
    assert [entry["name"] for entry in page["checks"]] == CHECK_NAMES
    assert all(entry["passed"] for entry in page["checks"])


def test_blank_document_fails_every_render_check_without_crashing():
    page = R.evaluate_page(blank_snapshot(), loads=True)

    assert page["passed"] is False
    assert [entry["name"] for entry in page["checks"]] == CHECK_NAMES
    # The blank document did load; everything about its content is missing.
    assert page["checks"][0]["name"] == "page_loads"
    assert page["checks"][0]["passed"] is True
    assert not any(entry["passed"] for entry in page["checks"][1:])


def test_load_failure_fails_the_first_check_only():
    page = R.evaluate_page(dashboard_snapshot(), loads=False, page_errors=["boom"])

    assert page["passed"] is False
    assert page["checks"][0]["name"] == "page_loads"
    assert page["checks"][0]["passed"] is False
    assert page["checks"][0]["page_error_count"] == 1
    assert all(entry["passed"] for entry in page["checks"][1:])


def test_body_must_be_visible_and_non_empty():
    snapshot = dashboard_snapshot()
    assert R.body_visible_check(snapshot)["passed"] is True

    snapshot["body"] = {"visible": True, "width": 1440, "height": 900, "textLength": 0}
    assert R.body_visible_check(snapshot)["passed"] is False

    snapshot["body"] = {"visible": False, "width": 1440, "height": 0, "textLength": 200}
    assert R.body_visible_check(snapshot)["passed"] is False


# ---------------------------------------------------------------- metric values


def test_metric_values_do_not_match_inside_larger_numbers():
    assert R.contains_token("ACTIVE INCIDENTS 3 1 critical", "3") is True
    assert R.contains_token("ACTIVE INCIDENTS 13 1 critical", "3") is False
    assert R.contains_token("DEPLOYS TODAY 18 All passed", "18") is True
    assert R.contains_token("DEPLOYS TODAY 1,842 All passed", "18") is False
    assert R.contains_token("UPTIME 10.84%", "0.84%") is False
    assert R.contains_token("CPU 164% Normal", "64%") is False
    assert R.contains_token("P95 LATENCY 284 ms", "284 ms") is True
    assert R.contains_token("DB CONNECTIONS 412 / 500", "412 / 500") is True
    assert R.contains_token("checkout v4.18.2", "18") is False
    assert R.contains_token("", "3") is False


def test_embedded_metric_value_fails_the_pair():
    snapshot = dashboard_snapshot()
    snapshot["containers"] = [
        {"tag": "div", "text": "ACTIVE INCIDENTS 13 1 critical"}
        if entry["text"].startswith("ACTIVE INCIDENTS")
        else entry
        for entry in snapshot["containers"]
    ]
    result = R.metrics_check(snapshot)

    assert result["passed"] is False
    assert result["unpaired_metrics"] == ["Active incidents"]


def test_metrics_allow_regrouping_but_not_deleted_names_or_values():
    # A restyled card still holds its label and value in one element.
    regrouped = dashboard_snapshot()
    regrouped["containers"] = [
        {"tag": "article", "text": f"{value} — {label}"}
        for label, value in R.METRICS.items()
    ]
    assert R.metrics_check(regrouped)["passed"] is True

    # A value moved into a different card breaks the pairing.
    split = dashboard_snapshot()
    split["containers"] = [
        {"tag": "div", "text": label} for label in R.METRICS
    ] + [{"tag": "div", "text": value} for value in R.METRICS.values()]
    result = R.metrics_check(split)
    assert result["passed"] is False
    assert len(result["missing_labels"]) + len(result["unpaired_metrics"]) > 0


def test_metrics_report_missing_label_and_changed_value_separately():
    deleted = dashboard_snapshot()
    deleted["containers"] = [
        entry for entry in deleted["containers"] if "REQUESTS / SEC" not in entry["text"]
    ]
    result = R.metrics_check(deleted)
    assert result["passed"] is False
    assert result["missing_labels"] == ["Requests / sec"]

    reworded = dashboard_snapshot()
    reworded["containers"] = [
        {"tag": "div", "text": entry["text"].replace("12.4k", "11.9k")}
        for entry in reworded["containers"]
    ]
    result = R.metrics_check(reworded)
    assert result["passed"] is False
    assert result["missing_labels"] == []
    assert result["unpaired_metrics"] == ["Requests / sec"]


def test_one_long_aggregate_container_cannot_hide_a_deleted_card():
    deleted = dashboard_snapshot()
    deleted["containers"] = [
        entry for entry in deleted["containers"] if "REQUESTS / SEC" not in entry["text"]
    ]
    aggregate = " ".join(
        f"{label} {value} ▲ 4.2% vs last week" for label, value in R.METRICS.items()
    )
    deleted["containers"].append({"tag": "section", "text": aggregate})
    # The aggregate is longer than MAX_CONTAINER_TEXT, so it is not a control;
    # the extraction would not even collect it.
    assert len(R.normalize(aggregate)) > R.MAX_CONTAINER_TEXT
    assert R.metrics_check(deleted)["passed"] is False


def test_container_cap_is_wired_into_the_extraction_script():
    assert f"const MAX_CONTAINER_TEXT = {R.MAX_CONTAINER_TEXT};" in R.EXTRACT_SNAPSHOT_JS


# --------------------------------------------------------------- event records


def test_event_records_require_every_baseline_row():
    anchor = anchor_of()
    rows = [list(row) for row in EVENT_RECORDS]
    del rows[2]

    result = check(
        R.evaluate_page(with_records(rows), loads=True, anchor=anchor),
        "event_records_preserved",
    )
    assert result["passed"] is False
    assert len(result["lost_records"]) == 1
    assert "14:11" in result["lost_records"][0]
    assert result["data_rows"] == 9


def test_ten_rows_of_the_wrong_events_still_fail():
    anchor = anchor_of()
    rows = [list(row) for row in EVENT_RECORDS]
    rows[5] = list(rows[0])  # duplicate one event, lose another; still ten rows

    result = check(
        R.evaluate_page(with_records(rows), loads=True, anchor=anchor),
        "event_records_preserved",
    )
    assert result["passed"] is False
    assert len(result["lost_records"]) == 1
    assert "13:22" in result["lost_records"][0]


def test_edited_cell_fails_the_record():
    anchor = anchor_of()
    rows = [list(row) for row in EVENT_RECORDS]
    rows[6][6] = "Open"

    result = check(
        R.evaluate_page(with_records(rows), loads=True, anchor=anchor),
        "event_records_preserved",
    )
    assert result["passed"] is False
    assert "13:05" in result["lost_records"][0]


def test_record_matching_ignores_row_and_column_order():
    anchor = anchor_of()
    rows = [list(reversed(row)) for row in reversed(EVENT_RECORDS)]

    page = R.evaluate_page(with_records(rows), loads=True, anchor=anchor)
    assert check(page, "event_records_preserved")["passed"] is True


def test_extra_rows_are_allowed():
    anchor = anchor_of()
    rows = [list(row) for row in EVENT_RECORDS] + [
        ["11:59", "INFO", "infra", "us-east-1", "Synthetic extra event", "J. Ruiz", "Complete"]
    ]

    page = R.evaluate_page(with_records(rows), loads=True, anchor=anchor)
    assert check(page, "event_records_preserved")["passed"] is True


def test_hidden_row_and_hidden_cell_do_not_count():
    anchor = anchor_of()
    # The extraction drops a display:none row before the gate sees it.
    without_row = [list(row) for row in EVENT_RECORDS if row[0] != "14:32"]
    result = check(
        R.evaluate_page(with_records(without_row), loads=True, anchor=anchor),
        "event_records_preserved",
    )
    assert result["passed"] is False
    assert "14:32" in result["lost_records"][0]

    # The extraction drops a hidden cell, so its row no longer carries the data.
    without_owner = [list(row[:6]) for row in EVENT_RECORDS]
    result = check(
        R.evaluate_page(with_records(without_owner), loads=True, anchor=anchor),
        "event_records_preserved",
    )
    assert result["passed"] is False


def test_merged_cells_keep_a_record_when_all_text_survives():
    anchor = anchor_of()
    merged = [[" ".join(row[:2])] + list(row[2:]) for row in EVENT_RECORDS]

    page = R.evaluate_page(with_records(merged), loads=True, anchor=anchor)
    assert check(page, "event_records_preserved")["passed"] is True


def test_baseline_anchor_needs_ten_records():
    result = R.event_records_check(with_records(EVENT_RECORDS[:9]), None)

    assert result["passed"] is False
    assert result["data_rows"] == 9


def test_bipartite_matching_requires_distinct_partners():
    assert R._bipartite_match([[0], [0]], 1) == [0, -1]
    assert R._bipartite_match([[0], [0, 1]], 2) == [0, 1]


# ------------------------------------------------------------ filter controls


def test_filter_controls_require_each_label_with_its_options():
    anchor = anchor_of()
    removed = dashboard_snapshot()
    removed["controls"] = [entry for entry in removed["controls"] if entry["label"] != "Region"]

    result = check(
        R.evaluate_page(removed, loads=True, anchor=anchor),
        "filter_controls_available",
    )
    assert result["passed"] is False
    assert result["missing_labels"] == ["Region"]


def test_wiped_or_reduced_option_list_fails():
    anchor = anchor_of()

    wiped = dashboard_snapshot()
    control(wiped, "Region")["options"] = []
    result = check(
        R.evaluate_page(wiped, loads=True, anchor=anchor), "filter_controls_available"
    )
    assert result["passed"] is False
    assert result["missing_labels"] == ["Region"]

    reduced = dashboard_snapshot()
    control(reduced, "Region")["options"].remove("eu-west-1")
    result = check(
        R.evaluate_page(reduced, loads=True, anchor=anchor), "filter_controls_available"
    )
    assert result["passed"] is False
    assert result["missing_labels"] == ["Region"]


def test_placeholder_option_may_be_renamed():
    anchor = anchor_of()
    renamed = dashboard_snapshot()
    control(renamed, "Region")["options"][0] = "Any region"

    page = R.evaluate_page(renamed, loads=True, anchor=anchor)
    assert check(page, "filter_controls_available")["passed"] is True


def test_one_merged_control_cannot_cover_three_labels():
    anchor = anchor_of()
    merged = dashboard_snapshot()
    region = control(merged, "Region")
    region["options"] += control(merged, "Service")["options"]
    region["options"] += control(merged, "Severity")["options"]
    merged["controls"] = [
        entry for entry in merged["controls"] if entry["label"] not in ("Service", "Severity")
    ]

    result = check(
        R.evaluate_page(merged, loads=True, anchor=anchor),
        "filter_controls_available",
    )
    assert result["passed"] is False
    assert result["missing_labels"] == ["Service", "Severity"]


def test_controls_are_identified_by_their_exposed_options_not_their_label():
    anchor = anchor_of()

    # Options alone identify the Region control even if the label is gone.
    unlabelled = dashboard_snapshot()
    control(unlabelled, "Region")["label"] = ""
    page = R.evaluate_page(unlabelled, loads=True, anchor=anchor)
    assert check(page, "filter_controls_available")["passed"] is True

    # A custom combobox whose open popup exposed its choices is graded like a
    # native select (see the render-level popup probe tests).
    opened = dashboard_snapshot()
    control(opened, "Region")["tag"] = "div"
    page = R.evaluate_page(opened, loads=True, anchor=anchor)
    assert check(page, "filter_controls_available")["passed"] is True

    # A labelled custom combobox that exposes no choices does not count: the
    # runner opens the popup, and an inert one has nothing to offer.
    silent = dashboard_snapshot()
    control(silent, "Region").update(tag="div", options=[])
    result = check(
        R.evaluate_page(silent, loads=True, anchor=anchor), "filter_controls_available"
    )
    assert result["passed"] is False
    assert result["missing_labels"] == ["Region"]

    labelled_but_empty = dashboard_snapshot()
    control(labelled_but_empty, "Region")["options"] = []
    result = R.filter_controls_check(labelled_but_empty, anchor["controls"])
    assert result["passed"] is False
    assert result["missing_labels"] == ["Region"]


def test_probe_clicks_a_custom_combobox_and_reads_the_open_popup(monkeypatch):
    snapshot = dashboard_snapshot()
    control(snapshot, "Region").update(tag="div", options=[])
    exposed = list(FILTER_OPTIONS["Region"])
    playwright = install_fake_playwright(monkeypatch, [0, [], exposed])
    page = playwright.chromium.launch(headless=True, args=[]).new_context().page

    R.probe_custom_controls(page, snapshot)

    assert [click["selector"] for click in page.clicks] == ['[data-eval-control="1"]']
    assert [click["timeout"] for click in page.clicks] == [R.INTERACTION_TIMEOUT_MS]
    assert page.keys == ["Escape"]
    assert control(snapshot, "Region")["options"] == exposed
    assert check(
        R.evaluate_page(snapshot, loads=True, anchor=anchor_of()),
        "filter_controls_available",
    )["passed"] is True


def test_probe_treats_a_failed_click_as_no_exposed_choices(monkeypatch):
    # Playwright's actionability covers hit-testing, so a covered, inert or
    # pointer-events:none combobox raises instead of being opened by an untrusted
    # dispatched event.
    snapshot = dashboard_snapshot()
    control(snapshot, "Region").update(tag="div", options=[])
    playwright = install_fake_playwright(
        monkeypatch, [0, []], click_error=RuntimeError("element is covered")
    )
    page = playwright.chromium.launch(headless=True, args=[]).new_context().page

    R.probe_custom_controls(page, snapshot)

    assert control(snapshot, "Region")["options"] == []
    result = check(
        R.evaluate_page(snapshot, loads=True, anchor=anchor_of()),
        "filter_controls_available",
    )
    assert result["passed"] is False
    assert result["missing_labels"] == ["Region"]


def test_probe_skips_native_selects_and_hidden_controls(monkeypatch):
    playwright = install_fake_playwright(monkeypatch)
    page = playwright.chromium.launch(headless=True, args=[]).new_context().page

    R.probe_custom_controls(page, dashboard_snapshot())
    assert page.scripts == []
    assert page.clicks == []

    hidden_custom = dashboard_snapshot()
    control(hidden_custom, "Region").update(tag="div", visible=False, options=[])
    R.probe_custom_controls(page, hidden_custom)
    assert page.clicks == []


def test_daily_controls_cannot_replace_the_filters():
    anchor = anchor_of()
    swapped = dashboard_snapshot()
    for entry in swapped["controls"]:
        if entry["label"] in R.FILTER_LABELS:
            entry["options"] = ["Last 24 hours", "Last 7 days"]

    result = check(
        R.evaluate_page(swapped, loads=True, anchor=anchor),
        "filter_controls_available",
    )
    assert result["passed"] is False
    assert result["missing_labels"] == ["Region", "Service", "Severity"]


def test_hidden_or_disabled_controls_do_not_count():
    anchor = anchor_of()
    for mutation in ({"visible": False}, {"enabled": False}):
        snapshot = dashboard_snapshot()
        control(snapshot, "Region").update(mutation)
        result = check(
            R.evaluate_page(snapshot, loads=True, anchor=anchor),
            "filter_controls_available",
        )
        assert result["passed"] is False, mutation
        assert result["missing_labels"] == ["Region"]


def test_baseline_anchor_needs_the_three_labelled_controls():
    snapshot = dashboard_snapshot()
    snapshot["controls"] = [
        entry for entry in snapshot["controls"] if entry["label"] != "Severity"
    ]
    result = R.filter_controls_check(snapshot, None)

    assert result["passed"] is False
    assert result["missing_labels"] == ["Severity"]


# ---------------------------------------------------------------- filter labels


def test_filter_labels_ignore_table_headers():
    snapshot = dashboard_snapshot()
    snapshot["containers"] = [
        entry for entry in snapshot["containers"] if entry["text"] != "Region"
    ]
    snapshot["containers"].append({"tag": "th", "text": "REGION", "inHeader": True})

    result = R.filter_labels_check(snapshot)
    assert result["passed"] is False
    assert result["missing_labels"] == ["Region"]


def test_filter_labels_allow_a_wrapping_label_and_a_colon():
    snapshot = dashboard_snapshot()
    snapshot["containers"] = [
        {"tag": "label", "text": "Region All regions"}
        if entry["text"] == "Region"
        else entry
        for entry in snapshot["containers"]
    ]
    assert R.filter_labels_check(snapshot)["passed"] is True

    colon = dashboard_snapshot()
    colon["containers"] = [
        {"tag": "label", "text": "Severity:"}
        if entry["text"] == "Severity"
        else entry
        for entry in colon["containers"]
    ]
    assert R.filter_labels_check(colon)["passed"] is True


# --------------------------------------------------------------- primary action


def test_primary_action_needs_to_be_visible_enabled_and_named():
    snapshot = dashboard_snapshot()
    assert R.primary_action_check(snapshot)["passed"] is True

    for mutation in (
        {"enabled": False},
        {"visible": False},
        {"text": "Create incident"},
    ):
        changed = dashboard_snapshot()
        changed["actions"][0].update(mutation)
        assert R.primary_action_check(changed)["passed"] is False, mutation

    decorated = dashboard_snapshot()
    decorated["actions"][0]["text"] = "＋ NEW INCIDENT"
    assert R.primary_action_check(decorated)["passed"] is True


def test_action_name_matching_is_word_exact():
    assert R.action_name_matches("New incident") is True
    assert R.action_name_matches("new INCIDENT") is True
    assert R.action_name_matches("＋ New incident") is True
    assert R.action_name_matches("New incident 3") is False
    assert R.action_name_matches("Create new incident") is False
    assert R.action_name_matches("New incidents") is False


# --------------------------------------------------------------------- reports


def test_missing_candidate_is_a_scored_failure_not_an_input_error():
    section = R.unavailable_candidate("cannot read /input/candidate.html: missing")

    assert section["rendered"] is False
    assert section["passed"] is False
    assert section["checks"][0]["name"] == "candidate_available"

    report = R.build_gate_report(
        baseline=R.evaluate_page(dashboard_snapshot(), loads=True),
        candidate=section,
        inputs={
            "baseline": {"path": "/input/baseline.html", "bytes": 1, "sha256": "a"},
            "candidate": {"path": "/input/candidate.html", "error": "missing"},
        },
        screenshots={"baseline": {"file": "baseline.png", "bytes": 10}, "candidate": None},
    )
    assert report["passed"] is False
    assert report["failed_checks"] == ["candidate_available"]


def test_unrenderable_candidate_records_the_load_failure():
    section = R.unrendered_candidate("Timeout 30000ms exceeded", page_errors=["boom"])

    assert section["rendered"] is False
    assert section["passed"] is False
    assert section["checks"][0]["name"] == "page_loads"
    assert section["checks"][0]["page_error_count"] == 1


def test_report_is_json_with_a_top_level_passed_boolean():
    baseline = R.evaluate_page(dashboard_snapshot(), loads=True)
    candidate = R.evaluate_page(
        dashboard_snapshot(), loads=True, anchor=anchor_of()
    )
    report = R.build_gate_report(
        baseline=baseline,
        candidate=candidate,
        inputs={"baseline": {}, "candidate": {}},
        screenshots={
            "baseline": {"file": "baseline.png", "bytes": 10},
            "candidate": {"file": "final.png", "bytes": 10},
        },
    )

    assert report["passed"] is True
    assert report["schema_version"] == 2
    assert report["viewport"] == {
        "width": 1440,
        "height": 1100,
        "device_scale_factor": 1,
        "locale": "en-US",
        "timezone_id": "UTC",
    }
    assert json.loads(json.dumps(report)) == report

    failed = R.evaluate_page(blank_snapshot(), loads=True, anchor=anchor_of())
    assert failed["passed"] is False
    assert "body_visible" in [entry["name"] for entry in failed["checks"]]


def test_lost_record_is_named_in_the_gate_report():
    anchor = anchor_of()
    rows = [list(row) for row in EVENT_RECORDS]
    del rows[0]

    report = R.build_gate_report(
        baseline=R.evaluate_page(dashboard_snapshot(), loads=True),
        candidate=R.evaluate_page(with_records(rows), loads=True, anchor=anchor),
        inputs={"baseline": {}, "candidate": {}},
        screenshots={
            "baseline": {"file": "baseline.png", "bytes": 10},
            "candidate": {"file": "final.png", "bytes": 10},
        },
    )
    assert report["passed"] is False
    assert report["failed_checks"] == ["event_records_preserved"]
    detail = next(
        entry for entry in report["candidate"]["checks"]
        if entry["name"] == "event_records_preserved"
    )
    assert "14:32" in detail["detail"]


# ------------------------------------------------------------------------- CLI


def test_cli_accepts_the_exact_integration_command():
    args = R.build_parser().parse_args(
        [
            "--baseline",
            "/input/baseline.html",
            "--candidate",
            "/input/candidate.html",
            "--output-dir",
            "/output",
        ]
    )

    assert args.baseline == Path("/input/baseline.html")
    assert args.candidate == Path("/input/candidate.html")
    assert args.output_dir == Path("/output")


def test_missing_baseline_exits_nonzero_without_touching_the_browser(tmp_path):
    code = R.main(
        [
            "--baseline",
            str(tmp_path / "missing.html"),
            "--candidate",
            str(tmp_path / "candidate.html"),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert code == R.EXIT_USAGE
    assert not (tmp_path / "out").exists()


def test_read_html_hashes_the_exact_bytes(tmp_path):
    path = tmp_path / "baseline.html"
    path.write_text("<p>café</p>", encoding="utf-8")

    html, meta = R.read_html(path)

    assert html == "<p>café</p>"
    assert meta["bytes"] == len(html.encode("utf-8"))
    assert meta["sha256"] == hashlib.sha256(html.encode("utf-8")).hexdigest()

    with pytest.raises(R.InputError):
        R.read_html(tmp_path / "absent.html")


def test_checker_image_pins_the_runner_where_the_harness_calls_it():
    source = (REPO_ROOT / "evals/browser/Dockerfile").read_text(encoding="utf-8")

    assert "mcr.microsoft.com/playwright/python:v1.58.0-noble" in source
    assert "COPY --chown=pwuser:pwuser browser_runner.py /opt/ui-eval/browser_runner.py" in source
    assert "USER pwuser" in source
    # The verifier transfers HTML through these mount points.
    assert re.search(r"(mkdir -p|install -d)[^\n]*/input[^\n]*/output", source)


# ------------------------------------------------------------------- wiring


def install_fake_playwright(monkeypatch, snapshots=None, *, click_error=None):
    """A stand-in for Playwright's sync API, so wiring tests need no browser.

    ``snapshots`` replays one value per ``evaluate`` call, so a test can hand the
    harness a saved snapshot and popup choices without touching a browser.
    ``click_error`` makes every locator click raise, which is how a covered or
    non-interactable control fails Playwright's actionability checks.
    """
    import types

    module = types.ModuleType("playwright.sync_api")
    replay = list(snapshots) if snapshots is not None else []

    class FakeLocator:
        def __init__(self, page, selector):
            self.page = page
            self.selector = selector

        def click(self, *, timeout):
            self.page.clicks.append({"selector": self.selector, "timeout": timeout})
            if click_error is not None:
                raise click_error

    class FakeKeyboard:
        def __init__(self, page):
            self.page = page

        def press(self, key):
            self.page.keys.append(key)

    class FakePage:
        def __init__(self):
            self.screenshots = []
            self.scripts = []
            self.clicks = []
            self.keys = []
            self.timeout = None

        def set_default_timeout(self, milliseconds):
            self.timeout = milliseconds

        def on(self, event, handler):
            self.event = event

        def set_content(self, html, wait_until):
            self.content = html
            self.wait_until = wait_until

        def evaluate(self, script, arg=None):
            self.scripts.append(script)
            return replay.pop(0) if replay else dashboard_snapshot()

        def locator(self, selector):
            return FakeLocator(self, selector)

        @property
        def keyboard(self):
            return FakeKeyboard(self)

        def screenshot(self, *, path, full_page, animations):
            Path(path).write_bytes(b"fake-png")
            self.screenshots.append(
                {"path": Path(path), "full_page": full_page, "animations": animations}
            )

    class FakeContext:
        def __init__(self):
            self.page = FakePage()

        def new_page(self):
            return self.page

        def close(self):
            pass

    class FakeBrowser:
        def __init__(self):
            self.context_options = []
            self.contexts = []

        def new_context(self, **options):
            self.context_options.append(options)
            context = FakeContext()
            self.contexts.append(context)
            return context

        def close(self):
            self.closed = True

    class FakeChromium:
        def __init__(self):
            self.browser = None
            self.args = None

        def launch(self, *, headless, args):
            self.headless = headless
            self.args = list(args)
            self.browser = FakeBrowser()
            return self.browser

    class FakePlaywright:
        def __init__(self):
            self.chromium = FakeChromium()

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    playwright = FakePlaywright()
    module.sync_playwright = lambda: playwright
    module.Error = RuntimeError
    monkeypatch.setitem(sys.modules, "playwright", types.ModuleType("playwright"))
    monkeypatch.setitem(sys.modules, "playwright.sync_api", module)
    return playwright


def test_render_context_is_fixed_offline_and_full_page(tmp_path, monkeypatch):
    playwright = install_fake_playwright(monkeypatch)
    report = R.run_gate(
        baseline_html="<html><body>baseline</body></html>",
        baseline_meta={"path": "/input/baseline.html"},
        candidate_html="<html><body>candidate</body></html>",
        candidate_meta={"path": "/input/candidate.html"},
        output_dir=tmp_path,
    )

    browser = playwright.chromium.browser
    assert browser.context_options[0] == {
        "viewport": {"width": 1440, "height": 1100},
        "device_scale_factor": 1,
        "locale": "en-US",
        "timezone_id": "UTC",
        "offline": True,
        "reduced_motion": "reduce",
    }
    for context in browser.contexts:
        assert context.page.timeout == R.OPERATION_TIMEOUT_MS
        assert context.page.screenshots[0]["full_page"] is True
        assert context.page.screenshots[0]["animations"] == "disabled"
    assert playwright.chromium.args[0] == "--no-sandbox"

    assert report["passed"] is True
    assert report["candidate"]["rendered"] is True
    assert (tmp_path / "baseline.png").exists()
    assert (tmp_path / "final.png").exists()
    assert json.loads((tmp_path / "gate.json").read_text(encoding="utf-8")) == report
    # The report records the baseline-derived data the candidate was graded
    # against, so a gate result can be audited without re-rendering.
    assert report["baseline_contract"]["event_records"][0][0] == "14:32"
    assert report["baseline_contract"]["filter_options"]["Region"] == [
        "All regions", "us-east-1", "eu-west-1"
    ]


def test_render_document_probes_a_custom_combobox_before_grading(tmp_path, monkeypatch):
    custom = dashboard_snapshot()
    control(custom, "Region").update(tag="div", options=[])
    exposed = list(FILTER_OPTIONS["Region"])
    # Extraction, control tagging, the pre-click read, then the open-popup read.
    playwright = install_fake_playwright(monkeypatch, [custom, 0, [], exposed])
    browser = playwright.chromium.launch(headless=True, args=[])

    rendered = R.render_document(
        browser,
        "<!doctype html><body></body>",
        screenshot_path=tmp_path / "candidate.png",
    )

    page = browser.contexts[0].page
    assert [click["selector"] for click in page.clicks] == ['[data-eval-control="1"]']
    assert page.keys == ["Escape"]
    snapshot = rendered["snapshot"]
    assert control(snapshot, "Region")["options"] == exposed
    gate = R.evaluate_page(snapshot, loads=True, anchor=anchor_of())
    assert check(gate, "filter_controls_available")["passed"] is True


def test_render_document_skips_the_probe_without_custom_controls(tmp_path, monkeypatch):
    playwright = install_fake_playwright(monkeypatch)
    browser = playwright.chromium.launch(headless=True, args=[])

    R.render_document(
        browser,
        "<!doctype html><body></body>",
        screenshot_path=tmp_path / "candidate.png",
    )

    assert len(browser.contexts[0].page.scripts) == 1


def test_cli_harness_replays_baseline_and_candidate_snapshots(tmp_path, monkeypatch):
    """End-to-end CLI wiring without a browser: baseline snapshot, candidate snapshot."""
    baseline = tmp_path / "baseline.html"
    baseline.write_text("<!doctype html><p>baseline</p>", encoding="utf-8")
    candidate = tmp_path / "candidate.html"
    candidate.write_text("<!doctype html><p>candidate</p>", encoding="utf-8")

    # 1. An unchanged candidate passes, and the contract is recorded.
    install_fake_playwright(monkeypatch, [dashboard_snapshot(), dashboard_snapshot()])
    output_dir = tmp_path / "out-identity"
    code = R.main([
        "--baseline", str(baseline),
        "--candidate", str(candidate),
        "--output-dir", str(output_dir),
    ])
    gate = json.loads((output_dir / "gate.json").read_text(encoding="utf-8"))
    assert code == R.EXIT_OK
    assert gate["passed"] is True
    assert gate["baseline_contract"]["event_records"][0][0] == "14:32"
    assert (output_dir / "final.png").exists()

    # 2. A candidate that lost one event record fails on exactly that check.
    rows = [list(row) for row in EVENT_RECORDS]
    del rows[2]
    install_fake_playwright(monkeypatch, [dashboard_snapshot(), with_records(rows)])
    lost_dir = tmp_path / "out-lost"
    code = R.main([
        "--baseline", str(baseline),
        "--candidate", str(candidate),
        "--output-dir", str(lost_dir),
    ])
    gate = json.loads((lost_dir / "gate.json").read_text(encoding="utf-8"))
    detail = next(
        entry for entry in gate["candidate"]["checks"]
        if entry["name"] == "event_records_preserved"
    )
    assert code == R.EXIT_OK
    assert gate["passed"] is False
    assert gate["failed_checks"] == ["event_records_preserved"]
    assert "14:11" in detail["detail"]
    assert (lost_dir / "final.png").exists()

    # 3. A candidate whose Region control lost its options fails on the control check.
    wiped = dashboard_snapshot()
    control(wiped, "Region")["options"] = []
    install_fake_playwright(monkeypatch, [dashboard_snapshot(), wiped])
    wiped_dir = tmp_path / "out-wiped"
    code = R.main([
        "--baseline", str(baseline),
        "--candidate", str(candidate),
        "--output-dir", str(wiped_dir),
    ])
    gate = json.loads((wiped_dir / "gate.json").read_text(encoding="utf-8"))
    assert code == R.EXIT_OK
    assert gate["passed"] is False
    assert gate["failed_checks"] == ["filter_controls_available"]


def test_extraction_script_guards_label_association_and_visibility():
    """A static contract guard for the in-page extraction the gate depends on.

    The associations themselves are exercised against real Chromium outside the
    unit suite; this keeps a refactor from silently dropping a strategy.
    """
    script = R.EXTRACT_SNAPSHOT_JS

    for strategy in (
        "'aria-label'",
        "'aria-labelledby'",
        "label[for]",
        "closest('label')",
        "previousElementSibling",
    ):
        assert strategy in script, f"label association strategy missing: {strategy}"
    # Hidden rows, hidden cells and hidden text must be filtered before they
    # become records or container text.
    assert "if (!isVisible(row)) continue;" in script
    assert "if (!isVisible(cell)) continue;" in script
    assert "records.push(cells)" in script
    assert "renderedText(el)" in script
    assert "renderedText(cell)" in script
    # Options come from native options and ARIA option children.
    assert 'option, [role="option"]' in script


def test_visibility_and_popup_probe_share_the_rendered_predicate():
    # The ancestor-opacity walk and the popup probe cannot drift apart: both
    # embed the same snippet, whose ancestor chain multiplication makes a
    # descendant of `opacity: 0` invisible even when its own opacity is 1.
    assert R.VISIBILITY_JS in R.EXTRACT_SNAPSHOT_JS
    assert R.VISIBILITY_JS in R.READ_EXPOSED_OPTIONS_JS
    for fragment in ("parentElement", "effectiveOpacity", "getComputedStyle"):
        assert fragment in R.VISIBILITY_JS, fragment

    # The probe reads only the popup linked to the clicked control; it never
    # scans the page for any visible popup.
    assert "data-eval-control" in R.TAG_CONTROLS_JS
    for fragment in (
        "aria-controls",
        "aria-owns",
        "closest('[inert]')",
        "pointerEvents",
        'role="option"',
        "nextElementSibling",
    ):
        assert fragment in R.READ_EXPOSED_OPTIONS_JS, fragment
    assert "document.querySelectorAll" not in R.READ_EXPOSED_OPTIONS_JS


def test_filter_options_tolerate_label_case_and_colon():
    snapshot = dashboard_snapshot()
    control(snapshot, "Region")["label"] = "  REGION:  "
    specs = R.filter_options(snapshot)

    assert specs["Region"] == ("All regions", "us-east-1", "eu-west-1")


def test_missing_candidate_output_is_a_scored_failure(tmp_path, monkeypatch):
    install_fake_playwright(monkeypatch)
    baseline = tmp_path / "baseline.html"
    baseline.write_text("<!doctype html><p>baseline</p>", encoding="utf-8")
    output_dir = tmp_path / "out"

    code = R.main(
        [
            "--baseline",
            str(baseline),
            "--candidate",
            str(tmp_path / "candidate.html"),
            "--output-dir",
            str(output_dir),
        ]
    )

    gate = json.loads((output_dir / "gate.json").read_text(encoding="utf-8"))
    assert code == R.EXIT_OK
    assert gate["passed"] is False
    assert gate["candidate"]["rendered"] is False
    assert gate["screenshots"]["candidate"] is None
    assert gate["inputs"]["candidate"]["error"].startswith("cannot read")
    assert (output_dir / "baseline.png").exists()
    assert not (output_dir / "final.png").exists()


# --------------------------------------------------------- real browser checks
# The visibility predicate, the rendered-text rebuild and the popup probe run
# inside the page, so their regressions execute the real extraction in a
# headless Chromium when one is installed. Still offline: no network, no Podman
# and no model call. These tests skip when no Chromium binary exists.


CHROMIUM = next(
    (
        found
        for name in ("chromium", "chromium-browser", "google-chrome")
        if (found := shutil.which(name)) is not None
    ),
    None,
)
requires_chromium = pytest.mark.skipif(
    CHROMIUM is None, reason="no Chromium binary to run the in-page extraction"
)

PAGE_STYLE = (
    "body{margin:0;font:14px sans-serif}"
    ".metric{border:1px solid #ccc;padding:8px;margin:4px}"
    "table{border-collapse:collapse}"
    "th,td{border:1px solid #ccc;padding:2px 6px}"
    ".filter{margin:4px}"
)

# The page-side half of the browser regressions: run the production extraction
# and serialise the snapshot into the DOM for `--dump-dom`.
BROWSER_HARNESS = r"""
const report = (payload) => {
  document.getElementById('result').textContent = JSON.stringify(payload);
};
window.addEventListener('load', () => {
  report({snapshot: extract()});
});
"""

# The popup reader needs the same control handles the probe tags, then reports
# the choices it would accept for each requested control.
READ_OPTIONS_HARNESS = r"""
window.addEventListener('load', () => {
  tag();
  const reads = indexes.map((index) => read(index));
  document.getElementById('result').textContent = JSON.stringify(reads);
});
"""


def metric_cards(hidden: Sequence[str] = ()) -> str:
    cards = []
    for label, value in R.METRICS.items():
        card = f'<div class="metric">{label} {value}</div>'
        if label in hidden:
            card = f'<div style="opacity:0"><div style="opacity:1">{card}</div></div>'
        cards.append(card)
    return '<section class="metrics">' + "".join(cards) + "</section>"


def event_table() -> str:
    header = "".join(
        f"<th>{name}</th>"
        for name in ("Time", "Severity", "Service", "Region", "Event", "Owner", "Status")
    )
    rows = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in EVENT_RECORDS
    )
    return f"<table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"


def native_filters(hidden: Sequence[str] = ()) -> str:
    blocks = []
    for label, options in FILTER_OPTIONS.items():
        select = (
            "<select>"
            + "".join(f"<option>{option}</option>" for option in options)
            + "</select>"
        )
        block = f"<label>{label}</label>{select}"
        if label in hidden:
            block = f'<div style="opacity:0"><div style="opacity:1">{block}</div></div>'
        blocks.append(f'<div class="filter">{block}</div>')
    return '<section class="filters">' + "".join(blocks) + "</section>"


def dashboard_document(
    *,
    hidden_metrics: Sequence[str] = (),
    hidden_filters: Sequence[str] = (),
    hide_action: bool = False,
) -> str:
    """A minimal dashboard carrying the fixture's data contract."""
    action = '<button class="btn">New incident</button>'
    if hide_action:
        action = f'<div style="opacity:0"><div style="opacity:1">{action}</div></div>'
    body = (
        metric_cards(hidden_metrics)
        + event_table()
        + native_filters(hidden_filters)
        + f'<div class="actions">{action}</div>'
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<style>{PAGE_STYLE}</style></head><body>{body}</body></html>"
    )


def with_runner(document: str, runner: str) -> str:
    """Append an in-page runner and its result placeholder to a document."""
    assert "</body>" in document
    return document.replace(
        "</body>",
        "<script>\n" + runner + '</script><pre id="result"></pre></body>',
        1,
    )


def chromium_report(work_dir: Path, document: str) -> dict:
    """Load a document in headless Chromium and return the JSON it reported."""
    work_dir.mkdir(parents=True, exist_ok=True)
    page = work_dir / "page.html"
    page.write_text(document, encoding="utf-8")
    process = subprocess.run(
        [
            CHROMIUM,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--disable-dev-shm-usage",
            f"--user-data-dir={work_dir / 'profile'}",
            f"--window-size={R.VIEWPORT_WIDTH},{R.VIEWPORT_HEIGHT}",
            "--virtual-time-budget=5000",
            "--dump-dom",
            page.as_uri(),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    match = re.search(r'<pre id="result">(.*?)</pre>', process.stdout, re.S)
    assert match is not None, process.stderr[-2000:]
    return json.loads(html.unescape(match.group(1)))


def browser_snapshot(work_dir: Path, document: str) -> dict:
    """Extract a page in headless Chromium, so the in-page predicate runs for real."""
    runner = "const extract = " + R.EXTRACT_SNAPSHOT_JS + ";\n" + BROWSER_HARNESS
    return chromium_report(work_dir, with_runner(document, runner))["snapshot"]


def exposed_choices(
    work_dir: Path, document: str, indexes: Sequence[int]
) -> list[list[str]]:
    """Run the popup reader for the given control indexes in a real browser."""
    runner = (
        "const tag = " + R.TAG_CONTROLS_JS + ";\n"
        + "const read = " + R.READ_EXPOSED_OPTIONS_JS + ";\n"
        + "const indexes = " + json.dumps(list(indexes)) + ";\n"
        + READ_OPTIONS_HARNESS
    )
    return chromium_report(work_dir, with_runner(document, runner))


@pytest.fixture(scope="module")
def baseline_snapshot(tmp_path_factory) -> dict:
    """The fixed fixture, rendered and extracted once in a real browser."""
    work_dir = tmp_path_factory.mktemp("fixture-render")
    return browser_snapshot(work_dir, FIXTURE.read_text(encoding="utf-8"))


@requires_chromium
def test_browser_extraction_of_the_fixture_passes_the_gate(baseline_snapshot):
    page = R.evaluate_page(
        baseline_snapshot, loads=baseline_snapshot["readyState"] == "complete"
    )

    assert page["passed"] is True, page["checks"]
    # The saved literals describe what the real extraction sees.
    assert [
        (control["tag"], control["label"], control["options"])
        for control in baseline_snapshot["controls"]
    ] == [(entry["tag"], entry["label"], entry["options"]) for entry in CONTROLS]
    assert R.table_records(baseline_snapshot) == [
        R.normalize_record(row) for row in EVENT_RECORDS
    ]


@requires_chromium
def test_visible_dashboard_document_passes_the_browser_gate(
    tmp_path, baseline_snapshot
):
    anchor = R.derive_anchor(baseline_snapshot)
    snapshot = browser_snapshot(tmp_path, dashboard_document())

    page = R.evaluate_page(snapshot, loads=True, anchor=anchor)
    assert page["passed"] is True, page["checks"]


@requires_chromium
def test_hidden_ancestor_opacity_fails_the_content_gates(tmp_path, baseline_snapshot):
    anchor = R.derive_anchor(baseline_snapshot)
    document = dashboard_document(
        hidden_metrics=("Requests / sec",),
        hidden_filters=("Region",),
        hide_action=True,
    )

    snapshot = browser_snapshot(tmp_path, document)
    # The faded subtree never enters the snapshot as rendered text ...
    assert not any(
        "requests / sec" in entry["text"].casefold()
        for entry in snapshot["containers"]
    )
    # ... so every gate that depends on the hidden data fails.
    page = R.evaluate_page(snapshot, loads=True, anchor=anchor)
    assert page["passed"] is False
    assert [entry["name"] for entry in page["checks"] if not entry["passed"]] == [
        "metrics_preserved",
        "filter_labels_visible",
        "filter_controls_available",
        "primary_action_enabled",
    ]
    assert check(page, "metrics_preserved")["missing_labels"] == ["Requests / sec"]
    assert check(page, "filter_labels_visible")["missing_labels"] == ["Region"]


@requires_chromium
def test_popup_reader_accepts_only_linked_selectable_choices(tmp_path):
    def options(items: Sequence[str]) -> str:
        return "".join(f'<li role="option">{item}</li>' for item in items)

    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<style>{PAGE_STYLE}</style></head><body>"
        '<section class="filters">'
        # Region: linked popup exposing the baseline choices.
        '<div class="filter"><span>Region</span>'
        '<button role="combobox" aria-label="Region" aria-controls="region-popup">All regions</button>'
        f'<ul id="region-popup" role="listbox">{options(FILTER_OPTIONS["Region"])}</ul></div>'
        # Service: no popup at all, only its label.
        '<div class="filter"><span>Service</span>'
        '<button role="combobox" aria-label="Service">All services</button></div>'
        # Severity: linked popup that cannot receive pointer events.
        '<div class="filter"><span>Severity</span>'
        '<button role="combobox" aria-label="Severity" aria-controls="severity-popup">All severities</button>'
        f'<ul id="severity-popup" role="listbox" style="pointer-events:none">'
        f'{options(FILTER_OPTIONS["Severity"])}</ul></div>'
        # Owner: linked popup inside an inert subtree.
        '<div class="filter"><span>Owner</span>'
        '<button role="combobox" aria-label="Owner" aria-controls="owner-popup">All owners</button>'
        f'<ul id="owner-popup" role="listbox" inert>'
        f'{options(("All owners", "M. Chen"))}</ul></div>'
        # An unrelated visible popup must never become a filter's choice set.
        f'<ul id="unrelated" role="listbox">{options(("Decoy option",))}</ul>'
        "</section></body></html>"
    )

    # Controls in document order: Region, its popup, Service, Severity, its popup,
    # Owner, its popup, the unrelated listbox.
    assert exposed_choices(tmp_path, document, [0, 2, 3, 5]) == [
        list(FILTER_OPTIONS["Region"]),
        [],
        [],
        [],
    ]
