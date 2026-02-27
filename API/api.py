from API.Services.NadeoCore import NadeoCore
from API.Services.NadeoLive import NadeoLive
from API.Services.TrackmaniaIO import TrackmaniaIO


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
    def io(self) -> TrackmaniaIO:
        if self._io is None:
            self._io = TrackmaniaIO()
        return self._io

    def get_weekly_data(self, club_id, offset=1):
        """Main entry point for main.py to fetch everything at once."""
        print("Fetching Weekly Shorts maps...")
        map_uids, campaign_name = self.live.get_weekly_shorts_uids(offset)
        print(f"Fetched: {campaign_name}")

        if not map_uids:
            return []

        print("Fetching map metadata...")
        map_names = self.core.get_map_names(map_uids)

        print("Fetching Club Member names...")
        member_map = self.io.get_club_members(club_id)
        print(f"Loaded {len(member_map)} members.")

        results = []
        for uid in map_uids:
            display_name = map_names.get(uid, uid)
            records = self.live.get_pb_leaderboard(uid, club_id)
            results.append({
                "name": display_name,
                "records": records,
                "member_map": member_map
            })
        return results
