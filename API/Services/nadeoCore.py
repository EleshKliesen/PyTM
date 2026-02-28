import json
import os

import requests

from API.Services.nadeoService import NadeoService


class NadeoCore(NadeoService):
    BASE_URL = "https://prod.trackmania.core.nadeo.online"

    def update_cache_metadata(self, campaign_name, map_names):
        """Injects map names into an existing cache entry."""
        cache_file = os.path.join(self.CACHE_DIR, "WeeklyShortsCache.json")
        if not os.path.exists(cache_file):
            return

        with open(cache_file, "r") as f:
            all_weeks = json.load(f)

        updated = False
        for week in all_weeks:
            if week.get("campaign_name") == campaign_name:
                week["map_names"] = map_names
                updated = True
                break

        if updated:
            with open(cache_file, "w") as f:
                json.dump(all_weeks, f, indent=4)

    def get_map_names(self, uids):
        """Fetches map names for a list of UIDs and returns a UID -> Name mapping."""
        if not uids:
            return {}

        uid_list_str = ",".join(uids)
        url = f"{self.BASE_URL}/maps/by-uid/?mapUidList={uid_list_str}"

        try:
            r = requests.get(url, headers=self.get_headers(), timeout=10)
            r.raise_for_status()
            # Clean names while building the dictionary
            return {m['mapUid']: self.clean_name(m.get('name')) for m in r.json()}
        except Exception as e:
            print(f"Core API Error: {e}")
            return {}
