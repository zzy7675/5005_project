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
print(f'  Sailor ID={SAILOR_ID}  Works={len(sailor_work_ids)}  Collaborators={len(collaborator_ids)}')

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
# STEP 5 – Influence Network
# ══════════════════════════════════════════════════════════════════════════════
print('Step 5: Building influence network...')
IVY_ECHOES_NAMES = ['sailor shift','maya jensen','lila hartman','lilly hartman','jade thompson','sophie ramirez']
ivy_echoes_ids = {}
for _, row in nodes_df[nodes_df['type']=='Person'].iterrows():
    nl = str(row.get('name','')).lower(); sl = str(row.get('stage_name','')).lower()
    for ivy_name in IVY_ECHOES_NAMES:
        if ivy_name in nl or ivy_name in sl:
            ivy_echoes_ids[ivy_name] = int(row['node_id']); break

hop1_influenced_ids = {r['influenced_work_id'] for r in sailor_influences_others}
hop2_influenced_ids = set()
for work_id in hop1_influenced_ids:
    for src, _, attrs in G.in_edges(work_id, data=True):
        if attrs.get('type') in INFLUENCE_EDGE_TYPES:
            hop2_influenced_ids.add(src)
hop2_influenced_ids -= hop1_influenced_ids

def get_artists_of_works(work_ids):
    result = {}
    for wid in work_ids:
        artists = [src for src,_,attrs in G.in_edges(wid,data=True)
                   if attrs.get('type') in WORK_EDGE_TYPES and G.nodes[src].get('type') in ('Person','MusicalGroup')]
        result[wid] = artists
    return result

hop1_artists = get_artists_of_works(hop1_influenced_ids)
hop2_artists = get_artists_of_works(hop2_influenced_ids)
all_influenced_artist_ids = set()
for artists in hop1_artists.values(): all_influenced_artist_ids.update(artists)
for artists in hop2_artists.values(): all_influenced_artist_ids.update(artists)

influence_node_ids = ({SAILOR_ID} | sailor_work_ids | hop1_influenced_ids |
                      hop2_influenced_ids | all_influenced_artist_ids | set(ivy_echoes_ids.values()))
inf_subgraph = G.subgraph(influence_node_ids).copy()
for n in inf_subgraph.nodes():
    if n == SAILOR_ID:                      inf_subgraph.nodes[n]['role'] = 'sailor'
    elif n in sailor_work_ids:              inf_subgraph.nodes[n]['role'] = 'sailor_work'
    elif n in hop1_influenced_ids:          inf_subgraph.nodes[n]['role'] = 'hop1_influenced'
    elif n in hop2_influenced_ids:          inf_subgraph.nodes[n]['role'] = 'hop2_influenced'
    elif n in all_influenced_artist_ids:    inf_subgraph.nodes[n]['role'] = 'influenced_artist'
    elif n in set(ivy_echoes_ids.values()): inf_subgraph.nodes[n]['role'] = 'ivy_echoes'
    else:                                   inf_subgraph.nodes[n]['role'] = 'other'

inf_nodes = [{'id':n,**{k:safe_val(v) for k,v in attrs.items()}} for n,attrs in inf_subgraph.nodes(data=True)]
inf_edges = [{'source':u,'target':v,**{k:safe_val(v2) for k,v2 in attrs.items()}} for u,v,attrs in inf_subgraph.edges(data=True)]
with open(f'{OUTPUT_DIR}/influence_network.json','w',encoding='utf-8') as f:
    json.dump({'nodes':inf_nodes,'links':inf_edges,'ivy_echoes_ids':ivy_echoes_ids,'sailor_id':SAILOR_ID},f,ensure_ascii=False,default=str)
print(f'  Hop-1: {len(hop1_influenced_ids)}  Hop-2: {len(hop2_influenced_ids)}  Artists: {len(all_influenced_artist_ids)}')

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
indirect_of_influenced = of_artist_ids & all_influenced_artist_ids
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

# D3 Influence Network
d3_inf_nodes = []
for n, attrs in inf_subgraph.nodes(data=True):
    nt = attrs.get('type','unknown'); role = attrs.get('role','other')
    d3_inf_nodes.append({'id':n,'label':attrs.get('name',str(n)),'type':nt,'role':role,
        'color':NODE_COLORS_D3.get(nt,NODE_COLORS_D3['unknown']),'size':ROLE_SIZE.get(role,8),
        'genre':attrs.get('genre'),'notable':safe_val(attrs.get('notable')),
        'release_date':safe_val(attrs.get('release_date')),'notoriety_date':safe_val(attrs.get('notoriety_date')),
        'stage_name':attrs.get('stage_name')})
d3_inf_edges = []
for u,v,attrs in inf_subgraph.edges(data=True):
    et = attrs.get('type','unknown')
    d3_inf_edges.append({'source':u,'target':v,'type':et,'color':EDGE_COLORS_D3.get(et,EDGE_COLORS_D3['unknown'])})
