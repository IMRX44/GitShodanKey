import re
from .base import BaseValidator
from ..models import Finding

AWS_KEY_PATTERN = re.compile(r"^AKIA[A-Z0-9]{16}$")


class AWSValidator(BaseValidator):
    async def validate(self, finding: Finding) -> Finding:
        # Only format-validate to avoid unintended STS calls against real infrastructure
        finding.validated = bool(AWS_KEY_PATTERN.match(finding.key))
        return finding
