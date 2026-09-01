# Publishing guide

## 1. Create the GitHub repository

Suggested repository name:

```text
ComfyUI-DLSS5-NR
```

Push the contents of this repository root. Do not add any NVIDIA DLLs.

## 2. Verify CI

The workflow `.github/workflows/ci.yml` runs on Windows and validates:

- Python syntax;
- absence of NVIDIA proprietary runtime DLLs in the repository;
- native MSVC build of `dlss5nr_bridge.dll` and `nvngx.dll_comfy.dll`.

Before the first release, ensure the CI job is green.

## 3. Create the first release

Update versions if needed, commit, then tag:

```bash
git tag v0.2.0
git push origin v0.2.0
```

`.github/workflows/release.yml` will build on `windows-latest` and create:

```text
ComfyUI-DLSS5-NR-v0.2.0-windows-x64.zip
ComfyUI-DLSS5-NR-v0.2.0-windows-x64.zip.sha256
```

The ZIP contains the project-owned prebuilt native bridge and caller helper, so end users do not need Visual Studio.

## 4. What must never be in the release

The release packaging script fails if it sees any of:

```text
_nvngx.dll
nvngx_dlssnr.dll
nvngx_dlss.dll
```

Users provide `runtime/nvngx_dlssnr.dll` themselves. `_nvngx.dll` is discovered from the installed NVIDIA driver when possible.

## 5. Comfy Registry / Manager later

The Comfy Registry powers discovery/install through ComfyUI-Manager and expects `pyproject.toml` metadata including a globally unique node name and PublisherId.

A starter file is provided as `pyproject.toml.example`. Before using it:

1. create a Publisher in the Comfy Registry;
2. choose the immutable registry node ID;
3. fill in your GitHub repository URL and PublisherId;
4. decide how the prebuilt Windows DLLs will be included in the registry package;
5. review the registry's legal/security standards and the project's `LEGAL_NOTES.md`.

Because this node loads native code and relies on undocumented NVIDIA runtime behavior, GitHub Releases are the recommended initial distribution channel.
