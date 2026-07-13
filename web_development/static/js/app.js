const state = { snapshot: null, filter: 'all' };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const fmtTemp = value => Number(value).toFixed(1);
const fmtTime = value => new Date(value).toLocaleString('ko-KR', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'});
const statusText = {normal:'정상',warning:'주의',danger:'위험'};

document.addEventListener('DOMContentLoaded', () => {
  updateClock(); setInterval(updateClock, 1000);
  $('#menuButton')?.addEventListener('click', () => $('#sidebar').classList.toggle('open'));
  document.addEventListener('click', event => {
    if (innerWidth <= 820 && $('#sidebar')?.classList.contains('open') && !event.target.closest('#sidebar') && !event.target.closest('#menuButton')) $('#sidebar').classList.remove('open');
  });
  $$('.filter').forEach(button => button.addEventListener('click', () => {
    $$('.filter').forEach(item => item.classList.remove('active'));
    button.classList.add('active'); state.filter = button.dataset.filter; renderCameraGrid();
  }));
  const page = document.body.dataset.page;
  if (['dashboard','cameras'].includes(page) || $('.detail-grid')) {
    loadSnapshot(); setInterval(loadSnapshot, 4000);
  }
  if ($('.detail-grid')) { loadCameraHistory(); setInterval(loadCameraHistory, 8000); }
});

async function loadSnapshot() {
  try {
    const response = await fetch('/api/snapshot', {headers:{'Accept':'application/json'}});
    if (response.status === 401 || response.redirected) { location.href = '/login'; return; }
    if (!response.ok) throw new Error('데이터 요청 실패');
    state.snapshot = await response.json();
    $('#lastUpdated') && ($('#lastUpdated').textContent = `${fmtTime(state.snapshot.generated_at)} 갱신`);
    renderDangerBanner();
    if (document.body.dataset.page === 'dashboard') renderDashboard();
    if (document.body.dataset.page === 'cameras') renderCameraGrid();
    if ($('.detail-grid')) renderCameraDetail();
  } catch (error) {
    $('#lastUpdated') && ($('#lastUpdated').textContent = '연결 오류');
    console.error(error);
  }
}

function renderDangerBanner() {
  const banner = $('#dangerBanner'); if (!banner || !state.snapshot) return;
  const dangerous = state.snapshot.cameras.filter(camera => camera.status === 'danger');
  banner.classList.toggle('hidden', dangerous.length === 0);
  if (dangerous.length) $('#dangerMessage').textContent = `${dangerous.map(item => item.location).join(', ')}에서 위험 온도가 감지되었습니다.`;
}

function renderDashboard() {
  const data = state.snapshot;
  $('#normalCount').textContent = data.counts.normal;
  $('#warningCount').textContent = data.counts.warning;
  $('#dangerCount').textContent = data.counts.danger;
  $('#maxTemperature').textContent = fmtTemp(data.max_temperature);
  $('#averageTemperature').textContent = fmtTemp(data.average_temperature);
  $('#cameraLinkCount') && ($('#cameraLinkCount').textContent = `${String(data.cameras.filter(c => c.connected).length).padStart(2,'0')} / ${String(data.cameras.length).padStart(2,'0')} ONLINE`);
  $('#eventCount') && ($('#eventCount').textContent = data.alerts.filter(item => !item.acknowledged).length);
  const alerts = $('#recentAlerts');
  if (alerts) alerts.innerHTML = data.alerts.length ? data.alerts.slice(0,5).map(alert => `<a class="stream-event ${alert.level}" href="/alerts"><div><strong><i></i>${alert.level === 'danger' ? '고온 발생 감지' : '온도 주의 감지'}</strong><time>${new Date(alert.occurred_at).toLocaleTimeString('ko-KR',{hour12:false})}</time></div><small>${escapeHtml(alert.camera_id)} · ${escapeHtml(alert.location)}</small><b>${fmtTemp(alert.max_temperature)}°C</b></a>`).join('') : '<p class="empty-state">최근 경고가 없습니다.</p>';
  const liveGrid = $('#liveCameraGrid');
  if (liveGrid) {
    liveGrid.innerHTML = data.cameras.map(camera => `<a class="live-feed single-feed ${camera.status}" href="/cameras/${encodeURIComponent(camera.camera_id)}"><img class="robot-thermal-image" src="/static/images/robot-arm-thermal.png" alt="로봇팔과 모터 열화상 카메라 화면"><header><span class="rec">REC</span><strong>N001 · THERMAL</strong><time>${new Date(camera.captured_at).toLocaleTimeString('ko-KR',{hour12:false})}</time></header><div class="robot-detection-box"><span>ROBOT_01</span></div><div class="hotspot-layer">${hotspotMarkup(camera.hotspots)}</div><footer><span>1920 × 1080 · 1 FPS</span><b class="feed-status">${camera.status === 'danger' ? 'HOT SPOT' : statusText[camera.status]}</b></footer><div class="feed-temp"><small>MAX TEMPERATURE</small><strong>${fmtTemp(camera.max_temperature)}°C</strong><small>AVG ${fmtTemp(camera.average_temperature)}°C</small></div></a>`).join('');
  }
  drawLineChart($('#trendChart'), data.trend, [
    {key:'max_temperature', color:'#ffab3d'}, {key:'average_temperature', color:'#2d8cff'}
  ], data.thresholds);
}

function updateClock() {
  const clock = $('#currentClock');
  if (clock) clock.textContent = new Date().toLocaleTimeString('ko-KR', {hour12:false});
}

function renderCameraGrid() {
  const grid = $('#cameraGrid'); if (!grid || !state.snapshot) return;
  grid.innerHTML = state.snapshot.cameras.map(camera => `<a class="camera-card single-camera-card ${state.filter !== 'all' && state.filter !== camera.status ? 'hidden-card' : ''}" href="/cameras/${encodeURIComponent(camera.camera_id)}" data-status="${camera.status}"><div class="thermal-wrap"><img class="robot-thermal-image" src="/static/images/robot-arm-thermal.png" alt="로봇팔 모터 열화상"><div class="hotspot-layer">${hotspotMarkup(camera.hotspots)}</div><span class="thermal-label">N001 · ROBOT_01</span><span class="connection">● ${camera.connected ? '온라인' : '오프라인'}</span></div><div class="camera-body"><div class="camera-title"><div><h2>${escapeHtml(camera.name)}</h2><p>단일 열화상 카메라 · ${escapeHtml(camera.location)}</p></div><span class="status-badge ${camera.status}">${statusText[camera.status]}</span></div><div class="camera-temperatures"><div><small>현재</small><strong>${fmtTemp(camera.current_temperature)}°C</strong></div><div><small>최고</small><strong>${fmtTemp(camera.max_temperature)}°C</strong></div><div><small>평균</small><strong>${fmtTemp(camera.average_temperature)}°C</strong></div></div></div></a>`).join('');
}

function renderCameraDetail() {
  const root = $('.detail-grid'); const cameraId = root?.dataset.cameraId;
  const camera = state.snapshot?.cameras.find(item => item.camera_id === cameraId); if (!camera) return;
  $('#detailMax').textContent = fmtTemp(camera.max_temperature); $('#detailCurrent').textContent = fmtTemp(camera.current_temperature); $('#detailAverage').textContent = fmtTemp(camera.average_temperature); $('#detailTime').textContent = fmtTime(camera.captured_at);
  $('#detailStatus').className = `status-badge ${camera.status}`; $('#detailStatus').textContent = statusText[camera.status];
  const hotspots = $('#detailHotspots');
  if (hotspots) hotspots.innerHTML = hotspotMarkup(camera.hotspots);
}

function hotspotMarkup(hotspots = []) {
  return hotspots.map(hotspot => `<span class="hotspot-marker ${hotspot.status}" style="left:${hotspot.x}%;top:${hotspot.y}%"><i></i><b>${escapeHtml(hotspot.name)}<strong>${fmtTemp(hotspot.temperature)}°C</strong></b></span>`).join('');
}

async function loadCameraHistory() {
  const id = $('.detail-grid')?.dataset.cameraId; if (!id) return;
  try { const response = await fetch(`/api/cameras/${encodeURIComponent(id)}/history`); const data = await response.json(); drawLineChart($('#detailChart'), data.readings, [{key:'max_temperature',color:'#ff7b45'},{key:'average_temperature',color:'#2d8cff'}]); } catch(error) { console.error(error); }
}

function drawThermal(canvas, seed, maxTemp) {
  if (!canvas) return; const rect = canvas.getBoundingClientRect(); const dpr = devicePixelRatio || 1;
  const width = Math.max(320, Math.round(rect.width || canvas.width)); const height = Math.max(180, Math.round(rect.height || canvas.height));
  canvas.width = width*dpr; canvas.height = height*dpr; const ctx = canvas.getContext('2d'); ctx.scale(dpr,dpr);
  const gradient = ctx.createLinearGradient(0,0,width,height); gradient.addColorStop(0,'#07004f'); gradient.addColorStop(.28,'#001eaa'); gradient.addColorStop(.55,'#8b006d'); gradient.addColorStop(.75,'#e02d17'); gradient.addColorStop(1,'#ffb300'); ctx.fillStyle=gradient;ctx.fillRect(0,0,width,height);
  const hotspots=[{x:.32+.08*Math.sin(seed),y:.4,r:.22},{x:.7,y:.58+.05*Math.cos(seed),r:.18},{x:.5,y:.18,r:.11}];
  hotspots.forEach((hot,index)=>{const x=hot.x*width,y=hot.y*height,r=hot.r*width;const glow=ctx.createRadialGradient(x,y,0,x,y,r);const intensity=Math.min(1,(maxTemp-35)/55);glow.addColorStop(0,index===0&&intensity>.75?'#fff':'#fff36b');glow.addColorStop(.18,'#ff9c00');glow.addColorStop(.48,'#ed1638');glow.addColorStop(1,'transparent');ctx.fillStyle=glow;ctx.fillRect(x-r,y-r,r*2,r*2)});
  ctx.globalAlpha=.2;ctx.strokeStyle='#d3efff';ctx.lineWidth=1;for(let x=0;x<width;x+=width/12){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,height);ctx.stroke()}for(let y=0;y<height;y+=height/7){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(width,y);ctx.stroke()}ctx.globalAlpha=1;
  ctx.strokeStyle='#fff';ctx.lineWidth=1;const cx=width*.32,cy=height*.4;ctx.beginPath();ctx.moveTo(cx-11,cy);ctx.lineTo(cx+11,cy);ctx.moveTo(cx,cy-11);ctx.lineTo(cx,cy+11);ctx.stroke();ctx.fillStyle='#fff';ctx.font='600 12px Inter';ctx.fillText(`${fmtTemp(maxTemp)}°C`,cx+15,cy-7);
}

