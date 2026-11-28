"""Trusted browser runner for the refactor-ui case-6 visual evaluation.

The eval harness gives a model the dense operations dashboard fixture and asks
for a density-aware cleanup. This runner renders the pre-edit baseline and the
model's candidate in an isolated headless Chromium, saves both screenshots, and
applies a hard gate to the candidate: the document must render, and the twelve
metrics, every baseline event record, the three labelled filter controls (with
their original options) and the ``New incident`` action must still be there.
Aesthetics are not graded here; the pairwise human preference is a separate
step.

The content gate is data preservation, not shape counting. The baseline render
is the data contract: the runner derives the expected event records (normalized
rendered cell text, order-insensitive across rows and columns) and the expected
option list of each ``Region``/``Service``/``Severity`` control from the
baseline snapshot, then requires each of them in the candidate. Hidden content
is not rendered data: visibility multiplies the ancestor opacity chain, so a
subtree under ``opacity: 0`` never satisfies a record, a metric, a filter or the
primary action even when its own computed opacity is 1. Custom comboboxes are
opened after the screenshot with a real, hit-tested click and graded on the
choices their linked popup exposes as visible, pointer-reachable and enabled
options; the label alone is not evidence.

CLI (exactly as the eval service calls it):

    python /opt/ui-eval/browser_runner.py \
        --baseline /input/baseline.html \
        --candidate /input/candidate.html \
        --output-dir /output

Writes ``baseline.png``, ``final.png`` and ``gate.json`` into the output
directory. ``final.png`` and the candidate checks only exist once the candidate
document rendered; a missing or unrenderable candidate is a *scored* failure,
not an infrastructure error:

* ``gate.json`` always has a top-level boolean ``passed``.
* ``0`` — the baseline rendered, ``gate.json`` (and ``baseline.png``) were
  written, and the candidate gate was evaluated. The gate may itself fail.
* ``2`` — the command line or the trusted baseline is unusable.
* ``3`` — the browser or verifier infrastructure failed, so no trustworthy
  candidate verdict exists. This includes a baseline that no longer satisfies
  the hard gate: the verdict would then be graded against the wrong anchor.

Only the two HTML documents are read. Rendering is offline: the HTML is
installed into the page with ``page.set_content`` instead of being fetched over
a URL, and the browser context is created with ``offline=True``.

The gate is a retention check, not an aesthetic one: it never inspects layout,
color, spacing or component choice, and its selectors walk rendered text and
semantic roles rather than CSS classes, so a CSS or layout rewrite does not
break it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

# Rendering contract: one fixed browser and desktop viewport, so the baseline
# and the candidate are captured under identical conditions.
VIEWPORT_WIDTH = 1440
VIEWPORT_HEIGHT = 1100
VIEWPORT = {"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
DEVICE_SCALE_FACTOR = 1
LOCALE = "en-US"
TIMEZONE_ID = "UTC"

# The fixed dense-dashboard fixture behind case 6. These name/value pairs are
# the data the case calls load-bearing; a revision may regroup or restyle them,
# but must not drop or reword them. Text is compared case-folded and with
# collapsed whitespace, because the fixture uppercases labels via CSS.
METRICS: Mapping[str, str] = {
    "Requests / sec": "12.4k",
    "Error rate": "0.84%",
    "P95 latency": "284 ms",
    "Saturation": "71%",
    "Uptime": "99.982%",
    "Queue depth": "1,842",
    "Active incidents": "3",
    "Deploys today": "18",
    "Cache hit rate": "93.1%",
    "DB connections": "412 / 500",
    "CPU": "64%",
    "Memory": "78%",
}

# The baseline anchor must keep exposing the fixture's ten event records (the
# panel says "10 of 2,418"); the candidate is graded on preserving them, not on
# a row count.
EVENT_TABLE_MIN_ROWS = 10
FILTER_LABELS = ("Region", "Service", "Severity")
MIN_FILTER_OPTIONS = 2  # a working filter control needs a real choice set
PRIMARY_ACTION = "New incident"

# Longest element text treated as a single control (a metric card, a filter
# label). The fixture's whole metrics grid renders as ~307 characters, so a cap
# above that would let one aggregate element pair every name with every value;
# 160 characters still holds a full card with its delta.
MAX_CONTAINER_TEXT = 160

OPERATION_TIMEOUT_MS = 30_000

# The service container is the isolation boundary: no network, no host mounts,
# an immutable image holding this runner. Inspect starts it as root, where
# Chromium's setuid sandbox is unavailable, and containers get a small /dev/shm.
BROWSER_ARGS = (
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--hide-scrollbars",
    "--force-color-profile=srgb",
)

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INFRA = 3


class RunnerError(RuntimeError):
    """The browser could not produce a trustworthy verdict."""


class InputError(ValueError):
    """An input document could not be read as UTF-8 HTML."""


# Effective visibility for the in-page extraction. Opacity is not inherited, so
# a descendant of an `opacity: 0` ancestor keeps its own computed opacity (often
# 1) and a non-zero box: the ancestor chain has to be multiplied before a subtree
# counts as rendered. `visibility` is inherited by the browser and `display: none`
# collapses the descendants' boxes, so only opacity needs the explicit walk.
# Kept as its own snippet because the popup probe below needs the same predicate.
VISIBILITY_JS = r"""
  const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'HEAD', 'META', 'LINK', 'TITLE']);

  const effectiveOpacity = (el) => {
    let opacity = 1;
    for (let node = el; node; node = node.parentElement) {
      opacity *= parseFloat(getComputedStyle(node).opacity || '1');
      if (opacity === 0) return 0;
    }
    return opacity;
  };

  const isVisible = (el) => {
    if (!el.isConnected || SKIP_TAGS.has(el.tagName)) return false;
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
    if (effectiveOpacity(el) === 0) return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };
