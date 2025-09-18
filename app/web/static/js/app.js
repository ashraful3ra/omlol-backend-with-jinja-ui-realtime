
const socket = (typeof io !== 'undefined') ? io() : null;

async function api(path, opts={}){
  const res = await fetch((window.API_BASE||'') + path, {headers:{'Content-Type':'application/json'}, ...opts});
  const txt = await res.text();
  let data = {}; try { data = txt ? JSON.parse(txt) : {}; } catch(e) { data = {success:false, error: txt||e+''}; }
  if(!res.ok || data.success===false){ throw new Error(data.message || data.error || ('HTTP '+res.status)); }
  return data;
}
function el(tag, attrs={}, ...children){
  const n = document.createElement(tag);
  for(const [k,v] of Object.entries(attrs||{})){
    if(k==='class') n.className = v;
    else if(k.startsWith('on') && typeof v==='function') n.addEventListener(k.slice(2).toLowerCase(), v);
    else if(v!==undefined) n.setAttribute(k, v);
  }
  for(const c of children){ if(c==null) continue; n.append(c.nodeType?c:document.createTextNode(c)); }
  return n;
}
function badge(text, on=true){ return el('span', {class:'badge ' + (on?'on':'off')}, text); }

/* -------- Modal helpers -------- */
function openModal(title, bodyEl, onOk){
  const root = document.getElementById('modalRoot');
  document.getElementById('modalTitle').textContent = title || 'Modal';
  const body = document.getElementById('modalBody'); body.innerHTML=''; body.append(bodyEl);
  root.classList.remove('hidden'); root.classList.add('flex');
  const ok = document.getElementById('modalOk'); const cancel = document.getElementById('modalCancel');
  function close(){ root.classList.add('hidden'); root.classList.remove('flex'); ok.onclick=null; cancel.onclick=null; }
  cancel.onclick = close;
  ok.onclick = async ()=>{ if(onOk){ await onOk(); } close(); };
}

/* -------- Dashboard -------- */
async function initDashboard(){
  const list = await api('/api/bots');
  const botList = document.getElementById('botList');
  const shell = document.getElementById('summaryShell');
  const empty = document.getElementById('summaryEmpty');

  botList.innerHTML = '';
  if(!list.bots || !list.bots.length){ botList.append(el('div', {class:'text-subtle text-sm'}, 'No bots yet.')); empty.classList.remove('hidden'); shell.classList.add('hidden'); return; }

  let selected = list.bots[0];
  function drawList(){
    botList.innerHTML = '';
    for(const b of list.bots){
      const row = el('div', {class: 'flex items-center justify-between rounded-xl p-3 bg-[rgba(27,37,56,.4)]'});
      row.append(el('div', {}, b.name), badge(b.status || 'stopped', b.status==='running'));
      // start button
      const startBtn = el('button', {class:'btn btn-primary ml-2'}, 'Start');
      startBtn.onclick = ()=> openStartModal(b);
      row.append(startBtn);
      row.addEventListener('click', async (e)=>{ if(e.target===startBtn) return; selected = b; await refreshSummary(); });
      botList.append(row);
    }
  }

  async function openStartModal(b){
    const wrap = el('div', {class:'space-y-3'});
    const accSel = el('select', {class:'select', id:'startAcc'}); wrap.append(el('div', {}, 'Select Account'), accSel);
    try{
      const accs = await api('/accounts/api');
      for(const a of (accs.accounts||[])){ const o = el('option', {}, a.name + (a.is_testnet?' (TEST)':' (LIVE)')); o.value = a.id; accSel.append(o); }
    }catch(e){}
    openModal('Start Bot', wrap, async ()=>{
      try{ await api(`/api/bots/${b.id}/start`, {method:'POST', body: JSON.stringify({account_id: Number(accSel.value)})}); await initDashboard(); } catch(e){ alert(e.message); }
    });
  }

  async function refreshSummary(){
    try{
      // details
      const d = await api('/api/bots/' + selected.id);
      // summary
      const r = await api('/api/reports/bot-summary/' + selected.id); const s = r.summary||{};
      shell.classList.remove('hidden'); empty.classList.add('hidden');
      document.getElementById('sumName').textContent = selected.name;
      document.getElementById('sumStart').textContent = 'Start at: ' + (d.last_started_at || d.created_at || '-');
      document.getElementById('sumAccount').textContent = 'Account: ' + (d.account_name || d.account_id || '-');
      document.getElementById('runSide').textContent = (s.running_side || '-') ;
      document.getElementById('entryPrice').textContent = (s.entry_price ?? '-') ;
      document.getElementById('runRoi').textContent = (s.current_roi_percent!=null? (s.current_roi_percent+'%') : '0%');
      document.getElementById('markPrice').textContent = (s.mark_price ?? '-') ;
      document.getElementById('winTrades').textContent = (s.win_trades ?? 0);
      document.getElementById('lossTrades').textContent = (s.loss_trades ?? 0);
      document.getElementById('totalTrades').textContent = (s.total_trades ?? 0);
      document.getElementById('totalProfit').textContent = '$' + ((s.total_profit ?? 0).toFixed ? (s.total_profit ?? 0).toFixed(2) : s.total_profit ?? 0);
      document.getElementById('totalLoss').textContent = '$' + ((s.total_loss ?? 0).toFixed ? (s.total_loss ?? 0).toFixed(2) : s.total_loss ?? 0);
      document.getElementById('netPnl').textContent = '$' + ((s.net_result ?? 0).toFixed ? (s.net_result ?? 0).toFixed(2) : s.net_result ?? 0);
      // actions
      document.getElementById('btnPush').onclick = async ()=>{ await api(`/api/bots/${selected.id}/push`, {method:'POST'}); await refreshSummary(); };
      document.getElementById('btnClose').onclick = async ()=>{ await api(`/api/bots/${selected.id}/close`, {method:'POST'}); await refreshSummary(); };
    }catch(e){
      shell.classList.add('hidden'); empty.classList.remove('hidden');
    }
  }

  drawList();
  await refreshSummary();
}

