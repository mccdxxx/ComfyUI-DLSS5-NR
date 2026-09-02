# v0.3.0-alpha2

This prerelease turns the successful alpha1 explicit-MV experiment into the default temporal path and adds real frame-to-frame motion estimation using NVIDIA Optical Flow.

## What changed

- Removed `temporal sequence (legacy no MV)`.
- Simplified `batch_mode` to exactly two choices:
  - `still images`
  - `temporal`
- `temporal` always binds a full-resolution `R16G16_FLOAT` motion-vector resource.
- First temporal frame uses explicit zero motion vectors and `Reset=1`.
- Later temporal frames use NVIDIA Optical Flow between the raw previous/current input frames with `Reset=0`.
- Added a private D3D11 device on the same NVIDIA adapter for `nvofapi64.dll`.
- Uses NVOFA grid 2, FAST mode, S10.5 flow output and nearest full-resolution reconstruction.
- Converts NVOFA current-to-previous pixel displacement to normalized UV and sets `DLSSNR.MVecScale=(width,height)`.
- Runtime Info reports whether the NVOF D3D11 driver entry point is available.
- `diagnose_runtime.bat` now reports the installed `nvofapi64.dll`.
- `nvofapi64.dll` is explicitly blocked from git/release packaging alongside other NVIDIA proprietary runtimes.

## Expected test

Use a normal video batch and compare `still images` vs `temporal`.

The temporal build should retain the static-frame stability seen with alpha1 zero-MV while improving history reprojection during actual motion.

If temporal output smears specifically along motion direction, capture a short reproducible source clip and open an issue; the first things to verify are motion direction/scale and scene/disocclusion behavior.

## Compatibility note

Saved alpha1 workflows containing `temporal sequence` or `temporal sequence (legacy no MV)` need the node re-added or the widget changed to `temporal`.
