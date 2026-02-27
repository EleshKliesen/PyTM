import requests

from API.Services.NadeoService import NadeoService


class NadeoCore(NadeoService):
    BASE_URL = "https://prod.trackmania.core.nadeo.online"

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
