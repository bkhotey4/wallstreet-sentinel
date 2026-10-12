/* Private holdings stay in memory. Authentication is delegated to the pinned SDK. */
(function (root) {
  'use strict';
  const empty = () => ({v: 1, h: [], cash: []});
  const copy = value => JSON.parse(JSON.stringify(value));
  function clean(value) {
    if (!value || value.v !== 1 || !Array.isArray(value.h) || !Array.isArray(value.cash) ||
        value.h.length > 2000 || value.cash.length > 3) throw new Error('INVALID');
    const seen = new Set(), currencies = new Set();
    const h = value.h.map(row => {
      if (!row || typeof row.s !== 'string' || !/^[A-Z0-9.\-^=]{1,16}$/.test(row.s) || seen.has(row.s) ||
          !Number.isFinite(row.n) || row.n <= 0 || !Number.isFinite(row.c) || row.c < 0 ||
          !Number.isFinite(row.p) || row.p < 0) throw new Error('INVALID');
      seen.add(row.s);
      return {s: row.s, n: row.n, c: row.c, p: row.p};
    });
    const cash = value.cash.map(row => {
      if (!row || !['TWD', 'USD', 'HKD'].includes(row.cur) || currencies.has(row.cur) || !Number.isFinite(row.a)) throw new Error('INVALID');
      currencies.add(row.cur);
      return {cur: row.cur, a: row.a};
    });
    return {v: 1, h, cash};
  }
  class Store {
    constructor(client, changed) {
      this.client = client; this.changed = changed; this.epoch = 0;
      this.user = null; this.ready = false; this.busy = false;
      this.data = empty(); this.version = 0; this.updated = null; this.message = '';
    }
    get() { return copy(this.data); }
    notify(message) { if (message !== undefined) this.message = message; this.changed(this); }
    reset(user) {
      ++this.epoch; this.user = user; this.ready = false; this.busy = false;
      this.data = empty(); this.version = 0; this.updated = null;
      this.notify(user ? '正在讀取私人持倉…' : '請使用 Google 登入。');
    }
    async session(session) {
      const user = session && session.user;
      if (user && this.user && user.id === this.user.id) return;
      this.reset(user || null);
      if (user) await this.reload();
    }
    accept(row) {
      if (!row || !Number.isSafeInteger(row.version) || row.version < 0) throw new Error('INVALID');
      this.data = clean(row.document); this.version = row.version; this.updated = row.updated_at; this.ready = true;
    }
    async reload() {
      if (!this.user || this.busy) return false;
      const epoch = this.epoch; this.busy = true; this.notify('正在同步…');
      try {
        const result = await this.client.load(this.user.id);
        if (epoch !== this.epoch) return false;
        if (result.error) throw result.error;
        this.accept(result.data); this.notify('已同步'); return true;
      } catch (error) {
        if (epoch === this.epoch) {
          this.ready = false; this.data = empty();
          this.notify(error.code === 'permission-denied' ? '此 Google 帳號尚未獲准存取。' : '讀取失敗，請檢查網路後按「重新同步」。');
        }
        return false;
      } finally { if (epoch === this.epoch) { this.busy = false; this.notify(); } }
    }
    async put(value) {
      if (!this.ready || this.busy) return false;
      let document;
      try { document = clean(value); } catch (_) { this.notify('資料格式不正確，未儲存。'); return false; }
      const epoch = this.epoch; this.busy = true; this.notify('儲存中…');
      try {
        const result = await this.client.save(this.user.id, this.version, document);
        if (epoch !== this.epoch) return false;
        if (result.error) throw result.error;
        this.accept(result.data); this.notify('已同步'); return true;
      } catch (error) {
        if (epoch === this.epoch) {
          if (error.code === 'permission-denied') { this.ready = false; this.data = empty(); }
          this.notify(error.code === 'version-conflict'
            ? '另一台裝置已更新。這次修改未儲存；請重新同步後再修改。'
            : '尚未確認儲存成功。請重新同步核對雲端資料，再重試。');
        }
        return false;
      } finally { if (epoch === this.epoch) { this.busy = false; this.notify(); } }
    }
  }
  // Transactions run on the server; Firestore rules enforce the same version check.
  function firebaseClient(db, auth, serverTimestamp) {
    function check(uid) {
      if (!auth.currentUser || auth.currentUser.uid !== uid) throw Object.assign(new Error('Signed out'), {code: 'permission-denied'});
    }
    function row(snap) {
      if (!snap.exists) return {document: empty(), version: 0, updated_at: null};
      const value = snap.data();
      return {...value, updated_at: value.updated_at.toDate().toISOString()};
    }
    return {
      async load(uid) {
        check(uid);
        const snap = await db.collection('wssPortfolios').doc(uid).get({source: 'server'});
        check(uid); return {data: row(snap)};
      },
      async save(uid, version, value) {
        check(uid); const document = clean(value);
        const ref = db.collection('wssPortfolios').doc(uid);
        await db.runTransaction(async tx => {
          check(uid);
          const snap = await tx.get(ref);
          const currentVersion = snap.exists ? snap.data().version : 0;
          if (currentVersion !== version) throw Object.assign(new Error('Version conflict'), {code: 'version-conflict'});
          const next = {document, version: version + 1, updated_at: serverTimestamp()};
          tx.set(ref, next);
          tx.set(ref.collection('revisions').doc(String(next.version)), next);
        });
        return this.load(uid);
      }
    };
  }
  if (typeof module !== 'undefined' && module.exports) { module.exports = {Store, clean, firebaseClient}; return; }
  root.WSSPortfolioCloud = {Store, clean, firebaseClient};
})(typeof window !== 'undefined' ? window : globalThis);

