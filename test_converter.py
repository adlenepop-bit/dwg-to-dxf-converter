"""
test_converter.py
=================
Unit tests and integration verification for DWG to DXF Converter.
Run with:
    python test_converter.py
    or
    python -m unittest test_converter.py
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from dwg_converter import (
    convert_dwg_to_dxf,
    ensure_dxf,
    _find_libredwg,
    _find_acme_converter,
    _find_accoreconsole,
    _find_oda_converter,
    DWGConversionError,
)


class TestDWGConverter(unittest.TestCase):

    def test_01_libredwg_engine_located(self):
        """Verifies that the standalone GNU LibreDWG engine binary is located."""
        binary_path = _find_libredwg()
        self.assertTrue(
            bool(binary_path),
            "LibreDWG binary (dwg2dxf) was not found in bin/cad/ or PATH."
        )
        self.assertTrue(
            Path(binary_path).exists(),
            f"Binary path resolved but does not exist on disk: {binary_path}"
        )
        print(f"\n[OK] Standalone engine located: {binary_path}")

    def test_02_engine_detectors_non_crashing(self):
        """Verifies that all alternate engine discovery functions run cleanly without exceptions."""
        acme = _find_acme_converter()
        accore = _find_accoreconsole()
        oda = _find_oda_converter()
        self.assertIsInstance(acme, str)
        self.assertIsInstance(accore, str)
        self.assertIsInstance(oda, str)

    def test_03_ensure_dxf_direct_passthrough(self):
        """Verifies that ensure_dxf passes through existing .dxf files directly."""
        dummy_dxf = Path(__file__).parent / "test_dummy.dxf"
        try:
            dummy_dxf.write_text("0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF\n", encoding="ascii")
            resolved = ensure_dxf(str(dummy_dxf))
            self.assertEqual(resolved, str(dummy_dxf.resolve()))
        finally:
            if dummy_dxf.exists():
                dummy_dxf.unlink()

    def test_04_unsupported_extension_error(self):
        """Verifies that unsupported file extensions raise DWGConversionError."""
        with self.assertRaises(DWGConversionError):
            ensure_dxf("document.pdf")

    def test_05_missing_dwg_file_error(self):
        """Verifies that non-existent DWG files raise DWGConversionError."""
        with self.assertRaises(DWGConversionError):
            convert_dwg_to_dxf("non_existent_file_xyz_123.dwg")


if __name__ == "__main__":
    unittest.main(verbosity=2)
