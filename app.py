import os
from flask import Flask, redirect, request, session, render_template, jsonify
from flask_session import Session
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import spotipy

from spotify import get_spotify_data
from groq_client import ask_music_assistant

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

SCOPE = "user-read-recently-played user-top-read playlist-read-private"


def get_auth_manager():
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=SCOPE,
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    auth_manager = get_auth_manager()
    return redirect(auth_manager.get_authorize_url())


@app.route("/callback")
def callback():
    auth_manager = get_auth_manager()
    code = request.args.get("code")

    if not code:
        return redirect("/")

    token_info = auth_manager.get_access_token(code)
    session["token_info"] = token_info

    # Fetch all Spotify data on login and store in session
    sp = spotipy.Spotify(auth=token_info["access_token"])
    spotify_data = get_spotify_data(sp)
    session["spotify_data"] = spotify_data

    return redirect("/chat")


@app.route("/chat")
def chat():
    if "spotify_data" not in session:
        return redirect("/")
    return render_template("chat.html", spotify_data=session["spotify_data"])


@app.route("/ask", methods=["POST"])
def ask():
    if "spotify_data" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    user_prompt = data.get("message", "").strip()

    if not user_prompt:
        return jsonify({"error": "Empty message"}), 400

    response = ask_music_assistant(user_prompt, session["spotify_data"])
    return jsonify({"response": response})


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
