import argparse
from datetime import timedelta

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session
from werkzeug.exceptions import HTTPException

import auth
import main
import system
from main import RepTrackerError

app = Flask(__name__)
app.secret_key = auth.SecretKey()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict",
                  PERMANENT_SESSION_LIFETIME=timedelta(days=30))
MAX_UPLOAD_GB = 3
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_GB * 1024 ** 3   # streamed to a temp file, then to disk


@app.errorhandler(RepTrackerError)
def handle_error(err):
    return jsonify({"error": str(err)}), 400


@app.errorhandler(system.AdminError)
def handle_admin_error(err):
    return jsonify({"error": str(err)}), 400


@app.errorhandler(413)
def too_large(err):
    return jsonify({"error": f"File is larger than {MAX_UPLOAD_GB} GB."}), 413


@app.errorhandler(Exception)
def unexpected(err):
    """A bug or an error nobody planned for: the page gets a sentence, the terminal gets the details."""
    if isinstance(err, HTTPException):
        return err
    app.logger.exception("Unexpected error")
    return jsonify({"error": f"Unexpected error in the server ({type(err).__name__}). "
                             "The details are in the terminal that runs app.py."}), 500


# ---------- sign-in: every page and API call needs it, except the login page itself ----------

OPEN_ENDPOINTS = {"login", "login_post"}


@app.before_request
def require_sign_in():
    if request.endpoint in OPEN_ENDPOINTS:
        return None
    if session.get("user") and session.get("account") and session.get("account") == auth.AccountId():
        return None
    session.clear()
    if request.path.startswith(("/api/", "/media/", "/research/")):
        return jsonify({"error": "Sign in first."}), 401
    return redirect("/login")


def _LoginPage(error=None, username=None, status=200):
    local = request.host.split(":")[0] in ("127.0.0.1", "localhost")
    return render_template("login.html", setup=not auth.AccountExists(), error=error, username=username,
                           min_password=auth.MIN_PASSWORD, secure=request.is_secure or local), status


@app.get("/login")
def login():
    if session.get("user") and session.get("account") == auth.AccountId():
        return redirect("/")
    return _LoginPage()


@app.post("/login")
def login_post():
    form = request.form
    try:
        if auth.AccountExists():
            user, account = auth.CheckLogin(form.get("username"), form.get("password"), request.remote_addr)
        else:
            user, account = auth.CreateAccount(form.get("username"), form.get("password"), form.get("confirm"))
    except auth.AuthError as err:
        return _LoginPage(str(err), form.get("username"), 400)
    session.clear()
    session.permanent = True
    session["user"], session["account"] = user, account
    return redirect("/")


