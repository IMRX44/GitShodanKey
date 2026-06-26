import asyncio
import shodan as shodan_lib
from .base import BaseValidator
from ..models import Finding


class ShodanValidator(BaseValidator):
    async def validate(self, finding: Finding) -> Finding:
        try:
            loop = asyncio.get_event_loop()
            api = shodan_lib.Shodan(finding.key)
            info = await loop.run_in_executor(None, api.info)
            finding.validated = True
            finding.credits = info.get("query_credits", 0)
            finding.extra_info = {
                "scan_credits": info.get("scan_credits", 0),
                "plan": info.get("plan", ""),
            }
        except Exception:
            finding.validated = False
        return finding
