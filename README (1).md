# Meshtastic T-Deck Offline Map Tile Builder

This project provides a **cross-platform GUI + CLI tool** for generating **offline raster map tiles** for the **LILYGO T-Deck (ESP32)** running **Meshtastic**.

The goal is to make it easy to:
- Select a geographic area visually
- Estimate tile count before downloading
- Download only the tiles you actually need
- Deploy them directly to an SD card in a layout Meshtastic understands

This avoids relying on online map access in the field and prevents accidental over-downloads that exceed SD card or device limits.

---

## Why This Exists

Meshtastic supports **offline map tiles**, but:
- There is no official desktop tool to generate them
- Tile math (zoom levels × area) is easy to get wrong
- Downloading too many tiles can overwhelm storage or bandwidth
- Manual workflows are error-prone

This tool provides:
- A **visual AOI selector**
- **Live tile count estimation**
- Guardrails on maximum tile counts
- A stable, repeatable workflow

---

## Features

- Web-based GUI (Leaflet)
- Search by **city name or ZIP code**
- Radius-based Area of Interest (AOI)
- Adjustable **min / max zoom levels**
- **Live tile count preview**
- Automatic tile download after AOI confirmation
- Correct SD-card directory layout for Meshtastic
- Cross-platform (Windows, macOS, Linux)

---

## Map Source

Currently supported:
- **OpenTopoMap**  
  https://opentopomap.org

Tile source:
```
https://a.tile.opentopomap.org/{z}/{x}/{y}.png
```

(Additional map sources can be added easily.)

---

## Requirements

Python 3.9+ recommended.

Python dependencies:
```bash
pip install flask requests mercantile tqdm
```

---

## Usage

### Launch the GUI

```bash
python fetch_map_tiles.py --gui
```

Optional debug output:
```bash
python fetch_map_tiles.py --gui --debug
```

### Workflow

1. GUI opens in your browser
2. Search for a city or ZIP code
3. Adjust radius and zoom levels
4. Review live tile count
5. Click **Use AOI**
6. Tiles download automatically

---

## Output Structure

Tiles are written in the format expected by Meshtastic:

```
sdcard/
  map/
    tiles/
      z/
        x/
          y.png
```

Copy the `sdcard/` directory directly onto the T-Deck SD card.

---

## Practical Tile Count Guidance

- **< 3,000 tiles** — ideal
- **3,000–6,000 tiles** — reasonable
- **> 10,000 tiles** — possible but usually unnecessary

The tool enforces a configurable maximum to prevent accidental overload.

---

## Status

- ✔️ Functional
- ✔️ Stable
- ✔️ Field-tested for offline map loading on T-Deck
- 🚧 CLI-only mode intentionally limited for now

---

## Notes

- This tool runs a **local Flask development server** for the GUI.
- It is not intended to be exposed to the network.
- Browser auto-launch may fail on some systems; the URL will be printed if so.

---

## License

This project is provided as-is.  
Check OpenTopoMap’s tile usage policy before large-scale redistribution.

---

## Acknowledgments

- Meshtastic project
- LILYGO T-Deck hardware
- OpenStreetMap contributors
- OpenTopoMap
