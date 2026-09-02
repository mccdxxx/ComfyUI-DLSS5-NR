# v0.3.0

This is the first stable project release of the NVIDIA Optical Flow temporal path tested in the `0.3.0-alpha1` / `0.3.0-alpha2` prereleases.

## Highlights

- Only two batch modes remain: `still images` and `temporal`.
- `still images` resets Neural Rendering history for every input image.
- `temporal` supplies an explicit zero `R16G16_FLOAT` motion-vector field for frame 0.
- From frame 1 onward, `temporal` estimates current-to-previous motion with the NVIDIA Optical Flow Accelerator through the driver-provided `nvofapi64.dll`.
- Motion estimation is performed from the raw input frames, not from Neural Rendering output.
- Added frame-by-frame ComfyUI progress reporting for IMAGE batches.
- Runtime/build/version labels have been promoted from `0.3.0-alpha2` to `0.3.0`.

## Runtime packaging

The Windows release ZIP contains the project-owned prebuilt native bridge and caller helper, but does not redistribute NVIDIA runtime DLLs. Users still provide their own compatible `runtime/nvngx_dlssnr.dll`; `_nvngx.dll` and `nvofapi64.dll` come from the installed NVIDIA driver unless an explicit supported override is used.

The prebuilt Windows ZIP is intentionally minimal. Developer sources, `tools/`, `docs/` and GitHub workflows are available in the repository/source archive rather than the runtime ZIP.

## Compatibility note

Saved workflows using the old `temporal sequence` or `temporal sequence (legacy no MV)` widget values should re-add the node or select one of the current values: `still images` or `temporal`.
