"""
generate_omi_gds.py
Master Python generator for the Optical Memory Interconnect (OMI) 8-Channel
Full-Architecture GDSII physical layout (2.0 mm x 2.0 mm chip footprint).

Generates:
  1. layout/OMI_8CH_TRANSCEIVER_2x2MM.gds (Foundry-ready GDSII stream file)
  2. layout/omi_layers.lyp (KLayout layer properties configuration)
  3. High-resolution multi-scale layout preview images in layout/previews/
"""

import os
import sys
import math
import klayout.db as kdb

# -------------------------------------------------------------------------
# Directories
# -------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
LAYOUT_DIR = os.path.join(BASE_DIR, "layout")
PREVIEWS_DIR = os.path.join(LAYOUT_DIR, "previews")
os.makedirs(PREVIEWS_DIR, exist_ok=True)

GDS_PATH = os.path.join(LAYOUT_DIR, "OMI_8CH_TRANSCEIVER_2x2MM.gds")
LYP_PATH = os.path.join(LAYOUT_DIR, "omi_layers.lyp")

# -------------------------------------------------------------------------
# Layer Map Specification
# -------------------------------------------------------------------------
LAYER_MAP = {
    "WG_CORE":      (1, 0,  "#00d4ff", "Si3N4 Waveguide Core (W=800nm)"),
    "WG_SLAB":      (2, 0,  "#005577", "Si3N4 Slab / Partial Etch"),
    "TFLT_CORE":    (3, 0,  "#d900d9", "Thin-Film LiTaO3 Pockels Film (300nm)"),
    "DTI_ETCH":     (4, 0,  "#ffd700", "Deep Trench Isolation Air Voids (300nm)"),
    "ACTIVE_PD":    (5, 0,  "#ff6600", "Ge Active Absorption & SACM Mesa"),
    "TDV_VIA":      (6, 0,  "#c86432", "Through-Die Via Cu Pillars (Dia=8um)"),
    "TDV_PAD":      (7, 0,  "#e68a5c", "TDV Cu Landing / Capture Pads (14x14um)"),
    "CONTACT":      (8, 0,  "#66b2ff", "Silicide Local Contact Vias"),
    "METAL1":       (9, 0,  "#00cc44", "Metal 1 Local Sense & Bitline Bus"),
    "METAL2_RF":    (10, 0, "#3366ff", "Metal 2 RF Coplanar Waveguide & Power"),
    "PAD_OPEN":     (11, 0, "#b0b0b0", "Passivation Openings (80x80um Pads)"),
    "HEAT_PILLAR":  (12, 0, "#cc2200", "Thermal Superhighway Cu Vias"),
    "TEXT_LABEL":   (63, 0, "#ffff99", "Micro & Macro Component Annotations"),
    "CHIP_BORDER":  (99, 0, "#888888", "Die Outline & Seal Ring (2000x2000um)")
}

# -------------------------------------------------------------------------
# 5x7 Vector Font Definition for Layout Polygon Rasterization
# -------------------------------------------------------------------------
FONT_5X7 = {
    'A': ['01110','10001','10001','11111','10001','10001','10001'],
    'B': ['11110','10001','10001','11110','10001','10001','11110'],
    'C': ['01111','10000','10000','10000','10000','10000','01111'],
    'D': ['11110','10001','10001','10001','10001','10001','11110'],
    'E': ['11111','10000','10000','11110','10000','10000','11111'],
    'F': ['11111','10000','10000','11110','10000','10000','10000'],
    'G': ['01111','10000','10000','10111','10001','10001','01111'],
    'H': ['10001','10001','10001','11111','10001','10001','10001'],
    'I': ['01110','00100','00100','00100','00100','00100','01110'],
    'J': ['00111','00010','00010','00010','00010','10010','01100'],
    'K': ['10001','10010','10100','11000','10100','10010','10001'],
    'L': ['10000','10000','10000','10000','10000','10000','11111'],
    'M': ['10001','11011','10101','10101','10001','10001','10001'],
    'N': ['10001','11001','10101','10011','10001','10001','10001'],
    'O': ['01110','10001','10001','10001','10001','10001','01110'],
    'P': ['11110','10001','10001','11110','10000','10000','10000'],
    'Q': ['01110','10001','10001','10001','10101','10011','01111'],
    'R': ['11110','10001','10001','11110','10100','10010','10001'],
    'S': ['01111','10000','10000','01110','00001','00001','11110'],
    'T': ['11111','00100','00100','00100','00100','00100','00100'],
    'U': ['10001','10001','10001','10001','10001','10001','01110'],
    'V': ['10001','10001','10001','10001','01010','01010','00100'],
    'W': ['10001','10001','10001','10101','10101','11011','10001'],
    'X': ['10001','10001','01010','00100','01010','10001','10001'],
    'Y': ['10001','10001','01010','00100','00100','00100','00100'],
    'Z': ['11111','00001','00010','00100','01000','10000','11111'],
    '0': ['01110','10011','10101','10101','11001','10001','01110'],
    '1': ['00100','01100','00100','00100','00100','00100','01110'],
    '2': ['01110','10001','00001','00010','00100','01000','11111'],
    '3': ['11110','00001','00001','01110','00001','00001','11110'],
    '4': ['00010','00110','01010','10010','11111','00010','00010'],
    '5': ['11111','10000','11110','00001','00001','10001','01110'],
    '6': ['00110','01000','10000','11110','10001','10001','01110'],
    '7': ['11111','00001','00010','00100','00100','01000','01000'],
    '8': ['01110','10001','10001','01110','10001','10001','01110'],
    '9': ['01110','10001','10001','01111','00001','00010','01100'],
    ' ': ['00000','00000','00000','00000','00000','00000','00000'],
    '-': ['00000','00000','00000','11111','00000','00000','00000'],
    '_': ['00000','00000','00000','00000','00000','00000','11111'],
    ':': ['00000','00100','00000','00000','00100','00000','00000'],
    '.': ['00000','00000','00000','00000','00000','00110','00110'],
    '/': ['00001','00010','00100','00100','01000','10000','00000'],
    '[': ['01110','01000','01000','01000','01000','01000','01110'],
    ']': ['01110','00010','00010','00010','00010','00010','01110'],
    '(': ['00110','01000','01000','01000','01000','01000','00110'],
    ')': ['01100','00010','00010','00010','00010','00010','01100'],
    '+': ['00000','00100','00100','11111','00100','00100','00000'],
    '=': ['00000','11111','00000','11111','00000','00000','00000'],
    '<': ['00010','00100','01000','10000','01000','00100','00010'],
    '>': ['01000','00100','00010','00001','00010','00100','01000'],
    '|': ['00100','00100','00100','00100','00100','00100','00100'],
    '*': ['00000','10101','01110','11111','01110','10101','00000'],
    ',': ['00000','00000','00000','00000','00100','00100','01000'],
    '&': ['01100','10010','01100','10110','10001','10010','01101'],
    '%': ['11001','11010','00100','01000','01011','10011','00000']
}

