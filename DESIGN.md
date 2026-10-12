# Animatrix interface redesign

The current editor hides its live preview below a long list of nested profile and element forms. Selecting, naming, enabling, editing, and reordering designs compete in the same card. Changes immediately affect the active lid display.

## Proposed interface

- A design library on the left: one selected design, named thumbnails, add/import actions.
- A large, always visible preview in the center using the real detected LED coordinates and physical panel proportions. Playback controls operate on the preview.
- A compact inspector on the right: brightness, speed, placement. Advanced element settings stay accessible in collapsible sections.
- Explicit Apply to laptop distinguishes previewing a draft from changing the active design. Clearly identify the design currently on the laptop.
- Separate device settings (lid, battery, sleep, startup) from artwork controls.
- Preserve existing profiles, file paths, power policies, CLI actions, and tray controls.

## Simple first, advanced when needed

The default workflow is choose a design, inspect the live preview, optionally adjust brightness or speed, then apply. Importing an image uses a sensible fit automatically. Do not require users to understand elements, timing, offsets, or the transport canvas to start.

Keep advanced controls in expandable groups within the same inspector, rather than a separate basic/expert mode:

- **Layers:** add image, text, clock, or battery elements; reorder, duplicate, and configure each element.
- **Motion and timing:** loop or bounce, frame rate, sequential playback, duration, cycles, and fades.
- **Placement and appearance:** scale, rotation, offsets, tilt compensation, contrast, black level, and overlays.

Device settings provide startup, sleep, lid and battery behavior with sensible defaults. Automatic profile switching and return delays are an optional expandable group there.

Show only controls applicable to the selected content. Explain unfamiliar settings beside the control. Keep the preview visible while editing, offer Reset for each group, and remember which groups the user opens.

Collapsed groups must not disable or reset advanced values. Preserve and summarize existing configurations, including designs imported from the old app. Expand the same controls for precise edits; never silently flatten a multi-element design to match the simple screen.

## Implementation sequence

1. Extract the LED drawing into a reusable preview component, independent of the hardware engine. Add a preview-only controller that reuses existing renderers and animation decoding.
2. Keep a selected draft profile separate from the active persisted profile. Apply validates and saves the draft, selects it, and refreshes the hardware engine. Revert restores the saved draft.
3. Replace the scrolling profile accordion with library selection and one selected-profile inspector. Retain existing element controls initially, grouping advanced settings.
4. Add native file import and thumbnails using the same rendering pipeline and detected geometry.
5. Make the large preview responsive, with accessible keyboard selection, labels, and state indicators.

## Verification

- Preview selection and changes produce zero hardware writes before Apply.
- Apply updates only the selected design and preserves unrelated policies and profiles.
- Existing profile files load and save without lost fields.
- The preview and applied design share the same frame rendering and LED mapping.
- Verify empty libraries, missing artwork, invalid elements, sleep/resume, and external CLI profile changes.

## Fork status

Upstream: https://github.com/crt0512/animatrix (declares MIT in README.md and Cargo.toml).
Local working branch: ui-redesign.
Hosted fork: https://github.com/Thijs5/animatrix.
Local checkout: /home/thijs/Shared/Projects/animatrix.
The mockups are proposals; the native editor has not been changed yet.
