"""Assemble existing measured results into a portable offline HTML report."""
from pathlib import Path
import csv, json, re, shutil, html
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[1]/'dexhand_hoi_learning'
ROOT=REPO/'audit/functional_hand_object_clusters_20261025/full_train_hoi_6241'
REL=ROOT/'link_contact_clearance_comparison'
E1=REPO/'audit/pose_manifold_e1_20261027/results_delivery'
DEMO=ROOT/'physx_contact_joint_clusters'
FINAL='link_near_and_distance_joint'
COLORS=['#2476b8','#f28e2b','#39a85a','#df5552','#9467bd','#8c564b']
for d in ['assets/poses','assets/videos','assets/hoi','assets/charts','data','sources']:(OUT/d).mkdir(parents=True,exist_ok=True)
def copy(src,dst):
    dst=OUT/dst; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def read(p): return json.loads(p.read_text())
def dump(p,x): (OUT/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def rows(p): return list(csv.DictReader(p.open()))
def esc(x):return html.escape(str(x))
def table(headers,records):
    return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>' for r in records)+'</tbody></table></div>'
def fig(name,caption):return f'<figure><a href="assets/charts/{name}.svg"><img loading="lazy" src="assets/charts/{name}.svg"></a><figcaption>{caption} · <a href="assets/charts/{name}.svg" download>SVG</a> / <a href="assets/charts/{name}.png" download>PNG</a></figcaption></figure>'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'#ffffff','axes.grid':True,'grid.alpha':.2,'svg.fonttype':'none'})
def save(f,name):
    f.tight_layout();f.savefig(OUT/f'assets/charts/{name}.svg',bbox_inches='tight');f.savefig(OUT/f'assets/charts/{name}.png',dpi=170,bbox_inches='tight');plt.close(f)

