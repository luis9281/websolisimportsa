/* Solis Import S.A. — comportamiento del sitio (sin dependencias) */
(function () {
  "use strict";

  /* Abrir el sitio haciendo doble clic en index.html (file://): los enlaces a carpetas apuntan a su index.html */
  if (location.protocol === "file:") {
    [].forEach.call(document.querySelectorAll("a[href]"), function (a) {
      var h = a.getAttribute("href");
      if (!h || /^([a-z]+:|#|\/\/)/i.test(h)) return;
      var m = h.match(/^([^?#]*)(.*)$/);
      if (m[1] === "" || m[1].slice(-1) === "/") a.setAttribute("href", m[1] + "index.html" + m[2]);
    });
  }

  /* Menú móvil */
  var menuBtn = document.querySelector(".menu-btn");
  var nav = document.querySelector(".nav");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* Diapositivas del inicio (manual, sin autoplay) */
  var slides = [].slice.call(document.querySelectorAll(".slide"));
  if (slides.length) {
    var dots = [].slice.call(document.querySelectorAll(".dot"));
    var current = 0;
    var show = function (i) {
      current = (i + slides.length) % slides.length;
      slides.forEach(function (s, n) { s.classList.toggle("is-active", n === current); });
      dots.forEach(function (d, n) { d.setAttribute("aria-current", n === current ? "true" : "false"); });
    };
    dots.forEach(function (d, n) { d.addEventListener("click", function () { show(n); }); });
    var prev = document.querySelector("[data-prev]");
    var next = document.querySelector("[data-next]");
    if (prev) prev.addEventListener("click", function () { show(current - 1); });
    if (next) next.addEventListener("click", function () { show(current + 1); });
    show(0);
  }

  /* Video de YouTube: se carga solo al hacer clic (mejor velocidad) */
  var video = document.querySelector(".video[data-yt]");
  if (video) {
    video.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + video.getAttribute("data-yt") + "?autoplay=1&rel=0";
      f.title = "Video institucional de Solis Import S.A.";
      f.allow = "autoplay; encrypted-media; picture-in-picture";
      f.allowFullscreen = true;
      video.innerHTML = "";
      video.appendChild(f);
    }, { once: true });
  }

  /* Catálogo: filtro por marca (multi-selección) + búsqueda */
  var finder = document.getElementById("finder");
  if (finder) {
    var tiles = [].slice.call(finder.querySelectorAll(".tile[data-brand]"));
    var cards = [].slice.call(document.querySelectorAll("#catalog [data-brand]"));
    var input = document.getElementById("q");
    var countEl = document.getElementById("count");
    var emptyEl = document.getElementById("empty");
    var clearBtns = [].slice.call(document.querySelectorAll("[data-clear]"));
    var selected = {};

    var norm = function (s) {
      return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    };

    var apply = function () {
      var keys = Object.keys(selected);
      var q = norm(input ? input.value : "");
      var shown = 0;
      cards.forEach(function (c) {
        var okBrand = !keys.length || selected[c.getAttribute("data-brand")];
        var okText = !q || norm(c.getAttribute("data-text")).indexOf(q) !== -1;
        var ok = okBrand && okText;
        c.hidden = !ok;
        if (ok) shown++;
      });
      tiles.forEach(function (t) {
        t.setAttribute("aria-pressed", selected[t.getAttribute("data-brand")] ? "true" : "false");
      });
      if (countEl) countEl.textContent = shown + (shown === 1 ? " resultado" : " resultados");
      if (emptyEl) emptyEl.hidden = shown !== 0;
      clearBtns.forEach(function (b) { b.hidden = !keys.length && !q; });
      /* Mantener la selección en la URL para poder compartirla */
      try {
        var p = new URLSearchParams();
        if (keys.length) p.set("marca", keys.join(","));
        if (q) p.set("q", input.value);
        var qs = p.toString();
        history.replaceState(null, "", location.pathname + (qs ? "?" + qs : ""));
      } catch (e) { /* sin historial disponible */ }
    };

    tiles.forEach(function (t) {
      t.addEventListener("click", function () {
        var b = t.getAttribute("data-brand");
        if (selected[b]) delete selected[b]; else selected[b] = true;
        apply();
      });
    });
    if (input) input.addEventListener("input", apply);
    clearBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        selected = {};
        if (input) input.value = "";
        apply();
      });
    });

    /* Leer ?marca=slug,slug&q=texto */
    try {
      var params = new URLSearchParams(location.search);
      (params.get("marca") || "").split(",").forEach(function (s) { if (s) selected[s] = true; });
      if (input && params.get("q")) input.value = params.get("q");
    } catch (e) { /* ignorar */ }
    apply();
  }

  /* Formulario de contacto: validación en el navegador + envío sin recargar */
  var form = document.getElementById("contact-form");
  if (form) {
    var errBox = document.getElementById("form-error");
    var okBox = document.getElementById("form-success");
    var msg = form.elements["mensaje"];
    var counter = document.getElementById("counter");
    var submitBtn = form.querySelector("button[type=submit]");
    var ready = false;

    var info = function (text) {
      if (!errBox) return;
      errBox.textContent = text; errBox.className = "banner info"; errBox.hidden = false;
    };
    fetch("token.php", { credentials: "same-origin", cache: "no-store", headers: { "X-Requested-With": "fetch" } })
      .then(function (r) { if (!r.ok) throw new Error("sin servidor"); return r.json(); })
      .then(function (d) {
        form.elements["csrf"].value = d.csrf;
        ready = true;
        if (d.turnstile) {
          var sc = document.createElement("script");
          sc.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
          sc.onload = function () { window.turnstile.render("#turnstile-box", { sitekey: d.turnstile }); };
          document.head.appendChild(sc);
        }
      })
      .catch(function () {
        info("Vista previa sin servidor PHP: puedes revisar el diseño, pero el envío solo funciona en el hosting.");
      });

    if (msg && counter) {
      var upd = function () { counter.textContent = msg.value.length + " / 1500"; };
      msg.addEventListener("input", upd); upd();
    }

    var setErr = function (name, text) {
      var p = form.querySelector('.err[data-for="' + name + '"]');
      if (!p) return;
      p.textContent = text || "";
      var field = p.closest(".field");
      if (field) field.classList.toggle("invalid", !!text);
    };
    var clearErrs = function () {
      [].forEach.call(form.querySelectorAll(".err"), function (p) { p.textContent = ""; });
      [].forEach.call(form.querySelectorAll(".invalid"), function (f) { f.classList.remove("invalid"); });
      if (errBox) errBox.hidden = true;
    };
    var validate = function () {
      var e = {};
      var v = function (n) { return (form.elements[n].value || "").trim(); };
      if (v("nombre").length < 2) e.nombre = "Escribe tu nombre.";
      if (v("empresa").length < 2) e.empresa = "Escribe el nombre de tu empresa o institución.";
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v("correo"))) e.correo = "Escribe un correo válido.";
      if (v("telefono") && !/^[0-9+()\-\s.]{6,25}$/.test(v("telefono"))) e.telefono = "Usa solo números, espacios, + o guiones.";
      if (v("mensaje").length < 10) e.mensaje = "Cuéntanos tu consulta (mínimo 10 caracteres).";
      if (!form.elements["acepto"].checked) e.acepto = "Debes aceptar el uso de tus datos para responderte.";
      return e;
    };
    var showErrors = function (e) {
      var first = null;
      Object.keys(e).forEach(function (k) { setErr(k, e[k]); if (!first) first = form.elements[k]; });
      if (first && first.focus) first.focus();
    };

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      clearErrs();
      var e = validate();
      if (Object.keys(e).length) { showErrors(e); return; }
      if (!ready) {
        info("El envío solo funciona en el hosting (requiere PHP). Mientras tanto, escríbenos por WhatsApp.");
        return;
      }

      submitBtn.classList.add("loading");
      submitBtn.setAttribute("aria-busy", "true");
      fetch(form.getAttribute("action"), {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: { "X-Requested-With": "fetch", "Accept": "application/json" }
      }).then(function (r) {
        return r.json().catch(function () { return { ok: false, message: "Respuesta inesperada del servidor." }; });
      }).then(function (d) {
        if (d.ok) {
          form.hidden = true;
          if (errBox) errBox.hidden = true;
          var sm = document.getElementById("success-msg");
          if (sm && d.message) sm.textContent = d.message;
          if (okBox) { okBox.hidden = false; okBox.scrollIntoView({ behavior: "smooth", block: "center" }); }
        } else {
          if (d.errors && Object.keys(d.errors).length) showErrors(d.errors);
          if (errBox) { errBox.textContent = d.message || "No se pudo enviar el mensaje."; errBox.className = "banner err"; errBox.hidden = false; }
          if (window.turnstile) { try { window.turnstile.reset(); } catch (x) { /* nada */ } }
        }
      }).catch(function () {
        if (errBox) { errBox.textContent = "No hay conexión con el servidor. Inténtalo de nuevo o escríbenos por WhatsApp."; errBox.hidden = false; }
      }).then(function () {
        submitBtn.classList.remove("loading");
        submitBtn.removeAttribute("aria-busy");
      });
    });
  }
})();
