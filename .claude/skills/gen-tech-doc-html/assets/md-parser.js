/* ===================================================================
   LAYER 2 . COMPONENTS
   Pure: data in, DOM out. Must not read STATE.
   =================================================================== */

function esc(s){ return String(s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function el(tag, attrs, kids){
  var n = document.createElement(tag);
  if(attrs) for(var k in attrs){
    if(k === 'html') n.innerHTML = attrs[k];
    else if(k === 'text') n.textContent = attrs[k];
    else n.setAttribute(k, attrs[k]);
  }
  (kids || []).forEach(function(c){ if(c) n.appendChild(c); });
  return n;
}

/* Code spans are pulled out before escaping and put back after, so that
   markup inside them is never interpreted. The sentinel is ordinary text,
   not a control character, so the source stays copy-paste safe. */
function inline(s){
  var keep = [];
  s = String(s).replace(/`([^`]+)`/g, function(_, c){
    keep.push(c); return 'K0DE' + (keep.length - 1) + 'K0DE';
  });
  s = esc(s)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*\w])\*([^*]+)\*(?![*\w])/g, '$1<em>$2</em>');
  return s.replace(/K0DE(\d+)K0DE/g, function(_, i){
    return '<code>' + esc(keep[+i]) + '</code>';
  });
}

var BLOCK = {
  h: function(b){
    var tag = b.level === 1 ? 'h2' : b.level === 2 ? 'h3' : 'h4';
    var m = /^(PHAN|PHẦN|PART)\s+(\d+)\s*—\s*(.*)$/.exec(b.text);
    if(tag === 'h2' && m){
      return el('h2', null, [
        el('span', { class: 'eyebrow', text: m[1] + ' ' + m[2] }),
        el('span', { html: inline(m[3]) })
      ]);
    }
    return el(tag, { html: inline(b.text) });
  },
  p:  function(b){ return el('p', { html: inline(b.text) }); },
  ul: function(b){ return el('ul', null, b.items.map(function(t){
        return el('li', { html: inline(t) }); })); },
  ol: function(b){ return el('ol', null, b.items.map(function(t){
        return el('li', { html: inline(t) }); })); },
  quote: function(b){ return el('blockquote', null, b.items.map(function(t){
        return el('p', { html: inline(t) }); })); },
  code: function(b){
    return el('div', { class: 'pre' }, [ el('pre', { text: b.text }) ]);
  },
  hr: function(){ return el('hr'); },
  table: function(b){
    var head = el('tr', null, b.head.map(function(c){
      return el('th', { html: inline(c) }); }));
    var body = b.rows.map(function(r){
      return el('tr', null, r.map(function(c){ return el('td', { html: inline(c) }); }));
    });
    return el('div', { class: 'tw' }, [
      el('table', null, [ el('thead', null, [head]), el('tbody', null, body) ])
    ]);
  },
  fig: function(b){
    var f = FIG[b.id];
    if(!f) return el('p', { text: '[missing figure: ' + b.id + ']' });
    var render = FIGURE[f.type];
    if(!render) return el('p', { text: '[no renderer: ' + f.type + ']' });
    return el('figure', null, [
      el('div', { class: 'fig' }, [ render(f) ]),
      f.cap ? el('figcaption', { html: inline(f.cap) }) : null
    ]);
  }
};

/* -- markdown ------------------------------------------------------- */

var MD = {
  parse: function(src){
    var lines = src.split('\n'), out = [], i = 0;
    function blank(s){ return !s.trim(); }
    function cells(s){
      return s.trim().replace(/^\|/, '').replace(/\|$/, '')
              .split('|').map(function(c){ return c.trim(); });
    }

    while(i < lines.length){
      var ln = lines[i];
      if(blank(ln)){ i++; continue; }

      /* figure directive: keep the id, skip the ASCII fallback body */
      var fm = /^@fig:(\S+)\s*$/.exec(ln);
      if(fm){
        var id = fm[1]; i++;
        while(i < lines.length && !/^@endfig\s*$/.test(lines[i])) i++;
        i++;
        out.push({ t: 'fig', id: id });
        continue;
      }

      var hm = /^(#{1,4})\s+(.*)$/.exec(ln);
      if(hm){ out.push({ t: 'h', level: hm[1].length, text: hm[2].trim() }); i++; continue; }

      if(/^---\s*$/.test(ln)){ out.push({ t: 'hr' }); i++; continue; }

      if(/^\|/.test(ln) && i + 1 < lines.length && /^\|[\s:|-]+\|?\s*$/.test(lines[i + 1])){
        var head = cells(ln); i += 2;
        var rows = [];
        while(i < lines.length && /^\|/.test(lines[i])){ rows.push(cells(lines[i])); i++; }
        out.push({ t: 'table', head: head, rows: rows });
        continue;
      }

      if(/^>\s?/.test(ln)){
        var q = [];
        while(i < lines.length && /^>\s?/.test(lines[i])){
          q.push(lines[i].replace(/^>\s?/, '')); i++;
        }
        out.push({ t: 'quote', items: q });
        continue;
      }

      var lm = /^(\s*)([-*]|\d+\.)\s+(.*)$/.exec(ln);
      if(lm){
        var ordered = /\d/.test(lm[2]), items = [];
        while(i < lines.length){
          var m2 = /^(\s*)([-*]|\d+\.)\s+(.*)$/.exec(lines[i]);
          if(m2){ items.push(m2[3]); i++; }
          else if(/^\s{2,}\S/.test(lines[i]) && items.length){
            items[items.length - 1] += ' ' + lines[i].trim(); i++;
          } else break;
        }
        out.push({ t: ordered ? 'ol' : 'ul', items: items });
        continue;
      }

      /* Four-space indented code. Blank lines inside one block are kept,
         then trimmed off the end, so a diagram split by blank lines stays
         a single block instead of becoming several. */
      if(/^ {4}\S/.test(ln)){
        var buf = [];
        while(i < lines.length){
          if(/^ {4}/.test(lines[i])){ buf.push(lines[i].slice(4)); i++; }
          else if(blank(lines[i]) && /^ {4}/.test(lines[i + 1] || '')){ buf.push(''); i++; }
          else break;
        }
        while(buf.length && !buf[buf.length - 1].trim()) buf.pop();
        out.push({ t: 'code', text: buf.join('\n') });
        continue;
      }

      var para = [ln.trim()]; i++;
      while(i < lines.length && !blank(lines[i]) &&
            !/^(#{1,4}\s|@fig:|@endfig|---\s*$|\||>\s?|\s*([-*]|\d+\.)\s|\s{4}\S)/.test(lines[i])){
        para.push(lines[i].trim()); i++;
      }
      out.push({ t: 'p', text: para.join(' ') });
    }
    return out;
  },

  render: function(blocks){
    var frag = document.createDocumentFragment();
    blocks.forEach(function(b){
      var fn = BLOCK[b.t];
      if(fn) frag.appendChild(fn(b));
    });
    return frag;
  }
};
