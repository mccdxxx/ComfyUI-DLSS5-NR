# ComfyUI-DLSS5-NR

**Unofficial, experimental ComfyUI integration for NVIDIA DLSS 5 Neural Rendering (NGX feature 18).**

The node runs Neural Rendering **in-process** inside ComfyUI through a small native D3D12 bridge. It does not launch a helper executable and it does not write temporary image files.

> [!WARNING]
> This project targets an undocumented / pre-release Neural Rendering interface and is not affiliated with, endorsed by, or supported by NVIDIA or Comfy Org. Runtime behavior may change with NVIDIA driver or `nvngx_dlssnr.dll` versions. Native driver/runtime failures can crash the ComfyUI process.

## What it does

```text
ComfyUI IMAGE
    -> Python/ctypes
    -> dlss5nr_bridge.dll
    -> D3D12 + NGX
    -> nvngx_dlssnr.dll (feature 18)
    -> ComfyUI IMAGE
```

Current v0.3.0 still uses CPU staging for the ComfyUI tensor transfer:

```text
Torch IMAGE -> CPU float32 -> D3D12 RGBA16F -> DLSS NR -> CPU float32 -> Torch IMAGE
```

There is no subprocess or disk round-trip. CUDA/D3D12 interop is planned as a later optimization.

ComfyUI receives **frame-by-frame progress updates** while an IMAGE batch is processed.

## Temporal mode: NVIDIA Optical Flow

v0.3.0 uses an explicit motion-vector temporal path and adds per-frame motion estimation through the **NVIDIA Optical Flow Accelerator (NVOFA)**.

Only two batch modes remain:

```text
still images
    Reset=1 for every image
    no temporal history
    no motion-vector resource

temporal
    frame 0: Reset=1 + explicit zero R16G16_FLOAT MV
    frame 1+: Reset=0 + NVIDIA Optical Flow MV from raw previous/current input frames
```

Temporal flow is estimated from the **raw input frames**, never from the DLSS-processed output:

```text
previous raw frame ----\
                        > NVIDIA Optical Flow -> current-to-previous MV -> DLSSNR.MVec
current raw frame -----/                                      |
                                                              + DLSS temporal history
```

Implementation details in v0.3.0:

- private D3D11 device on the same NVIDIA DXGI adapter used by the D3D12/NGX bridge;
- driver-provided `nvofapi64.dll` (no separate model/download);
- NVOFA output grid: **2x2**;
- NVOFA performance level: **FAST**;
- input to NVOFA: 8-bit luma in `B8G8R8A8_UNORM`;
- native NVOFA flow: coarse `R16G16_SINT`, S10.5 fixed-point (1/32 pixel);
- conversion to full-resolution `R16G16_FLOAT` using nearest-cell reconstruction;
- the DLSSNR MV texture stores normalized UV motion and uses `MVecScale=(width,height)`;
- NVOFA is called with current frame as input and previous frame as reference, producing the current-to-previous reprojection direction used by the temporal contract;
- NVOFA temporal hints are disabled in v0.3.0 so each frame pair is deterministic and a new ComfyUI batch can reset cleanly.

The first frame has no previous frame, so temporal mode bootstraps it with an explicit zero-MV field.

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

## Requirements

- Windows 10/11 x64
- NVIDIA RTX GPU
- Recent NVIDIA display driver
- NVIDIA Optical Flow driver API (`nvofapi64.dll`) for `temporal` mode
- A **compatible, legally obtained** `nvngx_dlssnr.dll`
- ComfyUI with Python, PyTorch and NumPy

NVIDIA Optical Flow hardware is available on Turing-generation NVIDIA GPUs and newer; all GeForce RTX generations satisfy that hardware-generation requirement. GPU support for Neural Rendering itself is still determined by the specific `nvngx_dlssnr.dll` you provide.

A `0xBAD00001` result means the Neural Rendering runtime rejected the feature on the current GPU/runtime/driver combination.

## Installation — normal users

**Do not download GitHub's automatically generated `Source code.zip` if you do not want to compile anything.**

1. Open **Releases** for this repository.
2. Download `ComfyUI-DLSS5-NR-vX.Y.Z-windows-x64.zip`.
3. Extract the contained `ComfyUI-DLSS5-NR` folder to:

   ```text
   ComfyUI/custom_nodes/ComfyUI-DLSS5-NR
   ```

