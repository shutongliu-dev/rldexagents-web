"""Build the local RLDexAgents research report from audited, bundled evidence.
Run with the project's lab51 Python (numpy, matplotlib, markdown, Pillow).
Does not run simulations, modify checkpoints, or rewrite the older supplement.
"""
from pathlib import Path
from site_assets import add_site_icons
from representative_viewer import build_viewer, embed_viewer
import json,re,html,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch
import markdown
from report_code_blocks import style_code_blocks
ROOT=Path(__file__).resolve().parent
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':9,'legend.fontsize':8,'svg.fonttype':'none','pdf.fonttype':42,'figure.facecolor':'white','savefig.facecolor':'white'})
colors=['#263746','#26756b','#b27835','#77678d','#b34d56','#628eaa']
def read(p):return json.loads((ROOT/p).read_text())
def save(fig,name):
 for ext in ['png','svg','pdf']:fig.savefig(FIG/f'{name}.{ext}',dpi=180,bbox_inches='tight',pad_inches=.12)
 plt.close(fig)
def panel(ax,xy,w,h,title,body,color=colors[0]):
 x,y=xy;ax.add_patch(Rectangle((x,y),w,h,fc='white',ec=color,lw=1.2));ax.text(x+w/2,y+h*.73,title,ha='center',va='center',weight='bold',fontsize=10,color=color);ax.text(x+w/2,y+h*.32,body,ha='center',va='center',fontsize=8.5,linespacing=1.5)
def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color='#555',lw=1))
# Four main figures: mechanism, representation, interfaces, and recorded execution.
import subprocess
from matplotlib.gridspec import GridSpec
from PIL import Image
# 1. User-supplied method figure: preserve the original PDF and render locally.
shutil.copy2(ROOT/'method.pdf', FIG/'method_overview.pdf')
subprocess.run(['pdftoppm','-scale-to','3500','-png','-singlefile',str(ROOT/'method.pdf'),str(FIG/'method_overview')],check=True)
subprocess.run(['pdftocairo','-svg',str(ROOT/'method.pdf'),str(FIG/'method_overview.svg')],check=True)
# 2. One large manifold view, using the interactive camera and source palette.
from matplotlib.offsetbox import OffsetImage, AnnotationBbox, TextArea, VPacker
from matplotlib.lines import Line2D
M=read('data/manifold.json'); method=M['methods']['link_near_and_distance_joint'];coords=np.asarray(method['coords']);meta=M['metadata']
# Read the browser palette directly so the paper figure cannot silently use a different mapping.
viewer=(ROOT/'manifold.html').read_text()
palette_block=re.search(r"datasetColors=(\{.*?\}),lineageColors=",viewer).group(1)
dataset_colors=dict(re.findall(r"'([^']+)':'(#[0-9a-fA-F]+)'",palette_block))
yaw,pitch=.72,.42
cy,sy,cp,sp=np.cos(yaw),np.sin(yaw),np.cos(pitch),np.sin(pitch)
def project_points(v):
 v=np.asarray(v);x,y,z=v[...,0],v[...,1],v[...,2];xx=cy*x+sy*z;zz=-sy*x+cy*z
 yy=cp*y-sp*zz;depth=sp*y+cp*zz;scale=.72/(2.7-depth*.4)
 return np.stack((xx*scale,yy*scale,depth),axis=-1)
projected=project_points(coords);order=np.argsort(projected[:,2])
f=plt.figure(figsize=(12,8.5));ax=f.add_axes([.035,.12,.93,.81]);ax.set_facecolor('#fdfaf4')
ax.scatter(projected[order,0],projected[order,1],s=9,c=[dataset_colors[meta[i][1]] for i in order],alpha=.62,edgecolors='none',rasterized=True,zorder=2)
# Equal scale preserves the viewer's screen-space geometry. Hand insets sit around, not over, the dense center.
span=max(np.ptp(projected[:,0]),np.ptp(projected[:,1]))
cx=(projected[:,0].min()+projected[:,0].max())/2;cy0=(projected[:,1].min()+projected[:,1].max())/2
ax.set_xlim(cx-span*.77,cx+span*.77);ax.set_ylim(cy0-span*.55,cy0+span*.55);ax.set_aspect('equal');ax.axis('off')
# The axis arrows are the same projected standardized PCA axes, not separate 2D coordinates.
origin=project_points([[0,0,0]])[0,:2]
for k,(name,c) in enumerate([('PC1','#b07a4e'),('PC2','#699268'),('PC3','#7796ad')]):
 v=np.zeros(3);v[k]=2.1;end=project_points([v])[0,:2]
 ax.annotate('',xy=end,xytext=origin,arrowprops=dict(arrowstyle='->',color=c,lw=1,alpha=.7),zorder=1)
 ax.text(end[0],end[1],name,fontsize=8,color=c,zorder=3)
