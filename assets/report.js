"use strict";
const R = JSON.parse(document.getElementById('reportData').textContent);
const frame = document.getElementById('manifoldFrame');
const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function locate(method, index) {
  frame.contentWindow.postMessage({type:'hoi-report-select', method, index}, '*');
  document.getElementById('manifold').scrollIntoView({behavior:'smooth'});
  showSelected(method, index);
}

function showSelected(method, index) {
  const M = R.methods[method], meta = R.metadata[index];
  if (!M || !meta) return;
  const c = M.labels[index];
  const medoid = R.medoids[method].find(x => Number(x.cluster) === c);
  const matches = R.videos.filter(v => v.labels[method] === c);
  const exact = matches.find(v => v.key === meta[0]);
  document.getElementById('selected').innerHTML = `
    <img src="assets/poses/${method}/cluster_${c}.png" alt="Observed representative for cluster C${c}">
    <div class="selection-text">
      <span class="badge">Selected sample / C${c}</span>
      <p class="sample-title">${esc(meta[0])}</p>
      <div class="selection-facts">
        <span>Source <strong>${esc(meta[1])}</strong></span>
        <span>Object <strong>${esc(meta[2])}</strong></span>
        <span>Frame <strong>${esc(meta[4])}</strong></span>
      </div>
      <p>Historical lift + pose label: <strong>${meta[5] ? 'Passed' : 'Not passed'}</strong>.</p>
      <p class="mono">Representative: ${esc(medoid.key)}</p>
      <p>${medoid.key === meta[0] ? 'The selected sample is this cluster representative.' : 'The hand image shows the cluster representative, not a reconstruction of the selected frame.'}
      ${matches.length} recorded ${matches.length === 1 ? 'example' : 'examples'} in this cluster.</p>
      ${exact ? '<button id="selectedVideo">Watch this trajectory</button>' : ''}
    </div>`;
  if (exact) document.getElementById('selectedVideo').onclick = () => showVideo(exact.key);
}

window.addEventListener('message', e => {
  if (e.source === frame.contentWindow && e.data?.type === 'hoi-report-point') {
    showSelected(e.data.method, e.data.index);
  }
});

function renderDemos() {
  const cluster = document.getElementById('demoFilter').value;
  const query = document.getElementById('demoSearch').value.trim().toLowerCase();
  const items = R.videos.filter(v =>
    (cluster === 'all' || v.final_cluster === Number(cluster)) &&
    (v.key + ' ' + v.object).toLowerCase().includes(query));
  document.getElementById('demoCount').textContent = `${items.length} of ${R.videos.length} examples`;
  document.getElementById('demoGrid').innerHTML = items.length ? items.map(v => {
    const media = v.display_media || v;
    return `<article class="demo-card" data-key="${esc(v.key)}">
      <video controls playsinline preload="none" poster="${esc(media.poster)}" src="${esc(media.video)}" aria-label="C${v.final_cluster} ${esc(v.object)} teacher demonstration"></video>
      <div class="text">
        <span class="badge">C${v.final_cluster} / Isaac Sim teacher</span>
        <h3>${esc(v.object)}</h3>
        <p class="mono" data-maintenance hidden>${esc(v.key)}</p>
        <dl class="demo-metrics" data-maintenance hidden>
          <div><dt>Clip length</dt><dd>${media.duration_s.toFixed(2)} s</dd></div>
          <div><dt>Original lift</dt><dd>${v.recorded_rollout_lift_success ? 'Yes' : 'No'}</dd></div>
          <div><dt>Original tail stability</dt><dd>${(v.tail_stable_fraction * 100).toFixed(0)}%</dd></div>
        </dl>
        <div class="demo-actions">
          <button data-point="${v.index}">Locate in 3D</button>
          <a href="${esc(media.video)}" download>Download video</a>
        </div>
        <div class="demo-snapshots">${Object.entries(media.snapshots).map(([key, path]) =>
          `<a href="${esc(path)}"><img loading="lazy" src="${esc(path)}" alt="C${v.final_cluster} ${esc(key)} snapshot"><small>${esc(key.charAt(0).toUpperCase() + key.slice(1))}</small></a>`).join('')}</div>
        <details>
          <summary>Trajectory details</summary>
          <p data-maintenance hidden>Color footage is matched to the same reference. The outcome and force measurements below describe the original audited recording.</p>
          <p>Peak force: ${v.peak_force_N.toFixed(2)} N. Frames above 20 N: ${(v.force_over_20N_fraction * 100).toFixed(1)}%.</p>
          <p>${esc(v.success_definition)}</p>
          <a href="${esc(v.trajectory_npz)}" download>Original states &amp; teacher actions / NPZ</a>
          <p class="mono" data-maintenance hidden>${esc(v.checkpoint)}</p>
        </details>
      </div>
    </article>`;
  }).join('') : '<div class="empty">No demonstrations match these filters.</div>';
  document.querySelectorAll('[data-point]').forEach(b => {
    b.onclick = () => locate(R.final, Number(b.dataset.point));
  });
}

function filterCluster(c) {
  document.getElementById('demoFilter').value = String(c);
  document.getElementById('demoSearch').value = '';
  renderDemos();
  document.getElementById('demos').scrollIntoView({behavior:'smooth'});
}

function showVideo(key) {
  document.getElementById('demoFilter').value = 'all';
  document.getElementById('demoSearch').value = key;
  renderDemos();
  document.getElementById('demos').scrollIntoView({behavior:'smooth'});
}

function renderHoi() {
  const c = document.getElementById('hoiFilter').value;
  const items = R.scenes.filter(x => c === 'all' || x.final_cluster === Number(c));
  document.getElementById('hoiGrid').innerHTML = items.length ? items.map(x => `
    <article class="demo-card">
      <a href="${esc(x.image)}"><img loading="lazy" style="width:100%;display:block" src="${esc(x.image)}" alt="HOI scene for cluster C${x.final_cluster}"></a>
      <div class="text">
        <span class="badge">C${x.final_cluster} / HOI scene</span>
        <p class="mono" data-maintenance hidden>${esc(x.key)}</p>
        <p>Object: ${esc(x.object)} / Saved HOLD frame: ${esc(x.hold_frame_index)}</p>
      </div>
    </article>`).join('') : '<div class="empty">No saved scene snapshots for this cluster.</div>';
}

document.getElementById('demoFilter').onchange = renderDemos;
document.getElementById('demoSearch').oninput = renderDemos;
document.getElementById('hoiFilter').onchange = renderHoi;
document.querySelectorAll('[data-medoid]').forEach(b => {
  b.onclick = () => locate(R.final, R.methods[R.final].medoids[b.dataset.medoid]);
});
document.querySelectorAll('[data-filter]').forEach(b => {
  b.onclick = () => filterCluster(b.dataset.filter);
});
renderDemos();
renderHoi();
showSelected(R.final, R.methods[R.final].medoids['0']);
