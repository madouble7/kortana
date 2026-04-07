"""Tests for cache.py - Redis-based caching layer"""
from unittest.mock import MagicMock

import fakeredis
import pytest

from src.kortana.cache import (
    CacheConfig,
    CacheManager,
    CacheMetrics,
    cache_key,
    cache_result,
    cache_result_async,
    get_cache_manager,
)


class TestCacheConfig:
    def test_defaults(self):
        config = CacheConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.ttl == 300
        assert config.enabled is True

    def test_from_env_defaults(self, monkeypatch):
        monkeypatch.delenv("REDIS_HOST", raising=False)
        monkeypatch.delenv("REDIS_PORT", raising=False)
        monkeypatch.delenv("REDIS_DB", raising=False)
        monkeypatch.delenv("REDIS_PASSWORD", raising=False)
        monkeypatch.delenv("CACHE_TTL", raising=False)
        monkeypatch.delenv("CACHE_ENABLED", raising=False)
        config = CacheConfig.from_env()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.enabled is True

    def test_from_env_custom(self, monkeypatch):
        monkeypatch.setenv("REDIS_HOST", "redishost")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB", "1")
        monkeypatch.setenv("REDIS_PASSWORD", "secret")
        monkeypatch.setenv("CACHE_TTL", "600")
        monkeypatch.setenv("CACHE_ENABLED", "false")
        config = CacheConfig.from_env()
        assert config.host == "redishost"
        assert config.port == 6380
        assert config.db == 1
        assert config.password == "secret"
        assert config.ttl == 600
        assert config.enabled is False


class TestCacheMetrics:
    def test_initial_state(self):
        m = CacheMetrics()
        assert m.hits == 0
        assert m.misses == 0
        assert m.errors == 0
        assert m.evictions == 0

    def test_hit_rate_zero(self):
        m = CacheMetrics()
        assert m.hit_rate() == 0.0

    def test_hit_rate_calculation(self):
        m = CacheMetrics()
        m.hits = 3
        m.misses = 1
        assert m.hit_rate() == 75.0

    def test_avg_get_time_zero(self):
        m = CacheMetrics()
        assert m.avg_get_time() == 0.0

    def test_avg_set_time_zero(self):
        m = CacheMetrics()
        assert m.avg_set_time() == 0.0

    def test_avg_times_with_data(self):
        m = CacheMetrics()
        m.hits = 2
        m.misses = 2
        m.total_get_time = 0.4
        m.total_set_time = 0.2
        assert m.avg_get_time() == 0.1
        assert m.avg_set_time() == 0.05

    def test_to_dict(self):
        m = CacheMetrics()
        m.hits = 5
        m.misses = 5
        d = m.to_dict()
        assert "hits" in d
        assert "misses" in d
        assert "errors" in d
        assert "hit_rate" in d
        assert d["hits"] == 5
        assert d["hit_rate"] == 50.0


class TestCacheManagerDisabled:
    """Tests for CacheManager when caching is disabled"""

    def setup_method(self):
        config = CacheConfig()
        config.enabled = False
        self.cache = CacheManager(config)

    def test_get_returns_none_when_disabled(self):
        result = self.cache.get("key")
        assert result is None

    def test_set_returns_false_when_disabled(self):
        result = self.cache.set("key", "value")
        assert result is False

    def test_delete_returns_false_when_disabled(self):
        result = self.cache.delete("key")
        assert result is False

    def test_clear_returns_zero_when_disabled(self):
        result = self.cache.clear()
        assert result == 0

    def test_is_available_returns_false_when_disabled(self):
        assert self.cache.is_available() is False

    def test_get_metrics_returns_dict(self):
        m = self.cache.get_metrics()
        assert isinstance(m, dict)
        assert "hits" in m

    def test_generate_key(self):
        key = self.cache.generate_key("prefix", "arg1", kw1="v1")
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hex digest

    def test_generate_key_deterministic(self):
        k1 = self.cache.generate_key("prefix", "arg1")
        k2 = self.cache.generate_key("prefix", "arg1")
        assert k1 == k2

    def test_generate_key_different_for_different_args(self):
        k1 = self.cache.generate_key("prefix", "arg1")
        k2 = self.cache.generate_key("prefix", "arg2")
        assert k1 != k2

    @pytest.mark.asyncio
    async def test_async_get_returns_none_when_disabled(self):
        result = await self.cache.async_get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_set_returns_false_when_disabled(self):
        result = await self.cache.async_set("key", "value")
        assert result is False

    @pytest.mark.asyncio
    async def test_async_delete_returns_false_when_disabled(self):
        result = await self.cache.async_delete("key")
        assert result is False


