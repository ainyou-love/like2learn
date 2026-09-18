/* ===================================================================
   LAYER 3 . LOGIC
   Binds DATA to COMPONENTS. The only layer that touches STATE.
   Pipeline:  SRC -> sections(front | body | footer) -> MD.parse
                  -> MD.render -> DOM -> table of contents
   Both views read the SAME text, so they cannot drift apart.
   =================================================================== */

/* front matter (title + lede) | body | footer, split on the outer rules */
function sections(){
  var t = SRC.replace(/^﻿/, '');
  var first = t.indexOf('\n---\n');
  var last = t.lastIndexOf('\n---\n');
  var head = t.slice(0, first).split('\n');
  return {
    title: (head.filter(function(l){ return l.indexOf('# ') === 0; })[0] || '# ').slice(2),
    lede: head
           .filter(function(l){ return l.indexOf('> ') === 0; })
           .map(function(l){ return l.slice(2); }),
    body: t.slice(first + 5, last),
    footer: t.slice(last + 5).split('\n\n')
             .map(function(p){ return p.trim(); })
             .filter(Boolean)
  };
}

/* the copy-out markdown drops layout directives; prose and ASCII stay */
function forCopy(){
  return SRC.split('\n')
    .filter(function(l){ return !/^@(fig:|endfig|box:|endbox)/.test(l); })
    .join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
}

function slug(s, i){
  var base = String(s).toLowerCase()
    .replace(/[^a-z0-9À-ỹ]+/g, '-')
    .replace(/^-+|-+$/g, '').slice(0, 44);
  return (base || 'muc') + '-' + i;
}

/* ---- rendering -------------------------------------------------- */

function buildToc(root){
  var toc = document.getElementById('toc');
  toc.textContent = '';
  var heads = root.querySelectorAll('h2, h3');
  var n = 0;
  Array.prototype.forEach.call(heads, function(h){
    n++;
    if(!h.id) h.id = slug(h.textContent, n);
    var isPart = h.tagName === 'H2';
    var label = h.textContent;
    if(isPart){
      var eb = h.querySelector('.eyebrow');
      if(eb) label = eb.textContent + ' — ' + label.slice(eb.textContent.length);
    }
    var a = el('a', {
      href: '#' + h.id,
      class: isPart ? 'part' : 'lv3',
      text: label
    });
    a.addEventListener('click', function(){ if(!wide()) setNav(false); });
    toc.appendChild(a);
  });
}

function render(){
  var s = sections();

  var h1 = document.getElementById('title');
  h1.textContent = s.title;
  document.title = s.title;

  var lede = document.getElementById('lede');
  lede.textContent = '';
  s.lede.forEach(function(p){ lede.appendChild(el('p', { html: inline(p) })); });

  var doc = document.getElementById('doc');
  doc.textContent = '';
  doc.appendChild(MD.render(MD.parse(s.body)));

  var foot = document.getElementById('foot');
  foot.textContent = '';
  s.footer.forEach(function(p){ foot.appendChild(el('p', { html: inline(p) })); });

  document.getElementById('mdtext').textContent = forCopy();

  buildToc(doc);

  var isDoc = STATE.view === 'doc';
  document.getElementById('docview').hidden = !isDoc;
  document.getElementById('md').hidden = isDoc;
  var vb = document.getElementById('viewbtn');
  vb.textContent = isDoc ? I18N.md : I18N.doc;
  vb.setAttribute('aria-pressed', isDoc ? 'false' : 'true');

  /* no anchors to jump to in the markdown view */
  var nb = document.getElementById('navbtn');
  nb.hidden = !isDoc;
  if(!isDoc && STATE.nav) setNav(false);

  spy();
}

/* ---- controls ---------------------------------------------------- */

function wide(){ return (window.innerWidth || 1280) >= 1180; }

function setView(v){ STATE.view = v; render(); }

function setNav(open){
  STATE.nav = open;
  document.getElementById('nav').classList.toggle('open', open);
  document.getElementById('scrim').hidden = !open || wide();
  document.getElementById('navbtn').setAttribute('aria-expanded', open ? 'true' : 'false');
}

function copyMd(){
  var btn = document.getElementById('copybtn');
  var text = document.getElementById('mdtext').textContent;
  function flash(msg){
    var old = btn.textContent; btn.textContent = msg;
    setTimeout(function(){ btn.textContent = old; }, 1600);
  }
  function fallback(){
    try{
      var r = document.createRange();
      r.selectNodeContents(document.getElementById('mdtext'));
      var sel = window.getSelection();
      sel.removeAllRanges(); sel.addRange(r);
      var ok = false;
      try{ ok = document.execCommand('copy'); }catch(e){}
      flash(ok ? I18N.done : 'Đã bôi đen — Cmd/Ctrl+C');
    }catch(e){ flash('Bôi đen thủ công'); }
  }
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(function(){ flash(I18N.done); }, fallback);
  } else fallback();
}

/* ---- scrollspy ---------------------------------------------------- */

var spyTimer = null;
function spy(){
  if(spyTimer) return;
  spyTimer = setTimeout(function(){
    spyTimer = null;
    var links = document.querySelectorAll('#toc a');
    var best = null, bestTop = -1e9;
    Array.prototype.forEach.call(links, function(a){
      var t = document.getElementById(a.getAttribute('href').slice(1));
      if(!t) return;
      var top = t.getBoundingClientRect().top - 90;
      if(top <= 0 && top > bestTop){ bestTop = top; best = a; }
    });
    Array.prototype.forEach.call(links, function(a){
      a.classList.toggle('on', a === best);
    });
  }, 90);
}

/* ---- wiring ------------------------------------------------------- */

function boot(){
  document.getElementById('kick').textContent = I18N.kick;
  document.getElementById('navhead').textContent = I18N.navHead;
  document.getElementById('copybtn').textContent = I18N.copy;
  document.getElementById('mdnote').textContent = I18N.mdNote;
  document.getElementById('navbtn').textContent = I18N.contents;

  document.getElementById('viewbtn').addEventListener('click', function(){
    setView(STATE.view === 'doc' ? 'md' : 'doc');
  });
  document.getElementById('navbtn').addEventListener('click', function(){
    setNav(!STATE.nav);
  });
  document.getElementById('scrim').addEventListener('click', function(){ setNav(false); });
  document.getElementById('copybtn').addEventListener('click', copyMd);

  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape' && STATE.nav) setNav(false);
  });
  window.addEventListener('scroll', spy, { passive: true });
  window.addEventListener('resize', function(){
    setNav(wide() ? false : STATE.nav);
  });

  render();
  setNav(false);
}

boot();