if(socket){
  socket.on('bot_status_update', async ()=>{
    try{
      if(document.getElementById('dashboard')) await initDashboard();
      if(document.getElementById('reportPage')) await initReportPage();
      if(window.drawBots) await window.drawBots();
    }catch(e){}
  });
}

/* -------- Bot page -------- */
async function initBotPage(){
  // ROI add new
  const addRoiBtn = document.getElementById('addRoi');
  addRoiBtn.addEventListener('click', (e)=>{
    e.preventDefault();
    const grid = addRoiBtn.closest('.grid');
    const current = Array.from(document.querySelectorAll('input.roi')).map(i=>i.getAttribute('data-roi'));
    const nextIdx = current.length + 2; // start from R2
    const key = 'R' + nextIdx;
    const holder = document.createElement('div');
    holder.innerHTML = `<div class="text-sm mb-1">${key} ROI %</div><input data-roi="${key}" type="number" class="input roi" value="5">`;
    grid.insertBefore(holder, grid.lastElementChild);
  });

  // Load accounts & symbols
  const accounts = await api('/accounts/api');
  const acc = accounts.accounts?.[0];
  if(acc){
    try{
      const r = await api('/api/symbols?account_id=' + acc.id);
      const hint = document.getElementById('hintSymbols');
      const few = (r.symbols||[]).slice(0,20);
      hint.textContent = few.join(', ') + (r.symbols && r.symbols.length>20 ? ' ...' : '');
    }catch(e){ /* ignore */ }
  }

  // Save
  document.getElementById('saveBot').addEventListener('click', async ()=>{
    const payload = {
      name: document.getElementById('botName').value.trim(),
      account_id: acc? acc.id : null,
      timeframe: document.getElementById('timeframe').value,
      symbols: document.getElementById('coins').value.split(',').map(s=>s.trim()).filter(Boolean),
      trade_mode: document.getElementById('tradeMode').value,
      leverage: Number(document.getElementById('leverage').value),
      margin_mode: document.getElementById('marginMode').value,
      margin_usd: Number(document.getElementById('marginUsd').value || 0),
      recovery_roi_threshold: Number(document.getElementById('recoveryRoi').value || 0),
      max_recovery_margin: Number(document.getElementById('maxCap').value || 0),
      roi_targets: (()=>{
        const obj = {};
        document.querySelectorAll('input.roi').forEach(i=> obj[i.getAttribute('data-roi')] = Number(i.value||0));
        return obj;
      })(),
      conditions: {
        open_at_candle_open: document.getElementById('openAtOpen').checked,
        open_after_close: document.getElementById('openAfterClose').checked,
        close_on_stoploss: document.getElementById('closeOnSl').checked,
        close_at_candle_close: document.getElementById('closeAtClose').checked,
        trail_by_r: document.getElementById('trailByR').checked,
        close_at_last_r: document.getElementById('closeAtLastR').checked,
        stoploss_roi: Number(document.getElementById('r1sl').value||0)
      },
      run_mode: document.getElementById('runMode').value,
      max_trades_limit: Number(document.getElementById('maxTrades').value || 0)
    };
    const msg = document.getElementById('saveMsg');
    try{
      await api('/api/bots', {method:'POST', body: JSON.stringify(payload)});
      msg.textContent = 'Saved ✔';
      await drawBots();
    }catch(e){ msg.textContent = e.message; }
  });

  // Existing bots
  async function drawBots(){
    const cont = document.getElementById('botCards'); cont.innerHTML = '';
    const list = await api('/api/bots');
    for(const b of (list.bots||[])){
      const row = el('div', {class:'flex items-center justify-between bg-[rgba(27,37,56,.4)] rounded-xl p-3'});
      const left = el('div', {class:'flex flex-col'},
        el('div', {class:'font-medium'}, b.name),
        el('div', {class:'text-xs text-subtle'}, (b.created_at || '').split('T')[0] || '')
      );
      const ctrl = el('div', {class:'flex items-center gap-2'},
        // pin to dashboard (localStorage)
        el('button', {class:'btn btn-ghost', onclick: ()=>{ togglePin(b.id); }}, '👁'),
        el('button', {class:'btn btn-ghost', onclick: async ()=>{ location.href='/app?bot='+b.id; }}, '✏️'),
        el('button', {class:'btn btn-danger', onclick: async ()=>{ if(confirm('Delete this bot?')){ await api('/api/bots/'+b.id, {method:'DELETE'}); drawBots(); } }}, '🗑'),
      );
      row.append(left, ctrl); cont.append(row);
    }
    if(cont.children.length===0){
      cont.append(el('div', {class:'text-subtle text-sm'}, 'No bots yet.'));
    }
  }
  window.drawBots = drawBots;
  drawBots();

  function togglePin(id){
    const key='pinned_bots'; const saved = JSON.parse(localStorage.getItem(key)||'[]');
    const i = saved.indexOf(id); if(i>=0) saved.splice(i,1); else saved.push(id);
    localStorage.setItem(key, JSON.stringify(saved));
    alert('Pinned bots updated');
  }
}

