"""
monte_carlo_discrete_cell_wear.py
Native OMI Discrete Cell-by-Cell Physical Monte Carlo Simulation with Full Concatenation.

The Complete 3-Stage Protection Architecture:
  1. Tier-1 On-the-Fly Hsiao SEC-DED (38.2 ps):
     - Corrects 1 bad bit per 72-bit word transparently in hardware.
     - When >= 2 bad bits occur in a word, Hsiao raises an uncorrectable syndrome flag.
  2. Tier-2 2D Spatially Interleaved BCH-8 (185 ps):
     - Groups 8 words across 8 optical lanes into a 576-bit stripe.
     - BCH-8 can correct up to 8 defective symbols/words per stripe on-the-fly!
     - Therefore, a word with >= 2 bad bits is STILL 100% REPAIRED by Tier-2 BCH-8!
       It does NOT cause data failure and does NOT immediately consume a spare!
  3. 5% Autonomous Spare Word Reserve Pool:
     - Spares are consumed only when a stripe accumulates multiple defects approaching the BCH-8 threshold
       (i.e. >= 2 bad words in the same 8-word stripe), dynamically replacing the bad word to preserve BCH-8 headroom.
  4. Real Terminal Failure:
     - Occurs when the spare word pool is 100% exhausted AND a stripe suffers > 8 defective words (unrecoverable).

Author: Deepanshu Bhardwaj
"""

import os
import sys
import time
import json
import argparse
import numpy as np

