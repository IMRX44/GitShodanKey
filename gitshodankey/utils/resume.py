import json
from pathlib import Path
from ..models import Finding


class ResumeState:
    def save(self, path: str, completed_keywords: list, findings: list[Finding]):
        data = {
            "completed_keywords": completed_keywords,
            "findings": [f.model_dump() for f in findings],
        }
        Path(path).write_text(json.dumps(data, indent=2, default=str))

    def load(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {"completed_keywords": [], "findings": []}
        data = json.loads(p.read_text())
        findings = [Finding(**f) for f in data.get("findings", [])]
        return {
            "completed_keywords": data.get("completed_keywords", []),
            "findings": findings,
        }
