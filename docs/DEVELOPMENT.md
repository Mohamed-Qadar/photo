# PhotoStudio 1.2.0 development

## Phase 1 — baseline corrections

The crop press handler cleared its origin after setting it. Clearing now happens
before recording the origin, with a real mouse-gesture regression test. Raster
crop also converts canvas coordinates into the active layer's coordinates.

Editing intents now refuse locked layers; group movement refuses groups containing
a locked member. Raster transforms ignore editable objects instead of crashing.
History callbacks mark visibility and lock changes dirty as well as controller edits.

Replacing or closing a modified document offers Save / Discard / Cancel. Cancelled
save dialogs and failed saves keep the current document. The title shows changes.

Rendering runs in a bounded worker queue on isolated metadata snapshots. Pixel
buffers can be shared because commands replace them instead of mutating them.
Only the latest render reaches the UI. Large filters use background processing;
results are discarded if the document changed while processing. Workers never
create or mutate widgets. Export retains full resolution.

Text content, font size, alignment and colour now have visible properties controls.
A canvas snapping action exposes the existing geometry helper.

Runtime, installer and package metadata use version 1.2.0. The Phase 1 report is
historical. The source tree has progressed beyond that initial delivery. Autosave
and the interactive object canvas are subsequent phases, not baseline capabilities.
