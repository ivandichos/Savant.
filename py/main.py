import json
from pyscript import document, window, when
from pyscript.ffi import create_proxy
from js import Date

# ---------- Catalog (sample prices in pesos) ----------
# id, brand, name, scent family, notes, bottle color, price 50 ml, price 100 ml
PERFUMES = [
    ("sauvage", "Dior", "Sauvage", "spicy", "Bergamot, pepper and ambroxan. Fresh with a spicy edge.", "#3f6f9a", 6200, 8500),
    ("bleu", "Chanel", "Bleu de Chanel", "woody", "Citrus, incense and cedar. Smooth and classic.", "#2c4f8a", 6900, 9500),
    ("eros", "Versace", "Eros", "sweet", "Mint, green apple and vanilla. Loud and sweet.", "#2f8f9a", 4000, 5500),
    ("million", "Paco Rabanne", "1 Million", "sweet", "Blood orange, cinnamon and leather. Warm and showy.", "#c0902f", 3800, 5200),
    ("acqua", "Giorgio Armani", "Acqua di Giò", "fresh", "Sea notes, citrus and rosemary. Clean for daily wear.", "#5a9fb5", 4200, 5800),
    ("aventus", "Creed", "Aventus", "woody", "Pineapple, birch and musk. A smoky fruity classic.", "#6a6f78", 14500, 22000),
    ("ysl-y", "Yves Saint Laurent", "Y", "fresh", "Apple, ginger and cedar. Sharp and modern.", "#3a5a8a", 4600, 6300),
    ("lemale", "Jean Paul Gaultier", "Le Male", "aromatic", "Lavender, mint and vanilla. Cool and creamy.", "#4a5d9a", 4300, 6000),
    ("prada", "Prada", "L'Homme", "aromatic", "Neroli, iris and amber. Soft, powdery and tidy.", "#8a8f9a", 4500, 6200),
    ("oudwood", "Tom Ford", "Oud Wood", "woody", "Oud, rosewood and cardamom. Rich and dark.", "#6b4a2a", 13500, 19500),
    ("boss", "Hugo Boss", "Boss Bottled", "spicy", "Apple, cinnamon and sandalwood. Easy office pick.", "#a05a2f", 3200, 4300),
    ("wanted", "Azzaro", "Wanted", "spicy", "Lemon, ginger and cardamom. Warm and playful.", "#b0452f", 3300, 4500),
    ("coolwater", "Davidoff", "Cool Water", "fresh", "Mint, lavender and sea notes. A budget fresh classic.", "#4a8fb0", 2200, 2800),
    ("explorer", "Montblanc", "Explorer", "woody", "Bergamot, vetiver and patchouli. Earthy and calm.", "#3f5f4f", 3000, 3800),
    ("hero", "Burberry", "Hero", "aromatic", "Juniper, bergamot and cedar. Crisp and woody.", "#5f7f9a", 4100, 5600),
]
BY_ID = {p[0]: p for p in PERFUMES}
BEST = ["sauvage", "bleu", "eros", "million", "acqua", "aventus"]
NEW = ["oudwood", "hero", "prada", "lemale", "ysl-y", "explorer", "wanted", "boss"]
BUDGET_LIMIT = 6000
FREE_DELIVERY = 5000
DELIVERY_FEE = 150
KEY = "savant_cart"
USERS = "savant_users"
SESSION = "savant_user"
VIEWS = ("home", "shop", "product", "cart", "login", "checkout")
SECTIONS = {"brands": "brands", "best": "best-sec", "reviews": "reviews", "about": "about"}
METHODS = {"card": "Credit card", "paymongo": "PayMongo (GCash, Maya and more)", "cod": "Cash on delivery"}
state = {"family": "all", "q": "", "sort": "featured", "after": ""}
promo = {"on": False}
pstate = {"id": "", "size": "100", "qty": 1, "art": "full", "desc": False}

# ---------- Helpers ----------
def q(sel):
    return document.querySelector(sel)

def each(sel):
    nodes = document.querySelectorAll(sel)
    return [nodes.item(i) for i in range(nodes.length)]

def val(sel):
    return q(sel).value.strip()

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def digits(s):
    return "".join(c for c in s if c in "0123456789")

def peso(n):
    s = str(int(n))
    out = ""
    while len(s) > 3:
        out = "," + s[-3:] + out
        s = s[:-3]
    return "₱" + s + out

