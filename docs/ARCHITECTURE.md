# Architecture

## v0.2.0 data path

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
    +-- DXGI NVIDIA adapter selection
    +-- D3D12 device/queue/list/fence
    +-- NGX core discovery/init
    +-- Neural Rendering feature 18
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
_nvngx.dll
```

## Planned optimization

Replace CPU staging with CUDA/D3D12 external-memory + fence/semaphore interoperability so ComfyUI tensors remain GPU-resident.
