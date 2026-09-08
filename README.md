# Replication Package: The Climate-Resilience Ledger

Companion code, simulation modeling, and preprints for the manuscript:  
**"The Climate-Resilience Ledger: Reinterpreting the Indus Script as an Ecological Survival Technology"** (Version 2, submitted to the *Journal of Archaeological Science* / *Nature Ecology & Evolution*).

This repository has been expanded to include a complete **statistical power verification suite and Monte Carlo simulation toolkit** to address the sampling imbalances in the Interactive Corpus of Indus Texts (ICIT) and provide a quantitative roadmap for future archaeological excavations.

---

## 1. Repository Structure

| Directory / File | Description |
| :--- | :--- |
| **`manuscript/`** | |
| ├── `zenodo_preprint_v2.pdf` | Academic preprint typeset in LaTeX with advanced statistical expansions. |
| ├── `journal_submission_package.md` | Abstract, cover letter, and peer-review defense guide. |
| ├── `archaeological_excavation_proposal.md` | Targeted field proposal outlining earthwork and ceramic sorting logistics. |
| **`analysis/`** | |
| ├── `analyze_icit.py` | Original script to parse ICIT SQL mirror, classify settlements, and run Fisher's exact tests. |
| ├── `ledger_power_simulator.py` | **[NEW]** Interactive Monte Carlo simulator for statistical power sweeps. |
| **`results/`** | |
| ├── `simulated_power_frontiers.png` | Plot charting simulated statistical power vs. peripheral sample size. |
| ├── `simulated_archaeological_scenarios.csv` | Grid search dataset mapping 15 distinct sampling tiers. |
| ├── `frequency_results.csv` | Point estimates and counts for the three "Jar + Numeral" variants. |
| ├── `fisher_tests.csv` | 2x2 contingency tables and exact p-values. |
| ├── `requirements.txt` | Python dependencies. |

---

## 2. Advanced Statistical Power Simulation Tool

Because the peripheral sample size in the ICIT is highly constrained ($n_P = 210$, representing only 8.4% of the corpus), asymptotic approximations are unreliable and conventional tests are severely underpowered. 

`ledger_power_simulator.py` uses high-fidelity **Monte Carlo simulations** to generate virtual corpora and compute exact empirical statistical power ($1 - eta$) and Type II error rates ($eta$). It bypasses the "zero-cell" division issues of standard Wald approximations.

### Features
* **Point Simulation Mode:** Simulates a single configuration of urban and peripheral sample sizes for $N$ trials.
* **Grid Sweep Mode:** Evaluates statistical power across a spectrum of peripheral sample sizes, writing a CSV results table and a publication-quality chart.

---

## 3. Quickstart & Setup

### Setup the Environment
Requires Python 3.9+ with virtual environment recommended:
```bash
# Clone and enter the repository
git clone https://github.com/your-username/climate-resilience-ledger.git
cd climate-resilience-ledger

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Point Power Simulator
Estimate the true power of the current sample size (1,000 Monte Carlo runs):
```bash
python analysis/ledger_power_simulator.py simulate --variant co_occurrence --simulations 1000
```

### Execute a Sampling Sweep (Grid Search)
Model power curves from $n_P = 100$ to $n_P = 3,000$ to locate the 80% power frontier:
```bash
python analysis/ledger_power_simulator.py grid --variant co_occurrence --simulations 2000 --output_csv results/simulated_archaeological_scenarios.csv --output_png results/simulated_power_frontiers.png
```
*Outputs written to `results/simulated_archaeological_scenarios.csv` and `results/simulated_power_frontiers.png`.*

---

## 4. Empirical Statistical Power Summary

Using 2,000-run Monte Carlo simulations, we mapped the statistical power curves for the three "Jar + Numeral" variants:

* **Canonical (*Jar → Numeral*):** Power is capped at **10.0%** under current sampling parameters due to a narrow proportion difference ($2.04\%$ vs. $1.43\%$) creating a "power ceiling." Resolving this requires an equal scaling of both groups to $n_U = n_P = 7,103$.
* **Co-occurrence:** Power is currently **15.8%** with an **84.2% chance of a Type II error (false negative)**. The simulation establishes that **$n_P = 1,757$ peripheral inscriptions** are required to cross the standard 80% power frontier.
* **Strict Terminal (*Numeral → Jar*):** Currently has a power of **29.4%**. The 80% power frontier is reached at **$n_P = 1,119$ peripheral inscriptions**.

---

## 5. Dependencies (`requirements.txt`)
Ensure these packages are updated in your environment:
```text
matplotlib>=3.7
seaborn>=0.12
numpy>=1.23
scipy>=1.10
pandas>=1.5
```

---

## 6. Citation & Data Attribution
Please cite the companion preprint when utilizing these scripts or models:
```text
Sharma, H. (2026). The Climate-Resilience Ledger: Reinterpreting the Indus Script as an Ecological Survival Technology (Version 2). Zenodo Preprint. https://doi.org/10.5281/zenodo.22649425
```

---
**Contact:** Harshit Sharma — harshit28102@gmail.com