"""

# The one in-page snapshot the gate reads. It deliberately walks rendered text
# and semantic roles only, so CSS classes, component structure and layout are
# free to change.
EXTRACT_SNAPSHOT_JS = r"""() => {
  const MAX_CONTAINER_TEXT = __MAX_CONTAINER_TEXT__;
__VISIBILITY_JS__
  const normalize = (value) => value.replace(/\s+/g, ' ').trim();

  // `innerText` still carries the text of a subtree that only an ancestor's
  // opacity hides, so rendered data is rebuilt from the text nodes whose element
  // chain is actually painted. Only the collapsed text matters to the gate, so
  // joining the visible text nodes with spaces is enough.
  const hiddenAncestorCache = new WeakMap();
  const hasHiddenAncestor = (el) => {
    if (hiddenAncestorCache.has(el)) return hiddenAncestorCache.get(el);
    const parent = el.parentElement;
    const hidden = parent !== null &&
      (getComputedStyle(parent).display === 'none' || hasHiddenAncestor(parent));
    hiddenAncestorCache.set(el, hidden);
    return hidden;
  };

  const renderedCache = new WeakMap();
  const isRendered = (el) => {
    if (!renderedCache.has(el)) {
      let rendered = false;
      if (el.isConnected && !SKIP_TAGS.has(el.tagName)) {
        const style = getComputedStyle(el);
        rendered = style.display !== 'none' &&
          style.visibility !== 'hidden' && style.visibility !== 'collapse' &&
          effectiveOpacity(el) !== 0 && !hasHiddenAncestor(el);
      }
      renderedCache.set(el, rendered);
    }
    return renderedCache.get(el);
  };

  const renderedText = (el) => {
    const parts = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const parent = node.parentElement;
      if (!parent || !isRendered(parent)) continue;
      const text = normalize(node.nodeValue || '');
      if (text.length > 0) parts.push(text);
    }
    return normalize(parts.join(' '));
  };

  const containers = [];
  if (document.body) {
    for (const el of document.body.querySelectorAll('*')) {
      if (!isVisible(el)) continue;
      const text = renderedText(el);
      if (text.length === 0 || text.length > MAX_CONTAINER_TEXT) continue;
      containers.push({
        tag: el.tagName.toLowerCase(),
        text,
        inHeader: el.closest('thead') !== null,
      });
    }
  }

  const tables = [];
  for (const el of document.querySelectorAll('table, [role="table"], [role="grid"]')) {
    if (!isVisible(el)) continue;
    let dataRows = 0;
    let headerCells = 0;
    const records = [];
    for (const row of el.querySelectorAll('tr, [role="row"]')) {
      // Only this table's own rows: a nested table is reported separately.
      if (row.closest('table, [role="table"], [role="grid"]') !== el) continue;
      if (!isVisible(row)) continue;  // a hidden row is not rendered data
      const cells = [];
      for (const cell of row.querySelectorAll(
        ':scope > th, :scope > td, :scope > [role="cell"], ' +
        ':scope > [role="columnheader"], :scope > [role="gridcell"]'
      )) {
        if (!isVisible(cell)) continue;  // a hidden cell is not rendered data
        const text = renderedText(cell);
        if (text.length > 0) cells.push(text);
      }
      const header = row.closest('thead') !== null ||
        row.querySelector(':scope > th, :scope > [role="columnheader"]') !== null;
      if (header) {
        headerCells += cells.length;
        continue;
      }
      if (cells.length < 2) continue;
      dataRows += 1;
      records.push(cells);
    }
    tables.push({ tag: el.tagName.toLowerCase(), visible: true, dataRows, headerCells, records });
  }

  // The label a filter control reads as, so a rewritten control can still be
  // recognised by its semantic label. CSS classes are never consulted.
  const labelForControl = (el) => {
    const own = normalize(el.getAttribute('aria-label') || '');
    if (own) return own;
    const labelledby = (el.getAttribute('aria-labelledby') || '').trim();
    if (labelledby) {
      const text = normalize(
        labelledby.split(/\s+/)
          .map(id => document.getElementById(id))
          .filter(Boolean)
          .map(node => normalize(node.innerText || ''))
          .join(' ')
      );
      if (text) return text;
    }
    const wrapping = el.closest('label');
    if (wrapping) {
      const clone = wrapping.cloneNode(true);
      clone.querySelectorAll('select, input, textarea, [role="combobox"], [role="listbox"]')
        .forEach(node => node.remove());
      const text = normalize(clone.textContent || '');
      if (text) return text;
    }
    if (el.id) {
      for (const label of document.querySelectorAll('label[for]')) {
        if (label.getAttribute('for') === el.id) {
          const text = normalize(label.innerText || '');
          if (text) return text;
        }
      }
    }
    let scope = el;
    for (let depth = 0; depth < 3 && scope; depth += 1) {
      let sibling = scope.previousElementSibling;
      for (let hops = 0; sibling && hops < 4; hops += 1) {
        if (sibling.matches('select, input, textarea, button, [role="combobox"], [role="listbox"]')) break;
        const text = normalize(sibling.innerText || '');
        if (text.length > 0 && text.length <= 48) return text;
        sibling = sibling.previousElementSibling;
      }
      scope = scope.parentElement;
    }
    return '';
  };

  const controls = [];
  for (const el of document.querySelectorAll('select, [role="combobox"], [role="listbox"]')) {
    const disabled = el.disabled === true ||
      el.getAttribute('aria-disabled') === 'true' ||
      el.closest('fieldset[disabled]') !== null;
    const options = [];
    for (const option of el.querySelectorAll('option, [role="option"]')) {
      // A disabled choice cannot be selected, so it is not part of the filter's
      // selectable option set.
      if (option.disabled === true || option.getAttribute('aria-disabled') === 'true') continue;
      const text = normalize(option.text || option.innerText || '');
      if (text.length > 0) options.push(text);
    }
    controls.push({
      tag: el.tagName.toLowerCase(),
      visible: isVisible(el),
      enabled: !disabled,
      label: labelForControl(el),
      options,
    });
  }

  const actions = [];
  for (const el of document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]')) {
    const text = normalize(el.innerText || el.value || el.getAttribute('aria-label') || '');
    const disabled = el.disabled === true ||
      el.getAttribute('aria-disabled') === 'true' ||
      el.closest('fieldset[disabled]') !== null;
    actions.push({ tag: el.tagName.toLowerCase(), text, visible: isVisible(el), enabled: !disabled });
  }

  const body = document.body;
  const bodyRect = body ? body.getBoundingClientRect() : null;
  const bodyText = body ? normalize(body.innerText || '') : '';
  return {
    readyState: document.readyState,
    title: document.title,
    body: {
      visible: body !== null && isVisible(body),
      width: bodyRect ? Math.round(bodyRect.width) : 0,
      height: bodyRect ? Math.round(bodyRect.height) : 0,
      textLength: bodyText.length,
    },
    containers,
    tables,
    controls,
    actions,
  };
}""".replace("__MAX_CONTAINER_TEXT__", str(MAX_CONTAINER_TEXT)).replace(
    "__VISIBILITY_JS__", VISIBILITY_JS
)

# Custom comboboxes materialise their choices only while their popup is open, so
# the runner opens each visible, enabled non-native control with a real browser
# click after the screenshot, reads the selectable choices of the popup that is
# linked to that control, and closes the popup again. Hit-testing comes from the
# click itself: a control that is covered, inert or ``pointer-events: none``
# cannot be opened and therefore exposes no choices. Nothing is selected and no
# filtering is exercised: only the filter's choice set is checked.
INTERACTION_TIMEOUT_MS = 1_000

# One stable handle per control, in extraction order, so a popup that the click
# adds to the document cannot shift the controls that follow it.
TAG_CONTROLS_JS = r"""() => {
  const controls = Array.from(document.querySelectorAll(
    'select, [role="combobox"], [role="listbox"]'
  ));
  controls.forEach((el, index) => el.setAttribute('data-eval-control', String(index)));
  return controls.length;
}"""

# Only a popup that is linked to the control counts: an ``aria-controls`` or
# ``aria-owns`` target, the control itself (an always-open listbox), a popup
# nested in the control, or an immediately following sibling. Scanning for any
# visible popup is deliberately not done: an unrelated open listbox elsewhere on
# the page is not this filter's choice set. Options must additionally be
# selectable - visible, not disabled, not inside ``[inert]`` and not
# ``pointer-events: none``.
READ_EXPOSED_OPTIONS_JS = r"""(index) => {
__VISIBILITY_JS__
  const POPUP_SELECTOR = '[role="listbox"], [role="menu"]';
  const normalize = (value) => value.replace(/\s+/g, ' ').trim();
  const isDisabled = (el) => el.disabled === true || el.getAttribute('aria-disabled') === 'true';

  const isSelectable = (el) => {
    if (el.closest('[inert]')) return false;
    return getComputedStyle(el).pointerEvents !== 'none';
  };

  const popupFor = (el) => {
    for (const attribute of ['aria-controls', 'aria-owns']) {
      const id = (el.getAttribute(attribute) || '').trim();
      if (!id) continue;
      const target = document.getElementById(id);
      if (target) return target;
    }
    if (el.matches(POPUP_SELECTOR)) return el;
    const nested = el.querySelector(POPUP_SELECTOR);
    if (nested) return nested;
    const sibling = el.nextElementSibling;
    return sibling && sibling.matches(POPUP_SELECTOR) ? sibling : null;
  };

  const control = document.querySelector(`[data-eval-control="${index}"]`);
  if (!control) return [];
  const popup = popupFor(control) || control;
  const options = [];
  for (const option of popup.querySelectorAll('[role="option"]')) {
    if (!isVisible(option) || isDisabled(option) || !isSelectable(option)) continue;
    const text = normalize(option.text || option.innerText || '');
    if (text.length > 0) options.push(text);
  }
  return options;
}""".replace("__VISIBILITY_JS__", VISIBILITY_JS)


def normalize(text: str) -> str:
    """Collapse whitespace so rendered text compares independently of markup."""
    return " ".join(text.split())


def fold(text: str) -> str:
    """Case-folded, whitespace-collapsed text (CSS may change letter case)."""
    return normalize(text).casefold()


def _check(name: str, passed: bool, detail: str, **evidence: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail, **evidence}


def page_loads_check(
    snapshot: Mapping[str, Any], loads: bool, page_errors: Sequence[str]
) -> dict[str, Any]:
    """The load event must have fired and the document must be complete."""
    ready_state = snapshot["readyState"]
    passed = loads and ready_state == "complete"
    detail = (
        f"readyState={ready_state}, load={'fired' if loads else 'did not fire'}, "
        f"{len(page_errors)} uncaught page error(s)"
    )
    return _check(
        "page_loads",
        passed,
        detail,
        page_error_count=len(page_errors),
        page_errors=list(page_errors[:10]),
    )


def body_visible_check(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """A non-empty, visible body means the document actually rendered."""
    body = snapshot["body"]
    text_length = int(body["textLength"])
    passed = bool(body["visible"]) and text_length > 0
    detail = f"visible={bool(body['visible'])}, rendered text length={text_length}"
    return _check("body_visible", passed, detail, text_length=text_length)


def _glued(edge: str, neighbour: str) -> bool:
    """Whether a token edge is glued to the character next to it.

    A metric value such as ``3`` or ``18`` must not be "found" inside ``13``,
    ``1,842`` or ``v4.18.2``, and ``64%`` must not be found inside ``164%``.
    """
    if not neighbour:
        return False
    if neighbour.isdigit():
        return True
    if edge.isdigit() and neighbour in ".,":
        return True
    return edge.isalnum() and neighbour.isalnum()


def contains_token(text: str, token: str) -> bool:
    """``token`` appears in ``text`` as a standalone token, not as a fragment."""
    haystack = fold(text)
    needle = fold(token)
    if not needle:
        return False
    start = 0
    while (index := haystack.find(needle, start)) != -1:
        before = haystack[index - 1] if index > 0 else ""
        end = index + len(needle)
        after = haystack[end] if end < len(haystack) else ""
        if not _glued(needle[0], before) and not _glued(needle[-1], after):
            return True
        start = index + 1
    return False


def metrics_check(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Every fixture metric name must sit next to its value in one element.

    A metric card is a small element holding its label and value; an element
    that aggregates many cards is longer than ``MAX_CONTAINER_TEXT`` and cannot
    satisfy the pair on its own. Values are matched as tokens, so a value that
    only survives inside a larger number is reported as lost.
    """
    texts = [
        fold(entry["text"])
        for entry in snapshot["containers"]
        if len(normalize(entry["text"])) <= MAX_CONTAINER_TEXT
    ]
    missing_labels = [
        label for label in METRICS if not any(contains_token(text, label) for text in texts)
    ]
    unpaired = [
        label
        for label, value in METRICS.items()
        if label not in missing_labels
        and not any(
            contains_token(text, label) and contains_token(text, value) for text in texts
        )
    ]
    found = len(METRICS) - len(missing_labels) - len(unpaired)
    passed = not missing_labels and not unpaired
    detail = f"{found}/{len(METRICS)} metric name+value pairs survived"
    if missing_labels:
        detail += f"; labels missing: {', '.join(missing_labels)}"
    if unpaired:
        detail += f"; values missing or separated from their label: {', '.join(unpaired)}"
    return _check(
        "metrics_preserved",
        passed,
        detail,
        missing_labels=missing_labels,
        unpaired_metrics=unpaired,
    )


