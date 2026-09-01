# Contributing

Contributions are welcome for the project-owned Python/C++ bridge and packaging code.

Please do not submit:

- NVIDIA proprietary DLLs or SDK headers;
- leaked/modified NVIDIA binaries;
- links whose only purpose is redistributing those binaries.

For native changes, make sure the Windows CI build passes. Keep node class IDs stable when possible so existing ComfyUI workflows remain loadable.
