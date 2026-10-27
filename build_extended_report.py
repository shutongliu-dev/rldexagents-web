"""Build the local RLDexAgents research report from audited, bundled evidence.
Run with the project's lab51 Python (numpy, matplotlib, markdown, Pillow).
Does not run simulations, modify checkpoints, or rewrite the older supplement.
"""
from pathlib import Path
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
# Figure 1: a mechanism diagram, not an empirical result.
f,ax=plt.subplots(figsize=(10,3));ax.set(xlim=(0,10),ylim=(0,3));ax.axis('off')
items=[('Motion data','Human HOI / robot\nSource + parent identity'),('Pose analysis','PCA / FK / proximity\nSource-balanced coverage'),('Pose bank','Observed representatives\nRetrieval + provenance'),('RL teachers','Privileged reference input\nPhysical rollout validation')]
for i,(t,b) in enumerate(items):panel(ax,(i*2.55,.0+1.65),2.3,1.05,t,b); i and arrow(ax,((i-1)*2.55+2.3,2.17),(i*2.55,2.17))
for x,t,b in [(0,'Agent execution','High-level choice / arm motion\nHand feedback at 30 Hz'),(3.6,'Skill registry','Command + checkpoint\nRuntime + outcome metadata'),(7.2,'Distillation','Successful demonstrations\nStudent-visited state labels')]:panel(ax,(x,.05),2.65,1.05,t,b,colors[1])
arrow(ax,(9.0,1.65),(8.55,1.1));arrow(ax,(7.2,.57),(6.25,.57));arrow(ax,(3.6,.57),(2.65,.57))
ax.text(5,1.37,'OFFLINE STRUCTURE AND PHYSICAL LEARNING  →  ONLINE TOOL EXECUTION',ha='center',fontsize=8,color='#666');save(f,'fig01_overview')
# Figure 2: original numeric results.
d=read('evidence/E01_pose_bank/summary.json');f,axs=plt.subplots(1,3,figsize=(11,3.05))
for i,(k,label) in enumerate([('sharpa_all_limit_valid','Sharpa: all'),('sharpa_hoi_limit_valid','Sharpa: HOI'),('sharpadex_free_hand','Sharpa: freehand'),('human_keypoints_60d','Human: landmarks')]):
 v=np.cumsum(d['pca_cohort_explained_variance_ratio'][k]);axs[0].plot(np.arange(1,len(v)+1),v*100,label=label,color=colors[i])
axs[0].axhline(95,color='#aaa',ls=':',lw=1);axs[0].set(xlim=(1,22),ylim=(40,101),xlabel='Number of components',ylabel='Cumulative variance (%)',title='(a) Different representation spaces');axs[0].legend(fontsize=7,loc='lower right')
for i,(m,label) in enumerate([('random','Random'),('joint_kmeans_22d','Joint KMeans'),('pca_kmeans_14d','PCA14 + KMeans'),('pca_kmedoids_14d','PCA14 + medoids')]):
 rows=sorted([x for x in d['bank_metrics'] if x['method']==m],key=lambda x:x['bank_size']);axs[1].plot([x['bank_size'] for x in rows],[x['source_macro_median_joint_rmse_rad'] for x in rows],'-o',ms=3,label=label,color=colors[i])