def normalize_record(cells: Sequence[str]) -> tuple[str, ...]:
    """One rendered table row, independent of column order and letter case."""
    return tuple(sorted(cell for cell in (fold(value) for value in cells) if cell))


def table_records(snapshot: Mapping[str, Any]) -> list[tuple[str, ...]]:
    """Visible data records of the largest visible semantic table.

    The event panel is the biggest table on the fixture, so its records are the
    baseline data contract. Hidden rows and hidden cells were never rendered
    data, so they never contribute a record.
    """
    tables = [table for table in snapshot["tables"] if table.get("visible")]
    if not tables:
        return []
    table = max(tables, key=lambda entry: len(entry.get("records", ())))
    return [
        record
        for record in (normalize_record(cells) for cells in table.get("records", ()))
        if len(record) >= 2
    ]


def record_preview(record: Sequence[str], limit: int = 160) -> str:
    """A readable, bounded rendering of one event record for the gate report."""
    text = " · ".join(record)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _record_preserved(record: Sequence[str], candidate: Sequence[str]) -> bool:
    """A baseline record survives when one visible row still carries its cells.

    Cells compare as a multiset, so column order is free. A cell text that a
    rewrite merged into another cell is still preserved, provided every baseline
    cell can be found in that one candidate row.
    """
    if Counter(record) <= Counter(candidate):
        return True
    joined = " ".join(candidate)
    return all(contains_token(joined, cell) for cell in record)