@app.post("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.get("/api/me")
def me():
    return jsonify({"user": session.get("user")})


# ---------- this installation: branch, update, restart, uninstall (D8) ----------

@app.get("/api/system")
def system_info():
    return jsonify(system.Info())


@app.get("/api/system/branches")
def system_branches():
    return jsonify({"branches": system.Branches()})


@app.post("/api/system/<action>")
def system_action(action):
    body = request.get_json(force=True) or {}
    if action == "uninstall":   # the one step that can't be undone from the page: ask for the password again
        try:
            auth.CheckLogin(session.get("user"), body.get("password"), request.remote_addr)
        except auth.AuthError as err:
            return jsonify({"error": str(err)}), 400
    return jsonify(system.Run(action, body.get("branch"), bool(body.get("deleteData"))))


# ---------- open on a phone: this server's addresses on the network, and a QR code ----------

def PhoneLinks():
    """The addresses a phone on the same network can open: IP addresses first (Android often can't look up
    .local names), then name.local. Empty when the server only listens on this computer (no --lan)."""
    port = app.config.get("LAN_PORT")
    if not port:
        return {"lan": False, "links": []}
    suffix = "" if port == 443 else f":{port}"
    links = [{"url": f"https://{a}{suffix}", "label": a + (" (Tailscale)" if a.startswith("100.") else "")}
             for a in sorted(auth.LanAddresses(), key=lambda a: a.startswith("100."))]
    links += [{"url": f"https://{n}{suffix}", "label": f"{n} (not on every Android phone)"} for n in auth.HostNames() if n.endswith(".local")]
    return {"lan": True, "links": links}


@app.get("/api/phone")
def phone_links():
    return jsonify(PhoneLinks())


@app.get("/api/phone/qr.svg")
def phone_qr():
    import io
    import segno
    url = request.args.get("url", "")
    if url not in [l["url"] for l in PhoneLinks()["links"]]:
        return jsonify({"error": "Not one of this server's addresses."}), 404
    out = io.BytesIO()
    segno.make(url, error="m").save(out, kind="svg", scale=6, border=2, dark="#000", light="#fff", xmldecl=False)
    return app.response_class(out.getvalue(), mimetype="image/svg+xml")


@app.route("/")
def home():
    return render_template("index.html")


# Every route below is per mode: "toy" (sample data) or "main" (starts empty).

# ---------- media (the simulated camera and sensors) ----------

@app.get("/api/<mode>/media")
def media(mode):
    return jsonify(main.ListMedia(mode))


@app.post("/api/<mode>/media/<kind>")
def upload_media(mode, kind):
    """The body is the file itself (not a form), named by the X-File-Name header: it streams straight to disk."""
    from urllib.parse import unquote
    name = unquote(request.headers.get("X-File-Name", ""))
    if not name or not request.content_length:
        raise RepTrackerError("Choose a file to upload.")
    return jsonify(main.SaveUpload(mode, kind, name, request.stream, request.content_length)), 201


@app.delete("/api/<mode>/media/videos/<name>")
def delete_video(mode, name):
    return jsonify(main.DeleteVideo(mode, name))


@app.get("/media/<mode>/videos/<path:name>")
def video(mode, name):
    return send_from_directory(main.VideosDir(mode), name)


@app.get("/media/<mode>/sensors/<path:name>")
def sensor(mode, name):
    path = main.SensorPath(mode, name.removesuffix(".json"))   # mode upload, else shared default
    return send_from_directory(path.parent, path.name)


# ---------- lizards ----------

@app.get("/api/<mode>/lizards")
def lizards(mode):
    return jsonify(main.ListLizards(mode))


@app.post("/api/<mode>/lizards")
def create_lizard(mode):
    return jsonify(main.CreateNewLizard(mode, request.get_json(force=True) or {})), 201


@app.put("/api/<mode>/lizards/<lizard_id>")
def update_lizard(mode, lizard_id):
    return jsonify(main.UpdateLizard(mode, lizard_id, request.get_json(force=True) or {}))


@app.delete("/api/<mode>/lizards/<lizard_id>")
def remove_lizard(mode, lizard_id):
    main.RemoveLizard(mode, lizard_id)
    return "", 204


# ---------- AI provider (one choice for this computer, not per mode) ----------

@app.get("/api/ai")
def ai_status():
    return jsonify(main.AiStatus())


@app.post("/api/ai")
def set_ai_provider():
    body = request.get_json(force=True) or {}
    return jsonify(main.SetProvider(body.get("provider")))


@app.post("/api/ai/claude-key")
def save_claude_key():
    body = request.get_json(force=True) or {}
    return jsonify(main.SaveClaudeKey(body.get("key")))


@app.post("/api/ai/claude-model")
def set_claude_model():
    body = request.get_json(force=True) or {}
    return jsonify(main.SetClaudeModel(body.get("model")))


@app.delete("/api/ai/claude-key")
def remove_claude_key():
    return jsonify(main.RemoveClaudeKey())


@app.post("/api/ai/test")
def test_ai_provider():
    return jsonify(main.TestProvider())


# ---------- species profiles (Research tab; shared by every mode) ----------

@app.get("/api/research")
def list_profiles():
    return jsonify(main.ListProfiles())


@app.post("/api/research")
def create_profile():
    body = request.get_json(force=True) or {}
    return jsonify(main.CreateProfile(body.get("species"), bool(body.get("regenerate")))), 201


@app.get("/api/research/<slug>")
def get_profile(slug):
    return jsonify(main.GetProfile(slug))


@app.get("/api/research-patterns")
def sensor_patterns():
    return jsonify(main.research.SENSOR_PATTERNS)


@app.post("/api/<mode>/research/<slug>/sensors")
def generate_sensors(mode, slug):
    body = request.get_json(force=True) or {}
    return jsonify(main.GenerateSensors(mode, slug, body.get("pattern"))), 201


@app.put("/api/research/<slug>")
def update_profile(slug):
    body = request.get_json(force=True) or {}
    return jsonify(main.UpdateProfile(slug, body.get("profile")))


@app.delete("/api/research/<slug>")
def delete_profile(slug):
    return jsonify(main.DeleteProfile(slug))


@app.get("/api/species-names")
def species_names():
    """Common kept reptiles and amphibians [common, scientific, type, nicknames], for spelling suggestions."""
    return send_from_directory(main.DATA, "species-names.json")


@app.get("/research/<slug>/images/<name>")
def profile_image(slug, name):
    return send_from_directory(main.research.Folder(slug) / "images", name)


# ---------- feeding log and movement ----------

@app.post("/api/<mode>/lizards/<lizard_id>/feedings")
def add_feeding(mode, lizard_id):
    return jsonify(main.AddFeeding(mode, lizard_id, request.get_json(force=True) or {})), 201


@app.delete("/api/<mode>/lizards/<lizard_id>/feedings/<feeding_id>")
def delete_feeding(mode, lizard_id, feeding_id):
    return jsonify(main.DeleteFeeding(mode, lizard_id, feeding_id))


@app.get("/api/<mode>/lizards/<lizard_id>/movement")
def movement(mode, lizard_id):
    return jsonify(main.MovementData(mode, lizard_id))


# ---------- prompts and AI ----------

@app.post("/api/<mode>/lizards/<lizard_id>/prompts")
def generate_prompts(mode, lizard_id):
    body = request.get_json(force=True) or {}
    return jsonify(main.GeneratePrompts(mode, lizard_id, body.get("start"), body.get("end"), body.get("images")))


@app.get("/api/<mode>/lizards/<lizard_id>/prompts/<bundle_id>/<path:file>")
def bundle_file(mode, lizard_id, bundle_id, file):
    folder, _ = main.LoadBundle(mode, lizard_id, bundle_id)
    return send_from_directory(folder, file)


@app.post("/api/<mode>/lizards/<lizard_id>/prompts/<bundle_id>/send")
def send_prompts(mode, lizard_id, bundle_id):
    return jsonify(main.SendPrompt(mode, lizard_id, bundle_id))


@app.post("/api/<mode>/lizards/<lizard_id>/ask")
def ask(mode, lizard_id):
    body = request.get_json(force=True) or {}
    return jsonify(main.AskQuestion(mode, lizard_id, body.get("question"), body.get("now"), bool(body.get("vision", True)),
                                    body.get("photo")))


def ServeLan(port, redirectPort):
    """The LAN server: cheroot (a production WSGI server) over HTTPS, and optionally a plain-HTTP port that
    only redirects to HTTPS, so typing reptracker.local works. Falls back to Flask's server without cheroot."""
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["LAN_PORT"] = port
    cert, key = auth.Certificate()
    suffix = "" if port == 443 else f":{port}"
    print("RepTracker on your network (HTTPS; the browser warns once about the self-signed certificate):")
    for address in auth.HostNames() + (auth.LanAddresses() or ["<this computer's IP>"]):
        print(f"  https://{address}{suffix}")
    try:
        from cheroot import wsgi
        from cheroot.ssl.builtin import BuiltinSSLAdapter
    except ImportError:
        app.run(host="0.0.0.0", port=port, ssl_context=(cert, key), debug=False, threaded=True)
        return
    import threading
    if redirectPort:
        def redirect_app(environ, start_response):
            host = (environ.get("HTTP_HOST") or "localhost").split(":")[0]
            path = environ.get("PATH_INFO", "/") + (f"?{environ['QUERY_STRING']}" if environ.get("QUERY_STRING") else "")
            start_response("301 Moved Permanently", [("Location", f"https://{host}{suffix}{path}"), ("Content-Length", "0")])
            return [b""]
        plain = wsgi.Server(("0.0.0.0", redirectPort), redirect_app, numthreads=2)
        threading.Thread(target=plain.safe_start, daemon=True).start()
    server = wsgi.Server(("0.0.0.0", port), app, numthreads=16, timeout=600)
    server.ssl_adapter = BuiltinSSLAdapter(cert, key)
    server.safe_start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RepTracker dashboard")
    parser.add_argument("--lan", action="store_true",
                        help="serve on the local network over HTTPS (self-signed certificate), with debug off")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--http-redirect", type=int, default=0, metavar="PORT",
                        help="with --lan: also listen on this plain-HTTP port, only to redirect to HTTPS (0 = off)")
    args = parser.parse_args()
    if args.lan:
        ServeLan(args.port, args.http_redirect)
    else:
        app.run(port=args.port, debug=True)   # this computer only (127.0.0.1)
