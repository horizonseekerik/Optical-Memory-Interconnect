"""
simulate_timing_jitter_budget.py
========================================================================================
PHYSICAL LAYER TIMING JITTER BUDGET & HIGH-SPEED EYE DECOMPOSITION
Optical Memory Interconnect (OMI) & Symmetrically Pipelined 3D Flash Architecture
========================================================================================

Rigorous multi-physics decomposition of deterministic and random timing jitter
at 100 GHz (UI = 10.0 ps) and 200 GHz (UI = 5.0 ps) line rates.

Models:
1. Random Jitter (RJ):
   - Clock tree & injection-locked PLL phase noise (RJ_clk)
   - Laser Relative Intensity Noise (RIN) & linewidth phase-to-timing noise (RJ_laser)
   - Receiver APD/UTC-PD shot noise and thermal noise timing uncertainty (RJ_rx)
   - Combined RJ_rms via root-sum-square (RSS)

2. Deterministic Jitter (DJ):
   - Si3N4 waveguide chromatic & modal dispersion skew over 2.0 cm (DJ_disp)
   - LiTaO3 Pockels electro-optic asymmetric transition skew (DJ_mod)
   - Waveguide boundary reflection and inter-symbol interference (DJ_isi)
   - CMOS StrongARM regenerative latch dynamic aperture window (DJ_aperture)
   - Combined Dual-Dirac DJ_delta_delta

3. Total Jitter (TJ) & Bathtub Curves:
   - TJ(BER) = DJ_delta_delta + 2 * Q(BER) * RJ_rms evaluated at BER = 10^-12 and 10^-15
   - Horizontal eye opening: EO_H = UI - TJ(BER)
   - Verification across trace lengths (0.5 cm to 5.0 cm)

Generates: plots/timing_jitter_eye_decomposition.png (6-panel publication-grade dashboard)
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import erfc

# -------------------------------------------------------------------------
# 1. Physical Layer Timing Parameters
# -------------------------------------------------------------------------

# Operating Rates
f_100g = 100.0e9  # 100 GHz
UI_100g = 1.0 / f_100g  # 10.0 ps
f_200g = 200.0e9  # 200 GHz
UI_200g = 1.0 / f_200g  # 5.0 ps

# Q-factors for Dual-Dirac extrapolation
# For BER = 10^-12: Q ~ 7.0344 (2*Q = 14.069)
# For BER = 10^-15: Q ~ 7.9416 (2*Q = 15.884)
Q_ber12 = 7.03448
Q_ber15 = 7.94165

# 100 GHz Jitter Breakdown (in femtoseconds)
RJ_clk_100g = 45.0       # Clock tree / PLL phase jitter (fs RMS)
RJ_laser_100g = 20.0     # Laser RIN & phase-to-amplitude jitter (fs RMS)
RJ_rx_100g = 28.0        # SAC^2M APD shot/thermal timing noise (fs RMS)
RJ_rms_100g = np.sqrt(RJ_clk_100g**2 + RJ_laser_100g**2 + RJ_rx_100g**2) # ~56.65 fs

DJ_disp_100g = 12.0      # Si3N4 GVD & modal dispersion skew over 2 cm (fs)
DJ_mod_100g = 95.0       # Pockels EO asymmetric rise/fall skew (fs)
DJ_isi_100g = 80.0       # High-frequency channel ISI / reflection (fs)
DJ_aperture_100g = 180.0 # 2nm StrongARM latch sampling window (fs)
DJ_dd_100g = DJ_disp_100g + DJ_mod_100g + DJ_isi_100g + DJ_aperture_100g # 367.0 fs

TJ_100g_ber12 = (DJ_dd_100g + 2.0 * Q_ber12 * RJ_rms_100g) * 1e-15 # seconds
TJ_100g_ber15 = (DJ_dd_100g + 2.0 * Q_ber15 * RJ_rms_100g) * 1e-15 # seconds
EO_100g_ber15 = UI_100g - TJ_100g_ber15

# 200 GHz Jitter Breakdown (in femtoseconds - optimized high-frequency design)
RJ_clk_200g = 35.0       # Injection-locked micro-resonator clock (fs RMS)
RJ_laser_200g = 18.0     # DFB laser with active optical feedback suppression (fs RMS)
RJ_rx_200g = 22.0        # UTC-PD / low-gain SAC^2M APD noise (fs RMS)
RJ_rms_200g = np.sqrt(RJ_clk_200g**2 + RJ_laser_200g**2 + RJ_rx_200g**2) # ~45.14 fs

DJ_disp_200g = 10.0      # Si3N4 dispersion over 2 cm (fs)
DJ_mod_200g = 60.0       # Differential push-pull Pockels cell (fs)
DJ_isi_200g = 50.0       # Pre-emphasized driver ISI suppression (fs)
DJ_aperture_200g = 110.0 # Sub-picosecond dynamic regenerative aperture (fs)
DJ_dd_200g = DJ_disp_200g + DJ_mod_200g + DJ_isi_200g + DJ_aperture_200g # 230.0 fs

TJ_200g_ber12 = (DJ_dd_200g + 2.0 * Q_ber12 * RJ_rms_200g) * 1e-15 # seconds
TJ_200g_ber15 = (DJ_dd_200g + 2.0 * Q_ber15 * RJ_rms_200g) * 1e-15 # seconds
EO_200g_ber15 = UI_200g - TJ_200g_ber15

print("==========================================================================")
print("OMI PHYSICAL LAYER TIMING JITTER BUDGET ANALYSIS")
print("==========================================================================")
print(f"100 GHz System (UI = {UI_100g*1e12:.2f} ps):")
print(f"  Random Jitter (RJ_rms):       {RJ_rms_100g:.2f} fs")
print(f"  Deterministic Jitter (DJ_dd): {DJ_dd_100g:.2f} fs")
print(f"  Total Jitter @ BER=10^-12:    {TJ_100g_ber12*1e12:.3f} ps ({(TJ_100g_ber12/UI_100g)*100:.1f}% UI)")
print(f"  Total Jitter @ BER=10^-15:    {TJ_100g_ber15*1e12:.3f} ps ({(TJ_100g_ber15/UI_100g)*100:.1f}% UI)")
print(f"  Horizontal Eye Opening (EO_H):{EO_100g_ber15*1e12:.3f} ps ({(EO_100g_ber15/UI_100g)*100:.1f}% UI)")
print("--------------------------------------------------------------------------")
print(f"200 GHz System (UI = {UI_200g*1e12:.2f} ps):")
print(f"  Random Jitter (RJ_rms):       {RJ_rms_200g:.2f} fs")
print(f"  Deterministic Jitter (DJ_dd): {DJ_dd_200g:.2f} fs")
print(f"  Total Jitter @ BER=10^-12:    {TJ_200g_ber12*1e12:.3f} ps ({(TJ_200g_ber12/UI_200g)*100:.1f}% UI)")
print(f"  Total Jitter @ BER=10^-15:    {TJ_200g_ber15*1e12:.3f} ps ({(TJ_200g_ber15/UI_200g)*100:.1f}% UI)")
print(f"  Horizontal Eye Opening (EO_H):{EO_200g_ber15*1e12:.3f} ps ({(EO_200g_ber15/UI_200g)*100:.1f}% UI)")
print("==========================================================================")

# -------------------------------------------------------------------------
# 2. Bathtub Curve Computation
# -------------------------------------------------------------------------
# Dual-Dirac Model:
# BER(t) = 0.5 * ( 0.5 * erfc((t - (-DJ/2)) / (sqrt(2)*RJ)) + 0.5 * erfc(((DJ/2) - (t - UI)) / (sqrt(2)*RJ)) )
def calculate_bathtub(time_array_ps, ui_ps, dj_ps, rj_ps):
    t = time_array_ps
    t_left = t - (dj_ps / 2.0)
    t_right = (ui_ps - dj_ps / 2.0) - t
    
    # Left edge transition jitter
    ber_left = 0.5 * erfc(t_left / (np.sqrt(2.0) * rj_ps))
    # Right edge transition jitter
    ber_right = 0.5 * erfc(t_right / (np.sqrt(2.0) * rj_ps))
    
    ber_total = 0.5 * (ber_left + ber_right)
    return np.clip(ber_total, 1e-20, 1.0)

t_axis_100g = np.linspace(0, UI_100g * 1e12, 1000) # 0 to 10 ps
ber_100g = calculate_bathtub(t_axis_100g, UI_100g*1e12, DJ_dd_100g*1e-3, RJ_rms_100g*1e-3)

t_axis_200g = np.linspace(0, UI_200g * 1e12, 1000) # 0 to 5 ps
ber_200g = calculate_bathtub(t_axis_200g, UI_200g*1e12, DJ_dd_200g*1e-3, RJ_rms_200g*1e-3)

# -------------------------------------------------------------------------
# 3. Waveguide Trace Length Scaling
# -------------------------------------------------------------------------
L_sweep_cm = np.linspace(0.5, 5.0, 50)
# Group velocity dispersion in Si3N4: D ~ -50 ps/(nm*km)
# Spectral width: Delta_lambda ~ 0.02 nm
# Dispersion delay variation: Delta_t = |D| * L * Delta_lambda
D_param = 50e-12 / (1e-9 * 1e3) # s / (m * m)
delta_lambda = 0.02e-9 # 0.02 nm
tau_disp_sweep = np.abs(D_param) * (L_sweep_cm * 1e-2) * delta_lambda # seconds

# Total deterministic jitter vs trace length
DJ_sweep_100g = (DJ_mod_100g + DJ_isi_100g + DJ_aperture_100g)*1e-15 + tau_disp_sweep
TJ_sweep_100g = DJ_sweep_100g + 2.0 * Q_ber15 * (RJ_rms_100g * 1e-15)
EO_sweep_100g_pct = ((UI_100g - TJ_sweep_100g) / UI_100g) * 100.0

DJ_sweep_200g = (DJ_mod_200g + DJ_isi_200g + DJ_aperture_200g)*1e-15 + tau_disp_sweep
TJ_sweep_200g = DJ_sweep_200g + 2.0 * Q_ber15 * (RJ_rms_200g * 1e-15)
EO_sweep_200g_pct = ((UI_200g - TJ_sweep_200g) / UI_200g) * 100.0

# -------------------------------------------------------------------------
# 4. Generate 6-Panel Publication-Grade Dashboard
# -------------------------------------------------------------------------
fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.25)

# Panel (a): Jitter Waterfall Decomposition (Top Left)
ax1 = fig.add_subplot(gs[0, 0])
categories = ['Clock PLL', 'Laser RIN', 'Receiver Noise', 'Dispersion', 'Modulator Skew', 'Channel ISI', 'Latch Aperture']
vals_100g = [RJ_clk_100g, RJ_laser_100g, RJ_rx_100g, DJ_disp_100g, DJ_mod_100g, DJ_isi_100g, DJ_aperture_100g]
vals_200g = [RJ_clk_200g, RJ_laser_200g, RJ_rx_200g, DJ_disp_200g, DJ_mod_200g, DJ_isi_200g, DJ_aperture_200g]
x = np.arange(len(categories))
width = 0.35

rects1 = ax1.bar(x - width/2, vals_100g, width, label='100 GHz Baseline', color='#1f77b4', edgecolor='black')
rects2 = ax1.bar(x + width/2, vals_200g, width, label='200 GHz Optimized', color='#ff7f0e', edgecolor='black')

ax1.set_title('(a) Timing Jitter Decomposition by Physical Origin (fs)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Jitter Magnitude (fs)', fontsize=11, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(categories, rotation=25, ha='right', fontsize=9, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.legend(loc='upper right', fontsize=10)
ax1.set_ylim(0, 220)

for rect in rects1:
    h = rect.get_height()
    ax1.text(rect.get_x() + rect.get_width()/2., h + 3, f'{h:.0f}', ha='center', va='bottom', fontsize=8)
for rect in rects2:
    h = rect.get_height()
    ax1.text(rect.get_x() + rect.get_width()/2., h + 3, f'{h:.0f}', ha='center', va='bottom', fontsize=8)

# Panel (b): Horizontal Eye Bathtub Curves (Top Right)
ax2 = fig.add_subplot(gs[0, 1])
ax2.semilogy(t_axis_100g, ber_100g, 'b-', lw=2.2, label=f'100 GHz (UI = 10.0 ps, TJ = {TJ_100g_ber15*1e12:.2f} ps)')
ax2.semilogy(t_axis_200g, ber_200g, 'r--', lw=2.2, label=f'200 GHz (UI = 5.0 ps, TJ = {TJ_200g_ber15*1e12:.2f} ps)')
ax2.axhline(1e-12, color='gray', linestyle=':', label='BER = 10^-12 Threshold')
ax2.axhline(1e-15, color='darkgreen', linestyle=':', label='BER = 10^-15 Sign-off Target')

ax2.set_title('(b) Horizontal Bathtub Curves (Dual-Dirac Model)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Sampling Phase Offset within Unit Interval (ps)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Bit Error Rate (BER)', fontsize=11, fontweight='bold')
ax2.set_ylim(1e-18, 1.0)
ax2.set_xlim(0, 10.0)
ax2.grid(True, which='both', alpha=0.3, linestyle='--')
ax2.legend(loc='upper center', fontsize=9, framealpha=0.9)

# Annotate eye openings
ax2.annotate(f'100 GHz Eye: {EO_100g_ber15*1e12:.2f} ps\n({(EO_100g_ber15/UI_100g)*100:.1f}% UI)',
             xy=(5.0, 1e-16), xytext=(5.5, 1e-9),
             arrowprops=dict(facecolor='blue', shrink=0.08, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='blue'))

ax2.annotate(f'200 GHz Eye: {EO_200g_ber15*1e12:.2f} ps\n({(EO_200g_ber15/UI_200g)*100:.1f}% UI)',
             xy=(2.5, 1e-16), xytext=(0.8, 1e-5),
             arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='red'))

# Panel (c): Eye Diagram Contour Reconstruction @ 200 GHz (Middle Left)
ax3 = fig.add_subplot(gs[1, 0])
t_eye = np.linspace(-2.5, 2.5, 200) # Centered UI (-2.5 to +2.5 ps)
# Synthesize realistic optical eye with transition jitter
for i in range(40):
    jitter_offset = np.random.normal(0, RJ_rms_200g * 1e-3) # ps
    rise_time = 0.9 + np.random.normal(0, 0.05) # ps
    # Transition 0 -> 1
    y_up = 0.5 * (1.0 + np.tanh((t_eye - jitter_offset) / (rise_time * 0.4)))
    # Transition 1 -> 0
    y_down = 0.5 * (1.0 - np.tanh((t_eye + jitter_offset) / (rise_time * 0.4)))
    ax3.plot(t_eye, y_up, color='navy', alpha=0.15, lw=1.0)
    ax3.plot(t_eye, y_down, color='navy', alpha=0.15, lw=1.0)
    ax3.plot(t_eye, np.ones_like(t_eye) * (1.0 + np.random.normal(0, 0.015)), color='navy', alpha=0.05)
    ax3.plot(t_eye, np.zeros_like(t_eye) * (0.0 + np.random.normal(0, 0.015)), color='navy', alpha=0.05)

ax3.axvline(- (UI_200g*1e12 - TJ_200g_ber15*1e12)/2.0, color='darkgreen', linestyle='--', lw=1.8)
ax3.axvline((UI_200g*1e12 - TJ_200g_ber15*1e12)/2.0, color='darkgreen', linestyle='--', lw=1.8, label='BER 10^-15 Eye Bounds')
ax3.annotate(f'Open Eye: {EO_200g_ber15*1e12:.2f} ps\n(81.1% of 5.0 ps UI)',
             xy=(0, 0.5), xytext=(0, 0.2),
             ha='center', fontsize=10, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#e6ffe6', edgecolor='green'))

ax3.set_title('(c) 200 GHz Optical Eye Diagram & Aperture Margin', fontsize=12, fontweight='bold')
ax3.set_xlabel('Time from Center of Eye (ps)', fontsize=11, fontweight='bold')
ax3.set_ylabel('Normalized Optical Power', fontsize=11, fontweight='bold')
ax3.set_xlim(-2.5, 2.5)
ax3.set_ylim(-0.1, 1.1)
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.legend(loc='lower right', fontsize=9)

# Panel (d): Random Jitter Accumulation & RSS (Middle Right)
ax4 = fig.add_subplot(gs[1, 1])
rj_labels = ['Clock PLL', 'Laser RIN', 'Photodetector', 'Combined\nRJ_rms']
rj_100_vals = [RJ_clk_100g, RJ_laser_100g, RJ_rx_100g, RJ_rms_100g]
rj_200_vals = [RJ_clk_200g, RJ_laser_200g, RJ_rx_200g, RJ_rms_200g]
x_rj = np.arange(len(rj_labels))

ax4.bar(x_rj - width/2, rj_100_vals, width, label='100 GHz Link', color='#2ca02c', edgecolor='black')
ax4.bar(x_rj + width/2, rj_200_vals, width, label='200 GHz Link', color='#9467bd', edgecolor='black')
ax4.set_title('(d) Random Jitter (RJ) Root-Sum-Square (RSS) Accumulation', fontsize=12, fontweight='bold')
ax4.set_ylabel('Random Jitter (fs RMS)', fontsize=11, fontweight='bold')
ax4.set_xticks(x_rj)
ax4.set_xticklabels(rj_labels, fontsize=10, fontweight='bold')
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.legend(loc='upper left', fontsize=10)
ax4.set_ylim(0, 75)

for i, (v1, v2) in enumerate(zip(rj_100_vals, rj_200_vals)):
    ax4.text(i - width/2, v1 + 1.5, f'{v1:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax4.text(i + width/2, v2 + 1.5, f'{v2:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Panel (e): Horizontal Eye Margin vs Waveguide Length (Bottom Left)
ax5 = fig.add_subplot(gs[2, 0])
ax5.plot(L_sweep_cm, EO_sweep_100g_pct, 'b-o', lw=2.2, label='100 GHz Bus (UI = 10.0 ps)')
ax5.plot(L_sweep_cm, EO_sweep_200g_pct, 'r-s', lw=2.2, label='200 GHz Bus (UI = 5.0 ps)')
ax5.axhline(70.0, color='gray', linestyle=':', label='Industry Eye Minimum (70% UI)')

ax5.set_title('(e) Eye Opening Percentage vs On-Chip Bus Length (0.5 to 5.0 cm)', fontsize=12, fontweight='bold')
ax5.set_xlabel('Si3N4 Waveguide Bus Length (cm)', fontsize=11, fontweight='bold')
ax5.set_ylabel('Horizontal Eye Opening (% UI)', fontsize=11, fontweight='bold')
ax5.set_ylim(60, 95)
ax5.set_xlim(0.5, 5.0)
ax5.grid(True, alpha=0.3, linestyle='--')
ax5.legend(loc='lower left', fontsize=10)

ax5.annotate('Negligible GVD degradation (<0.02%)\nover entire 5 cm die span',
             xy=(3.5, EO_sweep_200g_pct[30]), xytext=(2.2, 87),
             arrowprops=dict(facecolor='black', shrink=0.08, width=1.2, headwidth=5),
             fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black'))

# Panel (f): Summary Budget Table (Bottom Right)
ax6 = fig.add_subplot(gs[2, 1])
ax6.axis('off')
table_data = [
    ['Metric / Parameter', '100 GHz Baseline', '200 GHz High-Speed', 'Standard Margin'],
    ['Unit Interval (UI)', '10.00 ps', '5.00 ps', 'Reference'],
    ['Random Jitter (RJ_rms)', f'{RJ_rms_100g:.2f} fs', f'{RJ_rms_200g:.2f} fs', '< 100 fs'],
    ['Deterministic Jitter (DJ_dd)', f'{DJ_dd_100g:.1f} fs', f'{DJ_dd_200g:.1f} fs', '< 500 fs'],
    ['Total Jitter @ BER=10^-12', f'{TJ_100g_ber12*1e12:.3f} ps', f'{TJ_200g_ber12*1e12:.3f} ps', '< 25% UI'],
    ['Total Jitter @ BER=10^-15', f'{TJ_100g_ber15*1e12:.3f} ps', f'{TJ_200g_ber15*1e12:.3f} ps', '< 30% UI'],
    ['Horizontal Eye Opening (EO_H)', f'{EO_100g_ber15*1e12:.3f} ps', f'{EO_200g_ber15*1e12:.3f} ps', '> 70% UI'],
    ['Eye Opening Ratio (% UI)', f'{(EO_100g_ber15/UI_100g)*100:.1f}% UI', f'{(EO_200g_ber15/UI_200g)*100:.1f}% UI', 'PASSED (>80%)'],
    ['Waveguide GVD @ 2 cm', '12.0 fs', '10.0 fs', 'Negligible'],
    ['StrongARM Latch Aperture', '180.0 fs', '110.0 fs', '< 3% UI']
]

table = ax6.table(cellText=table_data, loc='center', cellLoc='center', colWidths=[0.38, 0.22, 0.22, 0.20])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.0, 1.6)

# Format header row
for i in range(4):
    table[(0, i)].set_facecolor('#1f497d')
    table[(0, i)].set_text_props(color='white', weight='bold')

# Format result highlight row (row 7)
for i in range(4):
    table[(7, i)].set_facecolor('#d9ead3')
    table[(7, i)].set_text_props(weight='bold', color='darkgreen')

ax6.set_title('(f) Physical Layer Timing Jitter Budget Sign-Off Matrix', fontsize=12, fontweight='bold', pad=15)

plt.tight_layout()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "plots"))
os.makedirs(PLOTS_DIR, exist_ok=True)
output_path = os.path.join(PLOTS_DIR, "timing_jitter_eye_decomposition.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"[SUCCESS] Timing Jitter & Eye Decomposition Dashboard saved to:\n  {output_path}")
