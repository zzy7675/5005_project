"""
run_preprocess.py
=================
Standalone script version of main_preprocess.ipynb.
Run from the project root:  python run_preprocess.py

Outputs are written to ./output/
The D3.js dashboard is at   ./output/index.html
"""

import json, os, sys
import networkx as nx
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')          # non-interactive backend for script mode
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ── Style ──────────────────────────────────────────────────────────────────
plt.style.use('dark_background')
ACCENT   = '#e94560'
BLUE     = '#4e79a7'
ORANGE   = '#f28e2b'
GREEN    = '#59a14f'
TEAL     = '#76b7b2'
PURPLE   = '#b07aa1'
BG_COLOR = '#1a1a2e'
PANEL_BG = '#16213e'

NODE_COLORS = {
    'Person': BLUE, 'Song': ORANGE, 'Album': '#e15759',
    'RecordLabel': TEAL, 'MusicalGroup': GREEN, 'unknown': '#bab0ac'
}
NODE_COLORS_D3 = {
    'Person': '#4e79a7', 'Song': '#f28e2b', 'Album': '#e15759',
    'RecordLabel': '#76b7b2', 'MusicalGroup': '#59a14f', 'unknown': '#bab0ac'
}
EDGE_COLORS_D3 = {
    'PerformerOf': '#4e79a7', 'ComposerOf': '#f28e2b', 'LyricistOf': '#e15759',
    'ProducerOf': '#76b7b2', 'RecordedBy': '#59a14f', 'DistributedBy': '#edc948',
    'MemberOf': '#b07aa1', 'InStyleOf': '#ff9da7', 'InterpolatesFrom': '#9c755f',
    'CoverOf': '#bab0ac', 'LyricalReferenceTo': '#d37295', 'DirectlySamples': '#a0cbe8',
    'unknown': '#cccccc'
}
ROLE_SIZE = {
    'sailor': 30, 'sailor_work': 18, 'collaborator': 14,
    'influence_source': 10, 'new_gen_artist': 11, 'other': 8
}

WORK_EDGE_TYPES      = {'PerformerOf', 'ComposerOf', 'LyricistOf'}
INFLUENCE_EDGE_TYPES = {'InStyleOf', 'InterpolatesFrom', 'CoverOf',
                        'LyricalReferenceTo', 'DirectlySamples'}

DATA_PATH  = 'MC1_graph.json'
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def safe_val(v):
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.bool_,)):   return bool(v)
    if isinstance(v, float) and np.isnan(v): return None
    return v

def to_decade(year):
    if pd.isna(year): return None
    return int(year) // 10 * 10

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 – Load & Validate Graph
# ══════════════════════════════════════════════════════════════════════════════
print('Step 1: Loading graph...')
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    raw = json.load(f)

G = nx.node_link_graph(raw, directed=True, multigraph=True)

for n, attrs in G.nodes(data=True):
    if 'Node Type' in attrs:
        attrs['type'] = attrs.pop('Node Type')
for u, v, k, attrs in G.edges(keys=True, data=True):
    if 'Edge Type' in attrs:
        attrs['type'] = attrs.pop('Edge Type')
    elif 'edge_type' in attrs:
        attrs['type'] = attrs.pop('edge_type')

num_nodes      = G.number_of_nodes()
num_edges      = G.number_of_edges()
num_components = nx.number_weakly_connected_components(G)
node_types     = sorted({a.get('type','unknown') for _,a in G.nodes(data=True)})
edge_types     = sorted({a.get('type','unknown') for _,_,a in G.edges(data=True)})

report = f"""# Graph Validation Report
| Property | Value |
|---|---|
| Is Directed MultiGraph | {G.is_directed() and G.is_multigraph()} |
| Total Nodes | {num_nodes} |
| Total Edges | {num_edges} |
| Weakly Connected Components | {num_components} |
| Node Types | {node_types} |
| Edge Types | {edge_types} |
"""
with open(f'{OUTPUT_DIR}/graph_validation_report.md', 'w', encoding='utf-8') as f:
    f.write(report)

# Plot graph overview
node_type_counts = {}
for _, attrs in G.nodes(data=True):
    t = attrs.get('type', 'unknown')
    node_type_counts[t] = node_type_counts.get(t, 0) + 1

edge_type_counts = {}
for _, _, attrs in G.edges(data=True):
    t = attrs.get('type', 'unknown')
    edge_type_counts[t] = edge_type_counts.get(t, 0) + 1

fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor=BG_COLOR)
fig.suptitle('MC1 Knowledge Graph — Overview', color='white', fontsize=14, fontweight='bold')
ax = axes[0]; ax.set_facecolor(PANEL_BG)
types = list(node_type_counts.keys()); counts = list(node_type_counts.values())
colors = [NODE_COLORS.get(t, '#bab0ac') for t in types]
bars = ax.barh(types, counts, color=colors, edgecolor='#303050', linewidth=0.5)
for bar, cnt in zip(bars, counts):
    ax.text(bar.get_width()+20, bar.get_y()+bar.get_height()/2, f'{cnt:,}', va='center', color='white', fontsize=9)
ax.set_xlabel('Count', color='#a0a0c0'); ax.set_title('Node Type Distribution', color='white', fontsize=11)
ax.tick_params(colors='#a0a0c0'); ax.spines[:].set_color('#303050'); ax.set_xlim(0, max(counts)*1.15)
ax2 = axes[1]; ax2.set_facecolor(PANEL_BG)
etypes = sorted(edge_type_counts.keys(), key=lambda x: edge_type_counts[x])
ecounts = [edge_type_counts[t] for t in etypes]
palette = plt.cm.tab20(np.linspace(0, 1, len(etypes)))
bars2 = ax2.barh(etypes, ecounts, color=palette, edgecolor='#303050', linewidth=0.5)
for bar, cnt in zip(bars2, ecounts):
    ax2.text(bar.get_width()+20, bar.get_y()+bar.get_height()/2, f'{cnt:,}', va='center', color='white', fontsize=9)
