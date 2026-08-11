* ============================================================.
* ProofRail thesis - SPSS syntax for hypothesis testing.
* Open this in SPSS: File > Open > Syntax, then Run > All.
* Edit the two file paths below to match where you saved the CSVs.
* ============================================================.

* ---------- H1 and H2 : import row-level case data ----------.
GET DATA /TYPE=TXT
  /FILE="C:\path\to\spss\h1_h2_cases.csv"
  /DELIMITERS=","
  /QUALIFIER='"'
  /FIRSTCASE=2
  /VARIABLES=
    system A20
    system_code F1.0
    latency_s F12.4
    touches F5.2
    auto_checks F5.2
    audit_score F5.2.
VARIABLE LABELS
  system_code 'System (1=ProofRail, 2=Bank)'
  latency_s 'Authorization latency (seconds)'
  touches 'Manual verification touches per case'
  auto_checks 'Automated checks per case'
  audit_score 'Auditability rubric rollup'.
VALUE LABELS system_code 1 'ProofRail' 2 'Bank'.
EXECUTE.

* ---------- Descriptives first (report these regardless) ----------.
EXAMINE VARIABLES=latency_s touches auto_checks BY system_code
  /PLOT=BOXPLOT HISTOGRAM
  /STATISTICS=DESCRIPTIVES EXTREME
  /PERCENTILES(5,10,25,50,75,90,95).

* ---------- H1 : authorization latency ----------.
* Mann-Whitney U. SPSS reports a TWO-tailed p by default.
* Prefer SPSS one-sided output when available. Halve a two-sided p only when
* the observed effect is in the pre-specified direction and the reference
* distribution is symmetric; document the output option used.
NPAR TESTS
  /M-W= latency_s BY system_code(1 2)
  /STATISTICS=DESCRIPTIVES QUARTILES
  /MISSING ANALYSIS.

* ---------- H2 : manual verification touches ----------.
NPAR TESTS
  /M-W= touches BY system_code(1 2)
  /STATISTICS=DESCRIPTIVES QUARTILES
  /MISSING ANALYSIS.

* ---------- H2 supporting : automated checks (substitution) ----------.
* Shows touches are REPLACED by machine checks, not merely dropped.
NPAR TESTS
  /M-W= auto_checks BY system_code(1 2)
  /STATISTICS=DESCRIPTIVES
  /MISSING ANALYSIS.

* ---------- H3 : DO NOT RUN A SIGNIFICANCE TEST ----------.
* The rubric assigns a near-constant score per system (Bank = 8.0 for every
* case, SD = 0). There is no sampling variance, so a Mann-Whitney here would
* return a tiny p-value that only restates the scoring rule. Report the
* descriptives below instead, and cite the tamper-detection experiment
* (240/240 mutations detected) for the tamper-evidence dimension.
MEANS TABLES=audit_score BY system_code
  /CELLS=MEAN STDDEV MIN MAX COUNT.

* ============================================================.
* ---------- H5 : terminal-state composition ----------.
* Separate file of aggregate counts; weight cases before the crosstab.
* ============================================================.
GET DATA /TYPE=TXT
  /FILE="C:\path\to\spss\h5_state_counts.csv"
  /DELIMITERS=","
  /QUALIFIER='"'
  /FIRSTCASE=2
  /VARIABLES=
    system A20
    terminal_state A24
    count F8.0.
EXECUTE.

WEIGHT BY count.

CROSSTABS
  /TABLES=system BY terminal_state
  /STATISTICS=CHISQ PHI
  /CELLS=COUNT ROW EXPECTED
  /COUNT ROUND CELL.

WEIGHT OFF.

* NOTE on H5: this is an exploratory crosstab of systems with a coded status.
* Bitcoin and smart-contract event extracts cannot appear because they have no
* commensurate status field. Ethereum failure is not equivalent to a ProofRail
* hold. Report dataset coding differences; do not infer protocol-wide
* impossibility from an absent field.
