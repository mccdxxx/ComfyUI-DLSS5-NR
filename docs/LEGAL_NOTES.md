# Legal notes for maintainers

This is not legal advice. It is a release checklist for the parts of this experimental integration that deserve explicit review before broad distribution.

## Low-risk project-owned material

The following are authored for this project and can be distributed under the repository's MIT license:

- ComfyUI Python node code;
- D3D12 resource/staging code;
- build and packaging scripts;
- the thin caller-forwarding helper source/binary, subject to the caveat below.

## NVIDIA material that must not be bundled by this repository

Keep these out of git history and GitHub release assets unless you have explicit rights to redistribute the exact material:

- `_nvngx.dll`;
- `nvngx_dlssnr.dll`;
- other NVIDIA `nvngx_*` runtime binaries;
- NVIDIA NGX/DLSS SDK headers.

CI includes a filename check to reduce accidental bundling.

## Undocumented identifiers and caller validation

The current integration relies on observed, undocumented runtime behavior, including:

- NGX feature id 18;
- Neural Rendering parameter names;
- observed application/project identifiers used during NGX initialization;
- a thin helper DLL whose call frame/module name satisfies the observed Neural Rendering caller check.

These facts are technically necessary for the experimental runtime path, but they may be governed by license/contract restrictions associated with the NVIDIA software being used. Treat this as the main legal-review item before promoting the project as a production integration or submitting it to a curated registry.

The repository should describe the feature as **unofficial/experimental**, avoid implying NVIDIA endorsement, and avoid links to leaked or modified NVIDIA binaries.

## Reference repository licensing

`Zonnery/dlss5-nr-player` is cited as a research/reference source. At the time v0.2.0 was prepared, no explicit open-source LICENSE file was visible in that repository root. Do not copy/vend its source code without permission or a clear license grant.

## Recommended release posture

1. Publish source + project-owned prebuilt bridge/helper only.
2. Require users to supply their own compatible NVIDIA runtime.
3. Start with GitHub Releases, clearly marked experimental.
4. Obtain independent legal review before commercial distribution or broader registry publication if the project becomes significant.