ax2.set_xlabel('Count', color='#a0a0c0'); ax2.set_title('Edge Type Distribution', color='white', fontsize=11)
ax2.tick_params(colors='#a0a0c0'); ax2.spines[:].set_color('#303050'); ax2.set_xlim(0, max(ecounts)*1.15)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/graph_overview.png', dpi=120, bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
print(f'  Nodes: {num_nodes:,}  Edges: {num_edges:,}  Components: {num_components}')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 – Node & Edge DataFrames
# ══════════════════════════════════════════════════════════════════════════════
print('Step 2: Building DataFrames...')
nodes_records = [{'node_id': nid, **attrs} for nid, attrs in G.nodes(data=True)]
nodes_df = pd.DataFrame(nodes_records)
for col in ['release_date', 'notoriety_date', 'written_date']:
    if col in nodes_df.columns:
        nodes_df[col] = pd.to_numeric(nodes_df[col], errors='coerce').astype('Int64')
if 'notable' in nodes_df.columns:
    nodes_df['notable'] = nodes_df['notable'].fillna(False).astype(bool)

edges_records = [{'source': s, 'target': t, 'key': k, **attrs}
                 for s, t, k, attrs in G.edges(keys=True, data=True)]
edges_df = pd.DataFrame(edges_records)
nodes_df.to_csv(f'{OUTPUT_DIR}/nodes_df.csv', index=False)
edges_df.to_csv(f'{OUTPUT_DIR}/edges_df.csv', index=False)
print(f'  nodes_df: {len(nodes_df)} rows  edges_df: {len(edges_df)} rows')

# Plot: Node & Edge type distributions
fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor=BG_COLOR)
fig.suptitle('Node & Edge Type Distributions', color='white', fontsize=13, fontweight='bold')
node_vc = nodes_df['type'].value_counts()
ax = axes[0]; ax.set_facecolor(PANEL_BG)
wedge_colors = [NODE_COLORS.get(t, '#bab0ac') for t in node_vc.index]
wedges, texts, autotexts = ax.pie(
    node_vc.values, labels=node_vc.index, colors=wedge_colors,
    autopct='%1.1f%%', startangle=140,
    textprops={'color': 'white', 'fontsize': 9},
    wedgeprops={'edgecolor': '#1a1a2e', 'linewidth': 1.5}
)
for at in autotexts:
    at.set_color('#1a1a2e'); at.set_fontsize(8)
ax.set_title(f'Node Types  (n={len(nodes_df):,})', color='white', fontsize=11)
edge_vc = edges_df['type'].value_counts().sort_values()
ax2 = axes[1]; ax2.set_facecolor(PANEL_BG)
palette = plt.cm.tab20(np.linspace(0, 1, len(edge_vc)))
bars = ax2.barh(edge_vc.index, edge_vc.values, color=palette, edgecolor='#303050', linewidth=0.5)
for bar, cnt in zip(bars, edge_vc.values):
    ax2.text(bar.get_width() + 30, bar.get_y() + bar.get_height()/2,
             f'{cnt:,}', va='center', color='white', fontsize=8)
ax2.set_xlabel('Count', color='#a0a0c0')
ax2.set_title(f'Edge Types  (n={len(edges_df):,})', color='white', fontsize=11)
ax2.tick_params(colors='#a0a0c0'); ax2.spines[:].set_color('#303050')
ax2.set_xlim(0, edge_vc.max() * 1.18)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/node_edge_distributions.png', dpi=120, bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
print('  Saved node_edge_distributions.png')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 – Sailor Shift Ego Network
# ══════════════════════════════════════════════════════════════════════════════
print('Step 3: Building Sailor Shift ego network...')
person_df = nodes_df[nodes_df['type'] == 'Person'].copy()
name_mask  = person_df['name'].str.lower().str.contains('sailor shift', na=False)
stage_mask = pd.Series(False, index=person_df.index)
if 'stage_name' in person_df.columns:
    stage_mask = person_df['stage_name'].str.lower().str.contains('sailor shift', na=False)
sailor_rows = person_df[name_mask | stage_mask]
assert len(sailor_rows) >= 1, 'Sailor Shift not found!'
SAILOR_ID = int(sailor_rows.iloc[0]['node_id'])

sailor_work_ids = set()
for _, tgt, attrs in G.out_edges(SAILOR_ID, data=True):
    if attrs.get('type') in WORK_EDGE_TYPES:
        sailor_work_ids.add(tgt)

collaborator_ids = set()
collab_edges = []
for work_id in sailor_work_ids:
    for src, _, attrs in G.in_edges(work_id, data=True):
        if attrs.get('type') in WORK_EDGE_TYPES and src != SAILOR_ID:
            if G.nodes[src].get('type') in ('Person', 'MusicalGroup'):
                collaborator_ids.add(src)
                collab_edges.append({
                    'collaborator_id': src, 'collaborator_name': G.nodes[src].get('name',''),
                    'work_id': work_id, 'work_name': G.nodes[work_id].get('name',''),
                    'edge_type': attrs.get('type')
                })

sailor_influenced_by = []
for work_id in sailor_work_ids:
    for _, tgt, attrs in G.out_edges(work_id, data=True):
        if attrs.get('type') in INFLUENCE_EDGE_TYPES:
            ta = G.nodes[tgt]
            sailor_influenced_by.append({
                'sailor_work_id': work_id, 'sailor_work_name': G.nodes[work_id].get('name',''),
                'influenced_by_id': tgt, 'influenced_by_name': ta.get('name',''),
                'influenced_by_type': ta.get('type','unknown'), 'influenced_by_genre': ta.get('genre',''),
                'influenced_by_year': ta.get('release_date'), 'edge_type': attrs.get('type')
            })