source_html=(REL/'manifold_3d_review/index.html').read_text().replace('HOI Full 20261010', 'OakInk (wrist-adapted)')
D=json.loads(re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>',source_html,re.S).group(1))
metrics=read(REL/'k6_comparison/summary.json'); E=read(E1/'summary.json')
medoids=read(REL/'manifold_review/medoids.json')
medoids={m['method']:m['medoids'] for m in medoids}
keyidx={m[0]:i for i,m in enumerate(D['metadata'])}
for method,items in medoids.items():
    for m in items: copy(REL/'manifold_review'/m['snapshot'],f'assets/poses/{method}/cluster_{m["cluster"]}.png')
# The original interactive renderer carries all five point sets inline, without CDN dependencies.
source_html=source_html.replace("pinned=i;showPoint(i)","pinned=i;showPoint(i);notifySelected(i)")
source_html=source_html.replace("pinned=Number(a.dataset.i);showPoint(pinned)","pinned=Number(a.dataset.i);showPoint(pinned);notifySelected(pinned)")
source_html=source_html.replace("methodSel.onchange=()=>{pinned=-1;current=-1;draw()}","methodSel.onchange=()=>{pinned=-1;current=-1;draw();notifySelected(D.methods[methodSel.value].medoids['0'])}")
hook='''
function notifySelected(i){parent.postMessage({type:'hoi-report-point',method:methodSel.value,index:i},'*')}
window.addEventListener('message',e=>{if(e.source!==parent||e.data?.type!=='hoi-report-select')return;const m=e.data.method,i=e.data.index;if(!D.methods[m]||!Number.isInteger(i)||i<0||i>=D.metadata.length)return;methodSel.value=m;D.datasets.forEach(s=>datasetOn[s]=true);for(let c=0;c<6;c++)clusterOn[c]=true;checks();pinned=i;showPoint(i);draw();notifySelected(i)});
notifySelected(D.methods[methodSel.value].medoids['0']);
'''
source_html=source_html.replace('</script></body>',hook+'</script></body>')
(OUT/'manifold.html').write_text(source_html)
dump('data/manifold.json',D);dump('data/clustering_summary.json',metrics);dump('data/medoids.json',medoids)
for fn in ['summary.json','bank_metrics.csv','source_generalization.csv','limits.json','pose_bank_entries.csv']:
    copy(E1/fn,'data/e1_'+fn)
copy(REL/'k6_comparison'/FINAL/'assignments.csv','data/final_cluster_assignments.csv')
copy(REL/'k6_comparison'/FINAL/'successful_examples.csv','data/final_successful_examples.csv')
copy(DEMO/'successful_demos.csv','data/original_successful_demos.csv')
for fn in ['pose_manifold_e1_20261027.md','full_hoi_link_contact_clustering_20261026.md','full_hoi_dataset_manifold_3d_20261026.md','hand_pose_pca_20261018.md']:
    original=REPO/'docs'/fn
    text=original.read_text()
    def local_image(match):
        label,target=match.groups(); asset=(original.parent/target).resolve()
        if not asset.is_file(): return label+'（原始图片未找到：'+target+'）'
        dest='assets/archive/'+fn.removesuffix('.md')+'_'+asset.name
        copy(asset,dest)
        return '!['+label+'](../'+dest+')'
    text=re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',local_image,text)
    def archive_link(match):
        label,target=match.groups()
        if target.startswith('../assets/'):return '['+label+']('+target+')'
        if target in ['pose_manifold_e1_20261027.md','full_hoi_link_contact_clustering_20261026.md','full_hoi_dataset_manifold_3d_20261026.md','hand_pose_pca_20261018.md']:return '['+label+']('+target+')'
        return label+'（原始来源路径：`'+target+'`）'
    text=re.sub(r'(?<!!)\[([^\]]*)\]\(([^)]+)\)',archive_link,text)
    (OUT/'sources'/fn).write_text(text)


# Join videos by exact trajectory key. Old PhysX cluster filenames are never reused as final labels.
vmeta={v['key']:v for v in read(DEMO/'successful_demo_review/videos.json')}
videos=[]
for r in rows(DEMO/'successful_demos.csv'):
    if r['key'] not in keyidx or r['key'] not in vmeta:continue
    v=vmeta[r['key']]; stem=r['demo_id']; i=keyidx[r['key']]
    copy(DEMO/'successful_demo_review/videos'/f'{stem}.mp4',f'assets/videos/{stem}.mp4')
    copy(DEMO/'successful_demo_review/videos'/f'{stem}.jpg',f'assets/videos/{stem}.jpg')
    videos.append(dict(r,index=i,final_cluster=D['methods'][FINAL]['labels'][i],labels={m:x['labels'][i] for m,x in D['methods'].items()},video=f'assets/videos/{stem}.mp4',poster=f'assets/videos/{stem}.jpg',checkpoint=v['checkpoint'],frames=v['frames'],fps=v['fps'],video_note=v['note']))
dump('data/successful_demos_remapped.json',videos)
scenes=[]
for r in rows(DEMO/'visualization_selection_expanded.csv'):
    img=DEMO/'snapshots'/f'{r["sample_id"]}.jpg'
    if img.exists() and r['key'] in keyidx:
        dst=f'assets/hoi/{r["sample_id"]}.jpg';copy(img,dst)
        scenes.append(dict(r,image=dst,final_cluster=D['methods'][FINAL]['labels'][keyidx[r['key']]]))
dump('data/hoi_scene_examples.json',scenes)
# Copy the geometric diagrams as an explicit fallback, never call them scene snapshots.
tool=OUT.parent/'dexterous_hand_harness/tools/hoi_reference/link_near_distance'
for c in range(6):
    copy(tool/f'images/cluster_{c}_hoi_reference.png',f'assets/hoi/cluster_{c}_clearance.png')
copy(tool/'data/cluster_reference.json','data/medoid_link_clearance.json')

# Quantitative charts use stored numeric outputs, not manually transcribed tables.
cohorts=E['pca_cohort_explained_variance_ratio']; names={'sharpa_all_limit_valid':'Sharpa all (22D)','sharpa_hoi_limit_valid':'Sharpa HOI (22D)','sharpadex_free_hand':'SharpaDex free hand (22D)','human_keypoints_60d':'Human normalized keypoints (60D)'}
f,axes=plt.subplots(1,2,figsize=(12,4.2))
for k,v in cohorts.items():
    a=axes[1] if k.startswith('human') else axes[0]; a.plot(range(1,len(v)+1),100*np.cumsum(v),label=names[k],linewidth=2)
for a,title in zip(axes,['Sharpa joint representations','Human keypoint representation']):
    a.axhline(95,color='#777777',linestyle='--');a.set(xlabel='PCA components',ylabel='Cumulative explained variance (%)',title=title,ylim=(0,102));a.legend(fontsize=8)
save(f,'variance')
r=E['reconstruction']; dims=[x['dimensions'] for x in r]
f,ax=plt.subplots(1,2,figsize=(12,4))
ax[0].plot(dims,[x['joint_rmse_rad'] for x in r],'o-',color='#2476b8');ax[0].set(xlabel='PCA components',ylabel='Joint RMS error (rad)',title='Joint reconstruction')
for stat in ['mean','p95']:ax[1].plot(dims,[x['fingertip_fk_error_mm'][stat] for x in r],'o-',label=stat)
ax[1].set(xlabel='PCA components',ylabel='Fingertip error (mm)',title='FK after joint-limit clipping');ax[1].legend();save(f,'reconstruction')
banks=E['bank_metrics'];methods=list(dict.fromkeys(x['method'] for x in banks));short={'random':'Random','joint_kmeans_22d':'Joint KMeans 22D','pca_kmeans_9d':'PCA KMeans 9D','pca_kmeans_14d':'PCA KMeans 14D','pca_kmeans_22d':'PCA KMeans 22D','pca_kmedoids_14d':'PCA KMedoids 14D','hand_taxonomy':'Taxonomy'}
f,axes=plt.subplots(1,2,figsize=(13,4.7))
for m in methods:
    z=sorted([x for x in banks if x['method']==m],key=lambda x:x['bank_size'])
    for a,col in zip(axes,['source_macro_median_joint_rmse_rad','bank_mean_pairwise_range_normalized_distance']):a.plot([x['bank_size'] for x in z],[x[col] for x in z],'o-',markersize=3,label=short[m])
axes[0].set(title='Bank size vs. coverage (lower is better)',ylabel='Source-macro median joint RMS (rad)');axes[1].set(title='Bank diversity',ylabel='Mean pairwise normalized L2 distance')
for a in axes:a.set_xscale('log',base=2);a.set_xticks([6,12,24,48,96,192],['6','12','24','48','96','192']);a.set_xlabel('Bank entries')
axes[1].legend(fontsize=8);save(f,'coverage')
loso=E['leave_one_source_out']; lm=list(dict.fromkeys(x['method'] for x in loso));f,a=plt.subplots(figsize=(9,4))
for m in lm:
    a.plot([24,96],[np.mean([x['coverage_joint_rmse_rad']['median'] for x in loso if x['method']==m and x['bank_size']==k]) for k in [24,96]],'o-',label=short[m])
a.set(xticks=[24,96],xlabel='Bank entries',ylabel='Held-out-source macro median RMS (rad)',title='Leave-one-source-out coverage');a.legend(fontsize=8);save(f,'source_generalization')
valid=E['source_joint_limit_validity'];f,a=plt.subplots(figsize=(10,5))
a.barh(list(valid),[100*v['joint_limit_valid_fraction'] for v in valid.values()],color=['#2476b8' if v['joint_limit_valid_fraction']>.9 else '#df5552' for v in valid.values()]);a.set(xlabel='Joint-limit-valid poses (%)',xlim=(0,105),title='Source joint-limit validity before E1 fitting');save(f,'validity')
variants=metrics['feature_variants'];ms=list(variants);mlabel=['Joint','Legacy relation','Tip + joint','Link near','Link near + distance'];f,axes=plt.subplots(1,3,figsize=(13,4.4))
for a,metric,title in zip(axes,['weighted_silhouette','restart_ari_to_first','nmi_cluster_object'],['Weighted silhouette','Restart ARI','Object NMI']):
    val=[variants[m]['k_metrics'][metric] if metric in variants[m]['k_metrics'] else variants[m]['cluster_quality_and_success'][metric] for m in ms]
    a.bar(range(5),val,color=['#b2c3d1']*4+['#2476b8']);a.set_xticks(range(5),mlabel,rotation=35,ha='right');a.set_title(title)
save(f,'methods')
clusters=variants[FINAL]['cluster_quality_and_success']['clusters'];f,ax=plt.subplots(1,2,figsize=(12,4))
ax[0].bar(range(6),[x['count'] for x in clusters],color=COLORS);ax[0].set(title='Final cluster population',ylabel='HOI reference samples',xticks=range(6),xticklabels=[f'C{i}' for i in range(6)])
x=np.arange(6);ax[1].bar(x-.18,[x['tabletop_pick_success_rate']*100 for x in clusters],.36,label='Pick');ax[1].bar(x+.18,[x['pick_and_pose_tracking_success_rate']*100 for x in clusters],.36,label='Pick AND pose');ax[1].set(title='Recorded teacher outcomes by cluster',ylabel='Success (%)',xticks=x,xticklabels=[f'C{i}' for i in x]);ax[1].legend();save(f,'cluster_outcomes')
mat=np.zeros((6,len(D['datasets'])),int)
for i,m in enumerate(D['metadata']):mat[D['methods'][FINAL]['labels'][i],D['datasets'].index(m[1])]+=1
f,a=plt.subplots(figsize=(10,4));a.imshow(mat,cmap='Blues',aspect='auto');a.set_xticks(range(len(D['datasets'])),D['datasets'],rotation=20,ha='right');a.set_yticks(range(6),[f'C{i}' for i in range(6)]);a.set_title('Original dataset × final cluster (sample counts)')
for i in range(6):
    for j in range(len(D['datasets'])):a.text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>mat.max()*.55 else '#172638')
