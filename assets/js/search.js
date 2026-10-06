/* Client-side search over /search.json. No dependencies. */
(function () {
  'use strict';

  var app = document.getElementById('search-app');
  if (!app) { return; }

  var input = document.getElementById('search-input');
  var status = document.getElementById('search-status');
  var results = document.getElementById('search-results');
  var form = document.getElementById('search-form');
  var indexUrl = app.getAttribute('data-index');
  var docs = null;
  var loading = null;

  function load() {
    if (docs) { return Promise.resolve(docs); }
    if (!loading) {
      loading = fetch(indexUrl).then(function (r) {
        if (!r.ok) { throw new Error('HTTP ' + r.status); }
        return r.json();
      }).then(function (d) { docs = d; return d; });
    }
    return loading;
  }

  function escapeRegExp(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  function parseTerms(q) {
    return q.toLowerCase().split(/\s+/).map(function (t) {
      return t.replace(/^[^a-z0-9+#]+|[^a-z0-9+#]+$/g, '');
    }).filter(Boolean);
  }

  // A term matches at the start of a word, so "nat" finds NAT and native but not "information".
  function countOccurrences(haystack, needle) {
    var re = new RegExp('(^|[^a-z0-9])' + escapeRegExp(needle), 'g');
    var m = haystack.match(re);
    return m ? m.length : 0;
  }

  function firstIndex(haystack, needle) {
    var m = new RegExp('(^|[^a-z0-9])' + escapeRegExp(needle)).exec(haystack);
    return m ? m.index + m[1].length : -1;
  }

  function score(doc, terms) {
    var title = doc.title.toLowerCase();
    var tags = doc.tags.join(' ').toLowerCase();
    var body = doc.content.toLowerCase();
    var total = 0;
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i];
      var inTitle = countOccurrences(title, t);
      var inTags = countOccurrences(tags, t);
      var inBody = countOccurrences(body, t);
      if (!inTitle && !inTags && !inBody) { return 0; }  // every word must match somewhere
      total += inTitle * 10 + inTags * 6 + Math.min(inBody, 10);
    }
    return total;
  }

  function snippet(doc, terms) {
    var body = doc.content;
    var lower = body.toLowerCase();
    var first = -1;
    for (var i = 0; i < terms.length; i++) {
      var p = firstIndex(lower, terms[i]);
      if (p !== -1 && (first === -1 || p < first)) { first = p; }
    }
    if (first === -1) { return body.slice(0, 160) + (body.length > 160 ? '…' : ''); }
    var start = Math.max(0, first - 70);
    var end = Math.min(body.length, first + 130);
    return (start > 0 ? '…' : '') + body.slice(start, end) + (end < body.length ? '…' : '');
  }

  function appendHighlighted(el, text, terms) {
    if (!terms.length) { el.textContent = text; return; }
    var re = new RegExp('(?:^|(?<=[^a-zA-Z0-9]))(' + terms.map(escapeRegExp).join('|') + ')', 'ig');
    text.split(re).forEach(function (part, i) {
      if (i % 2 === 1) {
        var m = document.createElement('mark');
        m.textContent = part;
        el.appendChild(m);
      } else if (part) {
        el.appendChild(document.createTextNode(part));
      }
    });
  }

  function render(matches, terms, query) {
    results.textContent = '';
    if (!query) {
      status.textContent = 'Type a word to search ' + docs.length + ' posts.';
      return;
    }
    status.textContent = matches.length === 0
      ? 'No posts match “' + query + '”.'
      : matches.length + (matches.length === 1 ? ' post matches “' : ' posts match “') + query + '”.';

    matches.forEach(function (m) {
      var li = document.createElement('li');
      li.className = 'search-result';

      var a = document.createElement('a');
      a.className = 'search-title';
      a.href = m.doc.url;
      appendHighlighted(a, m.doc.title, terms);
      li.appendChild(a);

      var meta = document.createElement('span');
      meta.className = 'search-meta';
      meta.textContent = m.doc.date + (m.doc.tags.length ? ' · ' + m.doc.tags.join(', ') : '');
      li.appendChild(meta);

      var p = document.createElement('p');
      appendHighlighted(p, snippet(m.doc, terms), terms);
      li.appendChild(p);

      results.appendChild(li);
    });
  }

  function run() {
    var query = input.value.trim();
    var terms = parseTerms(query);
    var url = new URL(window.location.href);
    if (query) { url.searchParams.set('q', query); } else { url.searchParams.delete('q'); }
    window.history.replaceState(null, '', url.toString());

    load().then(function () {
      var matches = [];
      if (terms.length) {
        docs.forEach(function (doc) {
          var s = score(doc, terms);
          if (s > 0) { matches.push({ doc: doc, score: s }); }
        });
        matches.sort(function (a, b) { return b.score - a.score; });
      }
      render(matches, terms, terms.length ? query : '');
    }).catch(function () {
      status.textContent = 'Search is unavailable right now. Try again later.';
    });
  }

  form.addEventListener('submit', function (e) { e.preventDefault(); run(); });
  input.addEventListener('input', run);

  var initial = new URLSearchParams(window.location.search).get('q');
  if (initial) { input.value = initial; }
  run();
  input.focus();
})();
