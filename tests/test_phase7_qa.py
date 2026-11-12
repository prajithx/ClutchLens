import pytest

from dashboard.app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


@pytest.mark.parametrize("route", ["/", "/analytics", "/players", "/ground", "/recruitment"])
def test_required_routes_render_successfully(client, route):
    response = client.get(route)

    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


@pytest.mark.parametrize(
    "asset",
    ["/static/css/style.css", "/static/js/main.js", "/static/js/animations.js"],
)
def test_required_assets_load_successfully(client, asset):
    response = client.get(asset)

    assert response.status_code == 200
    assert response.data


def test_players_api_preserves_id_and_name_fields(client):
    response = client.get("/api/players?q=raj")

    assert response.status_code == 200
    players = response.get_json()
    assert isinstance(players, list)
    assert players
    assert all({"id", "name"} <= set(player) for player in players)


def test_recruitment_contains_separate_shortlist_workflows(client):
    response = client.get("/recruitment")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Suggested Shortlist" in body
    assert "Human-reviewed working shortlist" in body
    assert "data-suggested-add" in body
    assert "data-shortlist-button" in body
