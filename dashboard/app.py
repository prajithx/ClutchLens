"""Local ClutchLens Flask application."""

from pathlib import Path

from flask import Flask, jsonify, render_template, request

try:
    from .data_service import (
        get_dashboard_data,
        get_player_data,
        get_players,
        get_recruitment_data,
        get_shot_data,
        get_venues,
    )
except ImportError:
    from data_service import (
        get_dashboard_data,
        get_player_data,
        get_players,
        get_recruitment_data,
        get_shot_data,
        get_venues,
    )


APP_ROOT = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=APP_ROOT / "templates", static_folder=APP_ROOT / "static")


@app.context_processor
def shared_context():
    return {"product_name": "CLUTCHLENS", "tagline": "SEE BEYOND STATISTICS."}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/analytics")
def analytics():
    return render_template("analytics.html", dashboard=get_dashboard_data())


@app.get("/players")
def players():
    selected = request.args.get("player_id", "")
    return render_template(
        "players.html",
        players=get_players(),
        selected=get_player_data(selected) if selected else None,
    )


@app.get("/ground")
def ground():
    venue_id = request.args.get("venue_id", "")
    return render_template("ground.html", shot_data=get_shot_data(venue_id), venues=get_venues())


@app.get("/recruitment")
def recruitment():
    return render_template("recruitment.html", recruitment=get_recruitment_data())


@app.get("/api/players")
def players_api():
    query = request.args.get("q", "").strip().lower()
    options = [
        player for player in get_players()
        if not query or query in player["name"].lower()
    ][:50]
    return jsonify(options)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