def price(pid, size):
    p = BY_ID[pid]
    return p[6] if size == "50" else p[7]

def was(n):
    return (n * 13 // 10 + 4) // 5 * 5

def reviews_of(pid):
    return (sum(ord(c) for c in pid) * 7) % 600 + 120

def go(name):
    window.location.hash = name

# Product pictures live in assets/products/
# Main picture (box + bottle): assets/products/<id>.png        e.g. sauvage.png
# Bottle-only picture:         assets/products/<id>-bottle.png e.g. sauvage-bottle.png
# Order tried: main .png, main .jpg, bottle .png, bottle .jpg, then assets/placeholder.svg
IMG_DIR = "assets/products/"
PLACEHOLDER = "assets/placeholder.svg"

def art(p, mode="full"):
    pid, brand, name = p[0], p[1], p[2]
    if mode == "full":
        tries = [pid + ".png", pid + ".jpg", pid + "-bottle.png", pid + "-bottle.jpg"]
    else:
        tries = [pid + "-bottle.png", pid + "-bottle.jpg", pid + ".png", pid + ".jpg"]
    tries = [IMG_DIR + t for t in tries]
    rest = json.dumps(tries[1:] + [PLACEHOLDER]).replace('"', "&quot;")
    return (
        '<img class="art" src="' + tries[0] + '" alt="' + esc(brand + " " + name) + '" loading="lazy" '
        'data-next="' + rest + '" '
        'onerror="var n=JSON.parse(this.dataset.next);if(n.length){this.src=n.shift();this.dataset.next=JSON.stringify(n)}else{this.onerror=null}">'
    )

def card_html(p):
    pid, brand, name, fam, notes, color, p50, p100 = p
    return (
        '<article class="card" data-id="' + pid + '" data-family="' + fam + '">'
        '<a class="thumb" href="#product/' + pid + '" aria-label="View ' + name + '">' + art(p) + "</a>"
        '<p class="brandname">' + brand + '</p><h3><a href="#product/' + pid + '">' + name + "</a></h3>"
        '<p class="notes">' + notes + "</p>"
        '<p class="rate"><span class="stars">★★★★★</span> <small>(' + str(reviews_of(pid)) + ")</small></p>"
        '<div class="buy"><select class="size" aria-label="Size"><option value="50">50 ml</option>'
        '<option value="100" selected>100 ml</option></select>'
        '<span><strong class="price">' + peso(p100) + '</strong> <s class="was">' + peso(was(p100)) + "</s></span></div>"
        '<button class="btn add">Add to cart</button></article>'
    )

def hide_toast():
    q("#toast").classList.remove("show")

hide_proxy = create_proxy(hide_toast)

def toast(msg):
    t = q("#toast")
    t.textContent = msg
    t.classList.add("show")
    window.setTimeout(hide_proxy, 2400)

# ---------- Browser storage ----------
def ls_get(key, default):
    try:
        raw = window.localStorage.getItem(key)
        return json.loads(raw) if raw else default
    except Exception:
        return default

def ls_set(key, value):
    try:
        window.localStorage.setItem(key, json.dumps(value))
    except Exception:
        pass

def cart_load():
    return ls_get(KEY, [])

def cart_save(items):
    ls_set(KEY, items)

def update_badge():
    q("#count").textContent = str(sum(i["qty"] for i in cart_load()))

def cart_add(pid, size, qty=1):
    items = cart_load()
    for item in items:
        if item["id"] == pid and item["size"] == size:
            item["qty"] += qty
            break
    else:
        items.append({"id": pid, "size": size, "qty": qty})
    cart_save(items)
    update_badge()

def bind_grid(grid):
    # Events are attached to the container (event delegation) because Python creates the cards.
    def on_click(event):
        btn = event.target
        if btn.classList.contains("add"):
            card = btn.closest(".card")
            pid = card.getAttribute("data-id")
            size = card.querySelector(".size").value
            cart_add(pid, size)
            toast("Added " + BY_ID[pid][1] + " " + BY_ID[pid][2] + " (" + size + " ml) to your cart.")

    def on_change(event):
        sel = event.target
        if sel.classList.contains("size"):
            card = sel.closest(".card")
            n = price(card.getAttribute("data-id"), sel.value)
            card.querySelector(".price").textContent = peso(n)
            card.querySelector(".was").textContent = peso(was(n))

    grid.addEventListener("click", create_proxy(on_click))
    grid.addEventListener("change", create_proxy(on_change))

# ---------- Login (front-end demo: accounts are kept in this browser only) ----------
def current_user():
    email = ls_get(SESSION, "")
    u = ls_get(USERS, {}).get(email) if email else None
    return {"email": email, "name": u["name"]} if u else None

def update_account():
    u = current_user()
    q("#acct").textContent = ("Hi, " + u["name"].split(" ")[0] + " · Log out") if u else "Login"

def go_after():
    dest = state["after"] or "home"
    state["after"] = ""
    go(dest)

@when("click", ".tab")
def pick_tab(event):
    which = event.target.getAttribute("data-tab")
    for t in each(".tab"):
        t.classList.toggle("on", t.getAttribute("data-tab") == which)
    q("#login-form").hidden = which != "login"
    q("#reg-form").hidden = which != "reg"
    q("#login-msg").textContent = ""

# Event: login form submit
@when("submit", "#login-form")
def do_login(event):
    event.preventDefault()
    email = val("#l-email").lower()
    u = ls_get(USERS, {}).get(email)
    if u and u["pw"] == q("#l-pw").value:
        ls_set(SESSION, email)
        update_account()
        q("#login-form").reset()
        go_after()
    else:
        q("#login-msg").textContent = "Wrong email or password. Create an account if you're new."

# Event: create account form submit
@when("submit", "#reg-form")
def do_register(event):
    event.preventDefault()
    name = val("#r-name")
    email = val("#r-email").lower()
    pw = q("#r-pw").value
    msg = q("#login-msg")
    users = ls_get(USERS, {})
    if not name:
        msg.textContent = "Enter your name."
    elif "@" not in email or "." not in email.split("@")[-1]:
        msg.textContent = "Enter a valid email address."
    elif len(pw) < 6:
        msg.textContent = "Password must be at least 6 characters."
    elif pw != q("#r-pw2").value:
        msg.textContent = "The two passwords don't match."
    elif email in users:
        msg.textContent = "That email already has an account. Try logging in."
    else:
        users[email] = {"name": name, "pw": pw}
        ls_set(USERS, users)
        ls_set(SESSION, email)
        update_account()
        q("#reg-form").reset()
        go_after()

# ---------- Routing: every page is a view inside this one file ----------
def show_route(event=None):
    name = window.location.hash.replace("#", "") or "home"
    if name == "login":
        # Logging in happens on its own page (login.html)
        nxt = "index.html%23checkout" if state["after"] == "checkout" else "index.html"
        window.location.href = "login.html?next=" + nxt
        return
    view = "home"
    if name.startswith("product/"):
        view = "product"
    elif name in ("shop", "cart", "login", "checkout"):
        view = name
    if view == "checkout":
        if not current_user():
            state["after"] = "checkout"
            go("login")
            return
        if not cart_load() and q("#co-done").hidden:
            go("cart")
            return
    for v in VIEWS:
        q("#view-" + v).hidden = v != view
    document.body.classList.toggle("co", view == "checkout")
    for a in each("a[data-nav]"):
        a.classList.toggle("on", a.getAttribute("data-nav") == view)
    if view == "home" and name in SECTIONS:
        q("#" + SECTIONS[name]).scrollIntoView()
    else:
        window.scrollTo(0, 0)
    if view == "product":
        render_product(name.split("/")[1])
    elif view == "cart":
        render_cart()
    elif view == "checkout":
        render_checkout()
    elif view == "login":
        q("#login-note").textContent = "Please log in or create an account to check out." if state["after"] == "checkout" else ""

# ---------- Home: product rows ----------
def fill(sel, ids):
    el = q(sel)
    el.innerHTML = "".join(card_html(BY_ID[i]) for i in ids)
    bind_grid(el)

fill("#best", BEST)
fill("#newin", NEW)
fill("#budget", [p[0] for p in PERFUMES if p[7] < BUDGET_LIMIT])

brands = sorted(set(p[1] for p in PERFUMES))
q("#brand-tiles").innerHTML = "".join(
    '<a class="tile" href="#shop" data-q="' + b + '">' + b + "</a>" for b in brands
)
cols = ""
for label, letters in (("A-E", "ABCDE"), ("F-J", "FGHIJ"), ("K-O", "KLMNO"), ("P-T", "PQRST"), ("U-Z", "UVWXYZ")):
    links = "".join('<a href="#shop" data-q="' + b + '">' + b + "</a>" for b in brands if b[0].upper() in letters)
    if links:
        cols += "<div><h4>" + label + "</h4>" + links + "</div>"
q("#mega-cols").innerHTML = cols
q("#co-logo").src = q("#main-logo").src

# Event: one click handler for the hamburger, brand menu, product rows, filter links and logout
def doc_click(event):
    t = event.target
    nav = q("#mainnav")
    menu = q("#menu")
    burger = q("#burger")
    btn = t.closest(".rbtn")
    if btn:
        track = btn.parentElement.querySelector(".track")
        track.scrollLeft += -480 if btn.classList.contains("prev") else 480
        return
    if t.closest("#acct") and current_user():
        event.preventDefault()
        ls_set(SESSION, "")
        update_account()
        toast("You're logged out.")
        go("home")
        return
    if t.closest("#burger"):
        # press the three lines to open the menu, press again to close it
        nav.classList.toggle("open")
        burger.classList.toggle("open", nav.classList.contains("open"))
        burger.setAttribute("aria-expanded", "true" if nav.classList.contains("open") else "false")
        menu.classList.remove("open")
        return
    if t.closest("#brands-btn"):
        menu.classList.toggle("open")
        return
    link = t.closest("a[data-family], a[data-q]")
    if link:
        state["family"] = link.getAttribute("data-family") or "all"
        state["q"] = link.getAttribute("data-q") or ""
        q("#search").value = state["q"]
        render_shop()
    if t.closest("#mainnav a") or not t.closest("#mainnav"):
        nav.classList.remove("open")
        burger.classList.remove("open")
        burger.setAttribute("aria-expanded", "false")
        menu.classList.remove("open")

document.addEventListener("click", create_proxy(doc_click))

# Event: header search form submit opens the shop with that search
@when("submit", "#hform")
def header_search(event):
    event.preventDefault()
    state["family"] = "all"
    state["q"] = val("#hsearch")
    q("#search").value = state["q"]
    render_shop()
    go("shop")

# Event: newsletter form submit with simple validation
@when("submit", "#news")
def subscribe(event):
    event.preventDefault()
    email = val("#email")
    msg = q("#news-msg")
    if "@" in email and "." in email.split("@")[-1]:
        msg.textContent = "Thanks. We'll send new arrivals and promos to " + email + "."
        q("#email").value = ""
    else:
        msg.textContent = "Enter a valid email address, like name@email.com."

# ---------- Shop ----------
grid = q("#grid")
bind_grid(grid)

def render_shop():
    term = state["q"].strip().lower()
    items = [p for p in PERFUMES
             if (state["family"] == "all" or p[3] == state["family"])
             and (term in p[1].lower() or term in p[2].lower())]
    if state["sort"] == "low":
        items = sorted(items, key=lambda p: p[7])
    elif state["sort"] == "high":
        items = sorted(items, key=lambda p: p[7], reverse=True)
    html = "".join(card_html(p) for p in items)
    grid.innerHTML = html or '<p class="empty">No perfume matches. Try another brand or scent family.</p>'
    q("#result-count").textContent = str(len(items)) + " of " + str(len(PERFUMES)) + " fragrances"
    for chip in each(".chip"):
        chip.classList.toggle("on", chip.getAttribute("data-filter") == state["family"])

@when("click", ".chip")
def pick_family(event):
    state["family"] = event.target.getAttribute("data-filter")
    render_shop()

@when("input", "#search")
def search(event):
    state["q"] = event.target.value
    render_shop()

@when("change", "#sort")
def sort(event):
    state["sort"] = event.target.value
    render_shop()

# ---------- Product page ----------
def render_product(pid):
    p = BY_ID.get(pid)
    box = q("#product-box")
    if not p:
        box.innerHTML = '<p class="empty">We could not find that perfume. <a href="#shop">Back to the shop</a>.</p>'
        return
    if pstate["id"] != pid:
        pstate["id"] = pid
        pstate["size"] = "100"
        pstate["qty"] = 1
        pstate["art"] = "full"
        pstate["desc"] = False
    size = pstate["size"]
    n = price(pid, size)
    opts = "".join('<option value="' + s + '"' + (" selected" if s == size else "") + ">" + s + " ml</option>" for s in ("50", "100"))
    desc = (
        p[2] + " by " + p[1] + " is a " + p[3] + " fragrance for men. " + p[4] +
        " It comes in 50 ml and 100 ml bottles. Every bottle is 100% authentic and sealed."
    )
    others = [x for x in PERFUMES if x[3] == p[3] and x[0] != pid][:4]
    if len(others) < 4:
        others += [x for x in PERFUMES if x[3] != p[3]][: 4 - len(others)]
    full_on = " on" if pstate["art"] == "full" else ""
    bottle_on = " on" if pstate["art"] == "bottle" else ""
    box.innerHTML = (
        '<div class="pgrid"><div><div class="pmain">' + art(p, pstate["art"]) + "</div>"
        '<div class="thumbs"><button class="pt' + full_on + '" data-act="thumb" data-v="full" aria-label="Box and bottle">' + art(p, "full") + "</button>"
        '<button class="pt' + bottle_on + '" data-act="thumb" data-v="bottle" aria-label="Bottle only">' + art(p, "bottle") + "</button></div></div>"
        '<div class="pinfo"><p class="rate"><span class="stars">★★★★★</span> <small>' + str(reviews_of(pid)) + " reviews</small></p>"
        '<p class="brandname">' + p[1] + '</p><h1 class="ptitle">' + p[1] + " " + p[2] + " " + size + "ml</h1>"
        '<p class="pprice"><strong class="price">' + peso(n) + '</strong> <s class="was">' + peso(was(n)) + "</s></p>"
        '<label for="psize">Size</label><select id="psize">' + opts + "</select>"
        '<div class="acc"><button class="accb" type="button" data-act="desc">Description <span>' + ("−" if pstate["desc"] else "+") + "</span></button>"
        '<div class="accp"' + ("" if pstate["desc"] else " hidden") + ">" + desc + "</div></div>"
        '<div class="qtybox"><button type="button" data-act="qminus" aria-label="Fewer">−</button><span>' + str(pstate["qty"]) + '</span><button type="button" data-act="qplus" aria-label="More">+</button></div>'
        '<p class="stock">In stock</p><button class="btn wide" type="button" data-act="addp">ADD TO CART</button>'
        '<div class="auth"><span>✔ 100% Authentic</span><span>★ Satisfaction guarantee</span></div></div></div>'
        '<h2 class="h2s">You may also like</h2><div class="grid" id="also">' + "".join(card_html(x) for x in others) + "</div>"
    )
    bind_grid(q("#also"))

# Event: clicks inside the product page (thumbnails, description, quantity, add to cart)
def pbox_click(event):
    b = event.target.closest("[data-act]")
    if not b:
        return
    act = b.getAttribute("data-act")
    if act == "thumb":
        pstate["art"] = b.getAttribute("data-v")
    elif act == "desc":
        pstate["desc"] = not pstate["desc"]
    elif act == "qplus":
        pstate["qty"] += 1
    elif act == "qminus":
        pstate["qty"] = max(1, pstate["qty"] - 1)
    elif act == "addp":
        cart_add(pstate["id"], pstate["size"], pstate["qty"])
        p = BY_ID[pstate["id"]]
        toast("Added " + str(pstate["qty"]) + " x " + p[1] + " " + p[2] + " (" + pstate["size"] + " ml) to your cart.")
        return
    render_product(pstate["id"])

def pbox_change(event):
    if event.target.id == "psize":
        pstate["size"] = event.target.value
        render_product(pstate["id"])

q("#product-box").addEventListener("click", create_proxy(pbox_click))
q("#product-box").addEventListener("change", create_proxy(pbox_change))

# ---------- Cart ----------
def totals(items):
    sub = sum(price(i["id"], i["size"]) * i["qty"] for i in items)
    disc = sub // 10 if promo["on"] else 0
    ship = 0 if (not items or sub - disc >= FREE_DELIVERY) else DELIVERY_FEE
    return sub, disc, ship, sub - disc + ship

def render_cart():
    items = cart_load()
    if not items:
        q("#cart-body").innerHTML = '<p class="empty center">Your cart is empty. <a href="#shop" data-family="all">Browse the shop</a>.</p>'
        q("#cart-foot").hidden = True
    else:
        rows = '<div class="chead"><span>Product</span><span>Quantity</span><span>Total</span></div>'
        for idx, i in enumerate(items):
            p = BY_ID[i["id"]]
            unit = price(i["id"], i["size"])
            k = str(idx)
            rows += (
                '<div class="crow"><div class="cprod"><a class="cthumb" href="#product/' + p[0] + '">' + art(p) + "</a>"
                '<div class="cinfo"><span class="brandname">' + p[1] + '</span><a href="#product/' + p[0] + '">' + p[2] + " " + i["size"] + 'ml</a><span class="unit">' + peso(unit) + "</span></div></div>"
                '<div class="cqty"><div class="qtybox"><button data-act="dec" data-i="' + k + '" aria-label="Fewer">−</button><span>' + str(i["qty"]) +
                '</span><button data-act="inc" data-i="' + k + '" aria-label="More">+</button></div>'
                '<button class="lnk" data-act="rm" data-i="' + k + '">Remove</button></div>'
                '<div class="ctotal">' + peso(unit * i["qty"]) + "</div></div>"
            )
        q("#cart-body").innerHTML = rows
        q("#cart-foot").hidden = False
        q("#cart-total").textContent = peso(totals(items)[0]) + " PHP"
    update_badge()

# Event: click on + , - or Remove in the cart (delegated, the buttons are created by Python)
def row_click(event):
    b = event.target.closest("[data-act]")
    if not b:
        return
    items = cart_load()
    idx = int(b.getAttribute("data-i"))
    act = b.getAttribute("data-act")
    if act == "inc":
        items[idx]["qty"] += 1
    elif act == "dec":
        items[idx]["qty"] -= 1
        if items[idx]["qty"] <= 0:
            items.pop(idx)
    else:
        items.pop(idx)
    cart_save(items)
    render_cart()

q("#cart-body").addEventListener("click", create_proxy(row_click))

# Event: click on Estimate shipping
@when("click", "#estimate")
def estimate(event):
    prov = q("#prov").value
    sub = totals(cart_load())[0]
    fee = "free" if sub >= FREE_DELIVERY else peso(DELIVERY_FEE)
    days = "3-7 days" if prov in ("Metro Manila", "Laguna", "Cavite", "Pampanga") else "4-10 days"
    q("#est-msg").textContent = "Standard delivery to " + prov + ": " + days + ", shipping fee " + fee + "."

# Event: click on Checkout. Customers must be logged in to buy.
@when("click", "#go-checkout")
def go_checkout(event):
    if not cart_load():
        toast("Your cart is empty.")
    elif current_user():
        go("checkout")
    else:
        state["after"] = "checkout"
        go("login")

# ---------- Checkout ----------
def render_checkout():
    items = cart_load()
    u = current_user()
    if u:
        if not val("#c-email"):
            q("#c-email").value = u["email"]
        if not val("#c-fn"):
            q("#c-fn").value = u["name"].split(" ")[0]
        q("#co-user").textContent = "Signed in as " + u["email"]
    if q("#co-done").hidden:
        q("#co-main").hidden = False
    html = ""
    for i in items:
        p = BY_ID[i["id"]]
        html += (
            '<div class="srow"><div class="sthumb">' + art(p) + '<span class="sbadge">' + str(i["qty"]) + "</span></div>"
            "<div><b>" + p[1] + " " + p[2] + "</b><small>" + i["size"] + " ml</small></div><span>" + peso(price(i["id"], i["size"]) * i["qty"]) + "</span></div>"
        )
    sub, disc, ship, total = totals(items)
    html += '<div class="sum"><span>Subtotal</span><span>' + peso(sub) + "</span></div>"
    if disc:
        html += '<div class="sum"><span>Discount (SAVANT10)</span><span>-' + peso(disc) + "</span></div>"
    html += '<div class="sum"><span>Shipping</span><span>' + ("Free" if ship == 0 else peso(ship)) + "</span></div>"
    q("#co-items").innerHTML = html
    q("#co-total-top").textContent = peso(total)
    q("#co-total").textContent = peso(total)
    q("#co-count").textContent = str(sum(i["qty"] for i in items)) + " items"
    update_ship_box()
    update_badge()

def update_ship_box():
    box = q("#ship-box")
    if val("#c-addr") and val("#c-city"):
        ship = totals(cart_load())[2]
        box.innerHTML = '<div class="shipopt"><span>Standard delivery<small>Metro areas 3-7 days, provinces 4-10 days</small></span><b>' + ("Free" if ship == 0 else peso(ship)) + "</b></div>"
    else:
        box.textContent = "Enter your shipping address to view available shipping methods."

# Event: typing the address shows the shipping method
@when("input", ".ship-in")
def ship_input(event):
    update_ship_box()

# Event: click on Order summary shows or hides the items
@when("click", "#sum-toggle")
def toggle_summary(event):
    box = q("#co-items")
    box.hidden = not box.hidden
    q("#sum-arrow").textContent = "▴" if not box.hidden else "▾"

# Event: choosing a payment method shows the card fields only for credit card
@when("change", "input[name=pay]")
def pick_payment(event):
    q("#card-fields").hidden = event.target.value != "card"

# Event: click on Add discount
@when("click", "#disc-btn")
def toggle_discount(event):
    box = q("#disc-row")
    box.hidden = not box.hidden

@when("click", "#apply")
def apply_promo(event):
    code = val("#promo").upper()
    promo["on"] = code == "SAVANT10"
    if promo["on"]:
        q("#promo-msg").textContent = "SAVANT10 applied: 10% off."
    else:
        q("#promo-msg").textContent = "That code isn't valid." if code else "Enter a promo code first."
    render_checkout()

def check_form():
    email = val("#c-email")
    if "@" not in email or "." not in email.split("@")[-1]:
        return "Enter a valid email address."
    for sel, label in (("#c-fn", "first name"), ("#c-ln", "last name"), ("#c-addr", "complete address"),
                       ("#c-brgy", "barangay"), ("#c-zip", "postal code"), ("#c-city", "city")):
        if not val(sel):
            return "Enter your " + label + "."
    if len(digits(val("#c-phone"))) < 7:
        return "Enter a valid phone number."
    if q("input[name=pay]:checked").value == "card":
        if len(digits(val("#c-card"))) < 13:
            return "Enter a valid card number."
        exp = val("#c-exp")
        if len(exp) != 5 or exp[2] != "/" or not digits(exp[:2] + exp[3:]) == exp[:2] + exp[3:]:
            return "Enter the expiration date as MM/YY."
        if len(digits(val("#c-cvc"))) < 3:
            return "Enter the security code."
        if not val("#c-cardname"):
            return "Enter the name on your card."
    return ""

# Event: Pay now (form submit). Nothing is charged, this is a class project demo.
@when("submit", "#pay-form")
def pay_now(event):
    event.preventDefault()
    items = cart_load()
    msg = q("#co-msg")
    if not items:
        msg.textContent = "Your cart is empty."
        return
    problem = check_form()
    if problem:
        msg.textContent = problem
        return
    msg.textContent = ""
    total = totals(items)[3]
    ref = "SAV-" + str(int(Date.now()) % 100000)
    lines = "".join("<li>" + str(i["qty"]) + " x " + BY_ID[i["id"]][1] + " " + BY_ID[i["id"]][2] + " (" + i["size"] + " ml)</li>" for i in items)
    who = esc(val("#c-fn") + " " + val("#c-ln"))
    where = esc(val("#c-addr") + ", " + val("#c-brgy") + ", " + val("#c-city") + " " + val("#c-zip") + ", " + q("#c-region").value)
    q("#co-done-body").innerHTML = (
        '<h2>Thank you, ' + esc(val("#c-fn")) + '.</h2><p class="lede">Your order <b>' + ref + "</b> is placed. We'll message you to confirm it.</p>"
        '<div class="panel"><ul class="dl">' + lines + "</ul>"
        '<p><b>Total:</b> ' + peso(total) + " (" + METHODS[q("input[name=pay]:checked").value] + ")</p>"
        "<p><b>Deliver to:</b> " + who + ", " + where + '</p></div><p style="margin-top:18px"><a class="btn" href="#shop" data-family="all">Continue shopping</a></p>'
    )
    cart_save([])
    promo["on"] = False
    q("#pay-form").reset()
    q("#card-fields").hidden = False
    q("#co-main").hidden = True
    q("#co-done").hidden = False
    q("#co-items").hidden = True
    update_badge()
    window.scrollTo(0, 0)

# ---------- Start ----------
window.addEventListener("hashchange", create_proxy(show_route))
update_account()
render_shop()
render_cart()
show_route()
