/* UI mockup inspector. Paste inside <script> at the end of <body>.
   Toggle: press ` (backquote) or click the "Inspect" button.
   Hover: outline + address.  Click: select.  Shift+click: add to selection.
   Alt+click (or "Parent" button): select the parent addressed element.
   Picking uses geometry, not browser hit testing, so it works through
   pointer-events:none layers, full-screen overlays, and scaled stages.
   "Move panel" moves the panel to the next corner if it covers an element.
   Panel: the Selector field shows the selector for the chosen scope. You can edit it.
   Write a change, "Add edit", then "Copy edits" to get edit commands.
   Readability: "Background" covers every [data-backdrop] element with a test
   background (bright, mid-gray, dark, busy) to check HUD text over gameplay.
   Motion: speed (1x-0.1x), reduced-motion toggle, replay via window.uiiReplay(ids). */
(() => {
  const css = `
  #uii-btn{position:fixed;right:12px;bottom:12px;z-index:2147483647;font:12px/1 monospace;padding:8px 10px;background:#111;color:#fff;border:1px solid #888;cursor:pointer}
  #uii-tip{position:fixed;z-index:2147483646;pointer-events:none;font:11px/1.3 monospace;background:#000c;color:#ffd75e;padding:2px 5px;white-space:nowrap}
  .uii-hover{outline:2px dashed #ffd75e!important;outline-offset:-2px}
  .uii-sel{outline:2px solid #4fd1ff!important;outline-offset:-2px}
  #uii-panel{position:fixed;right:12px;bottom:48px;z-index:2147483647;width:380px;max-height:70vh;overflow:auto;background:#111;color:#eee;border:1px solid #888;font:12px/1.4 monospace;padding:10px;box-sizing:border-box}
  #uii-panel textarea,#uii-panel input[type=text]{width:100%;box-sizing:border-box;background:#222;color:#eee;border:1px solid #555;font:inherit;padding:3px}
  #uii-panel textarea{height:60px}
  #uii-panel #uii-selector{color:#4fd1ff}
  #uii-panel button,#uii-panel select{font:inherit;background:#222;color:#eee;border:1px solid #555;margin:2px 2px 2px 0;padding:3px 6px;cursor:pointer;max-width:100%}
  #uii-panel .row{margin:6px 0;border-bottom:1px solid #333;padding-bottom:6px}
  #uii-panel .muted{color:#999}
  #uii-panel .flex{display:flex;gap:4px;align-items:center}
  #uii-panel .flex input{flex:1}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  let on = false, sel = [], hover = null, speed = 1, reduced = false, selector = '', pending = null, bg = 'original';

  // Readability test backgrounds. They cover every [data-backdrop] element (the fake gameplay scene).
  const BACKGROUNDS = {
    original: '',
    bright: 'linear-gradient(#bfe3ff, #ffffff 65%, #f1e2c2)',
    'mid-gray': '#7f7f7f',
    dark: '#06070b',
    busy: 'repeating-conic-gradient(#ffffff 0 25%, #0000 0 50%) 0 0 / 18px 18px, ' +
          'conic-gradient(#ff3b30, #ffd60a, #34c759, #0a84ff, #bf5af2, #ff3b30)'
  };
  function applyBackground() {
    document.querySelectorAll('.uii-bgtest').forEach(n => n.remove());
    if (bg === 'original') return;
    document.querySelectorAll('[data-backdrop]').forEach(b => {
      if (getComputedStyle(b).position === 'static') b.style.position = 'relative';
      const layer = document.createElement('div');
      layer.className = 'uii-bgtest';
      layer.style.cssText = `position:absolute;inset:0;pointer-events:none;background:${BACKGROUNDS[bg]}`;
      b.appendChild(layer);
    });
  }
  const root = document.documentElement;
  function applyMotion() {
    // CSS: use calc(var(--motion-duration-normal) / var(--motion-slow, 1)) in durations.
    root.style.setProperty('--motion-slow', speed);
    (document.getAnimations ? document.getAnimations() : []).forEach(a => { a.playbackRate = speed; });
    root.toggleAttribute('data-reduced-motion', reduced);
  }
  const notes = [];
  const btn = Object.assign(document.createElement('button'), {id: 'uii-btn', textContent: 'Inspect'});
  const tip = Object.assign(document.createElement('div'), {id: 'uii-tip'});
  const panel = Object.assign(document.createElement('div'), {id: 'uii-panel'});
  tip.hidden = panel.hidden = true;
  document.body.append(btn, tip, panel);

  // Panel corner. "Move panel" cycles it, so it does not cover the element you want.
  const docks = ['br', 'bl', 'tl', 'tr'];
  let dock = 0;
  try { dock = (+localStorage.getItem('uii-dock') || 0) % 4; } catch (_) {}
  function applyDock() {
    const d = docks[dock], v = d[0] === 'b' ? 'bottom' : 'top', h = d[1] === 'r' ? 'right' : 'left';
    for (const el of [btn, panel]) ['top', 'bottom', 'left', 'right'].forEach(k => { el.style[k] = 'auto'; });
    btn.style[v] = '12px'; btn.style[h] = '12px';
    panel.style[v] = '48px'; panel.style[h] = '12px';
    try { localStorage.setItem('uii-dock', dock); } catch (_) {}
  }
  applyDock();

  const own = el => el && el.closest && el.closest('#uii-btn,#uii-panel,#uii-tip');
  const addr = el => el && el.closest('[data-id]');
  const info = el => ({
    id: el.dataset.id,
    comp: el.dataset.component || '',
    tags: (el.dataset.tags || '').split(/\s+/).filter(Boolean)
  });
  const parentAddr = el => el.parentElement && addr(el.parentElement);
  const branch = id => id.replace(/\[\d+\]/g, '[*]');
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');

  // Geometric hit test. Ignores pointer-events and overlays.
  // Skips invisible elements and parts clipped by an overflow ancestor.
  const inside = (r, x, y) => x >= r.left && x <= r.right && y >= r.top && y <= r.bottom;
  function hitRect(el, x, y) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height || !inside(r, x, y)) return null;
    let o = 1;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return null;
      o *= parseFloat(cs.opacity);
      if (o < 0.05) return null;
      if (n !== el && cs.overflow !== 'visible' && !inside(n.getBoundingClientRect(), x, y)) return null;
    }
    return r;
  }
  function pick(x, y) {
    const hits = [];
    document.querySelectorAll('[data-id]').forEach(el => {
      if (own(el)) return;
      const r = hitRect(el, x, y);
      if (r) hits.push({el, area: r.width * r.height});
    });
    // Keep the deepest hits (no other hit inside them), then the smallest.
    const leaves = hits.filter(h => !hits.some(o => o !== h && h.el.contains(o.el)));
    leaves.sort((a, b) => a.area - b.area);
    return leaves.length ? leaves[0].el : null;
  }

  function toggle(v) {
    on = v ?? !on;
    btn.textContent = on ? 'Inspect: ON' : 'Inspect';
    panel.hidden = !on; tip.hidden = true;
    if (!on) { setHover(null); setSel([]); }
    render();
  }
  function setHover(el) {
    if (el === hover) return;
    hover && hover.classList.remove('uii-hover');
    hover = el;
    hover && hover.classList.add('uii-hover');
  }
  function setSel(list) {
    sel.forEach(e => e.classList.remove('uii-sel'));
    sel = [...new Set(list)];
    sel.forEach(e => e.classList.add('uii-sel'));
    const sc = scopes();
    selector = sc.length ? sc[0][1] : '';
    render();
  }

  function scopes() {
    if (!sel.length) return [];
    const i = sel.map(info), out = [];
    if (sel.length === 1) {
      out.push(['Only this instance', i[0].id]);
      if (/\[\d+\]/.test(i[0].id)) out.push(['All items in this list', branch(i[0].id)]);
      out.push(['This element and descendants', i[0].id + '.**']);
    } else {
      out.push(['These instances', i.map(x => x.id).join(', ')]);
    }
    const comps = [...new Set(i.map(x => x.comp))];
    const screen = i[0].id.split('.')[0];
    if (comps.length === 1 && comps[0]) {
      const base = comps[0].split(':')[0];
      out.push([`Component ${base} (all instances)`, base]);
      if (comps[0].includes(':')) out.push([`Component variant ${comps[0]}`, comps[0]]);
      out.push([`${base} on screen "${screen}"`, `${base} in ${screen}.**`]);
    }
    const common = i.map(x => x.tags).reduce((a, b) => a.filter(t => b.includes(t)));
    common.forEach(t => {
      out.push([`Tag ${t} on this screen`, `${screen}.** ${t}`]);
      out.push([`Tag ${t} everywhere`, t]);
    });
    return out;
  }

  function selectBy(pred) { setSel([...document.querySelectorAll('[data-id]')].filter(el => !own(el) && pred(el))); }

  function render() {
    if (!on) return;
    const note = panel.querySelector('#uii-note');
    const draft = note ? note.value : '';
    const i = sel.map(info), sc = scopes();
    panel.innerHTML = `
      <div class="row flex"><b>Inspector</b><span style="flex:1"></span><button data-a="dock">Move panel</button></div>
      <div class="row"><b>Selection (${sel.length})</b>
        ${i.map(x => `<div>${esc(x.id)}<br><span class="muted">${esc(x.comp || '(no component)')} ${esc(x.tags.join(' '))}</span></div>`).join('') || '<div class="muted">Click an element. Shift+click adds. Alt+click selects the parent.</div>'}
        ${sel.length ? `<div><button data-a="parent">Parent</button><button data-a="same-comp">Same component</button><button data-a="clear">Clear</button></div>` : ''}
      </div>
      ${sel.length ? `<div class="row">
        <div>Scope</div><select id="uii-scope">${sc.map(([l, s]) => `<option value="${esc(s)}"${s === selector ? ' selected' : ''}>${esc(l)}</option>`).join('')}${sc.some(([, s]) => s === selector) ? '' : '<option selected>(custom)</option>'}</select>
        <div>Selector</div>
        <div class="flex"><input type="text" id="uii-selector" value="${esc(selector)}" spellcheck="false"><button data-a="copy-sel">Copy</button></div>
        <div>Change</div><textarea id="uii-note" placeholder="for example: thinner, 2px inner stroke, use $color.accent.primary">${esc(draft)}</textarea>
        <button data-a="add">Add edit</button></div>` : ''}
      <div class="row"><b>Readability</b>
        <div>Background <select id="uii-bg">${Object.keys(BACKGROUNDS).map(k => `<option value="${k}"${k === bg ? ' selected' : ''}>${k}</option>`).join('')}</select></div>
        ${document.querySelector('[data-backdrop]') ? '' : '<div class="muted">This mockup has no [data-backdrop] element. Background test is not available.</div>'}
      </div>
      <div class="row"><b>Motion</b>
        <div>Speed <select id="uii-speed">${[1, 0.5, 0.25, 0.1].map(s => `<option value="${s}"${s === speed ? ' selected' : ''}>${s}x</option>`).join('')}</select>
        <button data-a="reduced">${reduced ? 'Reduced motion: ON' : 'Reduced motion: OFF'}</button>
        <button data-a="replay">Replay ${sel.length ? 'selection' : 'all'}</button></div>
        ${typeof window.uiiReplay === 'function' ? '' : '<div class="muted">This mockup has no window.uiiReplay(ids). Replay is not available.</div>'}
      </div>
      <div class="row"><b>Edits (${notes.length})</b>
        ${notes.map((n, k) => `<div>${esc(n.selector)}: ${esc(n.note)} <button data-a="del" data-k="${k}">x</button></div>`).join('') || '<div class="muted">No edits yet.</div>'}
        ${notes.length ? `<button data-a="copy">Copy edits</button>` : ''}
      </div>`;
  }

  function copyText(text, button) {
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
      .then(() => { button.textContent = 'Copied'; })
      .catch(() => { window.prompt('Copy:', text); });
  }

  panel.addEventListener('click', e => {
    const a = e.target.dataset.a; if (!a) return;
    if (a === 'dock') { dock = (dock + 1) % 4; applyDock(); }
    if (a === 'parent') setSel(sel.map(parentAddr).filter(Boolean));
    if (a === 'clear') setSel([]);
    if (a === 'same-comp') { const c = info(sel[0]).comp.split(':')[0]; if (c) selectBy(el => (el.dataset.component || '').split(':')[0] === c); }
    if (a === 'copy-sel') copyText(selector, e.target);
    if (a === 'add') {
      const note = panel.querySelector('#uii-note').value.trim();
      if (note && selector.trim()) {
        notes.push({selector: selector.trim(), note});
        panel.querySelector('#uii-note').value = '';
        render();
      }
    }
    if (a === 'reduced') { reduced = !reduced; applyMotion(); render(); }
    if (a === 'replay' && typeof window.uiiReplay === 'function') {
      window.uiiReplay(sel.map(s => s.dataset.id));
      setTimeout(applyMotion, 0);
    }
    if (a === 'del') { notes.splice(+e.target.dataset.k, 1); render(); }
    if (a === 'copy') copyText(notes.map(n => `${n.selector}: ${n.note}`).join('\n'), e.target);
  });

  panel.addEventListener('change', e => {
    if (e.target.id === 'uii-speed') { speed = +e.target.value; applyMotion(); }
    if (e.target.id === 'uii-bg') { bg = e.target.value; applyBackground(); }
    if (e.target.id === 'uii-scope' && e.target.value !== '(custom)') { selector = e.target.value; render(); }
  });
  panel.addEventListener('input', e => {
    if (e.target.id === 'uii-selector') selector = e.target.value;  // no re-render, keeps the caret
  });

  btn.addEventListener('click', () => toggle());
  document.addEventListener('keydown', e => {
    if (e.key === '`' && !/^(input|textarea|select)$/i.test(document.activeElement.tagName)) toggle();
  });

  function onMove(x, y) {
    const el = pick(x, y);
    setHover(el);
    if (!el) { tip.hidden = true; return; }
    const v = info(el);
    tip.textContent = `${v.id}  ${v.comp}  ${v.tags.join(' ')}`;
    tip.hidden = false;
    tip.style.left = Math.max(4, Math.min(x + 12, innerWidth - tip.offsetWidth - 4)) + 'px';
    tip.style.top = Math.min(y + 14, innerHeight - tip.offsetHeight - 4) + 'px';
  }
  document.addEventListener('mousemove', e => {
    if (!on || own(e.target)) { tip.hidden = true; setHover(null); return; }
    const x = e.clientX, y = e.clientY;
    if (!pending) pending = requestAnimationFrame(() => { pending = null; onMove(x, y); });
  }, true);
  document.addEventListener('mouseleave', () => { tip.hidden = true; setHover(null); });

  // In inspect mode, the mockup does not get pointer input.
  ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'dblclick', 'contextmenu'].forEach(t =>
    document.addEventListener(t, e => { if (on && !own(e.target)) { e.preventDefault(); e.stopPropagation(); } }, true));
  document.addEventListener('click', e => {
    if (!on || own(e.target)) return;
    e.preventDefault(); e.stopPropagation();
    let el = pick(e.clientX, e.clientY); if (!el) return;
    if (e.altKey) el = parentAddr(el) || el;
    setSel(e.shiftKey ? (sel.includes(el) ? sel.filter(s => s !== el) : [...sel, el]) : [el]);
  }, true);
})();
