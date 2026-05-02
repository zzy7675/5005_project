# Oceanus Folk: Then-and-Now — VAST Challenge MC1

Interactive visual analytics dashboard tracing **Sailor Shift's** rise to stardom and the influence of **Oceanus Folk** on the global music world, built for MSBD5005 Data Visualization (HKUST, Spring 2026).

---

## Project Overview

A local journalist — **Silas Reed** — is writing a piece titled *"Oceanus Folk: Then-and-Now"*. This project helps him explore a knowledge graph of 17,412 musical artists, songs, albums, and their relationships to answer three core questions:

1. Who has Sailor Shift been most **influenced by** over time?
2. Who has she **collaborated with** and directly or indirectly **influenced**?
3. How has she influenced collaborators of the broader **Oceanus Folk community**?

---

## Requirements

| Requirement | Version |
|---|---|
| **Python** | **3.10** (required) |
| networkx | 3.3 |
| pandas | 2.2.2 |
| numpy | 1.26.4 |
| matplotlib | 3.9.0 |

> The D3.js dashboard (`output/index.html`) runs entirely in the browser — no additional JavaScript packages need to be installed.

---

## Setup with venv

### 1 — Create a virtual environment (Python 3.10)

**Windows** (using the `py` launcher):
```bash
py -3.10 -m venv .venv
```

**macOS / Linux**:
```bash
python3.10 -m venv .venv
```

### 2 — Activate the virtual environment

**Windows (Command Prompt)**:
```cmd
.venv\Scripts\activate
```

**Windows (PowerShell)**:
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**:
```bash
source .venv/bin/activate
```

You should see `(.venv)` at the start of your prompt.

### 3 — Install pinned dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Preprocessor

Make sure you are in the **project root** (the folder containing `MC1_graph.json`) and your venv is activated.

### Option A — Standalone script (recommended)

```bash
python run_preprocess.py
```

This runs all 7 processing steps and writes every output file to `output/`. It takes ~1–3 minutes depending on your machine.

Expected console output:
```
Step 1: Loading graph...
  Nodes: 17,412  Edges: 37,857  Components: 18
Step 2: Building DataFrames...
Step 3: Building Sailor Shift ego network...
Step 4: Temporal analysis...
Step 5: Building influence network...
Step 6: Oceanus Folk community analysis...
Step 7: Exporting D3.js data...
============================================================
PREPROCESSING COMPLETE
============================================================
```

### Option B — Jupyter Notebook

```bash
pip install jupyter          # only needed once
jupyter notebook main_preprocess.ipynb
```

Run all cells top-to-bottom (Cell 0 → Cell 7). Each cell produces inline matplotlib plots **and** saves the corresponding output files.

---

## Viewing the Dashboard

The dashboard is a static HTML file that loads JSON data via `fetch()`. Browsers block local `fetch()` calls when a file is opened directly (`file:///...`), so you must serve it over HTTP.

### Start a local HTTP server

From the **project root** (with venv active):

```bash
python -m http.server 8080
```

> `http.server` is part of Python's standard library — no installation needed.  
> This command starts a file server on port 8080 serving the current directory.

### Open the dashboard

Open your browser and navigate to:

```
http://localhost:8080/output/
```

Press `Ctrl+C` in the terminal to stop the server when done.

### Alternative — VS Code Live Server

If you use VS Code, install the **Live Server** extension, then right-click `output/index.html` → **"Open with Live Server"**. No terminal needed.

---

## Dashboard Guide

The dashboard has four interactive panels:

### Top — Global Control Panel
| Control | Function |
|---|---|
| **Decade range slider** | Filter all views to a time window |
| **Node type toggles** | Show/hide Person, Song, Album, RecordLabel, MusicalGroup |
| **Edge type toggles** | Show/hide any of the 12 edge types |
| **Genre dropdown** | Filter to a specific music genre |
| **Notable only** | Show only chart-topping works |
| **Ego Net / Influence Net** | Switch the main graph between Sailor's ego network and the 2-hop influence network |

### Left — Force-Directed Network Graph
| Interaction | Action |
|---|---|
| Scroll | Zoom in/out |
| Drag background | Pan |
| Click a node | Highlight all its direct connections |
| Shift + drag | Box-select a subgraph |
| Double-click a node | Open detail panel (name, type, genre, year, notable) |

