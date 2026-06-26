import aiohttp
from .base import BaseValidator
from ..models import Finding


class StripeValidator(BaseValidator):
    async def validate(self, finding: Finding) -> Finding:
        try:
            headers = {"Authorization": f"Bearer {finding.key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.stripe.com/v1/account",
                    headers=headers,
                ) as resp:
                    finding.validated = resp.status == 200
        except Exception:
            finding.validated = False
        return finding