# Each leader line ends at the exact selected medoid, rather than a cluster centroid or a hand-placed cluster region.
locations={0:(.27,.23),1:(.80,.78),2:(.90,.48),3:(.095,.46),4:(.78,.23),5:(.28,.79)}
audit=[]
for c in range(6):
 idx=int(method['medoids'][str(c)]);point=projected[idx,:2];source=meta[idx][1];color=dataset_colors[source]
 ax.scatter(*point,s=115,marker='o',facecolor='white',edgecolor='#202a31',linewidth=1.4,zorder=5)
 ax.scatter(*point,s=52,marker='o',facecolor=color,edgecolor='none',zorder=6)
 im=Image.open(ROOT/f'assets/poses/link_near_and_distance_joint/cluster_{c}.png').convert('RGB');pix=np.asarray(im);yy,xx=np.where(pix.min(axis=2)<225)
 im=im.crop((max(0,int(xx.min())-10),max(0,int(yy.min())-10),min(im.width,int(xx.max())+11),min(im.height,int(yy.max())+11)))
 im.thumbnail((100,100),Image.Resampling.LANCZOS)
 label=TextArea(f'C{c}',textprops=dict(fontsize=12,weight='bold',ha='center',color='#202a31'))
 box=VPacker(children=[OffsetImage(np.asarray(im),zoom=1),label],align='center',pad=0,sep=3)
 annotation=AnnotationBbox(box,point,xybox=locations[c],xycoords='data',boxcoords='axes fraction',frameon=True,
  bboxprops=dict(boxstyle='round,pad=0.3',fc='white',ec='#d6d2c8',lw=.7),
  arrowprops=dict(arrowstyle='-',color='#59626a',lw=1.15,connectionstyle='arc3,rad=0',shrinkA=5,shrinkB=7),zorder=7)
 ax.add_artist(annotation)
 audit.append(dict(cluster=c,medoid_index=idx,key=meta[idx][0],dataset=source,source_color=color,pca_coordinates=coords[idx].tolist(),projected_xy=point.tolist()))
f.text(.5,.965,'Hand–object manifold and representative hand configurations',ha='center',fontsize=16,weight='bold')
f.text(.5,.935,'6,241 HOI configurations · link-near-and-distance representation · interactive-view source colors',ha='center',fontsize=9,color='#555')
handles=[Line2D([0],[0],marker='o',ls='',markersize=6,color=dataset_colors[s],label=s) for s in M['datasets']]
f.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.055),ncol=4,frameon=False,fontsize=9,handletextpad=.35,columnspacing=1.4)
f.text(.5,.025,'Callouts point to observed medoids in the projected 3D space; geometric groups do not establish equivalent grasp functions.',ha='center',fontsize=8.5,color='#555')
save(f,'main02_manifold')
(ROOT/'data/figure2_medoid_annotations.json').write_text(json.dumps({'method':'link_near_and_distance_joint','camera':{'yaw':yaw,'pitch':pitch},'source_palette':dataset_colors,'medoids':audit},indent=2))

