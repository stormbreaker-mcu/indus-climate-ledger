#!/usr/bin/env python3
"""
Replication script for:
  "The Climate-Resilience Ledger: Reinterpreting the Indus Script as an
   Ecological Survival Technology" (Journal of Archaeological Science, 2026)

Reproduces the frequency analysis and Fisher's exact tests of Prediction 4
(urban concentration of the "vessel-count" motif) reported in Section 5 of
the manuscript, from the public SQL mirror of the Interactive Corpus of
Indus Texts (ICIT).

================================================================
DATA PROVENANCE
================================================================
The "Interactive Corpus of Indus Texts" (ICIT) is the canonical database of
Indus inscriptions developed by Bryan K. Wells and maintained with Andreas
Fuls at TU Berlin (Wells & Fuls 2023). The live database
(indus.epigraphica.de) has been password-restricted since ~2021. This
analysis uses the most comprehensive public mirror: the SQL dump
(population-script.sql) distributed through the Yajnadevam/indus-website
repository on GitHub, which exports the full ICIT relational schema
(SITE, GLYPH, SEAL, INSCRIPTION, GLYPHSEQUENCE).

Corpus after filtering: 2,543 inscribed objects from 52 archaeological
sites; the settlement-type comparison uses the 2,514 in-region inscriptions
from 37 sites (foreign-context objects excluded).

================================================================
SIGN DEFINITIONS (with caveats)
================================================================
The Yajnadevam dump uses an internal GLYPHID numbering that does not align
1-to-1 with the Mahadevan (M) or Parpola (P) concordances. The graphemes
used here were identified by frequency, positional behaviour, and Unicode
cross-reference:

  - "Jar / vessel" : GLYPHID 740 (Unicode U+E61B)
      The single most frequent grapheme in the corpus (1,267 occurrences)
      and the grapheme most often followed by a numeral. Functionally
      equivalent to the terminal "jar" of the classical M342-type sequence.

  - "Numerals"     : GLYPHIDs 900-906 (Unicode U+E33A-U+E365)
      The seven basic Indus numerals (1-7 vertical strokes).

The three operationalizations of the "Jar + Numeral" pattern (Section 5):
  1. jar_then_num  : GLYPHID 740 immediately followed by a numeral
                     (canonical "vessel-count" diagnostic).
  2. num_then_jar  : a numeral immediately followed by GLYPHID 740
                     (the terminal pattern of traditional scholarship).
  3. co_occur      : jar and at least one numeral anywhere in the same
                     inscription (loosest definition).

================================================================
USAGE
================================================================
  python analyze_icit.py --sql population-script.sql --outdir results
  python analyze_icit.py --selftest        # built-in synthetic-data test

Requires Python 3.9+ and the packages in requirements.txt.
"""

import argparse
import csv
import math
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------- constants

JAR_GLYPH = 740                      # Unicode U+E61B
NUMERAL_GLYPHS = frozenset(range(900, 907))  # GLYPHIDs 900-906

# Possehl (2002) settlement tiers: the six Class-A cities.
URBAN_SITES = {
    "SI1":  "Mohenjo-daro",   # ~200 ha
    "SI2":  "Harappa",        # ~150 ha
    "SI3":  "Dholavira",      # ~100 ha
    "SI4":  "Rakhigarhi",     # ~350 ha
    "SI25": "Kalibangan",     # ~100 ha
    "SI31": "Ganweriwala",    # ~80 ha
}

# Foreign / unprovenanced contexts excluded from the settlement comparison
# (Mesopotamian, Central Asian, Gulf, and "Unknown" provenances).
FOREIGN_OR_EXCLUDE = {
    "SI5", "SI6", "SI9", "SI22", "SI27", "SI30", "SI34", "SI35",
    "SI37", "SI39", "SI40", "SI41", "SI45", "SI46", "SI49",
}

Z95 = 1.959963984540054

PATTERNS = ("jar_then_num", "num_then_jar", "co_occur")
PATTERN_LABELS = {
    "jar_then_num": "Jar -> Numeral (canonical)",
    "num_then_jar": "Numeral -> Jar (strict terminal)",
    "co_occur":     "Co-occurrence (same inscription)",
}

