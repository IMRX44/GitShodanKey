import asyncio
import pytest


def test_github_searcher_init():
    from gitshodankey.searchers.github import GitHubSearcher
    s = GitHubSearcher(token="test_token", concurrency=5)
    assert s.token == "test_token"
    asyncio.run(s.close())


def test_gitlab_searcher_init():
    from gitshodankey.searchers.gitlab import GitLabSearcher
    s = GitLabSearcher(token="test_token", concurrency=5)
    assert s.token == "test_token"
    asyncio.run(s.close())


def test_deduplicator():
    from gitshodankey.utils.dedup import Deduplicator
    d = Deduplicator()
    assert not d.is_duplicate("key1")
    d.add("key1")
    assert d.is_duplicate("key1")
    assert not d.is_duplicate("key2")
    assert d.size() == 1
