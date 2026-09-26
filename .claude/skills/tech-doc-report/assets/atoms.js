/* Atoms are pure: (props, ctx) -> HTML string. They never read DATA and never
   touch the DOM, which is what makes them safe to reuse across reports and
   trivial to reason about when one of them renders wrong.
   ctx = { lang, t, L, esc, state } */
const Atoms = {};

/* @@BEGIN:JS:ATOM:Icon */
const ICONS = {
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
  copy:   '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/>',
  ext:    '<path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>',
  sun:    '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19"/>',
  moon:   '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/>',
  menu:   '<path d="M4 7h16M4 12h16M4 17h16"/>',
  caret:  '<path d="M9 5l7 7-7 7"/>',
  print:  '<path d="M7 9V3h10v6"/><rect x="4" y="9" width="16" height="7" rx="2"/><path d="M7 14h10v7H7z"/>'
};
Atoms.Icon = (name) => '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">' +
  (ICONS[name] || '') + '</svg>';
/* @@END:JS:ATOM:Icon */

/* @@BEGIN:JS:ATOM:Text */
Atoms.Text = (lt, ctx, q) => {
  const r = L(lt, ctx.lang);
  const body = hi(esc(r.text), q);
  return r.miss
    ? '<span class="lt lt-miss" data-fallback="' + esc(r.miss) + '" title="' +
      esc(ctx.t('ui.missing_lang')) + '">' + body + '</span>'
    : body;
};
/* @@END:JS:ATOM:Text */

/* @@BEGIN:JS:ATOM:Badge */
/* variant picks the I18N namespace, so the badge label and the filter label can
   never drift apart -- they read the same key. */
Atoms.Badge = (variant, value, ctx) => {
  if (!value) return '';
  const cls = variant === 'kind' ? 'badge badge--kind' : 'badge';
  return '<span class="' + cls + '" data-v="' + esc(value) + '">' +
    esc(ctx.t(variant + '.' + value)) + '</span>';
};
/* @@END:JS:ATOM:Badge */

/* @@BEGIN:JS:ATOM:DateLabel */
Atoms.DateLabel = (date, precision, ctx) => {
  const p = precision || (date ? 'day' : 'tbd');
  if (!date) return '<span class="date" data-p="tbd">' + esc(ctx.t('ui.tbd')) + '</span>';
  let txt = date;
  if (p === 'month') txt = date.slice(0, 7);
  else if (p === 'quarter') txt = date.slice(0, 4) + '-Q' + (Math.floor((+date.slice(5, 7) - 1) / 3) + 1);
  return '<span class="date" data-p="' + esc(p) + '">' + esc(txt) + '</span>';
};
/* @@END:JS:ATOM:DateLabel */

/* @@BEGIN:JS:ATOM:CiteChip */
/* The chip stays out of the way of reading: a number, a hover card, and a click
   that lands on the source. An id with no source renders [?] rather than
   vanishing, because a silently dropped citation is indistinguishable from a
   claim that never had one. */
Atoms.CiteChip = (sid, ctx) => {
  const s = ctx.state.idx.sourcesById[sid];
  if (!s) {
    if (ctx.state.warned.indexOf(sid) < 0) {
      ctx.state.warned.push(sid);
      console.warn('[report] citation refers to a source that does not exist:', sid);
    }
    return '<span class="cite" data-unknown="1" title="' + esc(ctx.t('ui.unknown_source')) +
      ': ' + esc(sid) + '">[?]</span>';
  }
  const n = ctx.state.idx.citeNumber[sid];
  return '<button type="button" class="cite" data-act="cite" data-sid="' + esc(sid) +
    '" aria-label="' + esc(s.title) + '">[' + n + ']' +
    '<span class="cite-pop"><b>' + esc(s.title) + '</b><span>' + esc(s.publisher) +
    (s.published_at ? ' · ' + esc(s.published_at) : '') + ' · ' +
    esc(ctx.t('trust.' + s.trust)) + '</span></span></button>';
};
Atoms.Cites = (ids, ctx) => (ids || []).map(id => Atoms.CiteChip(id, ctx)).join('');
/* @@END:JS:ATOM:CiteChip */

/* @@BEGIN:JS:ATOM:ExtLink */
Atoms.ExtLink = (url, label, ctx) => {
  const u = safeUrl(url);
  if (!u) return esc(label);
  return '<a class="xl" href="' + esc(u) + '" target="_blank" rel="noopener noreferrer">' +
    esc(label) + Atoms.Icon('ext') + '<span class="dom">' + esc(domainOf(u)) + '</span></a>';
};
/* @@END:JS:ATOM:ExtLink */

/* @@BEGIN:JS:ATOM:CopyButton */
Atoms.CopyButton = (payload, ctx, label) =>
  '<button type="button" class="copy" data-act="copy" data-copy="' + esc(payload) + '">' +
  Atoms.Icon('copy') + ' ' + esc(label || ctx.t('ui.copy')) + '</button>';
/* @@END:JS:ATOM:CopyButton */

