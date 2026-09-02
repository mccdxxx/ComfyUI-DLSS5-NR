# Changelog

## 0.3.0 - 2026-09-02

- Promoted the tested NVIDIA Optical Flow temporal implementation from `0.3.0-alpha2` to the stable project release.
- Added native ComfyUI frame progress reporting for IMAGE batches.
- Stable release exposes only two batch modes: `still images` and `temporal`.
- `temporal` uses explicit zero motion vectors on frame 0 and NVIDIA Optical Flow current-to-previous vectors on later frames.
- Updated runtime/build/documentation version labels to `0.3.0`.

## 0.3.0-alpha2 - 2026-09-02

- Promoted the explicit motion-vector temporal path validated in alpha1.
- Reduced `batch_mode` to two choices: `still images` and `temporal`.
- Added NVIDIA Optical Flow (NVOFA) for frame 1+ in temporal mode.
- Temporal frame 0 uses explicit zero `R16G16_FLOAT` motion vectors; later frames use current-to-previous optical flow from the raw input sequence.
- Added a private D3D11 device on the same selected NVIDIA adapter and dynamic loading of driver-provided `nvofapi64.dll`.
- Uses NVOFA API 2.0 layout, grid 2 and FAST performance level.
- Converts S10.5 NVOFA flow to full-resolution normalized-UV `R16G16_FLOAT` with nearest-cell reconstruction and `MVecScale=(width,height)`.
- Runtime Info and diagnostics now report NVIDIA Optical Flow availability.
- Added `nvofapi64.dll` to proprietary-binary release guards.
- Added third-party attribution for the MIT-licensed NIGos `dlss5-bridge` work that informed the D3D11 NVOF table and measured flow convention.

## 0.3.0-alpha1 - 2026-09-02

- Added an explicit full-resolution `R16G16_FLOAT` zero motion-vector texture for `temporal sequence`.
- Binds the experimental motion contract as `DLSSNR.MVec` with `MVecScaleX/Y` and `MVecSubrect*` fields.
- Keeps `still images` unchanged and adds `temporal sequence (legacy no MV)` for direct A/B comparison with v0.2.0 behavior.
- Rebuilds Feature 18 when switching between zero-MV and no-MV contracts.
- Clears the MV parameter before releasing the D3D12 resource to avoid stale pointers across mode switches.
- Marks alpha tags as GitHub prereleases in the release workflow.
- This alpha intentionally uses zero vectors only; optical-flow estimation is not included yet.

## 0.2.0 - 2026-09-01

- Prepared repository for public GitHub distribution.
- Added GitHub Actions Windows CI and tagged-release packaging.
- Normal users can use prebuilt project-owned DLLs from release ZIPs; MSVC is developer-only.
- Added safeguards against accidentally bundling NVIDIA proprietary runtime DLLs.
- Improved DriverStore discovery to use the actual Windows directory instead of a hard-coded `C:\Windows` path.
- Build script now searches both Program Files roots, including full Visual Studio installations used by GitHub Actions.
- Runtime Info now reports selected GPU and SHA-256 of the user-supplied Neural Rendering runtime.
- Retained `channel_order = auto | RGBA | BGRA` compatibility handling.
- Added third-party notices, legal-release notes and publishing documentation.

## 0.1.10

- Preserved widget ordering for old workflows after adding `channel_order`.
