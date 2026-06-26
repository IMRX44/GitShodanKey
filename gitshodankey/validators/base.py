from abc import ABC, abstractmethod
from ..models import Finding


class BaseValidator(ABC):
    @abstractmethod
    async def validate(self, finding: Finding) -> Finding:
        """Returns updated Finding with validated=True/False and extra_info"""
        pass
