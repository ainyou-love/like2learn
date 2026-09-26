/* Acceptance suite for a built report page.
 *
 * Reading the HTML tells you what was written; only running it tells you what
 * the reader gets. A CiteChip pointing at a source that was dropped in the
 * merge, a filter that silently matches nothing, a YouTube facade that loaded
 * its iframe on page open -- none of those are visible by inspection, and all
 * of them fail here.
 *
 *   node test_report.js <built.html> [<report.json>]
 *
 * Passing the source JSON adds the byte-identity check on the JSON tab.
 * Needs jsdom:  npm install jsdom   (a scratch directory is fine)
 */
const fs = require('fs');
const path = require('path');

const OUT = process.argv[2];
const SRC = process.argv[3] || '';
if (!OUT) { console.error('usage: node test_report.js <built.html> [<report.json>]'); process.exit(2); }

let JSDOM, VirtualConsole;
try {
  const paths = [process.cwd(), __dirname, path.join(process.cwd(), 'node_modules')];
  ({ JSDOM, VirtualConsole } = require(require.resolve('jsdom', { paths })));
} catch (e) {
  console.error('jsdom not found. From any scratch directory:  npm install jsdom');
  process.exit(2);
}

const html = fs.readFileSync(OUT, 'utf8');
let fails = 0, checks = 0;
const ok = (cond, label, extra) => {
  checks++;
  if (!cond) { fails++; console.log('  FAIL  ' + label + (extra ? '  -> ' + extra : '')); }
  else console.log('  ok    ' + label + (extra ? '  (' + extra + ')' : ''));
};

const errors = [], warns = [];
const vc = new VirtualConsole()
  .on('jsdomError', e => errors.push(e.message))
  .on('error', m => errors.push(String(m)))
  .on('warn', m => warns.push(String(m)));
const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'file://' + path.resolve(OUT), virtualConsole: vc
});
const { window } = dom, doc = window.document;
const $ = s => doc.querySelector(s);
const $$ = s => Array.from(doc.querySelectorAll(s));
const click = el => el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
/* jsdom parses asynchronously, and the page deliberately waits for the data
 * block at the end of the file, so the suite has to wait too. Running the
 * assertions synchronously after construction tests an empty document. */
