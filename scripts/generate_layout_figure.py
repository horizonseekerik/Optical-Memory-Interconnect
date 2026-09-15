"""
generate_layout_figure.py
Assembles a publication-grade multi-panel datasheet figure combining:
  1. Main 2.0 mm x 2.0 mm Reticle Layout Overview
  2. 4 High-Resolution Insets (1:8 MMI Tree, LiTaO3 Modulator Bank, Centum TDVs, DTI Bus + APD)
  3. Physical Layer Mask Legend & Tape-Out Specifications Table

Outputs:
  - layout/previews/omi_layout_datasheet.png
"""

import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LAYOUT_DIR = os.path.join(BASE_DIR, "layout")
PREVIEWS_DIR = os.path.join(LAYOUT_DIR, "previews")

img_top = mpimg.imread(os.path.join(PREVIEWS_DIR, "omi_chip_top_overview.png"))
img_mmi = mpimg.imread(os.path.join(PREVIEWS_DIR, "omi_zoom_mmi_tree.png"))
img_mod = mpimg.imread(os.path.join(PREVIEWS_DIR, "omi_zoom_tflt_modulators.png"))
img_tdv = mpimg.imread(os.path.join(PREVIEWS_DIR, "omi_zoom_tdv_constellation.png"))
img_dti = mpimg.imread(os.path.join(PREVIEWS_DIR, "omi_zoom_dti_bus_apd.png"))
img_cpo = mpimg.imread(os.path.join(PREVIEWS_DIR, "omi_zoom_cpo_couplers.png"))
img_tst = mpimg.imread(os.path.join(PREVIEWS_DIR, "omi_zoom_test_structures.png"))

# Create 16:10 high-resolution figure
fig = plt.figure(figsize=(18, 12), dpi=200, facecolor="#1a1a1a")
gs = GridSpec(3, 4, figure=fig, hspace=0.18, wspace=0.15,
              left=0.04, right=0.96, top=0.92, bottom=0.05)

# Main overview: occupies left 2x2
ax_main = fig.add_subplot(gs[0:2, 0:2])
ax_main.imshow(img_top)
ax_main.set_title("(a) Top-Level 8-Channel OMI Reticle Floorplan (2000 um x 2000 um | 4.0 mm^2 MPW Tile)",
                  color="white", fontsize=11, fontweight="bold", pad=8)
ax_main.axis("off")

# Inset 1: 1:8 MMI Tree
ax1 = fig.add_subplot(gs[0, 2])
ax1.imshow(img_mmi)
ax1.set_title("(b) 1:8 Cascaded MMI Splitter Tree", color="white", fontsize=10, fontweight="bold", pad=6)
ax1.axis("off")

# Inset 2: TFLT Modulator Bank
ax2 = fig.add_subplot(gs[0, 3])
ax2.imshow(img_mod)
ax2.set_title("(c) Thin-Film LiTaO3 EO Modulators & CPW", color="white", fontsize=10, fontweight="bold", pad=6)
ax2.axis("off")

# Inset 3: Centum TDV Interface
ax3 = fig.add_subplot(gs[1, 2])
ax3.imshow(img_tdv)
ax3.set_title("(d) Centum-Node TDV Array & Sense Links", color="white", fontsize=10, fontweight="bold", pad=6)
ax3.axis("off")

# Inset 4: DTI Bus & SACM APD
ax4 = fig.add_subplot(gs[1, 3])
ax4.imshow(img_dti)
ax4.set_title("(e) Dense 1.5 um DTI Bus & SACM APD Array", color="white", fontsize=10, fontweight="bold", pad=6)
ax4.axis("off")

# Inset 5: CPO Couplers
ax5 = fig.add_subplot(gs[2, 0:2])
ax5.imshow(img_cpo)
ax5.set_title("(f) East CPO Fiber Ribbon Edge Couplers (127 um MT Ferrule Pitch)",
              color="white", fontsize=10, fontweight="bold", pad=6)
ax5.axis("off")

# Inset 6: Foundry Diagnostic Test Structures
ax6 = fig.add_subplot(gs[2, 2:4])
ax6.imshow(img_tst)
ax6.set_title("(g) South Reticle Foundry MPW Test Modules (Spiral, MMI, RF VNA, TDV Kelvin)",
              color="white", fontsize=10, fontweight="bold", pad=6)
ax6.axis("off")

fig.suptitle("OPTICAL MEMORY INTERCONNECT (OMI) 8-CHANNEL FOUNDRY TAPE-OUT PHYSICAL MASK LAYOUT (GDSII)",
             color="white", fontsize=15, fontweight="bold", y=0.97)

out_file = os.path.join(PREVIEWS_DIR, "omi_layout_datasheet.png")
plt.savefig(out_file, facecolor=fig.get_facecolor(), edgecolor="none")
plt.close()
print(f"[SUCCESS] Layout datasheet figure generated: {out_file} ({os.path.getsize(out_file):,} bytes)")
