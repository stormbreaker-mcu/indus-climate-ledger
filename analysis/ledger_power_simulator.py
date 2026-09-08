#!/usr/bin/env python3
"""
The Climate-Resilience Ledger (IVC) - Statistical Power Simulator & Scenario Planner
Author: Gemini Notebook (on behalf of Harshit Sharma's research)
Date: September 2026

This tool runs high-fidelity Monte Carlo simulations and analytical power calculations 
for testing the "Climate-Resilience Ledger" hypothesis. Specifically, it models the 
statistical power and Type II error rates when comparing the proportion of rationing-related 
grapheme combinations between Urban and Peripheral archaeological sites in the Indus Valley.
"""

import os
import sys
import argparse
import numpy as np
import scipy.stats as stats
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Baseline parameters from the original Harshit Sharma paper (September 2026)
BASELINES = {
    "canonical": {
        "name": "Jar -> Numeral (Canonical Suffix)",
        "urban_count": 47,
        "urban_total": 2304,
        "periph_count": 3,
        "periph_total": 210,
        "p_u": 47 / 2304,
        "p_p": 3 / 210
    },
    "strict_terminal": {
        "name": "Numeral -> Jar (Strict Terminal)",
        "urban_count": 6,
        "urban_total": 2304,
        "periph_count": 0,
        "periph_total": 210,
        "p_u": 6 / 2304,
        "p_p": 0 / 210
    },
    "co_occurrence": {
        "name": "Jar & Numeral Co-occurrence (Anywhere in text)",
        "urban_count": 78,
        "urban_total": 2304,
        "periph_count": 4,
        "periph_total": 210,
        "p_u": 78 / 2304,
        "p_p": 4 / 210
    }
}

def setup_cli():
    parser = argparse.ArgumentParser(
        description="Run statistical power and Type II error simulations for the Indus Script Climate-Resilience Ledger.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands to run")
    
    # Single simulation parser
    sim_parser = subparsers.add_parser("simulate", help="Run a single Monte Carlo power simulation for a specific variant")
    sim_parser.add_argument("--variant", choices=["canonical", "strict_terminal", "co_occurrence"], default="co_occurrence",
                           help="Which grapheme variant to model (default: co_occurrence)")
    sim_parser.add_argument("--n_urban", type=int, default=2304, help="Urban sample size (default: 2304)")
    sim_parser.add_argument("--n_peripheral", type=int, default=210, help="Peripheral sample size (default: 210)")
    sim_parser.add_argument("--p_urban", type=float, help="Custom Urban proportion (0.0 to 1.0)")
    sim_parser.add_argument("--p_peripheral", type=float, help="Custom Peripheral proportion (0.0 to 1.0)")
    sim_parser.add_argument("--simulations", type=int, default=5000, help="Number of Monte Carlo iterations (default: 5000)")
    sim_parser.add_argument("--alpha", type=float, default=0.05, help="Significance level (default: 0.05)")
    
    # Grid search parser
    grid_parser = subparsers.add_parser("grid", help="Perform a grid search across multiple peripheral sample sizes")
    grid_parser.add_argument("--variant", choices=["canonical", "strict_terminal", "co_occurrence"], default="co_occurrence",
                             help="Which grapheme variant to model (default: co_occurrence)")
    grid_parser.add_argument("--n_urban", type=int, default=2304, help="Urban sample size (default: 2304)")
    grid_parser.add_argument("--min_periph", type=int, default=100, help="Minimum peripheral sample size to test (default: 100)")
    grid_parser.add_argument("--max_periph", type=int, default=3000, help="Maximum peripheral sample size to test (default: 3000)")
    grid_parser.add_argument("--steps", type=int, default=15, help="Number of intermediate steps in the grid (default: 15)")
    grid_parser.add_argument("--simulations", type=int, default=3000, help="Monte Carlo simulations per step (default: 3000)")
    grid_parser.add_argument("--alpha", type=float, default=0.05, help="Significance level (default: 0.05)")
    grid_parser.add_argument("--output_csv", type=str, default="results/simulated_archaeological_scenarios.csv",
                             help="Path to save simulation results CSV")
    grid_parser.add_argument("--output_png", type=str, default="results/simulated_power_frontiers.png",
                             help="Path to save power frontier plot")

    return parser

def run_monte_carlo(n_u, p_u, n_p, p_p, alpha=0.05, n_sims=5000):
    """
    Simulates the power of Fisher's exact test using Monte Carlo drawing.
    This is highly robust for zero-count bins (like the strict terminal variant).
    """
    rejections = 0
    
    # Pre-draw all binomial trials for speed
    x_u_samples = np.random.binomial(n_u, p_u, n_sims)
    x_p_samples = np.random.binomial(n_p, p_p, n_sims)
    
    for i in range(n_sims):
        x_u = x_u_samples[i]
        x_p = x_p_samples[i]
        
        # Contingency table:
        #           Urban           Peripheral
        # Ration    x_u             x_p
        # Other     n_u - x_u       n_p - x_p
        table = [
            [x_u, x_p],
            [n_u - x_u, n_p - x_p]
        ]
        
        # Two-tailed Fisher's Exact Test
        _, p_val = stats.fisher_exact(table)
        if p_val < alpha:
            rejections += 1
            
    power = rejections / n_sims
    type_ii_error = 1.0 - power
    return power, type_ii_error