# 3. An open, transparent diagram that blends into the report page.
def draw_distillation_figure():
 with plt.rc_context({'svg.fonttype':'path'}):
  f=plt.figure(figsize=(12,4.25))
  ax=f.add_axes([0,0,1,1]);ax.set(xlim=(0,12),ylim=(0,4.25));ax.axis('off')
  ink,muted,rule,accent='#1b1b1b','#68645d','#d6cec1','#36766d'
  def text(x,y,value,size=10,color=ink,weight='normal',serif=False):
   return ax.text(x,y,value,ha='center',va='center',fontsize=size,color=color,weight=weight,
                  fontfamily='STIXGeneral' if serif else 'DejaVu Sans',linespacing=1.65)
  def connector(a,b):
   ax.add_patch(FancyArrowPatch(a,b,arrowstyle='->',mutation_scale=10,color='#a49b8b',lw=.85))
  stages=[(1.95,'01','Privileged teacher','Object state + future reference','Labels student-visited states'),
          (6,'02','Online learning','Teacher-action imitation + PPO','Teacher labels + task rewards'),
          (10.05,'03','Student rollout','Student executes finger actions','Contacts produce the next state')]
  for x,n,title,line1,line2 in stages:
   text(x,4.02,n,size=8,color=muted)
   text(x,3.72,title,size=14,weight='bold',serif=True)
   text(x,3.39,line1,size=9.5)
   text(x,3.12,line2,size=9,color=muted)
  connector((3.55,3.7),(4.4,3.7));connector((7.6,3.7),(8.45,3.7))
  ax.plot([.35,11.65],[2.77,2.77],color=rule,lw=.7)
  text(6,2.52,'FOUR ALTERNATIVE COMMANDS',size=8,color=muted)
  commands=[('Cluster','C0–C5','Configuration family'),('Joint','22 joint targets','Hand posture'),
            ('Fingertip','5 × 3 palm-frame targets','Endpoint geometry'),('Hybrid','Cluster + fingertips','Prior + geometry')]
  for x,(title,payload,meaning) in zip([1.5,4.5,7.5,10.5],commands):
   text(x,2.13,title,size=14,color=accent,weight='bold',serif=True)
   text(x,1.78,payload,size=10)
   text(x,1.51,meaning,size=9,color=muted)
   ax.plot([x,x],[1.24,1.05],color=rule,lw=.8)
  ax.plot([1.5,10.5],[1.05,1.05],color=rule,lw=.8)
  connector((6,1.05),(6,.81))
  text(6,.61,'Shared student architecture',size=13,weight='bold',serif=True)
  text(6,.27,'8-frame hand feedback + command / phase  →  recurrent policy  →  22 finger actions',size=10)
  for ext in ['png','svg','pdf']:
   f.savefig(FIG/f'main03_distillation.{ext}',dpi=180,bbox_inches='tight',pad_inches=.08,transparent=True)
  plt.close(f)
draw_distillation_figure()
# 4. Color teacher interactions, using the same exact-reference display media.
def draw_execution_figure():
 from matplotlib.patches import FancyBboxPatch
 demos=read('data/cluster_teacher_demos.json')
 with plt.rc_context({'svg.fonttype':'path'}):
  f=plt.figure(figsize=(12,8.5))
  flow=f.add_axes([0,.82,1,.18]);flow.set(xlim=(0,12),ylim=(0,1));flow.axis('off')
  stages=[(1.95,'01','Skill call','Select command and phase'),
          (6,'02','Tactile runtime','Feedback → student → finger targets'),
          (10.05,'03','Execution feedback','Contact status + object verification')]
  for x,n,title,body in stages:
   flow.text(x,.84,n,ha='center',fontsize=8,color='#807665',fontfamily='DejaVu Sans')
   flow.text(x,.57,title,ha='center',fontsize=15,weight='bold',fontfamily='STIXGeneral',color='#1b1b1b')
   flow.text(x,.28,body,ha='center',fontsize=9.5,color='#68645d',fontfamily='DejaVu Sans')
  for a,b in [(3.6,4.4),(7.6,8.4)]:
   flow.add_patch(FancyArrowPatch((a,.61),(b,.61),arrowstyle='->',mutation_scale=10,color='#a49b8b',lw=.85))
  flow.plot([.3,11.7],[.07,.07],color='#d6cec1',lw=.7)
  lefts=[.025,.355,.685]
  for j,d in enumerate(demos):
   row,col=divmod(j,3);left=lefts[col];bottom=.46 if row==0 else .075
   media=d.get('display_media',d)
   im=Image.open(ROOT/media['snapshots']['lift']).convert('RGB')
   # Keep the target interaction central; remove peripheral parallel scenes.
   w,h=im.size;im=im.crop((round(.125*w),round(.117*h),round(.875*w),round(.867*h)))
   ax=f.add_axes([left,bottom,.29,.307]);ax.axis('off')
   image=ax.imshow(im)
   clip=FancyBboxPatch((0,0),1,1,boxstyle='round,pad=0,rounding_size=0.025',
                       transform=ax.transAxes,facecolor='none',edgecolor='#d6cec1',lw=.65)
   ax.add_patch(clip);image.set_clip_path(clip)
   ax.set_title(f'C{d["final_cluster"]}  /  {d["object"]}',fontsize=12,fontfamily='STIXGeneral',
                weight='bold',loc='left',pad=10,color='#1b1b1b')
  f.text(.5,.022,'Selected Isaac Sim teacher interactions · one example per cluster · not agent-level success statistics',
         ha='center',fontsize=9,color='#807665',fontfamily='DejaVu Sans')
  for ext in ['png','svg','pdf']:
   f.savefig(FIG/f'main04_demonstrations.{ext}',dpi=180,bbox_inches='tight',pad_inches=.08,transparent=True)
  plt.close(f)
