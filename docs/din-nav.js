/*
 * Injects an "All activities" link into the codelab title bar, linking back to
 * the topic menu at index.html.
 *
 * Why this exists rather than markup in each page: codelab-elements builds
 * #codelab-title itself and replaces the element's contents when the custom
 * element upgrades, so anything authored inline there is discarded. This waits
 * for the bar to appear, then prepends the link.
 *
 * Why not reuse the built-in #arrow-back button: its href is computed from the
 * ?index= query parameter by a function that strips everything outside
 * [a-z0-9-] and resolves the result against location.origin. On a project
 * Pages site (roitraining.github.io/gcp-demos/) that can only ever yield
 * "/gcp-demos" or "/" -- it cannot express a path ending in a slash, so it
 * cannot reach this menu. custom.css keeps it hidden.
 */
(function () {
  'use strict';

  var LABEL = 'All activities';
  var HREF = 'index.html';

  /*
   * The "Done" button on the final step shares #arrow-back's computed href and
   * so has the same problem: it lands on the org root rather than this menu.
   * Repoint it. This matters most on the topic pages that currently hold a
   * single step, where Done is visible immediately.
   */
  function fixDone() {
    var done = document.querySelector('google-codelab #done');
    if (done) done.href = HREF;
  }

  function inject(bar) {
    if (bar.querySelector('.din-back')) return true;

    var link = document.createElement('a');
    link.className = 'din-back';
    link.href = HREF;
    link.setAttribute('aria-label', LABEL);

    var icon = document.createElement('i');
    icon.className = 'material-icons';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = 'arrow_back';

    var text = document.createElement('span');
    text.className = 'din-back-text';
    text.textContent = LABEL;

    link.appendChild(icon);
    link.appendChild(text);
    bar.insertBefore(link, bar.firstChild);
    return true;
  }

  function attempt() {
    var bar = document.querySelector('google-codelab #codelab-title');
    if (!bar) return false;
    inject(bar);
    fixDone();
    return true;
  }

  if (attempt()) return;

  // The bar is created during element upgrade, which may not have happened by
  // the time this runs. Watch for it, and stop watching once it is handled.
  var observer = new MutationObserver(function () {
    if (attempt()) observer.disconnect();
  });

  observer.observe(document.documentElement, {childList: true, subtree: true});

  // Backstop: if the codelab bundle fails to load, the bar never appears and
  // the observer would otherwise run for the life of the page.
  setTimeout(function () {
    observer.disconnect();
  }, 10000);
})();
