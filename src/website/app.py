from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.exceptions import HTTPException

import main
from main import RepTrackerError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024   # uploads up to 500 MB


@app.errorhandler(RepTrackerError)
def handle_error(err):
    return jsonify({"error": str(err)}), 400


@app.errorhandler(413)
def too_large(err):
    return jsonify({"error": "File is larger than 500 MB."}), 413


@app.errorhandler(Exception)
def unexpected(err):
    """A bug or an error nobody planned for: the page gets a sentence, the terminal gets the details."""
    if isinstance(err, HTTPException):
        return err
    app.logger.exception("Unexpected error")
    return jsonify({"error": f"Unexpected error in the server ({type(err).__name__}). "
                             "The details are in the terminal that runs app.py."}), 500


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
    file = request.files.get("file")
    if not file:
        raise RepTrackerError("Choose a file to upload.")
    return jsonify(main.SaveUpload(mode, kind, file.filename, file.read())), 201


@app.get("/media/<mode>/videos/<path:name>")
def video(mode, name):
    return send_from_directory(main.VideosDir(mode), name)


@app.get("/media/<mode>/sensors/<path:name>")
def sensor(mode, name):
    return send_from_directory(main.SensorsDir(mode), name)


# ---------- lizards ----------

@app.get("/api/<mode>/lizards")
def lizards(mode):
    return jsonify(main.ListLizards(mode))


@app.post("/api/<mode>/lizards")
def create_lizard(mode):
    return jsonify(main.CreateNewLizard(mode, request.get_json(force=True) or {})), 201


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


@app.post("/api/ai/test")
def test_ai_provider():
    return jsonify(main.TestProvider())


# ---------- prompts and AI ----------

@app.post("/api/<mode>/lizards/<lizard_id>/prompts")
def generate_prompts(mode, lizard_id):
    body = request.get_json(force=True) or {}
    return jsonify(main.GeneratePrompts(mode, lizard_id, body.get("start"), body.get("end")))


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
    return jsonify(main.AskQuestion(mode, lizard_id, body.get("question"), body.get("now")))


if __name__ == "__main__":
    app.run(debug=True)
