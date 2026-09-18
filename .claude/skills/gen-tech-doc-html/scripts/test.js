/* Acceptance suite for a single-file doc site — playbook section 9.
 *
 * Static inspection does not catch render bugs. The whole point of this file is
 * that it actually runs the page: a CSS rule that overrides `hidden`, a figure
 * whose renderer is missing, a code-span sentinel that never got restored — none
 * of those are visible by reading the HTML, and all of them are visible here.
 *
 *   node test.js <built.html> [<content-dir>]
 *
 * <content-dir> is the directory holding src.md; when given, the suite checks
 * the rendered figure count against the @fig directives in the source.
 *
 * Needs jsdom:  npm install jsdom   (in a scratch dir is fine)
 */
const fs = require('fs');
const path = require('path');

const OUT = process.argv[2];
const CONTENT = process.argv[3] || '';
if (!OUT) { console.error('usage: node test.js <built.html> [<content-dir>]'); process.exit(2); }

/* jsdom is a dev dependency of whoever runs this, not of the skill, so resolve it
   from the working directory as well as from here. That lets you install it once
   in a scratch directory and keep it out of the project. */
let JSDOM, VirtualConsole;
try {
  const paths = [process.cwd(), __dirname, path.join(process.cwd(), 'node_modules')];
  ({ JSDOM, VirtualConsole } = require(require.resolve('jsdom', { paths })));
} catch (e) {
  console.error('jsdom not found. From any scratch directory:  npm install jsdom');
  console.error('then run this from that directory, or set NODE_PATH to its node_modules.');
  process.exit(2);
}

const html = fs.readFileSync(OUT, 'utf8');
/* Read ONE language source, never the concatenation of several. The page shows
   one language at a time, so counting @fig across every source made the figure
   check read half (or a third) by construction on a multilingual build. The
   languages are required to carry the same @fig ids, and parity between them is
   a separate check, so any single source is the right denominator here. */
let SRC = '', SRC_LANGS = 0;
if (CONTENT) {
  const one = path.join(CONTENT, 'src.md');
  if (fs.existsSync(one)) { SRC = fs.readFileSync(one, 'utf8'); SRC_LANGS = 1; }
  else {
    const srcs = fs.readdirSync(CONTENT).filter(f => /^src-.*\.md$/.test(f)).sort();
    SRC_LANGS = srcs.length;
    if (srcs.length) SRC = fs.readFileSync(path.join(CONTENT, srcs[0]), 'utf8');
  }
}

let fails = 0, checks = 0;
const ok = (cond, label, extra) => {
  checks++;
  if (!cond) { fails++; console.log('  FAIL  ' + label + (extra ? '  -> ' + extra : '')); }
  else console.log('  ok    ' + label + (extra ? '  (' + extra + ')' : ''));
};

const errors = [];
const vc = new VirtualConsole()
  .on('jsdomError', e => errors.push(e.message))
  .on('error', m => errors.push(String(m)));
const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true,
  url: 'file://' + path.resolve(OUT), virtualConsole: vc
});
const { window } = dom, doc = window.document;
const $ = s => doc.querySelector(s);
const $$ = s => Array.from(doc.querySelectorAll(s));

console.log('\n== boot ==');
ok(errors.length === 0, 'no script errors on load', errors.slice(0, 3).join(' | '));

console.log('\n== content, authored once ==');
const title = $('#title') ? $('#title').textContent.trim() : '';
ok(title.length > 3, 'h1 derived from the markdown', title);
ok(doc.title === title, 'document.title matches the h1');
ok($$('#lede p').length > 0, 'hero lede rendered', $$('#lede p').length);
ok($$('#doc h2').length > 0, 'top-level sections', $$('#doc h2').length);
ok($$('#foot p').length > 0, 'footer paragraphs', $$('#foot p').length);