a.grid(False);save(f,'source_mix')

# Tables and gallery are emitted as ordinary HTML so numeric results remain visible without JS.
method_table=table(['表示','Silhouette ↑','重跑 ARI ↑','物体 NMI','PC1–2 方差'],[[esc(m),f"{v['k_metrics']['weighted_silhouette']:.3f}",f"{v['k_metrics']['restart_ari_to_first']:.3f}",f"{v['cluster_quality_and_success']['nmi_cluster_object']:.3f}",f"{sum(v['pca_explained_variance_ratio'][:2])*100:.1f}%"] for m,v in variants.items()])
cohort_table=table(['数据 / 特征空间','输入维数','95% 方差维数','PC1–3 方差'],[[esc(names[k]),len(v),int(np.searchsorted(np.cumsum(v),.95))+1,f'{sum(v[:3])*100:.1f}%'] for k,v in cohorts.items()])
recon_table=table(['PCA 维数','保留方差','关节 RMS / rad','裁剪前超限姿态','FK mean / mm','FK P95 / mm'],[[x['dimensions'],f"{x['explained_variance']*100:.1f}%",f"{x['joint_rmse_rad']:.4f}",f"{x['joint_limit_violating_pose_fraction']*100:.1f}%",f"{x['fingertip_fk_error_mm']['mean']:.2f}",f"{x['fingertip_fk_error_mm']['p95']:.2f}"] for x in r])
bank_table=table(['方法']+[str(k) for k in [6,12,24,48,96,192]],[[short[m]]+[f"{next(x for x in banks if x['method']==m and x['bank_size']==k)['source_macro_median_joint_rmse_rad']:.4f}" for k in [6,12,24,48,96,192]] for m in methods])
loso_table=table(['方法','K=24','K=96'],[[short[m]]+[f"{np.mean([x['coverage_joint_rmse_rad']['median'] for x in loso if x['method']==m and x['bank_size']==k]):.4f}" for k in [24,96]] for m in lm])
cluster_table=table(['簇','样本数','抓起','抓起且 pose 跟踪','已保存成功视频'],[[f'C{x["cluster"]}',x['count'],f"{x['tabletop_pick_successes']} / {x['count']} ({100*x['tabletop_pick_success_rate']:.1f}%)",f"{x['pick_and_pose_tracking_successes']} / {x['count']} ({100*x['pick_and_pose_tracking_success_rate']:.1f}%)",sum(v['final_cluster']==x['cluster'] for v in videos)] for x in clusters])
cards=[]
for m in medoids[FINAL]:
    c=int(m['cluster']);st=clusters[c];vv=[v for v in videos if v['final_cluster']==c];ss=[s for s in scenes if s['final_cluster']==c]
    if vv: image=vv[0]['poster']; label='同簇成功 HOI demo（不同于 medoid 帧）';context=vv[0]['key']
    elif ss:image=ss[0]['image'];label='同簇 HOI 示例（未按严格成功筛选）';context=ss[0]['key']
    else:image=f'assets/hoi/cluster_{c}_clearance.png';label='几何距离图；暂无同簇场景截图';context=m['key']
    objs=' · '.join(f'{esc(o)} × {n}' for o,n in st['object_top10'][:4])
    cards.append(f'''<article class="cluster-card" style="--cluster:{COLORS[c]}"><div class="cluster-head"><h3>C{c}</h3><span>{st['count']:,} samples</span></div><div class="pair"><figure><img loading="lazy" src="assets/poses/{FINAL}/cluster_{c}.png"><figcaption>真实样本代表手形 · frame {m['source_frame_index']}</figcaption></figure><figure><a href="{image}"><img loading="lazy" src="{image}"></a><figcaption>{label}</figcaption></figure></div><p class="mono">{esc(m['key'])}</p><p>簇内物体 ID 分布：{objs}</p><details><summary>HOI 图来源</summary><p class="mono">{esc(context)}</p></details><p>抓起＋跟踪：{st['pick_and_pose_tracking_successes']} / {st['count']}；成功视频 {len(vv)} 条。</p><button data-medoid="{c}">在 3D 图中定位代表手形</button> <button data-filter="{c}">浏览本簇视频</button></article>''')
