import base64
import json
import os
import time

import requests

import authConfig
import config


class NadeoAuth:
    TOKEN_DIR = "data/tokens/"

    def __init__(self):
        self.ubi_app_id = "86263886-327a-4328-ac69-527f0d20a237"
        self.user_agent = authConfig.USERAGENT
        self.files = {
            "live": os.path.join(self.TOKEN_DIR, "NadeoLiveServices.json"),
            "core": os.path.join(self.TOKEN_DIR, "NadeoServices.json")
        }
        self.ubi_ticket = None

    def _save(self, data, audience):
        data['timestamp'] = time.time()
        with open(self.files[audience], "w") as f:
            json.dump(data, f, indent=4)

    def _get_auth(self, aud):
        # Only perform Ubisoft login if we don't have a ticket yet
        if not self.ubi_ticket:
            print("Performing full Ubisoft authentication...")
            creds = base64.b64encode(f"{config.EMAIL}:{config.PASSWORD}".encode()).decode()
            headers = {
                "Content-Type": "application/json",
                "Ubi-AppId": self.ubi_app_id,
                "Authorization": f"Basic {creds}",
                "User-Agent": self.user_agent
            }

            res = requests.post("https://public-ubiservices.ubi.com/v3/profiles/sessions", headers=headers)
            res.raise_for_status()
            self.ubi_ticket = res.json().get("ticket")

        # Use the ticket to get the specific Nadeo token
        auth_url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/ubiservices"
        n_headers = {"Authorization": f"ubi_v1 t={self.ubi_ticket}", "User-Agent": self.user_agent}

        audience_name = "NadeoLiveServices" if aud == "live" else "NadeoServices"

        try:
            print(f"Getting {audience_name} token")
            r = requests.post(auth_url, headers=n_headers, json={"audience": audience_name})
            r.raise_for_status()
            self._save(r.json(), aud)
        except requests.exceptions.HTTPError as e:
            # If the ticket expired while the script was running, clear it and try once more
            if r.status_code == 401:
                self.ubi_ticket = None
                return self._get_auth(aud)
            raise e

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

        self._get_auth(audience)
        with open(file_path, "r") as f:
            return json.load(f)['accessToken']
