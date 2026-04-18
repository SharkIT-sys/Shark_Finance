/* ═══════════════════════════════════════════════════════════
   SHARK CONTABILIDAD — App JS
   ═══════════════════════════════════════════════════════════ */

'use strict';

// ── Register Service Worker ───────────────────────────────────
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(console.error);
}

// ── PWA Install Logic ─────────────────────────────────────────
let deferredPrompt;
const installBanner = document.getElementById('pwa-install-banner');
const installBtn = document.getElementById('pwa-install-btn');
const closeBtn = document.getElementById('pwa-close-btn');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  // Solo mostramos si no se ha cerrado manualmente en esta sesión
  if (!sessionStorage.getItem('pwa-banner-closed')) {
    installBanner.style.setProperty('display', 'flex', 'important');
  }
});

if (installBtn) {
  installBtn.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to install prompt: ${outcome}`);
    deferredPrompt = null;
    installBanner.style.display = 'none';
  });
}

if (closeBtn) {
  closeBtn.addEventListener('click', () => {
    installBanner.style.display = 'none';
    sessionStorage.setItem('pwa-banner-closed', 'true');
  });
}

// ── State ────────────────────────────────────────────────────
const state = {
  currentPage: 'dashboard',
  dashYear: new Date().getFullYear(),
  dashMonth: new Date().getMonth() + 1,
  charts: {},
};

// ── Utils ─────────────────────────────────────────────────────
const fmt = n => Number(n).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';
const fmtPct = n => Number(n).toFixed(1) + '%';
const MONTHS_ES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok && res.status === 401) { showLogin(); return null; }
  return res.json();
}

function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast' + (type ? ' ' + type : '');
  t.style.display = 'block';
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.style.display = 'none'; }, 2800);
}

// ── Screen Management ─────────────────────────────────────────
function showLogin() {
  document.getElementById('screen-login').classList.add('active');
  document.getElementById('screen-app').classList.remove('active');
}
function showApp() {
  document.getElementById('screen-login').classList.remove('active');
  document.getElementById('screen-app').classList.add('active');
  navigateTo('dashboard');
}

// ── Auth ──────────────────────────────────────────────────────
async function initAuth() {
  const status = await api('/api/auth/status');
  if (!status) return;

  if (status.authenticated) { showApp(); return; }

  if (status.needs_setup) {
    document.getElementById('login-title').textContent = 'Configura tu contraseña';
    document.getElementById('login-subtitle').textContent = 'Primera vez — crea tu contraseña maestra';
    document.getElementById('setup-fields').style.display = 'block';
    document.getElementById('recovery-fields').style.display = 'none';
    document.getElementById('login-fields').style.display = 'none';
    document.getElementById('login-btn').textContent = 'Crear contraseña';
  } else if (status.recovery_mode) {
    document.getElementById('login-title').textContent = 'Recuperación de Cuenta';
    document.getElementById('login-subtitle').textContent = 'Se han agotado los intentos. Responde para recuperar:';
    document.getElementById('setup-fields').style.display = 'none';
    document.getElementById('login-fields').style.display = 'none';
    document.getElementById('recovery-fields').style.display = 'block';
    document.getElementById('recovery-q-lbl').textContent = 'Pregunta: ' + status.security_question;
    document.getElementById('login-btn').textContent = 'Recuperar Acceso';
  } else {
    // Normal login
    document.getElementById('setup-fields').style.display = 'none';
    document.getElementById('recovery-fields').style.display = 'none';
    document.getElementById('login-fields').style.display = 'block';
    document.getElementById('login-btn').textContent = 'Entrar';
  }
  showLogin();
}

document.getElementById('setup-pwd').addEventListener('input', e => {
  const text = e.target.value;
  const strengthLbl = document.getElementById('setup-pwd-strength');
  let c = 0;
  if (text.length >= 8) c++;
  if (/[A-Z]/.test(text)) c++;
  if (/[a-z]/.test(text)) c++;
  if (/[!@#$%^&*()\-_+={[}\]|\\:;"'<,>.?/]/.test(text)) c++;
  
  if (text.length === 0) strengthLbl.textContent = '';
  else if (c <= 1) { strengthLbl.textContent = 'Débil (+8 carácteres, mayús y símbolos)'; strengthLbl.style.color = '#E74C3C'; }
  else if (c <= 3) { strengthLbl.textContent = 'Buena (Añade algún símbolo)'; strengthLbl.style.color = '#F39C12'; }
  else { strengthLbl.textContent = 'Fuerte ✓'; strengthLbl.style.color = '#2ECC71'; }
});

document.getElementById('login-btn').addEventListener('click', async () => {
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';

  const isSetup = document.getElementById('setup-fields').style.display !== 'none';
  const isRecovery = document.getElementById('recovery-fields').style.display !== 'none';
  
  if (isSetup) {
    const pwd = document.getElementById('setup-pwd').value;
    const conf = document.getElementById('setup-confirm').value;
    const sq = document.getElementById('setup-sec-q').value;
    const sa = document.getElementById('setup-sec-a').value;
    if (pwd.length < 4) { errEl.textContent = 'Mínimo 4 caracteres'; errEl.style.display = 'block'; return; }
    if (pwd !== conf) { errEl.textContent = 'Las contraseñas no coinciden'; errEl.style.display = 'block'; return; }
    if (!sq || !sa) { errEl.textContent = 'Pregunta y respuesta son obligatorias'; errEl.style.display = 'block'; return; }
    
    const r = await api('/api/auth/setup', { method: 'POST', body: JSON.stringify({ password: pwd, sec_question: sq, sec_answer: sa }) });
    if (r?.success) showApp();
    else { errEl.textContent = r?.error || 'Error'; errEl.style.display = 'block'; }
  } else if (isRecovery) {
    const ans = document.getElementById('recovery-pwd').value;
    const r = await api('/api/auth/recover', { method: 'POST', body: JSON.stringify({ answer: ans }) });
    if (r?.wiped) {
      alert("ATENCIÓN: Se han agotado todos los intentos de recuperación. La base de datos ha sido purgada por completo de forma irreversible por seguridad.");
      location.reload();
    } else if (r?.success) {
      alert("¡Recuperado! Tu contraseña maestra es:\n\n" + r.raw_pwd + "\n\nGuárdala a salvo en tu gestor de contraseñas. Puedes cambiarla en Ajustes.");
      showApp();
    } else {
      errEl.textContent = r?.error || 'Respuesta incorrecta';
      errEl.style.display = 'block';
    }
  } else {
    const pwd = document.getElementById('login-pwd').value;
    const r = await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ password: pwd }) });
    if (r?.success) showApp();
    else if (r?.wiped) {
      alert("ATENCIÓN: Demasiados intentos fallidos. La base de datos ha sido purgada por completo de forma irreversible por seguridad.");
      location.reload();
    } else { 
      errEl.textContent = r?.error || 'Contraseña incorrecta'; 
      errEl.style.display = 'block'; 
      if (r?.recovery_mode) {
        setTimeout(initAuth, 1500); // Reload the UI to show recovery
      }
    }
  }
});

// Allow Enter key on login
['login-pwd','setup-pwd','setup-confirm','setup-sec-q','setup-sec-a','recovery-pwd'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('keydown', e => { if (e.key === 'Enter') document.getElementById('login-btn').click(); });
});

document.getElementById('btn-logout').addEventListener('click', async () => {
  await api('/api/auth/logout', { method: 'POST' });
  showLogin();
  document.getElementById('login-pwd').value = '';
});

// ── Settings / Change Password ────────────────────────────────
document.getElementById('btn-settings').addEventListener('click', () => {
  openModal('Ajustes', `
    <h4 style="margin-bottom:12px;color:var(--text-1);font-size:16px;">Cambiar Contraseña Maestra</h4>
    <p style="font-size:13px;color:var(--text-3);margin-bottom:16px;">
      Cambiar tu contraseña encriptará de nuevo todos tus datos localmente. Este proceso puede tardar unos segundos.
    </p>
    <div class="input-group">
      <label>Contraseña Actual</label>
      <input type="password" id="f-old-pwd" placeholder="••••••••" autocomplete="current-password" />
    </div>
    <div class="input-group">
      <label>Nueva Contraseña</label>
      <input type="password" id="f-new-pwd" placeholder="Mínimo 4 caracteres" autocomplete="new-password" />
    </div>
    <div class="input-group">
      <label>Confirmar Nueva Contraseña</label>
      <input type="password" id="f-conf-pwd" placeholder="Repite la contraseña" autocomplete="new-password" />
    </div>
    <button class="btn-primary btn-full" id="modal-save-pwd-btn" style="margin-top:8px;">Actualizar Contraseña</button>
  `);

  document.getElementById('modal-save-pwd-btn').onclick = async () => {
    const oldPwd = document.getElementById('f-old-pwd').value;
    const newPwd = document.getElementById('f-new-pwd').value;
    const confPwd = document.getElementById('f-conf-pwd').value;

    if (!oldPwd) { showToast('Introduce la contraseña actual', 'error'); return; }
    if (newPwd.length < 4) { showToast('La nueva contraseña debe tener mínimo 4 caracteres', 'error'); return; }
    if (newPwd !== confPwd) { showToast('Las contraseñas nuevas no coinciden', 'error'); return; }

    const btn = document.getElementById('modal-save-pwd-btn');
    btn.disabled = true;
    btn.textContent = 'Procesando encriptación...';

    const r = await api('/api/auth/password', {
      method: 'PUT',
      body: JSON.stringify({ old_password: oldPwd, new_password: newPwd })
    });

    if (r?.success) {
      closeModal();
      showToast('Contraseña actualizada ✓', 'success');
      const loginPwd = document.getElementById('login-pwd');
      if (loginPwd) loginPwd.value = newPwd;
    } else {
      btn.disabled = false;
      btn.textContent = 'Actualizar Contraseña';
      showToast(r?.error || 'Error al actualizar', 'error');
    }
  };
});

// ── Navigation ────────────────────────────────────────────────
function navigateTo(page) {
  if (state.currentPage === page && page !== 'manual') return; 
  state.currentPage = page;

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const pageEl = document.getElementById('page-' + page);
  if (pageEl) pageEl.classList.add('active');

  const navEl = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (navEl) navEl.classList.add('active');

  // Cerrar menú más si estaba abierto
  const moreMenu = document.getElementById('more-menu');
  if (moreMenu) moreMenu.style.display = 'none';

  // Scroll to top
  document.getElementById('app-main').scrollTo({ top: 0 });

  // Load data
  if (page === 'dashboard') loadDashboard();
  else if (page === 'income') loadTransactions('income');
  else if (page === 'expense') loadTransactions('expense');
  else if (page === 'categories') loadCategories();
  else if (page === 'commitments') loadCommitments();
  else if (page === 'historic') loadHistoric();
  else if (page === 'health') loadHealth();
  else if (page === 'savings') loadSavings();
  else if (page === 'manual') loadManual();
}

document.querySelectorAll('.nav-item[data-page], .menu-item[data-page]').forEach(btn => {
  btn.addEventListener('click', () => navigateTo(btn.dataset.page));
});

// ── More Menu logic ──────────────────────────────────────────
const moreBtn = document.getElementById('btn-more');
const moreMenu = document.getElementById('more-menu');
const moreClose = document.getElementById('more-menu-close');

if (moreBtn && moreMenu) {
  moreBtn.addEventListener('click', () => { moreMenu.style.display = 'flex'; });
}
if (moreClose && moreMenu) {
  moreClose.addEventListener('click', () => { moreMenu.style.display = 'none'; });
}
if (moreMenu) {
  moreMenu.addEventListener('click', (e) => { if (e.target === moreMenu) moreMenu.style.display = 'none'; });
}

const menuSettingsBtn = document.getElementById('btn-menu-settings');
if (menuSettingsBtn) {
  menuSettingsBtn.addEventListener('click', () => {
    moreMenu.style.display = 'none';
    document.getElementById('btn-settings').click(); 
  });
}

// ── Dashboard ─────────────────────────────────────────────────
function updateMonthLabel() {
  document.getElementById('dash-month-label').textContent =
    MONTHS_ES[state.dashMonth - 1] + ' ' + state.dashYear;
}

document.getElementById('dash-prev').addEventListener('click', () => {
  if (state.dashMonth === 1) { state.dashMonth = 12; state.dashYear--; }
  else state.dashMonth--;
  loadDashboard();
});
document.getElementById('dash-next').addEventListener('click', () => {
  if (state.dashMonth === 12) { state.dashMonth = 1; state.dashYear++; }
  else state.dashMonth++;
  loadDashboard();
});

async function loadDashboard() {
  updateMonthLabel();
  const data = await api(`/api/dashboard?year=${state.dashYear}&month=${state.dashMonth}`);
  if (!data) return;
  const { summary, trend } = data;

  document.getElementById('dash-income').textContent = fmt(summary.total_income);
  document.getElementById('dash-expense').textContent = fmt(summary.total_expense);
  const bal = summary.balance;
  const balEl = document.getElementById('dash-balance');
  balEl.textContent = fmt(bal);
  balEl.style.color = bal >= 0 ? 'var(--income)' : 'var(--expense)';

  // Bar
  const inc = summary.total_income || 1;
  const expPct = Math.min(100, (summary.total_expense / inc) * 100);
  const freePct = bal > 0 ? Math.min(100 - expPct, (bal / inc) * 100) : 0;
  document.getElementById('dash-bar-expense').style.width = expPct + '%';
  document.getElementById('dash-bar-free').style.width = freePct + '%';
  document.getElementById('dash-bar-expense-lbl').textContent =
    `Gastos (${expPct.toFixed(1)}%)`;
  document.getElementById('dash-bar-free-lbl').textContent =
    `Libre (${freePct.toFixed(1)}%)`;

  // Pie
  renderPie(summary.expenses_breakdown);

  // Line
  renderLine(trend);
}

function renderPie(breakdown) {
  if (state.charts.pie) { state.charts.pie.destroy(); }
  const ctx = document.getElementById('dash-pie').getContext('2d');

  const legendEl = document.getElementById('dash-pie-legend');

  if (!breakdown || breakdown.length === 0) {
    legendEl.innerHTML = '<span style="color:var(--text-3);font-size:12px;">Sin datos este mes</span>';
    state.charts.pie = new Chart(ctx, { type: 'doughnut', data: { datasets: [{ data: [1], backgroundColor: ['rgba(255,255,255,0.05)'] }] }, options: { cutout: '65%', plugins: { legend: { display: false } }, animation: false } });
    return;
  }

  const labels = breakdown.map(b => b.name);
  const values = breakdown.map(b => b.amount);
  const colors = breakdown.map(b => b.color);
  const total = values.reduce((a, b) => a + b, 0);

  legendEl.innerHTML = breakdown.map(b =>
    `<span class="pie-legend-item"><span class="pie-legend-dot" style="background:${b.color}"></span>${b.name} (${((b.amount/total)*100).toFixed(1)}%)</span>`
  ).join('');

  state.charts.pie = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }] },
    options: {
      cutout: '65%',
      plugins: { legend: { display: false }, tooltip: {
        callbacks: { label: ctx => ` ${ctx.label}: ${fmt(ctx.raw)}` }
      }},
      animation: { duration: 600 }
    }
  });
}

function renderLine(trend) {
  if (state.charts.line) { state.charts.line.destroy(); }
  const ctx = document.getElementById('dash-line').getContext('2d');
  state.charts.line = new Chart(ctx, {
    type: 'line',
    data: {
      labels: trend.labels,
      datasets: [
        { label: 'Ingresos', data: trend.incomes, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.08)', tension: 0.4, pointRadius: 3 },
        { label: 'Gastos', data: trend.expenses, borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.08)', tension: 0.4, pointRadius: 3 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#a0a0b8', font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${fmt(ctx.raw)}` } } },
      scales: {
        x: { ticks: { color: '#6b6b85', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#6b6b85', font: { size: 10 }, callback: v => v + '€' }, grid: { color: 'rgba(255,255,255,0.04)' } }
      }
    }
  });
}

