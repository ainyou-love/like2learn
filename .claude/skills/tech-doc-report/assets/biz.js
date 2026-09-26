/* Business components read DATA through ctx.state.idx and compose atoms.
   One component = one CSS region + one JS region with the same name. */
const Biz = {};

/* @@BEGIN:JS:BIZ:TopBar */
Biz.TopBar = (D, ctx) => {
  const w = D.meta.time_window;
  const langs = D.meta.languages || ['vi'];
  const next = langs[(langs.indexOf(ctx.lang) + 1) % langs.length];
  return '<button type="button" class="ctl" id="navbtn" data-act="drawer"' +
      ' aria-expanded="false" aria-controls="sidebar" aria-label="' + esc(ctx.t('ui.menu')) + '">' +
      Atoms.Icon('menu') + '</button>' +
    '<span class="brand"><b>' + Atoms.Text(D.meta.title, ctx) + '</b>' +
      '<small>' + esc(w.from) + ' → ' + esc(w.to) + '</small></span>' +
    '<span class="grow"></span>' +
    '<label class="search">' + Atoms.Icon('search') +
      '<input id="q" type="search" autocomplete="off" placeholder="' +
      esc(ctx.t('ui.search')) + '" aria-label="' + esc(ctx.t('ui.search')) + '"></label>' +
    '<button type="button" class="ctl" data-act="lang" data-next="' + esc(next) + '" title="' +
      esc(ctx.t('ui.lang')) + '">' + esc(ctx.lang.toUpperCase()) + '</button>' +
    '<button type="button" class="ctl" data-act="theme" aria-pressed="' +
      (ctx.state.theme === 'dark' ? 'true' : 'false') + '" title="' + esc(ctx.t('ui.theme')) + '">' +
      Atoms.Icon(ctx.state.theme === 'dark' ? 'sun' : 'moon') + '</button>' +
    '<button type="button" class="ctl" data-act="print" title="' + esc(ctx.t('ui.print')) + '">' +
      Atoms.Icon('print') + '</button>';
};
/* @@END:JS:BIZ:TopBar */

/* @@BEGIN:JS:BIZ:Sidebar */
Biz.Sidebar = (D, ctx) => {
  const c = ctx.counts;
  const link = (href, label, n, key) =>
    '<a href="' + href + '" data-act="jump"' + (n == null ? '' : ' data-n="' + n + '"') + '>' +
    (key ? '<span class="k">' + esc(key) + '</span>' : '') + '<span>' + esc(label) + '</span>' +
    (n == null ? '' : '<span class="n">' + n + '</span>') + '</a>';
  let h = '<h4>' + esc(ctx.t('nav.overview')) + '</h4>' +
    link('#b-highlights', ctx.t('nav.highlights'), (D.highlights || []).length) +
    link('#b-stack', ctx.t('nav.stack_actions'), (D.stack_actions || []).length) +
    link('#b-deadlines', ctx.t('nav.deadlines'), (D.deadlines || []).length) +
    '<h4>' + esc(ctx.t('nav.topics')) + '</h4>';
  (D.sections || []).forEach(s => {
    h += link('#sec-' + s.id, L(s.title, ctx.lang).text, c.section[s.id] || 0, s.id);
  });
  h += '<h4>' + esc(ctx.t('nav.wrapup')) + '</h4>' +
    link('#b-checklist', ctx.t('nav.checklist'), (D.checklist || []).length) +
    link('#b-verify', ctx.t('nav.verify'), (D.verify || []).length) +
    link('#b-conflicts', ctx.t('nav.conflicts'), (D.conflicts || []).length) +
    link('#b-glossary', ctx.t('nav.glossary'), (D.glossary || []).length) +
    Biz.FilterPanel(D, ctx);
  return h;
};
/* @@END:JS:BIZ:Sidebar */

/* @@BEGIN:JS:BIZ:FilterPanel */
/* AND across groups, OR inside one: picking patch_now + try_now widens the
   result, adding a stack filter narrows it. That is the combination people
   actually reach for -- "anything urgent that touches Postgres". */