4. Supply your own compatible NVIDIA Neural Rendering runtime:

   ```text
   ComfyUI-DLSS5-NR/runtime/nvngx_dlssnr.dll
   ```

5. Restart ComfyUI.
6. Add **experimental -> DLSS 5 NR -> DLSS 5 Neural Rendering (Unofficial)**.

The release ZIP already contains the project-owned native files:

```text
native/bin/dlss5nr_bridge.dll
runtime/caller/nvngx.dll_comfy.dll
```

**Visual Studio / MSVC is not required for normal installation.**

The prebuilt Windows release ZIP intentionally contains only the files needed to run the node. Developer tools, native source code, workflows and extended documentation remain in the repository and GitHub source archives.

### `_nvngx.dll`

Do not normally copy `_nvngx.dll` yourself. The bridge attempts, in order:

1. `runtime/_nvngx.dll` as an explicit local override;
2. normal Windows DLL search;
3. automatic discovery in NVIDIA DriverStore packages matching `nv*.inf_*`.

The project does not redistribute `_nvngx.dll`.

### `nvofapi64.dll`

Do not download or bundle `nvofapi64.dll`. It is supplied by the NVIDIA display driver and is loaded from the normal Windows driver installation when `batch_mode = temporal`.

`still images` does not initialize NVOFA.

## Developer build

Only developers building from source need Visual Studio Build Tools.

Requirements:

- Visual Studio 2022 Build Tools or Visual Studio 2022 with **Desktop development with C++**
- Windows 10/11 SDK

Run from a normal `cmd.exe` or PowerShell window:

```bat
build_native.bat
```

The builder locates MSVC and the Windows SDK directly; a Developer Command Prompt is not required.

Outputs:

```text
native/bin/dlss5nr_bridge.dll
runtime/caller/nvngx.dll_comfy.dll
```

The bridge now links the standard Windows `d3d11.lib` in addition to D3D12/DXGI. `nvofapi64.dll` is loaded dynamically at runtime and is not linked or redistributed.

## Node parameters

| Parameter | Purpose |
|---|---|
| `style` | Neural Rendering style selector (`natural`, `cinematic`, `default`, numeric experimental styles). |
| `preset` | Internal render preset. `3` is the current default. |
| `intensity` | Overall Neural Rendering strength. |
| `tone` | Local tone / lighting strength (`DLSSNR.LocalToneStrength`). |
| `structure` | Local structure / micro-detail strength (`DLSSNR.LocalStructureStrength`). |
| `skin` | Skin-specific structure strength. `-1` leaves the runtime's default behavior. |
| `auto_mask` | Enables the runtime's automatic mask path. |
| `batch_mode` | `still images` processes independent frames; `temporal` keeps history and supplies zero/NVIDIA Optical Flow motion vectors. |
| `gpu_index` | NVIDIA DXGI adapter index. The private NVOFA D3D11 device is created on the same adapter. |
| `channel_order` | `auto`, `RGBA`, or `BGRA`; useful because different runtime builds have exposed different R/B ordering. |

Output resolution is identical to input resolution. This node is Neural Rendering/post-processing, not DLSS Super Resolution.

## Runtime Info node

`DLSS 5 NR Runtime Info` reports:

- plugin version;
- native bridge version;
- selected GPU name/index;
- whether the NVIDIA Optical Flow D3D11 API is visible;
- temporal NVOFA grid/performance settings;
- runtime directory;
- size and SHA-256 of the supplied `nvngx_dlssnr.dll`.

Use it first when diagnosing a new runtime/GPU combination.

## Troubleshooting

### `Native bridge is missing`

If you are a normal user, you probably installed GitHub's **Source code** archive instead of the prebuilt Windows release ZIP. Download the release asset. Developers can run `build_native.bat`.

### `nvngx_dlssnr.dll not found`

Place your compatible runtime at:

```text
runtime/nvngx_dlssnr.dll
```

This repository intentionally does not provide download links or mirrors for proprietary/leaked NVIDIA binaries.

### `Could not load NVIDIA NGX core _nvngx.dll`