sailor_influences_others = []
for work_id in sailor_work_ids:
    for src, _, attrs in G.in_edges(work_id, data=True):
        if attrs.get('type') in INFLUENCE_EDGE_TYPES:
            sa = G.nodes[src]
            sailor_influences_others.append({
                'sailor_work_id': work_id, 'sailor_work_name': G.nodes[work_id].get('name',''),
                'influenced_work_id': src, 'influenced_work_name': sa.get('name',''),
                'influenced_work_type': sa.get('type','unknown'), 'influenced_work_genre': sa.get('genre',''),
                'influenced_work_year': sa.get('release_date'), 'edge_type': attrs.get('type')
            })

# ── Influence sources (works Sailor's works reference) ─────────────────────
influence_source_ids = {r['influenced_by_id'] for r in sailor_influenced_by}

ego_node_ids = {SAILOR_ID} | sailor_work_ids | collaborator_ids | influence_source_ids
ego_subgraph = G.subgraph(ego_node_ids).copy()
for n in ego_subgraph.nodes():
    if n == SAILOR_ID:
        ego_subgraph.nodes[n]['role'] = 'sailor'
    elif n in sailor_work_ids:
        ego_subgraph.nodes[n]['role'] = 'sailor_work'
    elif n in collaborator_ids:
        ego_subgraph.nodes[n]['role'] = 'collaborator'
    elif n in influence_source_ids:
        ego_subgraph.nodes[n]['role'] = 'influence_source'
    else:
        ego_subgraph.nodes[n]['role'] = 'other'

ego_nodes = [{'id': n, **{k: safe_val(v) for k,v in attrs.items()}} for n,attrs in ego_subgraph.nodes(data=True)]
ego_edges = [{'source': u, 'target': v, **{k: safe_val(v2) for k,v2 in attrs.items()}} for u,v,attrs in ego_subgraph.edges(data=True)]
with open(f'{OUTPUT_DIR}/sailor_ego_network.json', 'w', encoding='utf-8') as f:
    json.dump({'nodes': ego_nodes, 'links': ego_edges}, f, ensure_ascii=False, default=str)
pd.DataFrame(collab_edges).to_csv(f'{OUTPUT_DIR}/sailor_collaborators.csv', index=False)
pd.DataFrame(sailor_influenced_by).to_csv(f'{OUTPUT_DIR}/sailor_influenced_by.csv', index=False)
pd.DataFrame(sailor_influences_others).to_csv(f'{OUTPUT_DIR}/sailor_influences_others.csv', index=False)

# ── Ivy Echoes band member lookup (needs only nodes_df) ────────────────────
IVY_ECHOES_NAMES = ['sailor shift','maya jensen','lila hartman','lilly hartman','jade thompson','sophie ramirez']
ivy_echoes_ids = {}
for _, row in nodes_df[nodes_df['type']=='Person'].iterrows():
    nl = str(row.get('name','')).lower(); sl = str(row.get('stage_name','')).lower()
    for ivy_name in IVY_ECHOES_NAMES:
        if ivy_name in nl or ivy_name in sl:
            ivy_echoes_ids[ivy_name] = int(row['node_id']); break

print(f'  Sailor ID={SAILOR_ID}  Works={len(sailor_work_ids)}  Collaborators={len(collaborator_ids)}  Ivy Echoes={len(ivy_echoes_ids)}')

# Plot: Ego Network Summary
fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor=BG_COLOR)
fig.suptitle(f'Sailor Shift Ego Network Summary  (node_id={SAILOR_ID})',
             color='white', fontsize=13, fontweight='bold')
role_counts = {}
for n in ego_subgraph.nodes():
    r = ego_subgraph.nodes[n].get('role', 'other')
    role_counts[r] = role_counts.get(r, 0) + 1
ax = axes[0]; ax.set_facecolor(PANEL_BG)
role_colors = {'sailor': '#ffdd00', 'sailor_work': ORANGE, 'collaborator': BLUE,
               'influence_source': PURPLE, 'hop1_influenced': '#ff9da7',
               'hop2_influenced': '#9c755f', 'influenced_artist': TEAL, 'other': '#404060'}
rc_labels = list(role_counts.keys()); rc_vals = list(role_counts.values())
rc_cols = [role_colors.get(r, '#bab0ac') for r in rc_labels]
bars = ax.bar(rc_labels, rc_vals, color=rc_cols, edgecolor='#303050', linewidth=0.5)
for bar, cnt in zip(bars, rc_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            str(cnt), ha='center', color='white', fontsize=9)
ax.set_title('Ego Node Roles', color='white', fontsize=11)
ax.set_ylabel('Count', color='#a0a0c0')
ax.tick_params(colors='#a0a0c0', axis='x', rotation=15); ax.spines[:].set_color('#303050')
inf_df_plot = pd.DataFrame(sailor_influenced_by)
ax2 = axes[1]; ax2.set_facecolor(PANEL_BG)
if not inf_df_plot.empty:
    et_vc = inf_df_plot['edge_type'].value_counts()
    palette2 = [plt.cm.tab10(i) for i in range(len(et_vc))]
    bars2 = ax2.barh(et_vc.index, et_vc.values, color=palette2, edgecolor='#303050')
    for bar, cnt in zip(bars2, et_vc.values):
        ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                 str(cnt), va='center', color='white', fontsize=9)
    ax2.set_xlim(0, et_vc.max() * 1.2)
