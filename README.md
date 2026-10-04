# Greenscreen Photo Remover

Remove the green-screen background from your photos — fast and easy, with a live preview.

> **Download:** grab the latest `GreenScreenRemover.exe` from the [Releases](https://github.com/eazyfixgr/greenscreen-photo-remover/releases) page. No installation required.

## Features

- Load a photo and remove the green screen
- Adjustable colour tolerance for precise edges
- Live preview before saving
- Export to transparent PNG
- Built with Python, Pillow and tkinter

## Getting started (run from source)

```bash
python -m pip install -r requirements.txt
python remove_greenscreen.py
```

## Build a standalone EXE

```bash
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name GreenScreenRemover remove_greenscreen.py
```

The executable is created in `dist/GreenScreenRemover.exe`.

## License

Released under the [MIT License](LICENSE).

---

# Greenscreen Photo Remover (Ελληνικά)

Αφαίρεση του πράσινου φόντου (greenscreen) από φωτογραφίες, με ζωντανή προεπισκόπηση.

> **Λήψη:** κατεβάστε το `GreenScreenRemover.exe` από τη σελίδα [Releases](https://github.com/eazyfixgr/greenscreen-photo-remover/releases).

## Δυνατότητες

- Φόρτωση φωτογραφίας και αφαίρεση του πράσινου φόντου
- Ρύθμιση ανοχής χρώματος για καθαρές άκρες
- Ζωντανή προεπισκόπηση
- Εξαγωγή σε διαφανές PNG