def _bipartite_match(edges: Sequence[Sequence[int]], right_size: int) -> list[int]:
    """Assign every left item a distinct right item; ``-1`` when none is left."""
    match_right = [-1] * right_size
    match_left: list[int] = [-1] * len(edges)

    def augment(left: int, seen: list[bool]) -> bool:
        for right in edges[left]:
            if seen[right]:
                continue
            seen[right] = True
            if match_right[right] == -1 or augment(match_right[right], seen):
                match_right[right] = left
                match_left[left] = right
                return True
        return False

    for left in range(len(edges)):
        augment(left, [False] * right_size)
    return match_left


def event_records_check(
    snapshot: Mapping[str, Any], expected: Sequence[Sequence[str]] | None = None
) -> dict[str, Any]:
    """Every baseline event record must still appear in a visible table row.

    The candidate is graded against the baseline records, not a row count:
    losing one event or editing one cell fails the gate even when ten rows
    remain, while reordering rows or columns keeps it passing.
    """
    records = table_records(snapshot)
    if expected is None:
        passed = len(records) >= EVENT_TABLE_MIN_ROWS
        detail = (
            f"baseline event table exposes {len(records)} record(s); "
            f"the anchor needs {EVENT_TABLE_MIN_ROWS}"
        )
        return _check(
            "event_records_preserved",
            passed,
            detail,
            data_rows=len(records),
            baseline_records=EVENT_TABLE_MIN_ROWS,
        )
    edges = [
        [
            index
            for index, candidate in enumerate(records)
            if _record_preserved(record, candidate)
        ]
        for record in expected
    ]
    matched = _bipartite_match(edges, len(records))
    lost = [expected[index] for index, right in enumerate(matched) if right == -1]
    passed = not lost
    detail = (
        f"{len(expected) - len(lost)}/{len(expected)} baseline event record(s) preserved "
        f"in {len(records)} visible row(s)"
    )
    if lost:
        detail += "; lost: " + "; ".join(record_preview(record) for record in lost[:3])
        if len(lost) > 3:
            detail += f" (+{len(lost) - 3} more)"
    return _check(
        "event_records_preserved",
        passed,
        detail,
        data_rows=len(records),
        baseline_records=len(expected),
        lost_records=[record_preview(record) for record in lost[:10]],
    )


