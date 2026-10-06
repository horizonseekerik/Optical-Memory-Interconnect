"""
test_sd_card_buffer_endurance.py
========================================================================================
EVALUATING 25% INDUSTRIAL SD-CARD / ENTERPRISE OVER-PROVISIONING BUFFER ON OMI 3D FLASH
Comparing 5% Baseline Reserve vs. 25% High-Endurance Buffer across 101 and 256 Pillars
========================================================================================

Author: Deepanshu Bhardwaj & Antigravity AI
"""

import os
import sys
import time
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_discrete_endurance(num_physical_cells=756_000, spare_ratio=0.05, pillars=101, seed=42):
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(int.from_bytes(os.urandom(4), byteorder='little'))
        
    t0 = time.time()
    
    # Pillar-dependent physics
    E_a = 0.35
    k_B = 8.617333262145e-5
    T_hot = 85.0 + 273.15
    
    if pillars == 256:
        T_omi = 37.15 + 273.15
        thermal_boost = np.exp((E_a / k_B) * ((1.0 / T_omi) - (1.0 / T_hot)))  # 5.882x
        pulsing_boost = 13.63                                                   # 13.63x (606 ps crisp pulse)
        voltage_boost = 7.50
        num_micro_zones = 256
        skew = 1.015
    else:
        # Baseline 101 pillars
        T_omi = 41.20 + 273.15
        thermal_boost = np.exp((E_a / k_B) * ((1.0 / T_omi) - (1.0 / T_hot)))  # 4.856x
        pulsing_boost = 11.22                                                   # 11.22x (2.2 ns pulse)
        voltage_boost = 7.50
        num_micro_zones = 100
        skew = 1.04
        
    eta_cell_baseline = 1.0e6
    eta_cell_omi = eta_cell_baseline * thermal_boost * pulsing_boost * voltage_boost
    beta_weibull = 1.85

    # Ensure exact word and cell alignment per micro-zone
    words_per_zone = max(1, (num_physical_cells // 72) // num_micro_zones)
    words_count = words_per_zone * num_micro_zones
    num_physical_cells = words_count * 72
    cells_per_zone = words_per_zone * 72
    stripes_count = words_count // 8             # 8 words (576 bits) per Tier-2 stripe
    spare_words_limit = int(words_count * spare_ratio)
    
    print(f"\n[RUN] Pillars: {pillars} | Buffer: {spare_ratio*100:.0f}% ({spare_words_limit:,} spare words) | eta_cell: {eta_cell_omi:,.0f}")
    
    # Synthesize Weibull thresholds
    u = np.random.uniform(1e-12, 1.0 - 1e-12, size=num_physical_cells)
    cell_breakdown_thresholds = (eta_cell_omi * ((-np.log(u)) ** (1.0 / beta_weibull))).astype(np.float32)
    
    cell_wear_counts = np.zeros(num_physical_cells, dtype=np.uint32)
    cell_broken = np.zeros(num_physical_cells, dtype=bool)
    
    cells_per_zone = num_physical_cells // num_micro_zones
    words_per_zone = cells_per_zone // 72
    ranks = np.arange(1, num_micro_zones + 1)
    zipf_weights = 1.0 / (ranks ** (0.85 if pillars == 101 else 0.70))
    zipf_probs = zipf_weights / np.sum(zipf_weights)
    
    zone_wear = np.zeros(num_micro_zones, dtype=np.float64)
    zone_mapping = np.arange(num_micro_zones)
    
    cumulative_writes = 0
    history_overwrites = []
    history_broken_cells = []
    history_retired_words = []
    
    step = 0
    spare_pct = 0.0
    terminal_failure_overwrite = None
    first_cell_puncture_overwrite = None
    first_hsiao_double_error_overwrite = None
    first_word_retired_overwrite = None
    
    while True:
        step += 1
        
        # Adaptive stepping
        if spare_pct < 60.0:
            overwrites_per_step = 250_000
        elif spare_pct < 85.0:
            overwrites_per_step = 100_000
        elif spare_pct < 95.0:
            overwrites_per_step = 25_000
        else:
            overwrites_per_step = 5_000  # ultra-fine terminal resolution
            
        step_writes = int(overwrites_per_step * num_physical_cells)
        
        # Rotator rebalancing
        sorted_physical_zones = np.argsort(zone_wear)
        zone_mapping = sorted_physical_zones
        zone_increment = overwrites_per_step * (zipf_probs * num_micro_zones)
        
        for logical_z in range(num_micro_zones):
            phys_z = zone_mapping[logical_z]
            base_inc = zone_increment[logical_z]
            zone_wear[phys_z] += base_inc
            
            start_idx = phys_z * cells_per_zone
            end_idx = start_idx + cells_per_zone
            
            jitter = np.random.normal(loc=1.0, scale=0.05, size=words_per_zone).astype(np.float32)
            word_inc = np.clip(np.round(base_inc * jitter), 1, None).astype(np.uint32)
            cell_inc = np.repeat(word_inc, 72)
            cell_wear_counts[start_idx:end_idx] += cell_inc
            
        cumulative_writes += step_writes
        full_device_overwrites = cumulative_writes / num_physical_cells
        
        # Check newly broken cells
        newly_broken = (cell_wear_counts >= cell_breakdown_thresholds) & (~cell_broken)
        if np.any(newly_broken):
            cell_broken[newly_broken] = True
            if first_cell_puncture_overwrite is None:
                first_cell_puncture_overwrite = full_device_overwrites
                
        total_broken_cells = int(np.sum(cell_broken))
        
        # Hsiao SEC-DED (72, 64)
        words_broken_bits = cell_broken[:words_count * 72].reshape(words_count, 72)
        bad_bits_per_word = np.sum(words_broken_bits, axis=1)
        hsiao_repaired_words = int(np.sum(bad_bits_per_word == 1))
        hsiao_double_errors = (bad_bits_per_word >= 2)
        total_hsiao_double_errors = int(np.sum(hsiao_double_errors))
        
        if total_hsiao_double_errors > 0 and first_hsiao_double_error_overwrite is None:
            first_hsiao_double_error_overwrite = full_device_overwrites
            
        # Tier-2 BCH-8 Concatenation
        stripes_bad_words = hsiao_double_errors[:stripes_count * 8].reshape(stripes_count, 8)
        bad_words_per_stripe = np.sum(stripes_bad_words, axis=1)
        excess_bad_words = np.maximum(0, bad_words_per_stripe - 1)
        total_retired_words = int(np.sum(excess_bad_words))
        
        if total_retired_words > 0 and first_word_retired_overwrite is None:
            first_word_retired_overwrite = full_device_overwrites
            
        spares_used = min(total_retired_words, spare_words_limit)
        spare_pct = (spares_used / spare_words_limit) * 100.0
        
        history_overwrites.append(full_device_overwrites)
        history_broken_cells.append(total_broken_cells)
        history_retired_words.append(total_retired_words)
        
        if step % 25 == 0 or (spare_pct > 80.0 and step % 10 == 0):
            print(f"    Step {step:4d} | Overwrites: {full_device_overwrites:12,.0f} | Spares: {spares_used:5d}/{spare_words_limit:5d} ({spare_pct:5.1f}%) | Broken: {total_broken_cells:6d}")
            
        if total_retired_words >= spare_words_limit:
            terminal_failure_overwrite = full_device_overwrites
            print(f"    --> TERMINAL FAILURE at {terminal_failure_overwrite:,.0f} full overwrites ({spare_ratio*100:.0f}% buffer exhausted)")
            break
            
    elapsed = time.time() - t0
    tbw_terabytes = terminal_failure_overwrite * 8.0 / 1e3
    tbw_petabytes = tbw_terabytes / 1e3
    
    return {
        "pillars": pillars,
        "spare_ratio": spare_ratio,
        "spare_words_limit": spare_words_limit,
        "terminal_overwrites": terminal_failure_overwrite,
        "first_puncture": first_cell_puncture_overwrite,
        "first_double_error": first_hsiao_double_error_overwrite,
        "first_word_retired": first_word_retired_overwrite,
        "tbw_terabytes": tbw_terabytes,
        "tbw_petabytes": tbw_petabytes,
        "elapsed_sec": elapsed,
        "history_overwrites": history_overwrites,
        "history_retired_words": history_retired_words,
        "history_broken_cells": history_broken_cells
    }

def main():
    print("=" * 80)
    print("  OMI 3D FLASH: IMPACT OF 25% INDUSTRIAL BUFFER (OVER-PROVISIONING)")
    print("=" * 80)
    
    # Configurations to test:
    # 1. 101 pillars, 5% buffer (baseline)
    # 2. 101 pillars, 25% buffer (industrial SD card OP)
    # 3. 256 pillars, 5% buffer (Pareto optimal)
    # 4. 256 pillars, 25% buffer (Pareto optimal + Industrial SD card OP)
    
    configs = [
        {"pillars": 101, "spare_ratio": 0.05, "label": "101 Pillars (5% Baseline Reserve)"},
        {"pillars": 101, "spare_ratio": 0.25, "label": "101 Pillars (25% Industrial SD Buffer)"},
        {"pillars": 256, "spare_ratio": 0.05, "label": "256 Pillars (5% Baseline Reserve)"},
        {"pillars": 256, "spare_ratio": 0.25, "label": "256 Pillars (25% Industrial SD Buffer)"},
    ]
    
    results = []
    for cfg in configs:
        res = run_discrete_endurance(
            num_physical_cells=756_000,
            spare_ratio=cfg["spare_ratio"],
            pillars=cfg["pillars"],
            seed=42
        )
        res["label"] = cfg["label"]
        results.append(res)
        
    print("\n" + "=" * 95)
    print(f"{'Configuration':<42} | {'Buffer':<8} | {'Full Overwrites':<18} | {'PBW (8 GB Tile)':<16} | {'Gain vs Baseline'}")
    print("-" * 95)
    baseline_ow = results[0]["terminal_overwrites"]
    for r in results:
        gain = r["terminal_overwrites"] / baseline_ow
        print(f"{r['label']:<42} | {r['spare_ratio']*100:5.0f}%  | {r['terminal_overwrites']:15,.0f}  | {r['tbw_petabytes']:12.2f} PBW  | {gain:6.2f}x")
    print("=" * 95)
    
    # -------------------------------------------------------------------------
    # Generate High-Resolution Publication Plot
    # -------------------------------------------------------------------------
    plot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    os.makedirs(plot_dir, exist_ok=True)
    plot_path = os.path.join(plot_dir, "buffer_endurance_comparison_25pct.png")
    
    fig, axs = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
    fig.patch.set_facecolor('#ffffff')
    
    colors = ['#888888', '#0077bb', '#ee7733', '#009944']
    styles = ['--', '-', '--', '-']
    
    # Panel 1: Retired Words vs Overwrites
    ax1 = axs[0]
    for i, r in enumerate(results):
        ax1.plot(r["history_overwrites"], r["history_retired_words"],
                 color=colors[i], linestyle=styles[i], lw=2.2, label=r["label"])
        ax1.scatter([r["terminal_overwrites"]], [r["spare_words_limit"]], color=colors[i], s=70, zorder=5)
        
    ax1.set_title("Autonomous Spare Pool Consumption to Failure", fontsize=11, fontweight='bold')
    ax1.set_xlabel("Cumulative Full-Device Overwrites", fontsize=10)
    ax1.set_ylabel("Retired Defective Words Count", fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper left', fontsize=8.5)
    
    # Panel 2: Comparative Bar Chart
    ax2 = axs[1]
    labels = [
        "101-Pillar\n5% Buffer",
        "101-Pillar\n25% Buffer",
        "256-Pillar\n5% Buffer",
        "256-Pillar\n25% Buffer"
    ]
    overwrites_millions = [r["terminal_overwrites"] / 1e6 for r in results]
    pbws = [r["tbw_petabytes"] for r in results]
    bars = ax2.bar(labels, overwrites_millions, color=colors, width=0.55, edgecolor='black', lw=1.2)
    
    for bar, ow, pb in zip(bars, overwrites_millions, pbws):
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 1.0,
                 f"{ow:.2f}M Writes\n({pb:.1f} PBW)",
                 ha='center', va='bottom', fontsize=8.8, fontweight='bold')
                 
    ax2.set_title("Full-Device Endurance by Architecture & Buffer Configuration", fontsize=11, fontweight='bold')
    ax2.set_ylabel("Millions of Full Device Overwrites", fontsize=10)
    ax2.set_ylim(0, max(overwrites_millions) * 1.25)
    ax2.grid(True, axis='y', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\n[+] High-Resolution Plot Saved to: {plot_path}")
    
    # Save results to JSON
    json_path = os.path.join(os.path.dirname(__file__), "buffer_endurance_results.json")
    clean_results = []
    for r in results:
        clean_results.append({
            "label": r["label"],
            "pillars": r["pillars"],
            "spare_ratio": r["spare_ratio"],
            "spare_words_limit": r["spare_words_limit"],
            "terminal_overwrites": float(r["terminal_overwrites"]),
            "tbw_petabytes": float(r["tbw_petabytes"]),
            "first_puncture": float(r["first_puncture"]) if r["first_puncture"] else None,
            "first_double_error": float(r["first_double_error"]) if r["first_double_error"] else None,
            "first_word_retired": float(r["first_word_retired"]) if r["first_word_retired"] else None
        })
    with open(json_path, "w") as f:
        json.dump(clean_results, f, indent=2)
    print(f"[+] Metrics Saved to: {json_path}")

if __name__ == "__main__":
    main()