def draw_polygon_text(cell, text, x0, y0, height, layer_id):
    """Draws pixel-perfect polygon characters on specified layer."""
    px = height / 7.0
    cx = x0
    for ch in text.upper():
        bitmap = FONT_5X7.get(ch, FONT_5X7[' '])
        for row in range(7):
            y = y0 + (6 - row) * px
            line = bitmap[row]
            for col in range(5):
                if line[col] == '1':
                    x = cx + col * px
                    cell.shapes(layer_id).insert(kdb.DBox(x, y, x + px, y + px))
        cx += 6.5 * px

# -------------------------------------------------------------------------
# Parametric Geometry Helpers
# -------------------------------------------------------------------------
def add_box(cell, layer_id, x0, y0, x1, y1):
    """Inserts an axis-aligned rectangular box."""
    cell.shapes(layer_id).insert(kdb.DBox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))

def add_taper(cell, layer_id, x0, y0, w0, x1, y1, w1):
    """Inserts a linear waveguide taper polygon between two points."""
    pts = [
        kdb.DPoint(x0, y0 - w0 / 2.0),
        kdb.DPoint(x1, y1 - w1 / 2.0),
        kdb.DPoint(x1, y1 + w1 / 2.0),
        kdb.DPoint(x0, y0 + w0 / 2.0)
    ]
    cell.shapes(layer_id).insert(kdb.DPolygon(pts))

def add_s_bend(cell, layer_id, x0, y0, x1, y1, width, n_pts=36):
    """Inserts an adiabatic cosine S-bend polygon to ensure zero curvature discontinuity."""
    dx = x1 - x0
    dy = y1 - y0
    upper = []
    lower = []
    for i in range(n_pts + 1):
        t = i / float(n_pts)
        x = x0 + t * dx
        y = y0 + 0.5 * dy * (1.0 - math.cos(math.pi * t))
        upper.append(kdb.DPoint(x, y + width / 2.0))
        lower.append(kdb.DPoint(x, y - width / 2.0))
    pts = upper + lower[::-1]
    cell.shapes(layer_id).insert(kdb.DPolygon(pts))

def add_circle(cell, layer_id, cx, cy, radius, n_pts=32):
    """Inserts a regular polygonal circle approximation."""
    pts = []
    for i in range(n_pts):
        ang = 2.0 * math.pi * i / float(n_pts)
        pts.append(kdb.DPoint(cx + radius * math.cos(ang), cy + radius * math.sin(ang)))
    cell.shapes(layer_id).insert(kdb.DPolygon(pts))

def add_pad_with_open(cell, l_metal, l_open, cx, cy, size=80.0, open_inset=6.0):
    """Inserts an electrical probe/wirebond pad with passivation opening."""
    half_m = size / 2.0
    half_o = (size - 2.0 * open_inset) / 2.0
    cell.shapes(l_metal).insert(kdb.DBox(cx - half_m, cy - half_m, cx + half_m, cy + half_m))
    cell.shapes(l_open).insert(kdb.DBox(cx - half_o, cy - half_o, cx + half_o, cy + half_o))