Biz.FilterPanel = (D, ctx) => {
  const groups = [
    ['action', ctx.t('col.action'), FILTER_VALUES.action, v => ctx.t('action.' + v)],
    ['truth', ctx.t('ui.data_quality'), FILTER_VALUES.truth, v => ctx.t('truth.' + v)],
    ['tag', 'Tags', FILTER_VALUES.tag, v => ctx.t('tag.' + v)],
    ['stack', 'Stack', D.meta.stack || [], v => v]
  ];
  let h = '<h4>' + esc(ctx.t('nav.filters')) + '</h4>';
  groups.forEach(g => {
    const vals = g[2].filter(v => (ctx.counts.facet[g[0]][v] || 0) > 0 || ctx.state.filters[g[0]].has(v));
    if (!vals.length) return;
    h += '<div class="fgroup"><div class="lbl">' + esc(g[1]) + '</div>' +
      vals.map(v => Atoms.FilterChip(g[0], v, g[3](v), ctx.counts.facet[g[0]][v] || 0,
        ctx.state.filters[g[0]].has(v))).join('') + '</div>';
  });
  h += '<button type="button" id="reset" data-act="reset">' + esc(ctx.t('ui.reset')) + '</button>';
  return h;
};
/* @@END:JS:BIZ:FilterPanel */

/* @@BEGIN:JS:BIZ:HeroHighlights */
Biz.HeroHighlights = (D, ctx) => {
  const hs = (D.highlights || []).slice().sort((a, b) => (a.rank || 0) - (b.rank || 0));
  let h = '<header class="hero"><h1>' + Atoms.Text(D.meta.title, ctx) + '</h1>' +
    '<p class="sub">' + Atoms.Text(D.meta.subtitle, ctx) + '</p></header>' +
    '<section class="blk" id="b-highlights"><h2>' + esc(ctx.t('nav.highlights')) + '</h2>';
  h += hs.length
    ? '<ol class="hl">' + hs.map(x => '<li>' + Atoms.Text(x.text, ctx, ctx.state.query) +
        '<span class="refs">' + (x.item_ids || []).map(id => Biz.ItemRef(id, ctx)).join(' ') +
        '</span></li>').join('') + '</ol>'
    : Atoms.EmptyState(ctx.t('ui.no_results'));
  if (L(D.meta.data_quality_note, ctx.lang).text) {
    h += Atoms.Callout('info', ctx.t('ui.data_quality'),
      '<p>' + Atoms.Text(D.meta.data_quality_note, ctx) + '</p>');
  }
  return h + '</section>';
};
Biz.ItemRef = (id, ctx) => {
  const it = ctx.state.idx.itemsById[id];
  if (!it) return '';
  return '<a href="#' + ctx.lang + '/report/' + esc(id) + '" data-act="focus" data-id="' +
    esc(id) + '" class="cite">' + esc(id) + '</a>';
};
/* @@END:JS:BIZ:HeroHighlights */

/* @@BEGIN:JS:BIZ:StackActionsTable */
Biz.StackActionsTable = (D, ctx) => {
  const rows = (D.stack_actions || []).map(a => [
    '<span class="sa-target">' + esc(a.target) + '</span>',
    Atoms.Badge('action', a.action, ctx),
    Atoms.Text(a.text, ctx, ctx.state.query),
    (a.item_ids || []).map(id => Biz.ItemRef(id, ctx)).join(' ')
  ]);
  return '<section class="blk" id="b-stack"><h2>' + esc(ctx.t('nav.stack_actions')) +
    '<span class="n">' + rows.length + '</span></h2>' +
    (rows.length ? Atoms.Table([ctx.t('col.target'), ctx.t('col.action'), ctx.t('col.what'),
      ctx.t('col.items')].map(esc), rows) : Atoms.EmptyState(ctx.t('ui.no_results'))) +
    '</section>';
};
/* @@END:JS:BIZ:StackActionsTable */

/* @@BEGIN:JS:BIZ:DeadlineTimeline */
Biz.DeadlineTimeline = (D, ctx) => {
  /* Undated entries sort last: a deadline with no date is still a deadline, but
     it cannot be planned around, so it must not sit between two that can. */
  const ds = (D.deadlines || []).slice().sort((a, b) => {
    if (!a.date && !b.date) return 0;
    if (!a.date) return 1;
    if (!b.date) return -1;
    return a.date < b.date ? -1 : 1;
  });
  return '<section class="blk" id="b-deadlines"><h2>' + esc(ctx.t('nav.deadlines')) +
    '<span class="n">' + ds.length + '</span></h2>' +
    (ds.length ? '<ul class="tl">' + ds.map(d =>
      '<li data-s="' + esc(d.status) + '"><div class="when">' +
      Atoms.DateLabel(d.date, d.date_precision, ctx) +
      '<span class="badge" data-v="' + esc(d.status) + '">' + esc(ctx.t('st.' + d.status)) + '</span>' +
      '</div><div>' + Atoms.Text(d.event, ctx, ctx.state.query) + ' ' +
      Atoms.Cites(d.source_ids, ctx) + '</div></li>').join('') + '</ul>'
      : Atoms.EmptyState(ctx.t('ui.no_results'))) + '</section>';
};
/* @@END:JS:BIZ:DeadlineTimeline */