axs[1].set(xscale='log',xlabel='Bank size (log scale)',ylabel='Macro-median joint RMS (rad)',title='(b) Coverage improves with bank size');axs[1].set_xticks([6,12,24,48,96,192],labels=['6','12','24','48','96','192']);axs[1].legend(fontsize=7)
rs=d['reconstruction'];axs[2].plot([x['dimensions'] for x in rs],[x['fingertip_fk_error_mm']['mean'] for x in rs],'-o',color=colors[1],label='Mean');axs[2].plot([x['dimensions'] for x in rs],[x['fingertip_fk_error_mm']['p95'] for x in rs],'-o',color=colors[2],label='95th percentile');axs[2].set(xlabel='Reconstruction components',ylabel='Fingertip FK error (mm)',title='(c) Variance is not precision');axs[2].legend();f.tight_layout(w_pad=2);save(f,'fig02_pose_analysis')
# Figure 3.
f,ax=plt.subplots(figsize=(10,3.1));ax.set(xlim=(0,10),ylim=(0,3.1));ax.axis('off')
panel(ax,(0,1.8),2.6,1.1,'Reference teacher','Hand / object / wrist state\nSix future reference samples');panel(ax,(3.5,1.8),2.8,1.1,'Teacher action labels','Original teacher observations\nEvaluate at visited simulator state');panel(ax,(7.2,1.8),2.6,1.1,'Mixed optimization','Teacher imitation + PPO\nPrivileged training critic');arrow(ax,(2.6,2.35),(3.5,2.35));arrow(ax,(6.3,2.35),(7.2,2.35))
panel(ax,(0,.05),2.6,1.1,'Deployable feedback','Eight frames: joints / velocities\nPrevious actions / fingertip forces',colors[1]);panel(ax,(3.5,.05),2.8,1.1,'Command-conditioned student','Fixed payload + phase + age\nFrame MLP → GRU → action head',colors[1]);panel(ax,(7.2,.05),2.6,1.1,'Closed-loop hand control','22 normalized finger actions\nDecode / smooth / joint limits',colors[1]);arrow(ax,(2.6,.6),(3.5,.6));arrow(ax,(6.3,.6),(7.2,.6));arrow(ax,(8.5,1.8),(5.6,1.15));arrow(ax,(8.5,1.15),(5.7,1.8));ax.text(4.9,1.5,'Student controls the rollout; teacher labels its visited states',ha='center',fontsize=8);save(f,'fig03_distillation')
# Figure 4.
f,ax=plt.subplots(figsize=(10,2.7));ax.set(xlim=(0,10),ylim=(0,2.7));ax.axis('off')
for i,(t,b) in enumerate([('Cluster','6-way ID\n117D / frame'),('Joint','22 joint targets\n133D / frame'),('Fingertip','5 × 3 palm keypoints\n126D / frame'),('Hybrid','Cluster + keypoints\n132D / frame')]):panel(ax,(i*2.55,1.45),2.3,1.05,t,b,colors[i])
panel(ax,(1.15,.05),7.7,.9,'Shared control backbone','107D hand feedback + command + phase/age → eight-frame GRU → 22 joint actions');
for i in range(4):arrow(ax,(i*2.55+1.15,1.45),(i*2.0+2,.95))
save(f,'fig04_interfaces')
# Figure 5.
f,axs=plt.subplots(1,2,figsize=(9.8,3.1),gridspec_kw={'width_ratios':[1.45,1]});ms=['teacher','cluster','joint','fingertip','hybrid'];stats=[read(f'evidence/E07_interfaces/eval_{m}_test/summary.json')['summary']['overall'] for m in ms];x=np.arange(5)
for k,(field,label) in enumerate([('lift_success','Lift'),('hold_1s_success','HOLD 1 s'),('hold_5s_success','HOLD 5 s')]):
 vals=[v[field] for v in stats];axs[0].bar(x+(k-1)*.24,np.array(vals)/68*100,.23,color=colors[k],label=label)
 for xx,v in zip(x+(k-1)*.24,vals):axs[0].text(xx,v/68*100+1,str(v),ha='center',fontsize=7)
axs[0].set(xticks=x,xticklabels=[m.title() for m in ms],ylabel='Success (% of 68 tasks)',ylim=(0,110),title='(a) Common held-out evaluation');axs[0].legend(loc='upper right',fontsize=7,ncol=1)
axs[1].bar(x,[v['hold_tip_goal_error_m_mean']*100 for v in stats],color=[colors[0]]+[colors[1]]*4,width=.65);axs[1].set(xticks=x,xticklabels=[m.title() for m in ms],ylabel='Mean fingertip error (cm)',ylim=(0,6.8),title='(b) Static target adherence');axs[1].tick_params(axis='x',rotation=20);f.tight_layout(w_pad=2);save(f,'fig05_interface_results')
# Figure 6.
c=read('evidence/E06_commands/contact_analysis/analysis.json');f,axs=plt.subplots(1,2,figsize=(9.5,3))
for i,(key,label) in enumerate([('teacher','Teacher'),('E0','No command'),('E1','Random groups'),('E2','Pose clusters')]):
 s=c['survival'][key]; t=np.array(s['time']);v=np.array(s['survival']);mask=t<=5;t=t[mask];v=v[mask];t=np.r_[t,5];v=np.r_[v,v[-1]]
 axs[0].step(t,v*100,where='post',label=label,color=colors[i]);axs[1].step(t,v*c['summary'][key]['lifted']/308*100,where='post',label=label,color=colors[i])