with open(f'{OUTPUT_DIR}/d3_influence_network.json','w',encoding='utf-8') as f:
    json.dump({'nodes':d3_inf_nodes,'links':d3_inf_edges,'sailor_id':SAILOR_ID,
               'ivy_echoes_ids':ivy_echoes_ids,'node_color_legend':NODE_COLORS_D3,
               'edge_color_legend':EDGE_COLORS_D3},f,ensure_ascii=False,default=str)

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

# D3 Linkage
linkage_records = []
for work_id in sailor_work_ids:
    wa = G.nodes[work_id]; wn = wa.get('name',str(work_id)); wt = wa.get('type','unknown')
    for src,_,attrs in G.in_edges(work_id,data=True):
        et = attrs.get('type','unknown')
        if et in WORK_EDGE_TYPES:
            sa = G.nodes[src]
            linkage_records.append({'work_id':work_id,'work_name':wn,'work_type':wt,
                'connected_id':src,'connected_name':sa.get('name',str(src)),
                'connected_type':sa.get('type','unknown'),'edge_type':et,'direction':'upstream'})
    for _,tgt,attrs in G.out_edges(work_id,data=True):
        et = attrs.get('type','unknown')
        if et in ('RecordedBy','DistributedBy'):
            ta = G.nodes[tgt]
            linkage_records.append({'work_id':work_id,'work_name':wn,'work_type':wt,
                'connected_id':tgt,'connected_name':ta.get('name',str(tgt)),
                'connected_type':ta.get('type','unknown'),'edge_type':et,'direction':'downstream'})
        elif et in INFLUENCE_EDGE_TYPES:
            ta = G.nodes[tgt]
            linkage_records.append({'work_id':work_id,'work_name':wn,'work_type':wt,
                'connected_id':tgt,'connected_name':ta.get('name',str(tgt)),
                'connected_type':ta.get('type','unknown'),'edge_type':et,'direction':'influence_source'})
with open(f'{OUTPUT_DIR}/d3_linkage.json','w',encoding='utf-8') as f:
    json.dump({'sailor_id':SAILOR_ID,'sailor_work_ids':list(sailor_work_ids),'linkage':linkage_records},
              f,ensure_ascii=False,default=str)

# D3 OF Community — for context-sensitive bottom-right panel
# 1. OF artist debut timeline (year → count, pre/post 2028)
of_debut_by_year = defaultdict(lambda: {'pre_sailor':0,'post_sailor':0,'collab':0,'new_gen':0})
for _, row in of_artist_df.iterrows():
    yr = row.get('first_of_work_year')
    if yr is None or pd.isna(yr): continue
    yr = int(yr)
    bucket = 'post_sailor' if yr >= SAILOR_BREAKTHROUGH_YEAR else 'pre_sailor'
    of_debut_by_year[yr][bucket] += 1
    if row.get('direct_collab_with_sailor'): of_debut_by_year[yr]['collab'] += 1
    if row.get('new_generation'): of_debut_by_year[yr]['new_gen'] += 1

# 2. Genre spread from OF (top genres that reference OF works, by year)
genre_spread_by_year = defaultdict(lambda: defaultdict(int))
if not of_spread_df.empty:
    for _, row in of_spread_df.iterrows():
        yr = row.get('referencing_year')
        genre = row.get('referencing_genre','')
        if yr and genre:
            try: genre_spread_by_year[int(float(str(yr)))][genre] += 1
            except: pass

top_spread_genres = []
if not of_spread_df.empty:
    top_spread_genres = of_spread_df['referencing_genre'].value_counts().head(8).index.tolist()

# 3. Influence sources breakdown (what influenced Sailor, by decade + genre)
infl_src_df = pd.DataFrame(sailor_influenced_by)
infl_src_by_decade = defaultdict(lambda: defaultdict(int))
if not infl_src_df.empty:
    for _, row in infl_src_df.iterrows():
        yr = row.get('influenced_by_year')
        genre = row.get('influenced_by_genre','') or 'Unknown'
        etype = row.get('edge_type','')
        if yr:
            try:
                dec = int(float(str(yr))) // 10 * 10
                infl_src_by_decade[dec][genre] += 1
            except: pass

# 4. Collaborator summary (for Q2 panel)
collab_df = pd.DataFrame(collab_edges)
collab_summary = []
if not collab_df.empty:
    for cid in collaborator_ids:
        cname = G.nodes[cid].get('name','')
        ctype = G.nodes[cid].get('type','')
        works = collab_df[collab_df['collaborator_id']==cid]['work_name'].tolist()
        etypes = collab_df[collab_df['collaborator_id']==cid]['edge_type'].tolist()
        collab_summary.append({
            'id': cid, 'name': cname, 'type': ctype,
            'works': list(set(works)), 'edge_types': list(set(etypes)),
            'work_count': len(set(works))
        })
    collab_summary.sort(key=lambda x: -x['work_count'])

