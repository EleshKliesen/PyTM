import datetime
import json
import os
import time

import requests

from API.Services.nadeoService import NadeoService


class NadeoLive(NadeoService):
    BASE_URL = "https://live-services.trackmania.nadeo.live/api"

    @staticmethod
    def _get_next_monday_jst():
        """Calculates the next Monday at 3 AM JST for cache expiration."""
        # JST is UTC+9
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        # Calculate days until next Monday (Monday is 0)
        days_ahead = (0 - now.weekday()) % 7
        if days_ahead == 0 and now.hour >= 3:
            days_ahead = 7

        next_monday = now.replace(hour=3, minute=0, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
        return next_monday.timestamp()

    def get_club_by_id(self, club='mine'):
        """Fetches the ID of the club the authenticated user is in."""
        # The URL remains the same
        url = f"{self.BASE_URL}/token/club/{club}"

        try:
            r = requests.get(url, headers=self.get_headers(), params={"length": 1, "offset": 0}, timeout=10)
            r.raise_for_status()

            clubs = r.json().get("clubList", [])
            if clubs:
                club_id = clubs[0].get("id")
                club_name = self.clean_name(clubs[0].get("name"))
                print(f"Found Club Name: {club_name}, Club ID: {club_id}")
                return club_id

            print("No clubs found for this account.")
            return None
        except Exception as e:
            print(f"Live API Error (Club Lookup): {e}")
            return None

    def get_weekly_shorts(self, length=1, offset=1):
        """Fetches the campaign data dictionary, using/updating the local cache."""
        cache_file = os.path.join(self.CACHE_DIR, "WeeklyShortsCache.json")
        all_weeks = []
        offset_time = time.time() - offset * 604800

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    all_weeks = json.load(f)

                if all_weeks:
                    all_weeks.sort(key=lambda x: x.get('start', 0), reverse=True)
                    for week in all_weeks:
                        if week.get('startTimestamp', 0) <= offset_time <= week.get('endTimestamp', 0):
                            print(f"Campaign ({week['campaign_name']}) found in cache.")
                            return week
            except (json.JSONDecodeError, KeyError):
                all_weeks = []

        print(f"Fetching Weekly Shorts (Offset: {offset})...")
        url = f"{self.BASE_URL}/campaign/weekly-shorts"
        try:
            r = requests.get(url, headers=self.get_headers(), params={"length": length, "offset": offset}, timeout=10)
            r.raise_for_status()
            campaigns = r.json().get("campaignList", [])

            if not campaigns:
                return {}

            campaign_data = campaigns[0]
            new_entry = {
                "startTimestamp": campaign_data.get("startTimestamp", 0),
                "endTimestamp": campaign_data.get("endTimestamp", 0),
                "campaign_name": self.clean_name(campaign_data.get("name", "Unknown Week")),
                "uids": [m['mapUid'] for m in campaign_data.get("playlist", [])],
                "map_names": {}
            }

            all_weeks = [w for w in all_weeks if w['campaign_name'] != new_entry["campaign_name"]]
            all_weeks.append(new_entry)
            all_weeks.sort(key=lambda x: x.get('start', 0), reverse=True)

            with open(cache_file, "w") as f:
                json.dump(all_weeks, f, indent=4)

            return new_entry
        except Exception as e:
            print(f"Live API Error: {e}")
            return {}

    def get_leaderboard(self, map_uid, club_id, group="Personal_Best", length=100, offset=0):
        """Generic leaderboard fetcher with customizable parameters."""
        url = f"{self.BASE_URL}/token/leaderboard/group/{group}/map/{map_uid}/club/{club_id}/top"
        try:
            r = requests.get(
                url,
                headers=self.get_headers(),
                params={"length": length, "offset": offset},
                timeout=10
            )
            r.raise_for_status()
            return r.json().get("top", [])
        except Exception as e:
            print(f"Leaderboard API Error ({group}): {e}")
            return []

    def get_pb_leaderboard(self, map_uid, club_id, length=100, offset=0):
        """Shortcut for the Personal_Best group."""
        return self.get_leaderboard(map_uid, club_id, "Personal_Best", length, offset)
