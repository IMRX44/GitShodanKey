import csv
import json
import io
from ..models import Finding


class JsonFormatter:
    def format(self, findings: list[Finding]) -> str:
        return json.dumps([f.model_dump() for f in findings], indent=2, default=str)


class CsvFormatter:
    def format(self, findings: list[Finding]) -> str:
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["service", "masked_key", "key", "repo", "file_path", "source_url", "validated", "credits"])
        for f in findings:
            writer.writerow([f.service.value, f.masked_key, f.key, f.repo, f.file_path, f.source_url, f.validated, f.credits or ""])
        return out.getvalue()


class TxtFormatter:
    def format(self, findings: list[Finding]) -> str:
        lines = []
        for f in findings:
            status = "VALID" if f.validated else "unverified"
            credits_str = f" | credits={f.credits}" if f.credits is not None else ""
            lines.append(f"[{f.service.value.upper()}] {f.masked_key} | {f.repo} | {status}{credits_str}")
            lines.append(f"  URL: {f.source_url}")
        return "\n".join(lines)


def get_formatter(fmt: str):
    return {"json": JsonFormatter, "csv": CsvFormatter, "txt": TxtFormatter}.get(fmt, TxtFormatter)()