// ── Transactions ──────────────────────────────────────────────
async function loadTransactions(type) {
  const data = await api(`/api/transactions?type=${type}`);
  if (!data) return;
  const listEl = document.getElementById(type === 'income' ? 'income-list' : 'expense-list');

  if (data.length === 0) {
    listEl.innerHTML = `<div class="empty-state"><div class="empty-icon">${type === 'income' ? '💚' : '❤️'}</div><p>No hay ${type === 'income' ? 'ingresos' : 'gastos'} registrados</p></div>`;
    return;
  }

  listEl.innerHTML = data.map(tx => {
    const recText = tx.recurrence_type === 'one_time' ? 'Única vez' :
      `Cada ${tx.recurrence_interval}m${tx.recurrence_duration ? ` · ${tx.recurrence_duration} veces` : ' · Permanente'}`;
    return `
      <div class="tx-item ${type}" data-id="${tx.id}">
        <span class="tx-dot" style="background:${tx.category_color}"></span>
        <div class="tx-body">
          <div class="tx-name">${escHtml(tx.name)}</div>
          <div class="tx-meta">${escHtml(tx.category_name)} · ${tx.date}</div>
          <div class="tx-actions">
            <button class="btn-sm info" onclick="showEditTxModal(${tx.id}, '${type}')">Editar</button>
            <button class="btn-sm danger" onclick="deleteTx(${tx.id}, '${type}')">Eliminar</button>
          </div>
        </div>
        <div class="tx-right">
          <div class="tx-amount">${fmt(tx.amount)}</div>
          <div class="tx-rec">${recText}</div>
        </div>
      </div>`;
  }).join('');
}