ax2.set_title(f'Influence Types → Sailor\n({len(inf_df_plot)} total)', color='white', fontsize=11)
ax2.set_xlabel('Count', color='#a0a0c0'); ax2.tick_params(colors='#a0a0c0'); ax2.spines[:].set_color('#303050')
ax3 = axes[2]; ax3.set_facecolor(PANEL_BG)
if not inf_df_plot.empty and 'influenced_by_genre' in inf_df_plot.columns:
    genre_vc = inf_df_plot['influenced_by_genre'].dropna().replace('', np.nan).dropna().value_counts().head(10)
    palette3 = plt.cm.tab20(np.linspace(0, 1, len(genre_vc)))
    bars3 = ax3.barh(genre_vc.index, genre_vc.values, color=palette3, edgecolor='#303050')
    for bar, cnt in zip(bars3, genre_vc.values):
        ax3.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
                 str(cnt), va='center', color='white', fontsize=8)
    ax3.set_xlim(0, genre_vc.max() * 1.2)
ax3.set_title('Top Genres Influencing Sailor', color='white', fontsize=11)
ax3.set_xlabel('Count', color='#a0a0c0'); ax3.tick_params(colors='#a0a0c0'); ax3.spines[:].set_color('#303050')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/ego_network_summary.png', dpi=120, bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
print('  Saved ego_network_summary.png')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 – Temporal Analysis
# ══════════════════════════════════════════════════════════════════════════════
print('Step 4: Temporal analysis...')
work_rows = nodes_df[nodes_df['node_id'].isin(sailor_work_ids)].copy()
work_rows['decade'] = work_rows['release_date'].apply(to_decade)
sailor_works_summary = work_rows[['node_id','name','type','genre','notable','release_date','notoriety_date','written_date','decade']].sort_values('release_date')
sailor_works_summary.to_csv(f'{OUTPUT_DIR}/sailor_works.csv', index=False)

of_mask = nodes_df['type'].isin(['Song','Album']) & nodes_df['genre'].str.lower().str.contains('oceanus folk', na=False)
of_df = nodes_df[of_mask].copy()
of_df['decade'] = of_df['release_date'].apply(to_decade)
all_works_df = nodes_df[nodes_df['type'].isin(['Song','Album'])].copy()
all_works_df['decade'] = all_works_df['release_date'].apply(to_decade)

sailor_decade_stats = work_rows.groupby('decade').agg(
    works_count=('node_id','count'), notable_count=('notable','sum'),
    genres=('genre', lambda x: x.value_counts().to_dict())).reset_index()
sailor_decade_stats['notable_ratio'] = sailor_decade_stats['notable_count'] / sailor_decade_stats['works_count']
global_of_decade_stats = of_df.groupby('decade').agg(works_count=('node_id','count'), notable_count=('notable','sum')).reset_index()
global_of_decade_stats['notable_ratio'] = global_of_decade_stats['notable_count'] / global_of_decade_stats['works_count']
global_decade_stats = all_works_df.groupby(['decade','genre']).agg(works_count=('node_id','count'), notable_count=('notable','sum')).reset_index()

with open(f'{OUTPUT_DIR}/sailor_temporal_stats.json', 'w', encoding='utf-8') as f:
    json.dump({
        'sailor_decade_stats': sailor_decade_stats.to_dict(orient='records'),
        'global_oceanus_folk_decade_stats': global_of_decade_stats.to_dict(orient='records'),
        'global_decade_genre_stats': global_decade_stats.to_dict(orient='records')
    }, f, ensure_ascii=False, default=str)

# Plot temporal evolution
decades_all = sorted(all_works_df['decade'].dropna().unique())
decade_labels = [f"'{str(int(d))[2:]}s" for d in decades_all]
fig, axes = plt.subplots(3, 1, figsize=(14, 12), facecolor=BG_COLOR)
fig.suptitle('Temporal Evolution of Sailor Shift & Oceanus Folk', color='white', fontsize=14, fontweight='bold')
total_by_dec = all_works_df.groupby('decade').size()
of_by_dec = of_df.groupby('decade').size()
sailor_by_dec = work_rows.groupby('decade').size()
total_vals = [total_by_dec.get(d,0) for d in decades_all]
of_vals = [of_by_dec.get(d,0) for d in decades_all]
sailor_vals = [sailor_by_dec.get(d,0) for d in decades_all]
other_vals = [max(0,t-o) for t,o in zip(total_vals,of_vals)]
of_no_sailor = [max(0,o-s) for o,s in zip(of_vals,sailor_vals)]
x = np.arange(len(decades_all)); w = 0.65
ax1 = axes[0]; ax1.set_facecolor(PANEL_BG)
ax1.bar(x, other_vals, width=w, label='Other Genres', color='#404060', edgecolor='#1a1a2e', lw=0.5)
ax1.bar(x, of_no_sailor, width=w, bottom=other_vals, label='Oceanus Folk', color=BLUE, edgecolor='#1a1a2e', lw=0.5)
ax1.bar(x, sailor_vals, width=w, bottom=[a+b for a,b in zip(other_vals,of_no_sailor)], label='Sailor Works', color=ACCENT, edgecolor='#1a1a2e', lw=0.5)
ax1.set_xticks(x); ax1.set_xticklabels(decade_labels, color='#a0a0c0', fontsize=9)
ax1.set_ylabel('Number of Works', color='#a0a0c0'); ax1.set_title('Works per Decade', color='white', fontsize=11)
ax1.legend(loc='upper left', fontsize=8, facecolor=PANEL_BG, edgecolor='#303050', labelcolor='white')
ax1.tick_params(colors='#a0a0c0'); ax1.spines[:].set_color('#303050')
ax2 = axes[1]; ax2.set_facecolor(PANEL_BG)
all_nr = [all_works_df.groupby('decade')['notable'].mean().get(d,0)*100 for d in decades_all]
of_nr  = [of_df.groupby('decade')['notable'].mean().get(d,0)*100 for d in decades_all]
sailor_nr_by_dec = work_rows.groupby('decade')['notable'].mean()*100
sailor_nr = [sailor_nr_by_dec.get(d,np.nan) for d in decades_all]
ax2.plot(x, all_nr, color=ORANGE, marker='o', markersize=5, linewidth=2, label='All Works')
ax2.plot(x, of_nr, color=BLUE, marker='s', markersize=5, linewidth=2, label='Oceanus Folk')
ax2.plot(x, sailor_nr, color=ACCENT, marker='^', markersize=6, linewidth=2, linestyle='--', label='Sailor Shift')
ax2.set_xticks(x); ax2.set_xticklabels(decade_labels, color='#a0a0c0', fontsize=9)
ax2.set_ylabel('Notable Works (%)', color='#a0a0c0'); ax2.set_title('Proportion of Notable Works per Decade', color='white', fontsize=11)
ax2.legend(loc='upper left', fontsize=8, facecolor=PANEL_BG, edgecolor='#303050', labelcolor='white')
ax2.tick_params(colors='#a0a0c0'); ax2.spines[:].set_color('#303050'); ax2.set_ylim(0,100)
ax3 = axes[2]; ax3.set_facecolor(PANEL_BG)
top_genres = all_works_df['genre'].dropna().value_counts().head(6).index.tolist()
genre_palette = plt.cm.tab10(np.linspace(0,1,len(top_genres)))
bottoms = np.zeros(len(decades_all))
for gi, genre in enumerate(top_genres):
    vals = np.array([all_works_df[all_works_df['genre']==genre].groupby('decade').size().get(d,0) for d in decades_all], dtype=float)
    ax3.bar(x, vals, width=w, bottom=bottoms, label=genre, color=genre_palette[gi], edgecolor='#1a1a2e', lw=0.3)
    bottoms += vals
