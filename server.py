# -*- coding: utf-8 -*-
"""
Taller — Inventario (versión editorial)
Servidor Flask con vista pública del trabajador rediseñada con un lenguaje
editorial minimalista: paleta Papel & grafito, tipografía serif Playfair + Inter,
sombras suaves multicapa, micro-animaciones y textura de grano sutil.
"""

from flask import Flask, request, render_template_string, jsonify, send_file
import database as db
from notifications import send_whatsapp
from config import SERVER_HOST, SERVER_PORT, ADMIN_KEY
import qrcode, io

app = Flask(__name__)
db.init_db()


def check_admin(req):
    return req.headers.get("X-Admin-Key") == ADMIN_KEY and ADMIN_KEY != ""


# ── API ADMIN ────────────────────────────────────────────────────────────────

@app.route("/api/items", methods=["GET", "POST"])
def api_items():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    if request.method == "GET":
        return jsonify([dict(i) for i in db.get_items()])
    data = request.get_json()
    db.add_item(data["name"], data["category"], float(data["quantity"]),
                data["unit"], data.get("location", ""), float(data.get("min_stock", 0)))
    return jsonify({"ok": True})


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id):
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    db.delete_item(item_id)
    return jsonify({"ok": True})


@app.route("/api/movements", methods=["GET"])
def api_movements():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    return jsonify([dict(m) for m in db.get_movements()])


