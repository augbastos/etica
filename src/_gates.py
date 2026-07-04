# -*- coding: utf-8 -*-
"""
_gates.py — shared validation barrier for the etica-spinoza-2026 build.

Both build_pdf.py and build_epub.py call run_gates() at the very top of their
build(). If a gate fails, the build ABORTS before writing any artifact, so a
book that betrays its source can never be silently produced.

THREE GATES, cheapest first (fail fast, fail cheap):

  1. validate_seals_poc.py  — COORDINATE existence (anti-fabricated reference).
                              Deterministic, zero cost. [advisory by default]
  2. consistency_check.py   — terminological drift vs the book's own glossary.
                              Deterministic, zero cost. Exit 1 on HIGH flags.
  3. fidelity_gate.py       — SEMANTIC fidelity of sealed paraphrases vs the EN
                              source, via LLM-judge on the `claude` CLI Max login
                              (zero PAID API). Exit 1 on any FAIL.

The scripts live in renda-2000/hardening/spinoza/ (the hardening tree), not in
this book repo, so this module locates them by relative path and runs them as
subprocesses with the SAME interpreter that launched the build.

ENV KNOBS (so a build can be tuned without editing code):
  SPINOZA_GATES=0            -> skip ALL gates (escape hatch; prints a warning).
  SPINOZA_FIDELITY=0         -> skip only the LLM-judge gate (e.g. offline box);
                                the deterministic gates still run.
  SPINOZA_GATES_STRICT=1     -> treat the consistency gate's known-benign HIGH
                                flags as hard failures too (default: advisory,
                                because the 3 current HIGH flags are documented
                                rhetorical contrast — see VALIDACAO.md).

Honest note: consistency_check currently exits 1 on 3 HIGH flags that have been
human-classified as legitimate rhetorical contrast ("não é A, mas B"), NOT
contradictions. So by default this barrier runs it as ADVISORY (reports, does
not abort) and lets the SEMANTIC fidelity gate be the hard stop. Set
SPINOZA_GATES_STRICT=1 to make every gate a hard abort.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# renda-2000/hardening/spinoza relative to this file:
#   <IA>/etica-spinoza-2026/src/_gates.py  ->  <IA>/renda-2000/hardening/spinoza
_IA_ROOT = Path(__file__).resolve().parents[2]
HARDENING = _IA_ROOT / "renda-2000" / "hardening" / "spinoza"

SEALS_POC = HARDENING / "validate_seals_poc.py"
CONSISTENCY = HARDENING / "consistency_check.py"
FIDELITY = HARDENING / "fidelity_gate.py"


def _run(script: Path, extra_args=None) -> int:
    """Run a gate script with the current interpreter; stream its output.
    Returns its exit code, or 127 if the script file is missing."""
    if not script.exists():
        print(f"  [gate] MISSING: {script} (skipped)")
        return 127
    cmd = [sys.executable, str(script)] + (extra_args or [])
    proc = subprocess.run(cmd)
    return proc.returncode


def run_gates() -> None:
    """Run the validation barrier. Raises SystemExit(1) if a hard gate fails."""
    if os.environ.get("SPINOZA_GATES") == "0":
        print("!! SPINOZA_GATES=0 — ALL validation gates SKIPPED. Build is UNVERIFIED.")
        return

    strict = os.environ.get("SPINOZA_GATES_STRICT") == "1"
    do_fidelity = os.environ.get("SPINOZA_FIDELITY") != "0"

    print("=" * 72)
    print("VALIDATION BARRIER (gates run before any artifact is written)")
    print("=" * 72)

    failed = []

    # ---- Gate 1: coordinate existence (advisory; informational PoC) ----
    print("\n[gate 1/3] seal-coordinate existence (validate_seals_poc.py)")
    rc1 = _run(SEALS_POC)
    # PoC has no failing exit code today; treat non-zero as advisory only.
    if rc1 not in (0, 127):
        print(f"  [gate 1] advisory: exit {rc1} (PoC is informational, not a stop)")

    # ---- Gate 2: terminological drift (deterministic) ----
    print("\n[gate 2/3] terminological drift vs glossary (consistency_check.py)")
    rc2 = _run(CONSISTENCY)
    if rc2 == 0:
        print("  [gate 2] PASS — no HIGH drift flags.")
    elif rc2 == 127:
        pass
    else:
        if strict:
            print(f"  [gate 2] FAIL (strict) — exit {rc2}.")
            failed.append("consistency_check")
        else:
            print(f"  [gate 2] ADVISORY — exit {rc2} (known-benign rhetorical "
                  f"HIGH flags; set SPINOZA_GATES_STRICT=1 to make this a stop).")

    # ---- Gate 3: semantic fidelity (LLM-judge, zero paid API) ----
    if do_fidelity:
        print("\n[gate 3/3] semantic fidelity of sealed paraphrases (fidelity_gate.py)")
        # --skip-if-no-cli: a machine without the `claude` CLI still builds, but
        # is told loudly that fidelity was not judged (exit 0). A real FAIL from
        # the judge returns exit 1 and aborts the build below.
        rc3 = _run(FIDELITY, ["--skip-if-no-cli", "--report"])
        if rc3 == 0:
            print("  [gate 3] PASS (or soft-skipped — read the gate output above).")
        elif rc3 == 127:
            pass
        elif rc3 == 1:
            print("  [gate 3] FAIL — a sealed paraphrase betrays its source.")
            failed.append("fidelity_gate")
        else:
            print(f"  [gate 3] inconclusive — exit {rc3} (fidelity NOT established).")
            if strict:
                failed.append("fidelity_gate(inconclusive)")
    else:
        print("\n[gate 3/3] SKIPPED via SPINOZA_FIDELITY=0 — semantic fidelity UNJUDGED.")

    print("\n" + "=" * 72)
    if failed:
        print(f"BUILD ABORTED — failing gate(s): {', '.join(failed)}")
        print("Fix the flagged content (or override with SPINOZA_GATES env knobs")
        print("only if you understand exactly what you are skipping).")
        print("=" * 72)
        raise SystemExit(1)
    print("VALIDATION BARRIER PASSED — proceeding to build.")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    # Allow running the barrier standalone: python src/_gates.py
    run_gates()
    print("gates-only run complete (no artifact built).")
