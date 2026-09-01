# ComfyUI-DLSS5-NR

**Unofficial, experimental ComfyUI integration for NVIDIA DLSS 5 Neural Rendering (NGX feature 18).**

The node runs Neural Rendering **in-process** inside ComfyUI through a small native D3D12 bridge. It does not launch a helper executable and it does not write temporary image files.

> [!WARNING]
> This project targets an undocumented / pre-release interface and is not affiliated with, endorsed by, or supported by NVIDIA or Comfy Org. Runtime behavior may change with NVIDIA driver or `nvngx_dlssnr.dll` versions. Native driver/runtime failures can crash the ComfyUI process.

## What it does

```text
ComfyUI IMAGE
    -> Python/ctypes
    -> dlss5nr_bridge.dll
    -> D3D12 + NGX
    -> nvngx_dlssnr.dll (feature 18)
    -> ComfyUI IMAGE
```

Current v0.2.0 uses CPU staging for the ComfyUI tensor transfer:

```text
Torch IMAGE -> CPU float32 -> D3D12 RGBA16F -> DLSS NR -> CPU float32 -> Torch IMAGE
```

There is no subprocess or disk round-trip. CUDA/D3D12 interop is planned as a later optimization.

## Requirements

- Windows 10/11 x64
- NVIDIA RTX GPU
- Recent NVIDIA display driver
- A **compatible, legally obtained** `nvngx_dlssnr.dll`
- ComfyUI with Python, PyTorch and NumPy

GPU support is determined by the specific Neural Rendering runtime you provide. Stock/pre-release builds may support only particular GPU generations. A `0xBAD00001` result means the runtime rejected the feature on the current GPU/runtime/driver combination.

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

### `_nvngx.dll`

Do not normally copy `_nvngx.dll` yourself. The bridge attempts, in order:

1. `runtime/_nvngx.dll` as an explicit local override;
2. normal Windows DLL search;
3. automatic discovery in the active NVIDIA DriverStore packages matching `nv*.inf_*`.

The project does not redistribute `_nvngx.dll`.

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
| `batch_mode` | `still images` resets temporal state for every image; `temporal sequence` keeps state after the first frame. |
| `gpu_index` | NVIDIA DXGI adapter index. |
| `channel_order` | `auto`, `RGBA`, or `BGRA`; useful because different runtime builds have exposed different R/B ordering. |

Output resolution is identical to input resolution. This node is Neural Rendering/post-processing, not DLSS Super Resolution.

## Runtime Info node

`DLSS 5 NR Runtime Info` reports:

- plugin version;
- native bridge version;
- selected GPU name/index;
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

### `CreateFeature(18) failed: 0xBAD00001`

Feature not supported by the supplied runtime on the selected GPU/driver combination. Use a runtime that legitimately supports your configuration.

### `0xBAD00002`

The observed Neural Rendering snippet rejected the caller. The release includes the project-owned thin caller helper expected by this integration. If this occurs with an untouched release ZIP, open an issue and attach the full ComfyUI error log plus the `Runtime Info` output.

### Wrong / blue colors

Try `channel_order = RGBA` or `BGRA`. `auto` compares both interpretations against the source and normally selects the plausible one.

## GitHub Releases

Tags matching `v*` trigger the Windows release workflow. GitHub Actions:

1. checks that NVIDIA proprietary DLLs were not committed;
2. builds the native bridge and caller helper on `windows-latest`;
3. assembles a clean user ZIP with the prebuilt project-owned DLLs;
4. writes a SHA-256 checksum;
5. creates the GitHub Release.

See [`docs/PUBLISHING.md`](docs/PUBLISHING.md).

## References / implementation notes

The integration uses observed behavior of NVIDIA NGX/Neural Rendering interfaces and public NGX API naming. Useful references include:

- NVIDIA DLSS / NGX public repository: https://github.com/NVIDIA/DLSS
- Zonnery's experimental DLSS 5 NR player/reference: https://github.com/Zonnery/dlss5-nr-player
- NVIDIA RTX nodes for ComfyUI: https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI

No NVIDIA SDK headers or NVIDIA runtime DLLs are vendored in this repository.

## Legal / licensing

The project's original source code is MIT licensed. NVIDIA trademarks, SDK/API names and proprietary binaries are owned by NVIDIA and are **not** covered by this project's MIT license.

This project does not redistribute:

- `_nvngx.dll`
- `nvngx_dlssnr.dll`
- other `nvngx_*` NVIDIA runtime binaries
- NVIDIA NGX SDK headers

The integration uses undocumented behavior, including a thin caller-forwarding helper and observed project/application identifiers. Before distributing or using this project, review the terms that apply to the NVIDIA software/runtime you use. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and [`docs/LEGAL_NOTES.md`](docs/LEGAL_NOTES.md).

## Status

v0.2.0 is intended as an **experimental GitHub release**, not an official NVIDIA integration. GitHub publication is the recommended first step; Comfy Registry / Manager publication should wait until the licensing/redistribution position and binary-scanning requirements have been reviewed.
