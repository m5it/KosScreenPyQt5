# KosScreenPyQt5

A small, friendly desktop screenshot utility written in Python and PyQt5.

## What it does

- **Capture the whole primary screen** in one click.
- **Select a region** of the screen and instantly create a new cropped image from it.
- **Save** the captured image to PNG, JPG or BMP.
- **Copy** the image to the clipboard.

## Setup

```bash
# create a virtual environment
python3 -m venv venv

# activate it
source venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

## Run

```bash
source venv/bin/activate
python main.py
```

## How to use

1. Click **Capture full screen** to grab everything.
2. Or click **Capture selection** to draw a rectangle on the screen.
   - `Enter` / click = capture the selected area.
   - `Esc` / right-click = cancel.
3. Use the **Hide window on capture** checkbox to control whether the main window hides itself while taking a screenshot.
3. Use **Save image** or `Ctrl+S` to save the image.
4. Use **Copy to clipboard** or `Ctrl+C` to copy it.

## Shortcuts

| Shortcut        | Action              |
|-----------------|---------------------|
| Ctrl+Shift+F    | Capture full screen |
| Ctrl+Shift+S    | Capture selection   |
| Ctrl+S          | Save image          |
| Ctrl+C          | Copy to clipboard   |
| Ctrl+Q          | Quit                |

## Requirements

- Python 3
- PyQt5 >= 5.15.0