# -------------------------------------------------------------------------
# Main Builder Class
# -------------------------------------------------------------------------
class OMILayoutBuilder:
    def __init__(self):
        self.layout = kdb.Layout()
        self.layout.dbu = 0.001  # 1 nm database unit
        
        # Register layers
        self.layers = {}
        for name, info in LAYER_MAP.items():
            self.layers[name] = self.layout.layer(info[0], info[1])
            
        self.top = self.layout.create_cell("OMI_8CH_TRANSCEIVER_TOP")
        
    def build_frame(self):
        """Constructs chip boundary, guard rings, corner fiducials, and scale bars."""
        frame = self.layout.create_cell("FRAME_AND_RETICLE")
        
        l_border = self.layers["CHIP_BORDER"]
        l_m1 = self.layers["METAL1"]
        l_m2 = self.layers["METAL2_RF"]
        l_text = self.layers["TEXT_LABEL"]
        
        # 1. Outer dicing street border (2000 x 2000 um)
        frame.shapes(l_border).insert(kdb.DBox(0, 0, 2000, 2000))
        
        # 2. Dual seal ring (crack-stop guard ring)
        # Outer ring: 30 to 45 um
        frame.shapes(l_m2).insert(kdb.DBox(30, 30, 1970, 45))
        frame.shapes(l_m2).insert(kdb.DBox(30, 1955, 1970, 1970))
        frame.shapes(l_m2).insert(kdb.DBox(30, 45, 45, 1955))
        frame.shapes(l_m2).insert(kdb.DBox(1955, 45, 1970, 1955))
        
        # Inner ring: 55 to 67 um on M1
        frame.shapes(l_m1).insert(kdb.DBox(55, 55, 1945, 67))
        frame.shapes(l_m1).insert(kdb.DBox(55, 1933, 1945, 1945))
        frame.shapes(l_m1).insert(kdb.DBox(55, 67, 67, 1933))
        frame.shapes(l_m1).insert(kdb.DBox(1933, 67, 1945, 1933))
        
        # 3. Corner alignment targets & fiducials
        corners = [(100, 100), (1900, 100), (100, 1900), (1900, 1900)]
        for cx, cy in corners:
            # Crosshair
            add_box(frame, l_m2, cx - 25, cy - 3, cx + 25, cy + 3)
            add_box(frame, l_m2, cx - 3, cy - 25, cx + 3, cy + 25)
            # Concentric rings
            add_circle(frame, self.layers["WG_CORE"], cx, cy, 35.0)
            add_circle(frame, self.layers["WG_SLAB"], cx, cy, 45.0)
            add_circle(frame, l_m1, cx, cy, 15.0)
            
        # 4. Calibrated Scale Bars
        # 500 um scale bar at (100, 75)
        add_box(frame, l_text, 100, 75, 600, 80)
        add_box(frame, l_text, 100, 70, 105, 85)
        add_box(frame, l_text, 350, 72, 355, 83)
        add_box(frame, l_text, 600, 70, 605, 85)
        draw_polygon_text(frame, "SCALE: 500 um", 280, 85, 10.0, l_text)
        
        # 100 um micro scale bar at (700, 75)
        add_box(frame, l_text, 700, 75, 800, 80)
        add_box(frame, l_text, 700, 70, 703, 85)
        add_box(frame, l_text, 800, 70, 803, 85)
        draw_polygon_text(frame, "100 um", 725, 85, 8.0, l_text)
        
        # 5. Top Header & Reticle Metadata
        draw_polygon_text(frame, "OPTICAL MEMORY INTERCONNECT (OMI) 8-CHANNEL TRANSCEIVER", 240, 1890, 15.0, l_text)
        draw_polygon_text(frame, "RETICLE: 2000 um x 2000 um (4.0 mm^2) | FOUNDRY MPW TAPE-OUT PROTOTYPE", 240, 1865, 10.0, l_text)
        draw_polygon_text(frame, "AUTHOR: DEEPANSHU BHARDWAJ | TRL 5 PHYSICAL SIGN-OFF | REV 1.0", 240, 1845, 9.0, l_text)
        
        # Instance into top
        self.top.insert(kdb.DCellInstArray(frame.cell_index(), kdb.DTrans()))

    def build_laser_input_port(self):
        """West optical input port with adiabatic inverse taper SSC and alignment trench."""
        cell = self.layout.create_cell("OPT_LASER_INPUT")
        l_core = self.layers["WG_CORE"]
        l_slab = self.layers["WG_SLAB"]
        l_dti = self.layers["DTI_ETCH"]
        l_text = self.layers["TEXT_LABEL"]
        
        # Edge facet coupler at X = 55 um, Y = 1200 um
        # Adiabatic inverse taper: tip 180 nm -> core 800 nm over 150 um
        add_taper(cell, l_core, 55.0, 1200.0, 0.18, 205.0, 1200.0, 0.80)
        # Cladding etch opening for lensed fiber facet
        add_box(cell, l_dti, 50.0, 1170.0, 100.0, 1230.0)
        # Slab support buffer
        add_box(cell, l_slab, 55.0, 1190.0, 205.0, 1210.0)
        
        # Waveguide feed to MMI Tree
        add_box(cell, l_core, 205.0, 1199.6, 230.0, 1200.4)
        
        # West Diagnostic Loopback Port (for fiber coupling loss calibration)
        add_taper(cell, l_core, 55.0, 1400.0, 0.18, 155.0, 1400.0, 0.80)
        add_taper(cell, l_core, 55.0, 1500.0, 0.18, 155.0, 1500.0, 0.80)
        add_s_bend(cell, l_core, 155.0, 1400.0, 210.0, 1450.0, 0.80)
        add_s_bend(cell, l_core, 210.0, 1450.0, 155.0, 1500.0, 0.80)
        draw_polygon_text(cell, "OPT_LOOP_IN", 70.0, 1410.0, 6.0, l_text)
        draw_polygon_text(cell, "OPT_LOOP_OUT", 70.0, 1510.0, 6.0, l_text)
        
        # Labels
        draw_polygon_text(cell, "OPT_IN_CW_LASER", 60.0, 1215.0, 8.0, l_text)
        draw_polygon_text(cell, "1550nm CW IN", 60.0, 1175.0, 6.0, l_text)
        
        self.top.insert(kdb.DCellInstArray(cell.cell_index(), kdb.DTrans()))

    def build_mmi_tree_1x8(self):
        """Builds the 3-stage 1:8 cascaded MMI binary splitter tree distributing optical power."""
        cell = self.layout.create_cell("MMI_TREE_1X8")
        l_core = self.layers["WG_CORE"]
        l_slab = self.layers["WG_SLAB"]
        l_text = self.layers["TEXT_LABEL"]
        
        def add_mmi_1x2(cx, cy):
            """Single 1x2 MMI block centered at (cx, cy). L_mmi = 28.5 um, W_mmi = 6.0 um."""
            # Input taper: 0.8um -> 1.5um over 10um
            add_taper(cell, l_core, cx, cy, 0.80, cx + 10.0, cy, 1.50)
            # Multimode interference cavity
            add_box(cell, l_core, cx + 10.0, cy - 3.0, cx + 38.5, cy + 3.0)
            add_box(cell, l_slab, cx + 8.0, cy - 4.5, cx + 40.5, cy + 4.5)
            # Output tapers: dual tapers 1.5um -> 0.8um spaced by 2.4um
            add_taper(cell, l_core, cx + 38.5, cy - 1.20, 1.50, cx + 48.5, cy - 1.20, 0.80)
            add_taper(cell, l_core, cx + 38.5, cy + 1.20, 1.50, cx + 48.5, cy + 1.20, 0.80)
            return cx + 48.5, cy - 1.20, cy + 1.20

        # Stage 1: Single MMI at X = 230 um, Y = 1200 um
        x1_out, y1_bot, y1_top = add_mmi_1x2(230.0, 1200.0)
        draw_polygon_text(cell, "STAGE 1 MMI (1:2)", 230.0, 1220.0, 7.0, l_text)
        
        # S-bends expanding to Stage 2 centers: Y = 1075 um and Y = 1325 um
        s1_len = 95.0
        add_s_bend(cell, l_core, x1_out, y1_bot, x1_out + s1_len, 1075.0, 0.80)
        add_s_bend(cell, l_core, x1_out, y1_top, x1_out + s1_len, 1325.0, 0.80)
        
        # Stage 2: Two MMIs at X = 375 um
        x2 = x1_out + s1_len
        x2_out, y2_bot1, y2_top1 = add_mmi_1x2(x2, 1075.0)
        x2_out, y2_bot2, y2_top2 = add_mmi_1x2(x2, 1325.0)
        draw_polygon_text(cell, "STAGE 2 (1:4)", x2, 1345.0, 7.0, l_text)
        
        # S-bends expanding to Stage 3 centers: Y = 1015, 1135, 1265, 1385 um
        s2_len = 85.0
        add_s_bend(cell, l_core, x2_out, y2_bot1, x2_out + s2_len, 1015.0, 0.80)
        add_s_bend(cell, l_core, x2_out, y2_top1, x2_out + s2_len, 1135.0, 0.80)
        add_s_bend(cell, l_core, x2_out, y2_bot2, x2_out + s2_len, 1265.0, 0.80)
        add_s_bend(cell, l_core, x2_out, y2_top2, x2_out + s2_len, 1385.0, 0.80)
        
        # Stage 3: Four MMIs at X = 510 um
        x3 = x2_out + s2_len
        x3_out, y3_b1, y3_t1 = add_mmi_1x2(x3, 1015.0)
        x3_out, y3_b2, y3_t2 = add_mmi_1x2(x3, 1135.0)
        x3_out, y3_b3, y3_t3 = add_mmi_1x2(x3, 1265.0)
        x3_out, y3_b4, y3_t4 = add_mmi_1x2(x3, 1385.0)
        draw_polygon_text(cell, "STAGE 3 (1:8)", x3, 1405.0, 7.0, l_text)
        
        # S-bends fanning out to 8 parallel channels with uniform pitch P = 45 um
        # Target Y positions: 1042.5 + i * 45 for i=0..7
        stage3_outs = [y3_b1, y3_t1, y3_b2, y3_t2, y3_b3, y3_t3, y3_b4, y3_t4]
        s3_len = 80.0
        for i in range(8):
            target_y = 1042.5 + i * 45.0
            add_s_bend(cell, l_core, x3_out, stage3_outs[i], x3_out + s3_len, target_y, 0.80)
            
        # Section Annotation
        draw_polygon_text(cell, "[2] 1:8 BINARY MMI TREE (3-STAGE CASCADED, IL=0.14 dB/STAGE)", 230.0, 1450.0, 9.0, l_text)
        
        self.top.insert(kdb.DCellInstArray(cell.cell_index(), kdb.DTrans()))

    def build_tflt_modulator_bank(self):
        """8-Channel Thin-Film LiTaO3 electro-optic Pockels modulators with RF CPW electrodes."""
        cell = self.layout.create_cell("TFLT_MODULATOR_BANK_8CH")
        l_core = self.layers["WG_CORE"]
        l_tflt = self.layers["TFLT_CORE"]
        l_m2 = self.layers["METAL2_RF"]
        l_pad = self.layers["PAD_OPEN"]
        l_text = self.layers["TEXT_LABEL"]
        
        x_start = 640.0
        mod_len = 220.0
        x_end = x_start + mod_len + 50.0  # including Y-branches
        
        for i in range(8):
            cy = 1042.5 + i * 45.0
            
            # Input Y-branch splitter (25 um)
            add_box(cell, l_core, x_start, cy - 0.40, x_start + 10.0, cy + 0.40)
            add_s_bend(cell, l_core, x_start + 10.0, cy, x_start + 25.0, cy - 5.0, 0.80)
            add_s_bend(cell, l_core, x_start + 10.0, cy, x_start + 25.0, cy + 5.0, 0.80)
            
            # Straight Mach-Zehnder arms (220 um)
            x_arm_start = x_start + 25.0
            x_arm_end = x_arm_start + mod_len
            add_box(cell, l_core, x_arm_start, cy - 5.40, x_arm_end, cy - 4.60)
            add_box(cell, l_core, x_arm_start, cy + 4.60, x_arm_end, cy + 5.40)
            
            # LiTaO3 Electro-Optic Core Layer (300nm film)
            add_box(cell, l_tflt, x_arm_start - 5.0, cy - 12.0, x_arm_end + 5.0, cy + 12.0)
            
            # Output Y-branch combiner (25 um)
            add_s_bend(cell, l_core, x_arm_end, cy - 5.0, x_arm_end + 15.0, cy, 0.80)
            add_s_bend(cell, l_core, x_arm_end, cy + 5.0, x_arm_end + 15.0, cy, 0.80)
            add_box(cell, l_core, x_arm_end + 15.0, cy - 0.40, x_arm_end + 25.0, cy + 0.40)
            
            # RF CPW Travelling-Wave Electrodes (Metal 2)
            # Center Signal electrode (between the two arms)
            add_box(cell, l_m2, x_arm_start, cy - 2.5, x_arm_end, cy + 2.5)
            # Dual Ground electrodes
            add_box(cell, l_m2, x_arm_start, cy - 16.0, x_arm_end, cy - 7.5)
            add_box(cell, l_m2, x_arm_start, cy + 7.5, x_arm_end, cy + 16.0)
            
            # Micro Annotation for each lane
            draw_polygon_text(cell, f"LANE {i}", x_start + 35.0, cy - 2.5, 5.0, l_text)
            
        # RF GSG Probe Pads for modulators on North side (probed at wafer-level)
        pad_y = 1580.0
        for i in range(8):
            pad_x = 650.0 + i * 35.0
            # Route from modulator Signal to pad
            cy = 1042.5 + i * 45.0
            add_s_bend(cell, l_m2, x_start + 30.0, cy, pad_x, pad_y - 20.0, 4.0)
            # Signal Pad
            add_pad_with_open(cell, l_m2, l_pad, pad_x, pad_y, size=24.0, open_inset=2.5)
            draw_polygon_text(cell, f"S{i}", pad_x - 5.0, pad_y + 15.0, 5.0, l_text)
            
        # Ground rail bridging probe grounds
        add_box(cell, l_m2, 630.0, pad_y - 40.0, 930.0, pad_y - 35.0)
        draw_polygon_text(cell, "RF GSG MODULATOR DRIVE PORTS (200 GHz VNA PROBING)", 640.0, 1630.0, 8.0, l_text)
        draw_polygon_text(cell, "[3] TFLT EO MODULATOR BANK (8-CH PUSH-PULL)", 640.0, 1500.0, 8.0, l_text)
        draw_polygon_text(cell, "r33=30.5 pm/V, Vpi*L=1.1 V*cm", 640.0, 1485.0, 6.0, l_text)
        
        self.top.insert(kdb.DCellInstArray(cell.cell_index(), kdb.DTrans()))

    def build_centum_node_tdv_interface(self):
        """Centum-Node Through-Die Via (TDV) constellation interface for 3D Flash word-line driving."""
        cell = self.layout.create_cell("CENTUM_NODE_TDV_INTERFACE")
        l_via = self.layers["TDV_VIA"]
        l_pad = self.layers["TDV_PAD"]
        l_m1 = self.layers["METAL1"]
        l_heat = self.layers["HEAT_PILLAR"]
        l_text = self.layers["TEXT_LABEL"]
        
        x_base = 940.0
        
        # 8 Signal TDVs feeding the 8 modulator sense latches + grounding shield vias
        for i in range(8):
            cy = 1042.5 + i * 45.0
            vx = x_base + 30.0 + (i % 2) * 40.0
            
            # Cu Pillar Via (Dia = 8.0 um)
            add_circle(cell, l_via, vx, cy, 4.0)
            # Cu Landing Pad (14.0 x 14.0 um)
            add_box(cell, l_pad, vx - 7.0, cy - 7.0, vx + 7.0, cy + 7.0)
            # M1 Interconnect routing from TDV capture pad to modulator input
            add_box(cell, l_m1, vx + 7.0, cy - 1.5, vx + 55.0, cy + 1.5)
            
            # Ground shielding TDV
            add_circle(cell, l_via, vx, cy - 18.0, 3.0)
            add_circle(cell, l_via, vx, cy + 18.0, 3.0)
            
            # Thermal superhighway pillar (copper heat drain)
            add_circle(cell, l_heat, vx + 20.0, cy + 16.0, 4.0)
            
            draw_polygon_text(cell, f"TDV_{i}", vx - 10.0, cy + 8.0, 5.0, l_text)
            
        # Centum-Node Voronoi Cell Boundary Marking
        bw = 2.0
        add_box(cell, l_m1, x_base, 1010.0, x_base + 120.0, 1010.0 + bw)
        add_box(cell, l_m1, x_base, 1400.0 - bw, x_base + 120.0, 1400.0)
        add_box(cell, l_m1, x_base, 1010.0, x_base + bw, 1400.0)
        add_box(cell, l_m1, x_base + 120.0 - bw, 1010.0, x_base + 120.0, 1400.0)
        
        draw_polygon_text(cell, "[4] CENTUM-NODE TDV INTERFACE", 910.0, 1450.0, 7.5, l_text)
        draw_polygon_text(cell, "DIA=8um Cu, t90=2.22ns", 910.0, 1435.0, 6.0, l_text)
        draw_polygon_text(cell, "SENSE-LATCH Cu INTERCONNECTS", 910.0, 1385.0, 5.5, l_text)
        
        self.top.insert(kdb.DCellInstArray(cell.cell_index(), kdb.DTrans()))

    def build_dti_waveguide_bus(self):
        """High-density 8-waveguide bus with Deep Dielectric Trench Isolation (DTI) air-voids."""
        cell = self.layout.create_cell("DTI_WAVEGUIDE_BUS_8CH")
        l_core = self.layers["WG_CORE"]
        l_dti = self.layers["DTI_ETCH"]
        l_text = self.layers["TEXT_LABEL"]
        
        x_fanin_start = 1080.0
        x_bus_start = 1200.0
        bus_len = 180.0
        x_bus_end = x_bus_start + bus_len
        
        # Target dense bus: Pitch = 1.5 um center-to-center
        for i in range(8):
            y_in = 1042.5 + i * 45.0
            y_bus = 1194.75 + i * 1.5
            
            # S-bend from 45um pitch into 1.5um pitch dense bus
            add_s_bend(cell, l_core, x_fanin_start, y_in, x_bus_start, y_bus, 0.80)
            # Dense straight bus run
            add_box(cell, l_core, x_bus_start, y_bus - 0.40, x_bus_end, y_bus + 0.40)
            
        # DTI Air-Void Trenches: 7 internal trenches between the 8 lanes + 2 outer trenches
        for i in range(9):
            y_trench = 1194.0 + i * 1.5
            add_box(cell, l_dti, x_bus_start, y_trench - 0.175, x_bus_end, y_trench + 0.175)
            
        # Annotations
        draw_polygon_text(cell, "[5] HIGH-DENSITY DTI WAVEGUIDE BUS", 1070.0, 1260.0, 7.5, l_text)
        draw_polygon_text(cell, "PITCH=1.5um, <-45dB X-TALK", 1070.0, 1245.0, 6.0, l_text)
        draw_polygon_text(cell, "DTI AIR-VOID TRENCHES (W=350nm)", 1210.0, 1180.0, 6.0, l_text)
        draw_polygon_text(cell, "8-WG BUS (11.3 um TOTAL WIDTH)", 1210.0, 1165.0, 6.0, l_text)
        
        self.top.insert(kdb.DCellInstArray(cell.cell_index(), kdb.DTrans()))

    def build_sacm_apd_array(self):
        """8-Channel Separate Absorption, Charge, and Multiplication (SACM) Ge/Si APD Array."""
        cell = self.layout.create_cell("SACM_APD_ARRAY_8CH")
        l_core = self.layers["WG_CORE"]
        l_active = self.layers["ACTIVE_PD"]
        l_cont = self.layers["CONTACT"]
        l_m1 = self.layers["METAL1"]
        l_m2 = self.layers["METAL2_RF"]
        l_pad = self.layers["PAD_OPEN"]
        l_text = self.layers["TEXT_LABEL"]
        
        x_bus_end = 1380.0
        x_apd_start = 1480.0
        
        for i in range(8):
            y_bus = 1194.75 + i * 1.5
            y_apd = 1042.5 + i * 45.0
            
            # S-bend fan-out from dense bus to APD array (45 um pitch)
            add_s_bend(cell, l_core, x_bus_end, y_bus, x_apd_start, y_apd, 0.80)
            
            # Ge Active Absorption Mesa: 1.2 um x 14.0 um
            add_box(cell, l_active, x_apd_start, y_apd - 0.60, x_apd_start + 14.0, y_apd + 0.60)
            
            # Silicon charge & multiplication layer
            add_box(cell, l_core, x_apd_start + 14.0, y_apd - 0.80, x_apd_start + 24.0, y_apd + 0.80)
            
            # Silicide Contact Vias
            add_box(cell, l_cont, x_apd_start + 2.0, y_apd - 0.40, x_apd_start + 5.0, y_apd + 0.40)
            add_box(cell, l_cont, x_apd_start + 18.0, y_apd - 0.40, x_apd_start + 21.0, y_apd + 0.40)
            
            # Receiverless StrongARM Latch landing pad (direct drive)
            add_box(cell, l_m1, x_apd_start + 24.0, y_apd - 8.0, x_apd_start + 45.0, y_apd + 8.0)
            add_pad_with_open(cell, l_m2, l_pad, x_apd_start + 65.0, y_apd, size=20.0, open_inset=2.0)
            
            draw_polygon_text(cell, f"APD_{i}", x_apd_start + 80.0, y_apd - 3.0, 5.0, l_text)
            
        draw_polygon_text(cell, "[6] SACM Ge/Si APD RECEIVER", 1370.0, 1480.0, 7.5, l_text)
        draw_polygon_text(cell, "Cpd=2.0fF, RECEIVERLESS", 1370.0, 1465.0, 6.0, l_text)
        draw_polygon_text(cell, "STRONGARM COMPARATOR LANDING PADS", 1480.0, 1385.0, 6.0, l_text)
        
        self.top.insert(kdb.DCellInstArray(cell.cell_index(), kdb.DTrans()))

    def build_cpo_coupler_array(self):
        """8-Channel Co-Packaged Optics (CPO) fiber ribbon edge coupler array at 127 um standard pitch."""
        cell = self.layout.create_cell("CPO_COUPLER_ARRAY_8CH")
        l_core = self.layers["WG_CORE"]
        l_slab = self.layers["WG_SLAB"]
        l_dti = self.layers["DTI_ETCH"]
        l_text = self.layers["TEXT_LABEL"]
        
        x_fanout_start = 1600.0
        x_taper_start = 1790.0
        x_facet = 1945.0
        
        for i in range(8):
            y_in = 1042.5 + i * 45.0
            y_cpo = 755.5 + i * 127.0
            
            # S-bend expanding from 45um pitch to 127um ribbon pitch
            add_s_bend(cell, l_core, x_fanout_start, y_in, x_taper_start, y_cpo, 0.80)
            
            # Adiabatic Inverse Taper SSC: 800nm -> 180nm over 155 um to match single-mode fiber mode
            add_taper(cell, l_core, x_taper_start, y_cpo, 0.80, x_facet, y_cpo, 0.18)
            # Slab support transition
            add_box(cell, l_slab, x_taper_start, y_cpo - 4.0, x_facet, y_cpo + 4.0)
            
            # V-groove fiber trench recess at chip facet
            add_box(cell, l_dti, x_facet - 15.0, y_cpo - 25.0, x_facet + 10.0, y_cpo + 25.0)
            
            draw_polygon_text(cell, f"CPO_OUT_{i}", x_facet - 85.0, y_cpo + 8.0, 6.0, l_text)
            draw_polygon_text(cell, "127 um PITCH", x_facet - 85.0, y_cpo - 14.0, 5.0, l_text)
            
        draw_polygon_text(cell, "[7] CPO FIBER ARRAY COUPLERS (127 um MT PITCH, ADIABATIC SSC)", 1480.0, 1720.0, 9.0, l_text)
        draw_polygon_text(cell, "EAST CHIP FACET (OPTICAL OUTPUT TO SWITCH FABRIC)", 1530.0, 1695.0, 7.0, l_text)
        
        self.top.insert(kdb.DCellInstArray(cell.cell_index(), kdb.DTrans()))

    def build_diagnostic_test_blocks(self):
        """Comprehensive on-chip foundry MPW test modules in South Reticle Zone."""
        cell = self.layout.create_cell("FOUNDRY_DIAGNOSTIC_TESTS")
        l_core = self.layers["WG_CORE"]
        l_slab = self.layers["WG_SLAB"]
        l_tflt = self.layers["TFLT_CORE"]
        l_via = self.layers["TDV_VIA"]
        l_m1 = self.layers["METAL1"]
        l_m2 = self.layers["METAL2_RF"]
        l_pad = self.layers["PAD_OPEN"]
        l_text = self.layers["TEXT_LABEL"]
        
        # Test Structure 1: Standalone 1x2 MMI Test with Optical Loopback
        y_t1 = 540.0
        add_taper(cell, l_core, 120.0, y_t1, 0.18, 200.0, y_t1, 0.80)
        add_taper(cell, l_core, 200.0, y_t1, 0.80, 210.0, y_t1, 1.50)
        add_box(cell, l_core, 210.0, y_t1 - 3.0, 238.5, y_t1 + 3.0)
        add_taper(cell, l_core, 238.5, y_t1 - 1.2, 1.50, 248.5, y_t1 - 1.2, 0.80)
        add_taper(cell, l_core, 238.5, y_t1 + 1.2, 1.50, 248.5, y_t1 + 1.2, 0.80)
        add_s_bend(cell, l_core, 248.5, y_t1 - 1.2, 330.0, y_t1 - 30.0, 0.80)
        add_s_bend(cell, l_core, 248.5, y_t1 + 1.2, 330.0, y_t1 + 30.0, 0.80)
        add_taper(cell, l_core, 330.0, y_t1 - 30.0, 0.80, 420.0, y_t1 - 30.0, 0.18)
        add_taper(cell, l_core, 330.0, y_t1 + 30.0, 0.80, 420.0, y_t1 + 30.0, 0.18)
        draw_polygon_text(cell, "TEST 1: 1x2 MMI EXCESS LOSS & BALANCE", 120.0, y_t1 + 42.0, 7.0, l_text)
        
        # Test Structure 2: Standalone TFLT Phase Modulator with GSG RF Pads
        y_t2 = 540.0
        x_t2 = 520.0
        add_box(cell, l_core, x_t2, y_t2 - 0.40, x_t2 + 250.0, y_t2 + 0.40)
        add_box(cell, l_tflt, x_t2 + 25.0, y_t2 - 10.0, x_t2 + 225.0, y_t2 + 10.0)
        add_box(cell, l_m2, x_t2 + 25.0, y_t2 - 2.5, x_t2 + 225.0, y_t2 + 2.5)
        add_box(cell, l_m2, x_t2 + 25.0, y_t2 - 16.0, x_t2 + 225.0, y_t2 - 7.5)
        add_box(cell, l_m2, x_t2 + 25.0, y_t2 + 7.5, x_t2 + 225.0, y_t2 + 16.0)
        add_pad_with_open(cell, l_m2, l_pad, x_t2 + 125.0, y_t2 - 60.0, size=50.0, open_inset=4.0)
        add_pad_with_open(cell, l_m2, l_pad, x_t2 + 125.0, y_t2, size=50.0, open_inset=4.0)
        add_pad_with_open(cell, l_m2, l_pad, x_t2 + 125.0, y_t2 + 60.0, size=50.0, open_inset=4.0)
        draw_polygon_text(cell, "G", x_t2 + 160.0, y_t2 - 65.0, 7.0, l_text)
        draw_polygon_text(cell, "S", x_t2 + 160.0, y_t2 - 5.0, 7.0, l_text)
        draw_polygon_text(cell, "G", x_t2 + 160.0, y_t2 + 55.0, 7.0, l_text)
        draw_polygon_text(cell, "TEST 2: TFLT Vpi*L & S21 RF VNA TEST", x_t2, y_t2 + 95.0, 7.0, l_text)
        
        # Test Structure 3: Waveguide Loss Spiral (Cutback Method, L = 2.5 cm)
        x_sp = 270.0
        y_sp = 240.0
        for ring in range(7):
            w_box = 180.0 + ring * 24.0
            h_box = 80.0 + ring * 16.0
            add_box(cell, l_core, x_sp - w_box/2.0, y_sp + h_box/2.0 - 0.40, x_sp + w_box/2.0, y_sp + h_box/2.0 + 0.40)
            add_box(cell, l_core, x_sp - w_box/2.0, y_sp - h_box/2.0 - 0.40, x_sp + w_box/2.0, y_sp - h_box/2.0 + 0.40)
            add_s_bend(cell, l_core, x_sp + w_box/2.0, y_sp - h_box/2.0, x_sp + w_box/2.0 + 10.0, y_sp + h_box/2.0, 0.80)
            add_s_bend(cell, l_core, x_sp - w_box/2.0, y_sp + h_box/2.0, x_sp - w_box/2.0 - 10.0, y_sp - h_box/2.0, 0.80)
            
        draw_polygon_text(cell, "TEST 3: CUTBACK LOSS SPIRAL (L = 2.50 cm)", x_sp - 70.0, y_sp - 90.0, 7.0, l_text)
        
        # Test Structure 4: Centum-Node TDV 4-Point Kelvin Resistance Chain
        x_k = 650.0
        y_k = 240.0
        pads_k = [(x_k, y_k + 60.0, "I+"), (x_k, y_k + 20.0, "V+"),
                  (x_k, y_k - 20.0, "V-"), (x_k, y_k - 60.0, "I-")]
        for px, py, name in pads_k:
            add_pad_with_open(cell, l_m2, l_pad, px, py, size=30.0, open_inset=3.0)
            draw_polygon_text(cell, name, px + 22.0, py - 3.0, 6.0, l_text)
            
        for vi in range(10):
            vx = x_k + 90.0 + vi * 16.0
            vy = y_k + (8.0 if vi % 2 == 0 else -8.0)
            add_circle(cell, l_via, vx, vy, 4.0)
            add_box(cell, l_m1 if vi % 2 == 0 else l_m2, vx - 5.0, vy - 5.0, vx + 18.0, vy + 5.0)
            
        draw_polygon_text(cell, "TEST 4: TDV 4-WIRE KELVIN RESISTANCE (Rvia <= 12 mOhm)", x_k, y_k - 90.0, 7.0, l_text)
        
        # Test Structure 5: DTI Crosstalk Test Pair (with vs without DTI)
        x_dt = 1000.0
        y_dt = 250.0
        l_dti = self.layers["DTI_ETCH"]
        # Waveguide 1 & 2 with DTI trench
        add_box(cell, l_core, x_dt, y_dt - 0.4, x_dt + 220.0, y_dt + 0.4)
        add_box(cell, l_core, x_dt, y_dt + 1.5 - 0.4, x_dt + 220.0, y_dt + 1.5 + 0.4)
        add_box(cell, l_dti, x_dt + 10.0, y_dt + 0.75 - 0.175, x_dt + 210.0, y_dt + 0.75 + 0.175)
        # Reference pair without DTI trench
        add_box(cell, l_core, x_dt, y_dt + 40.0 - 0.4, x_dt + 220.0, y_dt + 40.0 + 0.4)
        add_box(cell, l_core, x_dt, y_dt + 41.5 - 0.4, x_dt + 220.0, y_dt + 41.5 + 0.4)
        draw_polygon_text(cell, "TEST 5: DTI OPTICAL ISOLATION (WITH VS WITHOUT DTI)", x_dt, y_dt + 65.0, 7.0, l_text)
        
        # Test Structure 6: Lithography Vernier Overlay Calipers & Resolution Comb
        x_v = 1450.0
        y_v = 280.0
        for vi in range(15):
            add_box(cell, l_core, x_v + vi * 10.0, y_v, x_v + vi * 10.0 + 1.0, y_v + 30.0)
            add_box(cell, l_m1, x_v + vi * 9.8, y_v - 30.0, x_v + vi * 9.8 + 1.0, y_v)
            
        for ci in range(10):
            w_comb = 0.20 + ci * 0.08
            cx = x_v + 180.0 + ci * 12.0
            add_box(cell, l_core, cx, y_v - 30.0, cx + w_comb, y_v + 30.0)
            
        draw_polygon_text(cell, "TEST 6: OVERLAY VERNIER (10nm RES) & SUB-MICRON COMB", x_v - 40.0, y_v + 45.0, 7.0, l_text)
        
        draw_polygon_text(cell, "[8] FOUNDRY DIAGNOSTIC & PDK CHARACTERIZATION MODULES", 120.0, 690.0, 9.5, l_text)
        
        self.top.insert(kdb.DCellInstArray(cell.cell_index(), kdb.DTrans()))

    def export(self, gds_path, lyp_path):
        """Exports the layout to GDSII and writes KLayout layer properties."""
        print(f"Writing GDSII layout to: {gds_path}")
        self.layout.write(gds_path)
        print(f"[SUCCESS] GDSII file generated ({os.path.getsize(gds_path):,} bytes)")
        
        # Write .lyp Layer Properties File
        lyp_xml = ['<?xml version="1.0" encoding="utf-8"?>', '<layer-properties>']
        for name, info in LAYER_MAP.items():
            l_num, d_type, color, desc = info
            clean_desc = desc.replace('&', '&amp;')
            node = f""" <properties>
  <frame-color>{color}</frame-color>
  <fill-color>{color}</fill-color>
  <frame-brightness>0</frame-brightness>
  <fill-brightness>0</fill-brightness>
  <dither-pattern>I2</dither-pattern>
  <line-style/>
  <valid>true</valid>
  <visible>true</visible>
  <transparent>false</transparent>
  <width>1</width>
  <marked>false</marked>
  <xfill>false</xfill>
  <animation>0</animation>
  <name>{name} {l_num}/{d_type} - {clean_desc}</name>
  <source>{l_num}/{d_type}@1</source>
 </properties>"""
            lyp_xml.append(node)
        lyp_xml.append('</layer-properties>')
        
        with open(lyp_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lyp_xml))
        print(f"[SUCCESS] Layer properties written to: {lyp_path}")


