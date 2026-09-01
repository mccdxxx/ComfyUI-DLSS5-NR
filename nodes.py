# SPDX-License-Identifier: MIT
# Copyright (c) 2026 ComfyUI-DLSS5-NR contributors

import ctypes
import hashlib
import os
import platform
import threading
from pathlib import Path

import numpy as np
import torch

_ROOT = Path(__file__).resolve().parent
_BRIDGE = _ROOT / "native" / "bin" / "dlss5nr_bridge.dll"
_RUNTIME = _ROOT / "runtime"

_lock = threading.RLock()
_lib = None
_initialized_gpu = None
_dll_directory_handles = []

__version__ = "0.2.0"


class DLSS5NRError(RuntimeError):
    pass


def _decode_error(buf: ctypes.Array) -> str:
    try:
        return buf.value.decode("utf-8", errors="replace")
    except Exception:
        return "Unknown native DLSS5 NR error"


def _load_library():
    global _lib
    if _lib is not None:
        return _lib

    if platform.system() != "Windows":
        raise DLSS5NRError("DLSS 5 Neural Rendering node is Windows-only (D3D12/NGX).")
    if not _BRIDGE.exists():
        raise DLSS5NRError(
            f"Native bridge is missing: {_BRIDGE}\n"
            "Normal users: install the prebuilt Windows ZIP from GitHub Releases (not the GitHub Source code ZIP).\n"
            "Developers: run build_native.bat, then restart ComfyUI."
        )

    # Keep AddDllDirectory handles alive for the lifetime of the process.
    # CPython removes a directory when the returned handle is closed/GC'd.
    for dll_dir in (_ROOT / "native" / "bin", _RUNTIME, _RUNTIME / "caller"):
        if dll_dir.exists():
            _dll_directory_handles.append(os.add_dll_directory(str(dll_dir)))

    lib = ctypes.WinDLL(str(_BRIDGE))

    lib.dlss5nr_init.argtypes = [
        ctypes.c_int,
        ctypes.c_wchar_p,
        ctypes.c_char_p,
        ctypes.c_int,
    ]
    lib.dlss5nr_init.restype = ctypes.c_int

    lib.dlss5nr_process.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,   # style
        ctypes.c_int,   # preset
        ctypes.c_float, # intensity
        ctypes.c_float, # tone
        ctypes.c_float, # structure
        ctypes.c_float, # skin
        ctypes.c_int,   # automask
        ctypes.c_int,   # reset
        ctypes.c_char_p,
        ctypes.c_int,
    ]
    lib.dlss5nr_process.restype = ctypes.c_int

    lib.dlss5nr_shutdown.argtypes = []
    lib.dlss5nr_shutdown.restype = None

    lib.dlss5nr_version.argtypes = []
    lib.dlss5nr_version.restype = ctypes.c_char_p

    lib.dlss5nr_gpu_name.argtypes = []
    lib.dlss5nr_gpu_name.restype = ctypes.c_char_p

    _lib = lib
    return lib


def _ensure_initialized(gpu_index: int):
    global _initialized_gpu
    lib = _load_library()
    if _initialized_gpu == gpu_index:
        return lib

    if _initialized_gpu is not None:
        lib.dlss5nr_shutdown()
        _initialized_gpu = None

    nr_dll = _RUNTIME / "nvngx_dlssnr.dll"
    shim = _RUNTIME / "caller" / "nvngx.dll_comfy.dll"
    if not shim.exists():
        shim = _RUNTIME / "caller" / "nvngx.dll"  # legacy fallback
    if not nr_dll.exists():
        raise DLSS5NRError(
            f"Missing {nr_dll}. Place your legally obtained nvngx_dlssnr.dll in the runtime folder."
        )
    if not shim.exists():
        raise DLSS5NRError(
            f"Missing caller shim {shim}. Normal users should install the prebuilt Windows release ZIP. "
            "Developers can run build_native.bat."
        )

    err = ctypes.create_string_buffer(4096)
    ok = lib.dlss5nr_init(gpu_index, str(_RUNTIME), err, len(err))
    if not ok:
        raise DLSS5NRError(_decode_error(err))
    _initialized_gpu = gpu_index
    return lib


def _style_to_int(style: str) -> int:
    named = {"default": 0, "natural": 1, "cinematic": 2}
    if style in named:
        return named[style]
    return int(style)


