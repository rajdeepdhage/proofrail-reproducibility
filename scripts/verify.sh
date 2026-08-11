#!/usr/bin/env bash
# Full integrity + reproducibility check. Exits non-zero on any failure.
set -uo pipefail
cd "$(dirname "$0")/.."
status=0

echo "==> 1/9  Verifying artifact integrity against MANIFEST.sha256"
if [ ! -f MANIFEST.sha256 ]; then
  echo "    MANIFEST.sha256 not found — run: python3 scripts/make_manifest.py"
  status=1
elif command -v sha256sum >/dev/null 2>&1; then
  if sha256sum -c MANIFEST.sha256 --quiet; then
    echo "    OK — all artifacts match their recorded hashes"
  else
    echo "    FAILED — one or more artifacts have been modified"; status=1
  fi
elif command -v shasum >/dev/null 2>&1; then
  if shasum -a 256 -c MANIFEST.sha256 --quiet; then
    echo "    OK — all artifacts match their recorded hashes"
  else
    echo "    FAILED — one or more artifacts have been modified"; status=1
  fi
else
  echo "    SKIPPED — no sha256sum/shasum available"
fi

echo
echo "==> 2/9  Checking source and documentation"
if python3 scripts/check_line_endings.py && \
   python3 -m compileall -q generator metrics scripts verifier tests && \
   python3 scripts/check_markdown_links.py; then
  echo "    OK — Python source compiles and local links resolve"
else
  echo "    FAILED — source compilation or documentation-link error"; status=1
fi

echo
echo "==> 3/9  Regenerating frozen inputs from seed 42"
if python3 scripts/check_generator_reproducibility.py; then
  echo "    OK — 75-row and 5,000-row inputs are byte-identical"
else
  echo "    FAILED — generator output differs from the frozen inputs"; status=1
fi

echo
echo "==> 4/9  Recomputing reported metrics from per-transaction traces"
if python3 metrics/compute_metrics.py --check; then
  echo "    OK — recomputed metrics match the published summary"
else
  echo "    FAILED — recomputed metrics disagree with the published summary"; status=1
fi

echo
echo "==> 5/9  Verifying the sample audit chain"
if python3 verifier/verify_audit_chain.py verifier/sample_audit_chain.db; then
  echo "    OK — audit chain intact"
else
  echo "    FAILED — audit chain verification failed"; status=1
fi

echo
echo "==> 6/9  Checking four-comparison design invariants"
if python3 metrics/check_comparison_invariants.py > /tmp/proofrail_invariants.txt 2>&1; then
  echo "    OK — bank and ProofRail legs constant across all four comparisons"
else
  echo "    FAILED — a constant leg varied across comparisons"
  sed 's/^/      /' /tmp/proofrail_invariants.txt | tail -8
  status=1
fi

echo
echo "==> 7/9  Hypothesis tests H1/H2 (with paired robustness check)"
if python3 metrics/hypothesis_tests.py > /tmp/proofrail_h12.txt 2>&1; then
  echo "    OK — H1 and H2 supported within the modeled sensitivity envelope"
else
  echo "    FAILED — see output below"
  sed 's/^/      /' /tmp/proofrail_h12.txt | tail -12
  status=1
fi

echo
echo "==> 8/9  Tamper-detection experiment (measured, not scored)"
if python3 metrics/tamper_experiment.py --trials 240 > /tmp/proofrail_tamper.txt 2>&1; then
  grep -E "detected|localized" /tmp/proofrail_tamper.txt | head -2 | sed 's/^/    /'
  echo "    OK — all mutations detected"
else
  echo "    FAILED — a mutation escaped detection"
  sed 's/^/      /' /tmp/proofrail_tamper.txt | tail -10
  status=1
fi

echo
echo "==> 9/9  Running unit tests"
if python3 -m unittest discover -s tests -v; then
  echo "    OK — unit tests passed"
else
  echo "    FAILED — unit test failure"; status=1
fi

echo
if [ "$status" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
else
  echo "ONE OR MORE CHECKS FAILED"
fi
exit "$status"
