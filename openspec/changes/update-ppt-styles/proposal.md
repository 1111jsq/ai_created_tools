# Change: Update PPT Styles

## Why
The user requested support for multiple visual styles (themes) to make the presentations more attractive and varied.

## What Changes
- Added `ThemeStyle` model to support configurable colors and fonts.
- Updated `PPTRenderer` to support 'tech', 'light', and 'retro' themes.
- Updated CLI to accept `--style` argument.

## Impact
- Affected specs: `ppt-generator`
- Affected code: `PPT/src/models.py`, `PPT/src/ppt_renderer.py`, `PPT/src/main.py`

