/* ===== Helpers ===== */

function fmt(amount) {
  if (amount == null) return '—';
  return '₹' + Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function currentMonth() {
  const d = new Date();
  return d.toISOString().slice(0, 7); // YYYY-MM
}

function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }

/* ===== State ===== */
let _parsedData = null;

/* ===== On load ===== */
window.addEventListener('DOMContentLoaded', () => {
  const today = currentMonth();
  document.getElementById('month-picker').value = today;
  document.getElementById('filter-month').value = today;
  loadSummary();
  loadTransactions();
});

/* ===== Parse SMS ===== */
async function parseSMS() {
  const message = document.getElementById('sms-input').value.trim();
  const errEl = document.getElementById('parse-error');
  const resultEl = document.getElementById('parse-result');

  hide(errEl);
  hide(resultEl);
  _parsedData = null;

  if (!message) {
    errEl.textContent = 'Please paste an SMS message first.';
    show(errEl);
    return;
  }

  try {
    const res = await fetch('/api/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();

    if (!res.ok) {
      errEl.textContent = data.error || 'Failed to parse message.';
      show(errEl);
      return;
    }

    _parsedData = { ...data, raw_message: message };
    renderParseResult(data);
    show(resultEl);
  } catch (e) {
    errEl.textContent = 'Network error. Is the server running?';
    show(errEl);
  }
}

function renderParseResult(data) {
  const fields = document.getElementById('parse-fields');
  const amountClass = data.transaction_type === 'debit' ? 'debit' : 'credit';
  const sign = data.transaction_type === 'debit' ? '−' : '+';

  fields.innerHTML = `
    <div class="field-item">
      <div class="field-label">Amount</div>
      <div class="field-value ${amountClass}">${sign} ${fmt(data.amount)}</div>
    </div>
    <div class="field-item">
      <div class="field-label">Type</div>
      <div class="field-value">${data.transaction_type || '—'}</div>
    </div>
    <div class="field-item">
      <div class="field-label">Date</div>
      <div class="field-value">${fmtDate(data.date)}</div>
    </div>
    <div class="field-item">
      <div class="field-label">Account</div>
      <div class="field-value">****${data.account_number || '—'}</div>
    </div>
    <div class="field-item">
      <div class="field-label">Account Type</div>
      <div class="field-value">${data.account_type === 'credit_card' ? 'Credit Card' : 'Bank'}</div>
    </div>
    <div class="field-item">
      <div class="field-label">Balance</div>
      <div class="field-value">${fmt(data.balance)}</div>
    </div>
  `;

  document.getElementById('edit-merchant').value = data.merchant || '';

  const catSel = document.getElementById('edit-category');
  const cat = data.category || 'Other';
  for (let i = 0; i < catSel.options.length; i++) {
    if (catSel.options[i].value === cat) { catSel.selectedIndex = i; break; }
  }

  hide(document.getElementById('save-status'));
}

function clearParse() {
  document.getElementById('sms-input').value = '';
  hide(document.getElementById('parse-error'));
  hide(document.getElementById('parse-result'));
  _parsedData = null;
}

/* ===== Save Transaction ===== */
async function saveTransaction() {
  if (!_parsedData) return;

  const statusEl = document.getElementById('save-status');
  hide(statusEl);

  const payload = {
    ..._parsedData,
    merchant: document.getElementById('edit-merchant').value.trim() || _parsedData.merchant,
    category: document.getElementById('edit-category').value,
  };

  try {
    const res = await fetch('/api/transactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      statusEl.textContent = data.error || 'Save failed.';
      statusEl.className = 'save-status alert alert-error';
      show(statusEl);
      return;
    }

    statusEl.textContent = '✓ Transaction saved successfully!';
    statusEl.className = 'save-status alert alert-success';
    show(statusEl);

    // Refresh tables
    loadTransactions();
    loadSummary();
  } catch (e) {
    statusEl.textContent = 'Network error.';
    statusEl.className = 'save-status alert alert-error';
    show(statusEl);
  }
}

/* ===== Load Summary ===== */
async function loadSummary() {
  const month = document.getElementById('month-picker').value || currentMonth();

  try {
    const res = await fetch(`/api/summary?month=${month}`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById('total-debit').textContent = fmt(data.total_debit);
    document.getElementById('total-credit').textContent = fmt(data.total_credit);
    document.getElementById('txn-count').textContent = data.transaction_count;

    renderCategoryChart(data.category_totals || {});
    renderAccountBalances(data.account_balances || []);
  } catch (e) {
    // silently ignore if server not ready
  }
}

function renderCategoryChart(totals) {
  const el = document.getElementById('category-chart');
  const entries = Object.entries(totals).sort((a, b) => b[1] - a[1]);

  if (!entries.length) {
    el.innerHTML = '<p style="color:var(--muted);font-size:.85rem">No spending data for this month.</p>';
    return;
  }

  const max = entries[0][1];
  el.innerHTML = entries.map(([cat, amt]) => `
    <div class="chart-row">
      <span class="chart-label">${cat}</span>
      <div class="chart-bar-wrap">
        <div class="chart-bar" style="width:${Math.round((amt / max) * 100)}%"></div>
      </div>
      <span class="chart-amount">${fmt(amt)}</span>
    </div>
  `).join('');
}

function renderAccountBalances(balances) {
  const el = document.getElementById('account-balances');
  if (!balances.length) {
    el.innerHTML = '<p style="color:var(--muted);font-size:.85rem">No account data yet.</p>';
    return;
  }
  el.innerHTML = balances.map(a => `
    <div class="account-card ${a.account_type === 'credit_card' ? 'credit-card' : ''}">
      <div class="acct-label">Available Balance</div>
      <div class="acct-number">****${a.account_number}</div>
      <div class="acct-balance">${fmt(a.balance)}</div>
      <div class="acct-type">${a.account_type === 'credit_card' ? 'Credit Card' : 'Bank Account'}</div>
    </div>
  `).join('');
}

/* ===== Load Transactions ===== */
async function loadTransactions() {
  const month = document.getElementById('filter-month').value || currentMonth();
  const type = document.getElementById('filter-type').value;
  const category = document.getElementById('filter-category').value;

  const params = new URLSearchParams({ month });
  if (type) params.set('type', type);
  if (category) params.set('category', category);

  try {
    const res = await fetch(`/api/transactions?${params}`);
    if (!res.ok) return;
    const data = await res.json();
    renderTransactions(data);
  } catch (e) {
    // silently ignore
  }
}

function renderTransactions(transactions) {
  const tableEl = document.getElementById('txn-table');
  const emptyEl = document.getElementById('txn-empty');
  const tbody = document.getElementById('txn-tbody');

  if (!transactions.length) {
    hide(tableEl);
    show(emptyEl);
    return;
  }

  hide(emptyEl);
  show(tableEl);

  tbody.innerHTML = transactions.map(t => `
    <tr>
      <td>${fmtDate(t.date)}</td>
      <td><span class="badge badge-${t.transaction_type}">${t.transaction_type}</span></td>
      <td class="amount-${t.transaction_type}">${t.transaction_type === 'debit' ? '−' : '+'} ${fmt(t.amount)}</td>
      <td>${t.merchant || '<span style="color:var(--muted)">—</span>'}</td>
      <td><span class="badge badge-category">${t.category}</span></td>
      <td>${t.account_number ? '****' + t.account_number : '—'}</td>
      <td>${fmt(t.balance)}</td>
      <td>
        <button class="btn btn-danger" onclick="deleteTransaction(${t.id})" title="Delete">&#128465;</button>
      </td>
    </tr>
  `).join('');
}

/* ===== Delete Transaction ===== */
async function deleteTransaction(id) {
  if (!confirm('Delete this transaction?')) return;

  try {
    const res = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
    if (res.ok) {
      loadTransactions();
      loadSummary();
    }
  } catch (e) {
    alert('Delete failed. Check server connection.');
  }
}