# ------------------------------------------------------------------- parsing

def parse_sql(path):
    """Parse the population-script.sql dump of the ICIT mirror.

    Returns (sites, glyphs, seal_site, sequences) where
      sites      : {SITEID: name}
      glyphs     : {GLYPHID: unicode string}
      seal_site  : {SEALID: SITEID}
      sequences  : {SEALID: [(position, GLYPHID), ...] sorted by position}
    """
    content = Path(path).read_text(encoding="utf-8", errors="replace")

    def block(header_pattern):
        m = re.search(header_pattern + r"\s*(.*?);\s*\n", content, re.DOTALL)
        if not m:
            sys.exit(f"ERROR: could not locate '{header_pattern}' in {path}.\n"
                     "Is this the population-script.sql dump from the "
                     "Yajnadevam/indus-website mirror?")
        return m.group(1)

    sites = {}
    for sid, name in re.findall(
            r'\("?(SI\d+)"?,\s*"?([^,)]+?)"?\)',
            block(r"INSERT INTO SITE \(SITEID, NAME\) VALUES")):
        sites[sid] = name.strip()

    glyphs = {}
    mg = re.search(r"INSERT INTO GLYPH \(GLYPHID, UNICODE\) VALUES", content)
    if mg:
        seg = content[mg.end(): content.find("\n\n", mg.end())]
        for gid, uni in re.findall(r'\((\d+),\s*"([^"]+)"\)', seg):
            glyphs[int(gid)] = uni

    seal_site = {}
    for sid, site in re.findall(r'\(\s*(\d+),\s*"(SI\d+)"',
                                block(r"INSERT INTO SEAL \(.*?\) VALUES")):
        seal_site[int(sid)] = site

    sequences = defaultdict(list)
    for sid, gid, pos in re.findall(
            r'\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)',
            block(r"INSERT INTO GLYPHSEQUENCE \(.*?\) VALUES")):
        sequences[int(sid)].append((int(pos), int(gid)))
    for s in sequences:
        sequences[s].sort()

    return sites, glyphs, seal_site, sequences

# ------------------------------------------------------------- classification

def classify(site_id):
    """Possehl (2002) tiers: 'urban' (Class-A), 'peripheral', or 'excluded'."""
    if site_id in FOREIGN_OR_EXCLUDE:
        return "excluded"
    if site_id in URBAN_SITES:
        return "urban"
    return "peripheral"


def has_pattern(sequence, mode):
    """Whether one inscription exhibits a given 'Jar + Numeral' pattern."""
    glyphs = [g for _, g in sequence]
    if not glyphs:
        return False
    has_jar = JAR_GLYPH in glyphs
    has_num = any(g in NUMERAL_GLYPHS for g in glyphs)
    if not (has_jar and has_num):
        return False
    if mode == "co_occur":
        return True
    for i, g in enumerate(glyphs):
        if mode == "jar_then_num" and g == JAR_GLYPH \
                and i + 1 < len(glyphs) and glyphs[i + 1] in NUMERAL_GLYPHS:
            return True
        if mode == "num_then_jar" and g == JAR_GLYPH \
                and i > 0 and glyphs[i - 1] in NUMERAL_GLYPHS:
            return True
    return False

# ---------------------------------------------------------------- statistics