def filter_labels_check(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """The three daily filter labels must still be readable on screen.

    A rendered label may sit alone (``Region``) or share a small container with
    the control it labels (``Region All regions``), so the label is matched as a
    token. Table column headers are excluded: a column named ``Region`` is not
    the daily filter label and cannot stand in for a deleted one.
    """
    texts = [
        entry["text"]
        for entry in snapshot["containers"]
        if not entry.get("inHeader", False)
    ]
    missing = [
        label for label in FILTER_LABELS if not any(label_matches(text, label) for text in texts)
    ]
    passed = not missing
    detail = f"{len(FILTER_LABELS) - len(missing)}/{len(FILTER_LABELS)} filter labels shown"
    if missing:
        detail += f"; missing: {', '.join(missing)}"
    return _check("filter_labels_visible", passed, detail, missing_labels=missing)


def label_matches(text: str, label: str) -> bool:
    """A rendered label names ``label``, tolerating case and a trailing colon."""
    rendered = fold(text).rstrip(":：").strip()
    return rendered == fold(label) or contains_token(rendered, label)


def filter_options(snapshot: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """Option list of the baseline control associated with each filter label."""
    specs: dict[str, tuple[str, ...]] = {}
    for control in snapshot["controls"]:
        if not (control.get("visible") and control.get("enabled")):
            continue
        options = tuple(
            normalize(option) for option in control.get("options", ()) if normalize(option)
        )
        if len(options) < MIN_FILTER_OPTIONS:
            continue
        for label in FILTER_LABELS:
            if label not in specs and label_matches(control.get("label", ""), label):
                specs[label] = options
    return specs


def _required_options(expected: Sequence[str]) -> set[str]:
    """Filter values a candidate must still offer.

    The leading option of a fixture filter (``All regions``) is the "no filter"
    placeholder: its wording may change with the rewrite. The values after it
    are the actual filter data and have to survive.
    """
    values = list(expected)[1:] if len(expected) > 1 else list(expected)
    return {fold(value) for value in values}


def _options_preserved(control: Mapping[str, Any], expected: Sequence[str]) -> bool:
    """Whether a control exposes the baseline choices as selectable options.

    Empty options are a failure for every control: a native select whose options
    were removed and a custom combobox whose popup never exposed anything both
    lost the filter's choice set. The runner opens custom combobox popups before
    grading, so a closed combobox is not accepted on its label alone.
    """
    offered = {fold(option) for option in control.get("options", ()) if fold(option)}
    return _required_options(expected) <= offered


def _control_satisfies(control: Mapping[str, Any], expected: Sequence[str]) -> bool:
    """Visible, enabled, and still offering the daily control's choices."""
    if not (control.get("visible") and control.get("enabled")):
        return False
    return _options_preserved(control, expected)


def filter_controls_check(
    snapshot: Mapping[str, Any],
    expected: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    """Each of Region, Service and Severity must keep its own control.

    A control counts when it is visible and enabled and exposes its original
    choices as selectable options. Custom comboboxes are opened before grading,
    so their popup has to expose the choices; the label alone is not evidence.
    Distinct controls are required, so one merged dropdown cannot stand in for
    all three. The candidate need not make the selects filter anything: the
    fixture is static, so backend filtering is out of scope.
    """
    if expected is None:
        specs = filter_options(snapshot)
        missing = [label for label in FILTER_LABELS if label not in specs]
        passed = not missing
        detail = (
            f"baseline exposes a labelled control with >= {MIN_FILTER_OPTIONS} options for "
            f"{len(FILTER_LABELS) - len(missing)}/{len(FILTER_LABELS)} filter(s)"
        )
        if missing:
            detail += f"; missing: {', '.join(missing)}"
        return _check(
            "filter_controls_available",
            passed,
            detail,
            missing_labels=missing,
            baseline_labels=len(FILTER_LABELS),
        )
    controls = list(snapshot["controls"])
    labels = [label for label in FILTER_LABELS if label in expected]
    edges = [
        [
            index
            for index, control in enumerate(controls)
            if _control_satisfies(control, expected[label])
        ]
        for label in labels
    ]
    matched = _bipartite_match(edges, len(controls))
    missing = [labels[index] for index, right in enumerate(matched) if right == -1]
    passed = not missing
    detail = (
        f"{len(labels) - len(missing)}/{len(labels)} baseline filter control(s) available"
    )
    if missing:
        detail += f"; missing or without their original options: {', '.join(missing)}"
    return _check(
        "filter_controls_available",
        passed,
        detail,
        missing_labels=missing,
        controls=len(controls),
        baseline_labels=len(labels),
    )


def derive_anchor(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """The baseline's data contract for grading the candidate."""
    return {"records": table_records(snapshot), "controls": filter_options(snapshot)}


def action_name_matches(name: str, target: str = PRIMARY_ACTION) -> bool:
    """``New incident``, case-insensitively, ignoring icon-only decoration."""
    folded = fold(name)
    wanted = fold(target)
    if folded == wanted:
        return True
    if folded.endswith(wanted):
        return not any(char.isalnum() for char in folded[: -len(wanted)])
    if folded.startswith(wanted):
        return not any(char.isalnum() for char in folded[len(wanted):])
    return False


def primary_action_check(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """The primary incident action must still be visible and enabled."""
    named = [action for action in snapshot["actions"] if action["visible"] and action_name_matches(action["text"])]
    enabled = [action for action in named if action["enabled"]]
    passed = bool(enabled)
    detail = f"{len(named)} visible {PRIMARY_ACTION!r} action(s), {len(enabled)} enabled"
    return _check("primary_action_enabled", passed, detail, visible=len(named), enabled=len(enabled))


def evaluate_page(
    snapshot: Mapping[str, Any],
    *,
    loads: bool,
    page_errors: Sequence[str] = (),
    anchor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate the render/content/control-retention gate for one document.

    Without ``anchor`` the document is the trusted baseline: its own event
    records and labelled controls must satisfy the fixture shape, and they
    become the contract the candidate is graded against. With ``anchor`` the
    candidate must preserve every baseline record and filter option.
    """
    expected_records = None if anchor is None else anchor["records"]
    expected_controls = None if anchor is None else anchor["controls"]
    checks = [
        page_loads_check(snapshot, loads, page_errors),
        body_visible_check(snapshot),
        metrics_check(snapshot),
        event_records_check(snapshot, expected_records),
        filter_labels_check(snapshot),
        filter_controls_check(snapshot, expected_controls),
        primary_action_check(snapshot),
    ]
    return {
        "rendered": True,
        "passed": all(entry["passed"] for entry in checks),
        "checks": checks,
    }


def unavailable_candidate(reason: str) -> dict[str, Any]:
    """A candidate document that never arrived is a scored failure, not an error."""
    checks = [_check("candidate_available", False, reason)]
    return {"rendered": False, "passed": False, "checks": checks}


def unrendered_candidate(reason: str, page_errors: Sequence[str] = ()) -> dict[str, Any]:
    """A candidate document that failed to load is a scored failure as well."""
    checks = [
        _check(
            "page_loads",
            False,
            f"candidate did not finish loading: {reason}",
            page_error_count=len(page_errors),
            page_errors=list(page_errors[:10]),
        )
    ]
    return {"rendered": False, "passed": False, "checks": checks}


def baseline_contract(anchor: Mapping[str, Any]) -> dict[str, Any]:
    """The baseline-derived data the candidate was graded against, JSON-ready."""
    return {
        "event_records": [list(record) for record in anchor["records"]],
        "filter_options": {
            label: list(options) for label, options in anchor["controls"].items()
        },
    }


def build_gate_report(
    *,
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    inputs: Mapping[str, Any],
    screenshots: Mapping[str, Any],
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The JSON document the eval harness reads; ``passed`` is the verdict."""
    report = {
        "schema_version": 2,
        "runner": "refactor-ui-case-6",
        "viewport": {
            **VIEWPORT,
            "device_scale_factor": DEVICE_SCALE_FACTOR,
            "locale": LOCALE,
            "timezone_id": TIMEZONE_ID,
        },
        "inputs": inputs,
        "screenshots": screenshots,
        "baseline": baseline,
        "candidate": candidate,
        "passed": bool(candidate["passed"]),
        "failed_checks": [
            check["name"] for check in candidate["checks"] if not check["passed"]
        ],
    }
    if contract is not None:
        report["baseline_contract"] = dict(contract)
    return report


def read_html(path: Path) -> tuple[str, dict[str, Any]]:
    """Read one input document and record the exact bytes that were graded."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    try:
        html = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"{path} is not UTF-8: {exc}") from exc
    return html, {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def probe_custom_controls(page: Any, snapshot: dict[str, Any]) -> None:
    """Open custom comboboxes like a user and record the choices they expose.

    Native selects enumerate their options directly; a custom combobox only
    materialises them while open. Each visible, enabled non-native control is
    handled with real browser input: the choices of an already-open linked popup
    are read, otherwise the control is clicked with a bounded timeout, the popup
    is read and closed with Escape. A control that cannot be clicked (covered,
    ``pointer-events: none``, inert) contributes no choices, so it fails the gate
    instead of passing on its label.
    """
    from playwright.sync_api import Error as PlaywrightError

    indexes = [
        index
        for index, control in enumerate(snapshot["controls"])
        if control.get("tag") != "select"
        and control.get("visible")
        and control.get("enabled")
    ]
    if not indexes:
        return
    page.evaluate(TAG_CONTROLS_JS)
    for index in indexes:
        exposed = page.evaluate(READ_EXPOSED_OPTIONS_JS, index)
        if not exposed:
            try:
                page.locator(f'[data-eval-control="{index}"]').click(
                    timeout=INTERACTION_TIMEOUT_MS
                )
            except PlaywrightError:
                exposed = []
            else:
                exposed = page.evaluate(READ_EXPOSED_OPTIONS_JS, index)
                page.keyboard.press("Escape")
        snapshot["controls"][index]["options"] = [
            normalize(option) for option in exposed if normalize(option)
        ]


def render_document(
    browser: Any, html: str, *, screenshot_path: Path
) -> dict[str, Any]:
    """Render one document in a fresh offline context and capture its evidence.

    A document whose own scripts prevent the load event is reported as a load
    failure; browser or screenshot failures propagate to the caller, which
    reports them as infrastructure failures.
    """
    from playwright.sync_api import Error as PlaywrightError

    context = browser.new_context(
        viewport=dict(VIEWPORT),
        device_scale_factor=DEVICE_SCALE_FACTOR,
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
        offline=True,
        reduced_motion="reduce",
    )
    page_errors: list[str] = []

    def record_error(error: object) -> None:
        page_errors.append(str(error))

    try:
        page = context.new_page()
        page.set_default_timeout(OPERATION_TIMEOUT_MS)
        page.on("pageerror", record_error)
        loads = True
        try:
            page.set_content(html, wait_until="load")
        except PlaywrightError as exc:
            loads = False
            page_errors.append(str(exc))
        snapshot = None
        if loads:
            snapshot = page.evaluate(EXTRACT_SNAPSHOT_JS)
            page.screenshot(path=str(screenshot_path), full_page=True, animations="disabled")
            # Popups are opened after the screenshot so the saved render still
            # shows the page as the model left it.
            probe_custom_controls(page, snapshot)
    finally:
        context.close()
    return {"snapshot": snapshot, "loads": loads, "page_errors": page_errors}


def screenshot_metadata(path: Path) -> dict[str, Any]:
    """Screenshot evidence: a gate without a saved render cannot be trusted."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise RunnerError(f"missing screenshot {path}: {exc}") from exc
    if size <= 0:
        raise RunnerError(f"screenshot {path} is empty")
    return {"file": path.name, "bytes": size}


def run_gate(
    *,
    baseline_html: str,
    baseline_meta: Mapping[str, Any],
    candidate_html: str | None,
    candidate_meta: Mapping[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """Render both documents, apply the gate, and write the artifacts.

    The baseline must render cleanly: it is the verifier's trusted anchor, and
    a broken anchor is an infrastructure failure. A missing or unrenderable
    candidate is recorded in ``gate.json`` as a failed gate instead.
    """
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # the checker image always ships Playwright
        raise RunnerError(f"playwright is not available in this image: {exc}") from exc

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RunnerError(f"cannot create output directory {output_dir}: {exc}") from exc

    baseline_png = output_dir / "baseline.png"
    candidate_png = output_dir / "final.png"
    # A reused output directory must not leak an earlier run's screenshots into
    # this run's evidence.
    baseline_png.unlink(missing_ok=True)
    candidate_png.unlink(missing_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=list(BROWSER_ARGS))
            try:
                baseline_render = render_document(
                    browser, baseline_html, screenshot_path=baseline_png
                )
                if not baseline_render["loads"]:
                    raise RunnerError(
                        "the trusted baseline did not finish loading: "
                        + "; ".join(baseline_render["page_errors"])
                    )
                candidate_render = None
                if candidate_html is not None:
                    candidate_render = render_document(
                        browser, candidate_html, screenshot_path=candidate_png
                    )
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise RunnerError(f"browser failure: {exc}") from exc

    baseline = evaluate_page(
        baseline_render["snapshot"],
        loads=True,
        page_errors=baseline_render["page_errors"],
    )
    # The trusted baseline render supplies the expected event records and filter
    # options; a candidate is graded against that data, never against a count.
    anchor = derive_anchor(baseline_render["snapshot"])
    if candidate_html is None:
        candidate = unavailable_candidate(candidate_meta["error"])
    elif candidate_render is not None and candidate_render["loads"]:
        candidate = evaluate_page(
            candidate_render["snapshot"],
            loads=True,
            page_errors=candidate_render["page_errors"],
            anchor=anchor,
        )
    else:
        candidate = unrendered_candidate(
            candidate_render["page_errors"][-1], candidate_render["page_errors"]
        )

    screenshots = {
        "baseline": screenshot_metadata(baseline_png),
        "candidate": screenshot_metadata(candidate_png)
        if candidate["rendered"]
        else None,
    }
    report = build_gate_report(
        baseline=baseline,
        candidate=candidate,
        inputs={"baseline": dict(baseline_meta), "candidate": dict(candidate_meta)},
        screenshots=screenshots,
        contract=baseline_contract(anchor),
    )
    gate_path = output_dir / "gate.json"
    try:
        gate_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise RunnerError(f"cannot write {gate_path}: {exc}") from exc
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="browser_runner.py",
        description=(
            "Render the refactor-ui case-6 baseline and candidate, save the "
            "screenshots, and apply the render/content/control-retention gate."
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="baseline HTML file (the trusted fixture render)",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
        help="candidate HTML file produced from the baseline; may be absent",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="directory for baseline.png, final.png and gate.json",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        baseline_html, baseline_meta = read_html(args.baseline)
    except InputError as exc:
        print(f"browser_runner: {exc}", file=sys.stderr)
        return EXIT_USAGE

    try:
        candidate_html, candidate_meta = read_html(args.candidate)
    except InputError as exc:
        candidate_html = None
        candidate_meta = {
            "path": str(args.candidate),
            "bytes": None,
            "sha256": None,
            "error": str(exc),
        }

    try:
        report = run_gate(
            baseline_html=baseline_html,
            baseline_meta=baseline_meta,
            candidate_html=candidate_html,
            candidate_meta=candidate_meta,
            output_dir=args.output_dir,
        )
    except RunnerError as exc:
        print(f"browser_runner: {exc}", file=sys.stderr)
        return EXIT_INFRA

    if not report["baseline"]["passed"]:
        failed = ", ".join(
            check["name"] for check in report["baseline"]["checks"] if not check["passed"]
        )
        print(
            "browser_runner: the trusted baseline no longer satisfies its own gate "
            f"({failed}); the candidate verdict would be graded against the wrong anchor",
            file=sys.stderr,
        )
        return EXIT_INFRA

    verdict = "passed" if report["passed"] else "failed"
    print(f"browser_runner: candidate gate {verdict} ({args.output_dir / 'gate.json'})")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