async function deleteTx(id, type) {
  if (!confirm('¿Eliminar esta transacción?')) return;
  const r = await api(`/api/transactions/${id}`, { method: 'DELETE' });
  if (r?.success) { showToast('Eliminado ✓', 'success'); loadTransactions(type); }
  else showToast('Error al eliminar', 'error');
}

// ── Tx Modal ──────────────────────────────────────────────────
async function showAddTxModal(type) {
  const cats = await api(`/api/categories?type=${type}`);
  if (!cats) return;
  const typeEs = type === 'income' ? 'Ingreso' : 'Gasto';
  const today = new Date().toISOString().slice(0, 10);

  openModal(`Añadir ${typeEs}`, buildTxForm(cats, null, today));
  setupRecToggle();

  document.getElementById('modal-save-btn').onclick = async () => {
    const payload = collectTxForm(type);
    if (!payload) return;
    const r = await api('/api/transactions', { method: 'POST', body: JSON.stringify(payload) });
    if (r?.success || r?.id) {
      closeModal(); showToast(`${typeEs} añadido ✓`, 'success'); loadTransactions(type);
    } else showToast(r?.error || 'Error', 'error');
  };
}

async function showEditTxModal(id, type) {
  const allTx = await api(`/api/transactions?type=${type}`);
  const tx = allTx?.find(t => t.id === id);
  const cats = await api(`/api/categories?type=${type}`);
  if (!tx || !cats) return;
  const typeEs = type === 'income' ? 'Ingreso' : 'Gasto';

  openModal(`Editar ${typeEs}`, buildTxForm(cats, tx, tx.date));
  setupRecToggle();

  document.getElementById('modal-save-btn').onclick = async () => {
    const payload = collectTxForm(type);
    if (!payload) return;
    const r = await api(`/api/transactions/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
    if (r?.success) {
      closeModal(); showToast('Guardado ✓', 'success'); loadTransactions(type);
    } else showToast(r?.error || 'Error', 'error');
  };
}

function buildTxForm(cats, tx, date) {
  const isRec = tx && tx.recurrence_type !== 'one_time';
  const hasDur = tx?.recurrence_duration != null;
  return `
    <div class="input-group">
      <label>Nombre / Concepto</label>
      <input type="text" id="f-name" placeholder="Descripción" value="${tx ? escHtml(tx.name) : ''}" />
    </div>
    <div class="form-row">
      <div class="input-group">
        <label>Cantidad (€)</label>
        <input type="number" id="f-amount" placeholder="0.00" step="0.01" min="0.01" value="${tx ? tx.amount : ''}" />
      </div>
      <div class="input-group">
        <label>Fecha</label>
        <input type="date" id="f-date" value="${date}" />
      </div>
    </div>
    <div class="input-group">
      <label>Categoría</label>
      <select id="f-cat">
        ${cats.map(c => `<option value="${c.id}" ${tx?.category_id === c.id ? 'selected' : ''}>${escHtml(c.name)}</option>`).join('')}
      </select>
    </div>
    <label style="font-size:12px;font-weight:600;color:var(--text-2);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;display:block;">Recurrencia</label>
    <div class="rec-toggle">
      <button type="button" class="rec-toggle-btn ${!isRec ? 'active' : ''}" data-rec="one_time">Única vez</button>
      <button type="button" class="rec-toggle-btn ${isRec ? 'active' : ''}" data-rec="recurring">Recurrente</button>
    </div>
    <div class="rec-fields ${isRec ? 'visible' : ''}">
      <div class="form-row">
        <div class="input-group">
          <label>Cada (meses)</label>
          <input type="number" id="f-interval" min="1" max="120" value="${tx?.recurrence_interval || 1}" />
        </div>
        <div class="input-group">
          <label>Nº de veces (0=siempre)</label>
          <input type="number" id="f-duration" min="0" max="1200" value="${hasDur ? tx.recurrence_duration : 0}" placeholder="0 = permanente" />
        </div>
      </div>
    </div>
    <button class="btn-primary btn-full" id="modal-save-btn" style="margin-top:8px;">Guardar</button>`;
}

function setupRecToggle() {
  document.querySelectorAll('.rec-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.rec-toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const recFields = document.querySelector('.rec-fields');
      recFields.classList.toggle('visible', btn.dataset.rec === 'recurring');
    });
  });
}

function collectTxForm(type) {
  const name = document.getElementById('f-name').value.trim();
  const amount = parseFloat(document.getElementById('f-amount').value);
  const date = document.getElementById('f-date').value;
  const cat = document.getElementById('f-cat').value;
  const isRec = document.querySelector('.rec-toggle-btn.active')?.dataset.rec === 'recurring';

  if (!name) { showToast('Escribe un nombre', 'error'); return null; }
  if (isNaN(amount) || amount <= 0) { showToast('Cantidad no válida', 'error'); return null; }
  if (!date) { showToast('Selecciona una fecha', 'error'); return null; }

  const dur = parseInt(document.getElementById('f-duration')?.value || 0);
  return {
    type,
    name,
    amount,
    date,
    category_id: parseInt(cat),
    recurrence_type: isRec ? 'custom' : 'one_time',
    recurrence_interval: isRec ? parseInt(document.getElementById('f-interval').value) : 1,
    recurrence_duration: isRec && dur > 0 ? dur : null,
  };
}

document.getElementById('btn-add-income').addEventListener('click', () => showAddTxModal('income'));
document.getElementById('btn-add-expense').addEventListener('click', () => showAddTxModal('expense'));

// ── Categories ────────────────────────────────────────────────
async function loadCategories() {
  const cats = await api('/api/categories');
  if (!cats) return;
  const listEl = document.getElementById('categories-list');

  const incomes = cats.filter(c => c.type === 'income');
  const expenses = cats.filter(c => c.type === 'expense');

  const renderGroup = (arr, label) => `
    <div style="font-size:11px;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;margin-top:12px;">${label}</div>
    ${arr.map(c => `
      <div class="cat-item">
        <span class="cat-swatch" style="background:${c.color}"></span>
        <span class="cat-name">${escHtml(c.name)}</span>
        <button class="btn-sm danger" onclick="deleteCategory(${c.id})">Borrar</button>
      </div>`).join('')}`;

  listEl.innerHTML = renderGroup(incomes, 'Ingresos') + renderGroup(expenses, 'Gastos');
}

async function deleteCategory(id) {
  if (!confirm('¿Borrar esta categoría?')) return;
  const r = await api(`/api/categories/${id}`, { method: 'DELETE' });
  if (r?.success) { showToast('Categoría eliminada', 'success'); loadCategories(); }
}

const PALETTE = ['#ef4444','#f97316','#f59e0b','#eab308','#10b981','#14b8a6','#3b82f6','#6366f1','#8b5cf6','#ec4899','#6c63ff','#27AE60'];

document.getElementById('btn-add-category').addEventListener('click', () => {
  let selectedColor = PALETTE[0];
  openModal('Nueva Categoría', `
    <div class="input-group">
      <label>Nombre</label>
      <input type="text" id="f-cat-name" placeholder="Nombre de la categoría" />
    </div>
    <div class="input-group">
      <label>Tipo</label>
      <select id="f-cat-type">
        <option value="expense">Gasto</option>
        <option value="income">Ingreso</option>
      </select>
    </div>
    <div class="input-group">
      <label>Color</label>
      <div class="color-picker-row" id="color-picker">
        ${PALETTE.map((c, i) => `<span class="color-swatch ${i === 0 ? 'selected' : ''}" style="background:${c}" data-color="${c}"></span>`).join('')}
      </div>
    </div>
    <button class="btn-primary btn-full" id="modal-save-btn" style="margin-top:8px;">Crear Categoría</button>
  `);

  document.querySelectorAll('.color-swatch').forEach(s => {
    s.addEventListener('click', () => {
      document.querySelectorAll('.color-swatch').forEach(x => x.classList.remove('selected'));
      s.classList.add('selected');
      selectedColor = s.dataset.color;
    });
  });

  document.getElementById('modal-save-btn').onclick = async () => {
    const name = document.getElementById('f-cat-name').value.trim();
    const type = document.getElementById('f-cat-type').value;
    if (!name) { showToast('Escribe un nombre', 'error'); return; }
    const r = await api('/api/categories', { method: 'POST', body: JSON.stringify({ name, type, color: selectedColor }) });
    if (r?.id) { closeModal(); showToast('Categoría creada ✓', 'success'); loadCategories(); }
    else showToast(r?.error || 'Error', 'error');
  };
});

// ── Commitments ───────────────────────────────────────────────
async function loadCommitments() {
  const [items, summary] = await Promise.all([
    api('/api/commitments'),
    api('/api/commitments/summary'),
  ]);
  if (!items || !summary) return;

  const sumEl = document.getElementById('commitments-summary');
  sumEl.innerHTML = `
    <div class="sum-title">Total pendiente</div>
    <div class="sum-value">${fmt(summary.total_pending)}</div>
    ${summary.months_to_pay_estimation !== Infinity && summary.total_pending > 0
      ? `<div class="sum-note">Dedicando todos tus ingresos medios, liquidarías en ~${summary.months_to_pay_estimation.toFixed(1)} meses</div>` : ''}
  `;

  const listEl = document.getElementById('commitments-list');
  if (items.length === 0) {
    listEl.innerHTML = '<div class="empty-state"><div class="empty-icon">🎯</div><p>No hay compromisos registrados</p></div>';
    return;
  }

  listEl.innerHTML = items.map(c => `
    <div class="commitment-card" data-id="${c.id}">
      <div class="commitment-name">${escHtml(c.name)}</div>
      <div class="commitment-amounts">
        <span>Total: ${fmt(c.total_amount)}</span>
        <span>Pagado: ${fmt(c.total_paid)}</span>
      </div>
      <div class="commitment-progress">
        <div class="commitment-progress-fill" style="width:${Math.min(100, c.progress_pct).toFixed(1)}%"></div>
      </div>
      <div class="commitment-remaining">Pendiente: ${fmt(c.remaining)}</div>
      ${c.end_date ? `<div class="commitment-end">📌 Fin estimado: ${c.end_date}</div>` : ''}
      <div class="commitment-actions">
        ${c.remaining > 0 ? `
          <button class="btn-sm warn" onclick="showPaymentPlanModal(${c.id}, '${escHtml(c.name)}', ${c.remaining})">📅 Plan de Pagos</button>
          <button class="btn-sm success" onclick="showAportacionModal(${c.id}, '${escHtml(c.name)}', ${c.remaining})">💶 Aportación</button>
        ` : '<span style="color:var(--income);font-size:12px;font-weight:600;">✓ Liquidado</span>'}
        <button class="btn-sm danger" onclick="deleteCommitment(${c.id})">Borrar</button>
      </div>
    </div>`).join('');
}

async function deleteCommitment(id) {
  if (!confirm('¿Borrar este compromiso y todo su historial de pagos?')) return;
  const r = await api(`/api/commitments/${id}`, { method: 'DELETE' });
  if (r?.success) { showToast('Compromiso eliminado', 'success'); loadCommitments(); }
}

document.getElementById('btn-add-commitment').addEventListener('click', () => {
  openModal('Nuevo Compromiso', `
    <div class="input-group">
      <label>Nombre / Concepto</label>
      <input type="text" id="f-com-name" placeholder="ej: Préstamo coche" />
    </div>
    <div class="input-group">
      <label>Importe Total (€)</label>
      <input type="number" id="f-com-amount" placeholder="0.00" step="0.01" min="0.01" />
    </div>
    <button class="btn-primary btn-full" id="modal-save-btn" style="margin-top:8px;">Crear Compromiso</button>
  `);

  document.getElementById('modal-save-btn').onclick = async () => {
    const name = document.getElementById('f-com-name').value.trim();
    const amount = parseFloat(document.getElementById('f-com-amount').value);
    if (!name) { showToast('Escribe un nombre', 'error'); return; }
    if (isNaN(amount) || amount <= 0) { showToast('Importe no válido', 'error'); return; }
    const r = await api('/api/commitments', { method: 'POST', body: JSON.stringify({ name, total_amount: amount }) });
    if (r?.success || r?.id) { closeModal(); showToast('Compromiso creado ✓', 'success'); loadCommitments(); }
    else showToast(r?.error || 'Error', 'error');
  };
});

async function showPaymentPlanModal(cId, name, remaining) {
  const cats = await api('/api/categories?type=expense');
  if (!cats) return;
  const today = new Date().toISOString().slice(0, 10);

  openModal(`Plan de Pagos — ${name}`, `
    <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);border-radius:10px;padding:10px 14px;margin-bottom:16px;font-size:14px;">
      Pendiente total: <strong style="color:var(--expense);">${fmt(remaining)}</strong>
    </div>
    <div class="input-group">
      <label>Concepto del gasto</label>
      <input type="text" id="f-pp-name" value="Cuota ${name}" />
    </div>
    <div class="form-row">
      <div class="input-group">
        <label>Importe por cuota (€)</label>
        <input type="number" id="f-pp-amount" placeholder="0.00" step="0.01" oninput="autoCalcDuration(${remaining})" />
      </div>
      <div class="input-group">
        <label>Cada (meses)</label>
        <input type="number" id="f-pp-interval" value="1" min="1" max="24" oninput="updateLastDate()" />
      </div>
    </div>
    <div class="form-row">
      <div class="input-group">
        <label>Nº de cuotas</label>
        <input type="number" id="f-pp-duration" value="12" min="1" max="360" oninput="updateLastDate()" />
      </div>
      <div class="input-group">
        <label>Fecha inicio</label>
        <input type="date" id="f-pp-date" value="${today}" oninput="updateLastDate()" />
      </div>
    </div>
    <div class="input-group">
      <label>Categoría</label>
      <select id="f-pp-cat">
        ${cats.map(c => `<option value="${c.id}">${escHtml(c.name)}</option>`).join('')}
      </select>
    </div>
    <div style="font-size:13px;color:var(--free);font-weight:600;margin-bottom:16px;">📌 Última cuota: <span id="f-pp-last-date">—</span></div>
    <button class="btn-primary btn-full" id="modal-save-btn">📅 Crear Plan</button>
  `);

  updateLastDate();

  document.getElementById('modal-save-btn').onclick = async () => {
    const pName = document.getElementById('f-pp-name').value.trim();
    const amount = parseFloat(document.getElementById('f-pp-amount').value);
    const interval = parseInt(document.getElementById('f-pp-interval').value);
    const duration = parseInt(document.getElementById('f-pp-duration').value);
    const date = document.getElementById('f-pp-date').value;
    const catId = document.getElementById('f-pp-cat').value;

    if (!pName || isNaN(amount) || amount <= 0 || duration < 1) {
      showToast('Revisa los campos', 'error'); return;
    }
    const total = amount * duration;
    if (total > remaining) {
      showToast(`El plan (${fmt(total)}) supera lo pendiente (${fmt(remaining)})`, 'error'); return;
    }

    const r = await api(`/api/commitments/${cId}/plan`, {
      method: 'POST',
      body: JSON.stringify({ name: pName, amount, date, category_id: parseInt(catId), interval, duration }),
    });
    if (r?.success) {
      closeModal(); showToast('Plan creado ✓', 'success'); loadCommitments();
    } else showToast(r?.error || 'Error', 'error');
  };
}

function autoCalcDuration(remaining) {
  const amount = parseFloat(document.getElementById('f-pp-amount')?.value || 0);
  if (amount > 0) {
    const dur = Math.ceil(remaining / amount);
    document.getElementById('f-pp-duration').value = Math.min(dur, 360);
    updateLastDate();
  }
}

function updateLastDate() {
  const dateEl = document.getElementById('f-pp-date');
  const durEl = document.getElementById('f-pp-duration');
  const intEl = document.getElementById('f-pp-interval');
  const lastEl = document.getElementById('f-pp-last-date');
  if (!dateEl || !durEl || !lastEl) return;

  const startDate = new Date(dateEl.value + 'T00:00:00');
  const dur = parseInt(durEl.value) || 1;
  const interval = parseInt(intEl?.value) || 1;
  const monthsOffset = interval * (dur - 1);
  startDate.setMonth(startDate.getMonth() + monthsOffset);
  lastEl.textContent = startDate.toLocaleDateString('es-ES');
}

async function showAportacionModal(cId, name, remaining) {
  const cats = await api('/api/categories?type=expense');
  if (!cats) return;
  const today = new Date().toISOString().slice(0, 10);

  openModal(`Aportación — ${name}`, `
    <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);border-radius:10px;padding:10px 14px;margin-bottom:16px;font-size:14px;">
      Pendiente: <strong style="color:var(--expense);">${fmt(remaining)}</strong>
    </div>
    <div class="input-group">
      <label>Concepto del gasto</label>
      <input type="text" id="f-ap-name" value="Pago ${name}" />
    </div>
    <div class="form-row">
      <div class="input-group">
        <label>Importe (€)</label>
        <input type="number" id="f-ap-amount" placeholder="${remaining.toFixed(2)}" step="0.01" />
      </div>
      <div class="input-group">
        <label>Fecha</label>
        <input type="date" id="f-ap-date" value="${today}" />
      </div>
    </div>
    <div class="input-group">
      <label>Categoría</label>
      <select id="f-ap-cat">
        ${cats.map(c => `<option value="${c.id}">${escHtml(c.name)}</option>`).join('')}
      </select>
    </div>
    <button class="btn-primary btn-full" id="modal-save-btn">💶 Registrar Aportación</button>
  `);

  document.getElementById('modal-save-btn').onclick = async () => {
    const pName = document.getElementById('f-ap-name').value.trim();
    const amount = parseFloat(document.getElementById('f-ap-amount').value);
    const date = document.getElementById('f-ap-date').value;
    const catId = document.getElementById('f-ap-cat').value;

    if (!pName || isNaN(amount) || amount <= 0) {
      showToast('Revisa los campos', 'error'); return;
    }

    const r = await api(`/api/commitments/${cId}/payment`, {
      method: 'POST',
      body: JSON.stringify({ name: pName, amount, date, category_id: parseInt(catId) }),
    });
    if (r?.success) {
      closeModal(); showToast('Aportación registrada ✓', 'success'); loadCommitments();
    } else showToast(r?.error || 'Error', 'error');
  };
}

// ── Historic ──────────────────────────────────────────────────
async function loadHistoric() {
  const data = await api('/api/historic');
  if (!data) return;

  const incomes = data.incomes || [];
  const expenses = data.expenses || [];
  const balances = data.balances || [];

  const sumInc = incomes.reduce((a, b) => a + b, 0);
  const sumExp = expenses.reduce((a, b) => a + b, 0);
  const sumBal = balances.reduce((a, b) => a + b, 0);

  document.getElementById('hist-income').textContent = fmt(sumInc);
  document.getElementById('hist-expense').textContent = fmt(sumExp);
  const histBal = document.getElementById('hist-balance');
  histBal.textContent = fmt(sumBal);
  histBal.style.color = sumBal >= 0 ? 'var(--income)' : 'var(--expense)';

  // Line chart
  if (state.charts.histLine) state.charts.histLine.destroy();
  const ctx = document.getElementById('hist-line').getContext('2d');
  // Subsample for readability
  const step = Math.max(1, Math.floor(data.labels.length / 12));
  state.charts.histLine = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        { label: 'Ingresos', data: incomes, borderColor: '#10b981', tension: 0.3, pointRadius: 1, borderWidth: 2 },
        { label: 'Gastos', data: expenses, borderColor: '#ef4444', tension: 0.3, pointRadius: 1, borderWidth: 2 },
        { label: 'Balance', data: balances, borderColor: '#3b82f6', tension: 0.3, pointRadius: 1, borderWidth: 2 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#a0a0b8', font: { size: 10 } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${fmt(ctx.raw)}` } } },
      scales: {
        x: { ticks: { color: '#6b6b85', font: { size: 9 }, maxTicksLimit: 8 }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#6b6b85', font: { size: 9 }, callback: v => v + '€' }, grid: { color: 'rgba(255,255,255,0.04)' } }
      }
    }
  });

  // Year table
  const yearMap = {};
  data.labels.forEach((lbl, i) => {
    const parts = lbl.split(' ');
    const year = '20' + parts[1];
    if (!yearMap[year]) yearMap[year] = { inc: 0, exp: 0 };
    yearMap[year].inc += incomes[i];
    yearMap[year].exp += expenses[i];
  });

  const tableEl = document.getElementById('hist-year-table');
  const rows = Object.entries(yearMap).sort().map(([yr, d]) => {
    const bal = d.inc - d.exp;
    return `<tr>
      <td class="yr-col">${yr}</td>
      <td style="color:var(--income)">${fmt(d.inc)}</td>
      <td style="color:var(--expense)">${fmt(d.exp)}</td>
      <td style="color:${bal >= 0 ? 'var(--income)' : 'var(--expense)'}">${fmt(bal)}</td>
    </tr>`;
  }).join('');

  tableEl.innerHTML = `
    <table>
      <thead><tr><th>Año</th><th>Ingresos</th><th>Gastos</th><th>Balance</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="4" style="color:var(--text-3);text-align:center;padding:16px;">Sin datos</td></tr>'}</tbody>
    </table>`;
}