/* -------- Account -------- */
async function initAccountPage(){
  const listEl = document.getElementById('accList');
  async function load(){
    listEl.innerHTML='';
    const r = await api('/accounts/api');
    for(const a of (r.accounts||[])){
      const row = el('div', {class:'flex items-center justify-between bg-[rgba(27,37,56,.4)] rounded-xl p-3'},
        el('div', {class:'flex items-center gap-3'},
          el('div', {class:'font-medium'}, a.name),
          el('div', {class:'text-xs text-subtle'}, 'Balance: $' + (a.balance ?? '-'))
        ),
        el('div', {class:'flex gap-2'},
          el('button',{class:'btn btn-ghost', onclick: ()=>alert('Active/Inactive is a UI toggle only for now.')}, '👁'),
          el('button',{class:'btn btn-danger', onclick: async ()=>{ if(confirm('Delete account?')){ await api('/accounts/api/'+a.id, {method:'DELETE'}); load(); } }}, '🗑')
        )
      );
      listEl.append(row);
    }
    if(listEl.children.length===0) listEl.append(el('div',{class:'text-subtle text-sm'},'No accounts yet.'));
  }
  load();

  document.getElementById('accSave').addEventListener('click', async ()=>{
    const data = {
      name: document.getElementById('accName').value.trim(),
      api_key: document.getElementById('accKey').value,
      api_secret: document.getElementById('accSecret').value,
      is_testnet: document.getElementById('accTest').checked
    };
    const msg = document.getElementById('accMsg');
    try{ await api('/accounts/api', {method:'POST', body: JSON.stringify(data)}); msg.textContent='Saved ✔'; load(); }
    catch(e){ msg.textContent=e.message; }
  });
}

