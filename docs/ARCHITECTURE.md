# Architecture

## v0.3.0 data path

```text
ComfyUI IMAGE [B,H,W,C]
    |
    | torch -> CPU float32 RGB
    v
ctypes
    |
    v
dlss5nr_bridge.dll
    |
    +-- DXGI: select NVIDIA adapter
    +-- D3D12: DLSS/NGX device, queue, textures
    +-- NGX core discovery/init
    +-- Neural Rendering feature 18
    |
    +-- temporal only -----------------------------------------------+
    |                                                               |
    |   private D3D11 device on the SAME DXGI adapter               |
    |        |                                                      |
    |        +-- raw input RGB -> CPU luma/BGRA8 -> D3D11 texture   |
    |        +-- nvofapi64.dll / NVIDIA Optical Flow                |
    |        +-- R16G16_SINT S10.5 coarse flow                      |
    |        +-- CPU staging readback                               |
    |        +-- nearest reconstruction + UV normalization          |
    |        +-- D3D12 R16G16_FLOAT DLSSNR.MVec --------------------+
    |
    v
RGBA16F D3D12 input/output textures
    |
    v
CPU float32 RGB
    |
    v
ComfyUI IMAGE
```

The D3D12/NGX session and feature are persistent within the ComfyUI Python process and reused when compatible with the next image dimensions/settings.

The NVOFA session is created only in `temporal` mode. Switching back to `still images` releases its private D3D11 textures/session so that OFA VRAM is not retained unnecessarily.

## Runtime files

Project-owned:

```text
native/bin/dlss5nr_bridge.dll
runtime/caller/nvngx.dll_comfy.dll
```

User/NVIDIA supplied:

```text
runtime/nvngx_dlssnr.dll
```

Driver supplied/discovered:

```text
_nvngx.dll       # NGX core, discovered from DriverStore when necessary
nvofapi64.dll    # NVIDIA Optical Flow API, normal Windows driver search
```

None of the NVIDIA DLLs above are redistributed by this repository.

## Batch modes

### still images

Each image is independent:

```text
DLSSNR.Reset = 1
DLSSNR.MVec = null
```

No NVOFA session is opened.

### temporal

The feature has a persistent full-resolution `R16G16_FLOAT` MV resource.

Frame 0:

```text
NVOFA: prime current raw frame as previous-frame history
DLSSNR.Reset = 1
DLSSNR.MVec = explicit zero field
```

Frame N > 0:

```text
raw current + raw previous
    -> NVIDIA Optical Flow
    -> current-to-previous S10.5 flow
    -> nearest full-resolution reconstruction
    -> normalized UV R16G16_FLOAT
    -> DLSSNR.MVec

DLSSNR.Reset = 0
DLSSNR.MVecScale = (width, height)
```

The motion estimator receives **raw ComfyUI input frames**, not Neural Rendering output. This avoids a feedback loop where model-generated detail could alter the next frame's motion estimate.

## NVOFA transport

The Neural Rendering path is D3D12, but v0.3.0 uses the NVOF **D3D11** driver entry point on a private D3D11 device created from the same `IDXGIAdapter1`.

Reasons:

- the installed display driver provides `nvofapi64.dll`;
- D3D11 NVOF resource synchronization is handled by the driver/API;
- the D3D11 function-table behavior and flow direction have existing field validation;
- the current ComfyUI bridge already stages frames through CPU, so a small D3D11 flow readback does not introduce a new class of GPU-sharing synchronization yet.

Fixed v0.3.0 settings:

```text
NVOF API layout: 0x20
mode: optical flow
grid: 2x2
perf: FAST (20)
external hints: disabled
NVOFA temporal hints: disabled
input: B8G8R8A8_UNORM luma
output: R16G16_SINT
```

NVOF vectors use signed S10.5 storage: one integer unit is 1/32 pixel. For a cell `(fx,fy)`:

```text
pixel_motion = (fx, fy) / 32
stored_MV_uv = pixel_motion / (width, height)
DLSSNR.MVecScale = (width, height)
```

No sign flip is applied: with NVOFA `inputFrame=current` and `referenceFrame=previous`, the measured vector direction is already current-to-previous reprojection.

## Planned optimization

The current implementation prioritizes correctness/debuggability and still performs CPU staging for:

- ComfyUI image transfer;
- NVOFA flow readback/conversion.

A future version can replace this with direct CUDA/D3D12/D3D11 shared-resource paths and GPU-side flow conversion after the temporal contract is validated on a broader set of videos.