/* UI adapter. No Google client secret or database service key belongs here. */
if (typeof window !== 'undefined') window.startPortfolioCloud = async function (config, render) {
  const byId = id => document.getElementById(id);
  const panel = byId('pfprivate'), status = byId('pfcloudstatus');
  let store, signingOut = false;
  function changed(s) {
    panel.hidden = !s.ready;
    panel.querySelectorAll('input,button,select,textarea').forEach(e => { e.disabled = s.busy || !s.ready; });
    byId('pflogin').hidden = !!s.user;
    byId('pflogout').hidden = !s.user;
    byId('pfrefresh').hidden = !s.user;
    byId('pfrefresh').disabled = s.busy;
    byId('pfmigrate').hidden = !s.ready || !hasLegacy();
    byId('pfmigrate').disabled = s.busy;
    byId('pfaccount').textContent = s.user ? (s.user.email || '') : '';
    status.textContent = s.message + (s.updated && s.ready ? ' · 雲端更新：' + new Date(s.updated).toLocaleString() : '');
    render();
  }
  function hasLegacy() { try { return !!localStorage.getItem('wss_portfolio_v1'); } catch (_) { return false; } }
  function downloadLegacy() {
    try {
      const value = localStorage.getItem('wss_portfolio_v1'); if (!value) return;
      const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([value], {type: 'application/json'}));
      a.download = 'holdings-local-backup.json'; document.body.appendChild(a); a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    } catch (_) { status.textContent = '無法讀取本機備份。'; }
  }
  byId('pflegacyexport').hidden = !hasLegacy();
  byId('pflegacyexport').onclick = downloadLegacy;
  if (!config.apiKey || !config.projectId) { status.textContent = '私人持倉同步尚未啟用；原有本機資料仍保留，可先匯出備份。'; return; }
  try {
    for (const name of ['app', 'auth', 'firestore']) await new Promise((resolve, reject) => {
      const script = document.createElement('script'); script.src = 'firebase-' + name + '-compat-12.19.0.js';
      script.onload = resolve; script.onerror = reject; document.head.appendChild(script);
    });
    const app = window.firebase.initializeApp(config, 'wss-private');
    const auth = app.auth(), db = app.firestore();
    // Default Firestore cache is memory only. Never enable disk persistence for holdings.
    await auth.setPersistence(window.firebase.auth.Auth.Persistence.SESSION);
    const client = window.WSSPortfolioCloud.firebaseClient(db, auth, () => window.firebase.firestore.FieldValue.serverTimestamp());
    store = new window.WSSPortfolioCloud.Store(client, changed);
    window.wssPortfolioStore = store;
    byId('pflogin').disabled = false;
    byId('pflogin').onclick = async function () {
      signingOut = false;
      this.disabled = true;
      try {
        const provider = new window.firebase.auth.GoogleAuthProvider();
        provider.setCustomParameters({prompt: 'select_account'});
        await auth.signInWithPopup(provider);
      } catch (error) {
        status.textContent = error.code === 'auth/popup-blocked' ? '瀏覽器封鎖登入視窗，請允許彈出視窗後重試；手機請使用 Safari 或 Chrome。'
          : error.code === 'auth/unauthorized-domain' ? '此網站尚未加入 Firebase 的授權網域。'
          : 'Google 登入未完成，請重新點選登入。';
      } finally { this.disabled = false; }
    };
    byId('pflogout').onclick = async () => {
      signingOut = true;
      store.reset(null);
      try {
        await auth.signOut();
      } catch (_) { status.textContent = '畫面已清除，登出未完成；請關閉此分頁以清除登入工作階段。'; }
    };
    byId('pfrefresh').onclick = () => store.reload();
    byId('pfmigrate').onclick = async () => {
      if (!confirm('將本機持倉匯入目前登入的帳號，取代此帳號的雲端持倉？本機原始資料會保留。')) return;
      try {
        const value = JSON.parse(localStorage.getItem('wss_portfolio_v1'));
        // Legacy files may omit the optional cash collection.
        if (value && !value.cash) value.cash = [];
        if (await store.put(value)) status.textContent = '已匯入雲端，本機原始資料仍保留。';
      } catch (_) { status.textContent = '本機持倉格式不正確，請先匯出備份。'; }
    };
    auth.onAuthStateChanged(user => {
      if (!signingOut || !user) store.session(user ? {user: {id: user.uid, email: user.email}} : null);
    });
  } catch (_) {
    if (store) store.reset(null);
    status.textContent = '登入服務載入失敗，請重新整理；若持續失敗，請檢查 Firebase 設定。';
  }
};