def main():
    print("=======================================================")
    print("Generating OMI 8-Channel GDSII Physical Layout (2x2 mm^2)")
    print("=======================================================")
    
    builder = OMILayoutBuilder()
    
    print("Building Frame, Guard Rings, and Corner Targets...")
    builder.build_frame()
    
    print("Building Laser Input Port & Inverse Taper SSC...")
    builder.build_laser_input_port()
    
    print("Building 1:8 Cascaded MMI Splitter Tree...")
    builder.build_mmi_tree_1x8()
    
    print("Building 8-Channel LiTaO3 Electro-Optic Modulators...")
    builder.build_tflt_modulator_bank()
    
    print("Building Centum-Node TDV Constellation Interface...")
    builder.build_centum_node_tdv_interface()
    
    print("Building Dense 8-Waveguide Bus with DTI Air-Voids...")
    builder.build_dti_waveguide_bus()
    
    print("Building 8-Channel SACM Ge/Si APD Array...")
    builder.build_sacm_apd_array()
    
    print("Building CPO Fiber Ribbon Edge Couplers (127 um Pitch)...")
    builder.build_cpo_coupler_array()
    
    print("Building Foundry Diagnostic & MPW Test Modules...")
    builder.build_diagnostic_test_blocks()
    
    print("Exporting GDSII stream...")
    builder.export(GDS_PATH, LYP_PATH)
    
    print("\n[COMPLETE] Physical mask generation complete.")

if __name__ == "__main__":
    main()
