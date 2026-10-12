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

## Phase 2 — interactive canvas

The canvas now supports click and Shift selection, marquee selection, grouped or
multi-object movement, eight resize handles, rotation handles, arrow movement,
Space-drag panning, visible boundaries and cursor feedback. Shift constrains aspect
ratio or rotation to 15-degree steps. Canvas/object snapping uses a screen-space
tolerance and displays guides. Escape restores a cancelled gesture. Each completed
gesture is one undo step. Locked objects cannot be manipulated from the canvas.

Scale and clockwise rotation are persisted as optional layer fields. Old manifests
default to identity transforms. Raster source pixels and object specs stay editable.
Rotation and export use the same rendering path. Selection is shared by canvas,
controller and layer list; duplicate/delete support multiple selected objects.

## Phase 3 — layers and properties

Layers now show bounded background-generated thumbnails, editable names, visibility,
lock state in tooltips, opacity, shared multi-selection and context menus. Internal
drag ordering respects locked dragged objects. Reorder and rename are undoable.
Selection refresh preserves selected objects rather than rebuilding on every click.

Properties expose position, size, rotation, font family, bold, alignment, colour,
outline and shadow, plus shape type/fill/stroke/gradient and alignment actions. The
properties dock scrolls on smaller screens. System fonts resolve offline; the
renderer stays independent of Qt. Unicode Somali text and styled object specs
remain editable after project save and match full-resolution PNG exports.

## Phase 4 — design workflows

The editor has a left tools bar and top project controls, visible snapping,
canvas context actions, image-layer import/replacement and background colour
settings. Replacement retains the existing object's displayed dimensions and is
undoable. Gradient template backgrounds can be changed without adding an invisible
layer behind them. A searchable gallery renders previews in a background worker.

The baseline catalogue actually contained 21 designs despite documenting 22. An
original editable Somali phone-shop design brings the catalogue to 22. Bounded
preview compositing preserves source pixels and text specs. Property undo now
removes formerly absent spec fields instead of leaving invalid null values.

## Phase 5 — portrait and physical print workflows

Portrait properties expose effect strength and spot radius. Before-session compare
uses an isolated opening-state snapshot, so it includes raster beauty edits and
geometry changes rather than only switching off tone sliders. The canvas prevents
editing while displaying this comparison. Approximate portrait blur remains clearly
labelled and does not use or claim an AI segmentation model.

Passport layouts accept custom millimetre dimensions, DPI and copy counts, show
sheet capacity and reject impossible layouts. Standard 300-DPI sheets are prepared
on a worker; stale results cannot replace a document edited during preparation.
Physical dimensions remain correct in PDF export. Example-size disclaimers remain
visible. Generated sheets are marked unsaved until the user saves them.

Runtime, installer and package metadata use version 1.2.0. The Phase 1 report is
historical. The source tree has progressed beyond that initial delivery. Autosave
and the interactive object canvas are subsequent phases, not baseline capabilities.
