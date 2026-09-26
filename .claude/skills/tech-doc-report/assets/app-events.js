/* LAYER 4c -- the delegated event table and boot.
   Loaded last: start() runs here, so everything it touches is defined. */

/* @@BEGIN:JS:APP:EVENTS */
/* ---- events, delegated once ---- */
function setExpanded(id, on) {
  if (on) state.expanded.add(id); else state.expanded.delete(id);
  const art = document.getElementById(id);
  if (!art) return;
  art.dataset.open = on ? '1' : '0';
  const bd = document.getElementById('bd-' + id);
  if (bd) bd.hidden = !on;
  const hd = art.querySelector('.hd');
  if (hd) hd.setAttribute('aria-expanded', on ? 'true' : 'false');
}
document.addEventListener('click', ev => {
  const el = ev.target && ev.target.closest && ev.target.closest('[data-act]');
  if (!el) return;
  const act = el.dataset.act;

  if (act === 'item') {
    const id = el.dataset.id;
    setExpanded(id, !state.expanded.has(id));
    writeHash(state.expanded.has(id) ? id : '');
  } else if (act === 'card') {
    const open = el.getAttribute('aria-expanded') !== 'true';
    el.setAttribute('aria-expanded', open ? 'true' : 'false');
    const bd = el.nextElementSibling;
    if (bd) bd.hidden = !open;
  } else if (act === 'tab') {
    ev.preventDefault(); state.tab = el.dataset.tab; writeHash(); render();
  } else if (act === 'lang') {
    const y = window.scrollY;
    state.lang = el.dataset.next; writeHash(); render();
    window.scrollTo(0, y);
  } else if (act === 'theme') {
    state.theme = (document.documentElement.getAttribute('data-theme') === 'dark') ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    store.set(KEY + ':theme', state.theme);
    lastLang = null; render();
  } else if (act === 'print') {
    window.print();
  } else if (act === 'filter') {
    const g = el.dataset.g, v = el.dataset.v;
    if (state.filters[g].has(v)) state.filters[g].delete(v); else state.filters[g].add(v);
    render();
  } else if (act === 'reset') {
    Object.keys(state.filters).forEach(k => state.filters[k].clear());
    state.query = ''; const q = document.getElementById('q'); if (q) q.value = '';
    render();
  } else if (act === 'drawer') {
    drawer(!document.getElementById('sidebar').classList.contains('open'));
  } else if (act === 'cite') {
    ev.preventDefault();
    state.tab = 'sources'; render(); writeHash(el.dataset.sid);
    const s = document.getElementById('src-' + el.dataset.sid);
    if (s) s.scrollIntoView({block: 'center'});
  } else if (act === 'focus') {
    ev.preventDefault();
    const id = el.dataset.id;
    if (state.tab !== 'report') { state.tab = 'report'; render(); }
    setExpanded(id, true); writeHash(id);
    const tgt = document.getElementById(id);
    if (tgt) tgt.scrollIntoView({block: 'start'});
  } else if (act === 'jump') {
    /* Letting the browser follow the href would replace the whole hash with
       "#sec-H" and throw away the language and tab, so a reload after using
       the sidebar would open somewhere else. Scroll ourselves and keep the
       hash canonical -- which also makes a section deep-linkable. */
    ev.preventDefault();
    drawer(false);
    const id = el.getAttribute('href').slice(1);
    writeHash(id);
    const tgt = document.getElementById(id);
    if (tgt) tgt.scrollIntoView({block: 'start'});
  } else if (act === 'srcgroup') {
    state.srcGroup = el.dataset.g; render();
  } else if (act === 'copy') {
    copyText(el.dataset.copy, () => {
      el.dataset.done = '1';
      const was = el.innerHTML;
      el.textContent = t('ui.copied', state.lang);
      say(t('ui.copied', state.lang));
      setTimeout(() => { el.innerHTML = was; delete el.dataset.done; }, 1400);
    });
  } else if (act === 'download') {
    try {
      const url = URL.createObjectURL(new Blob([RAW], {type: 'application/json'}));
      const a = document.createElement('a');
      a.href = url; a.download = (DATA.meta.report_id || 'report') + '.json';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) { console.warn('[report] download unavailable, use Copy instead', e); }
  } else if (act === 'yt') {
    /* Only now does anything leave the page. nocookie keeps it to one host. */
    const box = el.parentNode;
    const fr = document.createElement('iframe');
    fr.src = 'https://www.youtube-nocookie.com/embed/' + box.dataset.yt +
      '?autoplay=1&rel=0' + (+box.dataset.start ? '&start=' + box.dataset.start : '');
    fr.allow = 'accelerometer;autoplay;encrypted-media;picture-in-picture';
    fr.allowFullscreen = true;
    fr.title = el.textContent.trim();
    box.innerHTML = ''; box.appendChild(fr);
  }
});
document.addEventListener('change', ev => {
  const el = ev.target.closest('[data-act="check"]');
  if (!el) return;
  const id = el.dataset.id;
  if (el.checked) state.checked.add(id); else state.checked.delete(id);
  el.closest('li').dataset.done = el.checked ? '1' : '0';
  store.set(KEY + ':checked', Array.from(state.checked));
});
document.addEventListener('input', ev => {
  if (ev.target.id !== 'q') return;
  clearTimeout(window.__qt);
  window.__qt = setTimeout(() => { state.query = ev.target.value; render(); }, 160);
});
document.addEventListener('keydown', ev => {
  if (ev.key === 'Escape') { drawer(false); return; }
  const tab = ev.target.closest && ev.target.closest('[role="tab"]');
  if (tab && (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft')) {
    ev.preventDefault();
    const i = TABS.indexOf(state.tab);
    state.tab = TABS[(i + (ev.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length];
    writeHash(); render();
    const nt = document.getElementById('tab-' + state.tab); if (nt) nt.focus();
  }
});
function drawer(open) {
  const sb = document.getElementById('sidebar'), sc = document.getElementById('scrim'),
        bt = document.getElementById('navbtn');
  sb.classList.toggle('open', !!open);
  sc.hidden = !open;
  if (bt) bt.setAttribute('aria-expanded', open ? 'true' : 'false');
}
window.addEventListener('hashchange', () => {
  if (hashByUs) { hashByUs = false; return; }
  const h = readHash();
  if (!h || !state) return;
  let dirty = false;
  if (h.lang && h.lang !== state.lang) { state.lang = h.lang; dirty = true; }
  if (h.tab && h.tab !== state.tab) { state.tab = h.tab; dirty = true; }
  if (dirty) render(h.id); else if (h.id) { setExpanded(h.id, true); }
});
/* @@END:JS:APP:EVENTS */

/* @@BEGIN:JS:APP:BOOT */
/* ---- boot ---- */
function start() {
  readData();
  const scrim = document.getElementById('scrim');
  if (scrim) scrim.addEventListener('click', () => drawer(false));

  if (state.theme) document.documentElement.setAttribute('data-theme', state.theme);
  else state.theme = window.matchMedia && window.matchMedia('(prefers-color-scheme:dark)').matches
    ? 'dark' : 'light';
  const h = readHash();
  if (h) {
    if (h.lang && LANGS.indexOf(h.lang) >= 0) state.lang = h.lang;
    if (h.tab) state.tab = h.tab;
    if (h.id) state.expanded.add(h.id);
  }
  render(h && h.id);
  writeHash(h && h.id);

  /* A top-level binding in a classic script is script-scoped, not a window
     property, so without this handle neither the browser console nor the
     acceptance suite can reach the data or re-render. One named object
     rather than a dozen globals. */
  window.REPORT = {DATA: DATA, RAW: RAW, I18N: I18N, state: state,
                   Atoms: Atoms, Biz: Biz, render: render, idx: idx};
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
else start();
/* @@END:JS:APP:BOOT */
