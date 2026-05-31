from collections import Counter
from groq_client import fetch_top_genres


# ── Helpers ────────────────────────────────────────────────────────────────────

def format_track(track):
    artists = ", ".join(a["name"] for a in track["artists"])
    return f"{track['name']} by {artists}"


# ── Data fetchers ──────────────────────────────────────────────────────────────

def fetch_recent_tracks(sp):
    data = sp.current_user_recently_played(limit=50)
    return [
        format_track(item["track"])
        for item in data.get("items", [])
        if item.get("track")
    ]


def fetch_top_tracks(sp):
    data = sp.current_user_top_tracks(limit=10, time_range="medium_term")
    return [format_track(t) for t in data.get("items", [])]


def fetch_top_artists(sp):
    data = sp.current_user_top_artists(limit=10, time_range="medium_term")
    return [a["name"] for a in data.get("items", [])]


def fetch_repeat_songs(sp, limit=5):
    # Find songs that appear more than once in the last 50 plays
    data = sp.current_user_recently_played(limit=50)
    track_counts = Counter()
    track_names = {}

    for item in data.get("items", []):
        track = item.get("track")
        if track and track.get("id"):
            tid = track["id"]
            track_counts[tid] += 1
            track_names[tid] = format_track(track)

    repeated = [
        f"{track_names[tid]} (x{count})"
        for tid, count in track_counts.most_common()
        if count > 1
    ]

    return repeated[:limit]


# ── Main aggregator ────────────────────────────────────────────────────────────

def get_spotify_data(sp):
    recent_tracks = fetch_recent_tracks(sp)
    top_tracks    = fetch_top_tracks(sp)
    top_artists   = fetch_top_artists(sp)
    repeat_songs  = fetch_repeat_songs(sp)
    top_genres    = fetch_top_genres(recent_tracks, top_artists)

    return {
        "recent_tracks": recent_tracks,
        "top_tracks":    top_tracks,
        "top_artists":   top_artists,
        "repeat_songs":  repeat_songs,
        "top_genres":    top_genres,
    }
