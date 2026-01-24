"""SciENcv Biosketch Automation using Playwright.

This module automates filling in NIH Biographical Sketch Common Form entries
on SciENcv. It uses accessibility-based selectors derived from Claude in Chrome
browser extension inspection.

Flow:
1. User logs in manually (2FA required)
2. Automation creates a new document
3. Fills each section in order:
   - A. Professional Preparation
   - B. Appointments and Positions
   - C. Products
   - Supplement A. Personal Statement
   - Supplement B. Honors
   - Supplement C. Contributions to Science
"""

from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Locator

from .selectors import Selectors


@dataclass
class BiosketchData:
    """Structured biosketch data from the app."""
    name: str
    era_commons_username: str
    position_title: str
    education: List[Dict[str, Any]]
    positions: List[Dict[str, Any]]
    honors: List[Dict[str, Any]]
    personal_statement: Dict[str, Any]
    contributions: List[Dict[str, Any]]
    products: Dict[str, List[Dict[str, Any]]]  # {related: [], other: []}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiosketchData':
        """Create BiosketchData from dictionary."""
        return cls(
            name=data.get('name', ''),
            era_commons_username=data.get('era_commons_username', ''),
            position_title=data.get('position_title', ''),
            education=data.get('education', []),
            positions=data.get('positions', []),
            honors=data.get('honors', []),
            personal_statement=data.get('personal_statement', {}),
            contributions=data.get('contributions', []),
            products=data.get('products', {'related': [], 'other': []})
        )


