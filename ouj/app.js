(function () {
  "use strict";
  var API = "https://vtsurdinopzycwsfzsuk.supabase.co/functions/v1/ouj-miniapp";
  var tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  try { tg && tg.ready(); tg && tg.expand(); tg && tg.setHeaderColor && tg.setHeaderColor("#0d0b08"); tg && tg.setBackgroundColor && tg.setBackgroundColor("#0d0b08"); } catch (e) {}
  var me = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) || null;

  var css = [
    ":root{--bg:#0d0b08;--card:#18140e;--line:#2c2418;--gold:#d8b46a;--gold2:#f1d79b;--txt:#f4ede0;--mut:#a89a82;--ok:#7fc48a;--bad:#e07a6a}",
    "*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}",
    "html,body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.45 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}",
    "#app{max-width:640px;margin:0 auto;padding:0 14px 110px}",
    ".hero{position:relative;margin:0 -14px 14px;height:190px;background:#000 center/cover no-repeat;display:flex;align-items:flex-end}",
    ".hero:after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(13,11,8,.1),rgba(13,11,8,.95))}",
    ".hero .in{position:relative;z-index:1;display:flex;gap:12px;align-items:center;padding:14px}",
    ".hero img{width:58px;height:58px;border-radius:14px;background:#000;object-fit:cover;border:1px solid var(--line)}",
    ".hero h1{margin:0;font-size:22px;letter-spacing:.5px;color:var(--gold2)}",
    ".hero p{margin:2px 0 0;color:var(--mut);font-size:13px}",
    ".item{display:flex;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:10px;margin-bottom:10px}",
    ".item.off{opacity:.5}",
    ".ph{width:96px;height:110px;flex:none;border-radius:12px;background:#222 center/cover no-repeat;display:flex;align-items:center;justify-content:center;color:var(--mut);font-size:12px}",
    ".item h3{margin:2px 0 4px;font-size:16px}",
    ".item .d{color:var(--mut);font-size:13px;margin:0 0 8px}",
    ".row{display:flex;align-items:center;justify-content:space-between;gap:8px}",
    ".price{color:var(--gold2);font-weight:600}",
    ".btn{border:0;border-radius:12px;padding:9px 14px;font:inherit;font-weight:600;background:var(--gold);color:#1a1307;cursor:pointer}",
    ".btn.sec{background:transparent;color:var(--gold);border:1px solid var(--gold)}",
    ".btn.del{background:transparent;color:var(--bad);border:1px solid var(--bad)}",
    ".btn:disabled{opacity:.45}",
    ".qty{display:flex;align-items:center;gap:10px}",
    ".qty b{min-width:18px;text-align:center}",
    ".qty .btn{padding:6px 12px}",
    ".bar{position:fixed;left:0;right:0;bottom:0;padding:12px 14px calc(12px + env(safe-area-inset-bottom));background:rgba(13,11,8,.96);border-top:1px solid var(--line)}",
    ".bar .btn{width:100%;max-width:612px;display:block;margin:0 auto;padding:14px;font-size:16px}",
    "h2{font-size:18px;margin:18px 0 10px;color:var(--gold2)}",
    "label{display:block;font-size:13px;color:var(--mut);margin:10px 0 4px}",
    "input,textarea,select{width:100%;padding:11px 12px;border-radius:12px;border:1px solid var(--line);background:var(--card);color:var(--txt);font:inherit}",
    "textarea{min-height:70px;resize:vertical}",
    ".seg{display:flex;gap:8px}.seg .btn{flex:1}",
    ".box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px;margin-bottom:10px}",
    ".mut{color:var(--mut);font-size:13px}",
    ".top{display:flex;justify-content:space-between;align-items:center;margin:12px 0}",
    ".link{background:none;border:0;color:var(--gold);font:inherit;padding:6px 0;cursor:pointer}",
    ".msg{padding:10px 12px;border-radius:12px;margin:10px 0;font-size:14px}.msg.ok{background:#1d2a1f;color:var(--ok)}.msg.bad{background:#2d1a17;color:var(--bad)}",
    ".tabs{display:flex;gap:6px;margin:8px 0 12px;overflow:auto}.tabs .btn{white-space:nowrap}",
    ".chk{display:flex;align-items:center;gap:10px;margin:10px 0}.chk input{width:auto}",
    ".ord{font-size:14px}.ord .st{font-size:12px;padding:2px 8px;border-radius:999px;border:1px solid var(--line)}",
    ".foot{color:var(--mut);font-size:12px;text-align:center;margin:20px 0}"
  ].join("");
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  var S = { items: [], shop: {}, hasPin: false, cart: {}, view: "menu", pin: "", adminTab: "items", edit: null, msg: null, orders: [] };
  var app = document.getElementById("app");
  function h(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function som(n) { return n == null ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " so'm"; }
  function isAdmin() { return !!(me && me.username && S.shop.admin_username && me.username.toLowerCase() === String(S.shop.admin_username).toLowerCase()); }
  function haptic() { try { tg && tg.HapticFeedback && tg.HapticFeedback.impactOccurred("light"); } catch (e) {} }

  function api(body) {
    return fetch(API, { method: body ? "POST" : "GET", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined })
      .then(function (r) { return r.json().then(function (d) { if (!r.ok || d.error) throw new Error(d.error || ("Xato " + r.status)); return d; }); });
  }
  function load() {
    return api().then(function (d) { S.items = d.items; S.shop = d.shop || {}; S.hasPin = d.has_pin; render(); })
      .catch(function (e) { app.innerHTML = '<div class="msg bad">Yuklab bo\'lmadi: ' + h(e.message) + '</div><button class="btn" id="rl">Qayta urinish</button>'; document.getElementById("rl").onclick = load; });
  }
  function cartLines() { return S.items.filter(function (i) { return S.cart[i.id] > 0; }).map(function (i) { return { item: i, qty: S.cart[i.id] }; }); }
  function cartCount() { return cartLines().reduce(function (s, l) { return s + l.qty; }, 0); }
  function cartSum() { var ls = cartLines(); if (!ls.length || ls.some(function (l) { return l.item.price == null; })) return null; return ls.reduce(function (s, l) { return s + l.item.price * l.qty; }, 0); }
  function msgHtml() { return S.msg ? '<div class="msg ' + (S.msg.ok ? "ok" : "bad") + '">' + h(S.msg.t) + "</div>" : ""; }
  function setMsg(t, ok) { S.msg = { t: t, ok: ok }; }

  function render() {
    if (tg && tg.BackButton) { try { S.view === "menu" ? tg.BackButton.hide() : tg.BackButton.show(); } catch (e) {} }
    if (S.view === "menu") return renderMenu();
    if (S.view === "cart") return renderCart();
    if (S.view === "done") return renderDone();
    if (S.view === "admin") return renderAdmin();
  }
  if (tg && tg.BackButton) tg.BackButton.onClick(function () { S.msg = null; if (S.view === "admin" && S.edit) { S.edit = null; } else { S.view = "menu"; } render(); });

  function renderMenu() {
    var sh = S.shop;
    var html = '<div class="hero" style="background-image:url(\'' + h(sh.cover_url || "") + '\')"><div class="in">' +
      (sh.logo_url ? '<img src="' + h(sh.logo_url) + '" alt="OUJ">' : "") +
      '<div><h1>' + h(sh.title || "OUJ Dessert") + '</h1><p>Uyda tayyorlangan desertlar · ' + h(sh.city || "Namangan") + '</p></div></div></div>';
    if (isAdmin()) html += '<div class="top"><span class="mut">Siz adminsiz</span><button class="btn sec" id="adm">✏️ Tahrirlash</button></div>';
    var list = S.items.filter(function (i) { return i.available || isAdmin(); });
    if (!list.length) html += '<div class="box mut">Menyu tez orada to\'ldiriladi.</div>';
    list.forEach(function (i) {
      var q = S.cart[i.id] || 0;
      html += '<div class="item' + (i.available ? "" : " off") + '"><div class="ph" style="' + (i.photo_url ? "background-image:url('" + h(i.photo_url) + "')" : "") + '">' + (i.photo_url ? "" : "Rasm yo'q") + '</div>' +
        '<div style="flex:1;min-width:0"><h3>' + h(i.name) + '</h3><p class="d">' + h(i.description) + '</p><div class="row">' +
        '<span class="price">' + (i.price != null ? som(i.price) + ' <span class="mut">/ ' + h(i.unit) + "</span>" : '<span class="mut">Narxini so\'rang</span>') + '</span>' +
        (!i.available ? '<span class="mut">Hozir yo\'q</span>' : q ? '<span class="qty"><button class="btn sec" data-m="' + i.id + '">−</button><b>' + q + '</b><button class="btn" data-p="' + i.id + '">+</button></span>' : '<button class="btn" data-p="' + i.id + '">Qo\'shish</button>') +
        "</div></div></div>";
    });
    html += '<p class="foot">Mahsulot rasmlari — haqiqiy desertlarimiz.</p>';
    var n = cartCount();
    if (n) html += '<div class="bar"><button class="btn" id="go">Savat: ' + n + ' ta' + (cartSum() != null ? " · " + som(cartSum()) : "") + "</button></div>";
    app.innerHTML = html;
    bindQty();
    var g = document.getElementById("go"); if (g) g.onclick = function () { S.view = "cart"; S.msg = null; render(); window.scrollTo(0, 0); };
    var a = document.getElementById("adm"); if (a) a.onclick = function () { S.view = "admin"; S.msg = null; render(); window.scrollTo(0, 0); };
  }
  function bindQty() {
    app.querySelectorAll("[data-p]").forEach(function (b) { b.onclick = function () { haptic(); S.cart[b.dataset.p] = (S.cart[b.dataset.p] || 0) + 1; render(); }; });
    app.querySelectorAll("[data-m]").forEach(function (b) { b.onclick = function () { haptic(); S.cart[b.dataset.m] = Math.max(0, (S.cart[b.dataset.m] || 0) - 1); render(); }; });
  }

  var form = { method: null, address: "", phone: "", note: "" };
  function renderCart() {
    var sh = S.shop, ls = cartLines();
    if (!ls.length) { S.view = "menu"; return render(); }
    if (!form.method) form.method = sh.delivery_enabled ? "delivery" : "pickup";
    var html = '<div class="top"><button class="link" id="bk">← Menyu</button></div><h2>Savat</h2><div class="box">';
    ls.forEach(function (l) {
      html += '<div class="row" style="margin:6px 0"><span>' + h(l.item.name) + '</span><span class="qty"><button class="btn sec" data-m="' + l.item.id + '">−</button><b>' + l.qty + '</b><button class="btn" data-p="' + l.item.id + '">+</button></span></div>';
    });
    var sum = cartSum(), dp = sh.delivery_price;
    var total = sum == null ? null : (form.method === "delivery" ? (dp == null ? null : sum + Number(dp)) : sum);
    html += '<div class="row" style="margin-top:10px;border-top:1px solid var(--line);padding-top:10px"><b>Jami</b><b class="price">' + (total != null ? som(total) : "Narx kelishiladi") + "</b></div></div>";
    html += "<h2>Qanday olasiz?</h2><div class=\"seg\">" +
      (sh.delivery_enabled ? '<button class="btn ' + (form.method === "delivery" ? "" : "sec") + '" id="md">🚗 Yetkazib berish</button>' : "") +
      (sh.pickup_enabled ? '<button class="btn ' + (form.method === "pickup" ? "" : "sec") + '" id="mp">🛍 Olib ketish</button>' : "") + "</div>";
    if (form.method === "delivery") html += '<p class="mut">' + h(sh.delivery_note || "") + (dp != null ? " · Yetkazish: " + som(dp) : "") + '</p><label>Manzil</label><textarea id="ad" placeholder="Ko\'cha, uy, mo\'ljal">' + h(form.address) + "</textarea>";
    else html += '<p class="mut">' + h(sh.pickup_note || "Olib ketish vaqti va joyini buyurtmadan keyin kelishamiz.") + "</p>";
    html += '<label>Telefon raqamingiz</label><input id="ph" type="tel" inputmode="tel" placeholder="+998 __ ___ __ __" value="' + h(form.phone) + '">' +
      '<label>Izoh (ixtiyoriy)</label><input id="nt" placeholder="Masalan: soat 18:00 ga" value="' + h(form.note) + '">' + msgHtml() +
      '<div class="bar"><button class="btn" id="send">Buyurtma berish</button></div>';
    app.innerHTML = html;
    bindQty();
    document.getElementById("bk").onclick = function () { S.view = "menu"; render(); };
    var md = document.getElementById("md"), mp = document.getElementById("mp");
    if (md) md.onclick = function () { save(); form.method = "delivery"; render(); };
    if (mp) mp.onclick = function () { save(); form.method = "pickup"; render(); };
    function save() { var a = document.getElementById("ad"); if (a) form.address = a.value; form.phone = document.getElementById("ph").value; form.note = document.getElementById("nt").value; }
    document.getElementById("send").onclick = function () {
      save();
      if (form.phone.replace(/\D/g, "").length < 9) { setMsg("Telefon raqamini to'liq yozing", false); return render(); }
      if (form.method === "delivery" && form.address.trim().length < 5) { setMsg("Manzilni yozing", false); return render(); }
      var btn = this; btn.disabled = true; btn.textContent = "Yuborilmoqda…";
      api({ action: "order", items: ls.map(function (l) { return { id: l.item.id, qty: l.qty }; }), method: form.method, address: form.address, phone: form.phone, note: form.note, tg_user: me })
        .then(function (d) { S.lastOrder = { id: d.id, total: d.total, lines: ls, form: JSON.parse(JSON.stringify(form)) }; S.cart = {}; S.view = "done"; S.msg = null; render(); })
        .catch(function (e) { setMsg(e.message, false); render(); });
    };
  }
  function orderText(o) {
    var t = "Assalomu alaykum! OUJ buyurtma #" + o.id + "\n";
    o.lines.forEach(function (l) { t += "• " + l.item.name + " × " + l.qty + "\n"; });
    t += (o.form.method === "delivery" ? "Yetkazib berish: " + o.form.address : "Olib ketaman") + "\n";
    t += "Tel: " + o.form.phone + (o.form.note ? "\nIzoh: " + o.form.note : "");
    if (o.total != null) t += "\nJami: " + som(o.total);
    return t;
  }
  function renderDone() {
    var o = S.lastOrder, u = S.shop.order_username || S.shop.admin_username || "OUJ_Dessert";
    app.innerHTML = '<h2>✅ Buyurtma #' + o.id + ' qabul qilindi</h2><div class="box"><p>Oxirgi qadam: buyurtmani bizga Telegram\'da yuboring, shunda tezroq bog\'lanamiz.</p>' +
      '<button class="btn" id="tgsend" style="width:100%">Telegram\'da yuborish</button></div><button class="link" id="bk">← Menyuga qaytish</button>';
    document.getElementById("tgsend").onclick = function () {
      var link = "https://t.me/" + encodeURIComponent(u) + "?text=" + encodeURIComponent(orderText(o));
      try { tg ? tg.openTelegramLink(link) : window.open(link, "_blank"); } catch (e) { window.open(link, "_blank"); }
    };
    document.getElementById("bk").onclick = function () { S.view = "menu"; render(); };
  }

  // ---------- admin ----------
  function resizeImage(file) {
    return new Promise(function (res, rej) {
      var r = new FileReader();
      r.onload = function () {
        var img = new Image();
        img.onload = function () {
          var m = 1080, w = img.width, hh = img.height, k = Math.min(1, m / Math.max(w, hh));
          var c = document.createElement("canvas"); c.width = Math.round(w * k); c.height = Math.round(hh * k);
          c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
          res(c.toDataURL("image/jpeg", 0.84));
        };
        img.onerror = function () { rej(new Error("Rasmni ochib bo'lmadi")); };
        img.src = r.result;
      };
      r.onerror = function () { rej(new Error("Faylni o'qib bo'lmadi")); };
      r.readAsDataURL(file);
    });
  }
  function renderAdmin() {
    if (!isAdmin()) { S.view = "menu"; return render(); }
    var html = '<div class="top"><button class="link" id="bk">← Menyu</button><span class="mut">@' + h(me.username) + "</span></div>";
    if (!S.hasPin) {
      html += '<h2>Admin PIN yarating</h2><div class="box"><p class="mut">4–8 xonali raqam o\'ylab toping. Tahrirlashda shu PIN so\'raladi. Uni hech kimga aytmang.</p><label>Yangi PIN</label><input id="p1" type="password" inputmode="numeric" maxlength="8"><label>PIN ni takrorlang</label><input id="p2" type="password" inputmode="numeric" maxlength="8">' + msgHtml() + '<button class="btn" id="sp" style="margin-top:12px;width:100%">Saqlash</button></div>';
      app.innerHTML = html; bindBack();
      document.getElementById("sp").onclick = function () {
        var a = document.getElementById("p1").value, b = document.getElementById("p2").value;
        if (!/^\d{4,8}$/.test(a)) { setMsg("PIN 4–8 ta raqam bo'lsin", false); return render(); }
        if (a !== b) { setMsg("PIN lar bir xil emas", false); return render(); }
        api({ action: "set_pin", pin: a, tg_user: me }).then(function () { S.hasPin = true; S.pin = a; setMsg("PIN saqlandi", true); render(); }).catch(function (e) { setMsg(e.message, false); render(); });
      };
      return;
    }
    if (!S.pin) {
      html += '<h2>Admin kirish</h2><div class="box"><label>PIN</label><input id="pi" type="password" inputmode="numeric" maxlength="8">' + msgHtml() + '<button class="btn" id="li" style="margin-top:12px;width:100%">Kirish</button></div>';
      app.innerHTML = html; bindBack();
      document.getElementById("li").onclick = function () {
        var p = document.getElementById("pi").value;
        api({ action: "login", pin: p }).then(function () { S.pin = p; S.msg = null; render(); }).catch(function (e) { setMsg(e.message, false); render(); });
      };
      return;
    }
    if (S.edit) return renderEdit(html);
    html += '<div class="tabs"><button class="btn ' + (S.adminTab === "items" ? "" : "sec") + '" data-t="items">Desertlar</button><button class="btn ' + (S.adminTab === "shop" ? "" : "sec") + '" data-t="shop">Yetkazish / olib ketish</button><button class="btn ' + (S.adminTab === "orders" ? "" : "sec") + '" data-t="orders">Buyurtmalar</button></div>' + msgHtml();
    if (S.adminTab === "items") {
      S.items.forEach(function (i) {
        html += '<div class="item' + (i.available ? "" : " off") + '"><div class="ph" style="' + (i.photo_url ? "background-image:url('" + h(i.photo_url) + "')" : "") + '">' + (i.photo_url ? "" : "Rasm yo'q") + '</div><div style="flex:1"><h3>' + h(i.name) + '</h3><p class="d">' + (i.price != null ? som(i.price) : "Narx kiritilmagan") + (i.available ? "" : " · Hozir yo'q") + '</p><button class="btn sec" data-e="' + i.id + '">Tahrirlash</button></div></div>';
      });
      html += '<button class="btn" id="add" style="width:100%">+ Yangi desert qo\'shish</button>';
    } else if (S.adminTab === "shop") {
      var s = S.shop;
      html += '<div class="box"><div class="chk"><input type="checkbox" id="de"' + (s.delivery_enabled ? " checked" : "") + '><b>Yetkazib berish bor</b></div><label>Yetkazish narxi (so\'m)</label><input id="dp" inputmode="numeric" value="' + h(s.delivery_price == null ? "" : s.delivery_price) + '" placeholder="Masalan: 15000"><label>Yetkazish haqida izoh</label><input id="dn" value="' + h(s.delivery_note) + '" placeholder="Masalan: Namangan shahri ichida, 10:00–21:00"></div>' +
        '<div class="box"><div class="chk"><input type="checkbox" id="pe"' + (s.pickup_enabled ? " checked" : "") + '><b>Olib ketish bor</b></div><label>Olib ketish haqida izoh</label><input id="pn" value="' + h(s.pickup_note) + '" placeholder="Masalan: mo\'ljal va vaqt"></div>' +
        '<div class="box"><label>Buyurtmalar keladigan Telegram (@username)</label><input id="ou" value="' + h(s.order_username) + '"><label>Muqova rasmi (ixtiyoriy)</label><input id="cv" type="file" accept="image/*"></div>' +
        '<button class="btn" id="ss" style="width:100%">Saqlash</button><div class="box" style="margin-top:16px"><label>PIN ni almashtirish</label><input id="np" type="password" inputmode="numeric" maxlength="8" placeholder="Yangi PIN"><button class="btn sec" id="cp" style="margin-top:8px">Almashtirish</button></div>';
    } else {
      html += '<div id="ol" class="mut">Yuklanmoqda…</div>';
    }
    app.innerHTML = html; bindBack();
    app.querySelectorAll("[data-t]").forEach(function (b) { b.onclick = function () { S.adminTab = b.dataset.t; S.msg = null; render(); }; });
    app.querySelectorAll("[data-e]").forEach(function (b) { b.onclick = function () { S.edit = JSON.parse(JSON.stringify(S.items.find(function (x) { return x.id === b.dataset.e; }))); S.msg = null; render(); window.scrollTo(0, 0); }; });
    var add = document.getElementById("add"); if (add) add.onclick = function () { S.edit = { name: "", description: "", price: null, unit: "dona", available: true, sort: (S.items.length + 1) * 10 }; S.msg = null; render(); };
    var ss = document.getElementById("ss");
    if (ss) ss.onclick = function () {
      ss.disabled = true; ss.textContent = "Saqlanmoqda…";
      var f = document.getElementById("cv").files[0];
      (f ? resizeImage(f) : Promise.resolve(null)).then(function (cover) {
        return api({ action: "save_shop", pin: S.pin, shop: { delivery_enabled: document.getElementById("de").checked, delivery_price: document.getElementById("dp").value, delivery_note: document.getElementById("dn").value, pickup_enabled: document.getElementById("pe").checked, pickup_note: document.getElementById("pn").value, order_username: document.getElementById("ou").value, cover_data: cover } });
      }).then(function () { setMsg("Saqlandi ✅", true); return load(); }).catch(function (e) { setMsg(e.message, false); render(); });
    };
    var cp = document.getElementById("cp");
    if (cp) cp.onclick = function () {
      var np = document.getElementById("np").value;
      api({ action: "change_pin", pin: S.pin, new_pin: np }).then(function () { S.pin = np; setMsg("PIN almashtirildi", true); render(); }).catch(function (e) { setMsg(e.message, false); render(); });
    };
    if (S.adminTab === "orders") loadOrders();
  }
  function loadOrders() {
    api({ action: "orders", pin: S.pin }).then(function (d) {
      var el = document.getElementById("ol"); if (!el) return;
      if (!d.orders.length) { el.textContent = "Hali buyurtma yo'q."; return; }
      var names = { new: "Yangi", accepted: "Qabul qilindi", done: "Bajarildi", cancelled: "Bekor" };
      el.className = ""; el.innerHTML = d.orders.map(function (o) {
        var dt = new Date(o.created_at);
        return '<div class="box ord"><div class="row"><b>#' + o.id + "</b><span class=\"st\">" + names[o.status] + '</span></div><div class="mut">' + dt.toLocaleString("ru-RU", { timeZone: "Asia/Tashkent" }) + "</div>" +
          o.items.map(function (l) { return "• " + h(l.name) + " × " + l.qty; }).join("<br>") +
          "<br>" + (o.method === "delivery" ? "🚗 " + h(o.address) : "🛍 Olib ketadi") + "<br>📞 " + h(o.phone) + (o.note ? "<br>💬 " + h(o.note) : "") +
          (o.tg_user && o.tg_user.username ? '<br>Telegram: @' + h(o.tg_user.username) : "") + (o.total != null ? "<br><b>" + som(o.total) + "</b>" : "") +
          '<div class="seg" style="margin-top:8px"><button class="btn sec" data-s="accepted" data-o="' + o.id + '">Qabul</button><button class="btn sec" data-s="done" data-o="' + o.id + '">Bajarildi</button><button class="btn del" data-s="cancelled" data-o="' + o.id + '">Bekor</button></div></div>';
      }).join("");
      el.querySelectorAll("[data-o]").forEach(function (b) { b.onclick = function () { api({ action: "order_status", pin: S.pin, id: b.dataset.o, status: b.dataset.s }).then(loadOrders); }; });
    }).catch(function (e) { var el = document.getElementById("ol"); if (el) el.textContent = e.message; });
  }
  function renderEdit(html) {
    var e = S.edit;
    html += "<h2>" + (e.id ? "Desertni tahrirlash" : "Yangi desert") + '</h2><div class="box">' +
      '<div class="ph" id="pv" style="width:100%;height:220px;' + (e.photo_url ? "background-image:url('" + h(e.photo_url) + "')" : "") + '">' + (e.photo_url ? "" : "Rasm yo'q") + "</div>" +
      '<label>Rasm (telefondan tanlang)</label><input id="ef" type="file" accept="image/*">' +
      '<label>Nomi</label><input id="en" value="' + h(e.name) + '"><label>Tavsif</label><textarea id="ed">' + h(e.description) + "</textarea>" +
      '<div class="seg"><div style="flex:2"><label>Narxi (so\'m)</label><input id="ep" inputmode="numeric" value="' + h(e.price == null ? "" : e.price) + '" placeholder="Masalan: 25000"></div><div style="flex:1"><label>Birlik</label><input id="eu" value="' + h(e.unit) + '"></div></div>' +
      '<div class="chk"><input type="checkbox" id="ea"' + (e.available ? " checked" : "") + '><b>Sotuvda bor</b></div><label>Tartib raqami (kichigi tepada)</label><input id="es" inputmode="numeric" value="' + h(e.sort) + '"></div>' + msgHtml() +
      '<button class="btn" id="sv" style="width:100%">Saqlash</button>' + (e.id ? '<button class="btn del" id="dl" style="width:100%;margin-top:10px">O\'chirish</button>' : "") +
      '<button class="link" id="cn" style="margin-top:8px">Bekor qilish</button>';
    app.innerHTML = html; bindBack();
    var photo = null;
    document.getElementById("ef").onchange = function () {
      var f = this.files[0]; if (!f) return;
      resizeImage(f).then(function (d) { photo = d; var pv = document.getElementById("pv"); pv.style.backgroundImage = "url('" + d + "')"; pv.textContent = ""; }).catch(function (er) { setMsg(er.message, false); render(); });
    };
    document.getElementById("cn").onclick = function () { S.edit = null; S.msg = null; render(); };
    document.getElementById("sv").onclick = function () {
      var b = this; b.disabled = true; b.textContent = "Saqlanmoqda…";
      var item = { id: e.id, name: document.getElementById("en").value, description: document.getElementById("ed").value, price: document.getElementById("ep").value, unit: document.getElementById("eu").value, available: document.getElementById("ea").checked, sort: document.getElementById("es").value, photo_data: photo };
      api({ action: "save_item", pin: S.pin, item: item }).then(function () { S.edit = null; setMsg("Saqlandi ✅", true); return load(); }).catch(function (er) { setMsg(er.message, false); render(); });
    };
    var dl = document.getElementById("dl");
    if (dl) dl.onclick = function () {
      var go = function () { api({ action: "delete_item", pin: S.pin, id: e.id }).then(function () { S.edit = null; setMsg("O'chirildi", true); return load(); }).catch(function (er) { setMsg(er.message, false); render(); }); };
      if (tg && tg.showConfirm) tg.showConfirm("Rostdan o'chirilsinmi?", function (ok) { if (ok) go(); }); else if (confirm("Rostdan o'chirilsinmi?")) go();
    };
  }
  function bindBack() { var b = document.getElementById("bk"); if (b) b.onclick = function () { S.view = "menu"; S.edit = null; S.msg = null; render(); }; }

  load();
})();
