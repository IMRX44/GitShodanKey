import aiohttp
from ..models import Finding


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    async def notify(self, finding: Finding):
        status = "✅ VALID" if finding.validated else "⚠️ unverified"
        credits_str = f" | {finding.credits} credits" if finding.credits else ""
        text = (
            f"🔑 *[{finding.service.value.upper()}]* Found key\n"
            f"`{finding.masked_key}`\n"
            f"📁 `{finding.repo}`\n"
            f"Status: {status}{credits_str}\n"
            f"🔗 [View File]({finding.source_url})"
        )
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"})
        except Exception:
            pass


class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def notify(self, finding: Finding):
        status = "✅ VALID" if finding.validated else "⚠️ unverified"
        credits_str = f" | {finding.credits} credits" if finding.credits else ""
        color = 0x3fb950 if finding.validated else 0xf85149
        embed = {
            "title": f"🔑 [{finding.service.value.upper()}] Key Found",
            "description": f"`{finding.masked_key}`",
            "color": color,
            "fields": [
                {"name": "Repository", "value": finding.repo, "inline": True},
                {"name": "Status", "value": f"{status}{credits_str}", "inline": True},
                {"name": "File", "value": finding.file_path, "inline": False},
            ],
            "url": finding.source_url,
        }
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.webhook_url, json={"embeds": [embed]})
        except Exception:
            pass
