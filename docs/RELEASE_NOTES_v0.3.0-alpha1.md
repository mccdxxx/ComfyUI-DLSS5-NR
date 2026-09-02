# v0.3.0-alpha1

Experimental temporal-consistency build.

## What changed

The normal `temporal sequence` mode now creates and binds an explicit full-resolution `R16G16_FLOAT` motion-vector texture containing only `(0, 0)` vectors. This is intended to test static input where every pixel should reproject to the same location in the previous frame.

A third mode, `temporal sequence (legacy no MV)`, keeps the v0.2.0 behavior for side-by-side testing.

## Recommended validation

Create a 20-30 frame IMAGE batch by repeating one identical frame. Run the same batch with:

1. `still images`
2. `temporal sequence`
3. `temporal sequence (legacy no MV)`

Do not use a moving clip as the first alpha1 test. Zero vectors are intentionally wrong for moving content. Real optical flow is planned only after this experiment tells us whether an explicit MV resource fixes the static-history flicker.

## Expected interpretation

- New temporal stable + legacy flickers: missing MV contract was likely the primary problem.
- Both temporal modes flicker: investigate other temporal inputs/state before adding optical flow.
- New temporal errors at Create/Evaluate: the supplied runtime may expect a different MV contract; report the full NGX error and runtime info.