ax3.set_xticks(x); ax3.set_xticklabels(decade_labels, color='#a0a0c0', fontsize=9)
ax3.set_ylabel('Number of Works', color='#a0a0c0'); ax3.set_title('Genre Distribution per Decade (Top 6)', color='white', fontsize=11)
ax3.legend(loc='upper left', fontsize=7, facecolor=PANEL_BG, edgecolor='#303050', labelcolor='white', ncol=2)
ax3.tick_params(colors='#a0a0c0'); ax3.spines[:].set_color('#303050')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/temporal_evolution.png', dpi=120, bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
print(f'  OF works: {len(of_df)}  Sailor works: {len(work_rows)}')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 – Influence Network Summary Plot
# ══════════════════════════════════════════════════════════════════════════════
print('Step 5: Influence network summary...')

# Plot: Influence Network Summary — repurposed panels since hop-1/hop-2 = 0 in this dataset
fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor=BG_COLOR)
fig.suptitle('Sailor Shift — Influence & Collaboration Summary', color='white', fontsize=13, fontweight='bold')

# Panel 1: Ego network node counts by role
ax = axes[0]; ax.set_facecolor(PANEL_BG)
ego_role_labels = ['Sailor', 'Her Works', 'Collaborators', 'Infl. Sources']
ego_role_vals   = [1, len(sailor_work_ids), len(collaborator_ids), len(influence_source_ids)]
ego_role_colors = ['#ffdd00', ORANGE, BLUE, PURPLE]
bars = ax.bar(ego_role_labels, ego_role_vals, color=ego_role_colors, edgecolor='#303050', lw=0.5)
for bar, cnt in zip(bars, ego_role_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            str(cnt), ha='center', color='white', fontsize=10)
ax.set_title('Ego Network Composition', color='white', fontsize=11)
ax.set_ylabel('Count', color='#a0a0c0')
ax.tick_params(colors='#a0a0c0', axis='x', labelsize=9); ax.spines[:].set_color('#303050')

# Panel 2: Influence edge types (what Sailor's works reference)
ax2 = axes[1]; ax2.set_facecolor(PANEL_BG)
inf_df_p = pd.DataFrame(sailor_influenced_by)
if not inf_df_p.empty:
    et_vc2 = inf_df_p['edge_type'].value_counts()
    palette2 = [plt.cm.tab10(i) for i in range(len(et_vc2))]
    bars2 = ax2.barh(et_vc2.index, et_vc2.values, color=palette2, edgecolor='#303050')
    for bar, cnt in zip(bars2, et_vc2.values):
        ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                 str(cnt), va='center', color='white', fontsize=9)
    ax2.set_xlim(0, et_vc2.max() * 1.2)
ax2.set_title(f'Influence Edge Types (Sailor → Sources)\n({len(inf_df_p)} references)', color='white', fontsize=11)
ax2.set_xlabel('Count', color='#a0a0c0'); ax2.tick_params(colors='#a0a0c0'); ax2.spines[:].set_color('#303050')

# Panel 3: Ivy Echoes members
ax3 = axes[2]; ax3.set_facecolor(PANEL_BG); ax3.axis('off')
ivy_text = 'Ivy Echoes Members Found:\n\n'
for name, nid in ivy_echoes_ids.items():
    ivy_text += f'  • {name.title()}  (id={nid})\n'
if not ivy_echoes_ids:
    ivy_text += '  (none found)'