// ── Health ────────────────────────────────────────────────────
async function loadHealth() {
  const data = await api('/api/health');
  if (!data) return;

  document.getElementById('health-score-num').textContent = Math.round(data.score);
  document.getElementById('health-savings').textContent = fmtPct(data.savings_rate);
  document.getElementById('health-needs').textContent = fmtPct(data.needs_pct);
  document.getElementById('health-wants').textContent = fmtPct(data.wants_pct);
  document.getElementById('health-avg-income').textContent = fmt(data.avg_monthly_income);
  document.getElementById('health-avg-expense').textContent = fmt(data.avg_monthly_expense);

  // Score ring
  const circle = document.getElementById('health-score-circle');
  const circumference = 2 * Math.PI * 50; // r=50
  const offset = circumference - (data.score / 100) * circumference;
  setTimeout(() => { circle.style.strokeDashoffset = offset; }, 100);

  // Score color
  const score = data.score;
  const color = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444';
  circle.style.stroke = color;
  document.getElementById('health-score-num').style.color = color;
}

// ── Modal ─────────────────────────────────────────────────────
function openModal(title, bodyHtml) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHtml;
  document.getElementById('modal-overlay').style.display = 'flex';
}

function closeModal() {
  document.getElementById('modal-overlay').style.display = 'none';
  document.getElementById('modal-body').innerHTML = '';
}

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
});