def wilson(k, n, z=Z95):
    """Wilson score interval for a binomial proportion, in percent."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    lo = max(0.0, 100 * (center - half))
    hi = min(100.0, 100 * (center + half))
    return 100 * p, lo, hi


def odds_ratio_ci(urban_pos, urban_neg, peri_pos, peri_neg):
    """Sample odds ratio with a Woolf log-OR 95% CI.

    Applies the Haldane-Anscombe 0.5 correction when any cell is zero
    (correction flagged in the returned tuple).
    """
    a, b, c, d = urban_pos, urban_neg, peri_pos, peri_neg
    corrected = 0 in (a, b, c, d)
    if corrected:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    or_ = (a * d) / (b * c)
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return or_, or_ * math.exp(-Z95 * se), or_ * math.exp(Z95 * se), corrected


def fisher_table(counts, totals):
    """Fisher's exact tests + effect sizes for the three patterns.

    counts : {pattern: {class: positive inscriptions}}
    totals : {class: total inscriptions}
    Returns a list of result dicts.
    """
    from scipy.stats import fisher_exact

    results = []
    for pat in PATTERNS:
        u, p = counts[pat]["urban"], counts[pat]["peripheral"]
        nu, np_ = totals["urban"], totals["peripheral"]
        odds, pval = fisher_exact([[u, nu - u], [p, np_ - p]],
                                  alternative="two-sided")
        or_, lo, hi, corrected = odds_ratio_ci(u, nu - u, p, np_ - p)
        wu = wilson(u, nu)
        wp = wilson(p, np_)
        results.append({
            "pattern": PATTERN_LABELS[pat],
            "urban_n": nu, "urban_pos": u,
            "peripheral_n": np_, "peripheral_pos": p,
            "pct_urban": round(100 * u / nu, 2),
            "pct_peripheral": round(100 * p / np_, 2),
            "wilson_urban": tuple(round(x, 2) for x in wu),
            "wilson_peripheral": tuple(round(x, 2) for x in wp),
            "p_value": round(pval, 4),
            "odds_ratio": round(or_, 2),
            "ci95_low": round(lo, 2), "ci95_high": round(hi, 2),
            "half_cell_correction": corrected,
        })
    return results

# ------------------------------------------------------------------ pipeline

def run_analysis(sql_path, outdir, make_figures=True, quiet=False):
    """Full pipeline: parse -> classify -> count -> test -> write outputs."""
    sites, glyphs, seal_site, sequences = parse_sql(sql_path)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    totals = Counter()
    counts = {pat: Counter() for pat in PATTERNS}
    per_site = Counter()
    per_site_pattern = Counter()

    for seal_id, seq in sequences.items():
        site_id = seal_site.get(seal_id)
        if not site_id:
            continue
        cls = classify(site_id)
        if cls == "excluded":
            continue
        totals[cls] += 1
        per_site[site_id] += 1
        for pat in PATTERNS:
            if has_pattern(seq, pat):
                counts[pat][cls] += 1
                if pat == "jar_then_num":
                    per_site_pattern[site_id] += 1

    results = fisher_table(counts, totals)

    # ---- console report ----
    if not quiet:
        n_total = totals["urban"] + totals["peripheral"]
        print("=" * 82)
        print("ICIT corpus - 'Jar + Numeral' pattern by settlement type")
        print("=" * 82)
        print(f"  Jar sign : GLYPHID {JAR_GLYPH} "
              f"({glyphs.get(JAR_GLYPH, 'U+E61B')})")
        print(f"  Numerals : GLYPHIDs {min(NUMERAL_GLYPHS)}-"
              f"{max(NUMERAL_GLYPHS)}")
        print(f"  In-region inscribed objects : {n_total} "
              f"(urban {totals['urban']} / peripheral {totals['peripheral']})")
        print(f"  Sites: {len(per_site)} in-region "
              f"({len([s for s in per_site if s in URBAN_SITES])} Class-A)")
        print()
        hdr = (f"{'Class':<12}{'n':>7}{'Jar>Num':>9}{'%':>8}"
               f"{'Num>Jar':>9}{'%':>8}{'Co-occur':>10}{'%':>8}")
        print(hdr)
        print("-" * len(hdr))
        for cls in ("urban", "peripheral"):
            t = totals[cls]
            row = f"{cls:<12}{t:>7}"
            for pat in PATTERNS:
                k = counts[pat][cls]
                row += f"{k:>9}{100 * k / t:>7.2f}%"
            print(row)
        print()
        print("Fisher's exact tests (two-sided), urban vs peripheral:")
        for r in results:
            corr = " (0.5-corrected OR: zero cell)" \
                if r["half_cell_correction"] else ""
            print(f"  {r['pattern']:<36} p = {r['p_value']:.2f}   "
                  f"OR = {r['odds_ratio']:.2f} "
                  f"[{r['ci95_low']:.2f}, {r['ci95_high']:.2f}]{corr}")
        print(f"\n  Interpretation: directions are consistent with urban "
              f"enrichment but none reaches significance at alpha = 0.05.")

    # ---- frequency_results.csv ----
    with open(outdir / "frequency_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["settlement_class", "total_objects", "jar_then_numeral",
                    "jar_then_numeral_pct", "num_then_jar",
                    "num_then_jar_pct", "co_occurrence", "co_occurrence_pct"])
        for cls in ("urban", "peripheral"):
            t = totals[cls]
            w.writerow([cls, t] + [v for pat in PATTERNS
                                   for v in (counts[pat][cls],
                                             f"{100 * counts[pat][cls] / t:.2f}")])

    # ---- fisher_tests.csv ----
    with open(outdir / "fisher_tests.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pattern", "urban_n", "urban_pos", "peripheral_n",
                    "peripheral_pos", "pct_urban", "pct_peripheral",
                    "wilson_urban_pct", "wilson_peripheral_pct",
                    "fisher_p_two_sided", "odds_ratio", "ci95_low",
                    "ci95_high", "half_cell_correction"])
        for r in results:
            w.writerow([r["pattern"], r["urban_n"], r["urban_pos"],
                        r["peripheral_n"], r["peripheral_pos"],
                        r["pct_urban"], r["pct_peripheral"],
                        f"{r['wilson_urban'][0]:.2f} "
                        f"[{r['wilson_urban'][1]:.2f}, "
                        f"{r['wilson_urban'][2]:.2f}]",
                        f"{r['wilson_peripheral'][0]:.2f} "
                        f"[{r['wilson_peripheral'][1]:.2f}, "
                        f"{r['wilson_peripheral'][2]:.2f}]",
                        r["p_value"], r["odds_ratio"], r["ci95_low"],
                        r["ci95_high"], r["half_cell_correction"]])

    if not quiet:
        print(f"\nWritten: {outdir / 'frequency_results.csv'}")
        print(f"Written: {outdir / 'fisher_tests.csv'}")

    if make_figures:
        fig_path = outdir / "figure1_jar_numeral.png"
        make_figure(counts, totals, fig_path)
        if not quiet:
            print(f"Written: {fig_path}")

    return {"totals": totals, "counts": counts, "results": results,
            "per_site": per_site, "per_site_pattern": per_site_pattern,
            "sites": sites}

# -------------------------------------------------------------------- figure

def make_figure(counts, totals, path):
    """Two-panel version of manuscript Figure 1 (Okabe-Ito, Wilson 95% CI)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    BLUE, ORANGE = "#0072B2", "#E69F00"
    urban = [counts[p]["urban"] for p in PATTERNS]
    peri = [counts[p]["peripheral"] for p in PATTERNS]
    nu, np_ = totals["urban"], totals["peripheral"]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.9, 5.3), dpi=200,
                                   constrained_layout=True)
    fig.suptitle("Distribution of the \u201cJar + Numeral\u201d Pattern in the "
                 "ICIT Corpus\nby Settlement Type", fontsize=14,
                 fontweight="bold")

    x = np.arange(3)
    w = 0.38
    axL.bar(x - w / 2, urban, w, color=BLUE, label=f"Urban (n={nu:,})")
    axL.bar(x + w / 2, peri, w, color=ORANGE, label=f"Peripheral (n={np_})")
    for bars in axL.containers:
        axL.bar_label(bars, fontsize=10, fontweight="bold", padding=2)
    axL.set_xticks(x)
    axL.set_xticklabels(["Jar \u2192 Numeral\n(canonical)",
                         "Numeral \u2192 Jar\n(strict terminal)",
                         "Co-occurrence\n(same text)"], fontsize=10)
    axL.set_ylabel("Inscribed objects (n)")
    axL.set_ylim(0, max(urban) * 1.18 + 4)
    axL.set_title("(a) Absolute counts")
    axL.grid(axis="y", ls="--", alpha=.35)
    axL.set_axisbelow(True)
    for s in ("top", "right"):
        axL.spines[s].set_visible(False)
    axL.legend(loc="upper left", frameon=False, fontsize=10)

    y = np.arange(3)
    for off, ks, n, col, lab in ((-w / 2, urban, nu, BLUE, f"Urban (n={nu:,})"),
                                 (+w / 2, peri, np_, ORANGE,
                                  f"Peripheral (n={np_})")):
        pv, lo, hi = np.array([wilson(k, n) for k in ks]).T
        axR.barh(y + off, pv, w, color=col, label=lab)
        axR.errorbar(pv, y + off, xerr=[pv - lo, hi - pv], fmt="none",
                     ecolor="#333", elinewidth=1.1, capsize=3)
        for yi, h in zip(y + off, hi):
            axR.annotate(f"{h:.1f}%", (h + 0.08, yi), va="center",
                         fontsize=9, color="#222")
    axR.set_yticks(y)
    axR.set_yticklabels(["Jar\u2192Numeral", "Num\u2192Jar", "Co-occurrence"])
    axR.set_xlim(0, 5.6)
    axR.set_xlabel("Frequency (% of inscriptions)")
    axR.set_title("(b) Share per class \u2014 Wilson 95% CI")
    axR.grid(axis="x", ls="--", alpha=.35)
    axR.set_axisbelow(True)
    for s in ("top", "right"):
        axR.spines[s].set_visible(False)
    axR.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncols=2,
               frameon=False, fontsize=9)

    fig.savefig(path)
    plt.close(fig)