class SciENcvAutomation:
    """Automates filling in SciENcv biosketch forms."""

    SCIENCV_URL = 'https://www.ncbi.nlm.nih.gov/labs/sciencv/'
    LOGIN_TIMEOUT = 300000  # 5 minutes for user to complete login

    def __init__(
        self,
        data: BiosketchData,
        headless: bool = False,
        on_status: Optional[Callable[[str], None]] = None
    ):
        """Initialize the automation.

        Args:
            data: Parsed biosketch data to fill
            headless: Whether to run browser in headless mode (default False for login)
            on_status: Callback for status updates
        """
        self.data = data
        self.headless = headless
        self.on_status = on_status or print
        self._page: Optional[Page] = None

    def _status(self, message: str):
        """Send status update."""
        self.on_status(f"[SciENcv] {message}")

    async def _click(self, role: str, name: str, exact: bool = False):
        """Click an element by role and name."""
        await self._page.get_by_role(role, name=name, exact=exact).click()
        await self._page.wait_for_timeout(300)

    async def _fill(self, role: str, name: str, value: str):
        """Fill a text input by role and name."""
        locator = self._page.get_by_role(role, name=name)
        await locator.click()
        await locator.fill(value)

    async def _select_dropdown(self, role: str, name: str, option_text: str):
        """Select an option from a dropdown/combobox."""
        # Click to open dropdown
        await self._page.get_by_role(role, name=name).click()
        await self._page.wait_for_timeout(300)

        # Type to filter and select
        await self._page.keyboard.type(option_text[:4])
        await self._page.wait_for_timeout(200)
        await self._page.keyboard.press('Enter')
        await self._page.wait_for_timeout(200)

    async def run(self) -> bool:
        """Run the complete automation process.

        Returns:
            True if automation completed successfully, False otherwise
        """
        try:
            async with async_playwright() as p:
                self._status("Launching browser...")
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()
                self._page = await context.new_page()

                # Step 1: Login
                if not await self._wait_for_login():
                    return False

                # Step 2: Create new document
                await self._create_document()

                # Step 3: Fill each section
                await self._fill_professional_preparation()
                await self._fill_appointments()
                await self._fill_products()
                await self._fill_personal_statement()
                await self._fill_honors()
                await self._fill_contributions()

                self._status("Automation complete! Review your biosketch in the browser.")

                # Keep browser open for review
                self._status("Press Ctrl+C when done reviewing to close the browser.")
                try:
                    await asyncio.sleep(3600)  # Wait up to 1 hour
                except asyncio.CancelledError:
                    pass

                return True

        except Exception as e:
            self._status(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    async def _wait_for_login(self) -> bool:
        """Navigate to SciENcv and wait for user to log in."""
        self._status("Navigating to SciENcv...")
        await self._page.goto(self.SCIENCV_URL)

        # Check if already logged in
        try:
            await self._page.wait_for_selector('text="My Documents"', timeout=5000)
            self._status("Already logged in!")
            return True
        except Exception:
            pass

        self._status("Please log in to SciENcv in the browser window...")
        self._status("(You have 5 minutes to complete login with 2FA)")

        try:
            await self._page.wait_for_selector('text="My Documents"', timeout=self.LOGIN_TIMEOUT)
            self._status("Login successful!")
            return True
        except Exception:
            self._status("Login timed out. Please try again.")
            return False

    async def _create_document(self):
        """Create a new NIH Biographical Sketch document."""
        self._status("Creating new NIH Biographical Sketch...")

        # Click NEW DOCUMENT button
        await self._click("button", "NEW DOCUMENT")
        await self._page.wait_for_timeout(1000)

        # Generate document name
        date_str = datetime.now().strftime("%Y-%m-%d")
        doc_name = f"{self.data.name} {date_str}"

        # Fill document name
        await self._fill("textbox", "Document Name *", doc_name)
        self._status(f"Document name: {doc_name}")

        # Select document type
        await self._click("button", "Document type")
        await self._page.wait_for_timeout(500)
        await self._page.get_by_role("option", name="NIH Biographical Sketch Common Form").click()
        await self._page.wait_for_timeout(300)
        self._status("Selected: NIH Biographical Sketch Common Form")

        # Select "Start with a blank document"
        await self._click("radio", "Start with a blank document")

        # Click CREATE
        await self._click("button", "CREATE")
        await self._page.wait_for_load_state('networkidle')
        await self._page.wait_for_timeout(2000)
        self._status("Document created!")

    async def _fill_professional_preparation(self):
        """Fill Section A: Professional Preparation (Education/Training)."""
        if not self.data.education:
            self._status("No education entries to add")
            return

        self._status(f"Adding {len(self.data.education)} education entries...")

        for i, edu in enumerate(self.data.education):
            is_last = (i == len(self.data.education) - 1)
            await self._add_education_entry(edu, is_last)
            self._status(f"  Added: {edu.get('institution', 'Unknown')} - {edu.get('degree', '')}")

    async def _add_education_entry(self, edu: Dict[str, Any], is_last: bool = False):
        """Add a single education/training entry."""
        # Click ADD PROFESSIONAL PREPARATION
        await self._click("button", "ADD PROFESSIONAL PREPARATION")
        await self._page.wait_for_timeout(800)

        # Determine if this is a training entry (postdoc, fellowship, residency)
        degree = edu.get('degree', '').lower()
        is_training = any(t in degree for t in ['postdoc', 'fellow', 'resident', 'training', 'intern'])

        if is_training:
            await self._click("radio", "Training")
            await self._page.wait_for_timeout(300)

        # Fill Organization
        await self._fill("textbox", "Organization *", edu.get('institution', ''))

        # Fill City (parse from location if needed)
        location = edu.get('location', '')
        city = location.split(',')[0].strip() if location else 'Chicago'
        await self._fill("textbox", "City *", city)

        # Select State/Province (US assumed)
        state = self._parse_state(location)
        if state:
            await self._select_dropdown("combobox", "State/Province *", state)

        # Select Degree
        degree_value = edu.get('degree', '')
        if degree_value:
            try:
                await self._select_dropdown("combobox", "Degree *", degree_value)
            except Exception:
                # Try common abbreviations
                pass

        # Fill Field of Study
        await self._fill("textbox", "Field of Study *", edu.get('field_of_study', ''))

        # Fill dates
        completion_date = edu.get('completion_date', '')
        if completion_date:
            # Parse date - could be "2012", "06/2012", "Jun 2012", etc.
            end_date = self._parse_date_for_sciencv(completion_date)
            await self._fill("textbox", "End Date", end_date)

        # Save
        if is_last:
            await self._click("button", "SAVE")
        else:
            await self._click("button", "SAVE & ADD ANOTHER ENTRY")

        await self._page.wait_for_timeout(500)

    async def _fill_appointments(self):
        """Fill Section B: Appointments and Positions."""
        if not self.data.positions:
            self._status("No positions to add")
            return

        self._status(f"Adding {len(self.data.positions)} appointments/positions...")

        for i, pos in enumerate(self.data.positions):
            is_last = (i == len(self.data.positions) - 1)
            await self._add_appointment_entry(pos, is_last)
            self._status(f"  Added: {pos.get('title', 'Unknown')}")

    async def _add_appointment_entry(self, pos: Dict[str, Any], is_last: bool = False):
        """Add a single appointment/position entry."""
        # Click ADD APPOINTMENT/POSITION
        await self._click("button", "ADD APPOINTMENT/POSITION")
        await self._page.wait_for_timeout(800)

        # Fill Title
        await self._fill("textbox", "Title *", pos.get('title', ''))

        # Fill Organization
        await self._fill("textbox", "Organization/Department *", pos.get('institution', ''))

        # Parse dates (format: "2021-Present" or "2015-2019")
        dates = pos.get('dates', '').replace('–', '-').replace('—', '-')
        parts = dates.split('-')
        start_year = parts[0].strip() if parts else ''
        end_year = parts[1].strip() if len(parts) > 1 else ''

        # Fill Start Year
        if start_year:
            await self._fill("textbox", "Start Year *", start_year)

        # Handle current position
        if end_year.lower() == 'present' or not end_year:
            try:
                await self._click("checkbox", "Current Position")
            except Exception:
                pass
        elif end_year:
            await self._fill("textbox", "End Year", end_year)

        # Save
        if is_last:
            await self._click("button", "SAVE")
        else:
            await self._click("button", "SAVE & ADD ANOTHER")

        await self._page.wait_for_timeout(500)

    async def _fill_products(self):
        """Fill Section C: Products."""
        related = self.data.products.get('related', [])
        other = self.data.products.get('other', [])

        if not related and not other:
            self._status("No products to add")
            return

        # Add related products
        if related:
            self._status(f"Adding {len(related)} related products...")
            await self._add_products_section(related, "SELECT RELATED PRODUCTS")

        # Add other significant products
        if other:
            self._status(f"Adding {len(other)} other significant products...")
            await self._add_products_section(other, "SELECT OTHER PRODUCTS")

    async def _add_products_section(self, products: List[Dict[str, Any]], button_name: str):
        """Add products to a specific section."""
        # Click SELECT button
        await self._click("button", button_name)
        await self._page.wait_for_timeout(1000)

        for product in products:
            pmid = product.get('pmid', '')
            if pmid:
                # Search by PMID
                search_input = self._page.get_by_role("textbox", name="Search citations")
                await search_input.click()
                await search_input.clear()
                await search_input.fill(pmid)
                await self._page.keyboard.press('Enter')
                await self._page.wait_for_timeout(1500)

                # Select the citation checkbox
                try:
                    checkbox = self._page.get_by_role("checkbox").first
                    await checkbox.click()
                    await self._page.wait_for_timeout(300)
                except Exception as e:
                    self._status(f"  Could not select citation for PMID {pmid}: {e}")

        # Click CONTINUE to save selections
        await self._click("button", "CONTINUE")
        await self._page.wait_for_timeout(500)

    async def _fill_personal_statement(self):
        """Fill Supplement A: Personal Statement."""
        ps = self.data.personal_statement
        if not ps or not ps.get('text'):
            self._status("No personal statement to add")
            return

        self._status("Adding personal statement...")

        # Build the full text including grants
        text = ps.get('text', '')

        # Add research support section if grants exist
        grants = ps.get('grants', [])
        if grants:
            text += "\n\nCurrent and recently completed research support:\n"
            for grant in grants:
                funder = grant.get('funder', '')
                number = grant.get('number', '')
                pi = grant.get('pi', '')
                role = grant.get('role', '')
                dates = grant.get('dates', '')
                title = grant.get('title', '')

                text += f"{funder} {number}\t{pi} ({role})\t{dates}\n"
                text += f"{title}\n\n"

        # Check character limit (3,500)
        if len(text) > 3500:
            self._status(f"  Warning: Personal statement is {len(text)} chars (limit: 3,500)")
            text = text[:3500]

        # Click ADD PERSONAL STATEMENT
        await self._click("button", "ADD PERSONAL STATEMENT")
        await self._page.wait_for_timeout(800)

        # Fill the textarea
        textarea = self._page.locator('textarea').first
        await textarea.fill(text)

        # Save
        await self._click("button", "SAVE")
        await self._page.wait_for_timeout(500)
        self._status(f"  Added personal statement ({len(text)} characters)")

    async def _fill_honors(self):
        """Fill Supplement B: Honors."""
        if not self.data.honors:
            self._status("No honors to add")
            return

        # NIH limits to 10 honors
        honors = self.data.honors[:10]
        self._status(f"Adding {len(honors)} honors...")

        for i, honor in enumerate(honors):
            is_last = (i == len(honors) - 1)
            await self._add_honor_entry(honor, is_last)
            self._status(f"  Added: {honor.get('year', '')} - {honor.get('description', '')[:50]}...")

    async def _add_honor_entry(self, honor: Dict[str, Any], is_last: bool = False):
        """Add a single honor entry."""
        # Click ADD HONOR
        await self._click("button", "ADD HONOR")
        await self._page.wait_for_timeout(800)

        # Fill Honor description
        description = honor.get('description', '')
        await self._fill("textbox", "Honor *", description)

        # Fill Organization (parse from description if not provided)
        organization = honor.get('organization', '')
        if organization:
            await self._fill("textbox", "Name of Organization *", organization)

        # Fill Year
        year = honor.get('year', '')
        if year:
            await self._fill("textbox", "Year *", year)

        # Save
        if is_last:
            await self._click("button", "SAVE")
        else:
            await self._click("button", "SAVE & ADD ANOTHER")

        await self._page.wait_for_timeout(500)

    async def _fill_contributions(self):
        """Fill Supplement C: Contributions to Science."""
        if not self.data.contributions:
            self._status("No contributions to add")
            return

        # NIH limits to 5 contributions
        contributions = self.data.contributions[:5]
        self._status(f"Adding {len(contributions)} contributions to science...")

        for i, contrib in enumerate(contributions):
            is_first = (i == 0)
            is_last = (i == len(contributions) - 1)
            await self._add_contribution_entry(contrib, is_first, is_last)
            narrative_preview = contrib.get('narrative', '')[:50]
            self._status(f"  Added contribution {i+1}: {narrative_preview}...")

    async def _add_contribution_entry(
        self,
        contrib: Dict[str, Any],
        is_first: bool = True,
        is_last: bool = False
    ):
        """Add a single contribution entry."""
        # Click appropriate add button
        if is_first:
            await self._click("button", "ADD CONTRIBUTION TO SCIENCE")
        else:
            await self._click("button", "ADD ANOTHER CONTRIBUTION TO SCIENCE")

        await self._page.wait_for_timeout(800)

        # Fill narrative (2,000 char limit)
        narrative = contrib.get('narrative', '')
        if len(narrative) > 2000:
            self._status(f"    Warning: Contribution is {len(narrative)} chars (limit: 2,000)")
            narrative = narrative[:2000]

        # Find and fill textarea
        textarea = self._page.locator('textarea').first
        await textarea.fill(narrative)

        # Save
        await self._click("button", "SAVE")
        await self._page.wait_for_timeout(1000)

        # Add citations if present
        citations = contrib.get('citations', [])
        if citations:
            self._status(f"    Adding {len(citations)} citations...")
            for citation in citations:
                await self._add_citation(citation)

    async def _add_citation(self, citation: Dict[str, Any]):
        """Add a citation to the current contribution."""
        pmid = citation.get('pmid', '')
        if not pmid:
            return

        try:
            # Click ADD CITATION
            await self._click("button", "ADD CITATION")
            await self._page.wait_for_timeout(800)

            # Search by PMID
            search_input = self._page.get_by_role("textbox", name="Search")
            await search_input.fill(pmid)
            await self._page.keyboard.press('Enter')
            await self._page.wait_for_timeout(1500)

            # Select the citation
            checkbox = self._page.get_by_role("checkbox").first
            await checkbox.click()
            await self._page.wait_for_timeout(300)

            # Confirm selection
            await self._click("button", "SELECT")
            await self._page.wait_for_timeout(500)

        except Exception as e:
            self._status(f"    Could not add citation PMID {pmid}: {e}")

    def _parse_state(self, location: str) -> str:
        """Parse state abbreviation from location string."""
        # Common state mappings
        states = {
            'IL': 'Illinois', 'Illinois': 'Illinois',
            'MA': 'Massachusetts', 'Massachusetts': 'Massachusetts',
            'NY': 'New York', 'New York': 'New York',
            'CA': 'California', 'California': 'California',
            'TX': 'Texas', 'Texas': 'Texas',
            'PA': 'Pennsylvania', 'Pennsylvania': 'Pennsylvania',
            'OH': 'Ohio', 'Ohio': 'Ohio',
            'MI': 'Michigan', 'Michigan': 'Michigan',
            'MD': 'Maryland', 'Maryland': 'Maryland',
            'NC': 'North Carolina', 'North Carolina': 'North Carolina',
        }

        for abbr, full in states.items():
            if abbr in location or full in location:
                return full

        return 'Illinois'  # Default

    def _parse_date_for_sciencv(self, date_str: str) -> str:
        """Parse various date formats to MM/YYYY for SciENcv."""
        import re

        # Already in MM/YYYY format
        if re.match(r'^\d{2}/\d{4}$', date_str):
            return date_str

        # Just year: YYYY -> 06/YYYY
        if re.match(r'^\d{4}$', date_str):
            return f"06/{date_str}"

        # Month Year: "Jun 2012" -> "06/2012"
        months = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }

        for month, num in months.items():
            if month in date_str.lower():
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    return f"{num}/{year_match.group()}"

        return date_str