// ── Helpers ───────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ── SAVINGS ──────────────────────────────────────────────────
async function loadSavings() {
  const data = await api('/api/savings');
  if (!data) return;
  
  const list = document.getElementById('savings-list');
  list.innerHTML = '';
  
  data.forEach(s => {
    const card = document.createElement('div');
    card.className = 'glass-card savings-card';
    const isNoCeiling = s.target_amount === 0;
    
    card.innerHTML = `
      <div class="savings-header">
        <div>
          <h4 class="savings-title">${s.name}</h4>
          <span class="savings-amount">${isNoCeiling ? 'Sin techo' : 'Meta: ' + fmt(s.target_amount)}</span>
        </div>
        <button class="btn-icon" data-id="${s.id}" data-action="delete">🗑️</button>
      </div>
      <div class="savings-progress-text">${fmt(s.total_saved)}</div>
      ${!isNoCeiling ? `
        <div class="progress-bar-track" style="margin-bottom:12px;">
          <div class="progress-bar-fill" style="width:${Math.min(100, s.progress_pct)}%; background:var(--accent);"></div>
        </div>
      ` : ''}
      <button class="btn-primary btn-full btn-sm" data-id="${s.id}" data-action="contribute">Aportar</button>
    `;
    
    // Add events
    card.querySelector('[data-action="delete"]').onclick = () => deleteSavings(s.id);
    card.querySelector('[data-action="contribute"]').onclick = () => openSavingsContributionModal(s.id, s.name);
    
    list.appendChild(card);
  });
}