ax3.text(0.05, 0.95, ivy_text, transform=ax3.transAxes, color='white', fontsize=10,
         va='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='#0f3460', edgecolor=ACCENT, alpha=0.9))
ax3.set_title('Ivy Echoes Band Members', color='white', fontsize=11)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/influence_network_summary.png', dpi=120, bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
print('  Saved influence_network_summary.png')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 – Oceanus Folk Community
# ══════════════════════════════════════════════════════════════════════════════
print('Step 6: Oceanus Folk community analysis...')
of_work_ids = set(of_df['node_id'].tolist())
of_artist_ids = set(); of_artist_work_map = {}
for wid in of_work_ids:
    for src,_,attrs in G.in_edges(wid,data=True):
        if attrs.get('type') in WORK_EDGE_TYPES and G.nodes[src].get('type') in ('Person','MusicalGroup'):
            of_artist_ids.add(src); of_artist_work_map.setdefault(src,[]).append(wid)

direct_of_collabs = of_artist_ids & collaborator_ids
# No incoming influence edges to Sailor's works in this dataset → always empty
all_influenced_artist_ids = set()
indirect_of_influenced = set()
SAILOR_BREAKTHROUGH_YEAR = 2028
new_gen_artist_ids = set()
for artist_id in of_artist_ids:
    work_years = []
    for wid in of_artist_work_map.get(artist_id,[]):
        yr = nodes_df.loc[nodes_df['node_id']==wid,'release_date']
        if not yr.empty and not pd.isna(yr.iloc[0]): work_years.append(int(yr.iloc[0]))
    if work_years and min(work_years) >= SAILOR_BREAKTHROUGH_YEAR: new_gen_artist_ids.add(artist_id)

of_artist_records = []
for artist_id in of_artist_ids:
    attrs = G.nodes[artist_id]
    work_years = []
    for wid in of_artist_work_map.get(artist_id,[]):
        yr = nodes_df.loc[nodes_df['node_id']==wid,'release_date']
        if not yr.empty and not pd.isna(yr.iloc[0]): work_years.append(int(yr.iloc[0]))
    of_artist_records.append({
        'artist_id':artist_id,'name':attrs.get('name',''),'stage_name':attrs.get('stage_name',''),
        'type':attrs.get('type',''),'of_works_count':len(of_artist_work_map.get(artist_id,[])),
        'first_of_work_year':min(work_years) if work_years else None,
        'last_of_work_year':max(work_years) if work_years else None,
        'direct_collab_with_sailor':artist_id in direct_of_collabs,
        'influenced_by_sailor':artist_id in indirect_of_influenced,
        'new_generation':artist_id in new_gen_artist_ids,
        'is_ivy_echoes':artist_id in set(ivy_echoes_ids.values())
    })
of_artist_df = pd.DataFrame(of_artist_records).sort_values('first_of_work_year')
of_artist_df.to_csv(f'{OUTPUT_DIR}/oceanus_folk_artists.csv', index=False)

of_influence_spread = []
for wid in of_work_ids:
    for src,_,attrs in G.in_edges(wid,data=True):
        if attrs.get('type') in INFLUENCE_EDGE_TYPES:
            sa = G.nodes[src]; sg = sa.get('genre','')
            if sg and 'oceanus folk' not in sg.lower():
                of_influence_spread.append({
                    'of_work_id':wid,'of_work_name':G.nodes[wid].get('name',''),
                    'referencing_work_id':src,'referencing_work_name':sa.get('name',''),
                    'referencing_genre':sg,'referencing_year':sa.get('release_date'),'edge_type':attrs.get('type')
                })
of_spread_df = pd.DataFrame(of_influence_spread)
of_spread_df.to_csv(f'{OUTPUT_DIR}/oceanus_folk_influence_spread.csv', index=False)
with open(f'{OUTPUT_DIR}/oceanus_folk_community.json','w',encoding='utf-8') as f:
    json.dump({
        'total_of_works':len(of_work_ids),'total_of_artists':len(of_artist_ids),
        'direct_sailor_collabs':len(direct_of_collabs),'sailor_influenced_artists':len(indirect_of_influenced),
        'new_generation_artists':len(new_gen_artist_ids),'sailor_breakthrough_year':SAILOR_BREAKTHROUGH_YEAR,
        'ivy_echoes_ids':ivy_echoes_ids,'genre_spread_count':len(of_spread_df),
        'genres_influenced':of_spread_df['referencing_genre'].value_counts().to_dict() if not of_spread_df.empty else {}
    },f,ensure_ascii=False,default=str)
print(f'  OF artists: {len(of_artist_ids)}  New-gen: {len(new_gen_artist_ids)}  Spread: {len(of_spread_df)}')

# Plot: Oceanus Folk Community
fig, axes = plt.subplots(2, 2, figsize=(15, 10), facecolor=BG_COLOR)
fig.suptitle('Oceanus Folk Community Analysis', color='white', fontsize=14, fontweight='bold')
ax = axes[0, 0]; ax.set_facecolor(PANEL_BG)
summary_labels = ['Direct Sailor\nCollabs', 'Sailor-Influenced', 'New Generation', 'Other OF Artists']
other_of = len(of_artist_ids) - len(direct_of_collabs) - len(indirect_of_influenced) - len(new_gen_artist_ids)
summary_vals = [len(direct_of_collabs), len(indirect_of_influenced), len(new_gen_artist_ids), max(0, other_of)]
summary_colors = [ACCENT, ORANGE, GREEN, '#404060']
wedges, texts, autotexts = ax.pie(
    summary_vals, labels=summary_labels, colors=summary_colors,
    autopct='%1.1f%%', startangle=90, pctdistance=0.75,
    textprops={'color': 'white', 'fontsize': 8},
    wedgeprops={'edgecolor': '#1a1a2e', 'linewidth': 1.5, 'width': 0.6}
)
for at in autotexts: at.set_color('#1a1a2e'); at.set_fontsize(7)
ax.text(0, 0, f'{len(of_artist_ids)}\nArtists', ha='center', va='center',
        color='white', fontsize=11, fontweight='bold')
ax.set_title('OF Artist Community Breakdown', color='white', fontsize=11)
ax2 = axes[0, 1]; ax2.set_facecolor(PANEL_BG)
if not of_artist_df.empty and 'first_of_work_year' in of_artist_df.columns:
    debut_years = of_artist_df['first_of_work_year'].dropna()
    ax2.hist(debut_years, bins=range(int(debut_years.min()), int(debut_years.max())+2),
             color=BLUE, edgecolor='#1a1a2e', linewidth=0.5, alpha=0.85)
    ax2.axvline(SAILOR_BREAKTHROUGH_YEAR, color=ACCENT, linewidth=2, linestyle='--',
                label=f'Sailor Breakthrough ({SAILOR_BREAKTHROUGH_YEAR})')
    ax2.legend(fontsize=8, facecolor=PANEL_BG, edgecolor='#303050', labelcolor='white')
ax2.set_xlabel('First OF Work Year', color='#a0a0c0'); ax2.set_ylabel('Number of Artists', color='#a0a0c0')
ax2.set_title('OF Artist Debut Year Distribution', color='white', fontsize=11)
ax2.tick_params(colors='#a0a0c0'); ax2.spines[:].set_color('#303050')
ax3 = axes[1, 0]; ax3.set_facecolor(PANEL_BG)
if not of_spread_df.empty:
    genre_spread_vc = of_spread_df['referencing_genre'].value_counts().head(12)
    palette3 = plt.cm.tab20(np.linspace(0, 1, len(genre_spread_vc)))
    bars3 = ax3.barh(genre_spread_vc.index, genre_spread_vc.values, color=palette3, edgecolor='#303050')
    for bar, cnt in zip(bars3, genre_spread_vc.values):
        ax3.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                 str(cnt), va='center', color='white', fontsize=8)
    ax3.set_xlim(0, genre_spread_vc.max() * 1.2)
