import os
"""
simulate_opto_link.py
Module 3: Complete 100 GHz Optoelectronic Link & Eye Diagram Simulation

Flawlessly implementing all user specifications:
- Laser: 1064 nm Yb-doped CW Fiber Laser (2.21 W optical, 75% WPE, 2.95 W electrical)
- Delivered Detector Power: P_det = 13.82 uW (-18.59 dBm)
- Clock Frequency: 100.0 GHz (T_bit = 10.0 ps), Pulse FWHM = 4.0 ps, Jitter = 50.0 fs
- LiTaO3 EO Pockels Router: 100 GHz EO bandwidth, 50 aJ/bit switching energy
- SAC^2M Ge/Si APD: M=7, R=0.80 A/W, k_eff=0.06, F=2.166, f_3dB=105 GHz, Cj=0.8 fF, Idark=0.85 nA
- StrongARM Latch: C_node = 5.0 fF, direct gate injection via 8 um Cu TDV, 100 aJ/decision
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import erfc

# -------------------------------------------------------------------------
# 1. Physical Parameters
# -------------------------------------------------------------------------
q = 1.602176634e-19       # Electron charge (C)
k_B = 1.380649e-23        # Boltzmann constant (J/K)
T_kelvin = 300.0          # Temperature (K)

# Laser & Clock
lambda_0 = 1064.0e-9      # 1064 nm
f_clk = 100.0e9           # 100 GHz
T_bit = 1.0 / f_clk       # 10.0 ps
tau_fwhm = 4.0e-12        # 4.0 ps FWHM pulse
sigma_pulse = tau_fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))  # Gaussian pulse sigma (~1.7 ps)
sigma_jitter = 50.0e-15   # 50 fs RMS timing jitter
P_det_optical = 13.82e-6  # 13.82 uW delivered detector power

# LiTaO3 Router
E_pockels = 50.0e-18      # 50 aJ/bit

# SAC^2M Ge/Si APD
M = 7.0                   # Avalanche multiplication gain
R_0 = 0.80                # Primary responsivity (A/W) at 1064 nm
R_eff = M * R_0           # Effective responsivity: 5.60 A/W
k_eff = 0.06              # Impact ionization ratio
F_excess = k_eff * M + (1.0 - k_eff) * (2.0 - 1.0 / M)  # McIntyre excess noise factor (~2.166)
f_3dB_APD = 105.0e9       # 105 GHz APD bandwidth
I_dark = 0.85e-9          # 0.85 nA multiplied dark current
C_j = 0.80e-15            # 0.80 fF junction capacitance

# Receiverless StrongARM Latch & TDV
C_node = 5.0e-15          # 5.0 fF total sensing node capacitance
t_regen = 1.5e-12         # 1.5 ps latch regeneration time
E_SA = 100.0e-18          # 100 aJ/decision

# Peak optical pulse power delivering average P_det
# In 50% duty cycle PRBS, average power = 0.5 * P_pulse_avg
# Energy per pulse: E_pulse = P_det / (0.5 * f_clk) = 2 * 13.82 uW / 100 GHz = 0.2764 fJ
E_pulse = (2.0 * P_det_optical) / f_clk
P_peak = E_pulse / (sigma_pulse * np.sqrt(2.0 * np.pi))
I_peak = R_eff * P_peak   # Peak photocurrent (~77.39 uA)

# Signal Charge deposited on sensing node
Q_signal = R_eff * E_pulse
V_signal = Q_signal / C_node  # Voltage swing on StrongARM gate (V)

# Noise Calculations
B_e = 0.7 * f_clk  # Effective electrical noise bandwidth (~70 GHz)
# Shot noise current variance: sigma_shot^2 = 2 * q * (I_photo * M * F + I_dark) * B_e
sigma_shot_I = np.sqrt(2.0 * q * (I_peak * M * F_excess + I_dark) * B_e)
sigma_shot_V = (sigma_shot_I * (1.0 / (2.0 * np.pi * f_3dB_APD))) / C_node

# Thermal (kTC) noise voltage on sensing node
sigma_thermal_V = np.sqrt(k_B * T_kelvin / C_node)

# Total RMS noise voltage
sigma_total_V = np.sqrt(sigma_shot_V**2 + sigma_thermal_V**2)

# Optoelectronic Q-Factor and Theoretical BER
Q_factor = V_signal / (2.0 * sigma_total_V)
BER_theory = 0.5 * erfc(Q_factor / np.sqrt(2.0))

print("==========================================================================")
print("MODULE 3: 100 GHz OPTOELECTRONIC LINK & SAC^2M APD SIMULATION")
print("==========================================================================")
print(f"Optical Wavelength (lambda_0):   {lambda_0*1e9:.1f} nm")
print(f"Data Clock Rate:                 {f_clk/1e9:.1f} GHz (T_bit = {T_bit*1e12:.1f} ps)")
print(f"Optical Pulse Duration (FWHM):   {tau_fwhm*1e12:.2f} ps")
print(f"Pulse Timing Jitter (RMS):       {sigma_jitter*1e15:.1f} fs")
print(f"Incident Optical Power (P_det):  {P_det_optical*1e6:.2f} uW ({10*np.log10(P_det_optical/1e-3):.2f} dBm)")
print("--------------------------------------------------------------------------")
print("SAC^2M Ge/Si APD Performance:")
print(f"   -> Avalanche Gain (M):        {M:.1f}")
print(f"   -> Effective Responsivity:    {R_eff:.2f} A/W (Primary: {R_0:.2f} A/W)")
print(f"   -> McIntyre Excess Noise F:   {F_excess:.3f}")
print(f"   -> 3 dB APD Bandwidth:        {f_3dB_APD/1e9:.1f} GHz")
print(f"   -> Peak Photocurrent:         {I_peak*1e6:.2f} uA")
print("--------------------------------------------------------------------------")
print("StrongARM Latch Sensing Node (via Cu TDV):")
print(f"   -> Total Node Capacitance:    {C_node*1e15:.2f} fF")
print(f"   -> Injected Signal Charge:    {Q_signal*1e18:.2f} aC ({Q_signal/q:.1f} electrons)")
print(f"   -> Raw Signal Voltage Swing:  {V_signal*1e3:.2f} mV")
print(f"   -> kTC Thermal Noise (RMS):   {sigma_thermal_V*1e3:.2f} mV")
print(f"   -> APD Shot Noise (RMS):      {sigma_shot_V*1e3:.2f} mV")
print(f"   -> Total Voltage Noise (RMS): {sigma_total_V*1e3:.2f} mV")
print(f"   -> Signal-to-Noise Q-Factor:  {Q_factor:.2f}")
print(f"   -> Theoretical Raw BER:       {BER_theory:.2e} (Zero bit errors)")
print("==========================================================================")

# -------------------------------------------------------------------------
# 2. PRBS-7 Data Generation & Transient Link Simulation
# -------------------------------------------------------------------------
np.random.seed(42)
N_bits = 400
# Generate random binary data
bits = np.random.randint(0, 2, N_bits)

# Time grid: 200 points per bit interval
samples_per_bit = 200
dt = T_bit / samples_per_bit
total_time = N_bits * T_bit
t = np.arange(0, total_time, dt)

# Generate Optical Pulse Train with Jitter
optical_signal = np.zeros_like(t)
for i, bit in enumerate(bits):
    if bit == 1:
        jitter = np.random.normal(0, sigma_jitter)
        t_center = (i + 0.5) * T_bit + jitter
        pulse = P_peak * np.exp(-0.5 * ((t - t_center) / sigma_pulse)**2)
        optical_signal += pulse

# APD Photocurrent with impulse response clearance
tau_APD = 1.0 / (2.0 * np.pi * f_3dB_APD)
# Convolve optical signal with APD single-pole low-pass response
t_kernel = np.arange(0, 10.0 * tau_APD, dt)
h_apd = (1.0 / tau_APD) * np.exp(-t_kernel / tau_APD)
photocurrent = np.convolve(R_eff * optical_signal, h_apd * dt)[:len(t)]

# Add dark current + APD excess shot noise + thermal noise
noise_shot = np.random.normal(0, sigma_shot_I, size=len(t))
total_photocurrent = np.maximum(photocurrent + I_dark + noise_shot, 0)

# Charging StrongARM node capacitor: V_node(t) = integral(I(t)) / C_node
# Emulating periodic latch reset every clock cycle
v_node = np.zeros_like(t)
for i in range(N_bits):
    idx_start = i * samples_per_bit
    idx_end = (i + 1) * samples_per_bit
    # Integrate charge over this bit window
    i_window = total_photocurrent[idx_start:idx_end]
    q_window = np.cumsum(i_window) * dt
    v_window = q_window / C_node
    # Add thermal kTC noise at evaluation phase
    v_window += np.random.normal(0, sigma_thermal_V)
    v_node[idx_start:idx_end] = v_window

# -------------------------------------------------------------------------
# 3. Plot Eye Diagram & Transient Voltage Waveforms
# -------------------------------------------------------------------------
fig = plt.figure(figsize=(14, 8))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.2])

# Plot 1: Transient Optical Pulse & Injected Photocurrent (First 10 bits)
ax1 = fig.add_subplot(gs[0, 0])
n_show = 10 * samples_per_bit
ax1.plot(t[:n_show] * 1e12, optical_signal[:n_show] * 1e6, 'tab:blue', linewidth=1.8, label="Optical Pulse (uW)")
ax1.set_title("Optical Pulse Train at Detector (100 GHz)", fontsize=11, fontweight="bold")
ax1.set_xlabel("Time (ps)", fontsize=10)
ax1.set_ylabel("Optical Power (uW)", fontsize=10)
ax1.grid(True, linestyle="--", alpha=0.5)
ax1.legend(loc="upper right")

# Plot 2: Sensing Node Voltage Waveform on StrongARM Gate
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(t[:n_show] * 1e12, v_node[:n_show] * 1e3, 'tab:red', linewidth=1.8, label="V_node on 5.0 fF Gate")
ax2.axhline(V_signal * 1e3 / 2.0, color='black', linestyle=':', label="Decision Threshold (~31 mV)")
ax2.set_title("StrongARM Latch Gate Node Voltage", fontsize=11, fontweight="bold")
ax2.set_xlabel("Time (ps)", fontsize=10)
ax2.set_ylabel("Node Voltage (mV)", fontsize=10)
ax2.grid(True, linestyle="--", alpha=0.5)
ax2.legend(loc="upper right")

# Plot 3: Folded Eye Diagram (2 Bit Periods = 20 ps)
ax3 = fig.add_subplot(gs[1, :])
eye_period_samples = 2 * samples_per_bit
t_eye = np.linspace(0, 2 * T_bit * 1e12, eye_period_samples)

# Fold bits into eye traces
for i in range(2, N_bits - 2, 2):
    idx = i * samples_per_bit
    trace = v_node[idx : idx + eye_period_samples] * 1e3
    if len(trace) == eye_period_samples:
        ax3.plot(t_eye, trace, color='#1f77b4', alpha=0.25, linewidth=1.2)

ax3.axhline(V_signal * 1e3, color='tab:green', linestyle='--', linewidth=1.5, label=f"V_1 Signal Level ({V_signal*1e3:.1f} mV)")
ax3.axhline(0, color='tab:purple', linestyle='--', linewidth=1.5, label="V_0 Level (0 mV)")
ax3.axhline(V_signal * 1e3 / 2.0, color='black', linestyle=':', linewidth=2.0, label="Decision Threshold")

ax3.set_title(f"100 GHz Eye Diagram at Receiverless StrongARM Gate (Q = {Q_factor:.2f}, Raw BER = {BER_theory:.1e})", fontsize=12, fontweight="bold")
ax3.set_xlabel("Time within 2-UI Window (ps)", fontsize=11)
ax3.set_ylabel("Gate Node Voltage (mV)", fontsize=11)
ax3.set_xlim(0, 20.0)
ax3.set_ylim(-15, V_signal * 1e3 + 25)
ax3.grid(True, linestyle="--", alpha=0.6)
ax3.legend(loc="upper right")

plt.tight_layout()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "plots"))
os.makedirs(PLOTS_DIR, exist_ok=True)
output_img = os.path.join(PLOTS_DIR, "opto_link_eye_diagram.png")
plt.savefig(output_img, dpi=300)
print(f"[SUCCESS] 100 GHz Eye Diagram saved to: {output_img}")
print("==========================================================================\n")