/* @@BEGIN:JS:BIZ:ItemCard */
Biz.ItemCard = (item, ctx) => {
  const open = ctx.state.expanded.has(item.id);
  const soft = (item.truth === 'UNVERIFIED' || item.truth === 'VENDOR_CLAIM') ? '1' : '0';
  const q = ctx.state.query;
  let hd = '<button type="button" class="hd" data-act="item" data-id="' + esc(item.id) +
    '" aria-expanded="' + (open ? 'true' : 'false') + '" aria-controls="bd-' + esc(item.id) + '">' +
    Atoms.Badge('kind', item.kind, ctx) +
    '<span class="nm">' + hi(esc(item.name), q) + '</span>' +
    (item.version ? '<span class="ver">' + esc(item.version) + '</span>' : '') +
    Atoms.DateLabel(item.date, item.date_precision, ctx) +
    (item.action ? Atoms.Badge('action', item.action, ctx) : '') +
    Atoms.Badge('truth', item.truth, ctx) +
    (item.truth === 'ASSUMPTION' && item.confidence
      ? '<span class="badge" data-v="' + esc(item.confidence) + '">' +
        esc(ctx.t('conf.' + item.confidence)) + '</span>' : '') +
    (item.tags || []).map(tg => Atoms.Badge('tag', tg, ctx)).join('') +
    (item.older_context ? '<span class="badge">' + esc(ctx.t('ui.older_context')) + '</span>' : '') +
    '<span class="caret">' + Atoms.Icon('caret') + '</span>' +
    '<p class="hl-txt">' + Atoms.Text(item.headline, ctx, q) + '</p></button>';

  /* The body is always in the DOM, only hidden. That is what lets the print
     stylesheet expand everything and the browser's own find-in-page reach a
     collapsed item. */
  let bd = '<p>' + Atoms.Text(item.body, ctx, q) + '</p>' + Atoms.Metrics(item.metrics, ctx);
  if ((item.commands || []).length) {
    bd += '<div class="grp"><b>' + esc(ctx.t('ui.commands')) + '</b>' +
      Atoms.CodeBlock(item.commands, ctx) + '</div>';
  }
  const links = (item.links || []).filter(l => safeUrl(l.url));
  if (links.length) {
    bd += '<div class="grp"><b>' + esc(ctx.t('ui.links')) + '</b><ul class="lnks">' +
      links.map(l => '<li>' + Atoms.ExtLink(l.url, L(l.label, ctx.lang).text || domainOf(l.url), ctx) +
        '</li>').join('') + '</ul></div>';
  }
  /* A talk is not a link to click later -- it is the evidence. Put the player
     under the claim it supports. */
  const vids = links.filter(l => isYouTube(l.url))
    .concat((item.source_ids || []).map(id => ctx.state.idx.sourcesById[id])
      .filter(s => s && isYouTube(s.url)).map(s => ({url: s.url, label: s.title})));
  const seen = {};
  vids.forEach(v => {
    const y = ytParse(v.url);
    if (!y || seen[y.id]) return;
    seen[y.id] = 1;
    bd += Atoms.YouTube(v.url, ctx, typeof v.label === 'string' ? v.label : L(v.label, ctx.lang).text);
  });
  if ((item.source_ids || []).length) {
    bd += '<div class="grp"><b>' + esc(ctx.t('ui.sources')) + '</b> ' +
      Atoms.Cites(item.source_ids, ctx) + '</div>';
  }
  return '<article class="item" id="' + esc(item.id) + '" data-soft="' + soft +
    '" data-open="' + (open ? '1' : '0') + '">' + hd +
    '<div class="bd" id="bd-' + esc(item.id) + '"' + (open ? '' : ' hidden') + '>' + bd +
    '</div></article>';
};
/* @@END:JS:BIZ:ItemCard */

/* @@BEGIN:JS:BIZ:SectionBlock */
Biz.SectionBlock = (s, ctx) => {
  const items = (s.items || []).filter(ctx.pass);
  let inner;
  if (s.status === 'empty' && !(s.items || []).length) inner = Atoms.EmptyState(ctx.t('ui.empty_section'));
  else if (!items.length) inner = Atoms.EmptyState(ctx.t('ui.no_results'));
  else inner = items.map(it => Biz.ItemCard(it, ctx)).join('');
  return '<section class="sec" id="sec-' + esc(s.id) + '"><header>' +
    '<span class="k">' + esc(s.id) + '</span><h2>' + Atoms.Text(s.title, ctx) + '</h2>' +
    '<span class="n">' + items.length + '</span></header>' +
    '<p class="sum">' + Atoms.Text(s.summary, ctx, ctx.state.query) + '</p>' + inner + '</section>';
};
/* @@END:JS:BIZ:SectionBlock */

