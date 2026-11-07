"""
dwg_converter.py
=================
High-performance standalone and multi-engine DWG to DXF converter.
Supports 5 conversion engines with graceful automatic fallback:
  1. Standalone High-Performance Engine: GNU LibreDWG (bin/cad/dwg2dxf.exe)
  2. Acme CAD Converter CLI (if installed)
  3. AutoCAD Core Console (accoreconsole.exe)
  4. ODA File Converter (if installed)
  5. Direct AutoCAD COM Automation (Windows)
"""

from __future__ import annotations

import sys
import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("dwg_converter")


class DWGConversionError(RuntimeError):
    pass


def _find_libredwg() -> str:
    """Localize integrated dwg2dxf binary or search system PATH."""
    bin_name = "dwg2dxf.exe" if sys.platform == "win32" else "dwg2dxf"
    candidates = [
        Path(__file__).parent / "bin" / "cad" / bin_name,
        Path(__file__).parent / "bin" / bin_name,
        Path(__file__).parent / bin_name,
    ]
    for c in candidates:
        if c.exists():
            return str(c.resolve())
    which_bin = shutil.which("dwg2dxf")
    return str(which_bin) if which_bin else ""


def _find_acme_converter() -> str:
    """Localize Acme CAD Converter executable if present."""
    candidates = [
        r"C:\Program Files\Acme CAD Converter\AcmeCADConverter.exe",
        r"C:\Program Files (x86)\Acme CAD Converter\AcmeCADConverter.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return str(c)
    which_bin = shutil.which("AcmeCADConverter")
    return str(which_bin) if which_bin else ""


def _find_accoreconsole() -> str:
    """Localize AutoCAD Core Console for native Autodesk batch conversion."""
    accore_paths = [
        r"C:\Program Files\Autodesk\AutoCAD 2026\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2025\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2024\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2021\accoreconsole.exe",
        r"C:\Program Files\Autodesk\AutoCAD 2020\accoreconsole.exe",
    ]
    for p in accore_paths:
        if Path(p).exists():
            return p
    which_bin = shutil.which("accoreconsole")
    return str(which_bin) if which_bin else ""


def _find_oda_converter() -> str:
    """Localize ODA File Converter executable if present."""
    for name in ("ODAFileConverter", "oda_file_converter", r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe"):
        path = shutil.which(name) or (name if Path(name).exists() else None)
        if path:
            return str(path)
    return ""


def _convert_via_autocad_com(dwg_path: Path, target_path: Path) -> bool:
    """Fallback using direct AutoCAD COM automation (Windows only)."""
    try:
        import win32com.client
    except ImportError:
        return False
    try:
        try:
            acad = win32com.client.GetActiveObject("AutoCAD.Application")
        except Exception:
            acad = win32com.client.Dispatch("AutoCAD.Application")
        acad.Visible = False
        doc = acad.Documents.Open(str(dwg_path.resolve()), True)
        save_success = False
        # DXF SaveAs format enum: 61 = 2018 DXF, 49 = 2013 DXF, 37 = 2010 DXF, 25 = 2004 DXF
        for fmt in (61, 49, 37, 25):
            try:
                doc.SaveAs(str(target_path.resolve()), fmt)
                save_success = True
                break
            except Exception:
                continue
        try:
            doc.Close(False)
        except Exception:
            pass
        return save_success and target_path.exists() and target_path.stat().st_size > 100
    except Exception as e_com:
        logger.warning("AutoCAD COM error: %s", e_com)
        return False


def convert_dwg_to_dxf(dwg_path: str | Path, output_dxf_path: Optional[str | Path] = None, out_version: str = "ACAD2018") -> str:
    """
    Converts a DWG file to DXF format and returns the resolved DXF path.
    Engine priority:
      1. LibreDWG dwg2dxf (100% standalone, fast, zero CAD license needed)
      2. Acme CAD Converter CLI (if installed)
      3. AutoCAD Core Console (accoreconsole.exe)
      4. ODA File Converter (if installed)
      5. Direct AutoCAD COM Automation (Windows)
    """
    dwg_path = Path(dwg_path).resolve()
    if not dwg_path.exists():
        raise DWGConversionError(f"DWG file not found: {dwg_path}")

    target = Path(output_dxf_path).resolve() if output_dxf_path else dwg_path.with_suffix(".dxf")
    target.parent.mkdir(parents=True, exist_ok=True)

    # 1. ENGINE 1: GNU LibreDWG (dwg2dxf) standalone
    libredwg = _find_libredwg()
    if libredwg:
        try:
            ver_clean = out_version.upper().replace("ACAD", "").replace("R", "")
            ver_arg = f"r{ver_clean}" if ver_clean in ("12", "14", "2000", "2004", "2007", "2010", "2013", "2018") else "r2018"
            cmd = [libredwg, "-y", "--as", ver_arg, "-o", str(target), str(dwg_path)]
            env = os.environ.copy()
            # Ensure dwg2dxf DLLs directory is prepended to PATH
            bin_dir = str(Path(libredwg).parent)
            env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
            
            res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=60, env=env)
            if target.exists() and target.stat().st_size > 100:
                logger.info("DWG->DXF conversion successful via LibreDWG (%d bytes)", target.stat().st_size)
                return str(target)
            else:
                logger.warning("LibreDWG conversion produced invalid output: %s", res.stderr[:300])
        except Exception as e_ld:
            logger.warning("LibreDWG error for %s: %s", dwg_path.name, e_ld)

    # 2. ENGINE 2: Acme CAD Converter CLI (/r /x{ver})
    acme = _find_acme_converter()
    if acme:
        try:
            ver_clean = out_version.upper().replace("ACAD", "").replace("R", "")
            if not ver_clean:
                ver_clean = "2018"
            cmd = [acme, "/r", f"/x{ver_clean}", str(dwg_path), str(target)]
            subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=60)
            if target.exists() and target.stat().st_size > 100:
                logger.info("DWG->DXF conversion successful via Acme CAD Converter (%d bytes)", target.stat().st_size)
                return str(target)
        except Exception as e_acme:
            logger.warning("Acme CAD Converter error for %s: %s", dwg_path.name, e_acme)

    # 3. ENGINE 3: AutoCAD Core Console (accoreconsole.exe)
    accore = _find_accoreconsole()
    if accore:
        scr_path = target.parent / f"convert_{target.stem}.scr"
        try:
            dxf_str = str(target).replace("\\", "/")
            with open(scr_path, "w", encoding="utf-8") as f:
                f.write("FILEDIA 0\n")
                f.write("CMDDIA 0\n")
                f.write("DXFOUT\n")
                f.write(f'"{dxf_str}"\n')
                f.write("16\n")
                f.write("QUIT\nY\n")
            cmd = [accore, "/i", str(dwg_path), "/s", str(scr_path)]
            subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=60)
            if target.exists() and target.stat().st_size > 100:
                logger.info("DWG->DXF conversion successful via accoreconsole (%d bytes)", target.stat().st_size)
                return str(target)
        except Exception as e_acc:
            logger.warning("AutoCAD accoreconsole error for %s: %s", dwg_path.name, e_acc)
        finally:
            if scr_path.exists():
                try:
                    scr_path.unlink()
                except Exception:
                    pass

    # 4. ENGINE 4: ODA File Converter
    converter = _find_oda_converter()
    if converter:
        try:
            with tempfile.TemporaryDirectory() as in_dir, tempfile.TemporaryDirectory() as out_dir:
                staged = Path(in_dir) / dwg_path.name
                shutil.copy(dwg_path, staged)
                cmd = [converter, in_dir, out_dir, out_version, "DXF", "0", "1", "*.dwg"]
                subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=120)
                produced = Path(out_dir) / (dwg_path.stem + ".dxf")
                if produced.exists():
                    shutil.move(produced, target)
                    return str(target)
        except Exception as e_oda:
            logger.warning("ODAFileConverter error for %s: %s", dwg_path.name, e_oda)

    # 5. ENGINE 5: Direct AutoCAD COM Automation fallback
    try:
        if _convert_via_autocad_com(dwg_path, target):
            logger.info("DWG->DXF conversion successful via AutoCAD COM (%d bytes)", target.stat().st_size)
            return str(target)
    except Exception:
        pass

    raise DWGConversionError(f"Unable to convert {dwg_path.name} to DXF. No functional conversion engine available.")


def ensure_dxf(path: str | Path) -> str:
    """Returns a usable DXF path, automatically converting from DWG if necessary."""
    path_str = str(path)
    if path_str.lower().endswith(".dxf"):
        return str(Path(path_str).resolve())
    if path_str.lower().endswith(".dwg"):
        return convert_dwg_to_dxf(path_str)
    raise DWGConversionError(f"Unsupported file extension: {path} (expected .dxf or .dwg)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="High-performance DWG to DXF Converter (Multi-Engine)")
    parser.add_argument("input", help="Path to input DWG file")
    parser.add_argument("output", nargs="?", default=None, help="Path to output DXF file (optional)")
    parser.add_argument("--version", default="ACAD2018", help="Target DXF version (default: ACAD2018)")
    args = parser.parse_args()

    try:
        out = convert_dwg_to_dxf(args.input, args.output, out_version=args.version)
        print(f"[OK] Conversion successful: {out}")
        sys.exit(0)
    except Exception as err:
        print(f"[ERROR] Conversion failed: {err}", file=sys.stderr)
        sys.exit(1)
