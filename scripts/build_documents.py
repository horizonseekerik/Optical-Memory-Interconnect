"""
build_documents.py
Master build script to compile IEEE Transactions Manuscript and Simulation Report,
and generate high-resolution page previews in manuscript/previews/.
All paths are dynamically resolved relative to this script.
"""

import os
import sys
import subprocess
import shutil

# Resolve directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MANUSCRIPT_DIR = os.path.join(BASE_DIR, "manuscript")
PREVIEWS_DIR = os.path.join(MANUSCRIPT_DIR, "previews")

os.makedirs(PREVIEWS_DIR, exist_ok=True)

# Find pdflatex and pdftoppm
def find_tool(name):
    p = shutil.which(name)
    if p:
        return p
    miktex_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64"),
        r"C:\Program Files\MiKTeX\miktex\bin\x64"
    ]
    for mp in miktex_paths:
        candidate = os.path.join(mp, name if name.endswith(".exe") else f"{name}.exe")
        if os.path.exists(candidate):
            return candidate
    return name

PDFLATEX = find_tool("pdflatex")
PDFTOPPM = find_tool("pdftoppm")

def compile_document(tex_filename):
    print(f"\n=======================================================")
    print(f"Compiling: {tex_filename}")
    print(f"=======================================================")
    tex_path = os.path.join(MANUSCRIPT_DIR, tex_filename)
    if not os.path.exists(tex_path):
        print(f"[ERROR] File not found: {tex_path}")
        return False

    for pass_num in range(1, 3):
        print(f"--- Running pass {pass_num} ---")
        res = subprocess.run(
            [PDFLATEX, "-interaction=nonstopmode", tex_filename],
            cwd=MANUSCRIPT_DIR,
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            print(f"[WARNING] Pass {pass_num} exited with code {res.returncode}")
        else:
            print(f"Pass {pass_num} succeeded.")

    pdf_filename = tex_filename.replace(".tex", ".pdf")
    pdf_path = os.path.join(MANUSCRIPT_DIR, pdf_filename)
    if os.path.exists(pdf_path):
        print(f"[SUCCESS] Generated: {pdf_path} ({os.path.getsize(pdf_path):,} bytes)")
        return True
    else:
        print(f"[ERROR] PDF generation failed for {pdf_filename}")
        return False

def render_previews(pdf_filename, prefix):
    pdf_path = os.path.join(MANUSCRIPT_DIR, pdf_filename)
    if not os.path.exists(pdf_path):
        print(f"[SKIP] PDF not found for previews: {pdf_path}")
        return

    output_prefix = os.path.join(PREVIEWS_DIR, prefix)
    print(f"Rendering previews for {pdf_filename} -> {output_prefix}-*.png")
    subprocess.run(
        [PDFTOPPM, "-png", "-r", "150", pdf_path, output_prefix],
        check=True
    )
    print(f"[SUCCESS] Previews generated in {PREVIEWS_DIR}")

def main():
    print(f"Base Repository: {BASE_DIR}")
    print(f"Manuscript Directory: {MANUSCRIPT_DIR}")
    print(f"Previews Directory: {PREVIEWS_DIR}")

    docs = [
        ("IEEE_TRANSACTIONS_OMI_MANUSCRIPT.tex", "ieee_page"),
        ("OMI_SIMULATION_REPORT_AND_BENCHMARKS.tex", "sim_report_page")
    ]

    for tex_file, prefix in docs:
        success = compile_document(tex_file)
        if success:
            render_previews(tex_file.replace(".tex", ".pdf"), prefix)

    # Clean intermediate auxiliary files in manuscript/
    for ext in [".aux", ".log", ".out"]:
        for f in os.listdir(MANUSCRIPT_DIR):
            if f.endswith(ext):
                try:
                    os.remove(os.path.join(MANUSCRIPT_DIR, f))
                except Exception:
                    pass

    print("\n[COMPLETE] All documents compiled and previews generated.")

if __name__ == "__main__":
    main()
