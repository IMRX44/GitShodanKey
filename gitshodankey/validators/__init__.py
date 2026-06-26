from .shodan import ShodanValidator
from .virustotal import VirusTotalValidator
from .censys import CensysValidator
from .aws import AWSValidator
from .stripe import StripeValidator
from .openai_val import OpenAIValidator
from .generic import GenericValidator
from ..models import ServiceType

VALIDATOR_MAP = {
    ServiceType.SHODAN: ShodanValidator,
    ServiceType.VIRUSTOTAL: VirusTotalValidator,
    ServiceType.CENSYS: CensysValidator,
    ServiceType.AWS: AWSValidator,
    ServiceType.STRIPE: StripeValidator,
    ServiceType.OPENAI: OpenAIValidator,
    ServiceType.SLACK: GenericValidator,
    ServiceType.TWILIO: GenericValidator,
    ServiceType.SENDGRID: GenericValidator,
    ServiceType.TELEGRAM: GenericValidator,
    ServiceType.GITHUB_TOKEN: GenericValidator,
}

def get_validator(service_type: ServiceType):
    cls = VALIDATOR_MAP.get(service_type, GenericValidator)
    return cls()