/* @@BEGIN:JS:BIZ:ChecklistBlock */
Biz.ChecklistBlock = (D, ctx) => {
  const cs = (D.checklist || []).slice().sort((a, b) => (a.order || 0) - (b.order || 0));
  if (!cs.length) return '';
  return '<section class="blk" id="b-checklist"><h2>' + esc(ctx.t('nav.checklist')) +
    '<span class="n">' + cs.length + '</span></h2><ul class="ck">' + cs.map(c => {
      const done = ctx.state.checked.has(c.id);
      return '<li data-done="' + (done ? '1' : '0') + '">' +
        '<input type="checkbox" data-act="check" data-id="' + esc(c.id) + '"' +
        (done ? ' checked' : '') + ' id="ck-' + esc(c.id) + '">' +
        '<span class="o">' + (c.order || '') + '</span>' +
        '<label class="txt" for="ck-' + esc(c.id) + '">' + Atoms.Text(c.text, ctx, ctx.state.query) +
        ' ' + (c.item_ids || []).map(id => Biz.ItemRef(id, ctx)).join(' ') +
        Atoms.CodeBlock(c.commands, ctx) + '</label></li>';
    }).join('') + '</ul></section>';
};
/* @@END:JS:BIZ:ChecklistBlock */

/* @@BEGIN:JS:BIZ:VerifyList */
Biz.VerifyList = (D, ctx) => {
  const vs = D.verify || [];
  if (!vs.length) return '';
  return '<section class="blk" id="b-verify"><h2>' + esc(ctx.t('nav.verify')) +
    '<span class="n">' + vs.length + '</span></h2><ul class="vf">' +
    vs.map(v => '<li><div>' + Atoms.Text(v.text, ctx, ctx.state.query) + '</div>' +
      Atoms.CodeBlock(v.commands, ctx) + '</li>').join('') + '</ul></section>';
};
/* @@END:JS:BIZ:VerifyList */

/* @@BEGIN:JS:BIZ:ConflictsPanel */
/* Two sources, two numbers, both shown. Picking one silently is how a report
   becomes wrong in a way nobody can trace later. */
Biz.ConflictsPanel = (D, ctx) => {
  const cs = D.conflicts || [];
  if (!cs.length) return '';
  return '<section class="blk cf" id="b-conflicts"><h2>' + esc(ctx.t('nav.conflicts')) +
    '<span class="n">' + cs.length + '</span></h2>' + cs.map(c =>
      Atoms.Callout('conflict', L(c.subject, ctx.lang).text,
        '<dl>' + (c.values || []).map(v => '<dt>' + esc(v.value) + '</dt><dd>' +
          Atoms.CiteChip(v.source_id, ctx) + '</dd>').join('') + '</dl>' +
        '<p>' + Atoms.Text(c.note, ctx) + '</p>')).join('') + '</section>';
};
/* @@END:JS:BIZ:ConflictsPanel */

/* @@BEGIN:JS:BIZ:GlossaryBlock */
Biz.GlossaryBlock = (D, ctx) => {
  const gs = D.glossary || [];
  if (!gs.length) return '';
  return '<section class="blk" id="b-glossary"><h2>' + esc(ctx.t('nav.glossary')) +
    '<span class="n">' + gs.length + '</span></h2><dl class="gl">' +
    gs.map(g => '<dt>' + esc(g.term) + '</dt><dd>' + Atoms.Text(g.definition, ctx) + '</dd>').join('') +
    '</dl></section>';
};
/* @@END:JS:BIZ:GlossaryBlock */

