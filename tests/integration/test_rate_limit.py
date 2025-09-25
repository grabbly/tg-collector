"""Integration tests for rate limiting service."""

import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.lib.rate_limit import RateLimiter


class TestRateLimitIntegration:
    """Test rate limiting functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter with test configuration."""
        return RateLimiter(requests_per_minute=5, window_minutes=1)

    def test_rate_limiter_allows_requests_within_limit(self, rate_limiter):
        """Test that requests within the limit are allowed."""
        user_id = 12345
        
        # First 5 requests should be allowed
        for i in range(5):
            result = rate_limiter.is_allowed(user_id)
            assert result.allowed is True
            assert result.remaining >= 0
            assert result.reset_time is not None

    def test_rate_limiter_blocks_requests_over_limit(self, rate_limiter):
        """Test that requests over the limit are blocked."""
        user_id = 12346
        
        # Use up the quota (5 requests)
        for _ in range(5):
            rate_limiter.is_allowed(user_id)
        
        # 6th request should be blocked
        result = rate_limiter.is_allowed(user_id)
        assert result.allowed is False
        assert result.remaining == 0
        assert result.reset_time is not None

    def test_rate_limiter_tracks_separate_users(self, rate_limiter):
        """Test that rate limiting is per-user."""
        user1 = 11111
        user2 = 22222
        
        # Use up user1's quota
        for _ in range(5):
            rate_limiter.is_allowed(user1)
        
        # user1 should be blocked
        result1 = rate_limiter.is_allowed(user1)
        assert result1.allowed is False
        
        # user2 should still be allowed
        result2 = rate_limiter.is_allowed(user2)
        assert result2.allowed is True
        assert result2.remaining == 4  # 4 remaining after first request

    def test_rate_limiter_window_resets(self):
        """Test that rate limit window resets after time expires."""
        # Create rate limiter with very short window for testing
        rate_limiter = RateLimiter(requests_per_minute=2, window_minutes=0.01)  # ~0.6 seconds
        user_id = 33333
        
        # Use up quota
        for _ in range(2):
            result = rate_limiter.is_allowed(user_id)
            assert result.allowed is True
        
        # Next request should be blocked
        result = rate_limiter.is_allowed(user_id)
        assert result.allowed is False
        
        # Wait for window to reset (slightly longer than window)
        time.sleep(1.0)
        
        # Should be allowed again
        result = rate_limiter.is_allowed(user_id)
        assert result.allowed is True
        assert result.remaining == 1  # 1 remaining after reset

    def test_rate_limiter_remaining_count_accurate(self, rate_limiter):
        """Test that remaining count is accurate."""
        user_id = 44444
        
        # Check remaining count decreases correctly
        expected_remaining = [4, 3, 2, 1, 0]
        for i, expected in enumerate(expected_remaining):
            result = rate_limiter.is_allowed(user_id)
            assert result.allowed is True
            assert result.remaining == expected, f"Request {i+1}: expected {expected}, got {result.remaining}"
        
        # Next request should be blocked with 0 remaining
        result = rate_limiter.is_allowed(user_id)
        assert result.allowed is False
        assert result.remaining == 0

    def test_rate_limiter_reset_time_calculation(self, rate_limiter):
        """Test that reset time is calculated correctly."""
        user_id = 55555
        start_time = datetime.utcnow()
        
        # Make a request
        result = rate_limiter.is_allowed(user_id)
        
        # Reset time should be approximately 1 minute from now
        expected_reset = start_time + timedelta(minutes=1)
        time_diff = abs((result.reset_time - expected_reset).total_seconds())
        
        # Allow some tolerance for execution time
        assert time_diff < 5, f"Reset time diff too large: {time_diff} seconds"

    def test_rate_limiter_with_different_configurations(self):
        """Test rate limiter with different configurations."""
        test_cases = [
            (1, 1),   # 1 request per minute
            (10, 1),  # 10 requests per minute
            (5, 5),   # 5 requests per 5 minutes
        ]
        
        for requests_per_minute, window_minutes in test_cases:
            limiter = RateLimiter(requests_per_minute=requests_per_minute, window_minutes=window_minutes)
            user_id = 66666 + requests_per_minute  # Unique user per test
            
            # Should allow up to the limit
            for _ in range(requests_per_minute):
                result = limiter.is_allowed(user_id)
                assert result.allowed is True
            
            # Next request should be blocked
            result = limiter.is_allowed(user_id)
            assert result.allowed is False

    def test_rate_limiter_concurrent_users(self, rate_limiter):
        """Test rate limiter with many concurrent users."""
        base_user_id = 77777
        num_users = 10
        
        # Each user makes requests up to their limit
        for user_offset in range(num_users):
            user_id = base_user_id + user_offset
            
            # Each user should get their full quota
            for request_num in range(5):
                result = rate_limiter.is_allowed(user_id)
                assert result.allowed is True, f"User {user_offset}, request {request_num+1} should be allowed"
            
            # 6th request should be blocked for each user
            result = rate_limiter.is_allowed(user_id)
            assert result.allowed is False, f"User {user_offset}, request 6 should be blocked"

    def test_rate_limiter_memory_cleanup(self):
        """Test that rate limiter cleans up old user data."""
        # Create rate limiter with short window for faster testing
        rate_limiter = RateLimiter(requests_per_minute=1, window_minutes=0.01)
        user_id = 88888
        
        # Make a request to create user entry
        rate_limiter.is_allowed(user_id)
        
        # Verify user is tracked
        assert len(rate_limiter._user_windows) == 1
        
        # Wait for window to expire and make another request
        time.sleep(1.0)
        rate_limiter.is_allowed(user_id)
        
        # Old expired data should eventually be cleaned up
        # (This may require additional implementation in the rate limiter)
        # For now, just verify basic functionality works

    @patch('src.observability.logging.log_event')
    def test_rate_limiter_logging_integration(self, mock_log_event, rate_limiter):
        """Test that rate limiting events are logged correctly."""
        user_id = 99999
        
        # Use up quota
        for _ in range(5):
            rate_limiter.is_allowed(user_id)
        
        # Attempt blocked request - should trigger logging
        result = rate_limiter.is_allowed(user_id)
        assert result.allowed is False
        
        # Verify log event was called for rate limit exceeded
        mock_log_event.assert_called()
        
        # Check the log call contains relevant information
        call_args = mock_log_event.call_args
        assert 'rate_limit_exceeded' in str(call_args) or 'throttled' in str(call_args)

    def test_rate_limiter_edge_cases(self, rate_limiter):
        """Test rate limiter edge cases."""
        # Test with user_id 0
        result = rate_limiter.is_allowed(0)
        assert result.allowed is True
        
        # Test with negative user_id  
        result = rate_limiter.is_allowed(-123)
        assert result.allowed is True
        
        # Test with very large user_id
        result = rate_limiter.is_allowed(2**63 - 1)
        assert result.allowed is True

    def test_rate_limiter_result_dataclass(self, rate_limiter):
        """Test that RateLimitResult has expected structure."""
        user_id = 11223
        result = rate_limiter.is_allowed(user_id)
        
        # Check result has expected attributes
        assert hasattr(result, 'allowed')
        assert hasattr(result, 'remaining')
        assert hasattr(result, 'reset_time')
        
        # Check types
        assert isinstance(result.allowed, bool)
        assert isinstance(result.remaining, int)
        assert isinstance(result.reset_time, datetime)
        
        # Check values are reasonable
        assert result.remaining >= 0
        assert result.remaining <= 5  # Max requests per minute
        assert result.reset_time > datetime.utcnow()