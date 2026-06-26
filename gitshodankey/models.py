from enum import Enum
from typing import Optional
from pydantic import BaseModel, computed_field


class ServiceType(str, Enum):
    SHODAN = "shodan"
    VIRUSTOTAL = "virustotal"
    CENSYS = "censys"
    AWS = "aws"
    STRIPE = "stripe"
    OPENAI = "openai"
    SLACK = "slack"
    TWILIO = "twilio"
    SENDGRID = "sendgrid"
    TELEGRAM = "telegram"
    GITHUB_TOKEN = "github_token"


class Finding(BaseModel):
    service: ServiceType
    key: str
    source_url: str
    repo: str
    file_path: str
    validated: bool = False
    credits: Optional[int] = None
    extra_info: dict = {}

    @computed_field
    @property
    def masked_key(self) -> str:
        if len(self.key) <= 10:
            return self.key[:2] + "***"
        return self.key[:6] + "***" + self.key[-4:]


class ScanResult(BaseModel):
    findings: list[Finding]
    total_found: int
    total_validated: int
    scan_duration: float
    services_scanned: list[str]
