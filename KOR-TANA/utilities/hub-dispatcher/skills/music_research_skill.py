import logging
import random
from typing import Any, Dict, List
from kortana_hub.autonomous_skill_base import AutonomousSkill


class MusicResearchSkill(AutonomousSkill):
    """Autonomous skill for researching music trends, new releases, and artist info.

    Fetches data from simulated APIs (Billboard, Pitchfork), analyzes for insights,
    posts results to Hub queue, and persists findings.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def run_periodic(self, hub, memory, config: Dict[str, Any]) -> None:
        """Perform periodic music research if network is allowed."""
        if not config.get("allow_network", False):
            self.logger.info("Network access not allowed, skipping music research.")
            return

        self.logger.info("Starting music research cycle.")

        try:
            # Fetch data from mock APIs
            billboard_data = self._fetch_billboard_top_100()
            pitchfork_data = self._fetch_pitchfork_reviews()

            # Analyze data for insights
            insights = self._analyze_data(billboard_data, pitchfork_data)

            # Post insights to Hub queue as intent
            hub.input_queue.put_nowait(("music_research", {"insights": insights}))

            # Persist findings
            summary = f"Music Research Insights: {insights}"
            memory.add_note(text=summary, source="music_research")

            self.logger.info("Music research completed and posted.")

        except Exception as e:
            self.logger.error(f"Error in music research: {e}")
            memory.add_note(text=f"Music research error: {e}", source="music_research")

    def _fetch_billboard_top_100(self) -> List[Dict[str, Any]]:
        """Simulate fetching top 100 songs from Billboard API."""
        genres = ["Pop", "Hip-Hop", "Rock", "Country", "Electronic", "R&B", "Indie"]
        artists = ["Artist" + str(i) for i in range(1, 21)]
        songs = ["Song" + str(i) for i in range(1, 101)]

        data = []
        for i in range(100):
            data.append({
                "rank": i + 1,
                "artist": random.choice(artists),
                "song": random.choice(songs),
                "genre": random.choice(genres)
            })
        return data

    def _fetch_pitchfork_reviews(self) -> List[Dict[str, Any]]:
        """Simulate fetching recent reviews from Pitchfork API."""
        artists = ["Artist" + str(i) for i in range(1, 21)]
        albums = ["Album" + str(i) for i in range(1, 51)]

        data = []
        for _ in range(20):
            data.append({
                "artist": random.choice(artists),
                "album": random.choice(albums),
                "score": round(random.uniform(5.0, 10.0), 1),
                "is_new": random.choice([True, False])
            })
        return data

    def _analyze_data(self, billboard: List[Dict[str, Any]], pitchfork: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze fetched data for music insights."""
        insights = {}

        # Trending genres from Billboard
        genre_counts = {}
        for song in billboard:
            genre = song["genre"]
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        insights["trending_genres"] = top_genres

        # Emerging artists from Pitchfork (high scores on new albums)
        emerging = []
        for review in pitchfork:
            if review["is_new"] and review["score"] >= 8.0:
                emerging.append({
                    "artist": review["artist"],
                    "album": review["album"],
                    "score": review["score"]
                })
        insights["emerging_artists"] = emerging[:5]  # Top 5

        # Top artists overall
        artist_counts = {}
        for song in billboard:
            artist = song["artist"]
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
        top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        insights["top_artists"] = top_artists

        return insights