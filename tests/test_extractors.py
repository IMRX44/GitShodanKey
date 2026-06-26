import pytest
from gitshodankey.extractors.key_extractor import KeyExtractor
from gitshodankey.models import ServiceType


def test_extract_aws_key():
    extractor = KeyExtractor(["aws"])
    content = 'aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"'
    findings = extractor.extract(content, "https://github.com/x/y/blob/main/f.py", "x/y", "f.py")
    assert any(f.service == ServiceType.AWS for f in findings)
    assert any(f.key == "AKIAIOSFODNN7EXAMPLE" for f in findings)


def test_extract_shodan_key():
    extractor = KeyExtractor(["shodan"])
    fake_key = "a" * 32
    content = f'shodan_api_key = "{fake_key}"'
    findings = extractor.extract(content, "https://github.com/x/y/blob/main/f.py", "x/y", "f.py")
    assert any(f.key == fake_key for f in findings)


def test_extract_openai_key():
    extractor = KeyExtractor(["openai"])
    content = 'OPENAI_API_KEY = "sk-' + "A" * 48 + '"'
    findings = extractor.extract(content, "https://github.com/x/y/blob/main/f.py", "x/y", "f.py")
    assert any(f.service == ServiceType.OPENAI for f in findings)


def test_no_false_positives():
    extractor = KeyExtractor(["aws"])
    content = "nothing interesting here"
    findings = extractor.extract(content, "url", "repo", "file")
    assert findings == []


def test_masked_key():
    extractor = KeyExtractor(["shodan"])
    fake_key = "abcdef1234567890abcdef1234567890"
    content = f'shodan_key = "{fake_key}"'
    findings = extractor.extract(content, "url", "repo", "file")
    if findings:
        assert findings[0].masked_key.startswith("abcdef")
        assert "***" in findings[0].masked_key
