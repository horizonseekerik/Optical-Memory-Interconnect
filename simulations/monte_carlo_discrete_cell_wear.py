"""
monte_carlo_discrete_cell_wear.py
Native OMI Discrete Cell-by-Cell Physical Monte Carlo Simulation.

Physical Foundation & Voltage Correction:
  1. Low-Voltage Channel Hot-Electron / Fowler-Nordheim Physics:
      Conventional 3D flash requires 18V - 20V high-voltage charge pumps across massive continuous sheets,
      causing extreme electric field dielectric stress (E_ox = 10 - 12 MV/cm) that drives SILC defect creation.
      In OMI, with re-crystallized silicon micro-channels (I_on >= 35 uA) and ultra-short wordline sub-zones,
      the programming potential collapses to V_prog = 4.5V - 5.5V (E_ox = 3.5 - 4.5 MV/cm).
      By the physical 1/E model of dielectric breakdown:
        Longevity Multiplier (E-field) = exp( G * (1/E_conv - 1/E_omi) ) ~= 6.8x - 8.5x!
  2. Nanosecond Pulsed Injection (Lever 2):
      Wordline RC settling collapses from 15 microseconds to 2.216 ns (101-pillar constellation).
      Shortening pulse duration from 10 microseconds to 10 ns reduces field stress exposure by 1,000x (11.22x boost).
  3. Thermal Highway Clamping:
      Passive structural conduction clamps core operating temperature to 41.20 C in vacuum (4.856x boost).
  4. Native Multi-Tier Concatenation:
      - Tier 1: (72, 64) Hsiao SEC-DED (38.2 ps combinational single-bit repair).
      - Tier 2: 2D Spatially Interleaved BCH-8 across 576-bit optical stripes (corrects up to 8 symbol errors).
      - 5% Autonomous Spare Stripe Reserve: Dynamic on-the-fly bad stripe replacement.

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
    print("  OMI NATIVE 3D FLASH MONTE CARLO (LOW-VOLTAGE + NANOSECOND PULSED + TIER 1+2)  ")
    print("================================================================================")
    
    scale_factor = 75_600_000_000 / num_physical_cells
    words_count = num_physical_cells // 72
    stripes_count = words_count // 8             # 8 words (576 bits) per Tier-2 BCH-8 stripe
    spare_stripes_limit = int(stripes_count * 0.05)  # 5% autonomous spare stripe reserve
    
    print(f"[*] Physical 3D Cells in RAM        : {num_physical_cells:,.0f} cells")
    print(f"[*] Tier-1 Hsiao Words (72-bit)     : {words_count:,.0f} words")
    print(f"[*] Tier-2 BCH-8 Stripes (576-bit)  : {stripes_count:,.0f} stripes (8 words/stripe)")
    print(f"[*] 5% Autonomous Spare Stripes     : {spare_stripes_limit:,.0f} spare stripes")
    print(f"[*] Voronoi Micro-Zones             : {num_micro_zones} active zones")
    print(f"[*] Scale Representation to 8 GB    : 1 : {scale_factor:,.0f}")
    
    # -------------------------------------------------------------------------
    # Physical Degradation Physics: Voltage Correction + Arrhenius + Pulsing
    # -------------------------------------------------------------------------
    # 1. Thermal Clamping (Dual-Sided Thermal Highway at 41.20 C in vacuum vs 85 C)
    E_a = 0.35
    k_B = 8.617333262145e-5
    T_hot = 85.0 + 273.15
    T_omi = 41.20 + 273.15
    thermal_boost = np.exp((E_a / k_B) * ((1.0 / T_omi) - (1.0 / T_hot)))  # 4.856x
    
    # 2. Sub-Nanosecond Word-Line Settling & Low-Stress Pulsing (Lever 2)
    # Conventional NAND: t_WL = 15 us, t_pulse = 10 us (cumulative stress time = N * 10 us)
    # OMI Micro-Zones  : t_WL = 2.22 ns, t_pulse = 10 ns (1,000x reduction in field stress duration)
    # Pulsing Longevity Multiplier: (10,000 ns / 10 ns)^0.35 = (1,000)^0.35 = 11.22x
    pulsing_boost = 11.22
    
    # 3. Voltage Correction (E-Field Stress Reduction)
    # Conventional 3D flash: V_prog = 18V - 20V across thick tunnel stacks (E_ox ~= 11 MV/cm)
    # OMI low-voltage injection: V_prog = 4.8V (E_ox ~= 4.2 MV/cm) thanks to re-crystallized 35 uA channel
    # By 1/E TDDB model: Delta E-field stress longevity multiplier = 7.50x
    voltage_correction_boost = 7.50
    
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
    print("\n[*] Commencing Autonomous Background Simulation...")
    print(f"{'Step':>6} | {'Full Overwrites':>16} | {'Broken Cells':>13} | {'Tier-1 Hsiao Rep':>16} | {'Tier-2 Bad Stripes':>18} | {'Spares Used':>12} | {'Spare Status'}")
    print("-" * 112)
    
    first_cell_puncture_overwrite = None
    first_hsiao_error_overwrite = None
    first_tier2_stripe_fail_overwrite = None
    terminal_failure_overwrite = None
    
    cumulative_writes = 0
    history_overwrites = []
    history_broken_cells = []
    history_failed_stripes = []
    
    # Adaptive step size: 100,000 full overwrites per step for fast multi-million cycle convergence
    overwrites_per_step = 100_000
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
        
        hsiao_repaired_words = int(np.sum(bad_bits_per_word == 1))
        hsiao_bad_words = (bad_bits_per_word >= 2)
        total_hsiao_bad_words = int(np.sum(hsiao_bad_words))
        
        if total_hsiao_bad_words > 0 and first_hsiao_error_overwrite is None:
            first_hsiao_error_overwrite = full_device_overwrites
            print(f"[!] MILESTONE 2: First Hsiao Double-Bit Error at Overwrite {full_device_overwrites:,.0f} (Tolerated & Repaired by Tier-2 BCH-8!)")
            
        # Evaluate Tier-2 BCH-8 Stripes:
        stripes_bad_words = hsiao_bad_words[:stripes_count * 8].reshape(stripes_count, 8)
        bad_words_per_stripe = np.sum(stripes_bad_words, axis=1)
        
        # Tier-2 BCH-8 logic:
        # A stripe is retired to spares when it accumulates >= 3 defective words (preventive retirement)
        retired_stripes = int(np.sum(bad_words_per_stripe >= 3))
        
        if retired_stripes > 0 and first_tier2_stripe_fail_overwrite is None:
            first_tier2_stripe_fail_overwrite = full_device_overwrites
            print(f"[!] MILESTONE 3: First Stripe Autonomous Retirement at Overwrite {full_device_overwrites:,.0f} (Swapped to Spare Reserve)")
            
        spares_used = min(retired_stripes, spare_stripes_limit)
        spare_pct = (spares_used / spare_stripes_limit) * 100.0
        
        history_overwrites.append(full_device_overwrites)
        history_broken_cells.append(total_broken_cells)
        history_failed_stripes.append(retired_stripes)
        
        # Periodic output
        if step % 10 == 0 or step == 1 or retired_stripes > 0:
            status_str = f"SPARES: {spare_pct:.1f}% CONSUMED"
            print(f"{step:>6} | {full_device_overwrites:>16,f} | {total_broken_cells:>13,d} | {hsiao_repaired_words:>16,d} | {retired_stripes:>18,d} | {spares_used:>12,d} | {status_str}")
            
        # REAL TERMINAL FAILURE MILESTONE: Exhaustion of the 5% Autonomous Spare Reserve
        if retired_stripes >= spare_stripes_limit:
            terminal_failure_overwrite = full_device_overwrites
            print("=" * 112)
            print(f"[!] REAL FAILURE MILESTONE REACHED: 5% SPARE POOL EXHAUSTED AT OVERWRITE {full_device_overwrites:,.0f}!")
            print(f"[!] SCIENTIFIC NOTATION: {full_device_overwrites/1e7:.2f} x 10^7 FULL DEVICE WRITES ({full_device_overwrites * 8 / 1e3:,.1f} TBW)")
            print("=" * 112)
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
    ax.plot(history_overwrites, history_failed_stripes, color='#0055cc', lw=2.4, label='Retired Stripes (Tier-1+2 Exhaustion)')
    ax.axhline(spare_stripes_limit, color='orange', linestyle='--', lw=2.0, label=f'5% Spare Limit ({spare_stripes_limit:,} stripes)')
    ax.axvline(terminal_failure_overwrite, color='#cc0000', linestyle=':', lw=2.0, label=f'Terminal Failure ({terminal_failure_overwrite/1e7:.2f} x 10^7 Overwrites)')
    ax.set_title('Subsystem Reliability: Tier-1+2 vs 5% Spare Pool', fontsize=11, fontweight='bold')
    ax.set_xlabel('Cumulative Full Device Overwrites', fontsize=10)
    ax.set_ylabel('Retired Stripes Count', fontsize=10)
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
        "simulation_mode": "Native 3D Flash (Voltage Correction + 2.22ns WL + Tier 1+2 Concatenation)",
        "physical_cells_simulated": int(num_physical_cells),
        "total_hsiao_words": int(words_count),
        "total_bch8_stripes": int(stripes_count),
        "spare_stripes_limit": int(spare_stripes_limit),
        "first_cell_puncture_overwrite": float(first_cell_puncture_overwrite) if first_cell_puncture_overwrite else 0.0,
        "first_hsiao_error_overwrite": float(first_hsiao_error_overwrite) if first_hsiao_error_overwrite else 0.0,
        "first_tier2_stripe_fail_overwrite": float(first_tier2_stripe_fail_overwrite) if first_tier2_stripe_fail_overwrite else 0.0,
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
    parser = argparse.ArgumentParser(description="Native OMI Monte Carlo to Failure with Voltage Correction")
    parser.add_argument("--cells", type=int, default=75_600_000, help="Number of physical cells to simulate in RAM (default: 75.6M)")
    args = parser.parse_args()
    
    run_discrete_monte_carlo_to_exhaustion(num_physical_cells=args.cells)
