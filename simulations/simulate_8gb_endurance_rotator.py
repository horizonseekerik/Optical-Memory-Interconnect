"""
simulate_8gb_endurance_rotator.py
Dual-Tier Extreme-Value Statistical Physics & Wear-Leveling Simulation for the 8 GB OMI Architecture.

Physical Hierarchy:
  - 8 GB User Volume = 64 Billion Bits = 1.00 Billion (72, 64) Hsiao SEC-DED Words
  - 75.6 Billion Total Physical 3D Cells (including +12.5% Hsiao Parity and 5% Spare Block Reserve)
  - 5% Autonomous Spare Sector Reserve (50 Million Spare Blocks for dynamic bad-word retirement)
  - Dual-Sided Thermal Highway: Passive conduction in vacuum / fanless space (41.20 C vs 85.0 C hot baseline)
  - Dual-Tier Failure Thresholds:
      Tier 1: 1st Isolated Raw Cell Oxide Breakdown across 75.6 Billion cells (Weibull weakest-link)
      Tier 2: True Functional Subsystem Failure: Exhaustion of Spare Reserve Blocks after Hsiao Multi-Bit Errors
  - Voronoi Micro-Zone Dynamic Rotator: Wear leveling across micro-zones under severe Zipfian write workloads

Azure Cloud Ready: Central India Linux/Windows Free-Tier CPU VM (1-2 vCPUs).
Self-contained, automatic headless execution, saves publication plot and JSON benchmark results.

Author: Deepanshu Bhardwaj
"""

import os
import sys
import time
import json
import numpy as np

