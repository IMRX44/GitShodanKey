import re
import yaml
from pathlib import Path
from ..models import ServiceType, Finding

KEYWORDS_DIR = Path(__file__).parent.parent.parent / "keywords"


class KeyExtractor:
    def __init__(self, services: list[str] = None):
        self.configs = {}
        self._load_configs(services)

    def _load_configs(self, services):
        for yaml_file in KEYWORDS_DIR.glob("*.yaml"):
            config = yaml.safe_load(yaml_file.read_text())
            service = config["service"]
            if services is None or service in services:
                self.configs[service] = config

    def extract(self, content: str, source_url: str, repo: str, file_path: str) -> list[Finding]:
        findings = []
        for service, config in self.configs.items():
            pattern = config["key_regex"]
            try:
                matches = re.findall(pattern, content)
            except re.error:
                continue
            for key in matches:
                try:
                    service_type = ServiceType[service.upper()]
                except KeyError:
                    continue
                findings.append(Finding(
                    service=service_type,
                    key=key,
                    source_url=source_url,
                    repo=repo,
                    file_path=file_path,
                ))
        return findings

    def get_search_patterns(self, service: str) -> list[str]:
        return self.configs.get(service, {}).get("patterns", [])

    def get_language(self, service: str) -> str | None:
        return self.configs.get(service, {}).get("language")

    @property
    def all_services(self) -> list[str]:
        return list(self.configs.keys())