### Top-Right — Temporal Evolution View
Three stacked bar charts showing per-decade trends:
1. **Works count** — Other genres / Oceanus Folk / Sailor's works
2. **Notable ratio** — % of chart-topping works (All / Oceanus Folk / Sailor)
3. **Genre distribution** — Top 6 genres stacked

Click any decade bar to filter the network graph to that era.

### Bottom-Right — Detailed Linkage View
Directed Sankey-style diagram for a selected node showing:
- **Upstream** — creators (Person, MusicalGroup) connected via PerformerOf / ComposerOf / LyricistOf
- **Downstream** — record labels connected via RecordedBy / DistributedBy
- **Influence sources** — works connected via InStyleOf / InterpolatesFrom / CoverOf / LyricalReferenceTo / DirectlySamples

Click any node in the main graph to populate this view.

---

## Output Files

All files are written to `output/` after running the preprocessor.

| File | Type | Description |
|---|---|---|
| `graph_validation_report.md` | Markdown | Graph statistics summary |
| `nodes_df.csv` | CSV | All 17,412 nodes with attributes |
| `edges_df.csv` | CSV | All 37,857 edges with attributes |
| `sailor_ego_network.json` | JSON | Ego network centred on Sailor Shift |
| `sailor_collaborators.csv` | CSV | Direct collaborators |
| `sailor_influenced_by.csv` | CSV | Works that influenced Sailor |
| `sailor_influences_others.csv` | CSV | Works influenced by Sailor |
| `sailor_works.csv` | CSV | Sailor's own works with metadata |
| `sailor_temporal_stats.json` | JSON | Decade-level stats for Sailor & Oceanus Folk |
| `influence_network.json` | JSON | 2-hop influence network |
| `oceanus_folk_artists.csv` | CSV | All Oceanus Folk artists with Sailor connection flags |
| `oceanus_folk_influence_spread.csv` | CSV | Cross-genre influence from Oceanus Folk |
| `oceanus_folk_community.json` | JSON | Community summary statistics |
| `d3_main_graph.json` | JSON | D3-ready ego network (colours & sizes) |
| `d3_influence_network.json` | JSON | D3-ready 2-hop influence network |
| `d3_timeline.json` | JSON | D3-ready decade timeline data |
| `d3_linkage.json` | JSON | D3-ready upstream/downstream linkage data |
| `graph_overview.png` | PNG | Node & edge type distribution charts |
| `node_edge_distributions.png` | PNG | Pie + bar distribution charts |
| `ego_network_summary.png` | PNG | Ego network role & influence breakdown |
| `temporal_evolution.png` | PNG | 3-panel decade trend charts |
| `influence_network_summary.png` | PNG | Influence reach & genre breakdown |
| `oceanus_folk_community.png` | PNG | Community analysis (4-panel) |
| `d3_export_summary.png` | PNG | Output file sizes & linkage summary |
| `index.html` | HTML | D3.js interactive dashboard |

---

## Project Structure

```
My5005Project/
├── MC1_graph.json              ← Input data (knowledge graph, ~50 MB)
├── run_preprocess.py           ← Standalone preprocessing script
├── main_preprocess.ipynb       ← Jupyter notebook (same logic + inline plots)
├── requirements.txt            ← Pinned Python 3.10 dependencies
├── README.md                   ← This file
├── Vast Challenge Project.md   ← Project specification
└── output/                     ← Generated by run_preprocess.py
    ├── index.html              ← D3.js dashboard (open via HTTP server)
    ├── d3_main_graph.json
    ├── d3_influence_network.json
    ├── d3_timeline.json
    ├── d3_linkage.json
    ├── *.csv                   ← Tabular data exports
    ├── *.json                  ← Graph & stats exports
    └── *.png                   ← Matplotlib plots
```

---

## Data Source

`MC1_graph.json` — a directed multigraph generated by Python's `networkx.node_link_data()` function, containing:

- **17,412 nodes** — Person, Song, Album, RecordLabel, MusicalGroup
- **37,857 edges** — MemberOf, PerformerOf, ComposerOf, ProducerOf, LyricistOf, InStyleOf, InterpolatesFrom, CoverOf, LyricalReferenceTo, DirectlySamples, RecordedBy, DistributedBy
- **18 weakly connected components**

---

## Deactivating the venv

When you are done:

```bash
deactivate
```