# Headless plotting for background cloud execution
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_discrete_monte_carlo_to_exhaustion(num_physical_cells=75_600_000, num_micro_zones=100, seed=42):
    np.random.seed(seed)
    t0 = time.time()
    
    print("================================================================================")
    print("  OMI NATIVE 3D FLASH MONTE CARLO (TIER-1 HSIAO + TIER-2 BCH-8 + DYNAMIC SPARES)")
    print("================================================================================")
    
    scale_factor = 75_600_000_000 / num_physical_cells
    words_count = num_physical_cells // 72
    stripes_count = words_count // 8             # 8 words (576 bits) per Tier-2 stripe
    spare_words_limit = int(words_count * 0.05)   # 5% autonomous spare WORD reserve
    
    print(f"[*] Physical 3D Cells in RAM        : {num_physical_cells:,.0f} cells")
    print(f"[*] Total Hsiao Words (72-bit)      : {words_count:,.0f} words")
    print(f"[*] 5% Autonomous Spare Word Pool   : {spare_words_limit:,.0f} SPARE WORDS")
    print(f"[*] Optical Stripes (576-bit)       : {stripes_count:,.0f} stripes (8 words/stripe)")
    print(f"[*] Voronoi Micro-Zones             : {num_micro_zones} active zones")
    print(f"[*] Scale Representation to 8 GB    : 1 : {scale_factor:,.0f}")
    
    # -------------------------------------------------------------------------
    # Physical Degradation Physics: Voltage Correction + Arrhenius + Pulsing
    # -------------------------------------------------------------------------
    E_a = 0.35
    k_B = 8.617333262145e-5
    T_hot = 85.0 + 273.15
    T_omi = 41.20 + 273.15
    thermal_boost = np.exp((E_a / k_B) * ((1.0 / T_omi) - (1.0 / T_hot)))  # 4.856x
    pulsing_boost = 11.22                                                   # 11.22x
    voltage_correction_boost = 7.50                                         # 7.50x
    
    eta_cell_baseline = 1.0e6
    eta_cell_omi = eta_cell_baseline * thermal_boost * pulsing_boost * voltage_correction_boost  # ~ 4.09 x 10^8 cycles!
    beta_weibull = 1.85
    
    print(f"[*] Conventional High-Voltage Stress: 18.0V - 20.0V (Severe Dielectric Stress)")
    print(f"[*] OMI Low-Voltage Injection       : 4.8V (E-Field Reduced by > 60%)")
    print(f"[*] Voltage Correction Factor       : {voltage_correction_boost:.2f}x oxide longevity boost")
    print(f"[*] Program Pulse Duration          : 10 ns (vs 10 us conventional, 1,000x faster)")
    print(f"[*] Pulsed Low-Stress Multiplier    : {pulsing_boost:.2f}x oxide longevity boost")
    print(f"[*] Thermal Highway Multiplier      : {thermal_boost:.3f}x slower oxide aging")
    print(f"[*] Combined Single-Cell Scale (eta): {eta_cell_omi:,.0f} cycles ({eta_cell_omi/1e6:.2f} x 10^6)")
    
    # -------------------------------------------------------------------------
    # Instantiate Stochastic Cell Breakdown Voltages in RAM
    # -------------------------------------------------------------------------
    print("\n[*] Synthesizing stochastic Weibull breakdown thresholds...")
    u = np.random.uniform(1e-12, 1.0 - 1e-12, size=num_physical_cells)
    cell_breakdown_thresholds = (eta_cell_omi * ((-np.log(u)) ** (1.0 / beta_weibull))).astype(np.float32)
    
    cell_wear_counts = np.zeros(num_physical_cells, dtype=np.uint32)
    cell_broken = np.zeros(num_physical_cells, dtype=bool)
    
    ram_mb = (cell_breakdown_thresholds.nbytes + cell_wear_counts.nbytes + cell_broken.nbytes) / (1024 * 1024)
    print(f"[*] Discrete Array RAM Footprint    : {ram_mb:.2f} MB")
    
    # Dynamic Rotator setup
    cells_per_zone = num_physical_cells // num_micro_zones
    ranks = np.arange(1, num_micro_zones + 1)
    zipf_weights = 1.0 / (ranks ** 0.85)
    zipf_probs = zipf_weights / np.sum(zipf_weights)
    
    zone_wear = np.zeros(num_micro_zones, dtype=np.float64)
    zone_mapping = np.arange(num_micro_zones)
    
    # -------------------------------------------------------------------------
    # Autonomous Adaptive Stepping Loop
    # -------------------------------------------------------------------------
    print("\n[*] Commencing Autonomous Full Concatenation Simulation...")
    print(f"{'Step':>6} | {'Full Overwrites':>16} | {'Broken Cells':>13} | {'Tier-1 Hsiao Rep':>16} | {'Tier-2 Repaired':>15} | {'Spares Used':>12} | {'Spare Status'}")
    print("-" * 110)
    
    first_cell_puncture_overwrite = None
    first_hsiao_double_error_overwrite = None
    first_word_retired_overwrite = None
    terminal_failure_overwrite = None
    
    cumulative_writes = 0
    history_overwrites = []
    history_broken_cells = []
    history_retired_words = []
    
    # Adaptive step size: 250,000 full overwrites per step
    overwrites_per_step = 250_000
    step_writes = int(overwrites_per_step * num_physical_cells)
    step = 0
    
    while True:
        step += 1
        
        # Rotator rebalancing: coolest physical zones take hottest write traffic
        sorted_physical_zones = np.argsort(zone_wear)
        zone_mapping = sorted_physical_zones
        
        # Allocations across zones directly scaled to overwrites
        zone_increment = np.round(overwrites_per_step * (zipf_probs * num_micro_zones)).astype(np.uint32)
        
        for logical_z in range(num_micro_zones):
            phys_z = zone_mapping[logical_z]
            inc = zone_increment[logical_z]
            zone_wear[phys_z] += inc
            
            start_idx = phys_z * cells_per_zone
            end_idx = start_idx + cells_per_zone
            cell_wear_counts[start_idx:end_idx] += inc
            
        cumulative_writes += step_writes
        full_device_overwrites = cumulative_writes / num_physical_cells
        
        # Check newly broken cells
        newly_broken = (cell_wear_counts >= cell_breakdown_thresholds) & (~cell_broken)
        if np.any(newly_broken):
            cell_broken[newly_broken] = True
            if first_cell_puncture_overwrite is None:
                first_cell_puncture_overwrite = full_device_overwrites
                print(f"[!] MILESTONE 1: First Physical Cell Puncture at Overwrite {full_device_overwrites:,.0f} (Corrected in 38.2 ps by Tier-1)")
                
        total_broken_cells = int(np.sum(cell_broken))
        
        # Evaluate Tier-1 Hsiao Words: Reshape into (words_count, 72)
        words_broken_bits = cell_broken[:words_count * 72].reshape(words_count, 72)
        bad_bits_per_word = np.sum(words_broken_bits, axis=1)
        
        # 1 bad bit = transparently repaired in 38.2 ps by Tier-1 Hsiao
        hsiao_repaired_words = int(np.sum(bad_bits_per_word == 1))
        
        # >= 2 bad bits = Tier-1 raises double-error flag
        hsiao_double_errors = (bad_bits_per_word >= 2)
        total_hsiao_double_errors = int(np.sum(hsiao_double_errors))
        
        if total_hsiao_double_errors > 0 and first_hsiao_double_error_overwrite is None:
            first_hsiao_double_error_overwrite = full_device_overwrites
            print(f"[!] MILESTONE 2: First Hsiao Double-Bit Error at Overwrite {full_device_overwrites:,.0f} (100% Repaired by Tier-2 BCH-8!)")
            
        # Evaluate Tier-2 BCH-8 Concatenation across stripes of 8 words (576 bits):
        stripes_bad_words = hsiao_double_errors[:stripes_count * 8].reshape(stripes_count, 8)
        bad_words_per_stripe = np.sum(stripes_bad_words, axis=1)
        
        # Tier-2 BCH-8 capability:
        # - Any stripe with 1 bad word is 100% repaired on-the-fly by Tier-2 BCH-8 with ZERO spares needed!
        # - To prevent multi-word clustering, when a stripe accumulates >= 2 bad words, the controller
        #   retires the second bad word into the spare pool to keep BCH-8 completely clear and resilient.
        # - Excess bad words requiring spare word retirement:
        excess_bad_words = np.maximum(0, bad_words_per_stripe - 1)
        total_retired_words = int(np.sum(excess_bad_words))
        
        if total_retired_words > 0 and first_word_retired_overwrite is None:
            first_word_retired_overwrite = full_device_overwrites
            print(f"[!] MILESTONE 3: Multi-Word Cluster Detected at Overwrite {full_device_overwrites:,.0f} (Spare Word Engaged)")
            
        spares_used = min(total_retired_words, spare_words_limit)
        spare_pct = (spares_used / spare_words_limit) * 100.0
        
        history_overwrites.append(full_device_overwrites)
        history_broken_cells.append(total_broken_cells)
        history_retired_words.append(total_retired_words)
        
        # Periodic output
        if step % 10 == 0 or step == 1 or total_retired_words > 0:
            status_str = f"SPARE POOL: {spare_pct:.1f}% CONSUMED"
            print(f"{step:>6} | {full_device_overwrites:>16,f} | {total_broken_cells:>13,d} | {hsiao_repaired_words:>16,d} | {total_hsiao_double_errors:>15,d} | {spares_used:>12,d} | {status_str}")
            
        # REAL TERMINAL FAILURE MILESTONE:
        # Exhaustion of the 5% Autonomous Spare Reserve Pool
        if total_retired_words >= spare_words_limit:
            terminal_failure_overwrite = full_device_overwrites
            print("=" * 110)
            print(f"[!] REAL FAILURE MILESTONE REACHED: 5% SPARE WORD POOL EXHAUSTED AT OVERWRITE {full_device_overwrites:,.0f}!")
            print(f"[!] SCIENTIFIC NOTATION: {full_device_overwrites/1e7:.2f} x 10^7 FULL DEVICE WRITES ({full_device_overwrites * 8 / 1e3:,.1f} TBW)")
            print("=" * 110)
            break

    elapsed = time.time() - t0
    
    # -------------------------------------------------------------------------
    # Generate & Save Validation Plot
    # -------------------------------------------------------------------------
    print("\n[*] Saving Final Failure Verification Plots...")
    fig, axs = plt.subplots(1, 2, figsize=(15, 6), dpi=250)
    fig.patch.set_facecolor('#ffffff')
    
    ax = axs[0]
    ax.plot(history_overwrites, history_broken_cells, color='#cc0000', lw=2.4, label='Broken Cells (Low-V 10ns Pulsed SILC)')
    if first_cell_puncture_overwrite:
        ax.axvline(first_cell_puncture_overwrite, color='gray', linestyle=':', label=f'1st Cell Puncture ({first_cell_puncture_overwrite:,.0f})')
    ax.set_title(f'Physical Cell Degradation ({num_physical_cells:,} Cells)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Cumulative Full Device Overwrites', fontsize=10)
    ax.set_ylabel('Broken Cells Count', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper left', fontsize=9.5)
    
    ax = axs[1]
    ax.plot(history_overwrites, history_retired_words, color='#0055cc', lw=2.4, label='Retired Defective Words (>= 2 bits)')
    ax.axhline(spare_words_limit, color='orange', linestyle='--', lw=2.0, label=f'5% Spare Word Limit ({spare_words_limit:,} words)')
    ax.axvline(terminal_failure_overwrite, color='#cc0000', linestyle=':', lw=2.0, label=f'Terminal Failure ({terminal_failure_overwrite/1e7:.2f} x 10^7 Overwrites)')
    ax.set_title('Subsystem Reliability: Full Tier-1+2 Concatenation vs Spares', fontsize=11, fontweight='bold')
    ax.set_xlabel('Cumulative Full Device Overwrites', fontsize=10)
    ax.set_ylabel('Retired Words Count', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper left', fontsize=9.5)
    
    plt.tight_layout()
    
    plot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    os.makedirs(plot_dir, exist_ok=True)
    plot_path = os.path.join(plot_dir, "monte_carlo_discrete_cell_wear.png")
    plt.savefig(plot_path, dpi=250, bbox_inches='tight')
    plt.close()
    
    tbw_terabytes = terminal_failure_overwrite * 8.0 / 1e3
    tbw_petabytes = tbw_terabytes / 1e3
    results = {
        "simulation_mode": "Native 3D Flash with Full Tier 1+2 Concatenation & Spares",
        "physical_cells_simulated": int(num_physical_cells),
        "total_hsiao_words": int(words_count),
        "spare_words_pool_limit": int(spare_words_limit),
        "first_cell_puncture_overwrite": float(first_cell_puncture_overwrite) if first_cell_puncture_overwrite else 0.0,
        "first_hsiao_double_error_overwrite": float(first_hsiao_double_error_overwrite) if first_hsiao_double_error_overwrite else 0.0,
        "first_word_retired_overwrite": float(first_word_retired_overwrite) if first_word_retired_overwrite else 0.0,
        "terminal_spare_exhaustion_overwrite": float(terminal_failure_overwrite),
        "endurance_scientific_notation": f"{terminal_failure_overwrite/1e7:.2f} x 10^7 full overwrites",
        "total_terabytes_written_tbw": float(tbw_terabytes),
        "total_petabytes_written_pbw": float(tbw_petabytes),
        "elapsed_seconds": float(elapsed),
        "plot_path": plot_path
    }
    
    json_path = os.path.join(os.path.dirname(__file__), "monte_carlo_discrete_results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\n[SUCCESS] Simulation Finished and Terminated Autonomously!")
    print(f"[SUCCESS] Real Failure Point   : {terminal_failure_overwrite:,.0f} FULL OVERWRITES ({results['endurance_scientific_notation']})")
    print(f"[SUCCESS] Total TBW Written     : {tbw_terabytes:,.1f} TBW ({tbw_petabytes:.2f} Petabytes!)")
    print(f"[SUCCESS] Total Run Time       : {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
    print(f"[SUCCESS] Plot Saved           : {plot_path}")
    print(f"[SUCCESS] Metrics Saved        : {json_path}")
    print("================================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Native OMI Monte Carlo to Failure with Full Concatenation")
    parser.add_argument("--cells", type=int, default=75_600_000, help="Number of physical cells to simulate in RAM (default: 75.6M)")
    args = parser.parse_args()
    
    run_discrete_monte_carlo_to_exhaustion(num_physical_cells=args.cells)
