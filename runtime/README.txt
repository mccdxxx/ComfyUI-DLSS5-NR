DLSS 5 NR runtime directory
===========================

Normal users must provide their own compatible NVIDIA Neural Rendering runtime:

    runtime\nvngx_dlssnr.dll

This project does NOT ship NVIDIA proprietary DLLs.

_nvngx.dll is normally discovered automatically from the installed NVIDIA driver
DriverStore. You may place a matching copy at runtime\_nvngx.dll only as an
explicit local override.

The project-owned caller helper is shipped in release ZIPs as:

    runtime\caller\nvngx.dll_comfy.dll