for ax,title,y in zip(axs,['(a) Conditional on successful lift','(b) All attempted rollouts'],['Post-lift survival (%)','Unconditional success (%)']):ax.set(xlim=(0,5),ylim=(40,101),xlabel='Seconds after first confirmed lift',ylabel=y,title=title);ax.grid(alpha=.15)
axs[0].legend(fontsize=8);f.tight_layout(w_pad=2);save(f,'fig06_contacts')
# Figure 7: actual camera evidence + supported runtime.
f,axs=plt.subplots(1,2,figsize=(9.6,3.4),gridspec_kw={'width_ratios':[1.25,1]});ax=axs[0];ax.set(xlim=(0,5),ylim=(0,3.7));ax.axis('off');panel(ax,(.15,2.6),4.7,.85,'Agent: choose command and phase','External arm controller owns wrist motion');panel(ax,(.15,1.3),4.7,.85,'Hand runtime: 30 Hz','Local feedback → history → policy → bounded targets',colors[1]);panel(ax,(.15,0),4.7,.85,'Outcome verification','Force alone does not certify object lift');arrow(ax,(2.5,2.6),(2.5,2.15));arrow(ax,(2.5,1.3),(2.5,.85));axs[1].imshow(plt.imread(FIG/'physical_readonly_rgb.png'));axs[1].axis('off');axs[1].set_title('Physical camera record · read-only\nmotion_sent = false',fontsize=9);f.tight_layout();save(f,'fig07_runtime')
# Supplement: actual robot pose renders.
f,axs=plt.subplots(2,3,figsize=(10,6))
for i,ax in enumerate(axs.flat):ax.imshow(plt.imread(ROOT/f'assets/poses/link_near_and_distance_joint/cluster_{i}.png'));ax.axis('off');ax.set_title(f'C{i}: geometric medoid',fontsize=10)
f.tight_layout();save(f,'figS01_medoids')
# Build HTML and publication-style LaTeX from the same Markdown.
md=(ROOT/'RLDexAgents_Supplementary_Report.md').read_text();equations=[]
def eq_html(m):
 s=m.group(1).strip();equations.append(s); idx=len(equations)
 display=s.replace(r'\text{',r'\mathrm{');display=re.sub(r'\\(mathcal|mathbb) ([A-Za-z])',r'\\\1{\2}',display)
 with plt.rc_context({'mathtext.fontset':'stix','svg.fonttype':'path'}):
  f=plt.figure(figsize=(11,.65));f.text(.5,.5,'$'+display+'$',ha='center',va='center',fontsize=14,fontfamily='STIXGeneral',color='#1b1b1b')
  f.savefig(FIG/f'equation_{idx:02d}.svg',bbox_inches='tight',pad_inches=.12,transparent=True);plt.close(f)
 return f'\n<div class="equation"><img src="figures/equation_{idx:02d}.svg" alt="{html.escape(s)}"></div>\n'
hmd=re.sub(r'\$\$(.*?)\$\$',eq_html,md,flags=re.S)
# Citations use local bibliography anchors, not network scripts.
hmd=re.sub(r'\[@(\w+)\]',lambda m:f'<a class="citation" href="#ref-{m[1]}">[{m[1]}]</a>',hmd)
body=markdown.markdown(hmd,extensions=['tables','fenced_code','toc'],extension_configs={'toc':{'permalink':False}})
body=style_code_blocks(body)
body=re.sub(r'<p><img alt="(Figure [^"]+)" src="([^"]+)" /></p>',lambda m:f'<figure><img loading="lazy" src="{m[2].replace(".png",".svg")}" alt="{m[1]}"><figcaption>{m[1]}</figcaption></figure>',body)
# Only figures produced here have SVG versions; embedded photos are inside their figure SVG.
for key in ['santello1998','ross2011','schulman2017','pinto2018','qi2023','ichter2023']:
 body=body.replace(f'<li><a class="citation" href="#ref-{key}">',f'<li id="ref-{key}"><a class="citation" href="#ref-{key}">')
# Inline local media supplement with complete scientific labels.
demos=read('data/successful_demos_remapped.json'); media=''
for cidx in [0,1,2,5]:
 d=next(x for x in demos if x['final_cluster']==cidx)
 media+=f'<figure><video controls preload="none" poster="{d["poster"]}"><source src="{d["video"]}" type="video/mp4"></video><figcaption><b>C{cidx} · Simulation replay</b><br>{html.escape(d["key"])}<br>Historical pick-and-pose success label; teacher 3200.</figcaption></figure>'