# Headless matplotlib backend for headless cloud VM environments
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_8gb_simulation():
    start_time = time.time()
    print("================================================================================")
    print("  OMI 8 GB WEAR-LEVELING & DUAL-TIER ENDURANCE SIMULATION (AZURE CLOUD READY)   ")
    print("================================================================================")

    # -------------------------------------------------------------------------
    # 1. 8 GB Physical Architecture Parameters
    # -------------------------------------------------------------------------
    capacity_gb = 8.0
    user_bits = capacity_gb * 8.0 * 1e9           # 64.0 Billion user bits
    word_size_user = 64                           # 64-bit user word
    word_size_total = 72                          # 72-bit Hsiao SEC-DED word (+8 parity bits)
    
    num_words = user_bits / word_size_user        # 1.00 Billion words (1.00e9)
    ecc_ratio = word_size_total / word_size_user  # 1.125 (12.5% ECC overhead)
    spare_reserve_ratio = 1.05                   # 5.0% spare block reserve
    
    total_physical_cells = user_bits * ecc_ratio * spare_reserve_ratio  # 75.6 Billion cells
    micro_zones = 100                             # Voronoi micro-zones for 8GB single-tile
    
    # Spare block retirement pool:
    # 5% of 1.00 Billion words = 50 Million spare words available for transparent on-the-fly retirement
    spare_words_pool = num_words * 0.05           # 50,000,000 spare words
    
    # -------------------------------------------------------------------------
    # 2. Physics of Oxide Degradation & Arrhenius Clamping (Vacuum / Passive)
    # -------------------------------------------------------------------------
    beta_weibull = 1.85                           # SILC trap percolation shape factor
    eta_cell_baseline = 1.0e6                     # Baseline single-cell scale life at 85 C hot stack (1.0 x 10^6 cycles)
    
    E_a = 0.35                                    # Activation energy (eV) for trap creation in dielectric
    k_B = 8.617333262145e-5                       # Boltzmann constant (eV/K)
    T_hot = 85.0 + 273.15                         # 358.15 K (conventional uncooled/hot stack in vacuum)
    T_omi = 41.20 + 273.15                        # 314.35 K (OMI passive thermal highway)
    
    # Rate_hot / Rate_omi:
    rate_ratio = np.exp((E_a / k_B) * ((1.0 / T_omi) - (1.0 / T_hot)))
    thermal_boost = rate_ratio
    eta_cell_omi = eta_cell_baseline * thermal_boost
    
    print(f"[*] Capacity Volume                 : {capacity_gb:.1f} GB ({user_bits/1e9:.1f} Gbit)")
    print(f"[*] Hsiao SEC-DED Words (72, 64)    : {num_words/1e9:.2f} Billion Words")
    print(f"[*] Total Physical 3D Cells         : {total_physical_cells/1e9:.2f} Billion Cells (incl. ECC & 5% Spares)")
    print(f"[*] 5% Autonomous Spare Word Pool   : {spare_words_pool/1e6:.1f} Million Spare Words")
    print(f"[*] Voronoi Rotator Micro-Zones     : {micro_zones} Active Micro-Zones")
    print(f"[*] Operating Environment           : Passive Conduction in Isolated Vacuum / Space")
    print(f"[*] Hot Uncooled Stack Temp         : {T_hot - 273.15:.1f} C")
    print(f"[*] OMI Clamped Stack Temp          : {T_omi - 273.15:.2f} C")
    print(f"[*] Arrhenius Longevity Multiplier  : {thermal_boost:.3f}x slower oxide degradation in OMI")
    print(f"[*] Single-Cell Scale Life (Hot)    : {eta_cell_baseline:,.0f} cycles (1.00 x 10^6)")
    print(f"[*] Single-Cell Scale Life (OMI)    : {eta_cell_omi:,.0f} cycles ({eta_cell_omi/1e6:.2f} x 10^6)")

    # -------------------------------------------------------------------------
    # 3. Dual-Tier Analytical Failure Probability Curves
    # -------------------------------------------------------------------------
    device_overwrites = np.logspace(0, 7.5, 800)  # 1 to ~30 Million full 8 GB device overwrites
    
    wear_factor_rotator = 1.04   # Voronoi dynamic rotator wear factor (4% peak variance)
    wear_factor_unleveled = 2.80 # Severe Zipfian hot-spotting without rotator (peak cell takes 2.8x wear)
    
    N_cell_omi = device_overwrites * wear_factor_rotator
    N_cell_hot_unleveled = device_overwrites * wear_factor_unleveled
    
    # --- TIER 1: 1st Isolated Raw Cell Breakdown (Weibull Extreme Value) ---
    M_cells = total_physical_cells
    raw_50_hot_exact = (eta_cell_baseline * ((np.log(2.0) / M_cells) ** (1.0 / beta_weibull))) / wear_factor_unleveled
    raw_50_omi_exact = (eta_cell_omi * ((np.log(2.0) / M_cells) ** (1.0 / beta_weibull))) / wear_factor_rotator
    
    exponent_raw_hot = M_cells * ((N_cell_hot_unleveled / eta_cell_baseline) ** beta_weibull)
    prob_raw_1st_cell_hot_unleveled = -np.expm1(-np.clip(exponent_raw_hot, 0.0, 700.0))
    
    exponent_raw_omi = M_cells * ((N_cell_omi / eta_cell_omi) ** beta_weibull)
    prob_raw_1st_cell_omi = -np.expm1(-np.clip(exponent_raw_omi, 0.0, 700.0))
    
    # --- TIER 2: Subsystem Failure (Hsiao Word Multi-Bit Exhaustion + Spare Reserve) ---
    # In each 72-bit word, 1 bad bit is transparently corrected in 38.2 ps.
    # A word experiences an uncorrectable error when >= 2 bits fail in the same 72-bit word.
    # p_word_fail = C(72, 2) * p_bit^2 = 2556 * p_bit^2
    # Expected number of failed words across the 1.00 Billion words:
    # E_failed_words = W_words * p_word_fail
    # Subsystem fails when cumulative failed words exceed the 5% Spare Reserve Pool (50,000,000 words):
    # E_failed_words >= spare_words_pool
    # W_words * 2556 * p_bit^2 = spare_words_pool
    # p_bit_crit = sqrt(spare_words_pool / (W_words * 2556)) = sqrt(0.05 / 2556) = 4.423e-3
    # N_cell_endurance = eta * (p_bit_crit)^(1/beta)
    W_words = num_words
    binom_72_2 = 72 * 71 / 2.0  # 2556
    
    # Critical bit error rate for spare exhaustion:
    p_bit_crit_spares = np.sqrt(spare_words_pool / (W_words * binom_72_2))
    
    # Subsystem endurance until 5% spare exhaustion:
    subsys_50_hot_spares = (eta_cell_baseline * (p_bit_crit_spares ** (1.0 / beta_weibull))) / wear_factor_unleveled
    subsys_50_omi_spares = (eta_cell_omi * (p_bit_crit_spares ** (1.0 / beta_weibull))) / wear_factor_rotator
    
    # Also calculate 1st uncorrected word before spares (pure single-word Hsiao threshold):
    p_bit_crit_1st_word = np.sqrt(np.log(2.0) / (W_words * binom_72_2))
    subsys_1st_word_omi = (eta_cell_omi * (p_bit_crit_1st_word ** (1.0 / beta_weibull))) / wear_factor_rotator
    
    # Probability distribution of spare exhaustion (Poisson / Normal tail around mean):
    p_bit_omi = -np.expm1(-np.clip((N_cell_omi / eta_cell_omi) ** beta_weibull, 0.0, 700.0))
    p_bit_hot = -np.expm1(-np.clip((N_cell_hot_unleveled / eta_cell_baseline) ** beta_weibull, 0.0, 700.0))
    
    expected_defects_omi = W_words * binom_72_2 * (p_bit_omi ** 2)
    expected_defects_hot = W_words * binom_72_2 * (p_bit_hot ** 2)
    
    # Sigmoid approximation to cumulative normal distribution for spare exhaustion
    z_omi = (expected_defects_omi - spare_words_pool) / (np.sqrt(spare_words_pool) + 1e-9)
    prob_subsystem_fail_omi = 0.5 * (1.0 + np.tanh(z_omi / (np.sqrt(2.0) * 10.0)))
    
    z_hot = (expected_defects_hot - spare_words_pool) / (np.sqrt(spare_words_pool) + 1e-9)
    prob_subsystem_fail_hot = 0.5 * (1.0 + np.tanh(z_hot / (np.sqrt(2.0) * 10.0)))

    print("\n--- Extreme-Value Endurance Benchmarks (Full 8 GB Device Overwrites) ---")
    print(f"[*] TIER 1 - 50% Median 1st Raw Cell Failure (Hot Legacy, Unleveled) : {raw_50_hot_exact:,.0f} Full Overwrites")
    print(f"[*] TIER 1 - 50% Median 1st Raw Cell Failure (OMI 41.2 C + Rotator)   : {raw_50_omi_exact:,.0f} Full Overwrites")
    print(f"[*] TIER 2A - 1st Uncorrectable Word Prior to Spares (OMI 41.2 C)     : {subsys_1st_word_omi:,.0f} Full Overwrites")
    print(f"[*] TIER 2B - 50% Functional Failure Post-Spares (Hot Legacy)         : {subsys_50_hot_spares:,.0f} Full Overwrites ({subsys_50_hot_spares*8/1e3:,.1f} TBW)")
    print(f"[*] TIER 2B - 50% Functional Failure Post-Spares (OMI 41.2 C)         : {subsys_50_omi_spares:,.0f} Full Overwrites ({subsys_50_omi_spares*8/1e3:,.1f} TBW)")

    # -------------------------------------------------------------------------
    # 4. Voronoi Micro-Zone Dynamic Rotator Monte Carlo Simulation (100 Zones)
    # -------------------------------------------------------------------------
    print("\n[*] Running 10,000,000 Write Allocation Monte Carlo on 100 Voronoi Micro-Zones...")
    np.random.seed(42)
    n_zones = micro_zones
    total_sim_writes = 10_000_000
    
    # Severe Zipfian distribution (alpha = 0.85, 80/20 rule)
    ranks = np.arange(1, n_zones + 1)
    zipf_weights = 1.0 / (ranks ** 0.85)
    zipf_probs = zipf_weights / np.sum(zipf_weights)
    
    # Unleveled (Legacy Memory: static address mapping)
    unleveled_zone_wear = np.random.multinomial(total_sim_writes, zipf_probs)
    
    # OMI Rotator (Dynamic wear-leveling with rotating zone pointer offset)
    leveled_zone_wear = np.zeros(n_zones, dtype=np.float64)
    epochs = 200
    epoch_writes = total_sim_writes // epochs
    for epoch in range(epochs):
        offset = epoch % n_zones
        shifted_probs = np.roll(zipf_probs, offset)
        leveled_zone_wear += np.random.multinomial(epoch_writes, shifted_probs)
        
    variance_unleveled = np.std(unleveled_zone_wear / np.mean(unleveled_zone_wear)) * 100.0
    variance_leveled = np.std(leveled_zone_wear / np.mean(leveled_zone_wear)) * 100.0
    
    print(f"[*] Unleveled Wear Disparity (StdDev): {variance_unleveled:.2f}% (Peak Zone: {np.max(unleveled_zone_wear)/np.mean(unleveled_zone_wear):.2f}x average)")
    print(f"[*] OMI Dynamic Rotator Disparity    : {variance_leveled:.2f}% (Within ±{variance_leveled:.1f}% uniform envelope)")

    # -------------------------------------------------------------------------
    # 5. Generate 4-Panel Verification Dashboard Plot
    # -------------------------------------------------------------------------
    print("\n[*] Generating High-Resolution Dashboard Plot...")
    fig, axs = plt.subplots(2, 2, figsize=(16, 11), dpi=300)
    fig.patch.set_facecolor('#ffffff')

    color_omi = '#0055cc'
    color_omi_ecc = '#009944'
    color_hot_raw = '#cc0000'
    color_hot_ecc = '#e65c00'
    color_accent = '#7700bb'

    # Panel (a): Dual-Tier Failure Probabilities vs Full Device Overwrites
    ax = axs[0, 0]
    ax.semilogx(device_overwrites, prob_raw_1st_cell_hot_unleveled, color=color_hot_raw, lw=2.0, linestyle=':', label='Raw 1st Cell Puncture (Hot 85 C, Unleveled)')
    ax.semilogx(device_overwrites, prob_raw_1st_cell_omi, color=color_omi, lw=2.2, linestyle='--', label='Raw 1st Cell Puncture (OMI 41.20 C + Rotator)')
    ax.semilogx(device_overwrites, prob_subsystem_fail_hot, color=color_hot_ecc, lw=2.2, linestyle='-.', label='True Subsystem Failure (Hot 85 C Stack)')
    ax.semilogx(device_overwrites, prob_subsystem_fail_omi, color=color_omi_ecc, lw=3.2, label='True OMI Subsystem Failure (41.20 C + Spares)')

    ax.axhline(0.5, color='gray', linestyle=':', lw=1.2, label='50% Failure Threshold')
    ax.scatter([subsys_50_omi_spares], [0.5], color=color_omi_ecc, s=120, zorder=5)
    ax.annotate(f'OMI Subsystem 50% Median:\n{subsys_50_omi_spares:,.0f} Full Overwrites\n({subsys_50_omi_spares*8/1e3:,.1f} TB Written)',
                xy=(subsys_50_omi_spares, 0.5), xytext=(subsys_50_omi_spares * 0.05, 0.72),
                arrowprops=dict(facecolor=color_omi_ecc, shrink=0.08, width=1.5, headwidth=6),
                fontsize=9.2, fontweight='bold', color=color_omi_ecc)

    ax.set_title('(a) Dual-Tier Endurance: Raw Cell Puncture vs Hsiao+Spare Exhaustion (8 GB)', fontsize=10.5, pad=10)
    ax.set_xlabel('Cumulative Full-Device Overwrite Cycles (N_dev x 8 GB volume)', fontsize=9.5)
    ax.set_ylabel('Cumulative Failure Probability F(N)', fontsize=9.5)
    ax.set_xlim(1e0, 1e7)
    ax.set_ylim(-0.02, 1.05)
    ax.grid(True, which='both', linestyle='--', alpha=0.4)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.95)

    # Panel (b): 100-Zone Voronoi Wear-Leveling Rotator Uniformity
    ax = axs[0, 1]
    zone_indices = np.arange(n_zones)
    ax.plot(zone_indices, unleveled_zone_wear / np.mean(unleveled_zone_wear), color=color_hot_raw, alpha=0.75, lw=1.6, label='Without Rotator (Zipfian Hot-Spot Degradation)')
    ax.plot(zone_indices, leveled_zone_wear / np.mean(leveled_zone_wear), color=color_omi, lw=2.4, label='With OMI Dynamic Rotator (Uniform Wear)')
    ax.axhline(1.0, color='black', linestyle='--', lw=1.2, label='Ideal Wear Balance (=1.00)')
    ax.fill_between(zone_indices, 0.96, 1.04, color=color_omi, alpha=0.18, label='+-4% Wear Balance Envelope')
    
    ax.set_title('(b) Micro-Zone Wear Balance Across 100 Voronoi Zones (10^7 Allocations)', fontsize=10.5, pad=10)
    ax.set_xlabel('Voronoi Micro-Zone Index (0 to 99)', fontsize=9.5)
    ax.set_ylabel('Normalized Micro-Zone Wear Intensity (W_i / W_mean)', fontsize=9.5)
    ax.set_xlim(0, n_zones - 1)
    ax.set_ylim(0.0, 3.5)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(loc='upper right', fontsize=8.8, framealpha=0.95)

    # Panel (c): Arrhenius Temperature Clamping in Vacuum/Space
    ax = axs[1, 0]
    temps_c = np.linspace(25.0, 100.0, 250)
    temps_k = temps_c + 273.15
    rel_rates = np.exp((E_a / k_B) * ((1.0 / T_hot) - (1.0 / temps_k)))
    
    ax.plot(temps_c, rel_rates, color=color_accent, lw=2.5, label='Oxide Trap Creation Rate (E_a = 0.35 eV)')
    ax.scatter([41.20], [np.exp((E_a / k_B) * ((1.0 / T_hot) - (1.0 / T_omi)))], color=color_omi, s=140, zorder=5, label='OMI Passive Clamped (41.20 C, Rate = 0.21)')
    ax.scatter([85.0], [1.0], color=color_hot_raw, s=140, zorder=5, label='Conventional Hot Stack (85.0 C, Rate = 1.00)')
    
    ax.annotate(f'Passive Highway Advantage:\n{thermal_boost:.2f}x Slower Oxide Aging!',
                xy=(41.20, np.exp((E_a / k_B) * ((1.0 / T_hot) - (1.0 / T_omi)))),
                xytext=(48, 0.45),
                arrowprops=dict(facecolor=color_omi, shrink=0.08, width=1.5, headwidth=6),
                fontsize=9.5, fontweight='bold', color=color_omi)
    
    ax.set_title('(c) Arrhenius Longevity Boost in Vacuum via Thermal Highway Conduction', fontsize=10.5, pad=10)
    ax.set_xlabel('Peak Core Operating Junction Temperature (deg C)', fontsize=9.5)
    ax.set_ylabel('Normalized Dielectric SILC Degradation Rate', fontsize=9.5)
    ax.set_xlim(25, 100)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(loc='upper left', fontsize=8.8, framealpha=0.95)

    # Panel (d): Absolute Overwrite Endurance Comparison (Log Scale)
    ax = axs[1, 1]
    categories = [
        'Tier 1: 1st Raw Cell\n(Hot 85 C, Unleveled)',
        'Tier 1: 1st Raw Cell\n(OMI 41.2 C + Rotator)',
        'Tier 2: Subsystem Fail\n(Hot 85 C, Unleveled)',
        'Tier 2: Subsystem Fail\n(OMI 41.2 C + Rotator)'
    ]
    vals = [raw_50_hot_exact, raw_50_omi_exact, subsys_50_hot_spares, subsys_50_omi_spares]
    bar_colors = [color_hot_raw, color_omi, color_hot_ecc, color_omi_ecc]
    
    bars = ax.bar(categories, vals, color=bar_colors, edgecolor='black', lw=1.2, width=0.55)
    ax.set_yscale('log')
    ax.set_ylim(1e0, 1e7)
    
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f'{h:,.0f}\nOverwrites',
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 5), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8.8, fontweight='bold')
        
    ax.set_title('(d) Absolute Physical Limits: 50% Median Full Device Overwrites', fontsize=10.5, pad=10)
    ax.set_ylabel('Cumulative Full 8 GB Device Overwrites', fontsize=9.5)
    ax.grid(True, which='both', axis='y', linestyle='--', alpha=0.4)
    
    plt.tight_layout()
    
    # Save output plot
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    os.makedirs(output_dir, exist_ok=True)
    out_plot = os.path.join(output_dir, "omi_8gb_endurance_wear_rotator.png")
    plt.savefig(out_plot, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save benchmark JSON
    results = {
        "architecture": "8 GB Optical Memory Interconnect (OMI)",
        "user_capacity_gb": capacity_gb,
        "total_physical_cells": total_physical_cells,
        "hsiao_words_count": num_words,
        "spare_words_pool_count": spare_words_pool,
        "voronoi_micro_zones": micro_zones,
        "clamped_temperature_c": 41.20,
        "hot_temperature_c": 85.00,
        "thermal_longevity_boost": float(f"{thermal_boost:.3f}"),
        "tier1_raw_cell_first_failure_50pct_hot_overwrites": float(raw_50_hot_exact),
        "tier1_raw_cell_first_failure_50pct_omi_overwrites": float(raw_50_omi_exact),
        "tier2_subsystem_spare_exhaustion_50pct_hot_overwrites": float(subsys_50_hot_spares),
        "tier2_subsystem_spare_exhaustion_50pct_omi_overwrites": float(subsys_50_omi_spares),
        "endurance_formula_overwrites": f"{subsys_50_omi_spares:,.0f} full 8 GB device writes ({subsys_50_omi_spares*8/1e3:,.1f} TB Total Bytes Written)",
        "plot_path": out_plot,
        "elapsed_seconds": time.time() - start_time
    }
    
    out_json = os.path.join(os.path.dirname(__file__), "omi_8gb_endurance_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\n[SUCCESS] Generated 4-Panel Verification Dashboard: {out_plot}")
    print(f"[SUCCESS] Exported Benchmark Metrics JSON: {out_json}")
    print(f"[SUCCESS] Total Simulation Execution Time: {results['elapsed_seconds']:.2f} seconds")
    print("================================================================================")
    print(f"  FINAL VERDICT: 8 GB OMI ENDURANCE = {subsys_50_omi_spares:,.0f} FULL OVERWRITES")
    print(f"  TOTAL TERABYTES WRITTEN (TBW)     = {subsys_50_omi_spares * 8.0 / 1e3:,.1f} TBW")
    print("================================================================================")

if __name__ == "__main__":
    run_8gb_simulation()