ax3.set_title('Genres Influenced by Oceanus Folk', color='white', fontsize=11)
ax3.set_xlabel('Number of Referencing Works', color='#a0a0c0')
ax3.tick_params(colors='#a0a0c0'); ax3.spines[:].set_color('#303050')
ax4 = axes[1, 1]; ax4.set_facecolor(PANEL_BG)
if not of_spread_df.empty and 'referencing_year' in of_spread_df.columns:
    spread_years = pd.to_numeric(of_spread_df['referencing_year'], errors='coerce').dropna()
    spread_decades = (spread_years // 10 * 10).value_counts().sort_index()
    ax4.bar(spread_decades.index, spread_decades.values, width=8,
            color=GREEN, edgecolor='#1a1a2e', linewidth=0.5, alpha=0.85)
    ax4.axvline(SAILOR_BREAKTHROUGH_YEAR, color=ACCENT, linewidth=2, linestyle='--',
                label=f'Sailor Breakthrough ({SAILOR_BREAKTHROUGH_YEAR})')
    ax4.legend(fontsize=8, facecolor=PANEL_BG, edgecolor='#303050', labelcolor='white')
ax4.set_xlabel('Decade', color='#a0a0c0'); ax4.set_ylabel('Cross-Genre References', color='#a0a0c0')
ax4.set_title('OF Influence Spread Over Time', color='white', fontsize=11)
ax4.tick_params(colors='#a0a0c0'); ax4.spines[:].set_color('#303050')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/oceanus_folk_community.png', dpi=120, bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
print('  Saved oceanus_folk_community.png')

# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 – D3.js Data Export
# ══════════════════════════════════════════════════════════════════════════════
print('Step 7: Exporting D3.js data...')

# D3 Main Graph — ego network + new-gen OF artists
d3_main_nodes = []
existing_node_ids = set()
for n, attrs in ego_subgraph.nodes(data=True):
    nt = attrs.get('type','unknown'); role = attrs.get('role','other')
    d3_main_nodes.append({'id':n,'label':attrs.get('name',str(n)),'type':nt,'role':role,
        'color':NODE_COLORS_D3.get(nt,NODE_COLORS_D3['unknown']),'size':ROLE_SIZE.get(role,8),
        'genre':attrs.get('genre'),'notable':safe_val(attrs.get('notable')),
        'release_date':safe_val(attrs.get('release_date')),'notoriety_date':safe_val(attrs.get('notoriety_date')),
        'stage_name':attrs.get('stage_name')})
    existing_node_ids.add(n)

# Add new-generation OF artists (debuted >= 2028) not already in ego subgraph
d3_main_edges = []
for u,v,attrs in ego_subgraph.edges(data=True):
    et = attrs.get('type','unknown')
    d3_main_edges.append({'source':u,'target':v,'type':et,'color':EDGE_COLORS_D3.get(et,EDGE_COLORS_D3['unknown'])})

NEW_GEN_COLOR = '#e9c46a'  # warm gold for new-gen artists
INSPIRED_COLOR = '#a8dadc'

for _, row in of_artist_df.iterrows():
    if not row.get('new_generation', False): continue
    aid = int(row['artist_id'])
    if aid in existing_node_ids: continue  # already in graph (e.g. collaborator)
    attrs = G.nodes[aid]
    nt = attrs.get('type', 'Person')
    d3_main_nodes.append({
        'id': aid,
        'label': row.get('name','') or str(aid),
        'type': nt,
        'role': 'new_gen_artist',
        'color': NEW_GEN_COLOR,
        'size': ROLE_SIZE['new_gen_artist'],
        'genre': 'Oceanus Folk',
        'notable': bool(row.get('influenced_by_sailor', False)),
        'release_date': safe_val(row.get('first_of_work_year')),
        'notoriety_date': None,
        'stage_name': attrs.get('stage_name'),
        'first_of_work_year': safe_val(row.get('first_of_work_year')),
        'of_works_count': int(row.get('of_works_count', 0)),
        'direct_collab_with_sailor': bool(row.get('direct_collab_with_sailor', False)),
    })
    existing_node_ids.add(aid)
    # Synthetic "Inspired" edge from Sailor to new-gen artist
    d3_main_edges.append({
        'source': SAILOR_ID, 'target': aid,
        'type': 'Inspired', 'color': INSPIRED_COLOR
    })

with open(f'{OUTPUT_DIR}/d3_main_graph.json','w',encoding='utf-8') as f:
    json.dump({'nodes':d3_main_nodes,'links':d3_main_edges,'sailor_id':SAILOR_ID,
               'node_color_legend':NODE_COLORS_D3,'edge_color_legend':EDGE_COLORS_D3},f,ensure_ascii=False,default=str)

# D3 Timeline
from collections import defaultdict
timeline_records = []
for _, row in all_works_df.iterrows():
    decade = row.get('decade')
    if decade is None or pd.isna(decade): continue
    timeline_records.append({
        'node_id':int(row['node_id']),'name':row.get('name',''),'type':row.get('type',''),
        'genre':row.get('genre',''),'decade':int(decade),'notable':bool(row.get('notable',False)),
        'release_date':None if pd.isna(row.get('release_date')) else int(row['release_date']),
        'is_sailor_work':int(row['node_id']) in sailor_work_ids,
        'is_oceanus_folk':'oceanus folk' in str(row.get('genre','')).lower()
    })
decade_agg = defaultdict(lambda: {'total':0,'notable':0,'genres':defaultdict(int),'sailor_works':0,'oceanus_folk':0})
for rec in timeline_records:
    d = rec['decade']
    decade_agg[d]['total'] += 1
    if rec['notable']:         decade_agg[d]['notable'] += 1
    if rec['genre']:           decade_agg[d]['genres'][rec['genre']] += 1
    if rec['is_sailor_work']:  decade_agg[d]['sailor_works'] += 1
    if rec['is_oceanus_folk']: decade_agg[d]['oceanus_folk'] += 1
with open(f'{OUTPUT_DIR}/d3_timeline.json','w',encoding='utf-8') as f:
    json.dump({'per_work':timeline_records,'per_decade':[
        {'decade':d,'total':v['total'],'notable':v['notable'],
         'notable_ratio':round(v['notable']/v['total'],4) if v['total']>0 else 0,
         'genres':dict(v['genres']),'sailor_works':v['sailor_works'],'oceanus_folk':v['oceanus_folk']}
        for d,v in sorted(decade_agg.items())
    ]},f,ensure_ascii=False,default=str)

# Plot: D3 Export Summary
fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor=BG_COLOR)
fig.suptitle('D3.js Export Summary', color='white', fontsize=13, fontweight='bold')
ax = axes[0]; ax.set_facecolor(PANEL_BG)
file_sizes = {}
for fname in sorted(os.listdir(OUTPUT_DIR)):
    if fname.endswith('.json') or fname.endswith('.csv'):
        fpath = os.path.join(OUTPUT_DIR, fname)
        file_sizes[fname] = os.path.getsize(fpath) / 1024