function drawLineChart(canvas, rows, series, thresholds) {
  if (!canvas || !rows?.length) return; const rect=canvas.getBoundingClientRect(),dpr=devicePixelRatio||1,width=Math.max(320,rect.width),height=Number(canvas.getAttribute('height'))||250;canvas.width=width*dpr;canvas.height=height*dpr;canvas.style.height=`${height}px`;const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);const pad={l:42,r:15,t:18,b:28};const values=rows.flatMap(row=>series.map(item=>Number(row[item.key])));const min=Math.max(0,Math.floor(Math.min(...values)/10)*10-5),max=Math.ceil(Math.max(...values,thresholds?.danger||0)/10)*10+5;ctx.clearRect(0,0,width,height);ctx.font='10px Inter';ctx.fillStyle='#718399';ctx.strokeStyle='#1b3045';ctx.lineWidth=1;
  for(let i=0;i<=4;i++){const y=pad.t+(height-pad.t-pad.b)*i/4;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(width-pad.r,y);ctx.stroke();const val=max-(max-min)*i/4;ctx.fillText(`${Math.round(val)}°`,5,y+3)}
  const xFor=i=>pad.l+(width-pad.l-pad.r)*(rows.length===1?0:i/(rows.length-1)),yFor=v=>pad.t+(max-v)/(max-min)*(height-pad.t-pad.b);
  if(thresholds){[['warning','#ffab3d'],['danger','#ff4d5e']].forEach(([key,color])=>{ctx.setLineDash([5,5]);ctx.strokeStyle=color+'99';ctx.beginPath();ctx.moveTo(pad.l,yFor(thresholds[key]));ctx.lineTo(width-pad.r,yFor(thresholds[key]));ctx.stroke();ctx.setLineDash([])})}
  series.forEach(item=>{ctx.strokeStyle=item.color;ctx.lineWidth=2;ctx.beginPath();rows.forEach((row,i)=>{const x=xFor(i),y=yFor(Number(row[item.key]));i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke()});
  const step=Math.max(1,Math.floor(rows.length/5));rows.forEach((row,i)=>{if(i%step===0||i===rows.length-1){const text=new Date(row.captured_at).toLocaleTimeString('ko-KR',{hour:'2-digit',minute:'2-digit'});ctx.fillStyle='#718399';ctx.fillText(text,Math.min(xFor(i)-15,width-45),height-7)}});
}

function escapeHtml(value) { const div=document.createElement('div'); div.textContent=String(value??''); return div.innerHTML; }