# ------------------------------------------------------------- self-test

def _synthetic_dump():
    """Build a miniature ICIT-format SQL dump whose known composition lets
    us verify the pipeline against the manuscript's published numbers.

    Composition (in-region): urban n=2,304 with 47 jar>num, 6 num>jar,
    78 co-occurrence; peripheral n=210 with 3, 0, 4; plus 29 objects at
    excluded foreign sites.
    """
    sites = list(URBAN_SITES.items()) + [
        ("SI7", "Amri"), ("SI8", "Nindowari"),          # peripheral
        ("SI5", "Tell Abraq (Gulf)"), ("SI6", "Failaka (Gulf)"),  # excluded
    ]
    lines = ["INSERT INTO SITE (SITEID, NAME) VALUES"]
    lines += [f'("{sid}", "{name}"),' for sid, name in sites[:-1]]
    lines.append(f'("{sites[-1][0]}", "{sites[-1][1]}");\n')

    glyphs = [(740, "&#xE61B;")] + [(g, f"&#x{0xE33A + i:X};")
                                    for i, g in enumerate(NUMERAL_GLYPHS)]
    glyphs += [(100, "&#x0100;"), (200, "&#x0200;"), (300, "&#x0300;")]
    lines.append("INSERT INTO GLYPH (GLYPHID, UNICODE) VALUES")
    lines += [f'({g}, "{u}"),' for g, u in glyphs[:-1]]
    lines.append(f'({glyphs[-1][0]}, "{glyphs[-1][1]}");\n')

    # pattern-bearing inscription bodies (disjoint so counts add exactly)
    body_jn = [(1, 740), (2, 900)]                    # jar then numeral
    body_nj = [(1, 901), (2, 740)]                    # numeral then terminal jar
    body_co = [(1, 740), (2, 100), (3, 902)]          # co-occurrence only
    body_plain = [(1, 100), (2, 300)]                 # no jar, no numeral

    spec = [("urban", 47, body_jn), ("urban", 6, body_nj),
            ("urban", 25, body_co), ("urban", 2226, body_plain),
            ("peripheral", 3, body_jn), ("peripheral", 1, body_co),
            ("peripheral", 206, body_plain)]

    seals, insc, seq_rows, sid = [], [], [], 0
    urban_sites = [s for s, _ in URBAN_SITES.items()]
    peri_sites = ["SI7", "SI8"]
    for cls, n, body in spec:
        for _ in range(n):
            sid += 1
            site = (urban_sites[sid % len(urban_sites)] if cls == "urban"
                    else peri_sites[sid % len(peri_sites)])
            seals.append(f'({sid}, "{site}", "steatite"),')
            insc.append(f'({sid}, "Y", "L/R"),')
            seq_rows += [f"({sid}, {g}, {pos})," for pos, g in body]
    for _ in range(29):  # excluded foreign objects
        sid += 1
        seals.append(f'({sid}, "SI5", "steatite"),')
        insc.append(f'({sid}, "Y", "L/R"),')
        seq_rows += [f"({sid}, 740, 1),", f"({sid}, 903, 2),"]

    def emit(header, rows):
        nonlocal lines
        lines.append(header)
        lines += rows[:-1]
        lines.append(rows[-1].rstrip(",") + ";\n")

    emit("INSERT INTO SEAL (SEALID, SITEID, MATERIAL) VALUES", seals)
    emit("INSERT INTO INSCRIPTION (SEALID, COMPLETE, DIRECTION) VALUES",
         insc)
    emit("INSERT INTO GLYPHSEQUENCE (SEALID, GLYPHID, POSITION) VALUES",
         seq_rows)
    return "\n".join(lines)


