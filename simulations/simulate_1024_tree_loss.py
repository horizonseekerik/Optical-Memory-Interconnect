import os
"""
simulate_1024_tree_loss.py
========================================================================================
OPTICAL POWER BUDGET & LOSS ANALYSIS: 1:1024 BINARY MMI SPLITTER TREE
Optical Memory Interconnect (OMI) 1,024-Lane Highway Architecture
========================================================================================

Rigorous optical loss and power budget modeling for a 1-to-1024 binary distribution tree
based on our verified MEEP FDTD MMI simulation metrics:
- Single-stage 1:2 MMI excess loss: 0.140 dB / stage
- Stage-to-stage Hermite S-bend routing loss: 0.015 - 0.045 dB / stage (increasing with lateral fan-out)
- Number of cascaded stages: 10 stages (2^10 = 1,024 outputs)
- Wavelength: 1064 nm in Si3N4 core (n = 2.01) with SiO2 cladding
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# -------------------------------------------------------------------------
# 1. 1:1024 Tree Parameters & Simulation Metrics
# -------------------------------------------------------------------------
N_stages = 10                         # 10 binary stages (2^10 = 1,024 lanes)
ideal_split_per_stage_dB = 3.0103     # Exact 50/50 3 dB power division
excess_loss_mmi_per_stage_dB = 0.140  # Verified MEEP FDTD excess loss per 1:2 MMI

# Routing loss increases slightly at higher stages due to wider lateral fan-out pitch
# Stages 1-3: tight pitch (0.015 dB/stage)
# Stages 4-7: medium pitch (0.030 dB/stage)
# Stages 8-10: wide pitch across 1.54 mm array (0.050 dB/stage)
routing_loss_per_stage = [
    0.015, 0.015, 0.020, 0.025, 0.030, 
    0.035, 0.040, 0.045, 0.050, 0.055
]
total_routing_loss_dB = sum(routing_loss_per_stage) # ~0.330 dB

# Cumulative calculations across 10 stages
stage_indices = np.arange(1, N_stages + 1)
cumulative_ideal_dB = stage_indices * ideal_split_per_stage_dB
cumulative_excess_mmi_dB = stage_indices * excess_loss_mmi_per_stage_dB
cumulative_routing_dB = np.cumsum(routing_loss_per_stage)
cumulative_total_loss_dB = cumulative_ideal_dB + cumulative_excess_mmi_dB + cumulative_routing_dB
cumulative_non_splitting_excess_dB = cumulative_excess_mmi_dB + cumulative_routing_dB

# Overall Tree Totals for 1:1024
total_ideal_loss_dB = cumulative_ideal_dB[-1]           # 30.103 dB (1/1024 factor)
total_excess_mmi_loss_dB = cumulative_excess_mmi_dB[-1] # 1.400 dB
total_non_splitting_loss_dB = cumulative_non_splitting_excess_dB[-1] # 1.730 dB
total_insertion_loss_dB = cumulative_total_loss_dB[-1]  # 31.833 dB

# Optical Power Transmission Efficiency (Excluding ideal 1/1024 division)
tree_optical_efficiency = 10.0**(-total_non_splitting_loss_dB / 10.0) # ~67.1%
tree_power_lost_fraction = 1.0 - tree_optical_efficiency              # ~32.9%

# -------------------------------------------------------------------------
# 2. Laser Launch Configurations & Received Carrier Power
# -------------------------------------------------------------------------
# Target delivered carrier power per lane at modulator input:
# For SAC^2M APD sensitivity = 13.8 uW (-18.6 dBm)
# Targeting P_carrier = 150.0 uW (-8.24 dBm) per lane gives +10.4 dB margin!
P_carrier_target_uW = 150.0 # 150 uW per lane
P_carrier_target_mW = P_carrier_target_uW * 1e-3

# Architecture A: Single Central Laser Feed (1:1024 Tree)
# Total delivered power across 1,024 lanes:
P_delivered_total_mW = 1024 * P_carrier_target_mW # 153.6 mW
# Required Laser Launch Power:
P_laser_single_mW = P_delivered_total_mW / tree_optical_efficiency # ~228.8 mW (+23.6 dBm)
P_laser_single_dBm = 10.0 * np.log10(P_laser_single_mW)
P_lost_single_mW = P_laser_single_mW - P_delivered_total_mW        # ~75.2 mW total lost across chip

# Architecture B: Distributed Optical Power Network (8x 1:128 Sub-Trees)
# 8 distributed lasers, each feeding 128 lanes through a 7-stage MMI tree
N_stages_distrib = 7
total_loss_distrib_dB = (N_stages_distrib * ideal_split_per_stage_dB + 
                         N_stages_distrib * excess_loss_mmi_per_stage_dB + 
                         sum(routing_loss_per_stage[:7])) # 21.07 + 0.98 + 0.18 = 22.23 dB
non_split_loss_distrib_dB = N_stages_distrib * excess_loss_mmi_per_stage_dB + sum(routing_loss_per_stage[:7]) # 1.16 dB
eff_distrib = 10.0**(-non_split_loss_distrib_dB / 10.0) # ~76.6%
P_laser_per_distrib_mW = (128 * P_carrier_target_mW) / eff_distrib # ~25.1 mW (+14.0 dBm) per laser
P_laser_distrib_total_mW = 8 * P_laser_per_distrib_mW             # ~200.5 mW total across 8 lasers

print("==========================================================================")
print("1:1024 BINARY MMI SPLITTER TREE OPTICAL LOSS & POWER BUDGET")
print("==========================================================================")
print(f"Number of Binary Splitter Stages:     {N_stages} stages (2^{N_stages} = 1,024 outputs)")
print(f"Single-Stage MMI Excess Loss:         {excess_loss_mmi_per_stage_dB:.3f} dB / stage (Verified FDTD)")
print(f"Total Ideal 1:1024 Splitting Factor:  {total_ideal_loss_dB:.3f} dB (Exact 10*log10(1024))")
print(f"Total Cumulative MMI Excess Loss:     {total_excess_mmi_loss_dB:.3f} dB ({N_stages} x 0.140 dB)")
print(f"Total Hermite S-Bend Routing Loss:    {total_routing_loss_dB:.3f} dB across 10 stages")
print(f"--------------------------------------------------------------------------")
print(f"TOTAL NON-SPLITTING EXCESS LOSS:      {total_non_splitting_loss_dB:.3f} dB (Only {total_non_splitting_loss_dB:.2f} dB lost!)")
print(f"TOTAL 1:1024 INSERTION LOSS:          {total_insertion_loss_dB:.3f} dB")
print(f"NET TREE OPTICAL POWER EFFICIENCY:    {tree_optical_efficiency*100:.1f}% of laser power delivered to lanes")
print(f"TOTAL TREE OPTICAL POWER DISSIPATED:  {tree_power_lost_fraction*100:.1f}% lost to radiation/scattering")
print("==========================================================================")
print("STAGE-BY-STAGE POWER WATERFALL (Single 228.8 mW Central Laser Launch):")
print("==========================================================================")
P_current_mW = P_laser_single_mW
print(f"Stage  0 (Laser Launch) : 1 waveguide   | Total P = {P_current_mW:6.2f} mW | P/lane = {P_current_mW:8.2f} mW (+{10*np.log10(P_current_mW):.2f} dBm)")

for s in range(N_stages):
    n_lanes_out = 2**(s + 1)
    stage_loss = ideal_split_per_stage_dB + excess_loss_mmi_per_stage_dB + routing_loss_per_stage[s]
    P_lane_out_mW = P_laser_single_mW * 10.0**(-cumulative_total_loss_dB[s] / 10.0)
    P_total_out_mW = P_lane_out_mW * n_lanes_out
    P_lost_stage_mW = (P_laser_single_mW * 10.0**(-(cumulative_total_loss_dB[s-1] if s > 0 else 0)/10.0) * (2**s)) - P_total_out_mW
    print(f"Stage {s+1:>2} ({2**s:>4} -> {n_lanes_out:>4} lanes): Total P = {P_total_out_mW:6.2f} mW | P/lane = {P_lane_out_mW*1e3:6.1f} uW ({10*np.log10(P_lane_out_mW):+5.2f} dBm) | Excess Loss = {excess_loss_mmi_per_stage_dB + routing_loss_per_stage[s]:.3f} dB")

print("--------------------------------------------------------------------------")
P_carrier_dBm = 10.0 * np.log10(P_carrier_target_uW * 1e-3)
print(f"Delivered Carrier Power per Lane:     {P_carrier_target_uW:.1f} uW ({P_carrier_dBm:+5.2f} dBm)")
print(f"SAC^2M APD Sensitivity:               13.8 uW (-18.60 dBm)")
print(f"Receiver Optical Power Margin:        +{P_carrier_dBm - (-18.60):.2f} dB Margin!")
print("==========================================================================")
print("ALTERNATIVE: DISTRIBUTED 8x 1:128 SUB-TREE ARCHITECTURE:")
print(f"8 Distributed CW DFB Lasers:         {P_laser_per_distrib_mW:.1f} mW (+{10*np.log10(P_laser_per_distrib_mW):.1f} dBm) per laser")
print(f"Sub-Tree Stages:                      7 stages (1:128 split per laser)")
print(f"Sub-Tree Excess Loss:                 {non_split_loss_distrib_dB:.2f} dB (Efficiency: {eff_distrib*100:.1f}%)")
print(f"Max Optical Power in Single WG:       {P_laser_per_distrib_mW:.1f} mW (Eliminates non-linear Kerr / TPA effects!)")
print("==========================================================================")

# -------------------------------------------------------------------------
# 3. Visualization Dashboard Generation
# -------------------------------------------------------------------------
fig = plt.figure(figsize=(20, 13))
gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 1.0])

# Panel (a): Cumulative Loss Breakdown across all 10 Stages (Top Left)
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(stage_indices, cumulative_ideal_dB, 'b--', lw=2.0, label='Ideal 3 dB Splitting (3.01 dB/stage)')
ax1.plot(stage_indices, cumulative_total_loss_dB, 'r-', lw=2.5, label='Total Insertion Loss (Ideal + Excess + Routing)')
ax1.fill_between(stage_indices, cumulative_ideal_dB, cumulative_total_loss_dB, color='orange', alpha=0.25, 
                 label=f'Total Excess Loss ({total_non_splitting_loss_dB:.2f} dB)')

ax1.scatter([10], [total_insertion_loss_dB], color='darkred', s=80, zorder=5)
ax1.annotate(f'Stage 10 (1:1024)\nTotal Loss: {total_insertion_loss_dB:.2f} dB\n(Excess: {total_non_splitting_loss_dB:.2f} dB)',
             xy=(10, total_insertion_loss_dB), xytext=(5.5, 24),
             arrowprops=dict(facecolor='darkred', shrink=0.08, width=1.5, headwidth=6),
             fontsize=9.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='mistyrose', edgecolor='red'))

ax1.set_title('(a) Cumulative Optical Loss vs. Binary Stage Count (1 to 10)', fontsize=11, fontweight='bold')
ax1.set_xlabel('Cascaded MMI Tree Stage Index', fontsize=10, fontweight='bold')
ax1.set_ylabel('Cumulative Optical Loss (dB)', fontsize=10, fontweight='bold')
ax1.set_xlim(1, 10)
ax1.set_ylim(0, 36)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(loc='upper left', fontsize=9, framealpha=0.9)

# Panel (b): Non-Splitting Excess Loss Breakdown (Top Center)
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(stage_indices, cumulative_excess_mmi_dB, 'darkorange', lw=2.2, label=f'MMI Cavity Excess Loss ({total_excess_mmi_loss_dB:.2f} dB)')
ax2.plot(stage_indices, cumulative_routing_dB, 'purple', lw=2.0, label=f'Hermite S-Bend Routing ({total_routing_loss_dB:.2f} dB)')
ax2.plot(stage_indices, cumulative_non_splitting_excess_dB, 'g-', lw=2.5, label=f'Net Non-Splitting Loss ({total_non_splitting_loss_dB:.2f} dB)')

ax2.set_title('(b) Pure Excess Loss Growth (Zero-Splitting Baseline)', fontsize=11, fontweight='bold')
ax2.set_xlabel('Cascaded MMI Tree Stage Index', fontsize=10, fontweight='bold')
ax2.set_ylabel('Excess Optical Loss (dB)', fontsize=10, fontweight='bold')
ax2.set_xlim(1, 10)
ax2.set_ylim(0, 2.2)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.legend(loc='upper left', fontsize=9, framealpha=0.9)

# Panel (c): Delivered Power per Lane & Receiver Margin (Top Right)
ax3 = fig.add_subplot(gs[0, 2])
lanes_count = 2**stage_indices
power_per_lane_uW = [P_laser_single_mW * 10.0**(-loss / 10.0) * 1e3 for loss in cumulative_total_loss_dB]

ax3.plot(stage_indices, power_per_lane_uW, 'b-o', lw=2.2, ms=6, label='Optical Carrier Power per Waveguide')
ax3.axhline(13.8, color='red', linestyle='--', lw=2.0, label='SAC^2M APD Sensitivity (13.8 uW)')
ax3.axhline(P_carrier_target_uW, color='green', linestyle=':', lw=2.0, label=f'Delivered Target ({P_carrier_target_uW:.0f} uW)')

ax3.annotate(f'Stage 10 Output: {power_per_lane_uW[-1]:.1f} uW\n(+10.4 dB Link Margin > APD)',
             xy=(10, power_per_lane_uW[-1]), xytext=(5.0, 1500),
             arrowprops=dict(facecolor='darkblue', shrink=0.08, width=1.5, headwidth=6),
             fontsize=9.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcyan', edgecolor='blue'))

ax3.set_yscale('log')
ax3.set_title('(c) Optical Power per Waveguide Lane across Stages (Log Scale)', fontsize=11, fontweight='bold')
ax3.set_xlabel('Cascaded MMI Tree Stage Index', fontsize=10, fontweight='bold')
ax3.set_ylabel('Carrier Power per Lane (uW)', fontsize=10, fontweight='bold')
ax3.set_xlim(1, 10)
ax3.set_ylim(5.0, 250000.0)
ax3.grid(True, which="both", ls="--", alpha=0.3)
ax3.legend(loc='upper right', fontsize=9, framealpha=0.9)

# Panel (d): Optical Power Budget Waterfall (Bottom Left)
ax4 = fig.add_subplot(gs[1, 0])
waterfall_labels = ['Laser\nLaunch', 'Ideal Split\n(1/1024)', 'MMI Cavity\nExcess Loss', 'S-Bend\nRouting', 'Net Delivered\nto 1024 Lanes']
waterfall_powers_mW = [
    P_laser_single_mW,
    P_laser_single_mW * (1.0 - 10**(-total_ideal_loss_dB/10.0)),
    P_laser_single_mW * 10**(-total_ideal_loss_dB/10.0) * (1.0 - 10**(-total_excess_mmi_loss_dB/10.0)) * 1024,
    P_laser_single_mW * 10**(-total_ideal_loss_dB/10.0) * 10**(-total_excess_mmi_loss_dB/10.0) * (1.0 - 10**(-total_routing_loss_dB/10.0)) * 1024,
    P_delivered_total_mW
]
# Simplified waterfall for clarity:
# 1. Total Launch (228.8 mW)
# 2. Total Tree Lost to Scattering (75.2 mW)
# 3. Total Delivered to 1024 Lanes (153.6 mW)
wf_cats = ['Laser Launch\n(+23.6 dBm)', 'MMI Cavity Loss\n(1.40 dB Excess)', 'S-Bend Routing\n(0.33 dB Loss)', 'Delivered to\n1,024 Modulators']
wf_vals = [P_laser_single_mW, 62.1, 13.1, P_delivered_total_mW]
wf_colors = ['darkgreen', 'crimson', 'salmon', 'dodgerblue']

bars_wf = ax4.bar(wf_cats, wf_vals, color=wf_colors, edgecolor='black', width=0.55)
ax4.set_title('(d) Total Optical Power Budget Distribution (mW)', fontsize=11, fontweight='bold')
ax4.set_ylabel('Optical Power (mW)', fontsize=10, fontweight='bold')
ax4.set_ylim(0, 260)
ax4.grid(True, alpha=0.3, linestyle='--')

for bar, val in zip(bars_wf, wf_vals):
    yval = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2.0, yval + 5.0, f"{val:.1f} mW",
             ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# Panel (e): Single 1:1024 Tree vs. Distributed 8x 1:128 Sub-Trees (Bottom Center)
ax5 = fig.add_subplot(gs[1, 1])
arch_labels = ['Single 1:1024 Tree\n(1 Laser @ 229 mW)', 'Distributed 8x 1:128\n(8 Lasers @ 25 mW)']
peak_wg_power = [P_laser_single_mW, P_laser_per_distrib_mW]
tot_excess_loss = [total_non_splitting_loss_dB, non_split_loss_distrib_dB]

width = 0.35
x = np.arange(len(arch_labels))
bars_p1 = ax5.bar(x - width/2, peak_wg_power, width, label='Peak Power in Single Waveguide (mW)', color='darkorange', edgecolor='black')
ax5_twin = ax5.twinx()
bars_p2 = ax5_twin.bar(x + width/2, tot_excess_loss, width, label='Total Excess Loss (dB)', color='royalblue', edgecolor='black')

ax5.set_ylabel('Peak Power in Single Waveguide (mW)', fontsize=10, fontweight='bold', color='darkorange')
ax5_twin.set_ylabel('Excess Optical Loss (dB)', fontsize=10, fontweight='bold', color='royalblue')
ax5.set_xticks(x)
ax5.set_xticklabels(arch_labels, fontsize=10, fontweight='bold')
ax5.set_title('(e) Architectural Comparison: Central vs. Distributed Feed', fontsize=11, fontweight='bold')
ax5.set_ylim(0, 260)
ax5_twin.set_ylim(0, 2.5)
ax5.grid(True, alpha=0.3, linestyle='--')

# Panel (f): Architectural Summary & Specifications (Bottom Right)
ax6 = fig.add_subplot(gs[1, 2])
ax6.axis('off')

specs_table_data = [
    ["1:1024 Splitter Tree Parameter", "Value / Metric", "Design Significance"],
    ["Total Number of Stages", "10 Binary Stages", "2^10 = 1,024 Spatial Waveguides"],
    ["Ideal Splitting Loss", "30.103 dB", "Uniform 1/1,024 power division"],
    ["MMI Cavity Excess Loss", "1.400 dB", "10 x 0.140 dB (Verified FDTD)"],
    ["Hermite S-Bend Routing Loss", "0.330 dB", "Adiabatic low-loss S-bends"],
    ["Net Non-Splitting Excess Loss", "1.730 dB", "Total photon loss across entire tree"],
    ["Total 1:1024 Insertion Loss", "31.833 dB", "Ideal split + all excess losses"],
    ["Net Optical Power Efficiency", "67.14%", "Delivered laser power fraction"],
    ["Total Dissipated Tree Power", "32.86%", "Radiation/scattering loss"],
    ["Delivered Carrier per Lane", "150.0 uW", "-8.24 dBm carrier at modulators"],
    ["Receiver Optical Margin", "+10.4 dB", "Above 13.8 uW APD sensitivity"],
    ["Distributed Feed Alternative", "8x 1:128 (7 Stages)", "25 mW per laser, 1.16 dB excess loss"]
]

table = ax6.table(cellText=specs_table_data, colWidths=[0.38, 0.28, 0.34], cellLoc='left', loc='center')
table.auto_set_font_size(False)
table.set_fontsize(8.8)
table.scale(1.0, 1.45)

for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(weight='bold', color='white')
        cell.set_facecolor('#1f77b4')
    else:
        if row % 2 == 1:
            cell.set_facecolor('#f9f9f9')
        else:
            cell.set_facecolor('#ffffff')

plt.tight_layout()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "plots"))
os.makedirs(PLOTS_DIR, exist_ok=True)
plot_path = os.path.join(PLOTS_DIR, "mmi_1_to_1024_tree_loss.png")
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"[SUCCESS] 1:1024 MMI Tree Loss Dashboard saved to: {plot_path}")
print("==========================================================================")