d3_of_community = {
    'sailor_id': SAILOR_ID,
    'sailor_breakthrough_year': SAILOR_BREAKTHROUGH_YEAR,
    'total_of_artists': len(of_artist_ids),
    'total_of_works': len(of_work_ids),
    'new_gen_count': len(new_gen_artist_ids),
    'direct_collab_count': len(direct_of_collabs),
    'genre_spread_count': len(of_spread_df),
    # OF artist debut by year
    'of_debut_by_year': [
        {'year': yr, **counts}
        for yr, counts in sorted(of_debut_by_year.items())
    ],
    # Genre spread by year (top genres)
    'genre_spread_by_year': [
        {'year': yr, **{g: cnt for g, cnt in genres.items()}}
        for yr, genres in sorted(genre_spread_by_year.items())
    ],
    'top_spread_genres': top_spread_genres,
    # Influence sources by decade
    'infl_src_by_decade': [
        {'decade': dec, 'genres': dict(genres)}
        for dec, genres in sorted(infl_src_by_decade.items())
    ],
    # Collaborator summary
    'collaborators': collab_summary,
    # Top genres influenced by OF (total)
    'genres_influenced': of_spread_df['referencing_genre'].value_counts().head(10).to_dict() if not of_spread_df.empty else {}
}

with open(f'{OUTPUT_DIR}/d3_of_community.json','w',encoding='utf-8') as f:
    json.dump(d3_of_community, f, ensure_ascii=False, default=str)

# D3 Sailor Influences — Q1: Who influenced Sailor, ranked + over time
infl_df = pd.DataFrame(sailor_influenced_by)

# Enrich with Sailor's work decade
sailor_work_decade = {}
for _, row in work_rows.iterrows():
    wid = int(row['node_id'])
    dec = row.get('decade')
    if dec is not None and not pd.isna(dec):
        sailor_work_decade[wid] = int(dec)

ranked_sources = []
if not infl_df.empty:
    # Rank by how many of Sailor's works reference each source
    src_counts = infl_df.groupby(['influenced_by_id','influenced_by_name','influenced_by_genre','influenced_by_type']).size().reset_index(name='ref_count')
    src_counts = src_counts.sort_values('ref_count', ascending=False)
    for _, row in src_counts.iterrows():
        ranked_sources.append({
            'id': safe_val(row['influenced_by_id']),
            'name': row['influenced_by_name'],
            'genre': row['influenced_by_genre'],
            'type': row['influenced_by_type'],
            'ref_count': int(row['ref_count'])
        })

# Influence by decade of Sailor's referencing work
infl_by_sailor_decade = defaultdict(lambda: defaultdict(int))
if not infl_df.empty:
    for _, row in infl_df.iterrows():
        wid = safe_val(row.get('sailor_work_id'))
        genre = row.get('influenced_by_genre','') or 'Unknown'
        etype = row.get('edge_type','')
        dec = sailor_work_decade.get(wid)
        if dec is not None:
            infl_by_sailor_decade[dec][genre] += 1

# Edge type breakdown
edge_type_counts_infl = {}
if not infl_df.empty:
    for et, cnt in infl_df['edge_type'].value_counts().items():
        edge_type_counts_infl[et] = int(cnt)

d3_sailor_influences = {
    'sailor_id': SAILOR_ID,
    'total_influence_refs': len(infl_df),
    'ranked_sources': ranked_sources[:40],  # top 40
    'infl_by_sailor_decade': [
        {'decade': dec, 'genres': dict(genres)}
        for dec, genres in sorted(infl_by_sailor_decade.items())
    ],
    'edge_type_counts': edge_type_counts_infl
}
with open(f'{OUTPUT_DIR}/d3_sailor_influences.json', 'w', encoding='utf-8') as f:
    json.dump(d3_sailor_influences, f, ensure_ascii=False, default=str)
print(f'  d3_sailor_influences.json: {len(ranked_sources)} ranked sources, {len(infl_by_sailor_decade)} decades')

# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('PREPROCESSING COMPLETE')
print('='*60)
print(f'd3_main_graph.json:        {len(d3_main_nodes)} nodes, {len(d3_main_edges)} edges')
print(f'd3_influence_network.json: {len(d3_inf_nodes)} nodes, {len(d3_inf_edges)} edges')
print(f'd3_timeline.json:          {len(timeline_records)} works, {len(decade_agg)} decades')
print(f'd3_linkage.json:           {len(linkage_records)} linkage records')
print(f'\nOutput directory: {os.path.abspath(OUTPUT_DIR)}')
print('\nAll output files:')
for fname in sorted(os.listdir(OUTPUT_DIR)):
    fpath = os.path.join(OUTPUT_DIR, fname)
    size_kb = os.path.getsize(fpath) / 1024
    print(f'  {fname:50s} {size_kb:8.1f} KB')
print(f'\n✓ Open output/index.html in a browser (via a local server) to view the dashboard.')
print('  e.g.:  python -m http.server 8080  (then visit http://localhost:8080/output/)')
