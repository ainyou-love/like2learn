/* @@BEGIN:JS:UTIL */
/* Everything that touches DATA goes through esc(). The report is assembled from
   web sources, so treat every string in it as hostile text, not as markup. */
const ESCMAP = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ESCMAP[c]);

/* L() resolves an LText. A missing translation is shown in the other language
   and marked, never left blank -- a blank line reads as "nothing happened",
   which is a different and much worse claim than "not translated yet". */
function L(lt, lang) {
  if (lt == null) return {text: '', miss: ''};
  if (typeof lt === 'string') return {text: lt, miss: ''};
  const v = lt[lang];
  if (v) return {text: v, miss: ''};
  for (const k of Object.keys(lt)) if (lt[k]) return {text: lt[k], miss: k};
  return {text: '', miss: ''};
}
const t = (key, lang) => (I18N[key] && (I18N[key][lang] || I18N[key].en)) || key;

/* Only http(s) survives. javascript: and data: URLs in a link built from
   scraped source data are the one injection route esc() does not close. */
function safeUrl(u) {
  const s = String(u == null ? '' : u).trim();
  return /^https?:\/\//i.test(s) ? s : '';
}
function domainOf(u) {
  const s = safeUrl(u);
  if (!s) return '';
  const m = s.match(/^https?:\/\/(?:www\.)?([^/?#]+)/i);
  return m ? m[1] : '';
}

/* YouTube ids arrive in four shapes and often carry a start time. */
function ytParse(u) {
  const s = safeUrl(u);
  if (!s) return null;
  const m = s.match(/(?:youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/|live\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  if (!m) return null;
  /* 1h2m3s must be tested before the bare-seconds form, or "t=1h30m" reads as 1. */
  let start = 0;
  const hms = s.match(/[?&](?:t|start)=(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)/);
  const sec = s.match(/[?&](?:t|start)=(\d+)\b/);
  if (hms) start = (+(hms[1] || 0)) * 3600 + (+(hms[2] || 0)) * 60 + (+(hms[3] || 0));
  else if (sec) start = +sec[1] || 0;
  return {id: m[1], start: start};
}
const isYouTube = u => !!ytParse(u);

/* Storage can throw before it can return: Safari private mode raises on write,
   and an embedded viewer may block it entirely. The page must not care. */
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
};

/* TextEncoder is not guaranteed on every runtime that renders this page
   (headless test harnesses in particular), and the byte count is cosmetic. */
const byteLen = s => encodeURIComponent(String(s)).replace(/%[0-9A-F]{2}/gi, 'x').length;
function fmtBytes(n) {
  if (n < 1024) return n + ' B';
  if (n < 1048576) return (n / 1024).toFixed(1) + ' KB';
  return (n / 1048576).toFixed(2) + ' MB';
}
const norm = s => String(s == null ? '' : s).toLowerCase()
  .normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[đĐ]/g, 'd');

/* Highlight search hits after escaping, so the <mark> we insert is the only
   markup in the string. */
function hi(escaped, q) {
  if (!q) return escaped;
  const nq = norm(q);
  if (!nq) return escaped;
  const plain = escaped.replace(/&[a-z]+;|&#\d+;/g, ' ');
  if (norm(plain).indexOf(nq) < 0) return escaped;
  const re = new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
  return escaped.replace(re, '<span class="mark">$1</span>');
}
function copyText(text, done) {
  const fallback = () => {
    const ta = document.createElement('textarea');
    ta.value = text; ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;left:-9999px';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta); done();
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, fallback);
  } else fallback();
}
/* @@END:JS:UTIL */