class DLSS5NeuralRendering:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "style": (["natural", "cinematic", "default", "3", "4", "5", "6"], {"default": "natural"}),
                "preset": ("INT", {"default": 3, "min": 0, "max": 3, "step": 1}),
                "intensity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "tone": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "structure": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "skin": ("FLOAT", {"default": -1.0, "min": -1.0, "max": 2.0, "step": 0.05}),
                "auto_mask": ("BOOLEAN", {"default": False}),
                "batch_mode": (["still images", "temporal sequence"], {"default": "still images"}),
                "gpu_index": ("INT", {"default": 0, "min": 0, "max": 15, "step": 1}),
                # Keep new widgets appended after existing ones so saved ComfyUI
                # workflows from v0.1.8 preserve positional widget values.
                "channel_order": (["auto", "RGBA", "BGRA"], {"default": "auto"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "process"
    CATEGORY = "experimental/DLSS 5 NR"
    DESCRIPTION = (
        "Unofficial experimental in-process DLSS 5 Neural Rendering (NGX feature 18). "
        "No external executable and no image files are written. Current build uses a CPU staging path."
    )

    def process(
        self,
        image,
        style="natural",
        preset=3,
        intensity=1.0,
        tone=1.0,
        structure=1.0,
        skin=-1.0,
        auto_mask=False,
        batch_mode="still images",
        channel_order="auto",
        gpu_index=0,
    ):
        if not isinstance(image, torch.Tensor) or image.ndim != 4:
            raise DLSS5NRError("Expected ComfyUI IMAGE tensor [B,H,W,C].")
        if image.shape[-1] < 3:
            raise DLSS5NRError("DLSS5 NR requires at least RGB input.")

        style_i = _style_to_int(style)
        is_sequence = batch_mode == "temporal sequence"

        # v0.1 intentionally uses CPU staging. This keeps the first native bridge
        # simple and robust while still remaining fully in-process.
        src = image[..., :3].detach().to(device="cpu", dtype=torch.float32).contiguous().numpy()
        out = np.empty_like(src, dtype=np.float32)

        with _lock:
            lib = _ensure_initialized(int(gpu_index))
            for i in range(src.shape[0]):
                frame_in = np.ascontiguousarray(src[i], dtype=np.float32)
                frame_out = np.empty_like(frame_in, dtype=np.float32)
                h, w, _ = frame_in.shape

                reset = 1 if (not is_sequence or i == 0) else 0
                err = ctypes.create_string_buffer(4096)
                ok = lib.dlss5nr_process(
                    frame_in.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                    frame_out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                    int(w), int(h),
                    int(style_i), int(preset),
                    ctypes.c_float(float(intensity)),
                    ctypes.c_float(float(tone)),
                    ctypes.c_float(float(structure)),
                    ctypes.c_float(float(skin)),
                    1 if auto_mask else 0,
                    int(reset),
                    err, len(err),
                )
                if not ok:
                    raise DLSS5NRError(f"Frame {i}: {_decode_error(err)}")

                # The leaked stock/reference runtime has been observed to expose
                # BGRA-like channel order, while some Ada-patched builds expose
                # ordinary RGBA. The native bridge deliberately returns raw RGB
                # slots; interpret them here.
                if channel_order == "RGBA":
                    corrected = frame_out
                elif channel_order == "BGRA":
                    corrected = frame_out[..., [2, 1, 0]]
                else:
                    # Automatic choice: DLSS NR may relight/reconstruct the image,
                    # but it should not globally swap red and blue. Pick the channel
                    # interpretation whose low-frequency colour statistics are closer
                    # to the source. Combining per-pixel MAE and mean-colour distance
                    # makes this robust without assuming a particular DLL build.
                    raw = frame_out
                    swapped = frame_out[..., [2, 1, 0]]
                    # Downsample by striding for cheap comparison on large images.
                    step_y = max(1, h // 128)
                    step_x = max(1, w // 128)
                    ref_s = frame_in[::step_y, ::step_x]
                    raw_s = raw[::step_y, ::step_x]
                    swp_s = swapped[::step_y, ::step_x]
                    raw_score = float(np.mean(np.abs(raw_s - ref_s))) + float(np.mean(np.abs(raw_s.mean(axis=(0,1)) - ref_s.mean(axis=(0,1)))))
                    swp_score = float(np.mean(np.abs(swp_s - ref_s))) + float(np.mean(np.abs(swp_s.mean(axis=(0,1)) - ref_s.mean(axis=(0,1)))))
                    corrected = raw if raw_score <= swp_score else swapped

                out[i] = corrected

        # Return to the same device/dtype convention ComfyUI supplied.
        result = torch.from_numpy(out).to(device=image.device, dtype=image.dtype)
        return (result.clamp_(0.0, 1.0),)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


class DLSS5NRRuntimeInfo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"gpu_index": ("INT", {"default": 0, "min": 0, "max": 15, "step": 1})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("info",)
    FUNCTION = "info"
    CATEGORY = "experimental/DLSS 5 NR"

    def info(self, gpu_index=0):
        with _lock:
            lib = _ensure_initialized(int(gpu_index))
            version = lib.dlss5nr_version()
            version_s = version.decode("utf-8", errors="replace") if version else "unknown"
            gpu = lib.dlss5nr_gpu_name()
            gpu_s = gpu.decode("utf-8", errors="replace") if gpu else "unknown"

        nr_dll = _RUNTIME / "nvngx_dlssnr.dll"
        nr_info = "missing"
        if nr_dll.exists():
            size_mib = nr_dll.stat().st_size / (1024 * 1024)
            nr_info = f"{size_mib:.1f} MiB\nSHA256: {_sha256_file(nr_dll)}"

        return (
            f"ComfyUI-DLSS5-NR: {__version__}\n"
            f"Bridge: {version_s}\n"
            f"GPU: {gpu_s}\n"
            f"GPU index: {gpu_index}\n"
            f"Runtime dir: {_RUNTIME}\n"
            f"nvngx_dlssnr.dll: {nr_info}",
        )


NODE_CLASS_MAPPINGS = {
    "DLSS5NeuralRendering": DLSS5NeuralRendering,
    "DLSS5NRRuntimeInfo": DLSS5NRRuntimeInfo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DLSS5NeuralRendering": "DLSS 5 Neural Rendering (Unofficial)",
    "DLSS5NRRuntimeInfo": "DLSS 5 NR Runtime Info",
}