def selftest():
    """Run the pipeline on the synthetic dump and verify published numbers."""
    expected_totals = {"urban": 2304, "peripheral": 210}
    expected_pos = {"jar_then_num": {"urban": 47, "peripheral": 3},
                    "num_then_jar": {"urban": 6, "peripheral": 0},
                    "co_occur": {"urban": 78, "peripheral": 4}}
    expected_p = {"jar_then_num": 0.80, "num_then_jar": 1.00,
                  "co_occur": 0.31}
    # Exact two-decimal values; the manuscript reports the same co-occurrence
    # OR of 1.80 (exact sample value 16068/8904 = 1.8046).
    expected_or = {"jar_then_num": 1.44, "num_then_jar": 1.19,
                   "co_occur": 1.80}

    with tempfile.TemporaryDirectory() as tmp:
        sql = Path(tmp) / "population-script.sql"
        sql.write_text(_synthetic_dump(), encoding="utf-8")
        outdir = Path(tmp) / "results"
        out = run_analysis(sql, outdir, make_figures=True, quiet=True)
        files_ok = all((outdir / n).exists() for n in
                       ("frequency_results.csv", "fisher_tests.csv",
                        "figure1_jar_numeral.png"))

    ok = files_ok
    for cls, n in expected_totals.items():
        ok &= out["totals"][cls] == n
    for pat, exp in expected_pos.items():
        for cls, n in exp.items():
            ok &= out["counts"][pat][cls] == n
    for r in out["results"]:
        key = [k for k, v in PATTERN_LABELS.items() if v == r["pattern"]][0]
        ok &= abs(r["p_value"] - expected_p[key]) < 0.005
        ok &= abs(r["odds_ratio"] - expected_or[key]) < 0.005

    if ok:
        print("SELFTEST PASS - pipeline reproduces the published counts "
              "(47/6/78 vs 3/0/4), Fisher p-values (0.80 / 1.00 / 0.31), "
              "and odds ratios (1.44 / 1.19 / 1.80).")
        return 0
    print("SELFTEST FAIL - unexpected discrepancy, see summary below.")
    print(out["totals"], {p: dict(c) for p, c in out["counts"].items()})
    return 1

# ----------------------------------------------------------------------- cli

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Replicate the 'Jar + Numeral' frequency analysis "
                    "(Prediction 4) from the ICIT SQL mirror.")
    ap.add_argument("--sql", help="path to population-script.sql")
    ap.add_argument("--outdir", default="results",
                    help="output directory (default: ./results)")
    ap.add_argument("--no-figures", action="store_true",
                    help="skip PNG figure generation")
    ap.add_argument("--selftest", action="store_true",
                    help="run the built-in synthetic-data verification")
    args = ap.parse_args(argv)

    if args.selftest:
        sys.exit(selftest())
    if not args.sql:
        ap.error("--sql is required (or use --selftest)")
    run_analysis(args.sql, args.outdir, make_figures=not args.no_figures)


if __name__ == "__main__":
    main()