/* @@BEGIN:JS:ATOM:CodeBlock */
Atoms.CodeBlock = (commands, ctx) => {
  const list = (commands || []).filter(Boolean);
  if (!list.length) return '';
  const text = list.join('\n');
  return '<div class="code">' + Atoms.CopyButton(text, ctx) +
    '<pre><code>' + esc(text) + '</code></pre></div>';
};
/* @@END:JS:ATOM:CodeBlock */

/* @@BEGIN:JS:ATOM:Metric */
Atoms.Metric = (m, ctx) =>
  '<div class="metric"><div class="v">' + esc(m.value) +
  (m.unit ? '<span class="u">' + esc(m.unit) + '</span>' : '') + '</div>' +
  '<div class="l">' + Atoms.Text(m.label, ctx) + ' ' +
  (m.source_id ? Atoms.CiteChip(m.source_id, ctx) : '') + '</div></div>';
Atoms.Metrics = (list, ctx) => !list || !list.length ? '' :
  '<div class="metrics">' + list.map(m => Atoms.Metric(m, ctx)).join('') + '</div>';
/* @@END:JS:ATOM:Metric */

/* @@BEGIN:JS:ATOM:Card */
Atoms.Card = (head, body, open) =>
  '<div class="card">' + (body
    ? '<button type="button" class="hd" data-act="card" aria-expanded="' + (open ? 'true' : 'false') + '">' +
      head + '</button><div class="bd"' + (open ? '' : ' hidden') + '>' + body + '</div>'
    : '<div class="hd">' + head + '</div>') + '</div>';
/* @@END:JS:ATOM:Card */

/* @@BEGIN:JS:ATOM:Table */
/* Four columns is the ceiling, and on a phone even four is too many: the CSS
   turns each row into a stacked block and prints the column name from data-l,
   so the important column is never the one behind a sideways scroll. That is
   why the header text is repeated onto every cell. */
Atoms.Table = (heads, rows) => {
  if (!rows.length) return '';
  const hs = heads.slice(0, 4);
  return '<div class="tw" tabindex="0"><table><thead><tr>' +
    hs.map(h => '<th scope="col">' + h + '</th>').join('') +
    '</tr></thead><tbody>' +
    rows.map(r => '<tr>' + r.slice(0, 4).map((c, i) =>
      '<td data-l="' + (hs[i] || '') + '">' + c + '</td>').join('') + '</tr>').join('') +
    '</tbody></table></div>';
};
/* @@END:JS:ATOM:Table */

/* @@BEGIN:JS:ATOM:Tabs */
Atoms.Tabs = (tabs, current) =>
  tabs.map(tb => '<button type="button" role="tab" id="tab-' + tb.id + '"' +
    ' aria-selected="' + (tb.id === current ? 'true' : 'false') + '"' +
    ' aria-controls="view" tabindex="' + (tb.id === current ? '0' : '-1') + '"' +
    ' data-act="tab" data-tab="' + tb.id + '">' + esc(tb.label) +
    (tb.n == null ? '' : '<span class="n">' + tb.n + '</span>') + '</button>').join('');
/* @@END:JS:ATOM:Tabs */

/* @@BEGIN:JS:ATOM:FilterChip */
Atoms.FilterChip = (group, value, label, n, on) =>
  '<button type="button" class="chip" data-act="filter" data-g="' + esc(group) +
  '" data-v="' + esc(value) + '" data-n="' + n + '" aria-pressed="' + (on ? 'true' : 'false') + '">' +
  '<span class="box" aria-hidden="true"></span><span>' + esc(label) +
  '</span><span class="n">' + n + '</span></button>';
/* @@END:JS:ATOM:FilterChip */

/* @@BEGIN:JS:ATOM:Callout */
Atoms.Callout = (variant, title, body) =>
  '<div class="callout" data-v="' + esc(variant) + '">' +
  (title ? '<b>' + esc(title) + '</b>' : '') + body + '</div>';
/* @@END:JS:ATOM:Callout */

/* @@BEGIN:JS:ATOM:EmptyState */
Atoms.EmptyState = (msg) => '<p class="empty">' + esc(msg) + '</p>';
/* @@END:JS:ATOM:EmptyState */

/* @@BEGIN:JS:ATOM:YouTube */
/* Rendered as a facade. The iframe is only created on click, so opening a
   report with a dozen talks in it costs nothing and phones home to nobody. */
Atoms.YouTube = (url, ctx, caption) => {
  const y = ytParse(url);
  if (!y) return '';
  return '<div class="yt" data-yt="' + esc(y.id) + '" data-start="' + y.start + '">' +
    '<button type="button" class="play" data-act="yt" aria-label="' + esc(ctx.t('ui.play_video')) + '">' +
    '<span class="btn" aria-hidden="true"></span>' +
    '<span>' + esc(caption || ctx.t('ui.play_video')) + '</span></button></div>';
};
/* @@END:JS:ATOM:YouTube */

/* @@SLOT:JS_ATOMS */
