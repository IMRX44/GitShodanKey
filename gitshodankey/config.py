import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(
        self,
        github_token: Optional[str] = None,
        gitlab_token: Optional[str] = None,
        services: Optional[list] = None,
        concurrency: int = 10,
        output_file: str = "results",
        output_format: str = "html",
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_webhook_url: Optional[str] = None,
        resume_file: str = ".gitshodankey_resume.json",
    ):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.gitlab_token = gitlab_token or os.environ.get("GITLAB_TOKEN")
        self.services = services
        self.concurrency = concurrency
        self.output_file = output_file
        self.output_format = output_format
        self.telegram_token = telegram_token or os.environ.get("TELEGRAM_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self.discord_webhook_url = discord_webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
        self.resume_file = resume_file

    @classmethod
    def from_file(cls, path: str) -> "Config":
        data = yaml.safe_load(Path(path).read_text())
        return cls(
            github_token=data.get("github_token"),
            gitlab_token=data.get("gitlab_token"),
            services=data.get("services"),
            concurrency=data.get("concurrency", 10),
            output_file=data.get("output_file", "results"),
            output_format=data.get("output_format", "html"),
            telegram_token=data.get("telegram_token"),
            telegram_chat_id=data.get("telegram_chat_id"),
            discord_webhook_url=data.get("discord_webhook_url"),
            resume_file=data.get("resume_file", ".gitshodankey_resume.json"),
        )
