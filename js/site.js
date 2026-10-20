/* viotours.in — site behaviour: menu, theme music, forms, package filters, currency hints. */
(function () {
  "use strict";
  var C = window.VIOTOURS || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} }
  };

  /* ---------- mobile menu ---------- */
  var header = $(".site-header"), menuBtn = $(".menu-btn");
  if (header && menuBtn) {
    menuBtn.addEventListener("click", function () {
      var open = header.classList.toggle("is-open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && header.classList.contains("is-open")) { header.classList.remove("is-open"); menuBtn.setAttribute("aria-expanded", "false"); menuBtn.focus(); }
    });
  }

  /* ---------- WhatsApp links ---------- */
  function waLink(text) { return "https://wa.me/" + (C.whatsappNumber || "") + (text ? "?text=" + encodeURIComponent(text) : ""); }
  $$("[data-wa]").forEach(function (a) { a.href = waLink(a.getAttribute("data-wa")); });
  $$("[data-email]").forEach(function (a) { a.href = "mailto:" + C.email; if (!a.textContent.trim()) a.textContent = C.email; });

  /* ---------- theme music ----------
     Plays once on load, fading to 35%. If the browser blocks sound, it starts on the first
     tap or key press. A mute lasts for the session and later pages don't restart it. */
  var audio = $("#bgm"), mbtn = $(".music");
  if (audio && mbtn && C.music && C.music.enabled) {
    var TARGET = C.music.volume || 0.35, fadeT, played = store.get("vt-music");
    audio.loop = !!C.music.loop;
    var ui = function (on) { mbtn.setAttribute("aria-pressed", on ? "true" : "false"); $(".music__label", mbtn).textContent = on ? "Mute" : "Play music"; mbtn.setAttribute("aria-label", on ? "Mute theme music" : "Play theme music"); };
    var fade = function (to, done) {
      clearInterval(fadeT);
      fadeT = setInterval(function () {
        var up = to > audio.volume, v = audio.volume + (up ? 0.02 : -0.02);
        if ((up && v >= to) || (!up && v <= to)) { audio.volume = to; clearInterval(fadeT); if (done) done(); }
        else audio.volume = Math.max(0, Math.min(1, v));
      }, 40);
    };
    var start = function () { audio.volume = 0; return audio.play().then(function () { fade(TARGET); ui(true); store.set("vt-music", "played"); }); };
    var arm = function () {
      var go = function (e) {
        if (e && mbtn.contains(e.target)) return;
        document.removeEventListener("pointerdown", go, true); document.removeEventListener("keydown", go, true);
        if (audio.paused && store.get("vt-music") !== "muted") start().catch(function () {});
      };
      document.addEventListener("pointerdown", go, true); document.addEventListener("keydown", go, true);
    };
    ui(false);
    // Autoplay only on the first page of the visit, never after a mute.
    if (!played) start().catch(arm);
    mbtn.addEventListener("click", function () {
      if (audio.paused) { if (audio.ended) audio.currentTime = 0; start().catch(function () {}); }
      else { fade(0, function () { audio.pause(); }); ui(false); store.set("vt-music", "muted"); }
    });
    audio.addEventListener("ended", function () { ui(false); });
  } else if (mbtn) { mbtn.hidden = true; }

  /* ---------- currency hint ---------- */
  var fmt = function (n) { return Math.round(n).toLocaleString("en-US"); };
  $$("[data-inr]").forEach(function (el) {
    var inr = +el.getAttribute("data-inr"); if (!inr || !C.fx) return;
    el.textContent = "≈ AED " + fmt(inr / C.fx.AED) + " · USD " + fmt(inr / C.fx.USD);
  });

  /* ---------- package filters ---------- */
  var grid = $("[data-filter-grid]");
  if (grid) {
    var cards = $$("[data-styles]", grid), empty = $("[data-empty]");
    var state = { style: "all", activity: "all" };
    var apply = function () {
      var shown = 0;
      cards.forEach(function (c) {
        var okS = state.style === "all" || (" " + c.getAttribute("data-styles") + " ").indexOf(" " + state.style + " ") > -1;
        var okA = state.activity === "all" || (" " + c.getAttribute("data-activities") + " ").indexOf(" " + state.activity + " ") > -1;
        c.hidden = !(okS && okA); if (!c.hidden) shown++;
      });
      if (empty) empty.hidden = shown > 0;
      var url = new URL(location.href);
      ["style", "activity"].forEach(function (k) { if (state[k] === "all") url.searchParams.delete(k); else url.searchParams.set(k, state[k]); });
      history.replaceState(null, "", url);
    };
    var bind = function (attr, key) {
      var btns = $$("[" + attr + "]");
      btns.forEach(function (b) {
        b.addEventListener("click", function () {
          var v = b.getAttribute(attr);
          state[key] = (state[key] === v && v !== "all") ? "all" : v;
          btns.forEach(function (x) { x.setAttribute("aria-pressed", x.getAttribute(attr) === state[key] ? "true" : "false"); });
          apply();
        });
      });
      var q = new URLSearchParams(location.search).get(key);
      if (q && btns.some(function (b) { return b.getAttribute(attr) === q; })) {
        state[key] = q; btns.forEach(function (x) { x.setAttribute("aria-pressed", x.getAttribute(attr) === q ? "true" : "false"); });
      }
    };
    bind("data-filter-style", "style"); bind("data-filter-activity", "activity"); apply();
  }

  /* ---------- prefill enquiry from ?package= ---------- */
  var pkgSel = $("#enq-package");
  if (pkgSel) {
    var p = new URLSearchParams(location.search).get("package");
    if (p) $$("option", pkgSel).forEach(function (o) { if (o.value === p) o.selected = true; });
  }

  /* ---------- forms ---------- */
  function summarise(data) {
    var lines = ["viotours.in — " + (data.form || "enquiry")];
    Object.keys(data).forEach(function (k) { if (k !== "form" && k !== "website" && data[k]) lines.push(k + ": " + data[k]); });
    return lines.join("\n");
  }
  function status(form, ok, html) {
    var s = $(".form-status", form); if (!s) return;
    s.className = "form-status " + (ok ? "is-ok" : "is-err"); s.innerHTML = html; s.setAttribute("role", ok ? "status" : "alert");
  }
  $$("form[data-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      var fd = new FormData(form), data = { form: form.getAttribute("data-form"), page: location.pathname };
      fd.forEach(function (v, k) { data[k] = data[k] ? data[k] + ", " + v : v; });
      if (data.website) return; // honeypot
      var btn = $("button[type=submit]", form), label = btn ? btn.textContent : "";
      if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
      var done = function () { if (btn) { btn.disabled = false; btn.textContent = label; } };
      var fallback = function () {
        var text = summarise(data);
        status(form, false, "We couldn't send this from the website just now. Please send it to us on " +
          '<a href="' + waLink(text) + '" target="_blank" rel="noopener">WhatsApp</a> or by ' +
          '<a href="mailto:' + C.email + "?subject=" + encodeURIComponent("viotours " + data.form) + "&body=" + encodeURIComponent(text) + '">email</a> — your details are already filled in.');
        done();
      };
      if (!C.enquiryEndpoint) return fallback();
      fetch(C.enquiryEndpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r; })
        .then(function () {
          status(form, true, form.getAttribute("data-ok") || "Thank you. A viotours planner will reply within one working day.");
          form.reset(); done();
        })
        .catch(fallback);
    });
  });

  /* ---------- footer year ---------- */
  $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