provenance={'date':'2026-10-27','cluster_source':str(REL),'pca_source':str(E1),'demo_source':str(DEMO),'cluster_method':FINAL,'samples':6241,'success_definition':'tabletop_pick_success AND pose_tracking_success','video_mapping':'exact trajectory key; original PhysX cluster IDs are not the final link-near IDs','missing_saved_success_video_clusters':[3,4],'source_files_are_provenance_only':'All displayed media, figures, point data, and scripts are copied locally.'}
dump('data/provenance.json',provenance)
APP={'metadata':D['metadata'],'methods':{m:{'labels':v['labels'],'medoids':v['medoids']} for m,v in D['methods'].items()},'medoids':medoids,'videos':videos,'scenes':scenes,'final':FINAL}
body=f'''
<header class="hero"><div class="eyebrow">DEXTEROUS HAND · TECHNICAL REPORT · 2026.10.27</div><h1>从手形到手物关系<br><em>Pose & HOI Manifolds</em></h1><p class="lead">聚类如何组织手部姿态？用交互点云查看分布，用真实代表手形和成功轨迹理解簇，再用 PCA 重建与 Pose Bank 覆盖检验表示。</p><div class="stats"><div><strong>6,241</strong><span>HOI 关系样本</span></div><div><strong>6</strong><span>最终 link-near＋distance 簇</span></div><div><strong>{len(videos)}</strong><span>已有成功 demo 视频</span></div><div><strong>13D</strong><span>E1 Sharpa 全集 95% 方差</span></div></div></header>
<nav><a href="#manifold">01 · 3D 分布</a><a href="#gestures">02 · 代表手形</a><a href="#demos">03 · 成功 demo</a><a href="#pca">04 · PCA</a><a href="#bank">05 · Pose Bank</a><a href="#findings">06 · 结论与数据</a></nav>
<main><section id="manifold"><div class="section-title"><span>01</span><h2>交互 3D 手物关系分布</h2></div><p>默认使用 <code>{FINAL}</code>：关节姿态、掌部关系、物体形状、26-link 的 5 mm 近邻标签与按物体尺寸归一化的距离。拖动旋转、滚轮缩放；按数据集、cluster 或物体着色。点击点或星号，可在下方查看对应簇的代表手形，并定位已有视频。不同表示的同号 cluster 不对应同一类别。</p><div class="note">这是 6,241 条 HOI reference 的单帧关系表示。三个 PCA 轴各自按标准差缩放以便观察，原始坐标可在点详情查看。三维邻近不能替代完整特征距离；本报告后面的 E1 PCA 使用另一套姿态数据口径。</div><iframe id="manifoldFrame" src="manifold.html" title="Interactive 3D HOI manifold"></iframe><div id="selected" class="selected"></div><details><summary>五种表示的定量对比</summary>{fig('methods','同一批样本，K=6；silhouette 与 ARI 描述聚类结构和重跑稳定性。NMI 是与物体 ID 的关联，不是功能性评分。')}{method_table}</details></section>
<section id="gestures"><div class="section-title"><span>02</span><h2>最终版本：六类代表手形与 HOI</h2></div><p>代表取每簇距离中心最近的真实样本。左图为代表手形；右图为同簇 HOI 场景或距离示意，来源逐条标出。C4 代表没有 link 落在 5 mm 近邻内，因此不能把六类一律称为“已抓稳”的手势。</p><div class="cluster-grid">{''.join(cards)}</div><details><summary>更多同簇 HOI 场景图片（24 张）</summary><p>按 trajectory key 映射到最终簇，图片为保存 rollout 的 HOLD 场景，不是该 key 的聚类代表帧，也未全部经过严格成功筛选。</p><label>最终 cluster <select id="hoiFilter"><option value="all">全部</option>{''.join(f'<option value="{c}">C{c}</option>' for c in range(6))}</select></label><div id="hoiGrid" class="demo-grid"></div></details>{fig('source_mix','原始数据集与最终簇的关系；SPIDER 中的 HOT3D、DexYCB、OakInk、HRDexDB 按 key 还原来源。')}{fig('cluster_outcomes','成败来自已有 teacher 评测；表示与成功的关联不证明聚类带来了策略性能提升。')}{cluster_table}</section>
<section id="demos"><div class="section-title"><span>03</span><h2>成功典型 demo：手物同框视频</h2></div><p>筛选条件：<code>tabletop_pick_success AND pose_tracking_success</code>。成功标签来自既有评测 CSV；视频展示同 key 的保存状态，视频文件本身不新增成功判定。录制使用 <code>train_patchfix/model_3200.pt</code>，完整路径保留在 JSON。</p><div class="controls"><label>最终 cluster <select id="demoFilter"><option value="all">全部（12）</option>{''.join(f'<option value="{c}">C{c}</option>' for c in range(6))}</select></label><label>轨迹 / 物体 <input id="demoSearch" placeholder="banana / washing_brush / traj…"></label><span id="demoCount"></span></div><div id="demoGrid" class="demo-grid"></div><p class="note">C3 / C4 尚无已保存并通过此严格筛选的成功视频。C3 有普通 HOI 图片；C4 使用几何距离图。这里保留缺口，不把其他聚类方法的同号视频冒充为它们的成功示例。</p></section>
<section id="pca"><div class="section-title"><span>04</span><h2>PCA：解释方差与重建精度</h2></div><p>最新 E1：1,029,112 个索引姿态中，1,015,044 个在 URDF 限位内；按 trajectory key 拆分，来源均衡拟合 8,867 个姿态、测试 5,016 个姿态。Sharpa 使用 22D 关节角；人手使用按手长归一化的 60D 局部关键点。不同特征空间分别绘图。</p>{fig('variance','95% 方差维数受特征空间、数据范围和加权方式影响，不能直接解释为不同手的内在维数排名。')}{cohort_table}<p class="takeaway">PCA-14 保留 96.1% 方差，但裁剪后指尖 FK 误差仍有均值 10.1 mm、P95 26.7 mm。解释方差高，不代表精确接触几何已被保留。</p>{fig('reconstruction','关节 RMS 为原始重建误差；指尖 FK 在关节限位裁剪后计算，超限率在裁剪前统计。')}{recon_table}</section>
<section id="bank"><div class="section-title"><span>05</span><h2>Pose Bank：规模、覆盖与跨来源泛化</h2></div><p>所有最终 Bank 条目取自真实限位内姿态。KMeans 中心也替换成最近的真实训练样本；K-Medoids 使用候选池上的交替更新。覆盖表为逐来源最近姿态中位误差的宏平均，单位 rad；多样性为按关节范围归一化后两两 L2 距离。</p>{fig('coverage','K=6、12、24、48、96、192。不同规模继续改善覆盖；多样性增加不一定改善最近邻覆盖。')}{bank_table}{fig('source_generalization','每次完整留出一个来源，13 个来源等权汇总；K=24 和 K=96。')}{loso_table}<details><summary>运动学有效性与数据口径</summary>{fig('validity','原始姿态限位内比例；E1 已排除超限姿态。离线限位/FK 不等价于 PhysX 自碰撞或抓取成功验证。')}<p>SPIDER 来源只有约 10–25% 的抽样姿态通过当前 URDF 限位检查，根因尚未解决。当前 Bank 限位违规率为 0；尚未验证 PhysX 自碰撞通过率。</p></details></section>
<section id="findings"><div class="section-title"><span>06</span><h2>结论、边界与原始数值</h2></div><div class="conclusions"><article><h3>手物关系分组更稳定</h3><p>Link-near＋distance 的重跑 ARI 为 0.997，高于 tip＋joint 的 0.444；其 silhouette 为 0.087。稳定分组仍不等于已验证的抓握语义。</p></article><article><h3>有选择的 Bank 改善覆盖</h3><p>K=24 时 Joint KMeans 的来源宏平均误差为 0.2263 rad，随机 Bank 为 0.2597 rad，改善约 12.9%。K=96/192 仍继续受益。</p></article><article><h3>Medoids 的价值是实际样本</h3><p>本轮 Medoids 没有超过 KMeans 的几何覆盖；两者最终都选真实姿态。执行性能还需任务与接触评测，不能从覆盖曲线直接推断。</p></article></div><p>历史 2026-10-18 PCA 报告与最新 E1 的采样、限位筛选和来源权重不同，数值不能混合成同一条趋势曲线。原始报告保留在 sources；本页最新数值由机器可读 summary/CSV 生成。</p><div class="downloads"><a href="data/manifold.json" download>3D 点云与全部标签 JSON</a><a href="data/final_cluster_assignments.csv" download>6,241 条最终分簇 CSV</a><a href="data/successful_demos_remapped.json" download>成功视频映射与来源</a><a href="data/medoids.json" download>五种方法的代表手形</a><a href="data/medoid_link_clearance.json" download>代表手形关节与 link 距离</a><a href="data/e1_summary.json" download>E1 完整数值 JSON</a><a href="data/e1_bank_metrics.csv" download>Bank 指标 CSV</a><a href="data/e1_source_generalization.csv" download>来源留出 CSV</a><a href="data/e1_pose_bank_entries.csv" download>Bank 姿态来源 CSV</a><a href="sources/pose_manifold_e1_20261027.md">E1 研究记录</a><a href="sources/full_hoi_link_contact_clustering_20261026.md">HOI 聚类研究记录</a><a href="sources/hand_pose_pca_20261018.md">历史 PCA 口径</a><a href="data/provenance.json">产物来源</a></div></section></main><footer>所有页面资源保存在本目录 · 无 CDN / 外部图片或视频依赖 · 2026-10-27</footer>
'''
(OUT/'index.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hand Pose & HOI Manifold — Technical Report</title><link rel="stylesheet" href="assets/report.css"></head><body>'+body+'<script id="reportData" type="application/json">'+json.dumps(APP,ensure_ascii=False).replace('</','<\\/')+'</script><script src="assets/report.js"></script></body></html>')
shutil.copy2(OUT/'index.html',OUT/'pose_hoi_manifold.html')
from gallery_english import localize_gallery
localize_gallery(OUT/'pose_hoi_manifold.html')
print('Report assembled:',OUT,'videos',len(videos),'scene images',len(scenes))
