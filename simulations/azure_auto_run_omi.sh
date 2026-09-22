#!/usr/bin/env bash
# ==============================================================================
# azure_auto_run_omi.sh
# Autonomous Provisioning, Execution, Artifact Sync, and Deletion on Azure
# Designed for Central India Free-Tier CPU (B1s / B2ats_v2)
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Configuration Variables
# ------------------------------------------------------------------------------
RESOURCE_GROUP="rg-omi-simulation"
LOCATION="centralindia"
VM_NAME="vm-omi-sim-8gb"
# Defaults to 4 vCPUs, scalable to large RAM (e.g. Standard_D4s_v5 or Standard_E4s_v5)
VM_SIZE="${AZURE_VM_SIZE:-Standard_D4s_v5}"
IMAGE="Ubuntu2204"
ADMIN_USER="azureuser"
GITHUB_REPO="https://github.com/horizonseekerik/Optical-Memory-Interconnect.git"

echo "================================================================================"
echo "  OMI 8 GB AZURE AUTONOMOUS LIFECYCLE CONTROLLER                                "
echo "================================================================================"
echo "[*] Target Region          : $LOCATION (Central India)"
echo "[*] Resource Group         : $RESOURCE_GROUP"
echo "[*] VM Specification       : $VM_NAME ($VM_SIZE)"
echo "[*] Repository             : $GITHUB_REPO"
echo "--------------------------------------------------------------------------------"

# Step 1: Create Resource Group if not exists
echo "[1/5] Ensuring Resource Group exists in $LOCATION..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output table

# Step 2: Create VM with SSH key generation
echo "[2/5] Provisioning free-tier eligible VM ($VM_SIZE)..."
az vm create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$VM_NAME" \
  --image "$IMAGE" \
  --size "$VM_SIZE" \
  --admin-username "$ADMIN_USER" \
  --generate-ssh-keys \
  --output table

# Step 3: Run the simulation remotely on the VM
echo "[3/5] Executing 8 GB OMI Simulation inside Azure VM..."
az vm run-command invoke \
  --resource-group "$RESOURCE_GROUP" \
  --name "$VM_NAME" \
  --command-id 'RunShellScript' \
  --scripts '
    set -e
    echo "[*] Updating and installing dependencies..."
    sudo apt-get update -y > /dev/null 2>&1
    sudo apt-get install -y python3-pip git > /dev/null 2>&1
    pip3 install numpy matplotlib > /dev/null 2>&1

    echo "[*] Cloning OMI repository..."
    git clone https://github.com/horizonseekerik/Optical-Memory-Interconnect.git /tmp/omi_repo
    cd /tmp/omi_repo

    echo "[*] Running 8 GB Dual-Tier Analytical Endurance Engine..."
    python3 simulations/simulate_8gb_endurance_rotator.py

    echo "[*] Running Option B: Discrete Cell-by-Cell Physical Monte Carlo Simulation..."
    echo "[*] Harnessing 4 vCPUs and High Memory for 75,600,000 discrete cells..."
    python3 simulations/monte_carlo_discrete_cell_wear.py --cells 75600000 --batches 500 --batch_size 1000000

    echo "[*] All OMI simulations completed successfully inside VM."
  ' --output json

# Step 4: Stop and Deallocate VM (Stops compute billing immediately)
echo "[4/5] Stopping and deallocating VM to prevent any resource charges..."
az vm deallocate --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" --output table

# Step 5: Optional Complete Tear-Down
echo "--------------------------------------------------------------------------------"
echo "[5/5] AUTONOMOUS EXECUTION FINISHED."
echo "To completely DELETE all Azure resources and leave zero trace, run:"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"
echo "================================================================================"
