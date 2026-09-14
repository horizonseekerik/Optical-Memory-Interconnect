"""
run_all_simulations.py
Batch orchestrator to run all physical simulation models in simulations/
and verify that all generated plots populate plots/.
All paths are dynamically resolved relative to this script.
"""

import os
import sys
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SIMULATIONS_DIR = os.path.join(BASE_DIR, "simulations")
PLOTS_DIR = os.path.join(BASE_DIR, "plots")

os.makedirs(PLOTS_DIR, exist_ok=True)

# List simulation scripts
SIM_SCRIPTS = [
    "simulate_1024_tree_loss.py",
    "simulate_200ghz_omi_system.py",
    "simulate_3d_thermal_stack.py",
    "simulate_8wg_meep.py",
    "simulate_flash_rc.py",
    "simulate_hbm4_vs_omi_comparison.py",
    "simulate_integrated_omi_flash_system.py",
    "simulate_mmi_splitter.py",
    "simulate_opto_link.py",
    "simulate_power_consumption_analysis.py",
    "simulate_readout_arbiter.py",
    "simulate_spatial_parallel_transceiver.py",
    "simulate_talbot_mmi_crossing.py",
    "simulate_trench_isolation.py",
    "test_outer_guard_trenches.py",
    "verify_sbend.py"
]

def run_simulation(script_name):
    script_path = os.path.join(SIMULATIONS_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"[ERROR] Script not found: {script_path}")
        return False

    print(f"\n>> Running: {script_name} ...")
    start = time.time()
    res = subprocess.run([sys.executable, script_path], cwd=SIMULATIONS_DIR)
    dur = time.time() - start
    if res.returncode == 0:
        print(f"[PASS] {script_name} completed in {dur:.2f}s")
        return True
    else:
        print(f"[FAIL] {script_name} exited with code {res.returncode}")
        return False

def main():
    print(f"Base Directory:        {BASE_DIR}")
    print(f"Simulations Directory: {SIMULATIONS_DIR}")
    print(f"Plots Directory:       {PLOTS_DIR}\n")

    results = {}
    for script in SIM_SCRIPTS:
        results[script] = run_simulation(script)

    print("\n=======================================================")
    print("SIMULATION EXECUTION SUMMARY")
    print("=======================================================")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for s, ok in results.items():
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status} {s}")
    print(f"\nOverall: {passed}/{total} simulations passed successfully.")

    # List plots in plots/
    plots = [f for f in os.listdir(PLOTS_DIR) if f.endswith(".png")]
    print(f"Total plots in plots/: {len(plots)}")

if __name__ == "__main__":
    main()
