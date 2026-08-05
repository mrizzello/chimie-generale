// Comportements maison ajoutés au thème Quarto par défaut :
// bascule sidebar / recherche / réglages de lecture depuis la navbar,
// navigation chapitre précédent-suivant au clavier et par flèches fixes.
// Volontairement en JS natif (pas de dépendance jQuery) pour ne pas dépendre
// de l'ordre de chargement des autres scripts inclus par ailleurs.

(function () {
  "use strict";

  var STORAGE_KEY = "reader-settings";

  var SIZE_CLASSES = ["reader-size-1", "reader-size-2", "reader-size-3", "reader-size-4", "reader-size-5"];
  var SPACING_CLASSES = ["reader-spacing-1", "reader-spacing-2", "reader-spacing-3"];
  var FONT_CLASSES = ["reader-font-serif", "reader-font-sans"];
  var THEME_CLASSES = ["reader-theme-white", "reader-theme-sepia", "reader-theme-night"];

  var defaultSettings = { size: 3, spacing: 2, font: "serif", theme: "white" };

  function loadSettings() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return Object.assign({}, defaultSettings);
      var parsed = JSON.parse(raw);
      return Object.assign({}, defaultSettings, parsed);
    } catch (e) {
      return Object.assign({}, defaultSettings);
    }
  }

  function saveSettings(settings) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (e) {
      /* localStorage indisponible (navigation privée, etc.) : on continue sans persister */
    }
  }

  function applySettings(settings) {
    var html = document.documentElement;
    SIZE_CLASSES.forEach(function (c) { html.classList.remove(c); });
    SPACING_CLASSES.forEach(function (c) { html.classList.remove(c); });
    FONT_CLASSES.forEach(function (c) { html.classList.remove(c); });
    THEME_CLASSES.forEach(function (c) { html.classList.remove(c); });

    html.classList.add("reader-size-" + settings.size);
    html.classList.add("reader-spacing-" + settings.spacing);
    html.classList.add("reader-font-" + settings.font);
    html.classList.add("reader-theme-" + settings.theme);

    var panel = document.getElementById("reader-settings-panel");
    if (!panel) return;
    panel.querySelectorAll("[data-reader-font]").forEach(function (btn) {
      btn.classList.toggle("reader-active", btn.getAttribute("data-reader-font") === settings.font);
    });
    panel.querySelectorAll("[data-reader-theme]").forEach(function (btn) {
      btn.classList.toggle("reader-active", btn.getAttribute("data-reader-theme") === settings.theme);
    });
  }

  function findNavbarToolByLabel(labelSubstring) {
    var links = document.querySelectorAll(".navbar a.nav-link, .navbar a.quarto-navigation-tool, a.quarto-navigation-tool");
    for (var i = 0; i < links.length; i++) {
      var icon = links[i].querySelector("[aria-label]");
      var label = (icon && icon.getAttribute("aria-label")) || links[i].getAttribute("aria-label") || links[i].getAttribute("title") || "";
      if (label.indexOf(labelSubstring) !== -1) return links[i];
    }
    return null;
  }

  function setupSidebarToggle() {
    var btn = findNavbarToolByLabel("barre latérale");
    if (!btn) return;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var sidebar = document.getElementById("quarto-sidebar");
      if (!sidebar) return;
      if (window.bootstrap && window.bootstrap.Collapse) {
        var instance = window.bootstrap.Collapse.getOrCreateInstance(sidebar, { toggle: false });
        instance.toggle();
      } else {
        sidebar.classList.toggle("show");
      }
    });
  }

  function setupSearchToggle() {
    var btn = findNavbarToolByLabel("recherche");
    if (!btn) return;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var box = document.querySelector(".sidebar-search");
      if (!box) return;
      box.classList.toggle("search-visible");
      if (box.classList.contains("search-visible")) {
        var input = box.querySelector("input");
        if (input) input.focus();
      }
    });
  }

  function setupReaderSettingsToggle() {
    var btn = findNavbarToolByLabel("Réglages de lecture");
    var panel = document.getElementById("reader-settings-panel");
    if (!btn || !panel) return;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      panel.classList.toggle("reader-settings-visible");
    });

    var settings = loadSettings();

    panel.querySelectorAll("[data-reader-action]").forEach(function (el) {
      el.addEventListener("click", function () {
        var action = el.getAttribute("data-reader-action");
        if (action === "size-inc") settings.size = Math.min(5, settings.size + 1);
        if (action === "size-dec") settings.size = Math.max(1, settings.size - 1);
        if (action === "spacing-inc") settings.spacing = Math.min(3, settings.spacing + 1);
        if (action === "spacing-dec") settings.spacing = Math.max(1, settings.spacing - 1);
        applySettings(settings);
        saveSettings(settings);
      });
    });

    panel.querySelectorAll("[data-reader-font]").forEach(function (el) {
      el.addEventListener("click", function () {
        settings.font = el.getAttribute("data-reader-font");
        applySettings(settings);
        saveSettings(settings);
      });
    });

    panel.querySelectorAll("[data-reader-theme]").forEach(function (el) {
      el.addEventListener("click", function () {
        settings.theme = el.getAttribute("data-reader-theme");
        applySettings(settings);
        saveSettings(settings);
      });
    });
  }

  function setupChapterNavigation() {
    var prevLink = document.querySelector('link[rel="prev"]');
    var nextLink = document.querySelector('link[rel="next"]');

    if (prevLink) {
      var prevArrow = document.createElement("a");
      prevArrow.href = prevLink.href;
      prevArrow.className = "reader-nav-arrow reader-nav-prev";
      prevArrow.setAttribute("aria-label", "Chapitre précédent");
      prevArrow.innerHTML = "&#8249;";
      document.body.appendChild(prevArrow);
    }
    if (nextLink) {
      var nextArrow = document.createElement("a");
      nextArrow.href = nextLink.href;
      nextArrow.className = "reader-nav-arrow reader-nav-next";
      nextArrow.setAttribute("aria-label", "Chapitre suivant");
      nextArrow.innerHTML = "&#8250;";
      document.body.appendChild(nextArrow);
    }

    document.addEventListener("keydown", function (e) {
      var tag = (document.activeElement && document.activeElement.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA" || (document.activeElement && document.activeElement.isContentEditable)) {
        return;
      }
      if (e.key === "ArrowLeft" && prevLink) {
        window.location.href = prevLink.href;
      } else if (e.key === "ArrowRight" && nextLink) {
        window.location.href = nextLink.href;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    applySettings(loadSettings());
    setupSidebarToggle();
    setupSearchToggle();
    setupReaderSettingsToggle();
    setupChapterNavigation();
  });
})();
