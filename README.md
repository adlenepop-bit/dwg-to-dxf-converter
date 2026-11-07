# DWG to DXF Converter (Multi-Engine & Standalone)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

> High-performance standalone and multi-engine tool converting AutoCAD DWG files (releases R12 through 2018+) to DXF without requiring an AutoCAD license or third-party CAD installation.
> 
> *Outil autonome haute performance convertissant les plans DWG AutoCAD (versions R12 à 2018+) en DXF sans dépendance obligatoire envers AutoCAD ni licence tierce.*

---

## English

### Overview

`dwg-to-dxf-converter` solves the common bottleneck of converting proprietary Autodesk DWG vector drawings into accessible, open-format DXF files. It implements an intelligent multi-engine cascade strategy:

1. **Engine 1: GNU LibreDWG (Bundled / Standalone)**: Embedded in `bin/cad/`, runs natively at high speed without external software or CAD licenses.
2. **Engine 2: Acme CAD Converter CLI**: Automatically detected if installed on the host machine.
3. **Engine 3: AutoCAD Core Console (`accoreconsole.exe`)**: Leverages headless official Autodesk console if AutoCAD is installed (AutoCAD 2020 through 2026).
4. **Engine 4: ODA File Converter**: Utilizes Open Design Alliance converter if present on the system.
5. **Engine 5: Direct AutoCAD COM Automation**: Native Windows COM dispatch fallback.

If an engine fails or is unavailable, the converter seamlessly rolls over to the next engine in the hierarchy.

---

### Features

- **Zero-Dependency by Default**: Works immediately out of the box on Windows with the integrated LibreDWG binary.
- **Universal AutoCAD Version Support**: DWG versions R12, R14, 2000, 2004, 2007, 2010, 2013, 2018+.
- **Dual Interface**: Command-Line Interface (CLI) for scripts and batch pipelines, plus a clean Python API.
- **Smart Path Resolver**: `ensure_dxf` utility passes existing DXFs transparently and only converts when receiving a DWG.

---

### Installation

Clone the repository:
```bash
git clone https://github.com/adlenepop-bit/dwg-to-dxf-converter.git
cd dwg-to-dxf-converter
```

Optional dependencies (only if you want to inspect or manipulate DXFs in Python):
```bash
pip install -r requirements.txt
```

---

### CLI Usage

```bash
# Convert a DWG to DXF (auto-named input.dxf)
python dwg_converter.py plan.dwg

# Convert specifying exact output file name
python dwg_converter.py plan.dwg output/plan_converted.dxf

# Specify target DXF format version (e.g. ACAD2018, ACAD2013, ACAD2010, ACAD2004, ACAD2000, ACAD14, ACAD12)
python dwg_converter.py plan.dwg --version ACAD2018
```

---

### Python API Usage

```python
from dwg_converter import convert_dwg_to_dxf, ensure_dxf

# 1. Direct conversion
dxf_path = convert_dwg_to_dxf("drawings/piping_isometric.dwg", "exports/piping_isometric.dxf")
print(f"DXF created at: {dxf_path}")

# 2. Transparent resolver (DXF unchanged, DWG converted on-the-fly)
clean_dxf = ensure_dxf("drawings/electrical_schematic.dwg")
```

---

### Running Tests

Execute the automated test suite:
```bash
python test_converter.py
# or
python -m unittest test_converter.py
```

---

## Français

### Présentation

`dwg-to-dxf-converter` résout le problème classique de la conversion des fichiers DWG propriétaires Autodesk en fichiers DXF standardisés et facilement analysables par les bibliothèques open-source (comme `ezdxf`).

Il intègre une cascade intelligente de 5 moteurs avec bascule automatique :

1. **Moteur 1 : GNU LibreDWG (Intégré et Autonome)** : Présent dans `bin/cad/`, ultra-rapide, 100% autonome, ne nécessite aucune installation d'AutoCAD.
2. **Moteur 2 : Acme CAD Converter CLI** : Détecté automatiquement s'il est installé sur la machine.
3. **Moteur 3 : AutoCAD Core Console (`accoreconsole.exe`)** : Console officielle Autodesk exécutée en arrière-plan (versions 2020 à 2026).
4. **Moteur 4 : ODA File Converter** : Détecté et exécuté si disponible sur le poste.
5. **Moteur 5 : Automatisation COM AutoCAD directe** : Pilote AutoCAD en arrière-plan sous Windows.

---

### Utilisation Rapide en Ligne de Commande (CLI)

```bash
# Conversion simple d'un DWG vers DXF
python dwg_converter.py plan.dwg

# Spécification du chemin de sortie
python dwg_converter.py plan.dwg exports/resultat.dxf

# Choix de la version DXF cible (ex: ACAD2018, ACAD2013, ACAD2004)
python dwg_converter.py plan.dwg --version ACAD2018
```

---

### Utilisation en Bibliothèque Python

```python
from dwg_converter import convert_dwg_to_dxf, ensure_dxf

# Conversion explicite
dxf_resultat = convert_dwg_to_dxf("plan_isometrique.dwg")

# Résolution transparente : retourne le fichier si déjà DXF, convertit si DWG
dxf_pret = ensure_dxf("chemin_vers_dessin.dwg")
```

---

## Project Structure / Structure du Projet

```text
dwg-to-dxf-converter/
├── bin/
│   └── cad/
│       ├── dwg2dxf.exe       # Moteur autonome LibreDWG
│       ├── libiconv-2.dll
│       ├── libpcre2-8-0.dll
│       ├── libpcre2-16-0.dll
│       └── libredwg-0.dll
├── dwg_converter.py          # Convertisseur multi-moteurs CLI & API
├── test_converter.py         # Suite de tests unitaires
├── requirements.txt          # Dépendances optionnelles
├── LICENSE                   # Licence MIT
├── .gitignore                # Règles d'exclusion Git
└── README.md                 # Documentation bilingue
```

---

## Author / Auteur

**adlenepop-bit**  
- GitHub: [https://github.com/adlenepop-bit](https://github.com/adlenepop-bit)

---

## License / Licence

Ce projet est distribué sous la [Licence MIT](LICENSE). Copyright (c) 2026 adlenepop-bit.
