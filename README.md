# Replication Package: The Climate-Resilience Ledger

Companion code for the manuscript *"The Climate-Resilience Ledger:
Reinterpreting the Indus Script as an Ecological Survival Technology"*
(submitted to the **Journal of Archaeological Science**).

`analyze_icit.py` reproduces the frequency analysis and Fisher's exact tests
of **Prediction 4** (urban concentration of the "vessel-count" motif)
reported in **Section 5** of the manuscript, directly from the public SQL
mirror of the **Interactive Corpus of Indus Texts (ICIT)**.

---

## 1. Repository contents

| File | Purpose |
|------|---------|
| `analyze_icit.py` | End-to-end analysis: parses the SQL dump, classifies settlements, computes the three "Jar + Numeral" operationalizations, runs Fisher's exact tests, writes CSV tables and a summary figure |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

## 2. Data provenance

- **Corpus:** Interactive Corpus of Indus Texts (ICIT), Wells & Fuls (2023).
- **Mirror used:** the public SQL dump `population-script.sql` distributed via
  the Yajnadevam project on GitHub:
  `https://github.com/yajnadevam/indus-website` (file: `population-script.sql`).
  Download the raw file into this folder.
- The live ICIT database (`indus.epigraphica.de`) has been password-restricted
  since ~2021; the GitHub mirror is the most comprehensive public export of
  the full relational schema (`SITE`, `GLYPH`, `SEAL`, `INSCRIPTION`,
  `GLYPHSEQUENCE`).

## 3. Setup

```bash
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
```

Requires Python 3.9+.

## 4. Run

```bash
# 1. Optional built-in verification (no data needed; ~5 s)
python analyze_icit.py --selftest

# 2. Full analysis against the downloaded SQL dump
python analyze_icit.py --sql population-script.sql --outdir results
```

Outputs (written to `results/`):

| Output | Content |
|--------|---------|
| `frequency_results.csv` | Counts and percentages of the three patterns by settlement class (source data of manuscript Table 5.1) |
| `fisher_tests.csv` | 2×2 tables, two-sided Fisher p-values, odds ratios with 95% CIs, Wilson 95% CIs for percentages |
| `figure1_jar_numeral.png` | Two-panel version of manuscript Figure 1 (colorblind-safe palette, Wilson CIs) |
| console report | Class-wise frequencies, test statistics, per-site breakdown of the canonical pattern |

`--no-figures` skips the PNG; all analysis is offline.

## 5. Expected results

With the ICIT mirror as distributed (2,543 inscribed objects after filtering;
2,514 in-region inscriptions across 37 sites), the analysis reproduces the
manuscript's Section 5 / Table 5.1:

| Pattern | Urban (n=2,304) | Peripheral (n=210) | Fisher p (two-sided) | Odds ratio [95% CI] |
|---|---|---|---|---|
| Jar → Numeral (canonical) | 47 (2.04%) | 3 (1.43%) | 0.80 | 1.44 [0.44, 4.66] |
| Numeral → Jar (strict terminal) | 6 (0.26%) | 0 (0.00%) | 1.00 | 1.19* [0.07, 21.21]* |
| Co-occurrence (same inscription) | 78 (3.39%) | 4 (1.90%) | 0.31 | 1.80 [0.65, 4.98] |

\* Haldane–Anscombe 0.5-corrected (zero peripheral cell). The co-occurrence
odds ratio is reported as 1.80 (exact sample value 16068/8904 = 1.8046,
two-decimal rounding), identical to the value in the manuscript and cover
letter. All other values are identical.

Interpretation (as stated in the manuscript): all three contrasts are
**directionally consistent** with urban enrichment, but **none reaches
statistical significance** at α = 0.05 at current sample sizes — a limitation
analysed explicitly in Section 7 of the paper.

## 6. Sign identification (important caveat)

The mirror uses an internal `GLYPHID` numbering that does **not** align 1:1
with the Mahadevan (M) or Parpola (P) concordances. The graphemes analysed
here were identified by frequency, positional behaviour, and Unicode
cross-reference:

- **"Jar / vessel"** = `GLYPHID 740` (Unicode `U+E61B`) — the most frequent
  grapheme (1,267 occurrences) and the one most often followed by a numeral.
- **"Numerals"** = `GLYPHIDs 900–906` (Unicode `U+E33A`–`U+E365`) — the seven
  basic stroke numerals.

To re-run the analysis with a different sign mapping, edit `JAR_GLYPH` and
`NUMERAL_GLYPHS` at the top of `analyze_icit.py`.

## 7. Settlement classification

Follows Possehl (2002). **Urban** = the six Class-A cities:
Mohenjo-daro (SI1), Harappa (SI2), Dholavira (SI3), Rakhigarhi (SI4),
Kalibangan (SI25), Ganweriwala (SI31). **Peripheral / rural** = all remaining
in-region sites. Foreign-context objects (Mesopotamian, Central Asian, Gulf,
"Unknown") are excluded — 15 site IDs listed in `FOREIGN_OR_EXCLUDE` in the
script. Caveat: ~94% of the urban sample derives from Mohenjo-daro and
Harappa alone; see Section 7 (Limitations) of the manuscript.

## 8. Citation

If this code or the derived frequency tables support your work, please cite
the manuscript and the corpus:

> Sharma, H. (2026). The Climate-Resilience Ledger: Reinterpreting the Indus
> Script as an Ecological Survival Technology. Submitted to the Journal of
> Archaeological Science.
>
> Wells, B. K., & Fuls, A. (2023). *Interactive Corpus of Indus Texts (ICIT)*.

## 9. License

Code: MIT License. The ICIT data itself remains under the terms of the
Wells & Fuls corpus release; use the mirror accordingly.

Contact: Harshit Sharma — harshit28102@gmail.com
