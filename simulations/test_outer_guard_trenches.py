"""
test_outer_guard_trenches.py
Test whether adding 2 outer guard trenches (9 trenches total vs 7 interior trenches)
makes any measurable difference to the edge waveguides (Lane 0 and Lane 7) compared to standard bulk cladding.
"""

import sys
import numpy as np

try:
    import meep as mp
except ImportError:
    print("[ERROR] MEEP is not installed in this environment.")
    sys.exit(1)

lambda_0 = 1.064
f_0 = 1.0 / lambda_0
df = 0.1 * f_0

w_core = 0.80
pitch = 1.50
gap = pitch - w_core
w_trench = 0.35
N_lanes = 8

eps_core = 2.01**2
eps_clad = 1.444**2
eps_trench = 1.000**2

core_mat = mp.Medium(epsilon=eps_core)
clad_mat = mp.Medium(epsilon=eps_clad)
trench_mat = mp.Medium(epsilon=eps_trench)

dpml = 1.5
L_sim = 25.0
sx = L_sim + 2 * dpml
sy = N_lanes * pitch + 2 * dpml + 4.0  # Extra margin for outer trenches
cell = mp.Vector3(sx, sy, 0)

y_centers = [(i - (N_lanes - 1) / 2.0) * pitch for i in range(N_lanes)]
# 7 interior trenches
y_trenches_7 = [(y_centers[i] + y_centers[i+1]) / 2.0 for i in range(N_lanes - 1)]
# 9 trenches (7 interior + 2 outer guard trenches at +/- 6.0 um)
y_trenches_9 = [y_centers[0] - 0.75] + y_trenches_7 + [y_centers[-1] + 0.75]

def run_simulation(trenches_y, label, launch_lane=0):
    geometry = []
    for y_c in y_centers:
        geometry.append(mp.Block(center=mp.Vector3(0, y_c, 0), size=mp.Vector3(mp.inf, w_core, mp.inf), material=core_mat))
    for y_t in trenches_y:
        geometry.append(mp.Block(center=mp.Vector3(0, y_t, 0), size=mp.Vector3(mp.inf, w_trench, mp.inf), material=trench_mat))
        
    pml_layers = [mp.PML(dpml)]
    src_x = -sx / 2.0 + dpml + 1.0
    src_y = y_centers[launch_lane]
    sources = [
        mp.Source(
            src=mp.GaussianSource(f_0, fwidth=df),
            component=mp.Ez,
            center=mp.Vector3(src_x, src_y, 0),
            size=mp.Vector3(0, w_core, 0)
        )
    ]
    sim = mp.Simulation(
        cell_size=cell,
        boundary_layers=pml_layers,
        geometry=geometry,
        default_material=clad_mat,
        sources=sources,
        resolution=25
    )
    mon_x = sx / 2.0 - dpml - 1.0
    flux_regions = [mp.FluxRegion(center=mp.Vector3(mon_x, y_c, 0), size=mp.Vector3(0, w_core * 1.5, 0)) for y_c in y_centers]
    trans_fluxes = [sim.add_flux(f_0, 0, 1, fr) for fr in flux_regions]
    
    print(f"\nRunning {label} (Exciting edge Lane {launch_lane})...")
    sim.run(until=75.0)
    power_out = [mp.get_fluxes(tf)[0] for tf in trans_fluxes]
    return power_out

print("==========================================================================")
print("TESTING OUTER GUARD TRENCHES VS STANDARD BULK CLADDING FOR EDGE WAVEGUIDES")
print("==========================================================================")

# Run Case A: 7 Interior Trenches (Outer bulk cladding)
power_7 = run_simulation(y_trenches_7, "Case A: 7 Trenches (Bulk Cladding on Edges)", launch_lane=0)

# Run Case B: 9 Trenches (7 Interior + 2 Outer Guard Trenches)
power_9 = run_simulation(y_trenches_9, "Case B: 9 Trenches (Full Outer Guard Trenches)", launch_lane=0)

P0_7 = power_7[0]
P1_7 = power_7[1]
xt_7 = 10.0 * np.log10(max(P1_7, 1e-15) / max(P0_7, 1e-15))

P0_9 = power_9[0]
P1_9 = power_9[1]
xt_9 = 10.0 * np.log10(max(P1_9, 1e-15) / max(P0_9, 1e-15))

diff_throughput_dB = 10.0 * np.log10(P0_9 / P0_7)
diff_xt_dB = xt_9 - xt_7

print("\n==========================================================================")
print("COMPARATIVE RESULTS FOR EDGE LANE (LANE 0):")
print(f"   Case A (7 Trenches, Bulk Cladding):")
print(f"      -> Lane 0 Transmission Power:    {P0_7:.6e}")
print(f"      -> Leakage into Lane 1:          {xt_7:.2f} dB")
print(f"   Case B (9 Trenches, Outer Guard Trenches):")
print(f"      -> Lane 0 Transmission Power:    {P0_9:.6e}")
print(f"      -> Leakage into Lane 1:          {xt_9:.2f} dB")
print("--------------------------------------------------------------------------")
print(f"   Transmission Difference (Lane 0):   {diff_throughput_dB:+.3f} dB")
print(f"   Crosstalk Difference (into Lane 1): {diff_xt_dB:+.3f} dB")
print("--------------------------------------------------------------------------")

if abs(diff_throughput_dB) < 0.2 and abs(diff_xt_dB) < 0.5:
    print("[CONCLUSION] The difference is NEGLIGIBLE (< 0.2 dB).")
    print("             Standard outer bulk SiO2 cladding is already optimal.")
    print("             RECOMMENDATION: REMOVE outer guard trenches and keep 7 clean interior trenches.")
else:
    print("[CONCLUSION] The outer guard trench shows measurable impact.")
    print("             RECOMMENDATION: RETAIN 9 trenches.")
print("==========================================================================")