sorted_files = sorted(file_sizes.items(), key=lambda x: x[1])
fnames_list = [f[0] for f in sorted_files]
fsizes_list = [f[1] for f in sorted_files]
palette_f = plt.cm.viridis(np.linspace(0.3, 0.9, len(fnames_list)))
bars = ax.barh(fnames_list, fsizes_list, color=palette_f, edgecolor='#303050', lw=0.5)
for bar, sz in zip(bars, fsizes_list):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{sz:.1f} KB', va='center', color='white', fontsize=7)
ax.set_xlabel('File Size (KB)', color='#a0a0c0')
ax.set_title('Output File Sizes', color='white', fontsize=11)
ax.tick_params(colors='#a0a0c0', labelsize=7); ax.spines[:].set_color('#303050')
ax.set_xlim(0, max(fsizes_list) * 1.25)
ax2 = axes[1]; ax2.set_facecolor(PANEL_BG)
# Works per role in ego graph
role_counts_d3 = {}
for n_data in d3_main_nodes:
    r = n_data.get('role','other')
    role_counts_d3[r] = role_counts_d3.get(r, 0) + 1
role_colors_d3 = {'sailor':'#ffdd00','sailor_work':ORANGE,'collaborator':BLUE,
                  'influence_source':PURPLE,'new_gen_artist':'#e9c46a','other':'#404060'}
rc2_labels = list(role_counts_d3.keys()); rc2_vals = list(role_counts_d3.values())
rc2_cols = [role_colors_d3.get(r,'#bab0ac') for r in rc2_labels]
bars2 = ax2.bar(rc2_labels, rc2_vals, color=rc2_cols, edgecolor='#303050', lw=0.5)
for bar, cnt in zip(bars2, rc2_vals):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             str(cnt), ha='center', color='white', fontsize=9)
ax2.set_title(f'd3_main_graph.json node roles\n({len(d3_main_nodes)} nodes, {len(d3_main_edges)} edges)',
              color='white', fontsize=11)
ax2.set_ylabel('Count', color='#a0a0c0'); ax2.tick_params(colors='#a0a0c0', axis='x', rotation=15); ax2.spines[:].set_color('#303050')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/d3_export_summary.png', dpi=120, bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
print('  Saved d3_export_summary.png')

# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('PREPROCESSING COMPLETE')
print('='*60)
print(f'd3_main_graph.json:  {len(d3_main_nodes)} nodes, {len(d3_main_edges)} edges')
print(f'd3_timeline.json:    {len(timeline_records)} works, {len(decade_agg)} decades')
print(f'\nOutput directory: {os.path.abspath(OUTPUT_DIR)}')
print('\nAll output files:')
for fname in sorted(os.listdir(OUTPUT_DIR)):
    fpath = os.path.join(OUTPUT_DIR, fname)
    size_kb = os.path.getsize(fpath) / 1024
    print(f'  {fname:50s} {size_kb:8.1f} KB')
print(f'\n✓ Open output/index.html in a browser (via a local server) to view the dashboard.')
print('  e.g.:  python -m http.server 8080  (then visit http://localhost:8080/output/)')
