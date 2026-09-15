"""
render_gds_previews.py
Generates high-resolution multi-scale layout preview renderings from the OMI GDSII file
using the KLayout LayoutView engine and custom layer properties.

Outputs:
  - layout/previews/omi_chip_top_overview.png
  - layout/previews/omi_zoom_mmi_tree.png
  - layout/previews/omi_zoom_tflt_modulators.png
  - layout/previews/omi_zoom_tdv_constellation.png
  - layout/previews/omi_zoom_dti_bus_apd.png
  - layout/previews/omi_zoom_cpo_couplers.png
  - layout/previews/omi_zoom_test_structures.png
"""

import os
import sys
import klayout.db as kdb
import klayout.lay as lay

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LAYOUT_DIR = os.path.join(BASE_DIR, "layout")
PREVIEWS_DIR = os.path.join(LAYOUT_DIR, "previews")
os.makedirs(PREVIEWS_DIR, exist_ok=True)

GDS_PATH = os.path.join(LAYOUT_DIR, "OMI_8CH_TRANSCEIVER_2x2MM.gds")
LYP_PATH = os.path.join(LAYOUT_DIR, "omi_layers.lyp")

VIEWS = [
    {
        "name": "omi_chip_top_overview.png",
        "title": "Full Die Reticle Overview (2000 um x 2000 um)",
        "box": None,  # zoom_fit
        "width": 2600,
        "height": 2600
    },
    {
        "name": "omi_zoom_mmi_tree.png",
        "title": "West Laser Input & 1:8 Binary MMI Splitter Tree",
        "box": (45.0, 980.0, 680.0, 1550.0),
        "width": 1920,
        "height": 1280
    },
    {
        "name": "omi_zoom_tflt_modulators.png",
        "title": "8-Channel Thin-Film LiTaO3 EO Modulators & RF CPW Probing",
        "box": (610.0, 1000.0, 960.0, 1680.0),
        "width": 1920,
        "height": 1380
    },
    {
        "name": "omi_zoom_tdv_constellation.png",
        "title": "Centum-Node TDV Interface & Sense-Latch Routing",
        "box": (880.0, 980.0, 1160.0, 1500.0),
        "width": 1800,
        "height": 1350
    },
    {
        "name": "omi_zoom_dti_bus_apd.png",
        "title": "Dense 1.5 um Pitch DTI Waveguide Bus & SACM Ge/Si APD Array",
        "box": (1060.0, 980.0, 1680.0, 1520.0),
        "width": 1920,
        "height": 1280
    },
    {
        "name": "omi_zoom_cpo_couplers.png",
        "title": "East CPO Fiber Ribbon Edge Couplers (127 um MT Pitch)",
        "box": (1560.0, 700.0, 1980.0, 1750.0),
        "width": 1800,
        "height": 1500
    },
    {
        "name": "omi_zoom_test_structures.png",
        "title": "South Reticle Foundry MPW Diagnostic & Characterization Modules",
        "box": (60.0, 80.0, 1940.0, 750.0),
        "width": 2400,
        "height": 1200
    }
]

def render_all():
    print(f"Loading GDSII: {GDS_PATH}")
    if not os.path.exists(GDS_PATH):
        print(f"[ERROR] GDS file not found: {GDS_PATH}")
        sys.exit(1)
        
    layout = kdb.Layout()
    layout.read(GDS_PATH)
    
    view = lay.LayoutView()
    view.show_layout(layout, False)
    
    if os.path.exists(LYP_PATH):
        print(f"Loading Layer Properties: {LYP_PATH}")
        view.load_layer_props(LYP_PATH)
    else:
        print("[WARNING] LYP file not found, using default layer styles.")
        view.init_layer_properties()
        
    # Expand hierarchy fully so all subcell shapes are visible
    view.max_hier_levels = 10
    view.max_hier()
    
    # Render each view
    for v in VIEWS:
        out_path = os.path.join(PREVIEWS_DIR, v["name"])
        print(f"Rendering: {v['name']} ({v['title']})...")
        if v["box"] is None:
            view.zoom_fit()
        else:
            x0, y0, x1, y1 = v["box"]
            view.zoom_box(kdb.DBox(x0, y0, x1, y1))
            
        view.save_image(out_path, v["width"], v["height"])
        print(f"  -> Saved {out_path} ({os.path.getsize(out_path):,} bytes)")

    # Clean test files if present
    for tf in ["test_full.png", "test_zoom.png"]:
        p = os.path.join(PREVIEWS_DIR, tf)
        if os.path.exists(p):
            os.remove(p)

    print("\n[COMPLETE] All high-resolution GDSII preview images generated.")

if __name__ == "__main__":
    render_all()