interactive=f'''<section class="interactive-evidence" id="interactive-manifold"><h3>Interactive evidence · poses, sources and executed demonstrations</h3><p>Rotate and zoom the 6,241-point projection, change the representation, and inspect source/cluster labels. A 3D projection is descriptive; use full-space metrics for quantitative comparison.</p><iframe src="manifold.html" title="Interactive hand-object manifold" loading="lazy"></iframe><p><a href="pose_hoi_manifold.html">Open the complete pose / HOI supplement</a> · <a href="manifold.html">Open 3D viewer separately</a></p><figure><img loading="lazy" src="figures/figS01_medoids.png" alt="Six actual geometric medoids"><figcaption>Actual representative Sharpa configurations. These are geometric medoids, not six verified functional grasp types.</figcaption></figure><div class="video-grid">{media}</div><p>No localized successful replay is available for final C3 or C4 in this selection. Older video filenames use their original partition; labels above use the final link-near-and-distance mapping.</p></section>'''
body=body.replace('<h2 id="4-from-pose-manifold-to-skill-bank">',interactive+'<h2 id="4-from-pose-manifold-to-skill-bank">')
heads=re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',body)
nav=''.join(f'<li><a href="#{a}">{b}</a></li>' for a,b in heads)
# Reuse the DEX-X hero, quick links, section-label and media structure.
body=re.sub(r'<h1.*?</h1>\s*<p>.*?</p>\s*<p>.*?</p>', '', body, count=1, flags=re.S)
body=re.sub(r'<h2 id="([^"]+)">',r'<h2 class="tagline" id="\1">',body)
body=body.replace('<figcaption>','<figcaption class="figure-caption">')
overview=re.search(r'<figure><img[^>]+src="figures/fig01_overview.svg".*?</figure>',body,re.S)
herofigure=overview.group(0) if overview else ''
if overview:body=body.replace(herofigure,'',1)
links=[('RLDexAgents_Supplementary_Report.md','Report'),('RLDexAgents_Supplementary_Report.tex','LaTeX'),('experiment_index.md','Experiments'),('pose_hoi_manifold.html','Interactive Gallery'),('references.bib','References'),('open_questions.md','Open Questions')]
quick=''.join(f'<a class="link-pill" href="{url}">{label}</a>' for url,label in links)
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RLDexAgents — Technical Report</title><meta name="description" content="Hand motion structure, executable skill distillation and an extensible agentic dexterous toolkit."><link rel="stylesheet" href="assets/template-fonts.css"><link rel="stylesheet" href="assets/dexx-template.css"><link rel="stylesheet" href="assets/rldex_report.css"></head><body><nav class="toc" aria-label="Report contents"><h3>Content</h3><hr><ul>{nav}</ul></nav><main class="main-content"><header class="report-hero"><h1 class="hero-text">RLDexAgents</h1><div class="sub-hero-text">An Extensible Dexterous Skill Toolkit for LLM Agents</div><p class="report-subtitle">From Hand Pose Manifolds to Interface-Conditioned Skill Distillation and Agentic Manipulation</p><div class="venue">Technical Report · 27 October 2026</div><div class="authors">Sharpa right-hand implementation · Audited experiment records</div>{herofigure}<div class="quick-links">{quick}</div></header><article class="section">{body}</article><footer class="footer">Audited project evidence · 27 October 2026.<br>Local figures and media · <a href="production_checks.md">Production notes</a><br>Page template adapted from the local DEX-X project page.</footer></main></body></html>'''
(ROOT/'supplementary_report.html').write_text(page)

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
  tex.append('\\begin{figure*}[t]\n\\centering\n\\includegraphics[width=\\textwidth,height=0.245\\textheight,keepaspectratio]{'+path+'}\n\\caption{'+inline(label)+'}\n\\end{figure*}');i+=1;continue
 if line.startswith('- '):
  if not in_list:tex.append(r'\begin{itemize}');in_list=True
  tex.append(r'\item '+inline(line[2:]));i+=1;continue
 if in_list and line.strip():tex.append(r'\end{itemize}');in_list=False
 if line.startswith('### '):
  title=re.sub(r'^\d+\.\d+\s*','',line[4:]);tex.append(r'\subsection{'+inline(title)+'}')
 elif line.startswith('## '):
  title=re.sub(r'^\d+\.\s*','',line[3:]);cmd='section*' if title.startswith(('Executive','Appendix')) else 'section';tex.append('\\'+cmd+'{'+inline(title)+'}')
 elif line.strip():tex.append(inline(line))
 else:tex.append('')
 i+=1
if in_list:tex.append(r'\end{itemize}')
tex.extend([r'\nocite{qi2023}',r'\bibliographystyle{plainnat}',r'\bibliography{references}',r'\end{document}'])
(ROOT/'RLDexAgents_Supplementary_Report.tex').write_text('\n'.join(tex))
print('Built 7 main figures, medoid supplement,',len(equations),'equations, HTML and LaTeX')
