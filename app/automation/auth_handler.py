"""Authentication handler for SciENcv login.

Handles the manual login flow where users authenticate via Login.gov/eRA Commons.
Since SciENcv requires 2FA, we cannot fully automate the login process.
Instead, we open a browser window and wait for the user to complete login.
"""

from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Optional, Callable

from playwright.async_api import Page, Browser, BrowserContext

from .selectors import SciENcvSelectors


class AuthHandler:
    """Handles SciENcv authentication flow."""

    SCIENCV_URL = 'https://www.ncbi.nlm.nih.gov/labs/sciencv/'
    LOGIN_TIMEOUT = 300000  # 5 minutes for user to complete login

    def __init__(
        self,
        browser_state_path: Optional[str] = None,
        on_status_update: Optional[Callable[[str], None]] = None
    ):
        """Initialize auth handler.

        Args:
            browser_state_path: Path to save/load browser state for session persistence
            on_status_update: Callback function for status updates
        """
        self.browser_state_path = browser_state_path or 'browser_state'
        self.on_status_update = on_status_update or print
        self._ensure_state_directory()

    def _ensure_state_directory(self):
        """Ensure browser state directory exists."""
        Path(self.browser_state_path).mkdir(parents=True, exist_ok=True)

    def _get_state_file(self) -> str:
        """Get the path to the browser state file."""
        return os.path.join(self.browser_state_path, 'sciencv_state.json')

    def _status(self, message: str):
        """Send status update."""
        self.on_status_update(message)

    async def has_saved_session(self) -> bool:
        """Check if we have a saved browser session."""
        return os.path.exists(self._get_state_file())

    async def create_context_with_state(
        self,
        browser: Browser
    ) -> BrowserContext:
        """Create a browser context, loading saved state if available.

        Args:
            browser: Playwright browser instance

        Returns:
            Browser context with optional saved state
        """
        state_file = self._get_state_file()

        if os.path.exists(state_file):
            self._status("Loading saved browser session...")
            try:
                context = await browser.new_context(storage_state=state_file)
                return context
            except Exception as e:
                self._status(f"Failed to load saved session: {e}")

        # Create fresh context
        self._status("Creating new browser session...")
        context = await browser.new_context()
        return context

    async def save_session(self, context: BrowserContext):
        """Save the current browser session state.

        Args:
            context: Browser context to save
        """
        state_file = self._get_state_file()
        try:
            await context.storage_state(path=state_file)
            self._status("Browser session saved for future use")
        except Exception as e:
            self._status(f"Failed to save session: {e}")

    async def wait_for_login(self, page: Page) -> bool:
        """Navigate to SciENcv and wait for user to complete login.

        Args:
            page: Playwright page instance

        Returns:
            True if login successful, False otherwise
        """
        self._status("Navigating to SciENcv...")
        await page.goto(self.SCIENCV_URL)

        # Check if already logged in
        try:
            await page.wait_for_selector(
                SciENcvSelectors.LOGGED_IN_INDICATOR,
                timeout=5000
            )
            self._status("Already logged in!")
            return True
        except Exception:
            pass

        # Need to log in
        self._status("Please log in to SciENcv in the browser window...")
        self._status("(You have 5 minutes to complete login with 2FA)")

        try:
            # Wait for login to complete
            await page.wait_for_selector(
                SciENcvSelectors.LOGGED_IN_INDICATOR,
                timeout=self.LOGIN_TIMEOUT
            )
            self._status("Login successful!")
            return True
        except Exception as e:
            self._status(f"Login timed out or failed: {e}")
            return False

    async def check_session_valid(self, page: Page) -> bool:
        """Check if the current session is still valid.

        Args:
            page: Playwright page instance

        Returns:
            True if session is valid, False otherwise
        """
        try:
            await page.goto(self.SCIENCV_URL)
            await page.wait_for_selector(
                SciENcvSelectors.LOGGED_IN_INDICATOR,
                timeout=10000
            )
            return True
        except Exception:
            return False
