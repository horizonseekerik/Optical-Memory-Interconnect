import os
"""
simulate_8wg_meep.py
Module 1: MEEP 2D FDTD Simulation of 8 Parallel Si3N4 Waveguides & 2 cm Coupled-Mode Extrapolation

Physical Specifications:
- 8 Parallel Si3N4 Rib Waveguides (w = 800 nm, pitch P = 1.5 um, gap g = 700 nm)
- Material Indices: Si3N4 core n_core = 2.01 (eps = 4.0401), SiO2 cladding n_clad = 1.444 (eps = 2.0851)
- Operating Wavelength: lambda = 1064 nm (freq = 1 / 1.064 = 0.93985 um^-1)
- Source: Fundamental mode pulse launched into Lane 3
- Extraction: Measures transmission and evanescent cross-coupling across all 8 lanes.
- Extrapolation: Integrates 8-channel Coupled-Mode Theory (CMT) over the user's 2.0 cm macroscopic link.
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.linalg import expm

try:
    import meep as mp
except ImportError:
    print("[ERROR] MEEP is not installed in this environment. Please run via WSL python3.")
    sys.exit(1)

# -------------------------------------------------------------------------
# 1. Simulation Parameters
# -------------------------------------------------------------------------
lambda_0 = 1.064         # um
f_0 = 1.0 / lambda_0     # ~0.93985 um^-1
df = 0.1 * f_0           # Pulse bandwidth

w_core = 0.80            # 800 nm core width
pitch = 1.50             # 1.5 um center-to-center pitch
gap = pitch - w_core     # 700 nm gap
N_lanes = 8              # 8 waveguides

# Material dielectric constants
eps_core = 2.01**2       # 4.0401 (Si3N4)
eps_clad = 1.444**2      # 2.0851 (SiO2)

core_mat = mp.Medium(epsilon=eps_core)
clad_mat = mp.Medium(epsilon=eps_clad)

# Cell geometry
dpml = 1.5               # 1.5 um PML thickness
L_sim = 25.0             # 25 um active propagation length
sx = L_sim + 2 * dpml    # 28 um total length
sy = N_lanes * pitch + 2 * dpml + 2.0  # ~17 um total height
cell = mp.Vector3(sx, sy, 0)

# Waveguide y-coordinates (centered at y = 0)
# y_i = (i - (N_lanes - 1)/2) * pitch
y_centers = [(i - (N_lanes - 1) / 2.0) * pitch for i in range(N_lanes)]
lanes_idx = list(range(N_lanes))

print("==========================================================================")
print("MODULE 1: MEEP 8-PARALLEL WAVEGUIDE ARRAY SIMULATION (lambda = 1064 nm)")
print("==========================================================================")
print(f"Number of Waveguides:            {N_lanes}")
print(f"Waveguide Core Width:            {w_core*1e3:.0f} nm")
print(f"Inter-Waveguide Pitch:           {pitch*1e3:.0f} nm")
print(f"Inter-Waveguide Gap:             {gap*1e3:.0f} nm")
print(f"Si3N4 Core Index:                {np.sqrt(eps_core):.3f}")
print(f"SiO2 Cladding Index:             {np.sqrt(eps_clad):.3f}")
print(f"Input Active Lane:               Lane 3 (y = {y_centers[3]:.2f} um)")
print(f"FDTD Domain Size:                {sx:.1f} um x {sy:.1f} um")
print("--------------------------------------------------------------------------")

# Build 8 parallel waveguides extending infinitely along x
geometry = []
for y_c in y_centers:
    wg_block = mp.Block(
        center=mp.Vector3(0, y_c, 0),
        size=mp.Vector3(mp.inf, w_core, mp.inf),
        material=core_mat
    )
    geometry.append(wg_block)

# Boundary condition: PML on all borders
pml_layers = [mp.PML(dpml)]

# Source: Continuous Gaussian pulse injected into Lane 3
src_x = -sx / 2.0 + dpml + 1.0
src_y = y_centers[3]
sources = [
    mp.Source(
        src=mp.GaussianSource(f_0, fwidth=df),
        component=mp.Ez,
        center=mp.Vector3(src_x, src_y, 0),
        size=mp.Vector3(0, w_core, 0)
    )
]

resolution = 30  # 30 pixels per um (dt = dx / 2 ~ 16 nm spatial step)
sim = mp.Simulation(
    cell_size=cell,
    boundary_layers=pml_layers,
    geometry=geometry,
    default_material=clad_mat,
    sources=sources,
    resolution=resolution
)

# Add output flux monitors across each of the 8 waveguides
mon_x = sx / 2.0 - dpml - 1.0
flux_regions = []
for y_c in y_centers:
    fr = mp.FluxRegion(
        center=mp.Vector3(mon_x, y_c, 0),
        size=mp.Vector3(0, w_core * 1.5, 0)
    )
    flux_regions.append(fr)

trans_fluxes = [sim.add_flux(f_0, 0, 1, fr) for fr in flux_regions]

# Run simulation until pulse propagates and clears through domain
print("Launching MEEP FDTD wave propagation...")
sim.run(until=80.0)

# Extract power flux at the central frequency
power_out = [mp.get_fluxes(tf)[0] for tf in trans_fluxes]
power_out = np.maximum(power_out, 1e-15)  # Avoid negative or zero numerical noise

P_injected = power_out[3]  # Main lane (Lane 3)
xt_dB_sim = [10.0 * np.log10(p / P_injected) for p in power_out]

print("--------------------------------------------------------------------------")
print(f"MEEP Results after L_sim = {L_sim:.1f} um propagation:")
for i in range(N_lanes):
    print(f"   Waveguide Lane {i} (y = {y_centers[i]:5.2f} um): Relative Power = {xt_dB_sim[i]:6.2f} dB")

# -------------------------------------------------------------------------
# 2. Evanescent Coupling Coefficient & 2 cm Coupled-Mode Theory (CMT)
# -------------------------------------------------------------------------
# Nearest-neighbor coupling power: P_neighbor / P_0 ~ (kappa * L_sim)^2
P_neighbor = max(power_out[2], power_out[4])
ratio = max(P_neighbor / P_injected, 1e-12)
kappa = np.arcsin(np.clip(np.sqrt(ratio), 0.0, 1.0)) / L_sim  # in um^-1
print("--------------------------------------------------------------------------")
print(f"Extracted Coupling Coefficient kappa: {kappa:.6e} um^-1 ({kappa * 1e3:.4f} mm^-1)")

# Assemble 8x8 Coupled-Mode Interaction Matrix M:
# d A / dz = -j * M * A
# where M is tridiagonal with beta on diagonal and kappa on off-diagonals
M_mat = np.zeros((N_lanes, N_lanes), dtype=complex)
beta = 2.0 * np.pi * np.sqrt(eps_core) / lambda_0
for i in range(N_lanes):
    M_mat[i, i] = beta
    if i > 0:
        M_mat[i, i - 1] = kappa
    if i < N_lanes - 1:
        M_mat[i, i + 1] = kappa

# Propagate across macroscopic length L_macro = 2.0 cm = 20,000 um
L_macro = 20000.0  # um
z_points = np.linspace(0, L_macro, 500)
# Initial state: 1.0 in Lane 3, 0 in all others
A_0 = np.zeros(N_lanes, dtype=complex)
A_0[3] = 1.0

# Calculate power in each lane vs z
P_z = np.zeros((len(z_points), N_lanes))
for idx, z in enumerate(z_points):
    # Propagator: U(z) = exp(-j * M * z)
    U_z = expm(-1j * M_mat * z)
    A_z = U_z @ A_0
    P_z[idx, :] = np.abs(A_z)**2

# Final power at z = 2.0 cm (20,000 um)
P_final = P_z[-1, :]
xt_final_dB = [10.0 * np.log10(p / P_final[3]) if i != 3 else 0.0 for i, p in enumerate(P_final)]

print("--------------------------------------------------------------------------")
print("Coupled-Mode Extrapolation across L = 2.0 cm (20,000 um):")
print(f"   Lane 3 (Primary Signal):     {10*np.log10(P_final[3]):.3f} dB ({P_final[3]*100:.2f}% power)")
print(f"   Lane 2 (Nearest Neighbor):   {xt_final_dB[2]:.2f} dB")
print(f"   Lane 4 (Nearest Neighbor):   {xt_final_dB[4]:.2f} dB")
print(f"   Lane 1 (Next-Neighbor):      {xt_final_dB[1]:.2f} dB")
print(f"   Lane 5 (Next-Neighbor):      {xt_final_dB[5]:.2f} dB")
worst_xt_neighbor = max(xt_final_dB[2], xt_final_dB[4])
print(f"   -> Worst-Case Neighbor XT:   {worst_xt_neighbor:.2f} dB (Specification: < -45.0 dB)")
print("==========================================================================")

# -------------------------------------------------------------------------
# 3. Plot Field Distribution and 2 cm Power Evolution
# -------------------------------------------------------------------------
# Get 2D Ez field from MEEP
ez_data = sim.get_array(center=mp.Vector3(), size=cell, component=mp.Ez)
ez_intensity = np.abs(ez_data)**2

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), gridspec_kw={'height_ratios': [1, 1.2]})

# Plot 1: MEEP 2D Electric Field Intensity |Ez|^2
extent = [-sx / 2.0, sx / 2.0, -sy / 2.0, sy / 2.0]
im = ax1.imshow(ez_intensity.T, interpolation='spline36', cmap='inferno', extent=extent, origin='lower')
for y_c in y_centers:
    ax1.axhline(y_c - w_core / 2.0, color='cyan', linestyle=':', alpha=0.4)
    ax1.axhline(y_c + w_core / 2.0, color='cyan', linestyle=':', alpha=0.4)
ax1.set_title("MEEP 2D FDTD Optical Field Intensity |Ez|^2 across 8 Waveguides (lambda = 1064 nm)", fontsize=11, fontweight="bold")
ax1.set_xlabel("Axial Position x (um)", fontsize=10)
ax1.set_ylabel("Lateral Position y (um)", fontsize=10)
fig.colorbar(im, ax=ax1, label="Normalized |Ez|^2", fraction=0.02, pad=0.02)

# Plot 2: 2 cm Optical Power Evolution across 8 Lanes
z_mm = z_points / 1000.0  # convert to mm
for i in range(N_lanes):
    if i == 3:
        ax2.plot(z_mm, P_z[:, i], label=f"Lane 3 (Signal)", color='tab:red', linewidth=2.5)
    else:
        ax2.plot(z_mm, P_z[:, i], label=f"Lane {i} (XT)", linestyle='--', linewidth=1.2)

ax2.set_title("Coupled-Mode Power Evolution across L = 2.0 cm (20,000 um) Waveguide Bus", fontsize=11, fontweight="bold")
ax2.set_xlabel("Propagation Distance z (mm)", fontsize=10)
ax2.set_ylabel("Normalized Optical Power", fontsize=10)
ax2.set_yscale("log")
ax2.set_ylim(1e-8, 1.2)
ax2.grid(True, which="both", linestyle="--", alpha=0.5)
ax2.legend(loc="upper right", ncol=4, fontsize=9)

plt.tight_layout()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "plots"))
os.makedirs(PLOTS_DIR, exist_ok=True)
output_img = os.path.join(PLOTS_DIR, "meep_8wg_crosstalk_2cm.png")
plt.savefig(output_img, dpi=300)
print(f"[SUCCESS] Field and 2 cm evolution plot saved to: {output_img}")
print("==========================================================================\n")