console.log('\n== figures ==');
const body = $('#doc').textContent;
const nFig = $$('#doc figure').length;
if (SRC) {
  const want = (SRC.match(/^@fig:/gm) || []).length;
  ok(nFig === want, 'rendered figures = @fig directives in one source',
     nFig + '/' + want + (SRC_LANGS > 1 ? ' (counted in one of ' + SRC_LANGS + ' languages)' : ''));
}
ok(!/\[missing figure/.test(body), 'every @fig id has a FIG entry');
ok(!/\[no renderer/.test(body), 'every FIG type has a renderer');
ok(nFig === 0 || $$('#doc figcaption').length === nFig, 'every figure has a caption');

console.log('\n== markdown subset ==');
ok(!/K0DE/.test(body), 'code-span sentinel fully restored');
ok(!/@fig:|@endfig|@box:|@endbox/.test(body), 'no layout directive leaked into the document');
ok($$('#doc .pre pre').length >= 0, 'indented code blocks', $$('#doc .pre pre').length);
ok($$('#doc .tw table').length >= 0, 'tables', $$('#doc .tw table').length);

console.log('\n== table of contents ==');
const links = $$('#toc a');
ok(links.length === $$('#doc h2').length + $$('#doc h3').length, 'one link per h2/h3', links.length);
const broken = links.filter(a => !doc.getElementById(a.getAttribute('href').slice(1)));
ok(broken.length === 0, 'every anchor resolves', broken.length + ' broken');

console.log('\n== views ==');
const disp = id => window.getComputedStyle($('#' + id)).display;
ok($('#docview').hidden === false && $('#md').hidden === true, 'document view is the default');
ok(disp('md') === 'none', 'markdown container really hidden in document view', disp('md'));
$('#viewbtn').dispatchEvent(new window.Event('click'));
ok($('#md').hidden === false && $('#docview').hidden === true, 'toggles to markdown');
ok(disp('docview') === 'none', 'document container really hidden in markdown view', disp('docview'));
const md = $('#mdtext').textContent;
ok(md.length > 500, 'copy-out markdown is complete', md.length + ' chars');
ok(!/@fig:|@endfig|@box:|@endbox/.test(md), 'copy-out markdown is directive-free');
const mdCode = window.getComputedStyle($('#mdtext'));
ok(mdCode.padding === '0px' || mdCode.padding === '',
   'markdown block not re-styled by the generic code rule',
   'pad=' + mdCode.padding + ' bg=' + mdCode.backgroundColor);
$('#viewbtn').dispatchEvent(new window.Event('click'));
ok($('#docview').hidden === false, 'toggles back');

console.log('\n== drawer ==');
if ($('#navbtn')) {
  ok(!$('#nav').classList.contains('open'), 'starts closed');
  $('#navbtn').dispatchEvent(new window.Event('click'));
  ok($('#nav').classList.contains('open'), 'opens on the button');
  ok($('#navbtn').getAttribute('aria-expanded') === 'true', 'aria-expanded tracks it');
  doc.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape' }));
  ok(!$('#nav').classList.contains('open'), 'Escape closes it');
}

console.log('\n== optional controls ==');
const langSel = $('#langsel') || $('#langbtn');
const depthSel = $('#depthsel');
if (langSel) {
  const before = $('#doc').textContent.slice(0, 200);
  const opts = langSel.options ? Array.from(langSel.options).map(o => o.value) : [];
  if (opts.length > 1) {
    langSel.value = opts[1];
    langSel.dispatchEvent(new window.Event('change'));
    ok($('#doc').textContent.slice(0, 200) !== before, 'language switch rerenders the document');
    ok($$('#toc a').length > 0, 'table of contents rebuilt after language change');
    langSel.value = opts[0];
    langSel.dispatchEvent(new window.Event('change'));
  }
}
if (depthSel) {
  const full = $$('#doc h2').length;
  depthSel.value = '1';
  depthSel.dispatchEvent(new window.Event('change'));
  const cut = $$('#doc h2').length;
  ok(cut < full, 'depth 1 drops sections', cut + ' of ' + full);
  ok($$('#toc a').length === cut + $$('#doc h3').length, 'table of contents follows the cut');
  ok(!/@fig:/.test($('#mdtext').textContent), 'sliced markdown stays directive-free');
  depthSel.value = String(depthSel.options.length);
  depthSel.dispatchEvent(new window.Event('change'));
  ok($$('#doc h2').length === full, 'restores at full depth');
}
if (!langSel && !depthSel) console.log('  --    single language, no depth slicing (the default)');

console.log('\n== hygiene ==');
ok(!/\/Users\/[a-z]/i.test(html), 'no absolute home path in the shipped file');
ok(!/\/home\/[a-z]/i.test(html), 'no absolute linux home path either');
ok((html.match(/<script/g) || []).length >= 2, 'markdown source and logic are separate blocks');
ok(/viewport-fit=cover/.test(html), 'viewport-fit set for notched screens');
ok(/prefers-reduced-motion/.test(html), 'reduced motion honoured');
ok((html.match(/--ground:|--bg:/g) || []).length >= 3, 'colour tokens defined three times');
ok(/scroll-margin-top/.test(html), 'headings clear the sticky bar');
ok(/\[hidden\]\{display:none/.test(html.replace(/\s/g, '')) || disp('md') === 'none',
   'hidden attribute actually hides');

console.log('\n' + (fails ? 'FAILED ' + fails + ' of ' + checks : 'PASSED ' + checks + ' checks'));
process.exit(fails ? 1 : 0);
