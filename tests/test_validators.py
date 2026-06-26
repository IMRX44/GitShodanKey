import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from gitshodankey.models import Finding, ServiceType


def make_finding(service=ServiceType.SHODAN, key="a" * 32):
    return Finding(service=service, key=key, source_url="https://x.com", repo="x/y", file_path="f.py")


def test_aws_validator_valid_format():
    from gitshodankey.validators.aws import AWSValidator
    v = AWSValidator()
    f = make_finding(ServiceType.AWS, "AKIAIOSFODNN7EXAMPLE")
    result = asyncio.run(v.validate(f))
    assert result.validated is True


def test_aws_validator_invalid_format():
    from gitshodankey.validators.aws import AWSValidator
    v = AWSValidator()
    f = make_finding(ServiceType.AWS, "notanawskey")
    result = asyncio.run(v.validate(f))
    assert result.validated is False


@pytest.mark.asyncio
async def test_virustotal_validator_mocked():
    from gitshodankey.validators.virustotal import VirusTotalValidator
    v = VirusTotalValidator()
    f = make_finding(ServiceType.VIRUSTOTAL, "a" * 64)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await v.validate(f)
    assert result.validated is True
