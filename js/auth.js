/* Savant login / sign up / forgot password
   Demo only: accounts are saved in this browser (localStorage), in the same
   format the shop uses, so a login here also logs you in on index.html. */
(function () {
  "use strict";

  var USERS = "savant_users";     // { "email": { name, pw } }
  var SESSION = "savant_user";    // "email" of the logged-in person
  var REMEMBER = "savant_remember_email";

  function read(key, fallback) {
    try { var raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback; }
    catch (e) { return fallback; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); return true; }
    catch (e) { return false; }
  }
  function $(sel) { return document.querySelector(sel); }
  function has(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }

  function emailOk(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }
  function passOk(v) { return v.length >= 8 && /[A-Za-z]/.test(v) && /\d/.test(v); }
  var PASS_RULE = "Use at least 8 characters with a letter and a number.";

  // Where to go after logging in (only pages of this site are allowed)
  function nextParam() {
    var n = new URLSearchParams(location.search).get("next") || "";
    return /^index\.html(#[a-z0-9\/-]*)?$/.test(n) ? n : "index.html";
  }
  function withNext(page, extra) {
    var q = new URLSearchParams(extra || {});
    var n = new URLSearchParams(location.search).get("next");
    if (n) q.set("next", n);
    var s = q.toString();
    return page + (s ? "?" + s : "");
  }

  // ----- field helpers -----
  function setErr(input, text) {
    var f = input.closest(".field");
    f.classList.add("invalid");
    f.querySelector(".err").textContent = text;
    input.setAttribute("aria-invalid", "true");
  }
  function clearAll(form) {
    var fields = form.querySelectorAll(".field");
    for (var i = 0; i < fields.length; i++) {
      fields[i].classList.remove("invalid");
      fields[i].querySelector(".err").textContent = "";
      var inp = fields[i].querySelector("input");
      if (inp) inp.removeAttribute("aria-invalid");
    }
    message("", "");
  }
  function message(text, kind) {
    var m = $("#form-msg");
    if (!m) return;
    m.textContent = text;
    m.className = "msg" + (kind ? " " + kind : "");
  }

  // Show / hide password buttons
  document.addEventListener("click", function (e) {
    var b = e.target.closest(".toggle");
    if (!b) return;
    var input = document.getElementById(b.getAttribute("data-target"));
    var show = input.type === "password";
    input.type = show ? "text" : "password";
    b.textContent = show ? "Hide" : "Show";
    b.setAttribute("aria-label", (show ? "Hide" : "Show") + " password");
  });

  // Product image fallback on the left side
  var art = $(".auth-art img");
  if (art) art.addEventListener("error", function () {
    if (art.getAttribute("src") !== "assets/placeholder.svg") art.src = "assets/placeholder.svg";
  });

  var page = document.body.getAttribute("data-page");

  // Already logged in? Skip the login and sign up pages.
  if ((page === "login" || page === "signup") && read(SESSION, "")) {
    var current = read(USERS, {})[read(SESSION, "")];
    if (current) location.replace(nextParam());
  }

  // =============== LOGIN ===============
  if (page === "login") {
    var lform = $("#login-form"), lemail = $("#email"), lpw = $("#password"), lrem = $("#remember");
    var qs = new URLSearchParams(location.search);
    if (qs.get("registered")) message("Account created! Log in to continue.", "success");
    if (qs.get("reset")) message("Password updated. Log in with your new password.", "success");

    var saved = read(REMEMBER, "");
    if (saved) { lemail.value = saved; lrem.checked = true; }

    lform.addEventListener("submit", function (e) {
      e.preventDefault();
      clearAll(lform);
      var email = lemail.value.trim().toLowerCase(), pw = lpw.value, ok = true;
      if (!emailOk(email)) { setErr(lemail, "Enter a valid email address."); ok = false; }
      if (!pw) { setErr(lpw, "Enter your password."); ok = false; }
      if (!ok) return;

      var users = read(USERS, {});
      if (!has(users, email) || users[email].pw !== pw) {
        message("Wrong email or password. If you're new, create an account.", "error");
        return;
      }
      write(SESSION, email);
      if (lrem.checked) write(REMEMBER, email);
      else try { localStorage.removeItem(REMEMBER); } catch (err) {}
      location.href = nextParam();
    });
  }

  // =============== SIGN UP ===============
  if (page === "signup") {
    var sform = $("#signup-form"), sname = $("#name"), semail = $("#email"),
        spw = $("#password"), spw2 = $("#confirm"), sterms = $("#terms"),
        bar = $("#meter-bar"), btxt = $("#meter-text");

    spw.addEventListener("input", function () {
      var v = spw.value, score = 0;
      if (v.length >= 8) score++;
      if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
      if (/\d/.test(v)) score++;
      if (/[^A-Za-z0-9]/.test(v)) score++;
      var labels = ["", "Weak", "Fair", "Good", "Strong"];
      var colors = ["#b3261e", "#b3261e", "#c98a1b", "#7a9a3a", "#2f6b3a"];
      bar.style.width = (v ? score * 25 : 0) + "%";
      bar.style.background = colors[score];
      btxt.textContent = v ? "Strength: " + labels[score || 1] : PASS_RULE;
    });

    sform.addEventListener("submit", function (e) {
      e.preventDefault();
      clearAll(sform);
      var name = sname.value.trim().replace(/\s+/g, " "),
          email = semail.value.trim().toLowerCase(),
          pw = spw.value, ok = true;
      if (name.length < 2) { setErr(sname, "Enter your full name."); ok = false; }
      if (!emailOk(email)) { setErr(semail, "Enter a valid email address."); ok = false; }
      if (!passOk(pw)) { setErr(spw, PASS_RULE); ok = false; }
      else if (pw !== spw2.value) { setErr(spw2, "The two passwords don't match."); ok = false; }
      if (!sterms.checked) { setErr(sterms, "Please agree to continue."); ok = false; }
      if (!ok) return;

      var users = read(USERS, {});
      if (has(users, email)) {
        setErr(semail, "That email already has an account. Try logging in.");
        return;
      }
      users[email] = { name: name, pw: pw };
      if (!write(USERS, users)) {
        message("Couldn't save your account. Check that your browser allows site storage.", "error");
        return;
      }
      location.href = withNext("login.html", { registered: "1" });
    });
  }

  // =============== FORGOT PASSWORD ===============
  if (page === "forgot") {
    var fform = $("#forgot-form"), rform = $("#reset-form"),
        femail = $("#email"), rpw = $("#password"), rpw2 = $("#confirm"),
        target = "";

    fform.addEventListener("submit", function (e) {
      e.preventDefault();
      clearAll(fform);
      var email = femail.value.trim().toLowerCase();
      if (!emailOk(email)) { setErr(femail, "Enter a valid email address."); return; }
      var users = read(USERS, {});
      if (!has(users, email)) {
        setErr(femail, "No account found with that email.");
        return;
      }
      target = email;
      fform.hidden = true;
      rform.hidden = false;
      $("#reset-for").textContent = email;
      rpw.focus();
    });

    rform.addEventListener("submit", function (e) {
      e.preventDefault();
      clearAll(rform);
      var pw = rpw.value, ok = true;
      if (!passOk(pw)) { setErr(rpw, PASS_RULE); ok = false; }
      else if (pw !== rpw2.value) { setErr(rpw2, "The two passwords don't match."); ok = false; }
      if (!ok) return;
      var users = read(USERS, {});
      if (!has(users, target)) { message("Something went wrong. Please start again.", "error"); return; }
      users[target].pw = pw;
      write(USERS, users);
      location.href = withNext("login.html", { reset: "1" });
    });
  }
})();