draw_execution_figure()

# Build HTML and publication-style LaTeX from the same Markdown.
md=(ROOT/'RLDexAgents_Technical_Report.md').read_text();equations=[]
def eq_html(m):
 s=m.group(1).strip();equations.append(s); idx=len(equations)
 display=s.replace(r'\text{',r'\mathrm{');display=re.sub(r'\\(mathcal|mathbb) ([A-Za-z])',r'\\\1{\2}',display)
 with plt.rc_context({'mathtext.fontset':'stix','svg.fonttype':'path'}):
  f=plt.figure(figsize=(11,.65));f.text(.5,.5,'$'+display+'$',ha='center',va='center',fontsize=14,fontfamily='STIXGeneral',color='#1b1b1b')
  f.savefig(FIG/f'main_equation_{idx:02d}.svg',bbox_inches='tight',pad_inches=.12,transparent=True);plt.close(f)
 return f'\n<div class="equation"><img src="figures/main_equation_{idx:02d}.svg" alt="{html.escape(s)}"></div>\n'
hmd=re.sub(r'\$\$(.*?)\$\$',eq_html,md,flags=re.S)
# Citations use local bibliography anchors, not network scripts.
hmd=re.sub(r'\[@(\w+)\]',lambda m:f'<a class="citation" href="#ref-{m[1]}">[{m[1]}]</a>',hmd)
body=markdown.markdown(hmd,extensions=['tables','fenced_code','toc'],extension_configs={'toc':{'permalink':False}})
body=style_code_blocks(body)
body=re.sub(r'<p><img alt="(Figure [^"]+)" src="([^"]+)" /></p>',lambda m:f'<figure><img loading="lazy" src="{m[2].replace(".png",".svg")}" alt="{m[1]}"><figcaption>{m[1]}</figcaption></figure>',body)
# Only figures produced here have SVG versions; embedded photos are inside their figure SVG.
for key in ['santello1998','ross2011','schulman2017','pinto2018','qi2023','ichter2023']:
 body=body.replace(f'<li><a class="citation" href="#ref-{key}">',f'<li id="ref-{key}"><a class="citation" href="#ref-{key}">')
# Optional exploration does not interrupt the four-figure main narrative.
explorer='<section class="interactive-evidence" id="interactive-manifold"><h3>Explore the hand manifold</h3><p>Rotate the 3D view, color points by dataset source, and switch source filters to compare coverage. <b>OakInk (wrist-adapted)</b> contains 68 OakInk-v2 right-hand references with reconstructed pre-contact wrist motion.</p><iframe src="manifold.html" title="Interactive hand-object manifold by dataset source" loading="eager"></iframe><p><a href="manifold.html" target="_blank" rel="noopener">Open full-size 3D viewer</a> · <a href="pose_hoi_manifold.html">Pose and replay gallery</a> · <a href="data/wrist_adapted_source_audit.json">Source audit</a></p></section>'
# Keep source exploration visible at the top, before the report abstract.
tldr='<h2 id="tldr">TL;DR</h2><div class="tldr"><p><em>RLDexAgents</em> turns diverse human and robot hand motions into an extensible toolkit of agent-callable dexterous skills. Pose banks organize candidates, RL teachers provide physically executed demonstrations, and command-conditioned students use local feedback for closed-loop finger control. Experiments show better geometric coverage and identify contact establishment and the teacher–student performance gap as key challenges for reliable skill reuse.</p></div>'
body=body.replace('<h2 id="abstract">',explorer+tldr+'<h2 id="abstract">')
demos=read('data/cluster_teacher_demos.json');videos=''
for d in demos:
 display=d.get('display_media',d)
 videos+=f'<div class="cluster-rollout"><h4>C{d["final_cluster"]} · {html.escape(d["object"])}</h4><video controls playsinline preload="none" poster="{display["poster"]}"><source src="{display["video"]}" type="video/mp4"></video><p>Isaac Sim teacher · lift: {"yes" if d["recorded_rollout_lift_success"] else "no"} · tail stability: {d["tail_stable_fraction"]:.0%}<br><small>{html.escape(d["key"])}</small></p><a href="{d["trajectory_npz"]}" download>Recorded trajectory</a></div>'
