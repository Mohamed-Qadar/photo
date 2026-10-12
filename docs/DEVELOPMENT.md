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

## Phase 6 — localization, recovery and performance

English/Somali display strings use an offline catalogue and live widget translation.
Settings retain the language and theme. Switching language preserves the document,
selection, user text and undo history; translated combo labels resolve to stable
model keys. Qt standard buttons use the catalogue translator. Recent saved projects
are available from the home screen.

Autosave writes an isolated editable recovery project every 30 seconds when dirty,
on a worker. Recovery discovery offers interrupted projects without overwriting
the user's original file. Normal save/discard/close removes this instance's recovery
files. Autosave skips active mouse gestures; switching documents invalidates pending
writes. Native project replacement is atomic, with regression coverage for failure.

UI previews are limited to 1600 pixels on the longest side and remain positioned
in document coordinates. Export stays full resolution. Row-tiled alpha compositing
reduces float intermediates and fixes multiply blending over transparency. Large
filters/transforms and print-sheet creation use guarded background jobs. File open,
save and export use worker-backed modal progress while the UI event loop continues.
Images/canvases above 40 megapixels are rejected before allocation; EXIF orientation
is honored. Older project manifests default missing transform fields to identity.

Runtime, installer and package metadata use version 1.2.0. The Phase 1 report is
historical. The source tree has progressed beyond that initial delivery. Autosave
and the interactive object canvas are subsequent phases, not baseline capabilities.

## Phase 7 — visible workflows and Windows packaging

The final local suite passes all 117 tests. The eight canvas interaction tests also
pass with 200% display scaling. Real Qt mouse events exercise object movement and
layer reordering; visible window workflows cover property edits, save/reopen,
PNG/JPG export, language switching and cancellation of a save during close.
PNG/JPG exports preserve document DPI, and text placement accounts for font bearings.

The source entry point passes the expanded GUI smoke workflow. English editor and
Somali home screenshots are checked in under `docs/screenshots`. The smoke runner
is included in the application package and can be invoked with `--smoke-test`.
Windows CI now runs it against both source and the actual PyInstaller executable
before building the installer, and uploads screenshots/results as `PhotoStudio-QA`.
The installer and SHA-256 checksum remain available as `PhotoStudio-Setup`.

Version stays 1.2.0 in active development. These are test artifacts; this work does
not create a version tag or publish a release. Remaining product boundaries are
documented in README.md, including approximate portrait effects, the 40-megapixel
allocation limit, and future masks/adjustment layers/batch editing.

## Offline watermark license

This update is limited to export attribution, manual payment instructions and a
perpetual one-computer watermark-removal license. All editing tools remain free.
Export rendering and its visible preview share verified license policy; project
content and editor rendering remain unchanged. Signed activation is verified with
Ed25519 entirely offline and persisted atomically. The private signing credential
is outside the checkout; only its public verification key is bundled. A separate
developer CLI issues keys after payment verification and keeps issuance records
outside the repository. See LICENSING.md for commands and practical offline limits.

Local validation: 134 tests pass, including 17 licensing/watermark tests. Those 17
also pass at 200% display scaling. The source GUI smoke workflow passes with the
payment dialog, invalid-signature check, visible export preview and free export
watermark. Windows CI runs this same smoke workflow against the packaged app.

## Forty new editable templates

The original 22 catalogue entries retain their keys, names, dimensions and layer
data unchanged; a baseline SHA-256 regression check protects the original content.
Exactly 40 additions bring the total to 62 across 11 categories: 6 sports, 7
business/marketing, 5 Ramadan/holidays, 5 celebrations, 5 education/books, 5
announcements/civic information and 7 digital designs. Each has its own layout,
editable text/shapes and at least one replaceable image slot. All images are original
geometric illustrations generated locally; no external asset, photo or font service
is required. Bundled code/data stays small; documentation preview PNGs are not
included in the application package. Book/certificate designs retain print DPI.

The gallery streams bounded thumbnails, prioritizes the selected design, supports
category/search filtering and shows a large proportional preview. Custom cards wrap
long names; the explicit Use Template button remains visible. Closing stops pending
work. Double-click text edits it; a single photo click opens the local picker, while
dragging keeps normal transform behavior. Replacement center-crops to the frame and
preserves size, position and rotation. Background clicks open solid/gradient controls.
Object context menus add Edit, Replace Image, Bring Forward, Send Backward and
Lock/Unlock alongside existing duplicate/delete/group actions. Changes remain undoable.

All 40 designs have individual previews and seven labeled contact sheets under
`docs/template-previews`; the renderings were visually inspected and overlapping
image frames corrected. Example prices, dates and contact details are customizable.
Election information is neutral and explicitly requires verified official details.

Validation: 178 automated tests pass. Every addition is edited, has its image replaced,
colors changed and objects moved/resized/rotated, then saved/reopened and exported.
The ten canvas/browser interaction tests also pass at 200% scaling. The expanded
source smoke workflow passes and runs against the actual executable in Windows CI;
CI uploads all 40 previews with its QA screenshots. Export watermark/offline licensing
remains unchanged and its 17 regression tests are part of the full suite. Version
remains 1.2.0 in development; no release or tag is created for this update.