def main():
    parser = setup_cli()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
        
    if args.command == "simulate":
        v_data = BASELINES[args.variant]
        p_u = args.p_urban if args.p_urban is not None else v_data["p_u"]
        p_p = args.p_peripheral if args.p_peripheral is not None else v_data["p_p"]
        
        print("="*60)
        print("           CLIMATE-RESILIENCE LEDGER: POWER SIMULATION")
        print("="*60)
        print(f"Variant:            {v_data['name']}")
        print(f"Urban Sample (n_U): {args.n_urban}  (p_U = {p_u:.4%})")
        print(f"Periph Sample (n_P):{args.n_peripheral}  (p_P = {p_p:.4%})")
        print(f"Alpha level:        {args.alpha}")
        print(f"Monte Carlo Runs:   {args.simulations:,}")
        print("-"*60)
        print("Running Monte Carlo simulation...")
        
        power, beta = run_monte_carlo(args.n_urban, p_u, args.n_peripheral, p_p, args.alpha, args.simulations)
        
        print("="*60)
        print("                           RESULTS")
        print("="*60)
        print(f"Statistical Power (1 - Beta):  {power:.4%}  (Chance of detecting true difference)")
        print(f"Type II Error Rate (Beta):      {beta:.4%}  (Chance of false negative)")
        print(f"Statistical Significance:      {'YES (>=80% power)' if power >= 0.8 else 'NO (Underpowered)'}")
        print("="*60)
        print("Interpretation:")
        if power < 0.8:
            print(f"This design is heavily underpowered. You have a {beta:.1%} chance of failing")
            print("to detect a true difference even if the urban enrichment hypothesis is correct.")
            print("To resolve this, you must discover and catalog more peripheral inscriptions.")
        else:
            print("This design has sufficient power (>=80%) to detect the specified difference.")
            print("Any non-significant archaeological result here represents strong evidence for the null.")
        print("="*60)

    elif args.command == "grid":
        print("="*60)
        print("         CLIMATE-RESILIENCE LEDGER: GRID POWER SEARCH")
        print("="*60)
        v_data = BASELINES[args.variant]
        print(f"Target Variant:      {v_data['name']}")
        print(f"Urban Sample (n_U):  {args.n_urban} (Fixed)")
        print(f"Peripheral (n_P):    Testing range from {args.min_periph} to {args.max_periph}")
        print(f"Steps:               {args.steps}")
        print(f"Simulations/step:    {args.simulations:,}")
        print("-"*60)
        
        periph_sizes = np.linspace(args.min_periph, args.max_periph, args.steps, dtype=int)
        results = []
        
        print("Processing grid search...")
        for i, n_p in enumerate(periph_sizes):
            sys.stdout.write(f"\rStep {i+1}/{args.steps}: modeling n_P = {n_p:<5}")
            sys.stdout.flush()
            
            # Run simulation
            power, beta = run_monte_carlo(args.n_urban, v_data["p_u"], n_p, v_data["p_p"], args.alpha, args.simulations)
            results.append({
                "n_urban": args.n_urban,
                "p_urban_pct": v_data["p_u"] * 100,
                "n_peripheral": n_p,
                "p_peripheral_pct": v_data["p_p"] * 100,
                "simulations": args.simulations,
                "alpha": args.alpha,
                "statistical_power": power,
                "type_ii_error": beta
            })
            
        print("\nGrid search complete. Saving dataset...")
        df = pd.DataFrame(results)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(args.output_csv) or ".", exist_ok=True)
        df.to_csv(args.output_csv, index=False)
        print(f"Saved CSV results table to: {args.output_csv}")
        
        # Generate plot
        print("Generating power curve plot...")
        sns.set_theme(style="whitegrid", palette="colorblind", font="DejaVu Sans")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot power curve
        sns.lineplot(data=df, x="n_peripheral", y="statistical_power", marker="o", linewidth=2.5, ax=ax, color="blue")
        
        # Reference line for 80% power
        ax.axhline(0.80, color="red", linestyle="--", linewidth=1.5, label="80% Standard Power Threshold")
        
        # Identify crossing point
        crossing_df = df[df["statistical_power"] >= 0.80]
        if not crossing_df.empty:
            target_n_p = crossing_df.iloc[0]["n_peripheral"]
            ax.axvline(target_n_p, color="green", linestyle=":", linewidth=1.5, 
                       label=f"80% Power Achieved at n_P ≈ {target_n_p:,}")
            # Highlight with a scatter point
            target_power = crossing_df.iloc[0]["statistical_power"]
            ax.scatter([target_n_p], [target_power], color="green", s=100, zorder=5)
            ax.annotate(f"n_P = {target_n_p:,}\nPower = {target_power:.1%}",
                        xy=(target_n_p, target_power),
                        xytext=(target_n_p + (args.max_periph - args.min_periph)*0.05, target_power - 0.1),
                        arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                        fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.3))
            
        # Customize plot
        ax.set_title(f"Required Peripheral Inscriptions for {v_data['name']}\nTargeting 80% Power vs. Type II Error Frontier", 
                     fontsize=12, fontweight="bold", pad=15)
        ax.set_xlabel("Peripheral Sample Size (n_P)")
        ax.set_ylabel("Statistical Power (1 - Beta)")
        ax.set_ylim(0, 1.05)
        ax.legend(loc="lower right")
        sns.despine()
        plt.tight_layout(pad=1.5)
        
        fig.savefig(args.output_png, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Saved visualization to: {args.output_png}")
        print("Done!")

if __name__ == "__main__":
    main()