player=f'<details class="demo-playback" open><summary>Cluster demonstrations · six Isaac Sim teacher rollouts</summary><p>Current C0–C5, one selected rollout each. Teacher controls fingers; wrist follows reference. Stable tail HOLD requires ≥2 cm lift and at least two target-contacting fingertips ≥0.5 N in ≥95% of the final 30 ticks. This is not a five-second HOLD or an agent success-rate test.</p><div class="video-grid">{videos}</div><p><a href="pose_hoi_manifold.html#demos">Snapshots, forces and manifold locations</a></p></details>'
body=body.replace('<h2 id="6-experiments-and-key-findings">',player+'<h2 id="6-experiments-and-key-findings">')
heads=re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',body)
nav='<li><a href="#interactive-manifold">Interactive Manifold</a></li>'+''.join(f'<li><a href="#{a}">{b}</a></li>' for a,b in heads)
# Reuse the DEX-X hero, quick links, section-label and media structure.
body=re.sub(r'<h1.*?</h1>\s*<p>.*?</p>\s*<p>.*?</p>', '', body, count=1, flags=re.S)
body=re.sub(r'<h2 id="([^"]+)">',r'<h2 class="tagline" id="\1">',body)
body=body.replace('<figcaption>','<figcaption class="figure-caption">')
overview=re.search(r'<figure><img[^>]+src="figures/method_overview.svg".*?</figure>',body,re.S)
herofigure=overview.group(0) if overview else ''
if overview:
 body=body.replace(herofigure,'',1)
 herofigure=herofigure.replace('<img ', '<a href="method.pdf" target="_blank" rel="noopener" title="Open original method PDF"><img ',1).replace('<figcaption', '</a><figcaption',1)
