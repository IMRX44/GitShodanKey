import aiohttp
from .base import BaseValidator
from ..models import Finding


class VirusTotalValidator(BaseValidator):
    async def validate(self, finding: Finding) -> Finding:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"x-apikey": finding.key}
                async with session.get(
                    "https://www.virustotal.com/api/v3/users/user",
                    headers=headers,
                ) as resp:
                    finding.validated = resp.status == 200
        except Exception:
            finding.validated = False
        return finding