/* @@BEGIN:JS:BIZ:SourcesTab */
Biz.SourcesTab = (D, ctx) => {
  const q = ctx.state.query, nq = norm(q);
  const all = (D.sources || []).filter(s => !nq ||
    norm(s.title).indexOf(nq) >= 0 || norm(s.publisher).indexOf(nq) >= 0 ||
    norm(s.url).indexOf(nq) >= 0);
  const g = ctx.state.srcGroup;
  const keyOf = s => g === 'type' ? ctx.t('srctype.' + s.source_type)
    : g === 'trust' ? ctx.t('trust.' + s.trust)
    : ((s.topics || []).join(', ') || '—');
  const bar = '<div class="grpbar"><span>' + esc(ctx.t('ui.group_by')) + '</span>' +
    [['topic', 'ui.by_topic'], ['type', 'ui.by_type'], ['trust', 'ui.by_trust']].map(p =>
      '<button type="button" data-act="srcgroup" data-g="' + p[0] + '" aria-pressed="' +
      (g === p[0] ? 'true' : 'false') + '">' + esc(ctx.t(p[1])) + '</button>').join('') + '</div>';
  if (!all.length) return bar + Atoms.EmptyState(ctx.t('ui.no_sources'));
  const buckets = {};
  all.forEach(s => { const k = keyOf(s); (buckets[k] = buckets[k] || []).push(s); });
  return bar + Object.keys(buckets).sort().map(k =>
    '<section class="blk"><h2>' + esc(k) + '<span class="n">' + buckets[k].length +
    '</span></h2>' + buckets[k].map(s => Biz.SourceCard(s, ctx)).join('') + '</section>').join('');
};
Biz.SourceCard = (s, ctx) => {
  const n = ctx.state.idx.citeNumber[s.id];
  const cited = ctx.state.idx.citedBy[s.id] || [];
  const yt = isYouTube(s.url);
  return '<article class="src" id="src-' + esc(s.id) + '">' +
    '<div class="top"><span class="no">[' + (n || '?') + ']</span>' +
    Atoms.Badge('srctype', s.source_type, ctx) + Atoms.Badge('trust', s.trust, ctx) +
    (s.published_at ? Atoms.DateLabel(s.published_at, 'day', ctx) : '') + '</div>' +
    '<div class="ttl">' + Atoms.ExtLink(s.url, s.title, ctx) + '</div>' +
    '<div class="meta">' + esc(s.publisher) + ' · ' + esc(s.id) +
    (s.original_lang ? ' · ' + esc(s.original_lang) : '') + '</div>' +
    (yt ? Atoms.YouTube(s.url, ctx, s.title) : '') +
    (cited.length ? '<div class="back">' + esc(ctx.t('ui.cited_by')) + ' ' +
      cited.map(id => Biz.ItemRef(id, ctx)).join(' ') + '</div>' : '') +
    '</article>';
};
/* @@END:JS:BIZ:SourcesTab */

/* @@BEGIN:JS:BIZ:JsonTab */
/* Shows the embedded text, not a re-serialisation: what you copy out is what
   the next run should be able to read back in. */
Biz.JsonTab = (D, ctx) => {
  /* copyraw, not CopyButton: the payload is the whole dataset and it has no
     business being round-tripped through a data- attribute. */
  return '<div class="jsonbar">' +
    '<button type="button" class="copy" data-act="copyraw">' + Atoms.Icon('copy') + ' ' +
      esc(ctx.t('ui.copy_all')) + '</button>' +
    '<button type="button" class="copy" data-act="download">' + esc(ctx.t('ui.download')) + '</button>' +
    '<span class="size">' + esc(fmtBytes(byteLen(RAW))) + '</span></div>' +
    '<div id="jsonview"><ul>' + Biz.JsonNode(D, '', true) + '</ul></div>';
};
Biz.JsonNode = (v, key, open) => {
  const label = key ? '<span class="kk">' + esc(key) + '</span>: ' : '';
  if (v === null) return '<li>' + label + '<span class="vn">null</span></li>';
  if (Array.isArray(v)) {
    if (!v.length) return '<li>' + label + '[]</li>';
    return '<li><details' + (open ? ' open' : '') + '><summary>' + label + '[' + v.length + ']</summary><ul>' +
      v.map((x, i) => Biz.JsonNode(x, String(i), false)).join('') + '</ul></details></li>';
  }
  if (typeof v === 'object') {
    const ks = Object.keys(v);
    if (!ks.length) return '<li>' + label + '{}</li>';
    return '<li><details' + (open ? ' open' : '') + '><summary>' + label + '{' + ks.length + '}</summary><ul>' +
      ks.map(k => Biz.JsonNode(v[k], k, false)).join('') + '</ul></details></li>';
  }
  const cls = typeof v === 'string' ? 'vs' : 'vn';
  const txt = typeof v === 'string' ? '"' + v + '"' : String(v);
  return '<li>' + label + '<span class="' + cls + '">' + esc(txt) + '</span></li>';
};
/* @@END:JS:BIZ:JsonTab */

/* @@SLOT:JS_BIZ */
