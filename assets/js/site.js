/* Site-wide behaviour: theme toggle, code copy buttons, table of contents,
   widget embeds, copy-link buttons and the tag filter. No dependencies. */
(function () {
  'use strict';

  var root = document.documentElement;

  /* ---------- Theme ---------- */
  function storedTheme() {
    try { return localStorage.getItem('theme'); } catch (e) { return null; }
  }

  function notifyFrames(theme) {
    var frames = document.querySelectorAll('iframe.widget-frame');
    Array.prototype.forEach.call(frames, function (f) {
      try { f.contentWindow.postMessage({ type: 'set-theme', theme: theme }, window.location.origin); } catch (e) {}
    });
  }

  function applyTheme(theme, persist) {
    root.setAttribute('data-theme', theme);
    if (persist) { try { localStorage.setItem('theme', theme); } catch (e) {} }
    var btn = document.getElementById('theme-toggle');
    if (btn) { btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false'); }
    notifyFrames(theme);
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: theme } }));
  }

  function initTheme() {
    var btn = document.getElementById('theme-toggle');
    var current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    if (btn) {
      btn.setAttribute('aria-pressed', current === 'dark' ? 'true' : 'false');
      btn.addEventListener('click', function () {
        applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark', true);
      });
    }
    var mq = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
    if (mq && mq.addEventListener) {
      mq.addEventListener('change', function (e) {
        if (!storedTheme()) { applyTheme(e.matches ? 'dark' : 'light', false); }
      });
    }
  }

  /* ---------- Clipboard helper ---------- */
  function legacyCopy(text) {
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(ta);
      ok ? resolve() : reject(new Error('copy not permitted'));
    });
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      // The Clipboard API can refuse (no focus, permissions policy); fall back to the older method.
      return navigator.clipboard.writeText(text).catch(function () { return legacyCopy(text); });
    }
    return legacyCopy(text);
  }

  function flash(btn, label) {
    var original = btn.getAttribute('data-label') || btn.textContent;
    btn.setAttribute('data-label', original);
    btn.textContent = label;
    window.setTimeout(function () { btn.textContent = original; }, 1500);
  }

  /* ---------- Copy buttons on code blocks ---------- */
  function initCodeCopy() {
    var blocks = document.querySelectorAll('.post-content pre');
    Array.prototype.forEach.call(blocks, function (pre) {
      if (pre.classList.contains('mermaid')) { return; }
      if (pre.parentNode.classList.contains('code-block')) { return; }
      var wrap = document.createElement('div');
      wrap.className = 'code-block';
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'copy-btn';
      btn.textContent = 'Copy';
      btn.setAttribute('aria-label', 'Copy code to clipboard');
      btn.addEventListener('click', function () {
        var code = pre.querySelector('code') || pre;
        copyText(code.textContent).then(function () { flash(btn, 'Copied'); }, function () { flash(btn, 'Failed'); });
      });
      wrap.appendChild(btn);
    });
  }

  /* ---------- Copy link buttons ---------- */
  function initCopyLink() {
    var buttons = document.querySelectorAll('[data-copy-link]');
    Array.prototype.forEach.call(buttons, function (btn) {
      btn.addEventListener('click', function () {
        copyText(btn.getAttribute('data-copy-link')).then(function () { flash(btn, 'Link copied'); }, function () { flash(btn, 'Failed'); });
      });
    });
  }

  /* ---------- Table of contents ---------- */
  function slugify(text) {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'section';
  }

  function initToc() {
    var host = document.getElementById('toc');
    var content = document.querySelector('.post-content');
    if (!host || !content) { return; }
    if (content.querySelectorAll('h2').length < 3) { return; }

    var used = {};
    var list = document.createElement('ol');
    var lastItem = null;
    var sub = null;

    Array.prototype.forEach.call(content.querySelectorAll('h2, h3'), function (h) {
      if (!h.id) {
        var base = slugify(h.textContent);
        var id = base, n = 2;
        while (used[id] || document.getElementById(id)) { id = base + '-' + n++; }
        h.id = id;
      }
      used[h.id] = true;

      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = h.textContent;
      li.appendChild(a);

      if (h.tagName === 'H2') {
        list.appendChild(li);
        lastItem = li;
        sub = null;
      } else {
        if (!sub) {
          sub = document.createElement('ol');
          (lastItem || list).appendChild(sub);
        }
        sub.appendChild(li);
      }
    });

    var details = document.createElement('details');
    details.open = window.innerWidth > 700;  // collapsed on phones so it does not push the article off screen
    var summary = document.createElement('summary');
    summary.textContent = 'On this page';
    details.appendChild(summary);
    details.appendChild(list);
    host.appendChild(details);
    host.hidden = false;
  }

  /* ---------- Widget embeds ---------- */
  function initWidgets() {
    window.addEventListener('message', function (e) {
      if (e.origin !== window.location.origin) { return; }
      if (!e.data || e.data.type !== 'widget-resize' || !(e.data.height > 200)) { return; }
      var frames = document.querySelectorAll('iframe.widget-frame');
      Array.prototype.forEach.call(frames, function (f) {
        if (f.contentWindow === e.source) { f.style.height = (e.data.height + 4) + 'px'; }
      });
    });
    var frames = document.querySelectorAll('iframe.widget-frame');
    Array.prototype.forEach.call(frames, function (f) {
      f.addEventListener('load', function () {
        try { f.contentWindow.postMessage({ type: 'set-theme', theme: root.getAttribute('data-theme') }, window.location.origin); } catch (e) {}
      });
    });
  }

  /* ---------- Tag page filter ---------- */
  function initTagFilter() {
    var sections = document.querySelectorAll('.tag-section');
    if (!sections.length) { return; }
    var showAll = document.getElementById('tag-show-all');

    function apply() {
      var id = '';
      try { id = decodeURIComponent(window.location.hash.slice(1)); } catch (e) {}
      var known = false;
      Array.prototype.forEach.call(sections, function (s) { if (s.id === id) { known = true; } });
      Array.prototype.forEach.call(sections, function (s) { s.hidden = known && s.id !== id; });
      if (showAll) { showAll.hidden = !known; }
    }
    window.addEventListener('hashchange', apply);
    apply();
  }

  function init() {
    initTheme();
    initCodeCopy();
    initCopyLink();
    initToc();
    initWidgets();
    initTagFilter();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
