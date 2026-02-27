import os
import re

import authConfig


class NadeoService:
    CACHE_DIR = os.path.join("data", "cache")

    def __init__(self, auth_provider, audience):
        self.auth = auth_provider
        self.audience = audience
        self.user_agent = authConfig.USERAGENT

    def get_headers(self):
        """Fetches fresh tokens from your NadeoAuth class."""
        token = self.auth.get_token(self.audience)
        return {
            "Authorization": f"nadeo_v1 t={token}",
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }

    @staticmethod
    def clean_name(name):
        """Removes Trackmania color/format codes like $f00 or $i."""
        if not name:
            return name
        return re.sub(r'\$([0-9a-fA-F]{3}|[iIswntgzjGLS<>]|[oO]|\$)', '', name)