class TestCacheManagerWithFakeRedis:
    """Tests for CacheManager with a fake Redis backend"""

    def setup_method(self):
        """Set up cache with fakeredis"""
        config = CacheConfig()
        config.enabled = True
        self.config = config
        self.fake_redis = fakeredis.FakeRedis(decode_responses=True)

    def _make_cache(self):
        cache = CacheManager(self.config)
        cache._client = self.fake_redis
        return cache

    def test_set_and_get(self):
        cache = self._make_cache()
        cache.set("mykey", {"data": "hello"}, ttl=60)
        result = cache.get("mykey")
        assert result == {"data": "hello"}

    def test_get_miss(self):
        cache = self._make_cache()
        result = cache.get("nonexistent")
        assert result is None

    def test_set_and_delete(self):
        cache = self._make_cache()
        cache.set("delkey", "value", ttl=60)
        deleted = cache.delete("delkey")
        assert deleted is True
        assert cache.get("delkey") is None

    def test_delete_nonexistent(self):
        cache = self._make_cache()
        result = cache.delete("nothere")
        assert result is False

    def test_clear_pattern(self):
        cache = self._make_cache()
        cache.set("k1", "v1", ttl=60)
        cache.set("k2", "v2", ttl=60)
        count = cache.clear("k*")
        assert count == 2

    def test_clear_no_keys(self):
        cache = self._make_cache()
        count = cache.clear("z*")
        assert count == 0

    def test_metrics_tracking_on_hit(self):
        cache = self._make_cache()
        cache.set("mkey", "mval", ttl=60)
        cache.get("mkey")
        assert cache.metrics.hits == 1
        assert cache.metrics.misses == 0

    def test_metrics_tracking_on_miss(self):
        cache = self._make_cache()
        cache.get("missing")
        assert cache.metrics.misses == 1

    def test_metrics_eviction_on_delete(self):
        cache = self._make_cache()
        cache.set("ekey", "val", ttl=60)
        cache.delete("ekey")
        assert cache.metrics.evictions == 1

    def test_is_available(self):
        cache = self._make_cache()
        assert cache.is_available() is True

    def test_get_no_client_returns_none(self):
        cache = CacheManager(self.config)
        # Don't set _client - force connection failure
        cache._client = None
        # Patch _get_client to return None
        original = cache._get_client
        cache._get_client = lambda: None
        result = cache.get("key")
        assert result is None
        cache._get_client = original

    def test_set_no_client_returns_false(self):
        cache = CacheManager(self.config)
        cache._client = None
        cache._get_client = lambda: None
        result = cache.set("key", "val")
        assert result is False

    def test_delete_no_client_returns_false(self):
        cache = CacheManager(self.config)
        cache._client = None
        cache._get_client = lambda: None
        result = cache.delete("key")
        assert result is False

    def test_clear_no_client_returns_zero(self):
        cache = CacheManager(self.config)
        cache._client = None
        cache._get_client = lambda: None
        result = cache.clear()
        assert result == 0

    def test_is_available_no_client(self):
        cache = CacheManager(self.config)
        cache._client = None
        cache._get_client = lambda: None
        assert cache.is_available() is False

    def test_get_error_path(self):
        cache = self._make_cache()
        cache._client.get = MagicMock(side_effect=Exception("Redis error"))
        result = cache.get("key")
        assert result is None
        assert cache.metrics.errors == 1

    def test_get_reports_metric_hit(self, monkeypatch):
        cache = self._make_cache()
        cache.set("metric-key", "metric-val", ttl=60)
        tracked: list[bool] = []
        monkeypatch.setattr("src.kortana.cache.track_cache_hit", tracked.append)

        assert cache.get("metric-key") == "metric-val"
        assert tracked == [True]

    def test_get_reports_metric_miss(self, monkeypatch):
        cache = self._make_cache()
        tracked: list[bool] = []
        monkeypatch.setattr("src.kortana.cache.track_cache_hit", tracked.append)

        assert cache.get("missing") is None
        assert tracked == [False]

    def test_set_error_path(self):
        cache = self._make_cache()
        cache._client.setex = MagicMock(side_effect=Exception("Redis error"))
        result = cache.set("key", "val")
        assert result is False
        assert cache.metrics.errors == 1

    def test_set_reports_metric_error(self, monkeypatch):
        cache = self._make_cache()
        tracked: list[str] = []
        monkeypatch.setattr("src.kortana.cache.track_cache_error", tracked.append)
        cache._client.setex = MagicMock(side_effect=Exception("Redis error"))

        assert cache.set("key", "val") is False
        assert tracked == ["set"]

    def test_delete_error_path(self):
        cache = self._make_cache()
        cache._client.delete = MagicMock(side_effect=Exception("Redis error"))
        result = cache.delete("key")
        assert result is False

    def test_clear_error_path(self):
        cache = self._make_cache()
        cache._client.keys = MagicMock(side_effect=Exception("Redis error"))
        result = cache.clear()
        assert result == 0

    def test_delete_reports_metric_eviction(self, monkeypatch):
        cache = self._make_cache()
        cache.set("evict-me", "value", ttl=60)
        tracked: list[int] = []
        monkeypatch.setattr(
            "src.kortana.cache.track_cache_eviction",
            lambda count=1: tracked.append(count),
        )

        assert cache.delete("evict-me") is True
        assert tracked == [1]

    def test_is_available_error(self):
        cache = self._make_cache()
        cache._client.ping = MagicMock(side_effect=Exception("Redis error"))
        assert cache.is_available() is False


