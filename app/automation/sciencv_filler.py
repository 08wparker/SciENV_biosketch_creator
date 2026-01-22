"""Main SciENcv automation module using Playwright.

This module handles the browser automation to fill in SciENcv biosketch entries.
It requires the user to manually log in (due to 2FA requirements), then
automates the form filling process.
"""

from __future__ import annotations
import asyncio
from typing import Optional, Callable, Dict, Any, List

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from ..parser.models import BiosketchData, Education, Position, Honor, Contribution
from .auth_handler import AuthHandler
from .selectors import SciENcvSelectors


class SciENcvFiller:
    """Automates filling in SciENcv biosketch forms."""

    def __init__(
        self,
        data: BiosketchData,
        headless: bool = False,
        browser_state_path: Optional[str] = None,
        on_status_update: Optional[Callable[[str], None]] = None
    ):
        """Initialize the filler.

        Args:
            data: Parsed biosketch data to fill
            headless: Whether to run browser in headless mode (default False for login)
            browser_state_path: Path for browser session persistence
            on_status_update: Callback for status updates
        """
        self.data = data
        self.headless = headless
        self.on_status_update = on_status_update or print

        self.auth_handler = AuthHandler(
            browser_state_path=browser_state_path,
            on_status_update=self.on_status_update
        )

        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def _status(self, message: str):
        """Send status update."""
        self.on_status_update(message)

    async def start(self) -> bool:
        """Start the automation process.

        Returns:
            True if automation completed successfully, False otherwise
        """
        try:
            async with async_playwright() as p:
                # Launch browser (always headed for login)
                self._status("Launching browser...")
                self._browser = await p.chromium.launch(headless=self.headless)

                # Create context with potential saved state
                self._context = await self.auth_handler.create_context_with_state(
                    self._browser
                )

                # Create page
                self._page = await self._context.new_page()

                # Handle login
                logged_in = await self.auth_handler.wait_for_login(self._page)
                if not logged_in:
                    self._status("Login failed. Please try again.")
                    return False

                # Save session for future use
                await self.auth_handler.save_session(self._context)

                # Create new biosketch
                self._status("Creating new biosketch document...")
                await self._create_new_biosketch()

                # Fill each section
                await self._fill_education()
                await self._fill_personal_statement()
                await self._fill_positions()
                await self._fill_honors()
                await self._fill_contributions()

                self._status("Biosketch automation complete!")
                return True

        except Exception as e:
            self._status(f"Error during automation: {str(e)}")
            return False
        finally:
            if self._browser:
                # Keep browser open for user to review
                self._status("Browser will remain open for you to review and finalize.")
                # Don't close: await self._browser.close()

    async def _create_new_biosketch(self):
        """Navigate to My Documents and create a new biosketch."""
        page = self._page

        # Go to My Documents
        self._status("Navigating to My Documents...")
        try:
            await page.click(SciENcvSelectors.MY_DOCUMENTS)
            await page.wait_for_load_state('networkidle')
        except Exception:
            # May already be on documents page
            pass

        # Click New Document
        self._status("Creating new NIH Biographical Sketch...")
        await page.click(SciENcvSelectors.NEW_DOCUMENT)
        await page.wait_for_timeout(1000)

        # Select NIH Biographical Sketch
        await page.click(SciENcvSelectors.NIH_BIOSKETCH)
        await page.wait_for_load_state('networkidle')

        # Set document title
        self._status("Setting document title...")
        title = f"{self.data.name} - NIH Biosketch"
        try:
            await page.fill(SciENcvSelectors.DOCUMENT_TITLE_INPUT, title)
        except Exception:
            self._status("Could not set document title - will use default")

    async def _fill_education(self):
        """Fill the Education/Training section."""
        if not self.data.education:
            self._status("No education entries to add")
            return

        self._status(f"Adding {len(self.data.education)} education entries...")

        # Navigate to education section
        try:
            await self._page.click(SciENcvSelectors.EDUCATION_SECTION)
            await self._page.wait_for_load_state('networkidle')
        except Exception:
            pass

        for i, edu in enumerate(self.data.education):
            self._status(f"Adding education {i + 1}/{len(self.data.education)}: {edu.institution}")
            await self._add_education_entry(edu)

    async def _add_education_entry(self, edu: Education):
        """Add a single education entry."""
        page = self._page

        try:
            # Click Add Education
            await page.click(SciENcvSelectors.ADD_EDUCATION)
            await page.wait_for_timeout(500)

            # Fill fields
            await page.fill(SciENcvSelectors.INSTITUTION_INPUT, edu.institution)
            await page.fill(SciENcvSelectors.DEGREE_INPUT, edu.degree)
            await page.fill(SciENcvSelectors.COMPLETION_DATE_INPUT, edu.completion_date)
            await page.fill(SciENcvSelectors.FIELD_OF_STUDY_INPUT, edu.field_of_study)

            # Save
            await page.click(SciENcvSelectors.SAVE_BUTTON)
            await page.wait_for_timeout(500)
        except Exception as e:
            self._status(f"Error adding education entry: {e}")

    async def _fill_personal_statement(self):
        """Fill the Personal Statement section."""
        if not self.data.personal_statement:
            self._status("No personal statement to add")
            return

        self._status("Adding personal statement...")

        try:
            # Navigate to personal statement section
            await self._page.click(SciENcvSelectors.PERSONAL_STATEMENT_SECTION)
            await self._page.wait_for_load_state('networkidle')

            # Fill the text
            await self._page.fill(
                SciENcvSelectors.PERSONAL_STATEMENT_TEXTAREA,
                self.data.personal_statement.text
            )

            # Save
            await self._page.click(SciENcvSelectors.SAVE_BUTTON)
            await self._page.wait_for_timeout(500)

            # Add citations if present
            if self.data.personal_statement.citations:
                self._status(f"Adding {len(self.data.personal_statement.citations)} citations to personal statement...")
                for citation in self.data.personal_statement.citations:
                    await self._add_citation(citation.pmid if citation.pmid else citation.text)

        except Exception as e:
            self._status(f"Error adding personal statement: {e}")

    async def _fill_positions(self):
        """Fill the Positions section."""
        if not self.data.positions:
            self._status("No positions to add")
            return

        self._status(f"Adding {len(self.data.positions)} positions...")

        try:
            await self._page.click(SciENcvSelectors.POSITIONS_SECTION)
            await self._page.wait_for_load_state('networkidle')
        except Exception:
            pass

        for i, pos in enumerate(self.data.positions):
            self._status(f"Adding position {i + 1}/{len(self.data.positions)}: {pos.title}")
            await self._add_position_entry(pos)

    async def _add_position_entry(self, pos: Position):
        """Add a single position entry."""
        page = self._page

        try:
            await page.click(SciENcvSelectors.ADD_POSITION)
            await page.wait_for_timeout(500)

            # Parse dates (format: "2021-Present" or "2015-2019")
            dates = pos.dates.replace('–', '-').split('-')
            start_date = dates[0].strip() if dates else ''
            end_date = dates[1].strip() if len(dates) > 1 else ''

            await page.fill(SciENcvSelectors.POSITION_TITLE_INPUT, pos.title)
            await page.fill(SciENcvSelectors.POSITION_ORG_INPUT, pos.institution)

            if start_date:
                await page.fill(SciENcvSelectors.POSITION_START_DATE, start_date)
            if end_date and end_date.lower() != 'present':
                await page.fill(SciENcvSelectors.POSITION_END_DATE, end_date)

            await page.click(SciENcvSelectors.SAVE_BUTTON)
            await page.wait_for_timeout(500)
        except Exception as e:
            self._status(f"Error adding position: {e}")

    async def _fill_honors(self):
        """Fill the Honors section."""
        if not self.data.honors:
            self._status("No honors to add")
            return

        self._status(f"Adding {len(self.data.honors)} honors...")

        try:
            await self._page.click(SciENcvSelectors.HONORS_SECTION)
            await self._page.wait_for_load_state('networkidle')
        except Exception:
            pass

        for i, honor in enumerate(self.data.honors):
            self._status(f"Adding honor {i + 1}/{len(self.data.honors)}")
            await self._add_honor_entry(honor)

    async def _add_honor_entry(self, honor: Honor):
        """Add a single honor entry."""
        page = self._page

        try:
            await page.click(SciENcvSelectors.ADD_HONOR)
            await page.wait_for_timeout(500)

            await page.fill(SciENcvSelectors.HONOR_YEAR_INPUT, honor.year)
            await page.fill(SciENcvSelectors.HONOR_DESCRIPTION_INPUT, honor.description)

            await page.click(SciENcvSelectors.SAVE_BUTTON)
            await page.wait_for_timeout(500)
        except Exception as e:
            self._status(f"Error adding honor: {e}")

    async def _fill_contributions(self):
        """Fill the Contributions to Science section."""
        if not self.data.contributions:
            self._status("No contributions to add")
            return

        # NIH limits to 5 contributions
        contributions = self.data.contributions[:5]
        self._status(f"Adding {len(contributions)} contributions to science...")

        try:
            await self._page.click(SciENcvSelectors.CONTRIBUTIONS_SECTION)
            await self._page.wait_for_load_state('networkidle')
        except Exception:
            pass

        for i, contrib in enumerate(contributions):
            self._status(f"Adding contribution {i + 1}/{len(contributions)}")
            await self._add_contribution_entry(contrib)

    async def _add_contribution_entry(self, contrib: Contribution):
        """Add a single contribution entry."""
        page = self._page

        try:
            await page.click(SciENcvSelectors.ADD_CONTRIBUTION)
            await page.wait_for_timeout(500)

            await page.fill(SciENcvSelectors.CONTRIBUTION_NARRATIVE, contrib.narrative)

            await page.click(SciENcvSelectors.SAVE_BUTTON)
            await page.wait_for_timeout(500)

            # Add citations for this contribution
            if contrib.citations:
                self._status(f"Adding {len(contrib.citations)} citations...")
                for citation in contrib.citations:
                    await self._add_citation(citation.pmid if citation.pmid else citation.text)

        except Exception as e:
            self._status(f"Error adding contribution: {e}")

    async def _add_citation(self, identifier: str):
        """Add a citation by PMID or text search."""
        page = self._page

        try:
            await page.click(SciENcvSelectors.ADD_CITATION)
            await page.wait_for_timeout(500)

            # Try PMID first
            if identifier and identifier.isdigit():
                try:
                    await page.fill(SciENcvSelectors.PMID_INPUT, identifier)
                except Exception:
                    await page.fill(SciENcvSelectors.CITATION_SEARCH, identifier)
            else:
                await page.fill(SciENcvSelectors.CITATION_SEARCH, identifier[:100] if identifier else '')

            await page.click(SciENcvSelectors.SAVE_BUTTON)
            await page.wait_for_timeout(500)
        except Exception as e:
            self._status(f"Error adding citation: {e}")


async def run_automation(
    data_dict: Dict[str, Any],
    headless: bool = False,
    browser_state_path: Optional[str] = None,
    on_status_update: Optional[Callable[[str], None]] = None
) -> bool:
    """Run the SciENcv automation with the provided data.

    Args:
        data_dict: Dictionary of biosketch data
        headless: Whether to run headless (default False)
        browser_state_path: Path for session persistence
        on_status_update: Status callback

    Returns:
        True if successful, False otherwise
    """
    data = BiosketchData.from_dict(data_dict)
    filler = SciENcvFiller(
        data=data,
        headless=headless,
        browser_state_path=browser_state_path,
        on_status_update=on_status_update
    )
    return await filler.start()
