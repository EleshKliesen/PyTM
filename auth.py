import base64
import json
import os
import time
import requests

import authConfig
import config


class NadeoAuth:
    def __init__(self):
        self.ubi_app_id = "86263886-327a-4328-ac69-527f0d20a237"
        self.user_agent = authConfig.USERAGENT
        self.files = {
            "live": "NadeoLiveServices.json",
            "core": "NadeoServices.json"
        }

    def _save(self, data, audience):
        data['timestamp'] = time.time()
        with open(self.files[audience], "w") as f:
            json.dump(data, f, indent=4)

    def _get_full_auth(self):
        print("Performing full Ubisoft authentication...")
        creds = base64.b64encode(f"{config.EMAIL}:{config.PASSWORD}".encode()).decode()
        headers = {"Content-Type": "application/json", "Ubi-AppId": self.ubi_app_id, "Authorization": f"Basic {creds}",
                   "User-Agent": self.user_agent}

        res = requests.post("https://public-ubiservices.ubi.com/v3/profiles/sessions", headers=headers)
        res.raise_for_status()
        ticket = res.json().get("ticket")

        # Get both tokens immediately
        auth_url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices"
        n_headers = {"Authorization": f"ubi_v1 t={ticket}", "User-Agent": self.user_agent}

        for aud in ["live", "core"]:
            audience_name = "NadeoLiveServices" if aud == "live" else "NadeoServices"
            r = requests.post(auth_url, headers=n_headers, json={"audience": audience_name})
            self._save(r.json(), aud)

    def get_token(self, audience):
        file_path = self.files[audience]
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                tokens = json.load(f)
            if time.time() - tokens.get('timestamp', 0) < 3300:
                return tokens['accessToken']

            # Try refresh
            print(f"Refreshing {audience} token...")
            refresh_url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/refresh"
            r = requests.post(refresh_url, headers={"Authorization": f"nadeo_v1 t={tokens['refreshToken']}",
                                                    "User-Agent": self.user_agent})
            if r.status_code == 200:
                self._save(r.json(), audience)
                return r.json()['accessToken']

        self._get_full_auth()
        with open(file_path, "r") as f:
            return json.load(f)['accessToken']
