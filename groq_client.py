import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# ── Genre inference ────────────────────────────────────────────────────────────

def fetch_top_genres(recent_tracks, top_artists):
    # Spotify's genre API is broken for most artists so we ask Groq to infer
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""
Based on these recently played songs and top artists, list the user's top 5 music genres.
Return ONLY a simple numbered list of genres, nothing else. No intro, no explanation.

Recently played:
{chr(10).join(f"- {t}" for t in recent_tracks[:50])}

Top artists:
{chr(10).join(f"- {a}" for a in top_artists)}
"""
        }]
    )

    genres = []
    for line in response.choices[0].message.content.strip().splitlines():
        cleaned = line.strip().lstrip("0123456789.)- ").strip()
        if cleaned:
            genres.append(cleaned)

    return genres[:5]


# ── Music assistant ────────────────────────────────────────────────────────────

def ask_music_assistant(user_prompt, spotify_data):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    repeat_section = (
        chr(10).join(f"- {t}" for t in spotify_data["repeat_songs"])
        if spotify_data["repeat_songs"]
        else "- No repeated songs detected in last 50 plays"
    )

    context = f"""
You are a personalized music assistant with deep knowledge of music.

Here is the user's Spotify data:

Recently played (last 50 songs):
{chr(10).join(f"- {t}" for t in spotify_data["recent_tracks"])}

Top tracks (last 6 months):
{chr(10).join(f"- {t}" for t in spotify_data["top_tracks"])}

Top artists (last 6 months):
{chr(10).join(f"- {a}" for a in spotify_data["top_artists"])}

Top genres:
{chr(10).join(f"- {g}" for g in spotify_data["top_genres"]) if spotify_data["top_genres"] else "- Not available"}

Most repeated songs recently:
{repeat_section}

RESPONSE FORMATTING RULES — always follow these:
- If recommending songs, list each one as:
  🎵 Song Name - Artist Name
     Why: One sentence explaining why it fits their taste based on their Spotify data.

- If recommending a playlist or group around a theme, start with the theme name then list songs underneath in the same format.

- If answering a general question (not a list of songs), respond conversationally in short clear paragraphs. No bullet points unless it genuinely helps.

- Never give a wall of text. Keep it scannable and easy to read.
- Always tie recommendations back to something specific in their listening history.
- Be conversational, not robotic. Talk like a friend who knows their music taste really well.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": context},
            {"role": "user",   "content": user_prompt},
        ],
    )

    return response.choices[0].message.content