The bridge searches NVIDIA DriverStore automatically. As a diagnostic fallback:

```powershell
Get-ChildItem "$env:SystemRoot\System32\DriverStore\FileRepository" -Filter _nvngx.dll -Recurse -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object FullName, LastWriteTime, Length
```

A matching driver copy can be placed at `runtime/_nvngx.dll` as a local override. Do **not** rename `nvngx_dlss.dll`; it is a different component.

### `NVIDIA Optical Flow: could not load nvofapi64.dll`

This only affects `temporal` mode. Verify that a recent NVIDIA display driver is installed. Run `diagnose_runtime.bat`; it reports the driver copy under `%SystemRoot%\System32` when present.

Do not download `nvofapi64.dll` from third-party DLL sites.

### `NVIDIA Optical Flow: nvOFInit / nvOFExecute failed`

Attach the complete ComfyUI exception and `DLSS 5 NR Runtime Info` output to an issue. The native bridge includes the driver's own NVOF last-error text when available.

### `CreateFeature(18) failed: 0xBAD00001`

Feature not supported by the supplied Neural Rendering runtime on the selected GPU/driver combination. Use a runtime that legitimately supports your configuration.

### `0xBAD00002`

The observed Neural Rendering snippet rejected the caller. The release includes the project-owned thin caller helper expected by this integration. If this occurs with an untouched release ZIP, open an issue and attach the full ComfyUI error log plus the `Runtime Info` output.

### Wrong / blue colors

Try `channel_order = RGBA` or `BGRA`. `auto` compares both interpretations against the source and normally selects the plausible one.

### Old workflow says `batch_mode` is invalid

v0.3.0 uses only `still images` and `temporal`; the older `temporal sequence` / `temporal sequence (legacy no MV)` values are no longer valid. Delete and re-add the node, or change the saved widget to one of the two current values:

```text
still images
temporal
```

## GitHub Releases

Tags matching `v*` trigger the Windows release workflow. GitHub Actions:

1. checks that NVIDIA proprietary DLLs were not committed;
2. builds the native bridge, NVIDIA Optical Flow integration and caller helper on `windows-latest`;
3. assembles a clean user ZIP with the prebuilt project-owned DLLs;
4. writes a SHA-256 checksum;
5. creates the GitHub Release.

See [`docs/PUBLISHING.md`](docs/PUBLISHING.md).

## References / implementation notes

Useful references include:

- NVIDIA DLSS / NGX public repository: https://github.com/NVIDIA/DLSS
- NVIDIA Optical Flow SDK public repository: https://github.com/NVIDIA/NVIDIAOpticalFlowSDK
- NVIDIA Optical Flow programming guide: https://docs.nvidia.com/video-technologies/optical-flow-sdk/nvofa-programming-guide/index.html
- Zonnery experimental DLSS 5 NR player/reference: https://github.com/Zonnery/dlss5-nr-player
- NIGos DLSS5 bridge: https://github.com/NIGos/dlss5-bridge
- NVIDIA RTX nodes for ComfyUI: https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI

The NVOF D3D11 function-table integration and measured flow-direction/normalization behavior were informed by the MIT-licensed NIGos `dlss5-bridge`; attribution is retained in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

No NVIDIA runtime DLLs or NVIDIA SDK headers are vendored in this repository.

## Legal / licensing

The project's original source code is MIT licensed. NVIDIA trademarks, SDK/API names and proprietary binaries are owned by NVIDIA and are **not** covered by this project's MIT license.

This project does not redistribute:

- `_nvngx.dll`
- `nvngx_dlssnr.dll`
- `nvofapi64.dll`
- other NVIDIA runtime binaries
- NVIDIA NGX/Optical Flow SDK headers

The integration uses undocumented/pre-release Neural Rendering behavior, including a thin caller-forwarding helper and observed project/application identifiers. Before distributing or using this project, review the terms that apply to the NVIDIA software/runtime you use. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and [`docs/LEGAL_NOTES.md`](docs/LEGAL_NOTES.md).

## Status

v0.3.0 is the first stable project release with the explicit motion-vector temporal path and NVIDIA Optical Flow for real frame-to-frame motion. The integration remains unofficial and experimental with respect to the NVIDIA Neural Rendering interface.
