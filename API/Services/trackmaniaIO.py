import requests

import authConfig


class TrackmaniaIO:
    BASE_URL = "https://trackmania.io/api"

    def __init__(self):
        self.headers = {"User-Agent": authConfig.USERAGENT}

    def get_club_members(self, club_id):
        url = f"{self.BASE_URL}/club/{club_id}/members/0"
        r = requests.get(url, headers=self.headers, timeout=10)
        r.raise_for_status()
        return {m['player']['id']: m['player']['name'] for m in r.json().get("members", [])}
