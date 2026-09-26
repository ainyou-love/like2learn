/* LAYER 4a -- the dataset, the indexes built from it, and the render context.
   Split out of one oversized JS:APP region so that changing how items are
   filtered never means reading the router and the event table too. */

/* @@BEGIN:JS:APP:DATA */
/* The DATA block deliberately sits at the very end of the file, so that an
   agent editing the components never has to load the dataset into context.
   The cost of that choice is exactly this: at the moment this script runs,
   the data element does not exist yet. Everything that depends on it is
   therefore assigned in start(), which waits for the parser to reach it. */
let RAW, DATA, LANGS, KEY, idx, state;

const FILTER_VALUES = {
  action: ['patch_now', 'try_now', 'watch', 'ignore'],
  truth: ['FACT', 'ASSUMPTION', 'UNVERIFIED', 'VENDOR_CLAIM'],
  tag: ['RISK', 'RISK/SECURITY', 'RISK/MIGRATION', 'TRADE_OFF', 'DECISION', 'CONCERN']
};
const TABS = ['report', 'sources', 'json'];

function readData() {
  /* The embedded text is the source of truth, not a re-serialisation of it.
     build_report.py escaped "</" so the block could not be closed from inside
     a string; undoing exactly that one substitution gives back the bytes the
     research step wrote, which is what the JSON tab hands you. */
  const el = document.getElementById('report-data');
  if (!el) throw new Error('report-data block is missing from the page');
  RAW = el.textContent.replace(/<\\\//g, '</').trim();
  DATA = JSON.parse(RAW);
  LANGS = (DATA.meta && DATA.meta.languages) || ['vi'];
  KEY = 'tdr:' + ((DATA.meta && DATA.meta.report_id) || 'report');

  idx = {itemsById: {}, sourcesById: {}, sectionOfItem: {}, citeNumber: {}, citedBy: {}, all: []};
  (DATA.sections || []).forEach(s => (s.items || []).forEach(it => {
    idx.itemsById[it.id] = it; idx.sectionOfItem[it.id] = s.id; idx.all.push(it);
  }));
  (DATA.sources || []).forEach((s, i) => { idx.sourcesById[s.id] = s; idx.citeNumber[s.id] = i + 1; });
  idx.all.forEach(it => (it.source_ids || []).forEach(sid => {
    (idx.citedBy[sid] = idx.citedBy[sid] || []).push(it.id);
  }));

  state = {
    lang: LANGS.indexOf(DATA.meta.default_language) >= 0 ? DATA.meta.default_language : LANGS[0],
    theme: store.get(KEY + ':theme', ''),
    tab: 'report',
    query: '',
    filters: {action: new Set(), truth: new Set(), tag: new Set(), stack: new Set()},
    expanded: new Set(),
    checked: new Set(store.get(KEY + ':checked', [])),
    srcGroup: 'topic',
    warned: [],
    idx: idx
  };
}

function makeCtx() {
  const ctx = {lang: state.lang, t: k => t(k, state.lang), L: L, esc: esc, state: state};
  ctx.pass = it => itemPasses(it, ctx);
  ctx.counts = counts(ctx);
  return ctx;
}
/* @@END:JS:APP:DATA */
