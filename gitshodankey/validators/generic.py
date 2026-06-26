import aiohttp
from .base import BaseValidator
from ..models import Finding, ServiceType

# Validation endpoints for services without dedicated validators
_ENDPOINTS = {
    ServiceType.SLACK: {
        "url": "https://slack.com/api/auth.test",
        "method": "POST",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    ServiceType.TWILIO: {
        "url": "https://api.twilio.com/2010-04-01/Accounts.json",
        "method": "GET",
        # Twilio API key alone cannot authenticate; format check only
        "headers": lambda key: {},
        "format_only": True,
    },
    ServiceType.SENDGRID: {
        "url": "https://api.sendgrid.com/v3/user/profile",
        "method": "GET",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
    },
    ServiceType.TELEGRAM: {
        "url": "https://api.telegram.org/bot{key}/getMe",
        "method": "GET",
        "headers": lambda key: {},
        "url_template": True,
    },
    ServiceType.GITHUB_TOKEN: {
        "url": "https://api.github.com/user",
        "method": "GET",
        "headers": lambda key: {"Authorization": f"token {key}"},
    },
}


class GenericValidator(BaseValidator):
    async def validate(self, finding: Finding) -> Finding:
        config = _ENDPOINTS.get(finding.service)
        if not config:
            finding.validated = False
            return finding

        if config.get("format_only"):
            finding.validated = True
            return finding

        try:
            url = config["url"]
            if config.get("url_template"):
                url = url.replace("{key}", finding.key)

            headers = config["headers"](finding.key)
            method = config.get("method", "GET")

            async with aiohttp.ClientSession() as session:
                req = session.get if method == "GET" else session.post
                async with req(url, headers=headers) as resp:
                    finding.validated = resp.status == 200
        except Exception:
            finding.validated = False
        return finding
