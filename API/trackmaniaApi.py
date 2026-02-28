from concurrent.futures import ThreadPoolExecutor

from API.Services.nadeoCore import NadeoCore
from API.Services.nadeoLive import NadeoLive
from API.Services.nadeoMeet import NadeoMeet
from API.Services.trackmaniaIO import TrackmaniaIO


class TrackmaniaAPI:
    def __init__(self, auth_provider):
        self._auth = auth_provider
        self._core = None
        self._live = None
        self._io = None

    @property
    def core(self) -> NadeoCore:
        if self._core is None:
            # Service is only created when first accessed
            self._core = NadeoCore(self._auth, "core")
        return self._core

    @property
    def live(self) -> NadeoLive:
        if self._live is None:
            self._live = NadeoLive(self._auth, "live")
        return self._live

    @property
    def meet(self) -> NadeoMeet:
        if self._live is None:
            self._live = NadeoMeet(self._auth, "live")
        return self._live

    @property
    def io(self) -> TrackmaniaIO:
        if self._io is None:
            self._io = TrackmaniaIO()
        return self._io

    def get_weekly_data(self, club_id, offset=1):
        """Main entry point for main.py to fetch everything at once."""
        print("Fetching Weekly Shorts maps...")
        campaign = self.live.get_weekly_shorts(offset=offset)
        if not campaign:
            print("No campaign found for the given offset.")
            return []

        campaign_name = campaign['campaign_name']
        print(f"Fetched: {campaign_name}")

        uids = campaign.get("uids", [])
        map_names = campaign.get("map_names", {})

        if not map_names:
            print("Fetching map metadata...")
            map_names = self.core.get_map_names(uids)
            self.core.update_cache_metadata(campaign_name, map_names)

        print("Fetching Club Member names...")
        member_map = self.io.get_club_members(club_id)
        print(f"Loaded {len(member_map)} members.")

        def fetch_task(uid):
            display_name = map_names.get(uid, uid)
            records = self.live.get_pb_leaderboard(uid, club_id)
            return {
                "name": display_name,
                "records": records,
                "member_map": member_map
            }

        # Use a thread pool to hit the API in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(fetch_task, uids))

        return results