async def run_automation(
    data_dict: Dict[str, Any],
    headless: bool = False,
    on_status: Optional[Callable[[str], None]] = None
) -> bool:
    """Run the SciENcv automation with provided data.

    Args:
        data_dict: Dictionary of biosketch data from the app
        headless: Whether to run headless (default False for login)
        on_status: Status callback function

    Returns:
        True if successful, False otherwise
    """
    data = BiosketchData.from_dict(data_dict)
    automation = SciENcvAutomation(
        data=data,
        headless=headless,
        on_status=on_status
    )
    return await automation.run()


# CLI entry point for testing
if __name__ == '__main__':
    import json
    import sys

    async def main():
        # Load test data from file or use sample
        if len(sys.argv) > 1:
            with open(sys.argv[1]) as f:
                data = json.load(f)
        else:
            # Sample data for testing
            data = {
                "name": "William Parker",
                "era_commons_username": "WILLIAMFPARKER",
                "position_title": "Assistant Professor",
                "education": [
                    {
                        "institution": "Williams College",
                        "degree": "Bachelor of Arts",
                        "completion_date": "2008",
                        "field_of_study": "Physics",
                        "location": "Williamstown, MA"
                    }
                ],
                "positions": [
                    {
                        "title": "Assistant Professor",
                        "institution": "University of Chicago",
                        "dates": "2021-Present"
                    }
                ],
                "honors": [],
                "personal_statement": {
                    "text": "Sample personal statement text...",
                    "grants": []
                },
                "contributions": [],
                "products": {"related": [], "other": []}
            }

        await run_automation(data, headless=False)

    asyncio.run(main())