@app.route("/api/movements/latest", methods=["GET"])
def api_latest():
    """Devuelve los movimientos más nuevos que el id pasado como ?since=X — para polling en la app."""
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    since = int(request.args.get("since", 0))
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT m.*, i.name as item_name, i.unit as unit
           FROM movements m JOIN items i ON m.item_id = i.id
           WHERE m.id > ? ORDER BY m.id ASC""", (since,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/workers", methods=["GET", "POST", "DELETE"])
def api_workers():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    if request.method == "GET":
        return jsonify(db.get_workers())
    if request.method == "POST":
        data = request.get_json()
        db.add_worker(data["name"])
        return jsonify({"ok": True})
    if request.method == "DELETE":
        data = request.get_json()
        db.delete_worker(data["name"])
        return jsonify({"ok": True})


@app.route("/api/notifications", methods=["GET"])
def api_notifications():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    return jsonify([dict(n) for n in db.get_unsent_notifications()])


@app.route("/api/notifications/retry", methods=["POST"])
def api_retry_notifications():
    if not check_admin(request):
        return jsonify({"error": "no autorizado"}), 401
    pending = db.get_unsent_notifications()
    sent = 0
    for n in pending:
        ok, _ = send_whatsapp(n["message"])
        if ok:
            db.mark_notification_sent(n["id"])
            sent += 1
    return jsonify({"sent": sent, "total": len(pending)})


@app.route("/qr")
def qr_general():
    base_url = request.url_root.rstrip("/")
    img = qrcode.make(base_url + "/")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ── VISTA TRABAJADORES (EDITORIAL) ──────────────────────────────────────────

WORKER_HTML = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#FAFAF7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E0E0E" media="(prefers-color-scheme: dark)">
<title>Taller — Registro</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,400;1,9..144,500&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --paper:        #FAFAF7;
    --paper-warm:   #F4F1EA;
    --paper-deep:   #EFEBE2;
    --ink:          #2C2C2C;
    --ink-soft:     #4A4A48;
    --ink-mute:     #8A8A86;
    --ink-faint:    #B8B6AE;
    --ink-blue:     #1E3A5F;
    --ink-blue-2:   #2A4F7C;
    --oxblood:      #8C2F2F;
    --oxblood-deep: #6E2424;
    --moss:         #3F5B3A;
    --hairline:     rgba(44, 44, 44, 0.14);
    --hairline-2:   rgba(44, 44, 44, 0.08);
    --hairline-3:   rgba(44, 44, 44, 0.04);
    --on-ink:       #FAFAF7;
    --on-accent:    #FAFAF7;
    --shadow-paper:
      0 1px 1px rgba(44, 44, 44, 0.02),
      0 2px 4px rgba(44, 44, 44, 0.03),
      0 8px 16px rgba(44, 44, 44, 0.04),
      0 24px 48px rgba(44, 44, 44, 0.06);
    --shadow-elevated:
      0 1px 2px rgba(44, 44, 44, 0.03),
      0 4px 8px rgba(44, 44, 44, 0.05),
      0 16px 32px rgba(44, 44, 44, 0.08),
      0 40px 80px rgba(44, 44, 44, 0.10);
    --shadow-button:
      0 1px 2px rgba(44, 44, 44, 0.04),
      0 4px 12px rgba(44, 44, 44, 0.06);
    --grain-opacity: 0.035;
    --grain-blend: multiply;
  }

  html[data-theme="dark"] {
    --paper:        #0E0E0E;
    --paper-warm:   #1A1A1A;
    --paper-deep:   #242424;
    --ink:          #EDEAE3;
    --ink-soft:     #C8C5BE;
    --ink-mute:     #7A7A75;
    --ink-faint:    #4A4A48;
    --ink-blue:     #C9A961;
    --ink-blue-2:   #B5954A;
    --oxblood:      #D65555;
    --oxblood-deep: #B33838;
    --moss:         #7AAB6F;
    --hairline:     rgba(237, 234, 227, 0.14);
    --hairline-2:   rgba(237, 234, 227, 0.08);
    --hairline-3:   rgba(237, 234, 227, 0.04);
    --on-ink:       #0E0E0E;
    --on-accent:    #0E0E0E;
    --shadow-paper:
      0 1px 1px rgba(0, 0, 0, 0.20),
      0 2px 4px rgba(0, 0, 0, 0.25),
      0 8px 16px rgba(0, 0, 0, 0.30),
      0 24px 48px rgba(0, 0, 0, 0.40);
    --shadow-elevated:
      0 1px 2px rgba(0, 0, 0, 0.30),
      0 4px 8px rgba(0, 0, 0, 0.40),
      0 16px 32px rgba(0, 0, 0, 0.50),
      0 40px 80px rgba(0, 0, 0, 0.60);
    --shadow-button:
      0 1px 2px rgba(0, 0, 0, 0.30),
      0 4px 12px rgba(0, 0, 0, 0.40);
    --grain-opacity: 0.06;
    --grain-blend: screen;
  }

  html, body { background: var(--paper); }

  body {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--ink);
    min-height: 100vh;
    min-height: 100dvh;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    line-height: 1.5;
    font-size: 15px;
    letter-spacing: 0.005em;
    padding: 32px 20px 64px;
    position: relative;
    overflow-x: hidden;
    transition: background-color 0.5s cubic-bezier(0.22, 0.61, 0.36, 1),
                color 0.5s cubic-bezier(0.22, 0.61, 0.36, 1);
  }

  body::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 9999;
    opacity: var(--grain-opacity);
    mix-blend-mode: var(--grain-blend);
    background-image: url("data:image/svg+xml;utf8,<svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
    background-size: 220px 220px;
  }

  body::after {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 280px;
    pointer-events: none;
    z-index: 0;
    background: radial-gradient(ellipse at top, rgba(44, 44, 44, 0.05), transparent 70%);
  }
  html[data-theme="dark"] body::after {
    background: radial-gradient(ellipse at top, rgba(201, 169, 97, 0.04), transparent 70%);
  }

  .stage {
    max-width: 560px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }

  /* ── Masthead ────────────────────────────────────────── */
  .masthead {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--ink);
    margin-bottom: 4px;
  }
  .masthead-left { display: flex; flex-direction: column; gap: 4px; }
  .eyebrow {
    font-family: "JetBrains Mono", "SF Mono", Menlo, monospace;
    font-size: 10px;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 600;
  }
  .brand {
    font-family: "Fraunces", "Playfair Display", Georgia, serif;
    font-weight: 500;
    font-size: 28px;
    letter-spacing: -0.015em;
    color: var(--ink);
    line-height: 1;
  }
  .brand em {
    font-style: italic;
    font-weight: 400;
    color: var(--ink-blue);
  }
  .masthead-right {
    text-align: right;
    display: flex;
    flex-direction: column;
    gap: 6px;
    align-items: flex-end;
  }
  .vol {
    font-family: "JetBrains Mono", "SF Mono", Menlo, monospace;
    font-size: 10px;
    letter-spacing: 0.22em;
    color: var(--ink-mute);
    text-transform: uppercase;
    font-weight: 600;
  }
  .theme-toggle {
    background: transparent;
    border: 1px solid var(--hairline);
    color: var(--ink);
    padding: 6px 12px;
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 1.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s var(--ease, cubic-bezier(0.22, 0.61, 0.36, 1));
  }
  .theme-toggle:hover {
    background: var(--paper-warm);
    border-color: var(--ink);
  }
  .date {
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 13px;
    color: var(--ink-soft);
  }

  /* ── Tagline ─────────────────────────────────────────── */
  .tagline {
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-weight: 400;
    font-size: 17px;
    color: var(--ink-soft);
    line-height: 1.4;
    padding: 18px 0 28px;
    max-width: 460px;
  }

  /* ── Índice de pasos ─────────────────────────────────── */
  .index {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0;
    margin-bottom: 28px;
    border-top: 1px solid var(--hairline);
    border-bottom: 1px solid var(--hairline);
  }
  .index-row {
    display: grid;
    grid-template-columns: 64px 1fr auto;
    align-items: center;
    gap: 18px;
    padding: 16px 0;
    border-bottom: 1px solid var(--hairline-2);
    transition: opacity 0.5s var(--ease, cubic-bezier(0.22, 0.61, 0.36, 1)),
                color 0.4s var(--ease, cubic-bezier(0.22, 0.61, 0.36, 1));
    color: var(--ink-faint);
  }
  .index-row:last-child { border-bottom: none; }
  .index-row.active { color: var(--ink); }
  .index-row.done { color: var(--ink-mute); }
  .index-num {
    font-family: "Fraunces", Georgia, serif;
    font-weight: 400;
    font-size: 36px;
    line-height: 1;
    letter-spacing: -0.02em;
    color: var(--ink-faint);
    transition: color 0.4s var(--ease, cubic-bezier(0.22, 0.61, 0.36, 1));
  }
  .index-row.active .index-num {
    color: var(--ink-blue);
    font-style: italic;
  }
  .index-row.done .index-num { color: var(--ink-blue); }
  .index-label {
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 600;
  }
  .index-row.active .index-label { color: var(--ink); }
  .index-desc {
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 14px;
    color: var(--ink-mute);
    margin-top: 2px;
  }
  .index-marker {
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.18em;
    color: var(--ink-faint);
    text-transform: uppercase;
  }
  .index-row.active .index-marker {
    color: var(--ink-blue);
    font-weight: 600;
  }
  .index-row.active .index-marker::before {
    content: "→ ";
    color: var(--ink-blue);
  }

  /* ── Sheet ───────────────────────────────────────────── */
  .sheet {
    background: var(--paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 40px 36px 36px;
    box-shadow: var(--shadow-paper);
    position: relative;
    transition: box-shadow 0.5s var(--ease, cubic-bezier(0.22, 0.61, 0.36, 1));
  }
  .sheet::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    pointer-events: none;
    background: linear-gradient(180deg, rgba(255,255,255,0.6), transparent 12%);
  }
  html[data-theme="dark"] .sheet::before {
    background: linear-gradient(180deg, rgba(255,255,255,0.03), transparent 12%);
  }
  .sheet > * { position: relative; z-index: 1; }

  .sheet-corner {
    position: absolute;
    top: 16px;
    right: 24px;
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 96px;
    line-height: 1;
    color: var(--hairline-3);
    pointer-events: none;
    user-select: none;
    font-weight: 300;
    z-index: 0;
  }
  .sheet.corner-1 .sheet-corner::before { content: "01"; }
  .sheet.corner-2 .sheet-corner::before { content: "02"; }
  .sheet.corner-3 .sheet-corner::before { content: "03"; }

  /* ── Step blocks ─────────────────────────────────────── */
  .step-block { animation: fadeUp 0.55s cubic-bezier(0.22, 0.61, 0.36, 1) both; }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .hidden { display: none !important; }

  .step-title {
    font-family: "Fraunces", Georgia, serif;
    font-weight: 500;
    font-size: 26px;
    line-height: 1.2;
    letter-spacing: -0.015em;
    color: var(--ink);
    margin-bottom: 6px;
  }
  .step-title em {
    font-style: italic;
    font-weight: 400;
    color: var(--ink-blue);
  }
  .step-sub {
    font-family: "Inter", sans-serif;
    font-size: 13px;
    color: var(--ink-mute);
    margin-bottom: 28px;
    letter-spacing: 0.01em;
  }

  /* ── Worker grid ─────────────────────────────────────── */
  .worker-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  .worker-btn {
    padding: 20px 16px;
    background: var(--paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    font-family: "Fraunces", Georgia, serif;
    font-size: 18px;
    font-weight: 400;
    color: var(--ink);
    cursor: pointer;
    text-align: center;
    transition: all 0.35s cubic-bezier(0.22, 0.61, 0.36, 1);
    letter-spacing: -0.005em;
    position: relative;
    overflow: hidden;
  }
  .worker-btn::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--ink);
    transform: scaleY(0);
    transform-origin: bottom;
    transition: transform 0.4s cubic-bezier(0.22, 0.61, 0.36, 1);
    z-index: 0;
  }
  .worker-btn span { position: relative; z-index: 1; }
  .worker-btn:hover {
    border-color: var(--ink-blue);
    color: var(--ink-blue);
    transform: translateY(-2px);
    box-shadow: var(--shadow-button);
  }
  .worker-btn:active { transform: translateY(0); }

  /* ── Search ──────────────────────────────────────────── */
  .search-wrap {
    position: relative;
    margin-bottom: 18px;
  }
  .search-icon {
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 20px;
    color: var(--ink-mute);
    pointer-events: none;
  }
  .search-box {
    width: 100%;
    padding: 16px 0 16px 32px;
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--ink);
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 18px;
    color: var(--ink);
    transition: border-color 0.3s cubic-bezier(0.22, 0.61, 0.36, 1);
  }
  .search-box::placeholder { color: var(--ink-faint); }
  .search-box:focus {
    outline: none;
    border-bottom-color: var(--ink-blue);
  }

  /* ── Item list ───────────────────────────────────────── */
  .item-grid {
    display: flex;
    flex-direction: column;
    gap: 0;
    max-height: 380px;
    overflow-y: auto;
    margin: 0 -8px;
    padding: 0 8px;
  }
  .item-grid::-webkit-scrollbar { width: 4px; }
  .item-grid::-webkit-scrollbar-track { background: transparent; }
  .item-grid::-webkit-scrollbar-thumb { background: var(--hairline); border-radius: 2px; }

  .item-btn {
    padding: 20px 4px;
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--hairline-2);
    cursor: pointer;
    text-align: left;
    transition: all 0.3s cubic-bezier(0.22, 0.61, 0.36, 1);
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
    align-items: baseline;
    width: 100%;
    color: inherit;
    font-family: inherit;
  }
  .item-btn:last-child { border-bottom: none; }
  .item-btn:hover {
    padding-left: 12px;
    background: linear-gradient(90deg, var(--hairline-3), transparent 80%);
  }
  .item-btn:hover .item-name { color: var(--ink-blue); }
  .item-name {
    font-family: "Fraunces", Georgia, serif;
    font-size: 19px;
    font-weight: 500;
    color: var(--ink);
    line-height: 1.25;
    letter-spacing: -0.01em;
    transition: color 0.3s cubic-bezier(0.22, 0.61, 0.36, 1);
  }
  .item-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: 4px;
  }
  .item-stock {
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 600;
  }
  .item-stock strong {
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-weight: 500;
    font-size: 14px;
    color: var(--ink-blue);
    letter-spacing: 0;
    text-transform: none;
    margin-right: 4px;
  }
  .item-loc {
    font-family: "Inter", sans-serif;
    font-size: 11px;
    color: var(--ink-faint);
    font-style: italic;
  }
  .item-arrow {
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 24px;
    color: var(--ink-faint);
    transition: transform 0.3s cubic-bezier(0.22, 0.61, 0.36, 1), color 0.3s cubic-bezier(0.22, 0.61, 0.36, 1);
    align-self: center;
  }
  .item-btn:hover .item-arrow {
    transform: translateX(6px);
    color: var(--ink-blue);
  }

  /* ── Resumen ─────────────────────────────────────────── */
  .resumen {
    background: var(--paper-warm);
    border-left: 2px solid var(--ink-blue);
    padding: 22px 24px;
    margin-bottom: 28px;
    font-family: "Fraunces", Georgia, serif;
    font-size: 15px;
    color: var(--ink-soft);
    line-height: 1.7;
  }
  .resumen-row {
    display: grid;
    grid-template-columns: 110px 1fr;
    gap: 12px;
    padding: 4px 0;
  }
  .resumen-row + .resumen-row { border-top: 1px solid var(--hairline-2); padding-top: 8px; margin-top: 4px; }
  .resumen-key {
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 600;
    padding-top: 3px;
  }
  .resumen-val {
    font-family: "Fraunces", Georgia, serif;
    font-size: 16px;
    color: var(--ink);
    font-weight: 500;
    letter-spacing: -0.005em;
  }
  .resumen-val em {
    font-style: italic;
    font-weight: 400;
    color: var(--ink-blue);
  }

  /* ── Action buttons ──────────────────────────────────── */
  .label {
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 600;
    margin-bottom: 10px;
    display: block;
  }
  .action-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 28px;
  }
  .action-btn {
    padding: 24px 16px;
    background: var(--paper);
    border: 1px solid var(--hairline);
    border-radius: 2px;
    font-family: "Fraunces", Georgia, serif;
    font-size: 18px;
    font-weight: 500;
    color: var(--ink);
    cursor: pointer;
    text-align: center;
    transition: all 0.35s cubic-bezier(0.22, 0.61, 0.36, 1);
    letter-spacing: -0.005em;
    position: relative;
  }
  .action-btn .action-key {
    display: block;
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.28em;
    color: var(--ink-faint);
    margin-bottom: 6px;
    font-weight: 600;
    text-transform: uppercase;
    transition: color 0.3s cubic-bezier(0.22, 0.61, 0.36, 1);
  }
  .action-btn:hover {
    border-color: var(--ink);
    transform: translateY(-2px);
    box-shadow: var(--shadow-button);
  }
  .action-btn.retiro.selected {
    background: var(--oxblood);
    border-color: var(--oxblood);
    color: var(--on-accent);
  }
  .action-btn.retiro.selected .action-key { color: rgba(255,255,255,0.7); }
  html[data-theme="dark"] .action-btn.retiro.selected .action-key { color: rgba(14,14,14,0.7); }
  .action-btn.devolucion.selected {
    background: var(--moss);
    border-color: var(--moss);
    color: var(--on-accent);
  }
  .action-btn.devolucion.selected .action-key { color: rgba(255,255,255,0.7); }
  html[data-theme="dark"] .action-btn.devolucion.selected .action-key { color: rgba(14,14,14,0.7); }

  /* ── Quantity stepper ────────────────────────────────── */
  .qty-block { margin-bottom: 32px; }
  .qty-row {
    display: grid;
    grid-template-columns: 64px 1fr 64px;
    gap: 0;
    align-items: stretch;
    border-top: 1px solid var(--ink);
    border-bottom: 1px solid var(--ink);
  }
  .qty-btn {
    background: transparent;
    border: none;
    border-right: 1px solid var(--hairline);
    font-family: "Fraunces", Georgia, serif;
    font-size: 32px;
    font-weight: 300;
    color: var(--ink);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.22, 0.61, 0.36, 1);
    height: 80px;
  }
  .qty-btn:last-child {
    border-right: none;
    border-left: 1px solid var(--hairline);
  }
  .qty-btn:hover {
    background: var(--ink);
    color: var(--on-ink);
  }
  .qty-input-wrap {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 8px;
  }
  .qty-input {
    width: 100%;
    background: transparent;
    border: none;
    font-family: "Fraunces", Georgia, serif;
    font-size: 44px;
    font-weight: 400;
    color: var(--ink);
    text-align: center;
    letter-spacing: -0.02em;
    line-height: 1;
    -moz-appearance: textfield;
  }
  .qty-input::-webkit-outer-spin-button,
  .qty-input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
  .qty-input:focus { outline: none; }
  .qty-unit {
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: var(--ink-mute);
    margin-top: 4px;
    font-weight: 600;
  }

  /* ── Primary button ──────────────────────────────────── */
  .btn-primary {
    width: 100%;
    padding: 22px;
    background: var(--ink);
    color: var(--on-ink);
    border: none;
    border-radius: 2px;
    font-family: "Fraunces", Georgia, serif;
    font-size: 18px;
    font-weight: 500;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.22, 0.61, 0.36, 1);
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
  }
  .btn-primary::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--ink-blue);
    transform: translateY(100%);
    transition: transform 0.45s cubic-bezier(0.22, 0.61, 0.36, 1);
  }
  .btn-primary span { position: relative; z-index: 1; }
  .btn-primary:hover { box-shadow: var(--shadow-button); }
  .btn-primary:hover::before { transform: translateY(0); }
  .btn-primary:disabled {
    background: var(--ink-faint);
    cursor: not-allowed;
  }
  .btn-primary:disabled::before { display: none; }
  .btn-primary .arrow {
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 22px;
    position: relative;
    z-index: 1;
    transition: transform 0.4s cubic-bezier(0.22, 0.61, 0.36, 1);
  }
  .btn-primary:hover .arrow { transform: translateX(4px); }

  /* ── Back link ───────────────────────────────────────── */
  .back-link {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 20px;
    color: var(--ink-mute);
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 15px;
    cursor: pointer;
    transition: color 0.3s cubic-bezier(0.22, 0.61, 0.36, 1);
    background: none;
    border: none;
    width: 100%;
    padding: 8px;
  }
  .back-link:hover { color: var(--ink-blue); }
  .back-link .arrow-back {
    font-family: "Fraunces", Georgia, serif;
    font-size: 18px;
    transition: transform 0.3s cubic-bezier(0.22, 0.61, 0.36, 1);
  }
  .back-link:hover .arrow-back { transform: translateX(-4px); }

  /* ── Result state ────────────────────────────────────── */
  .result-block { text-align: center; }
  .result-mark {
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-weight: 300;
    font-size: 88px;
    line-height: 1;
    color: var(--ink-blue);
    margin-bottom: 16px;
    animation: fadeUp 0.6s cubic-bezier(0.22, 0.61, 0.36, 1) both;
  }
  .result-mark.err { color: var(--oxblood); }
  .result-eyebrow {
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: var(--ink-mute);
    margin-bottom: 12px;
    font-weight: 600;
  }
  .result-msg {
    font-family: "Fraunces", Georgia, serif;
    font-size: 19px;
    color: var(--ink);
    line-height: 1.5;
    margin-bottom: 32px;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }
  .result-msg em { font-style: italic; color: var(--ink-blue); }

  /* ── Empty state ─────────────────────────────────────── */
  .empty {
    padding: 40px 16px;
    text-align: center;
    color: var(--ink-mute);
    font-family: "Fraunces", Georgia, serif;
    font-style: italic;
    font-size: 15px;
    line-height: 1.6;
  }
  .empty::before {
    content: "—";
    display: block;
    font-size: 24px;
    color: var(--ink-faint);
    margin-bottom: 8px;
  }

  /* ── Colophon ────────────────────────────────────────── */
  .colophon {
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1px solid var(--hairline);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: var(--ink-mute);
    font-weight: 600;
  }
  .colophon-dot {
    display: inline-block;
    width: 4px;
    height: 4px;
    background: var(--ink-blue);
    border-radius: 50%;
    margin: 0 8px;
    vertical-align: middle;
  }

  /* ── Responsive ──────────────────────────────────────── */
  @media (max-width: 480px) {
    body { padding: 20px 14px 40px; font-size: 14px; }
    .sheet { padding: 32px 24px 28px; }
    .sheet-corner { font-size: 72px; top: 12px; right: 16px; }
    .brand { font-size: 22px; }
    .tagline { font-size: 15px; padding: 14px 0 22px; }
    .step-title { font-size: 23px; }
    .index-row { grid-template-columns: 48px 1fr auto; gap: 14px; padding: 14px 0; }
    .index-num { font-size: 28px; }
    .item-name { font-size: 17px; }
    .qty-input { font-size: 36px; }
    .qty-btn { height: 72px; font-size: 28px; }
    .action-btn { padding: 20px 12px; font-size: 16px; }
    .worker-btn { padding: 18px 10px; font-size: 16px; }
    .resumen-row { grid-template-columns: 90px 1fr; gap: 8px; }
    .masthead-right .vol { display: none; }
  }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>
</head>
<body>
  <div class="stage">

    <header class="masthead">
      <div class="masthead-left">
        <span class="eyebrow">Taller · Inventario</span>
        <span class="brand">Registro <em>diario</em></span>
      </div>
      <div class="masthead-right">
        <div style="display:flex; gap:10px; align-items:center;">
          <span class="vol">Vol. I</span>
          <button class="theme-toggle" id="themeToggle" type="button">◐ DARK</button>
        </div>
        <span class="date" id="fecha"></span>
      </div>
    </header>

    <p class="tagline">Registrá lo que retirás o devolvés del taller en tres pasos. Tocá, confirmá, listo.</p>

    <nav class="index" aria-label="Pasos del registro">
      <div class="index-row active" id="idx1">
        <div class="index-num">01</div>
        <div>
          <div class="index-label">Quién</div>
          <div class="index-desc">identificá tu nombre</div>
        </div>
        <div class="index-marker">en curso</div>
      </div>
      <div class="index-row" id="idx2">
        <div class="index-num">02</div>
        <div>
          <div class="index-label">Qué</div>
          <div class="index-desc">elegí el material o herramienta</div>
        </div>
        <div class="index-marker">pendiente</div>
      </div>
      <div class="index-row" id="idx3">
        <div class="index-num">03</div>
        <div>
          <div class="index-label">Cuánto</div>
          <div class="index-desc">retiro o devolución, y cantidad</div>
        </div>
        <div class="index-marker">pendiente</div>
      </div>
    </nav>

    <main class="sheet corner-1" id="sheet">
      <div class="sheet-corner" aria-hidden="true"></div>

      <section id="paso1" class="step-block">
        <h2 class="step-title">¿Quién <em>sos?</em></h2>
        <p class="step-sub">Elegí tu nombre de la lista para empezar el registro.</p>
        <div class="worker-grid" id="workerGrid">
          {% for w in workers %}
          <button class="worker-btn" onclick="elegirTrabajador(this, '{{ w }}')"><span>{{ w }}</span></button>
          {% else %}
          <div class="empty" style="grid-column: span 2;">
            No hay trabajadores cargados todavía.<br>
            El administrador debe agregarlos desde la app de escritorio.
          </div>
          {% endfor %}
        </div>
      </section>

      <section id="paso2" class="step-block hidden">
        <h2 class="step-title">¿Qué <em>retirás</em> o devolvés?</h2>
        <p class="step-sub">Buscá por nombre o navegá la lista completa del taller.</p>

        <div class="search-wrap">
          <span class="search-icon">⌕</span>
          <input class="search-box" type="text" placeholder="Buscar material o herramienta…"
                 oninput="filtrarItems(this.value)" aria-label="Buscar">
        </div>

        <div class="item-grid" id="itemGrid">
          {% for item in items %}
          <button class="item-btn" data-nombre="{{ item['name']|lower }}"
                  onclick="elegirItem({{ item['id'] }}, '{{ item['name'] }}', {{ item['quantity'] }}, '{{ item['unit'] }}')">
            <div>
              <div class="item-name">{{ item['name'] }}</div>
              <div class="item-meta">
                <span class="item-stock"><strong>{{ item['quantity'] }}</strong>{{ item['unit'] }} disponible</span>
                {% if item['location'] %}<span class="item-loc">{{ item['location'] }}</span>{% endif %}
              </div>
            </div>
            <span class="item-arrow">→</span>
          </button>
          {% else %}
          <div class="empty">No hay ítems cargados todavía.</div>
          {% endfor %}
        </div>
      </section>

      <section id="paso3" class="step-block hidden">
        <h2 class="step-title">Confirmá el <em>movimiento</em></h2>
        <p class="step-sub">Revisá los datos, elegí la acción y la cantidad.</p>

        <div class="resumen" id="resumen"></div>

        <span class="label">Acción</span>
        <div class="action-row">
          <button class="action-btn retiro" onclick="elegirAccion('retiro', this)">
            <span class="action-key">Salir</span>
            Retirar
          </button>
          <button class="action-btn devolucion" onclick="elegirAccion('devolucion', this)">
            <span class="action-key">Volver</span>
            Devolver
          </button>
        </div>

        <div class="qty-block">
          <span class="label">Cantidad</span>
          <div class="qty-row">
            <button class="qty-btn" onclick="cambiarQty(-1)" aria-label="Restar">−</button>
            <div class="qty-input-wrap">
              <input class="qty-input" type="number" id="qty" value="1" min="1" step="1" inputmode="numeric">
              <span class="qty-unit" id="qtyUnit">u.</span>
            </div>
            <button class="qty-btn" onclick="cambiarQty(1)" aria-label="Sumar">+</button>
          </div>
        </div>

        <button class="btn-primary" id="btnConfirmar" onclick="confirmar()">
          <span>Confirmar movimiento</span>
          <span class="arrow">→</span>
        </button>
        <button class="back-link" onclick="volverPaso2()">
          <span class="arrow-back">←</span>
          <span>cambiar material</span>
        </button>
      </section>

      <section id="resultado" class="step-block result-block hidden">
        <div class="result-mark" id="resultMark">✓</div>
        <div class="result-eyebrow" id="resultEyebrow">Registro confirmado</div>
        <div class="result-msg" id="msgResultado"></div>
        <button class="btn-primary" onclick="reiniciar()">
          <span>Registrar otro movimiento</span>
          <span class="arrow">→</span>
        </button>
      </section>
    </main>

    <footer class="colophon">
      <span>Taller <span class="colophon-dot"></span> Inventario</span>
      <span>v. Editorial</span>
    </footer>

  </div>

<script>
  // Fecha en masthead
  (function(){
    const f = new Date();
    const meses = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
    document.getElementById('fecha').textContent = f.getDate() + ' de ' + meses[f.getMonth()] + ' · ' + f.getFullYear();
  })();

  // Theme toggle (light/dark) con persistencia en localStorage
  (function(){
    const html = document.documentElement;
    const btn = document.getElementById('themeToggle');
    const saved = localStorage.getItem('taller-theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      html.setAttribute('data-theme', 'dark');
      btn.textContent = '◐ LIGHT';
    }
    btn.addEventListener('click', () => {
      const isDark = html.getAttribute('data-theme') === 'dark';
      if (isDark) {
        html.removeAttribute('data-theme');
        localStorage.setItem('taller-theme', 'light');
        btn.textContent = '◐ DARK';
      } else {
        html.setAttribute('data-theme', 'dark');
        localStorage.setItem('taller-theme', 'dark');
        btn.textContent = '◐ LIGHT';
      }
    });
  })();

  let trabajador = '', itemId = null, itemNombre = '', itemStock = 0, itemUnidad = '', accion = '';
  const STATE_LABELS = { active: 'en curso', done: 'completo', pending: 'pendiente' };

  function setStep(n) {
    const sheet = document.getElementById('sheet');
    sheet.className = 'sheet corner-' + n;
    [1,2,3].forEach(i => {
      const row = document.getElementById('idx'+i);
      row.classList.remove('active','done');
      if (i < n) {
        row.classList.add('done');
        row.querySelector('.index-marker').textContent = STATE_LABELS.done;
      } else if (i === n) {
        row.classList.add('active');
        row.querySelector('.index-marker').textContent = STATE_LABELS.active;
      } else {
        row.querySelector('.index-marker').textContent = STATE_LABELS.pending;
      }
    });
  }

  function elegirTrabajador(btn, nombre) {
    trabajador = nombre;
    document.querySelectorAll('.worker-btn').forEach(b => {
      b.style.background = '';
      b.style.color = '';
      b.style.borderColor = '';
    });
    const cs = getComputedStyle(document.documentElement);
    btn.style.background = cs.getPropertyValue('--ink-blue').trim();
    btn.style.color = cs.getPropertyValue('--on-accent').trim();
    btn.style.borderColor = cs.getPropertyValue('--ink-blue').trim();
    setTimeout(() => {
      swapStep('paso1','paso2');
      setStep(2);
    }, 220);
  }

  function filtrarItems(q) {
    const term = q.toLowerCase().trim();
    document.querySelectorAll('.item-btn').forEach(btn => {
      const match = !term || btn.dataset.nombre.includes(term);
      btn.style.display = match ? '' : 'none';
    });
  }

  function elegirItem(id, nombre, stock, unidad) {
    itemId = id; itemNombre = nombre; itemStock = stock; itemUnidad = unidad;
    document.getElementById('qtyUnit').textContent = unidad || 'u.';
    document.getElementById('resumen').innerHTML =
      '<div class="resumen-row"><span class="resumen-key">Trabajador</span><span class="resumen-val">' + escapeHtml(trabajador) + '</span></div>' +
      '<div class="resumen-row"><span class="resumen-key">Material</span><span class="resumen-val">' + escapeHtml(nombre) + '</span></div>' +
      '<div class="resumen-row"><span class="resumen-key">Stock actual</span><span class="resumen-val"><em>' + stock + '</em> ' + unidad + '</span></div>';
    swapStep('paso2','paso3');
    accion = '';
    document.querySelectorAll('.action-btn').forEach(b => b.classList.remove('selected'));
    document.getElementById('qty').value = 1;
    setStep(3);
  }

  function elegirAccion(a, btn) {
    accion = a;
    document.querySelectorAll('.action-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
  }

  function cambiarQty(delta) {
    const inp = document.getElementById('qty');
    inp.value = Math.max(1, (parseFloat(inp.value) || 1) + delta);
  }

  function volverPaso2() {
    swapStep('paso3','paso2');
    setStep(2);
  }

  async function confirmar() {
    if (!accion) { shake(document.querySelector('.action-row')); return; }
    const qty = parseFloat(document.getElementById('qty').value);
    if (!qty || qty <= 0) { shake(document.querySelector('.qty-row')); return; }

    const btn = document.getElementById('btnConfirmar');
    btn.disabled = true;
    btn.querySelector('span').textContent = 'Enviando…';

    try {
      const resp = await fetch('/registrar', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({worker_name: trabajador, item_id: itemId, action: accion, quantity: qty})
      });
      const data = await resp.json();

      document.getElementById('paso3').classList.add('hidden');
      const r = document.getElementById('resultado');
      r.classList.remove('hidden');
      r.style.animation = 'none';
      void r.offsetWidth;
      r.style.animation = '';

      const mark = document.getElementById('resultMark');
      const eye  = document.getElementById('resultEyebrow');
      const msg  = document.getElementById('msgResultado');

      if (data.ok) {
        mark.textContent = '✓';
        mark.classList.remove('err');
        eye.textContent = 'Registro confirmado';
        msg.innerHTML = '<em>' + escapeHtml(trabajador) + '</em> ' + (accion === 'retiro' ? 'retiró' : 'devolvió') +
                        ' <em>' + qty + ' ' + itemUnidad + '</em> de ' + escapeHtml(itemNombre) + '.';
      } else {
        mark.textContent = '✕';
        mark.classList.add('err');
        eye.textContent = 'No se pudo registrar';
        msg.textContent = data.mensaje || 'Ocurrió un error. Probá de nuevo.';
      }
      setStepDone(3);
    } catch (e) {
      document.getElementById('paso3').classList.add('hidden');
      const r = document.getElementById('resultado');
      r.classList.remove('hidden');
      document.getElementById('resultMark').textContent = '✕';
      document.getElementById('resultMark').classList.add('err');
      document.getElementById('resultEyebrow').textContent = 'Sin conexión';
      document.getElementById('msgResultado').textContent = 'No se pudo contactar al servidor. Revisá tu conexión e intentá de nuevo.';
      setStepDone(3);
    } finally {
      btn.disabled = false;
      btn.querySelector('span').textContent = 'Confirmar movimiento';
    }
  }

  function setStepDone(n) {
    const row = document.getElementById('idx'+n);
    row.classList.remove('active');
    row.classList.add('done');
    row.querySelector('.index-marker').textContent = STATE_LABELS.done;
  }

  function reiniciar() {
    trabajador = ''; itemId = null; accion = '';
    document.querySelectorAll('.worker-btn').forEach(b => {
      b.style.background = '';
      b.style.color = '';
      b.style.borderColor = '';
    });
    ['paso2','paso3','resultado'].forEach(id => document.getElementById(id).classList.add('hidden'));
    document.getElementById('paso1').classList.remove('hidden');
    const p1 = document.getElementById('paso1');
    p1.style.animation = 'none';
    void p1.offsetWidth;
    p1.style.animation = '';
    setStep(1);
  }

  function swapStep(fromId, toId) {
    document.getElementById(fromId).classList.add('hidden');
    const to = document.getElementById(toId);
    to.classList.remove('hidden');
    to.style.animation = 'none';
    void to.offsetWidth;
    to.style.animation = '';
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  function shake(el) {
    el.style.animation = 'none';
    void el.offsetWidth;
    el.style.animation = 'shake 0.4s cubic-bezier(0.22, 0.61, 0.36, 1)';
    setTimeout(() => { el.style.animation = ''; }, 400);
  }

  (function(){
    const s = document.createElement('style');
    s.textContent = '@keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-6px)} 75%{transform:translateX(6px)} }';
    document.head.appendChild(s);
  })();
</script>
</body>
</html>
"""


NOT_FOUND_HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>No encontrado</title></head><body style="font-family:Georgia,serif;text-align:center;padding:80px 20px;background:#FAFAF7;color:#2C2C2C;">
<h2 style="font-style:italic;font-weight:400;">Ítem no encontrado</h2>
<p style="color:#6B6B6B;margin-top:8px;">Consultá con el administrador del taller.</p>
</body></html>"""


@app.route("/")
def home():
    return render_template_string(WORKER_HTML, workers=db.get_workers(), items=db.get_items())


@app.route("/registrar", methods=["POST"])
def registrar():
    data = request.get_json()
    ok, mensaje, new_qty = db.register_movement(
        data["item_id"], data["worker_name"], data["action"], float(data["quantity"])
    )
    if ok:
        send_whatsapp(mensaje)
    return jsonify({"ok": ok, "mensaje": mensaje})


def run_server():
    db.init_db()
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)


if __name__ == "__main__":
    run_server()
