"""Tests for `PATCH /api/v1/artists/{artist_id}` (#1021)."""

from src.models import Artist


def _make_artist(db_session, name):
    artist = Artist(name=name)
    db_session.add(artist)
    db_session.commit()
    db_session.refresh(artist)
    return artist


def test_200_renames_artist_and_persists_the_change(client, db_session):
    artist = _make_artist(db_session, "Old Name")

    response = client.patch(f"/api/v1/artists/{artist.id}", json={"name": "New Name"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == artist.id
    assert body["name"] == "New Name"

    follow_up = client.get(f"/api/v1/artists/{artist.id}")
    assert follow_up.status_code == 200
    assert follow_up.json()["name"] == "New Name"


def test_422_for_empty_name_leaves_artist_unchanged(client, db_session):
    artist = _make_artist(db_session, "Unchanged Artist")

    response = client.patch(f"/api/v1/artists/{artist.id}", json={"name": ""})

    assert response.status_code == 422
    db_session.refresh(artist)
    assert artist.name == "Unchanged Artist"


def test_422_for_whitespace_only_name(client, db_session):
    artist = _make_artist(db_session, "Whitespace Guard Artist")

    response = client.patch(f"/api/v1/artists/{artist.id}", json={"name": "   "})

    assert response.status_code == 422
    db_session.refresh(artist)
    assert artist.name == "Whitespace Guard Artist"


def test_409_when_another_artist_already_holds_the_name(client, db_session):
    renaming_artist = _make_artist(db_session, "Renaming Artist")
    holder = _make_artist(db_session, "Taken Name")

    response = client.patch(f"/api/v1/artists/{renaming_artist.id}", json={"name": "Taken Name"})

    assert response.status_code == 409
    assert response.json() == {"detail": "An artist with that name already exists"}
    db_session.refresh(renaming_artist)
    db_session.refresh(holder)
    assert renaming_artist.name == "Renaming Artist"
    assert holder.name == "Taken Name"


def test_200_renaming_artist_to_its_own_current_name_is_a_no_op(client, db_session):
    artist = _make_artist(db_session, "Self Rename Artist")

    response = client.patch(f"/api/v1/artists/{artist.id}", json={"name": "Self Rename Artist"})

    assert response.status_code == 200
    assert response.json()["name"] == "Self Rename Artist"


def test_404_for_unknown_artist_id(client):
    response = client.patch("/api/v1/artists/999999", json={"name": "Anything"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Artist not found"}


def test_404_takes_precedence_over_409_when_id_unknown_and_name_taken(client, db_session):
    _make_artist(db_session, "Already Taken Name")

    response = client.patch("/api/v1/artists/999999", json={"name": "Already Taken Name"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Artist not found"}


def test_422_for_non_integer_artist_id(client):
    response = client.patch("/api/v1/artists/abc", json={"name": "Anything"})

    assert response.status_code == 422