async function deleteSavings(id) {
  if (!confirm('¿Eliminar esta hucha y todos sus registros?')) return;
  const r = await api(`/api/savings/${id}`, { method: 'DELETE' });
  if (r?.success) { showToast('Hucha eliminada', 'success'); loadSavings(); }
}

const btnAddSavings = document.getElementById('btn-add-savings');
if (btnAddSavings) {
  btnAddSavings.onclick = () => {
    openModal('Nueva Hucha', `
      <div class="input-group">
        <label>Nombre del propósito</label>
        <input type="text" id="f-savings-name" placeholder="Ej: Fondo de Emergencia" />
      </div>
      <div class="input-group">
        <label>Meta de ahorro (0 para sin techo)</label>
        <input type="number" id="f-savings-target" value="0" />
      </div>
      <button class="btn-primary btn-full" id="modal-save-savings-btn">Crear Hucha</button>
    `);
    document.getElementById('modal-save-savings-btn').onclick = async () => {
      const name = document.getElementById('f-savings-name').value;
      const target = document.getElementById('f-savings-target').value;
      if (!name) return showToast('Nombre obligatorio', 'error');
      const r = await api('/api/savings', { method: 'POST', body: JSON.stringify({ name, target_amount: target }) });
      if (r?.success) { closeModal(); showToast('Hucha creada ✓', 'success'); loadSavings(); }
    };
  };
}