function suite() {
const R = window.REPORT || {};

console.log('\n== boot ==');
ok(errors.length === 0, 'no script errors on load', errors.slice(0, 2).join(' | '));
ok(!!R.DATA, 'the page exposes window.REPORT for console debugging');
ok($('#view').children.length > 0, 'the report tab rendered something');

console.log('\n== data integrity ==');
if (R.DATA) {
  const D = R.DATA;
  const items = (D.sections || []).reduce((n, s) => n + (s.items || []).length, 0);
  ok(items > 0, 'items present', items);
  ok((D.sources || []).length > 0, 'sources present', (D.sources || []).length);
  const ids = {}; let dup = 0;
  (D.sections || []).forEach(s => (s.items || []).forEach(i => { if (ids[i.id]) dup++; ids[i.id] = 1; }));
  ok(dup === 0, 'item ids unique', dup + ' duplicates');
  const known = {}; (D.sources || []).forEach(s => known[s.id] = 1);
  let bad = 0;
  (D.sections || []).forEach(s => (s.items || []).forEach(i =>
    (i.source_ids || []).forEach(x => { if (!known[x]) bad++; })));
  ok(bad === 0, 'every source_ids entry resolves', bad + ' dangling');
  const langs = D.meta.languages || ['vi'];
  ok(langs.indexOf(D.meta.default_language) >= 0, 'default_language is one of languages',
     D.meta.default_language);
  /* If every source is cited exactly once, any assertion about citation counts
     or about ordering by them passes without proving anything -- "1 >= 1" is
     green whether the feature works or not. A dataset used for testing has to
     have an uneven spread, so this check guards the fixture itself. */
  const spread = {};
  (D.sections || []).forEach(s => (s.items || []).forEach(i =>
    (i.source_ids || []).forEach(x => { spread[x] = (spread[x] || 0) + 1; })));
  const counts = Object.keys(spread).map(k => spread[k]);
  ok(counts.length > 0 && Math.max.apply(null, counts) > Math.min.apply(null, counts),
     'citation counts are uneven, so count- and order-dependent checks are not vacuous',
     counts.sort((a, b) => b - a).join('/') || 'no citations');
}
if (SRC && R.RAW) {
  /* The JSON tab promises the original bytes, not a re-serialisation. If the
     "</" escaping is not undone exactly, this is where it shows. */
  const src = fs.readFileSync(SRC, 'utf8').trim();
  ok(R.RAW === src, 'embedded JSON round-trips byte-identical to the source file',
     R.RAW.length + ' vs ' + src.length + ' chars');
}
ok(!/<\/script/i.test((html.match(/id="report-data">([\s\S]*?)<\/script>/) || ['', ''])[1]),
   'no unescaped closing script tag inside the dataset');

console.log('\n== language ==');
const before = $('#view').textContent.slice(0, 400);
const langBtn = $('[data-act="lang"]');
if (langBtn && R.DATA && (R.DATA.meta.languages || []).length > 1) {
  const from = doc.documentElement.lang;
  click(langBtn);
  ok(doc.documentElement.lang !== from, 'html lang changes', from + ' -> ' + doc.documentElement.lang);
  ok($('#view').textContent.slice(0, 400) !== before, 'visible content changes with the language');
  ok($$('#tabs [role=tab]')[0].textContent.trim().length > 0, 'tab labels are translated too');
  click($('[data-act="lang"]'));
  ok(doc.documentElement.lang === from, 'toggles back', doc.documentElement.lang);
} else {
  ok(true, 'single language, nothing to toggle');
}
ok($$('.lt-miss').length === 0, 'no item is missing a translation',
   $$('.lt-miss').length + ' flagged');

console.log('\n== tabs ==');
ok($$('#tabs [role=tab]').length === 3, 'three tabs', $$('#tabs [role=tab]').length);
ok($('#view').getAttribute('role') === 'tabpanel', 'the view is a tabpanel');
click($('[data-tab="sources"]'));
ok($$('.src').length > 0, 'sources tab lists sources', $$('.src').length);
ok($('[data-tab="sources"]').getAttribute('aria-selected') === 'true', 'aria-selected tracks the tab');
click($('[data-tab="json"]'));
ok(!!$('#jsonview'), 'json tab renders a viewer');
ok($$('#jsonview details').length > 0, 'json viewer nodes are collapsible',
   $$('#jsonview details').length);
ok(/\d+(\.\d+)? ?(B|KB|MB)/.test($('.jsonbar .size').textContent), 'json tab shows the byte size',
   $('.jsonbar .size').textContent);
click($('[data-tab="report"]'));
ok($$('.item').length > 0, 'back on the report tab', $$('.item').length + ' items');

console.log('\n== items ==');
const first = $('.item');
ok(first.getAttribute('data-open') === '0', 'items start collapsed');
ok(!!first.querySelector('.bd'), 'the body is in the DOM even when collapsed');
ok(first.querySelector('.bd').hidden === true, 'and is really hidden');
click(first.querySelector('.hd'));
ok(first.getAttribute('data-open') === '1', 'clicking the header expands it');
ok(first.querySelector('.bd').hidden === false, 'the body is shown');
ok(first.querySelector('.hd').getAttribute('aria-expanded') === 'true', 'aria-expanded tracks it');
click(first.querySelector('.hd'));
ok(first.getAttribute('data-open') === '0', 'and collapses again');
const soft = $$('.item[data-soft="1"]');
if (R.DATA) {
  const want = (R.DATA.sections || []).reduce((n, s) => n + (s.items || [])
    .filter(i => i.truth === 'UNVERIFIED' || i.truth === 'VENDOR_CLAIM').length, 0);
  ok(soft.length === want, 'unverified / vendor-claim items are marked', soft.length + '/' + want);
}
ok($$('.item .badge').length > 0, 'badges carry text, not just colour');

console.log('\n== citations ==');
const chips = $$('.cite[data-sid]');
ok(chips.length > 0, 'citation chips rendered', chips.length);
ok($$('.cite[data-unknown="1"]').length === 0, 'no citation points at a missing source',
   $$('.cite[data-unknown="1"]').length + ' unknown');
ok($$('.cite-pop').length === chips.length, 'every chip carries a hover preview');
if (chips.length) {
  const sid = chips[0].dataset.sid;
  click(chips[0]);
  ok($('[data-tab="sources"]').getAttribute('aria-selected') === 'true',
     'clicking a chip lands on the sources tab');
  ok(!!doc.getElementById('src-' + sid), 'and the target source exists there', sid);
  ok($$('.src .back').length > 0, 'sources link back to the items that cite them');
  click($('[data-tab="report"]'));
}

console.log('\n== filters and search ==');
const total0 = +$('#tabs [data-tab="report"] .n').textContent;
const chip = $$('.chip').find(c => +c.dataset.n > 0 && +c.dataset.n < total0);
if (chip) {
  const label = chip.dataset.g + '=' + chip.dataset.v;
  click(chip);
  const total1 = +$('#tabs [data-tab="report"] .n').textContent;
  ok(total1 < total0, 'a filter narrows the result', label + ': ' + total0 + ' -> ' + total1);
  ok($$('.chip[aria-pressed="true"]').length === 1, 'the chip reads as pressed');
  ok(+$$('#sidebar a[data-n]').reduce((n, a) => n + +a.dataset.n, 0) > 0 || total1 === 0,
     'sidebar counts recomputed');
  click($('#reset'));
  ok(+$('#tabs [data-tab="report"] .n').textContent === total0, 'reset restores everything');
} else {
  ok(true, 'dataset too small for a discriminating filter chip');
}
const q = $('#q');
q.value = 'zzzqqqxx';
q.dispatchEvent(new window.Event('input', { bubbles: true }));
// the input handler is debounced, so drive the state directly for the assertion
R.state.query = 'zzzqqqxx'; R.render();
ok($$('.empty').length > 0, 'a search with no hits shows an empty state');
ok(+$('#tabs [data-tab="report"] .n').textContent === 0, 'and the tab count goes to zero');
R.state.query = ''; R.render();
ok(+$('#tabs [data-tab="report"] .n').textContent === total0, 'clearing the search restores');

console.log('\n== youtube ==');
const yts = $$('.yt');
const ytSources = R.DATA ? (R.DATA.sources || []).filter(s => /youtu\.?be/.test(s.url || '')) : [];
if (ytSources.length) {
  click($('[data-tab="sources"]'));
  const f = $$('.yt');
  ok(f.length > 0, 'youtube sources render a player facade', f.length);
  ok($$('.yt iframe').length === 0, 'no iframe exists before the reader asks for one');
  click(f[0].querySelector('.play'));
  const fr = $('.yt iframe');
  ok(!!fr, 'clicking play creates the iframe');
  ok(/youtube-nocookie\.com\/embed\//.test(fr.src), 'and uses the nocookie embed host', fr.src);
  ok(fr.getAttribute('allowfullscreen') !== null || fr.allowFullscreen, 'fullscreen allowed');
  click($('[data-tab="report"]'));
} else {
  ok(yts.length === 0, 'no youtube sources in this dataset, no facades rendered');
}

console.log('\n== checklist ==');
if (R.DATA && (R.DATA.checklist || []).length) {
  const box = $('.ck input');
  ok(!!box, 'checklist renders checkboxes');
  box.checked = true;
  box.dispatchEvent(new window.Event('change', { bubbles: true }));
  ok(box.closest('li').dataset.done === '1', 'ticking marks the row done');
} else { ok(true, 'no checklist in this dataset'); }

console.log('\n== drawer and keyboard ==');
ok(!$('#sidebar').classList.contains('open'), 'drawer starts closed');
click($('#navbtn'));
ok($('#sidebar').classList.contains('open'), 'opens on the menu button');
ok($('#navbtn').getAttribute('aria-expanded') === 'true', 'aria-expanded tracks it');
doc.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
ok(!$('#sidebar').classList.contains('open'), 'Escape closes it');
ok($('.skip') && $('.skip').getAttribute('href') === '#view', 'skip link targets the content');

console.log('\n== mobile-first css ==');
/* jsdom has no layout engine, so these read the stylesheet rather than the
   rendered box -- enough to catch a desktop-first regression. */
const css = (html.match(/<style>([\s\S]*?)<\/style>/) || ['', ''])[1];
ok(/viewport-fit=cover/.test(html), 'viewport-fit set for notched screens');
ok(/@media \(min-width:900px\)/.test(css), 'the sidebar column is a min-width enhancement');
ok(!/@media \(max-width:9\d\dpx\)/.test(css), 'no max-width rescue query for the main layout');
ok(/#topbar \.search input\{[^}]*font:[^}]*16px/.test(css.replace(/\s*\n\s*/g, '')),
   'search input is 16px so iOS does not zoom on focus');
ok(/env\(safe-area-inset/.test(css), 'safe-area insets honoured');
ok(/min-height:44px/.test(css), 'primary tap targets are at least 44px');
ok(/overflow-x:hidden/.test(css), 'the page itself never scrolls sideways');
const flat = css.replace(/\s*\n\s*/g, '');
ok(/\.tw td::before\{content:attr\(data-l\)/.test(flat),
   'tables stack into labelled rows on a phone instead of scrolling sideways');
ok(/@media \(min-width:700px\)\{\.tw\{overflow-x:auto\}/.test(flat),
   'and become a real grid, in its own scroll container, once there is width');
ok($$('.tw td[data-l]').length > 0, 'table cells carry their column name for the stacked view',
   $$('.tw td[data-l]').length + ' cells');
ok(/prefers-reduced-motion/.test(css), 'reduced motion honoured');
ok(/@media print/.test(css), 'print stylesheet present');
ok(/\[hidden\]\{display:none ?!important\}/.test(css.replace(/\s*\n\s*/g, '')),
   'the hidden attribute really hides');
ok((css.match(/--accent:/g) || []).length >= 3, 'colour tokens declared for both themes',
   (css.match(/--accent:/g) || []).length + ' declarations');

console.log('\n== edit markers ==');
const begins = (html.match(/@@BEGIN:([A-Za-z0-9_:*.-]+)/g) || []).map(s => s.slice(8));
const ends = (html.match(/@@END:([A-Za-z0-9_:*.-]+)/g) || []).map(s => s.slice(6));
ok(begins.length > 20, 'regions present', begins.length);
ok(begins.length === ends.length, 'every BEGIN has an END', begins.length + '/' + ends.length);
const notUnique = begins.filter(n => (html.split('@@BEGIN:' + n).length - 1) !== 1);
ok(notUnique.length === 0, 'every marker string is unique', notUnique.join(', '));
ok(/@@SLOT:CSS_ATOMS/.test(html) && /@@SLOT:JS_ATOMS/.test(html) &&
   /@@SLOT:JS_BIZ/.test(html) && /@@SLOT:I18N_KEYS/.test(html), 'insertion slots present');
const dataAt = html.indexOf('@@BEGIN:DATA'), jsAt = html.indexOf('@@BEGIN:JS:APP');
ok(dataAt > jsAt, 'the dataset is last, so reading the code costs no dataset tokens');

console.log('\n== hygiene ==');
ok(!/\/Users\/[a-z]/i.test(html), 'no absolute home path in the shipped file');
ok(!/\/home\/[a-z]/i.test(html), 'no absolute linux home path either');
const ext = (html.match(/https?:\/\/[^"'\s)]+/g) || [])
  .filter(u => !/fonts\.(googleapis|gstatic)\.com|youtube-nocookie\.com/.test(u));
const inTag = (html.match(/(src|href)="https?:\/\/[^"]+"/g) || [])
  .filter(u => !/fonts\.(googleapis|gstatic)\.com/.test(u));
ok(inTag.length === 0, 'no external resource loads except the font', inTag.slice(0, 2).join(' '));
ok(html.length < 16 * 1024 * 1024, 'under the 16 MB ceiling',
   (html.length / 1048576).toFixed(2) + ' MB');

}

function run() {
  /* A throw part-way through used to abort the suite silently: the summary
     line never printed, every later check was skipped, and the scrollback
     still looked like a clean run. Turn it into the failure it is. */
  try {
    suite();
  } catch (e) {
    checks++; fails++;
    console.log('  FAIL  suite aborted by an exception: ' + ((e && e.message) || e));
    if (e && e.stack) console.log(e.stack.split('\n').slice(1, 4).join('\n'));
  }
  console.log('\n' + (fails ? 'FAILED ' + fails + ' of ' + checks : 'PASSED ' + checks + ' checks'));
  process.exit(fails ? 1 : 0);
}

if (doc.readyState === 'complete') run();
else window.addEventListener('load', run);
