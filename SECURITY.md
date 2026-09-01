# Security policy

This project loads native D3D12/NVIDIA runtime code inside the ComfyUI process. A crash in the native bridge, display driver, NGX core, or user-supplied Neural Rendering runtime may terminate ComfyUI.

## Reporting

Please report reproducible bridge crashes through a private GitHub security advisory if the issue appears exploitable. For ordinary compatibility failures, use GitHub Issues and include:

- ComfyUI version;
- Windows version;
- GPU model;
- NVIDIA driver version;
- `DLSS 5 NR Runtime Info` output;
- full traceback/console log.

Do not upload or attach proprietary NVIDIA DLLs to issues.