/* -------- Report -------- */
async function initReportPage(){
  const body = document.getElementById('reportRows');
  const search = document.getElementById('search');
  const fromDate = document.getElementById('fromDate');
  const toDate = document.getElementById('toDate');

  async function load(){
    body.innerHTML='';
    const list = await api('/api/bots');
    let i = 0;
    for(const b of (list.bots||[])){
      let s = {total_trades:0,loss_trades:0,win_trades:0,breakeven_trades:0,net_result:0,total_profit:0,total_loss:0};
      let d = {};
      try{ const r = await api('/api/reports/bot-summary/'+b.id); s = {...s, ...(r.summary||{})}; }catch(e){}
      try{ d = await api('/api/bots/' + b.id); } catch(e){}

      const startTxt = (d.last_started_at || d.created_at || '-');
      const stopTxt = (d.last_stopped_at || 'Ongoing');
      const name = b.name || '';
      const row = document.createElement('tr'); row.className='border-t border-[rgba(27,37,56,.5)]';
      row.dataset.name = name.toLowerCase();
      row.dataset.start = startTxt.split('T')[0] || '';

      row.innerHTML = `
        <td class="py-2 pr-4">${String(++i).padStart(2,'0')}.</td>
        <td class="py-2 pr-4 text-emerald-400 font-medium">${name}</td>
        <td class="py-2 pr-4"><div>${startTxt.replace('T', ', ').slice(0,16)}</div><div class="text-xs text-subtle">${stopTxt==='Ongoing'?'Ongoing':stopTxt.replace('T', ', ').slice(0,16)}</div></td>
        <td class="py-2 pr-4">${s.total_trades||0}</td>
        <td class="py-2 pr-4">${s.loss_trades||0}</td>
        <td class="py-2 pr-4">${s.win_trades||0}</td>
        <td class="py-2 pr-4">${s.breakeven_trades||0}</td>
        <td class="py-2 pr-4"><div>Profit: $${(s.total_profit||0).toFixed? (s.total_profit||0).toFixed(2) : s.total_profit||0}</div><div>Loss: $${(s.total_loss||0).toFixed? (s.total_loss||0).toFixed(2) : s.total_loss||0}</div><div class="font-semibold">Net: $${(s.net_result||0).toFixed? (s.net_result||0).toFixed(2) : s.net_result||0}</div></td>
      `;
      body.append(row);
    }
    if(body.children.length===0){
      const tr = document.createElement('tr'); tr.innerHTML = `<td class="py-3 text-subtle" colspan="8">No data yet.</td>`; body.append(tr);
    }
    applyFilters();
  }

  function applyFilters(){
    const q = (search.value||'').trim().toLowerCase();
    const f = fromDate.value || null;
    const t = toDate.value || null;
    for(const tr of Array.from(body.children)){
      if(tr.children.length < 5) continue; // skip empty row
      const name = tr.dataset.name || '';
      const start = tr.dataset.start || '';
      let show = true;
      if(q && !name.includes(q)) show = false;
      if(f && start && start < f) show = False;
      if(t && start && start > t) show = False;
      tr.style.display = show ? '' : 'none';
    }
  }

  search.addEventListener('input', applyFilters);
  fromDate.addEventListener('change', applyFilters);
  toDate.addEventListener('change', applyFilters);

  await load();
  // Auto refresh every 10s
  setInterval(load, 10000);
}

document.addEventListener('DOMContentLoaded', ()=>{
  if(document.getElementById('dashboard')) initDashboard();
  if(document.getElementById('botPage')) initBotPage();
  if(document.getElementById('accountPage')) initAccountPage();
  if(document.getElementById('reportPage')) initReportPage();
});
