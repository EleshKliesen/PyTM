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
        self._token_cache = {}
        self.ubi_ticket = None
        os.makedirs(self.TOKEN_DIR, exist_ok=True)

    def _save(self, data, audience):
        """Updates memory cache and saves to disk."""
        data['timestamp'] = time.time()
        self._token_cache[audience] = data

        file_path = self.files[audience]
        with open(file_path, "w") as f:
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
            auth_data = r.json()
            self._save(auth_data, aud)
            return auth_data['accessToken']
        except requests.exceptions.HTTPError as e:
            # If the ticket expired while the script was running, clear it and try once more
            if r.status_code == 401:
                self.ubi_ticket = None
                return self._get_auth(aud)
            raise e

    def get_token(self, audience):
        token_data = self._load_token(audience)

        # 1. Check if the in-memory/loaded token is still valid (3300s = 55 mins)
        if token_data and (time.time() - token_data.get('timestamp', 0) < 3300):
            return token_data['accessToken']

        # 2. Token is expired or missing - Try to refresh
        if token_data and 'refreshToken' in token_data:
            new_tokens = self._refresh_token(audience, token_data['refreshToken'])
            if new_tokens:
                return new_tokens['accessToken']

        # 3. Else Perform full login
        print(f"Token required for {audience}...")
        return self._get_auth(audience)

    def _load_token(self, audience):
        """Checks memory first, then disk."""
        # Check in-memory cache first
        if audience in self._token_cache:
            return self._token_cache[audience]

        # Check disk if not in memory
        file_path = self.files.get(audience)
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self._token_cache[audience] = data
                    return data
            except (json.JSONDecodeError, IOError):
                pass
        return None

    def _refresh_token(self, audience, refresh_token):
        """Attempts to use the refresh token to get a new access token."""
        print(f"Refreshing {audience} token...")
        url = "https://prod.trackmania.core.nadeo.online/v2/authentication/token/refresh"
        try:
            r = requests.post(
                url,
                headers={
                    "Authorization": f"nadeo_v1 t={refresh_token}",
                    "User-Agent": self.user_agent
                },
                timeout=10
            )
            if r.status_code == 200:
                new_data = r.json()
                self._save(new_data, audience)
                return new_data
            else:
                print(f"Refresh failed with status: {r.status_code}")
                return None
        except Exception as e:
            print(f"Refresh failed: {e}")
        return None
