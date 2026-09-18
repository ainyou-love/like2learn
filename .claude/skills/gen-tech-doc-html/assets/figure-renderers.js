/* -- figure renderers ---------------------------------------------- */

var FIGURE = {

  questions: function(f){
    return el('div', null, [
      el('ol', { class: 'qlist' }, f.items.map(function(t){
        return el('li', { html: inline(t) }); })),
      el('div', { class: 'score' }, f.scores.map(function(s){
        return el('div', { class: 'sc ' + s.kind }, [
          el('b', { text: s.n }), el('span', { text: s.label })
        ]);
      }))
    ]);
  },

  proof: function(f){
    return el('div', null, [
      el('div', { class: 'proof' }, f.rows.map(function(r){
        return el('div', { class: 'proof-row ' + r.kind }, [
          el('div', { class: 'proof-what' }, [
            el('span', { html: inline(r.what) }),
            el('em', { text: r.detail })
          ]),
          el('div', { class: 'proof-n', text: r.n })
        ]);
      })),
      f.note ? el('div', { class: 'proof-note', html: inline(f.note) }) : null
    ]);
  },

  graph: function(f){
    var kids = [ el('div', { class: 'gnodes' }, f.nodes.map(function(n){
      return el('span', { class: 'gn' + (n[1] ? ' core' : ''), text: n[0] }); })) ];
    f.groups.forEach(function(g){
      if(g.title) kids.push(el('div', { class: 'gsplit', text: g.title }));
      kids.push(el('div', { class: 'gedges' }, g.edges.map(function(e){
        return el('div', { class: 'ge' }, [
          el('i', { text: e[0] }), el('b', { text: e[1] }), el('s', { text: e[2] })
        ]);
      })));
    });
    return el('div', null, kids);
  },

  loop: function(f){
    var kids = f.steps.map(function(s, i){
      return el('div', { class: 'lp' }, [
        el('em', { text: String(i + 1) }),
        el('div', { html: inline(s) })
      ]);
    });
    if(f.back) kids.push(el('div', { class: 'loop-back', text: f.back }));
    return el('div', { class: 'loop' }, kids);
  },

  levels: function(f){
    return el('div', null, f.levels.map(function(L){
      return el('div', { class: 'lvl' }, [
        el('div', { class: 'lvl-h' }, [
          el('span', { text: L.name + '  ' }),
          el('span', { text: L.note })
        ])
      ].concat(L.tools.map(function(t){
        return el('div', { class: 'tool' }, [
          el('b', { text: t[0] }), el('span', { html: inline(t[1]) })
        ]);
      })));
    }));
  },

  routes: function(f){
    return el('div', null, [
      el('div', { class: 'routes-top', text: f.top }),
      el('div', { class: 'routes' }, f.routes.map(function(r){
        return el('div', { class: 'rt' }, [
          el('b', { text: r[0] }), el('span', { html: inline(r[1]) })
        ]);
      })),
      el('div', { class: 'routes-bot', text: f.bottom })
    ]);
  },

  hooks: function(f){
    return el('div', { class: 'hooks' }, f.rows.map(function(r){
      return el('div', { class: 'hk' + (r.none ? ' none' : '') }, [
        el('b', { text: r.hook }),
        el('i', { text: r.reaches }),
        el('span', { html: inline(r.carries) })
      ]);
    }));
  },

  gates: function(f){
    return el('div', { class: 'gates' }, f.rows.map(function(r){
      return el('div', { class: 'gt' }, [
        el('b', { text: r[0] }), el('span', { html: inline(r[1]) })
      ]);
    }));
  },

  islands: function(f){
    var kids = f.rows.map(function(r){
      return el('div', { class: 'is' + (r.shared ? ' shared' : '') }, [
        el('s', { text: r.where }),
        el('i', { text: '→' }),
        el('b', { text: r.scope })
      ]);
    });
    if(f.note) kids.push(el('div', { class: 'isl-note', text: f.note }));
    return el('div', { class: 'isl' }, kids);
  },

  bars: function(f){
    var max = Math.max.apply(null, f.rows.map(function(r){ return r.ms; }));
    return el('div', { class: 'bars' }, f.rows.map(function(r){
      var pct = Math.max(2, Math.round(r.ms / max * 100));
      return el('div', { class: 'br' + (r.cold ? ' cold' : '') }, [
        el('b', { html: inline(r.label) }),
        el('div', { class: 'br-track' }, [
          el('div', { class: 'br-fill', style: 'width:' + pct + '%' }),
          el('span', { class: 'br-val', text: r.val })
        ])
      ]);
    }));
  },

  guards: function(f){
    return el('div', { class: 'guards' }, f.rows.map(function(r){
      return el('div', { class: 'gd ' + r.kind }, [
        el('b', { text: r.tag }),
        el('p', { html: inline(r.text) })
      ]);
    }));
  }
};