class TestCacheManagerConnectionFailure:
    """Tests that CacheManager disables itself on Redis connection failure"""

    def test_connection_failure_disables_cache(self):
        config = CacheConfig()
        config.enabled = True
        config.host = "nonexistent_host_xyz"
        config.port = 1
        cache = CacheManager(config)
        # Force connection attempt
        client = cache._get_client()
        # Should either return None or disable cache
        assert client is None or cache.config.enabled is False


class TestCacheHelpers:
    """Tests for module-level helper functions"""

    def test_get_cache_manager_singleton(self):
        import src.kortana.cache as cache_module

        cache_module._cache_manager = None
        mgr1 = get_cache_manager()
        mgr2 = get_cache_manager()
        assert mgr1 is mgr2

    def test_cache_key_generates_string(self):
        import src.kortana.cache as cache_module

        cache_module._cache_manager = None
        key = cache_key("test", "arg1", kw="v")
        assert isinstance(key, str)


class TestCacheResultDecorator:
    """Tests for cache_result and cache_result_async decorators"""

    def test_cache_result_when_disabled(self):
        """Decorator should call function directly when cache disabled"""
        config = CacheConfig()
        config.enabled = False
        import src.kortana.cache as cache_module

        original_mgr = cache_module._cache_manager
        cache_module._cache_manager = CacheManager(config)

        try:
            call_count = [0]

            @cache_result(ttl=60, key_prefix="test")
            def my_func(x):
                call_count[0] += 1
                return x * 2

            assert my_func(5) == 10
            assert my_func(5) == 10
            assert call_count[0] == 2  # Both calls hit the function
        finally:
            cache_module._cache_manager = original_mgr

    def test_cache_result_with_fake_redis(self):
        """Decorator should cache function results"""
        config = CacheConfig()
        config.enabled = True
        fake_redis = fakeredis.FakeRedis(decode_responses=True)

        import src.kortana.cache as cache_module

        original_mgr = cache_module._cache_manager

        cache_mgr = CacheManager(config)
        cache_mgr._client = fake_redis
        cache_module._cache_manager = cache_mgr

        try:
            call_count = [0]

            @cache_result(ttl=60, key_prefix="test")
            def my_func(x):
                call_count[0] += 1
                return x * 2

            result1 = my_func(5)
            result2 = my_func(5)
            assert result1 == 10
            assert result2 == 10
            assert call_count[0] == 1  # Second call hits cache
        finally:
            cache_module._cache_manager = original_mgr

    @pytest.mark.asyncio
    async def test_cache_result_async_when_disabled(self):
        """Async decorator should call function directly when cache disabled"""
        config = CacheConfig()
        config.enabled = False

        import src.kortana.cache as cache_module

        original_mgr = cache_module._cache_manager
        cache_module._cache_manager = CacheManager(config)

        try:
            call_count = [0]

            @cache_result_async(ttl=60, key_prefix="async_test")
            async def my_async_func(x):
                call_count[0] += 1
                return x * 3

            assert await my_async_func(4) == 12
            assert await my_async_func(4) == 12
            assert call_count[0] == 2
        finally:
            cache_module._cache_manager = original_mgr
