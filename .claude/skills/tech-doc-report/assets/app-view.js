/* LAYER 4b -- filtering, search, the hash router, and render(). */

/* @@BEGIN:JS:APP:FILTER */
/* ---- filtering and search ---- */
function itemText(it) {
  const parts = [it.name, L(it.headline, state.lang).text, L(it.body, state.lang).text,
    (it.commands || []).join(' ')];
  (it.source_ids || []).forEach(sid => {
    const s = idx.sourcesById[sid];
    if (s) parts.push(s.title, s.publisher);
  });
  return norm(parts.join(' '));
}
function itemPasses(it) {
  const f = state.filters;
  if (f.action.size && !f.action.has(it.action)) return false;
  if (f.truth.size && !f.truth.has(it.truth)) return false;
  if (f.tag.size && !(it.tags || []).some(x => f.tag.has(x))) return false;
  if (f.stack.size && !(it.stack_relevance || []).some(x => f.stack.has(x))) return false;
  const nq = norm(state.query);
  if (nq && itemText(it).indexOf(nq) < 0) return false;
  return true;
}
/* Facet counts ignore their own group, so a chip never reads 0 for something
   you can still turn on -- the count answers "how many would I get", not
   "how many are left after I already filtered by this". */
function counts() {
  const out = {section: {}, facet: {action: {}, truth: {}, tag: {}, stack: {}}, total: 0};
  (DATA.sections || []).forEach(s => {
    out.section[s.id] = (s.items || []).filter(itemPasses).length;
    out.total += out.section[s.id];
  });
  const saved = state.filters;
  Object.keys(out.facet).forEach(g => {
    state.filters = Object.assign({}, saved, {[g]: new Set()});
    const pool = idx.all.filter(itemPasses);
    state.filters = saved;
    const vals = g === 'stack' ? (DATA.meta.stack || []) : FILTER_VALUES[g];
    vals.forEach(v => {
      out.facet[g][v] = pool.filter(it =>
        g === 'action' ? it.action === v :
        g === 'truth' ? it.truth === v :
        g === 'tag' ? (it.tags || []).indexOf(v) >= 0 :
        (it.stack_relevance || []).indexOf(v) >= 0).length;
    });
  });
  return out;
}
/* @@END:JS:APP:FILTER */

/* @@BEGIN:JS:APP:ROUTER */
/* ---- hash routing: #<lang>/<tab>[/<id>] ---- */
function readHash() {
  const p = (location.hash || '').replace(/^#/, '').split('/').filter(Boolean);
  if (!p.length) return null;
  const out = {};
  if (LANGS.indexOf(p[0]) >= 0) { out.lang = p[0]; p.shift(); }
  if (p.length && TABS.indexOf(p[0]) >= 0) { out.tab = p[0]; p.shift(); }
  if (p.length) out.id = p.join('/');
  return out;
}
let hashByUs = false;
function writeHash(id) {
  const h = '#' + state.lang + '/' + state.tab + (id ? '/' + id : '');
  if (location.hash === h) return;
  try {
    history.replaceState(null, '', h);
  } catch (e) {
    /* Some engines refuse replaceState on a file:// URL. The hash itself still
       works, so fall back to it rather than losing deep links entirely --
       and flag it, because assigning to location.hash fires hashchange. */
    hashByUs = true;
    location.hash = h;
  }
}
/* @@END:JS:APP:ROUTER */

/* @@BEGIN:JS:APP:RENDER */
/* ---- render ---- */
let lastLang = null;
function mountTopBar(ctx) {
  const box = document.getElementById('topbar');
  const old = document.getElementById('q');
  const val = old ? old.value : state.query;
  const had = old && document.activeElement === old;
  box.innerHTML = Biz.TopBar(DATA, ctx);
  const q = document.getElementById('q');
  q.value = val;
  if (had) { q.focus(); try { q.setSelectionRange(val.length, val.length); } catch (e) {} }
}
function render(focusId) {
  const ctx = makeCtx();
  if (lastLang !== state.lang) {
    document.documentElement.lang = state.lang;
    document.documentElement.setAttribute('data-lang', state.lang);
    mountTopBar(ctx);
    lastLang = state.lang;
  }
  document.getElementById('sidebar').innerHTML = Biz.Sidebar(DATA, ctx);
  document.getElementById('tabs').innerHTML = Atoms.Tabs([
    {id: 'report', label: ctx.t('tab.report'), n: ctx.counts.total},
    {id: 'sources', label: ctx.t('tab.sources'), n: (DATA.sources || []).length},
    {id: 'json', label: ctx.t('tab.json')}
  ], state.tab);

  const view = document.getElementById('view');
  if (state.tab === 'report') {
    let h = Biz.HeroHighlights(DATA, ctx) + Biz.StackActionsTable(DATA, ctx) +
      Biz.DeadlineTimeline(DATA, ctx);
    const secs = (DATA.sections || []).slice().sort((a, b) => (a.order || 0) - (b.order || 0));
    h += secs.map(s => Biz.SectionBlock(s, ctx)).join('');
    if (!ctx.counts.total && (state.query || anyFilter())) h += Atoms.EmptyState(ctx.t('ui.no_results'));
    h += Biz.ChecklistBlock(DATA, ctx) + Biz.VerifyList(DATA, ctx) +
      Biz.ConflictsPanel(DATA, ctx) + Biz.GlossaryBlock(DATA, ctx);
    view.innerHTML = h;
  } else if (state.tab === 'sources') {
    view.innerHTML = Biz.SourcesTab(DATA, ctx);
  } else {
    view.innerHTML = Biz.JsonTab(DATA, ctx);
  }
  view.setAttribute('role', 'tabpanel');
  view.setAttribute('aria-labelledby', 'tab-' + state.tab);
  spy();
  if (focusId) {
    const el = document.getElementById(focusId) || document.getElementById('src-' + focusId);
    if (el) el.scrollIntoView({block: 'start', behavior: 'auto'});
  }
}
const anyFilter = () => Object.keys(state.filters).some(k => state.filters[k].size > 0);
function say(msg) { const l = document.getElementById('live'); if (l) l.textContent = msg; }
/* @@END:JS:APP:RENDER */

/* @@BEGIN:JS:APP:SPY */
/* ---- scroll-spy ---- */
let obs = null;
function spy() {
  if (obs) obs.disconnect();
  if (state.tab !== 'report' || !window.IntersectionObserver) return;
  const links = {};
  Array.from(document.querySelectorAll('#sidebar a')).forEach(a => { links[a.getAttribute('href').slice(1)] = a; });
  const targets = Array.from(document.querySelectorAll('.sec[id], .blk[id]'));
  obs = new IntersectionObserver(es => {
    es.forEach(e => {
      const a = links[e.target.id];
      if (!a) return;
      if (e.isIntersecting) {
        Object.keys(links).forEach(k => links[k].removeAttribute('aria-current'));
        a.setAttribute('aria-current', 'true');
      }
    });
  }, {rootMargin: '-15% 0px -70% 0px'});
  targets.forEach(el => obs.observe(el));
}
/* @@END:JS:APP:SPY */