async function openSavingsContributionModal(id, name) {
  const cats = await api('/api/categories?type=expense');
  openModal('Aportar a Hucha', `
    <p style="margin-bottom:12px;font-size:14px;color:var(--text-2);">Aportando a: <b>${name}</b></p>
    <div class="input-group">
      <label>Concepto</label>
      <input type="text" id="f-cont-name" value="Aportación hucha ${name}" />
    </div>
    <div class="input-group">
      <label>Cantidad</label>
      <input type="number" id="f-cont-amount" placeholder="0.00" />
    </div>
    <div class="input-group">
      <label>Fecha</label>
      <input type="date" id="f-cont-date" value="${new Date().toISOString().split('T')[0]}" />
    </div>
    <div class="input-group">
      <label>Categoría que asume el gasto</label>
      <select id="f-cont-cat">
        ${cats.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
      </select>
    </div>
    <button class="btn-primary btn-full" id="modal-save-cont-btn">Registrar Aportación</button>
  `);
  document.getElementById('modal-save-cont-btn').onclick = async () => {
    const cName = document.getElementById('f-cont-name').value;
    const amount = document.getElementById('f-cont-amount').value;
    const date = document.getElementById('f-cont-date').value;
    const cat = document.getElementById('f-cont-cat').value;
    if (!amount || amount <= 0) return showToast('Cantidad inválida', 'error');
    const r = await api(`/api/savings/${id}/contribution`, {
      method: 'POST',
      body: JSON.stringify({ name: cName, amount, date, category_id: cat })
    });
    if (r?.success) { closeModal(); showToast('¡Ahorro registrado! 🦈', 'success'); loadSavings(); }
  };
}

// ── MANUAL ────────────────────────────────────────────────────
async function loadManual() {
  const data = await api('/api/manual');
  if (!data) return;
  const list = document.getElementById('manual-content');
  if (!list) return;
  list.innerHTML = '';
  data.forEach(sec => {
    const card = document.createElement('div');
    card.className = 'glass-card manual-card';
    card.innerHTML = `
      <span class="manual-q">${sec.title}</span>
      <p class="manual-a">${sec.desc}</p>
    `;
    list.appendChild(card);
  });
}

// ── Boot ──────────────────────────────────────────────────────

initAuth();
