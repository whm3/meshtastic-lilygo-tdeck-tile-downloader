#!/usr/bin/env python3

import argparse
import os
import sys
import time
import threading
import requests
import mercantile
from tqdm import tqdm

# =========================
# ARGUMENTS
# =========================

parser = argparse.ArgumentParser(
    description="Fetch OpenTopoMap tiles for Meshtastic T-Deck"
)

parser.add_argument("--gui", action="store_true", help="Launch GUI")
parser.add_argument("--debug", action="store_true", help="Verbose debug output")
parser.add_argument("--output", default=os.path.join("sdcard", "map", "tiles"))
parser.add_argument("--delay", type=float, default=0.2)
parser.add_argument("--max-tiles", type=int, default=5000)

args = parser.parse_args()

def log(msg):
    if args.debug:
        print(f"[DEBUG] {msg}")

# =========================
# GUI
# =========================

def launch_gui():
    from flask import Flask, request, jsonify, render_template_string
    import webbrowser

    app = Flask(__name__)
    selection = {}
    done_event = threading.Event()

    HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>T-Deck Tile Builder</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>

<style>
body { margin:0; }
#map { height:100vh; }

/* Search panel */
#search-panel {
  position:absolute;
  top:10px;
  left:10px;
  background:white;
  padding:10px;
  z-index:1000;
  font-family:sans-serif;
  width:260px;
}

/* Zoom panel */
#zoom-panel {
  position:absolute;
  bottom:10px;
  left:10px;
  background:white;
  padding:10px;
  z-index:1000;
  font-family:sans-serif;
  width:260px;
}

#count { font-weight:bold; }
</style>
</head>

<body>

<div id="search-panel">
  <input id="search" placeholder="City or ZIP" style="width:100%"><br><br>

  <label>Radius (km)</label><br>
  <input id="radius" type="number" value="10" style="width:100%"><br><br>

  <button onclick="applySearch()">Search</button>
  <button id="useBtn" onclick="submitAOI()">Use AOI</button>
</div>

<div id="zoom-panel">
  <label>Min Zoom</label><br>
  <input id="zmin" type="number" value="12" style="width:100%"><br><br>

  <label>Max Zoom</label><br>
  <input id="zmax" type="number" value="14" style="width:100%"><br><br>

  <div>Tiles: <span id="count">—</span></div>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<script>
const map = L.map('map', { zoomControl: false })
  .setView([40.5, -75.1], 12);

L.control.zoom({ position: 'bottomright' }).addTo(map);

L.tileLayer(
  'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
  { maxZoom: 17 }
).addTo(map);

let circle = null;

function applySearch() {
  const q = document.getElementById("search").value;
  const r = parseFloat(document.getElementById("radius").value) * 1000;

  fetch("/geocode?q=" + encodeURIComponent(q))
    .then(r => r.json())
    .then(p => {
      map.setView([p.lat, p.lon], 12);
      if (circle) map.removeLayer(circle);
      circle = L.circle([p.lat, p.lon], { radius: r }).addTo(map);
      updateCount();
    });
}

function updateCount() {
  if (!circle) return;
  const b = circle.getBounds();

  fetch("/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      bbox: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()],
      zmin: parseInt(document.getElementById("zmin").value),
      zmax: parseInt(document.getElementById("zmax").value)
    })
  })
  .then(r => r.json())
  .then(d => {
    document.getElementById("count").innerText = d.total;
  });
}

["radius", "zmin", "zmax"].forEach(id =>
  document.getElementById(id).addEventListener("change", updateCount)
);

function submitAOI() {
  if (!circle) {
    alert("Search first.");
    return;
  }

  document.getElementById("useBtn").disabled = true;
  const b = circle.getBounds();

  fetch("/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      bbox: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()],
      zoom_min: document.getElementById("zmin").value,
      zoom_max: document.getElementById("zmax").value
    })
  }).then(() => {
    alert("AOI submitted. Download starting.");
    window.close();
  });
}
</script>

</body>
</html>
"""

    @app.route("/")
    def index():
        return render_template_string(HTML)

    @app.route("/geocode")
    def geocode():
        q = request.args.get("q")
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1},
            headers={"User-Agent": "tdeck-tiles"}
        ).json()
        return jsonify({"lat": float(r[0]["lat"]), "lon": float(r[0]["lon"])})

    @app.route("/estimate", methods=["POST"])
    def estimate():
        data = request.json
        tiles = set()
        for z in range(data["zmin"], data["zmax"] + 1):
            for t in mercantile.tiles(*data["bbox"], z):
                tiles.add((t.z, t.x, t.y))
        return jsonify({"total": len(tiles)})

    @app.route("/submit", methods=["POST"])
    def submit():
        nonlocal selection
        selection = request.json
        log("AOI received")
        done_event.set()
        return jsonify({"ok": True})

    def run_server():
        log("Starting Flask at http://127.0.0.1:5000")
        app.run(debug=False, use_reloader=False)

    threading.Thread(target=run_server, daemon=True).start()

    url = "http://127.0.0.1:5000"
    try:
        webbrowser.open(url)
    except Exception:
        print(f"Open manually: {url}")

    log("Waiting for AOI...")
    done_event.wait()
    log("GUI done")

    return selection

# =========================
# DOWNLOAD
# =========================

def download_tiles(bbox, zmin, zmax):
    tiles = set()
    for z in range(zmin, zmax + 1):
        for t in mercantile.tiles(*bbox, z):
            tiles.add((t.z, t.x, t.y))

    print(f"\nTOTAL tiles: {len(tiles)}")

    if len(tiles) > args.max_tiles:
        print("❌ Too many tiles, aborting.")
        sys.exit(1)

    for z, x, y in tqdm(sorted(tiles)):
        path = os.path.join(args.output, str(z), str(x))
        os.makedirs(path, exist_ok=True)
        fn = os.path.join(path, f"{y}.png")

        if not os.path.exists(fn):
            r = requests.get(
                f"https://a.tile.opentopomap.org/{z}/{x}/{y}.png"
            )
            if r.status_code == 200:
                with open(fn, "wb") as f:
                    f.write(r.content)

        time.sleep(args.delay)

    print("\n✅ Tiles downloaded.")

# =========================
# MAIN
# =========================

if not args.gui:
    print("Use --gui")
    sys.exit(1)

log("Launching GUI")
sel = launch_gui()

download_tiles(
    sel["bbox"],
    int(sel["zoom_min"]),
    int(sel["zoom_max"])
)
