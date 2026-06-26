import aiohttp
from .base import BaseValidator
from ..models import Finding


class CensysValidator(BaseValidator):
    async def validate(self, finding: Finding) -> Finding:
        # Censys uses api_id:secret as basic auth; key format is "api_id:secret"
        try:
            parts = finding.key.split(":", 1)
            if len(parts) == 2:
                api_id, secret = parts
            else:
                api_id, secret = finding.key, ""

            auth = aiohttp.BasicAuth(api_id, secret)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://search.censys.io/api/v1/account",
                    auth=auth,
                ) as resp:
                    finding.validated = resp.status == 200
        except Exception:
            finding.validated = False
        return finding
