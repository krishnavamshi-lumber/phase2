"""
Environment configuration for different test environments.
Centralized configuration management for CI/CD and local development.
Mirrors: fixtures/environments/environment.config.ts
"""

from __future__ import annotations

import os
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class CredentialsConfig:
    admin_username: str
    admin_password: str
    test_username: Optional[str] = None
    test_password: Optional[str] = None


@dataclass
class TimeoutsConfig:
    navigation: int
    element: int
    manual_login: int
    form_submission: int
    short: int
    medium: int
    long: int


@dataclass
class FeaturesConfig:
    manual_login: bool
    screenshots: bool
    video: bool
    trace: bool


@dataclass
class EnvironmentConfig:
    name: str
    base_url: str
    api_url: str
    credentials: CredentialsConfig
    timeouts: TimeoutsConfig
    features: FeaturesConfig


# ============================================================================
# ENVIRONMENT MANAGER (Singleton)
# ============================================================================

class EnvironmentManager:
    _instance: Optional["EnvironmentManager"] = None
    _current_environment: Optional[EnvironmentConfig] = None

    def __new__(cls) -> "EnvironmentManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_environment = cls._instance._load_environment()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "EnvironmentManager":
        return cls()

    def _load_environment(self) -> EnvironmentConfig:
        env = os.environ.get("NODE_ENV", "development")
        self._load_environment_variables()

        env_lower = env.lower()
        if env_lower == "production":
            return self._get_production_config()
        elif env_lower == "staging":
            return self._get_staging_config()
        elif env_lower == "development":
            return self._get_development_config()
        else:
            return self._get_staging_config()

    def _load_environment_variables(self) -> None:
        """Load .env file if python-dotenv is available (optional dependency)."""
        try:
            from dotenv import load_dotenv, dotenv_values
            result = load_dotenv()
            if result:
                print("✅ Loaded .env file successfully")
                print(f"🔧 NAVIGATION_TIMEOUT from env: {os.environ.get('NAVIGATION_TIMEOUT')}")
            else:
                print("⚠️ Error loading .env file or file not found")
        except ImportError:
            print("dotenv not available, using system environment variables")

    def get_current_environment(self) -> EnvironmentConfig:
        return self._current_environment

    def set_environment(self, environment: EnvironmentConfig) -> None:
        self._current_environment = environment

    def get_config(self) -> EnvironmentConfig:
        return self._current_environment

    def get_base_url(self) -> str:
        return self._current_environment.base_url

    def get_api_url(self) -> str:
        return self._current_environment.api_url

    def get_credentials(self) -> CredentialsConfig:
        return self._current_environment.credentials

    def get_timeouts(self) -> TimeoutsConfig:
        return self._current_environment.timeouts

    def get_features(self) -> FeaturesConfig:
        return self._current_environment.features

    def _get_production_config(self) -> EnvironmentConfig:
        return EnvironmentConfig(
            name="production",
            base_url=os.environ.get("PROD_BASE_URL", "https://admin.lumberfi.com"),
            api_url=os.environ.get("PROD_API_URL", "https://api.lumberfi.com"),
            credentials=CredentialsConfig(
                admin_username=os.environ.get("PROD_ADMIN_USERNAME", ""),
                admin_password=os.environ.get("PROD_ADMIN_PASSWORD", ""),
            ),
            timeouts=TimeoutsConfig(
                navigation=30000,
                element=15000,
                manual_login=120000,
                form_submission=30000,
                short=5000,
                medium=15000,
                long=30000,
            ),
            features=FeaturesConfig(
                manual_login=False,
                screenshots=True,
                video=False,
                trace=False,
            ),
        )

    def _get_staging_config(self) -> EnvironmentConfig:
        return EnvironmentConfig(
            name="staging",
            base_url=os.environ.get("STAGING_BASE_URL", "https://stage-admin.lumberfi.com"),
            api_url=os.environ.get("STAGING_API_URL", "https://stage-api.lumberfi.com"),
            credentials=CredentialsConfig(
                admin_username=os.environ.get("STAGING_ADMIN_USERNAME", ""),
                admin_password=os.environ.get("STAGING_ADMIN_PASSWORD", ""),
            ),
            timeouts=TimeoutsConfig(
                navigation=int(os.environ.get("NAVIGATION_TIMEOUT", "60000")),
                element=int(os.environ.get("ELEMENT_TIMEOUT", "30000")),
                manual_login=int(os.environ.get("MANUAL_LOGIN_TIMEOUT", "600000")),
                form_submission=int(os.environ.get("FORM_SUBMISSION_TIMEOUT", "60000")),
                short=int(os.environ.get("SHORT_TIMEOUT", "10000")),
                medium=int(os.environ.get("MEDIUM_TIMEOUT", "30000")),
                long=int(os.environ.get("LONG_TIMEOUT", "60000")),
            ),
            features=FeaturesConfig(
                manual_login=os.environ.get("MANUAL_LOGIN", "true") != "false",
                screenshots=os.environ.get("SCREENSHOT_MODE", "") != "never",
                video=os.environ.get("VIDEO_MODE", "") != "never",
                trace=os.environ.get("TRACE_MODE", "") != "never",
            ),
        )

    def _get_development_config(self) -> EnvironmentConfig:
        return EnvironmentConfig(
            name="development",
            base_url=os.environ.get("DEV_BASE_URL", "http://localhost:3000"),
            api_url=os.environ.get("DEV_API_URL", "https://qa-platform.lumberfi.com/"),
            credentials=CredentialsConfig(
                admin_username=os.environ.get("DEV_ADMIN_USERNAME", "admin"),
                admin_password=os.environ.get("DEV_ADMIN_PASSWORD", "password"),
                test_username=os.environ.get("DEV_TEST_USERNAME", "testuser"),
                test_password=os.environ.get("DEV_TEST_PASSWORD", "testpass"),
            ),
            timeouts=TimeoutsConfig(
                navigation=120000,
                element=60000,
                manual_login=600000,
                form_submission=120000,
                short=15000,
                medium=60000,
                long=120000,
            ),
            features=FeaturesConfig(
                manual_login=True,
                screenshots=True,
                video=True,
                trace=True,
            ),
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_environment() -> EnvironmentConfig:
    return EnvironmentManager.get_instance().get_config()


def get_base_url() -> str:
    return EnvironmentManager.get_instance().get_base_url()


def get_api_url() -> str:
    return EnvironmentManager.get_instance().get_api_url()


def get_credentials() -> CredentialsConfig:
    return EnvironmentManager.get_instance().get_credentials()


def get_timeouts() -> TimeoutsConfig:
    return EnvironmentManager.get_instance().get_timeouts()


def get_features() -> FeaturesConfig:
    return EnvironmentManager.get_instance().get_features()


def _x(a: int, b: int, c: int) -> bool:
    """
    License/expiry check. Returns True if current date is before a/b/c (year/month/day).
    Mirrors: export function _x(a, b, c) in environment.config.ts
    """
    n = datetime.now()
    return (
        n.year < a
        or (n.year == a and n.month < b)
        or (n.year == a and n.month == b and n.day < c)
    )


def _e(t: int, arr: list[str]) -> str:
    """
    Mirrors: export function _e(t, arr) in environment.config.ts
    """
    return arr[math.floor(t % len(arr))]