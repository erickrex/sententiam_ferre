"""
Custom throttle classes for rate limiting
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limit for login attempts: 5 attempts per 15 minutes
    """
    scope = 'login'
    rate = '5/15m'


class GeneralAPIRateThrottle(UserRateThrottle):
    """
    General rate limit for authenticated API endpoints
    """
    scope = 'api'
    rate = '1000/hour'
