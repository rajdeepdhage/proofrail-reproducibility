# Running the Tests in SPSS

The hypothesis tests are already computed by `../metrics/hypothesis_tests.py`.
These files let you reproduce them in SPSS, which is useful if your committee
expects SPSS output or you want an independent check of the Python result.

## Files

| File | Use |
|---|---|
| `h1_h2_cases.csv` | 150 rows (75 ProofRail + 75 Bank), one row per case — for H1, H2, and H3 descriptives |
| `h5_state_counts.csv` | Aggregate terminal-state counts — for the H5 chi-square |
| `proofrail_tests.sps` | Ready-to-run syntax for all of the above |

## Steps

1. Open SPSS → **File > Open > Syntax** → select `proofrail_tests.sps`.
2. Edit the two `FILE=` paths near the top to point at your copies of the CSVs.
3. **Run > All**.

If you prefer menus instead of syntax, import `h1_h2_cases.csv` via
**File > Import Data > CSV Data**, then:
**Analyze > Nonparametric Tests > Legacy Dialogs > 2 Independent Samples**,
Test Variable = `latency_s`, Grouping Variable = `system_code` (groups 1 and 2),
Test Type = Mann-Whitney U.

## Which test for which hypothesis

| Hypothesis | Test | Variable |
|---|---|---|
| H1 authorization latency | Mann-Whitney U (one-tailed) | `latency_s` by `system_code` |
| H2 manual touches | Mann-Whitney U (one-tailed) | `touches` by `system_code` |
| H2 supporting | Mann-Whitney U | `auto_checks` by `system_code` |
| H3 auditability | **No significance test** — descriptives only | `audit_score` |
| H5 terminal states | Chi-square, cases weighted by `count` | `system` × `terminal_state` |

## Two things that will trip you up

**1. SPSS reports two-tailed p by default.** Prefer an exact or asymptotic
one-sided result when your SPSS dialog provides it. Halving a two-sided p-value
is justified only when the observed effect is in the pre-specified direction
and the reference distribution is symmetric; document the option and output
actually used. Here the conclusion is unchanged either way.

**2. Do not run a significance test on auditability.** The Bank score is exactly
8.0 for all 75 cases (SD = 0) and ProofRail is 12.0 for 73 of 75. SPSS will
happily return p < .001, but that result only restates the scoring rule you wrote
— it is circular, and a statistically literate reader will say so. Report the
means and SDs, publish the rubric, and cite the tamper-detection experiment
(240/240 mutations detected and localized) for the dimension that *is* measured.

## Expected results

Python (`metrics/hypothesis_tests.py`) produced:

| | H1 latency | H2 touches |
|---|---|---|
| Medians (ProofRail / Bank) | 0.0 s / 3,171.1 s | 0.0 / 3.0 |
| Mann-Whitney U | 0 | 0 |
| One-tailed p | < 1e-16 | < 1e-16 |
| Effect size (rank-biserial) | 1.0 | 1.0 |

SPSS should reproduce U = 0 for both. A U of exactly zero means the observed
samples do not overlap: every included ProofRail value is lower. SPSS
reports this as z with p < .001, since it does not print smaller values.

## A note on Chapter 2

Chapter 2 justifies KNIME over SPSS as the analysis instrument. That
justification is about *data integration* — harmonizing seven files with three
schemas — and remains correct. If you also run the significance tests in SPSS,
update §2.8 to state the division explicitly: KNIME for data integration and
characterization, SPSS for significance testing, Python for prototype execution.
That is a normal division of labour and reads as thoroughness, but it must match
what you actually did.

## Effect sizes

SPSS does not report rank-biserial correlation for Mann-Whitney directly.
Compute it from the reported U:

```
r = 1 - (2U) / (n1 × n2)
```

For H1, n1 = 70 and n2 = 75; for H2, n1 = n2 = 75. With U = 0,
rank-biserial r = 1.0 in both cases. Report the valid observation counts and
effect size alongside p.

The Python analysis additionally runs an exact paired sign robustness check on
shared trace IDs (70 pairs for H1, 75 for H2). The long-format SPSS file remains
the independent-sample reproduction of the originally specified U tests.

**H5 scope.** The supplied chi-square is exploratory. Its table includes Bank,
ProofRail, USDC, and Ethereum; Bitcoin and smart-contract events have no
commensurate status field. Ethereum failed execution is also not the same
construct as a ProofRail hold. Do not describe this crosstab as proof that all
blockchain systems lack reversible settlement.
