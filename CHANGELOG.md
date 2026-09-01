# Changelog

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
