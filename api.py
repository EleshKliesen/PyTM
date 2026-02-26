import datetime
import json
import os
import time

import requests
import re

import authConfig


class TrackmaniaAPI:
    def __init__(self):
        self.headers_base = {
            "User-Agent": authConfig.USERAGENT,
            "Accept": "application/json"
        }

    # --- UTILS ---
    @staticmethod
    def clean_name(name):
        """Removes Trackmania color/format codes like $f00 or $i."""
        if not name:
            return name
        return re.sub(r'\$([0-9a-fA-F]{3}|[iIswntgzjGLS<>]|[oO]|\$)', '', name)

    # --- NADEO CORE SERVICES (Official) ---
    def get_map_names(self, core_token, uids):
        """Fetches map names for a list of UIDs and returns a UID -> Name mapping."""
        if not uids:
            return {}

        uid_list_str = ",".join(uids)
        url = f"https://prod.trackmania.core.nadeo.online/maps/by-uid/?mapUidList={uid_list_str}"
        headers = {**self.headers_base, "Authorization": f"nadeo_v1 t={core_token}"}

        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return {m.get('mapUid'): self.clean_name(m.get('name')) for m in data if m.get('mapUid')}
            return {}
        except Exception as e:
            print(f"Core API Error (Maps): {e}")
            return {}

    # --- NADEO LIVE SERVICES (Official) ---
    def get_my_club_id(self, live_token):
        """Fetches the ID of the first club the authenticated user is in."""
        url = "https://live-services.trackmania.nadeo.live/api/token/club/mine"
        headers = {**self.headers_base, "Authorization": f"nadeo_v1 t={live_token}"}

        try:
            r = requests.get(url, headers=headers, params={"length": 1, "offset": 0}, timeout=10)
            r.raise_for_status()
            clubs = r.json().get("clubList", [])
            return clubs[0].get("id") if clubs else None
        except Exception as e:
            print(f"Live API Error (Club Lookup): {e}")
            return None

    def get_weekly_shorts_uids(self, live_token):
        """
        Fetches Weekly Shorts UIDs.
        Only calls the API if the current time is past Monday 3AM JST.
        """
        cache_file = "WeeklyShortsCache.json"
        now = time.time()

        # 1. Load Cache and Check Timestamp
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cache = json.load(f)

            # If we haven't reached the reset time yet, return cached data
            if now < cache.get("next_reset", 0):
                print(f"Cache Valid. Next reset: {time.ctime(cache['next_reset'])}")
                return cache.get("map_uids", [])

        # 2. If expired or no cache, make the API CALL
        print("Cache expired or missing. Fetching new Weekly Shorts...")
        url = "https://live-services.trackmania.nadeo.live/api/campaign/weekly-shorts"
        headers = {**self.headers_base, "Authorization": f"nadeo_v1 t={live_token}"}

        try:
            r = requests.get(url, headers=headers, params={"offset": 1, "length": 1}, timeout=10)
            r.raise_for_status()
            campaigns = r.json().get("campaignList", [])

            if not campaigns:
                return []

            # 3. Calculate Next Monday 3 AM JST
            # JST is UTC+9. 3 AM JST is 6 PM UTC (Sunday).
            current_date = datetime.datetime.now(datetime.timezone.utc)
            # Days until next Sunday (weekday 6)
            days_ahead = (6 - current_date.weekday()) % 7
            if days_ahead == 0 and current_date.hour >= 18:
                days_ahead = 7

            next_reset_dt = current_date.replace(hour=18, minute=0, second=0, microsecond=0) + datetime.timedelta(
                days=days_ahead)
            next_reset_ts = next_reset_dt.timestamp()

            # 4. Save to Cache
            playlist = campaigns[0].get("playlist", [])
            map_uids = [item.get("mapUid") for item in playlist]

            new_cache = {
                "next_reset": next_reset_ts,
                "map_uids": map_uids,
                "campaign_name": campaigns[0].get("name")
            }

            with open(cache_file, "w") as f:
                json.dump(new_cache, f, indent=4)

            return map_uids

        except Exception as e:
            print(f"API Error: {e}. Falling back to old cache if available.")
            return cache.get("map_uids", []) if 'cache' in locals() else []

    def get_pb_leaderboard(self, live_token, club_id, map_uid):
        """Returns the raw top records list for Personal Bests."""
        return self.get_leaderboard(live_token, club_id, "Personal_Best", map_uid)

    def get_leaderboard(self, live_token, club_id, group, map_uid):
        """Fetches raw leaderboard JSON and returns the 'top' list."""
        url = (
            "https://live-services.trackmania.nadeo.live/api/token/leaderboard/"
            f"group/{group}/map/{map_uid}/club/{club_id}/top"
        )
        headers = {**self.headers_base, "Authorization": f"nadeo_v1 t={live_token}"}
        try:
            r = requests.get(url, headers=headers, params={"length": 100, "offset": 0}, timeout=10)
            r.raise_for_status()
            return r.json().get("top", [])
        except Exception as e:
            print(f"Leaderboard API Error: {e}")
            return []

    # --- TRACKMANIA.IO SERVICES (Community) ---
    def get_club_members(self, club_id):
        """Uses Trackmania.io to map Account IDs to display names for a club."""
        url = f"https://trackmania.io/api/club/{club_id}/members/0"
        try:
            r = requests.get(url, headers=self.headers_base, timeout=10)
            r.raise_for_status()

            # Change this to members_data (or whatever you prefer)
            members_data = r.json().get("members", [])

            # Ensure we use members_data here too
            return {
                m['player']['id']: m['player']['name']
                for m in members_data
                if 'player' in m
            }
        except Exception as e:
            print(f"Trackmania.io Error: {e}")
            return
