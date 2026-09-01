# SPDX-License-Identifier: MIT
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {
    "_nvngx.dll",
    "nvngx_dlssnr.dll",
    "nvngx_dlss.dll",
}

bad = []
for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    if ".git" in path.parts or "dist" in path.parts:
        continue
    if path.name.lower() in FORBIDDEN:
        bad.append(path.relative_to(ROOT))

if bad:
    print("ERROR: proprietary NVIDIA runtime DLL(s) found in repository tree:")
    for item in bad:
        print(f"  - {item}")
    sys.exit(1)

print("OK: no forbidden NVIDIA runtime DLLs found in repository tree.")