links=[('RLDexAgents_Technical_Report.md','Report'),('RLDexAgents_Technical_Report.tex','LaTeX'),('method.pdf','Method Figure'),('supplementary_report.html','Supplementary'),('pose_hoi_manifold.html','Interactive Gallery'),('references.bib','References'),('open_questions.md','Open Questions')]
quick=''.join(f'<a class="link-pill" href="{url}">{label}</a>' for url,label in links)
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RLDexAgents — Technical Report</title><meta name="description" content="Hand motion structure, executable skill distillation and an extensible agentic dexterous toolkit."><link rel="stylesheet" href="assets/template-fonts.css"><link rel="stylesheet" href="assets/dexx-template.css"><link rel="stylesheet" href="assets/rldex_report.css"></head><body><nav class="toc" aria-label="Report contents"><h3>Content</h3><hr><ul>{nav}</ul></nav><main class="main-content"><header class="report-hero"><h1 class="hero-text">RLDexAgents</h1><div class="sub-hero-text">An Extensible Dexterous Skill Toolkit for LLM Agents</div><p class="report-subtitle">From Hand Pose Manifolds to Interface-Conditioned Skill Distillation and Agentic Manipulation</p><div class="venue">Technical Report · 27 October 2026</div><div class="authors">Sharpa right-hand implementation · Audited experiment records</div>{herofigure}<div class="quick-links" hidden>{quick}</div></header><article class="section">{body}</article><footer class="footer">Audited project evidence · 27 October 2026.<br>Local figures and media · <a href="production_checks.md">Production notes</a><br>Page template adapted from the local DEX-X project page.</footer></main></body></html>'''
build_viewer(ROOT)
(ROOT/'index.html').write_text(add_site_icons(embed_viewer(page)),encoding='utf-8')

# Minimal deterministic Markdown-to-LaTeX renderer for this report's constructs.
def esc(s):
 trans={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','≥':r'$\geq$','≤':r'$\leq$','≈':r'$\approx$','±':r'$\pm$','→':r'$\rightarrow$','×':r'$\times$','−':'-','–':'--','—':'---','’':"'",'“':'``','”':"''",'·':r'$\cdot$','°':r'$^\circ$'}
 return ''.join(trans.get(c,c) for c in s)
def inline(s):
 pats=re.compile(r'\[@(\w+)\]|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|\*([^*]+)\*');out='';last=0
 for m in pats.finditer(s):
  out+=esc(s[last:m.start()]);g=m.groups()
  if g[0]:out+=r'\citep{'+g[0]+'}'
  elif g[1]:out+=r'\texttt{'+esc(g[1])+'}'
  elif g[2]:out+=r'\href{'+g[3].replace('%',r'\%').replace('#',r'\#')+'}{'+esc(g[2])+'}'
  elif g[4]:out+=r'\textbf{'+esc(g[4])+'}'
  else:out+=r'\emph{'+esc(g[5])+'}'
  last=m.end()
 return out+esc(s[last:])
tex=[r'''\documentclass[10pt,twocolumn]{article}
\usepackage[a4paper,margin=0.72in,columnsep=0.25in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{mathptmx,amsmath,amssymb,graphicx,booktabs,tabularx}
\usepackage[numbers,sort&compress]{natbib}
\usepackage{microtype,url}
\usepackage[colorlinks=true,allcolors=black]{hyperref}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}
\setlength{\parindent}{1em}
\setlength{\parskip}{0.15em}
\setlength{\textfloatsep}{12pt}
\title{RLDexAgents: An Extensible Dexterous Skill Toolkit for LLM Agents\\[5pt]\large From Hand Pose Manifolds to Interface-Conditioned Skill Distillation and Agentic Manipulation}
\author{Project technical report}
\date{Evidence audit: 27 October 2026}
\begin{document}
\maketitle
''']
lines=md.splitlines();i=0;in_list=False;eqid=0
while i<len(lines):
 line=lines[i]
 if line.startswith('## References'):break
 if line.startswith('# ') or line.startswith('*From Hand Pose') or line.startswith('Technical report ·'):i+=1;continue
 if line.startswith('```'):
  if in_list:tex.append(r'\end{itemize}');in_list=False
  i+=1;code=[]
  while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
  # Wide code block prevents long import lines overflowing a narrow column.
  tex.append('\\begin{figure*}[t]\n\\small\\begin{verbatim}\n'+'\n'.join(code)+'\n\\end{verbatim}\n\\caption*{Supported host-side command example.}\n\\end{figure*}');i+=1;continue
 if line.startswith('$$'):
  eq=line.strip('$');tex.append('\\[\n'+eq+'\n\\]');i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):
   cells=[x.strip() for x in lines[i].strip('|').split('|')]
   if not all(re.fullmatch(r'[:\- ]+',x) for x in cells):rows.append(cells)
   i+=1
  n=len(rows[0]);spec='l'+'X'*(n-1);t=['\\begin{table*}[t]','\\small','\\begin{tabularx}{\\textwidth}{@{}'+spec+'@{}}','\\toprule']
  for j,row in enumerate(rows):t.append(' & '.join(inline(x) for x in row)+r' \\'); j==0 and t.append(r'\midrule')
  t.extend([r'\bottomrule',r'\end{tabularx}']);k=i
  while k<len(lines) and not lines[k].strip():k+=1
  if k<len(lines) and lines[k].startswith('*Table '):
   cap=re.sub(r'^\*Table \d+\.\s*','',lines[k]).rstrip('*');t.append(r'\caption{'+inline(cap)+'}');i=k+1
  t.append(r'\end{table*}');tex.append('\n'.join(t));continue
 m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
 if m:
  label,path=m.groups();label=re.sub(r'^Figure \d+ — ','',label);path=path.replace('.png','.pdf')
  tex.append('\\begin{figure*}[t]\n\\centering\n\\includegraphics[width=\\textwidth,height=0.34\\textheight,keepaspectratio]{'+path+'}\n\\caption{'+inline(label)+'}\n\\end{figure*}');i+=1;continue
 if line.startswith('- '):
  if not in_list:tex.append(r'\begin{itemize}');in_list=True
  tex.append(r'\item '+inline(line[2:]));i+=1;continue
 if in_list and line.strip():tex.append(r'\end{itemize}');in_list=False
 if line.startswith('### '):
  title=re.sub(r'^\d+\.\d+\s*','',line[4:]);tex.append(r'\subsection{'+inline(title)+'}')
 elif line.startswith('## '):
  title=re.sub(r'^\d+\.\s*','',line[3:]);cmd='section*' if title.startswith(('Abstract','Supplementary','Executive','Appendix')) else 'section';tex.append('\\'+cmd+'{'+inline(title)+'}')
 elif line.strip():tex.append(inline(line))
 else:tex.append('')
 i+=1
if in_list:tex.append(r'\end{itemize}')
tex.extend([r'\bibliographystyle{plainnat}',r'\bibliography{references}',r'\end{document}'])
(ROOT/'RLDexAgents_Technical_Report.tex').write_text('\n'.join(tex))
print('Built four main figures,',len(equations),'equations, concise HTML and LaTeX')
