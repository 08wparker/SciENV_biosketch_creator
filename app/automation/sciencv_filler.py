"""SciENcv Biosketch Automation using Playwright.

This module automates filling in NIH Biographical Sketch Common Form entries
on SciENcv. Selectors are derived from Claude in Chrome browser extension
inspection (see claude_logs/ folder).

SELECTOR MAPPING (Claude in Chrome → Playwright):
  'button "TEXT"'   → get_by_role("button", name="TEXT")
  'textbox "LABEL"' → get_by_label("LABEL")  (strips asterisk, Material UI labels)
  'combobox "LABEL"'→ get_by_role("combobox", name="LABEL")
  'radio "TEXT"'    → get_by_role("radio", name="TEXT")
  'option "TEXT"'   → get_by_role("option", name="TEXT")
  'checkbox "TEXT"' → get_by_role("checkbox", name="TEXT")

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
import re
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# ==========================================================================
# HTML FORMATTING HELPERS
# SciENcv supports HTML in Personal Statement and Contributions to Science.
# Supported tags: <b>, <i>, <br>, <sup>, <sub>
# Reference: html_format_tips/SciENcv_HTML_Guide.pdf
# ==========================================================================

class HTMLFormatter:
    """Formats text with HTML tags for SciENcv fields."""

    # Common gene names to italicize
    GENE_NAMES = [
        'ACE2', 'BRCA1', 'BRCA2', 'TP53', 'EGFR', 'KRAS', 'BRAF', 'HER2',
        'CFTR', 'APOE', 'TNF', 'IL6', 'IL1B', 'VEGF', 'MYC', 'RAS', 'AKT',
        'PTEN', 'RB1', 'APC', 'MLH1', 'MSH2', 'CDKN2A', 'CDK4', 'JAK2',
        'BCR', 'ABL', 'FLT3', 'NPM1', 'IDH1', 'IDH2', 'DNMT3A', 'TET2',
    ]

    # Section headers commonly used in personal statements
    SECTION_HEADERS = [
        'Overview:', 'Expertise:', 'Commitment:', 'Background:',
        'Training:', 'Experience:', 'Qualifications:', 'Summary:',
        'Research Focus:', 'Clinical Focus:', 'Leadership:', 'Mentoring:',
        'Current and recently completed research support:',
    ]

    @classmethod
    def format_for_sciencv(cls, text: str, is_contribution: bool = False) -> str:
        """Apply all HTML formatting to text for SciENcv.

        Args:
            text: The text to format
            is_contribution: If True, also format contribution headers

        Returns:
            HTML-formatted text
        """
        if not text:
            return text

        # Apply formatting in order
        text = cls.format_scientific_notation(text)
        text = cls.format_gene_names(text)
        text = cls.format_section_headers(text)

        if is_contribution:
            text = cls.format_contribution_header(text)

        # Convert paragraph breaks (double newlines) to HTML
        text = cls.format_paragraph_breaks(text)

        return text

    @classmethod
    def format_contribution_header(cls, text: str) -> str:
        """Bold contribution headers and add line break after.

        Example: "Contribution 1: Topic here. My work..." becomes
                 "<b>Contribution 1: Topic here.</b><br>My work..."
        """
        # Match "Contribution N: " followed by text until first period
        pattern = r'^(Contribution\s+\d+:\s*[^.]+\.)\s*'
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            header = match.group(1)
            rest = text[match.end():]
            return f"<b>{header}</b><br>{rest}"
        return text

    @classmethod
    def format_section_headers(cls, text: str) -> str:
        """Bold common section headers.

        Example: "Overview: I am a researcher" becomes
                 "<b>Overview:</b> I am a researcher"
        """
        for header in cls.SECTION_HEADERS:
            # Case-insensitive replacement, preserving original case
            pattern = re.compile(re.escape(header), re.IGNORECASE)
            text = pattern.sub(lambda m: f"<b>{m.group(0)}</b>", text)
        return text

    @classmethod
    def format_scientific_notation(cls, text: str) -> str:
        """Convert scientific notation to superscript.

        Examples:
            - "10^8" -> "10<sup>8</sup>"
            - "R2" or "R^2" -> "R<sup>2</sup>"
            - "CO2" -> "CO<sub>2</sub>"
            - "H2O" -> "H<sub>2</sub>O"
        """
        # Handle explicit exponents: 10^8, 2^10, etc.
        text = re.sub(r'(\d+)\^(\d+)', r'\1<sup>\2</sup>', text)

        # Handle R-squared variants: R2, R^2
        text = re.sub(r'\bR\^?2\b', r'R<sup>2</sup>', text)

        # Handle p-values with exponents: p<10^-5, 10^-8
        text = re.sub(r'10\^(-?\d+)', r'10<sup>\1</sup>', text)

        # Handle common chemical formulas (subscripts)
        # CO2, H2O, O2, N2, etc. - be careful not to match gene names
        text = re.sub(r'\b(CO)2\b', r'\1<sub>2</sub>', text)
        text = re.sub(r'\b(H)2(O)\b', r'\1<sub>2</sub>\2', text)
        text = re.sub(r'\b(O)2\b', r'\1<sub>2</sub>', text)
        text = re.sub(r'\b(N)2\b', r'\1<sub>2</sub>', text)

        return text

    @classmethod
    def format_gene_names(cls, text: str) -> str:
        """Italicize known gene names.

        Example: "The ACE2 receptor" becomes "The <i>ACE2</i> receptor"
        """
        for gene in cls.GENE_NAMES:
            # Word boundary match to avoid partial matches
            pattern = re.compile(r'\b(' + re.escape(gene) + r')\b')
            text = pattern.sub(r'<i>\1</i>', text)
        return text

    @classmethod
    def format_paragraph_breaks(cls, text: str) -> str:
        """Convert double newlines to HTML paragraph breaks.

        Single newlines become <br>, double newlines become <br><br>.
        """
        # First normalize line endings
        text = text.replace('\r\n', '\n')

        # Double newlines -> paragraph break
        text = re.sub(r'\n\n+', '<br><br>', text)

        # Single newlines -> line break (but not if already followed by <br>)
        text = re.sub(r'\n(?!<br>)', '<br>', text)

        return text


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
    products: Dict[str, List[Dict[str, Any]]]

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
    """Automates filling in SciENcv biosketch forms.

    Selectors are from Claude in Chrome logs in claude_logs/ folder.
    """

    SCIENCV_URL = 'https://www.ncbi.nlm.nih.gov/labs/sciencv/'
    LOGIN_TIMEOUT = 300000  # 5 minutes
    SCREENSHOT_DIR = '/tmp'

    def __init__(
        self,
        data: BiosketchData,
        headless: bool = False,
        on_status: Optional[Callable[[str], None]] = None
    ):
        self.data = data
        self.headless = headless
        self.on_status = on_status or print
        self._page: Optional[Page] = None
        self._screenshot_counter = 0

    def _status(self, message: str):
        """Send status update."""
        self.on_status(f"[SciENcv] {message}")

    async def _screenshot(self, name: str, log: bool = True):
        """Take a screenshot for debugging."""
        if self._page:
            self._screenshot_counter += 1
            path = f"{self.SCREENSHOT_DIR}/sciencv_{self._screenshot_counter:02d}_{name}.png"
            try:
                await self._page.screenshot(path=path, full_page=False)
                if log:
                    self._status(f"Screenshot: {path}")
            except Exception as e:
                self._status(f"Could not take screenshot: {e}")

    async def run(self) -> bool:
        """Run the complete automation process."""
        try:
            async with async_playwright() as p:
                self._status("Launching browser...")
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()
                self._page = await context.new_page()

                # Step 1: Login
                if not await self._wait_for_login():
                    return False

                # Step 2: Create new document (from create_document.js)
                await self._create_document()

                # Step 3: Fill each section
                await self._fill_professional_preparation()  # Section A (section_a_education.js)
                await self._fill_appointments()              # Section B (section_b_appointments_positions.js)
                await self._fill_products()                  # Section C (section_c_products.js)
                await self._fill_personal_statement()        # Supplement A (supplement_a_personal_statement.js)
                await self._fill_honors()                    # Supplement B (supplement_b_honors.js)
                await self._fill_contributions()             # Supplement C (supplement_c_contributions.js)

                await self._screenshot("complete")
                self._status("Automation complete! Review your biosketch.")

                # Keep browser open for review
                self._status("Press Ctrl+C when done reviewing.")
                try:
                    await asyncio.sleep(3600)
                except asyncio.CancelledError:
                    pass

                return True

        except Exception as e:
            self._status(f"Error: {str(e)}")
            await self._screenshot("error_final")
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
            await self._screenshot("login_success")
            return True
        except Exception:
            pass

        self._status("Please log in to SciENcv in the browser window...")
        self._status("(You have 5 minutes to complete login with 2FA)")

        try:
            await self._page.wait_for_selector('text="My Documents"', timeout=self.LOGIN_TIMEOUT)
            self._status("Login successful!")
            await self._screenshot("login_success")
            return True
        except Exception:
            self._status("Login timed out. Please try again.")
            await self._screenshot("error_login_timeout")
            return False

    # ==========================================================================
    # CREATE DOCUMENT (from create_document.js)
    # Selectors:
    #   newDocumentButton: 'button "NEW DOCUMENT"'
    #   documentNameField: 'textbox "Document Name *"'
    #   documentTypeButton: 'button "Document type"'
    #   blankDocumentRadio: 'radio "Start with a blank document"'
    #   createButton: 'button "CREATE"'
    # ==========================================================================

    async def _create_document(self):
        """Create a new NIH Biographical Sketch document."""
        self._status("Creating new NIH Biographical Sketch...")

        # 1. Click NEW DOCUMENT button
        # Log: await click('button "NEW DOCUMENT"')
        await self._page.get_by_role("button", name="NEW DOCUMENT").click()
        await self._page.wait_for_timeout(1500)

        # 2. Wait for dialog - waitForElement('textbox "Document Name *"')
        await self._page.get_by_label("Document Name").wait_for(state='visible', timeout=10000)
        await self._screenshot("create_dialog")

        # 3. Generate document name with timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        doc_name = f"{self.data.name} {timestamp}"

        # 4. Enter Document Name
        # Log: await formInput('textbox "Document Name *"', config.documentName)
        self._status(f"  Document name: {doc_name}")
        await self._page.get_by_label("Document Name").fill(doc_name)
        await self._page.wait_for_timeout(500)

        # 5. Select Document Type
        # Log: await click('button "Document type"')
        # Log: await click('option "NIH Biographical Sketch Common Form"')
        self._status("  Selecting document type...")
        await self._page.get_by_label("Document type").click()
        await self._page.wait_for_timeout(500)
        await self._page.get_by_role("option", name="NIH Biographical Sketch Common Form").click()
        await self._page.wait_for_timeout(500)

        # 6. Select Data Source - blank document
        # Log: await click('radio "Start with a blank document"')
        self._status("  Selecting blank document...")
        await self._page.get_by_role("radio", name="Start with a blank document").click()
        await self._page.wait_for_timeout(300)
        await self._screenshot("create_form_filled")

        # 7. Click CREATE button
        # Log: await click('button "CREATE"')
        self._status("  Clicking CREATE...")
        await self._page.get_by_role("button", name="CREATE").click()
        await self._page.wait_for_load_state('networkidle')
        await self._page.wait_for_timeout(2000)
        await self._screenshot("document_created")
        self._status("Document created!")

    # ==========================================================================
    # SECTION A: PROFESSIONAL PREPARATION (from section_a_education.js)
    # Selectors:
    #   addButton: 'button "ADD PROFESSIONAL PREPARATION"'
    #   organizationField: 'textbox "Organization *"'
    #   cityField: 'textbox "City *"'
    #   stateDropdown: 'combobox "State/Province *"'
    #   degreeDropdown: 'combobox "Degree *"'  (or 'combobox "Training *"' for Training type)
    #   fieldOfStudyField: 'textbox "Field of Study *"'
    #   startDateField: 'textbox "Start Date"'
    #   endDateField: 'textbox "End Date"'
    #   trainingRadio: 'radio "Training"'
    #   saveButton: 'button "SAVE"'
    #   saveAndAddButton: 'button "SAVE & ADD ANOTHER ENTRY"'
    # ==========================================================================

    async def _fill_professional_preparation(self):
        """Fill Section A: Professional Preparation."""
        if not self.data.education:
            self._status("No education entries to add")
            return

        self._status(f"Adding {len(self.data.education)} education entries...")
        await self._screenshot("section_a_start")

        success_count = 0
        for i, edu in enumerate(self.data.education):
            is_first = (i == 0) or (success_count == 0)  # Treat as first if no successful entries yet
            is_last = (i == len(self.data.education) - 1)
            self._status(f"  [{i+1}/{len(self.data.education)}] {edu.get('institution', 'Unknown')} - {edu.get('degree', '')}")
            try:
                await self._add_education_entry(edu, is_first, is_last)
                success_count += 1
            except Exception as e:
                await self._screenshot(f"error_edu_{i}")
                self._status(f"    Error adding entry: {e}")
                # Try to close any open dialog
                try:
                    cancel_btn = self._page.get_by_role("button", name="CANCEL")
                    if await cancel_btn.is_visible():
                        await cancel_btn.click()
                        await self._page.wait_for_timeout(500)
                except Exception:
                    pass

        await self._screenshot("section_a_complete")
        self._status(f"Section A complete! ({success_count}/{len(self.data.education)} entries added)")

    async def _add_education_entry(self, edu: Dict[str, Any], is_first: bool = True, is_last: bool = False):
        """Add a single education/training entry.

        From section_a_education.js:
        1. Click ADD PROFESSIONAL PREPARATION button
        2. Wait for dialog to open
        3. Select Type (Degree or Training)
        4. Fill Organization
        5. Fill City
        6. Select State/Province
        7. Select Degree (or Training type)
        8. Fill Field of Study
        9. Fill Start Date
        10. Fill End Date
        11. Save
        """
        # 1. Click ADD button (only for first entry - dialog stays open after SAVE & ADD ANOTHER)
        if is_first:
            # Log: await click('button "ADD PROFESSIONAL PREPARATION"')
            self._status("    Clicking ADD PROFESSIONAL PREPARATION...")
            add_btn = self._page.get_by_role("button", name="ADD PROFESSIONAL PREPARATION")
            await add_btn.scroll_into_view_if_needed()
            await self._page.wait_for_timeout(500)
            await add_btn.click()
            await self._page.wait_for_timeout(1500)

        # 2. Wait for dialog - use label-based selector (not CSS #orgname)
        org_field = self._page.get_by_label("Organization", exact=False)
        await org_field.wait_for(state='visible', timeout=10000)
        if is_first:
            await self._screenshot("edu_dialog")

        # 3. Select Type (Degree or Training)
        degree = edu.get('degree', '').lower()
        is_training = any(t in degree for t in ['postdoc', 'fellow', 'resident', 'training', 'intern'])

        if is_training:
            self._status("    Type: Training")
            await self._page.get_by_role("radio", name="Training").click()
            await self._page.wait_for_timeout(500)

        # 4. Fill Organization
        # Parse institution - may contain location like "Williams College, Williamstown, MA"
        institution_raw = edu.get('institution', '')
        location = edu.get('location', '')

        # If location is empty, try to extract it from institution string
        if not location and ',' in institution_raw:
            # Split by comma and check if last parts look like city, state
            parts = [p.strip() for p in institution_raw.split(',')]
            if len(parts) >= 3:
                # Likely format: "Institution, City, State"
                org_name = parts[0]
                location = ', '.join(parts[1:])
            elif len(parts) == 2:
                # Could be "Institution, City State" or "Institution, Location"
                # Check if second part contains a state abbreviation
                if self._parse_state(parts[1]):
                    org_name = parts[0]
                    location = parts[1]
                else:
                    org_name = institution_raw
        else:
            org_name = institution_raw

        self._status(f"    Organization: {org_name}")
        await self._page.get_by_label("Organization", exact=False).first.fill(org_name)

        # 5. Fill City (required field)
        city = location.split(',')[0].strip() if location else ''
        if city:
            self._status(f"    City: {city}")
            await self._page.get_by_label("City", exact=False).first.fill(city)

        # 6. Select State/Province (required field)
        state = self._parse_state(location)
        if state:
            self._status(f"    State: {state}")
            try:
                state_field = self._page.get_by_label("State/Province", exact=False)
                await state_field.click()
                await self._page.wait_for_timeout(500)
                await self._page.keyboard.type(state[:4])
                await self._page.wait_for_timeout(800)
                try:
                    option = self._page.get_by_role("option", name=state).first
                    await option.wait_for(state='visible', timeout=2000)
                    await option.click()
                except Exception:
                    await self._page.keyboard.press('Enter')
                await self._page.wait_for_timeout(300)
            except Exception as e:
                self._status(f"    Warning: Could not set state: {e}")

        # 7. Select Degree or Training type (required field)
        degree_value = edu.get('degree', '')
        if degree_value:
            self._status(f"    Degree/Training: {degree_value}")
            try:
                # Map common training types to SciENcv dropdown options
                training_map = {
                    'fellow': 'Fellowship',
                    'fellowship': 'Fellowship',
                    'resident': 'Residency',
                    'residency': 'Residency',
                    'postdoc': 'Postdoctoral',
                    'postdoctoral': 'Postdoctoral',
                    'intern': 'Internship',
                    'internship': 'Internship',
                }

                if is_training:
                    # For Training type - try multiple selector strategies
                    dropdown = self._page.get_by_label("Training", exact=False)
                    search_text = training_map.get(degree_value.lower(), degree_value)
                else:
                    # For Degree type - try label-based selector
                    dropdown = self._page.get_by_label("Degree", exact=False)
                    # Strip parenthesized abbreviation for search
                    search_text = degree_value.split('(')[0].strip()

                # Click the dropdown to open it
                await dropdown.click()
                await self._page.wait_for_timeout(500)

                # Type to filter options
                await self._page.keyboard.type(search_text[:12])
                await self._page.wait_for_timeout(1000)

                # Try to click the first matching option
                try:
                    option = self._page.get_by_role("option").first
                    await option.wait_for(state='visible', timeout=3000)
                    await option.click()
                except Exception:
                    # Fallback: press Enter to select
                    await self._page.keyboard.press('Enter')
                await self._page.wait_for_timeout(300)

            except Exception as e:
                await self._screenshot("error_degree")
                self._status(f"    Warning: Could not set degree/training: {e}")

        # 8. Fill Field of Study
        self._status(f"    Field: {edu.get('field_of_study', '')}")
        await self._page.get_by_label("Field of Study *").fill(edu.get('field_of_study', ''))

        # 9. Fill Start Date (mm/yyyy format)
        start_date = edu.get('start_date', '')
        if start_date:
            parsed_start = self._parse_date_for_sciencv(start_date)
            self._status(f"    Start Date: {parsed_start}")
            await self._page.locator('input[placeholder="mm/yyyy"]').first.fill(parsed_start)

        # 10. Fill End Date (mm/yyyy format)
        completion_date = edu.get('completion_date', '')
        if completion_date:
            end_date = self._parse_date_for_sciencv(completion_date)
            self._status(f"    End Date: {end_date}")
            await self._page.locator('input[placeholder="mm/yyyy"]').last.fill(end_date)

        await self._screenshot("edu_entry", log=False)

        # 11. Save
        await self._page.wait_for_timeout(500)
        if is_last:
            # Log: await click('button "SAVE"')
            self._status("    Clicking SAVE...")
            await self._page.get_by_role("button", name="SAVE", exact=True).click()
            await self._page.wait_for_timeout(2000)
        else:
            # Log: await click('button "SAVE & ADD ANOTHER ENTRY"')
            self._status("    Clicking SAVE & ADD ANOTHER ENTRY...")
            await self._page.get_by_role("button", name="SAVE & ADD ANOTHER ENTRY").click()
            await self._page.wait_for_timeout(1500)

        # Check if dialog is still open (required field validation failed)
        # If so, cancel and continue to prevent blocking subsequent sections
        if is_last:
            try:
                dialog_title = self._page.locator('text="Add Professional Preparation"')
                if await dialog_title.is_visible():
                    self._status("    Warning: Dialog still open - required fields may be missing")
                    await self._screenshot("edu_dialog_stuck")
                    cancel_btn = self._page.get_by_role("button", name="CANCEL")
                    if await cancel_btn.is_visible():
                        await cancel_btn.click()
                        await self._page.wait_for_timeout(1000)
            except Exception:
                pass

    # ==========================================================================
    # SECTION B: APPOINTMENTS AND POSITIONS (from section_b_appointments_positions.js)
    # Selectors:
    #   addButton: 'button "ADD APPOINTMENT/POSITION"'
    #   positionTitle: label "Appointment or Position Title *"
    #   organization: label "Name of Organization/Department"
    #   city: label "City *"
    #   stateDropdown: 'combobox "State/Province *"'
    #   startYear: 'input[placeholder="yyyy"]' first
    #   endYear: 'input[placeholder="yyyy"]' second
    #   saveAndAdd: 'button "SAVE & ADD ANOTHER ENTRY"'
    #   save: 'button "SAVE"'
    # ==========================================================================

    async def _fill_appointments(self):
        """Fill Section B: Appointments and Positions.

        SciENcv auto-populates the current appointment from eRA Commons,
        but without date/location. If a position is flagged as primary,
        we edit the existing entry instead of adding a duplicate.
        """
        if not self.data.positions:
            self._status("No positions to add")
            return

        # Separate primary from other positions
        primary = None
        others = []
        for pos in self.data.positions:
            if pos.get('primary'):
                primary = pos
            else:
                others.append(pos)

        self._status(f"Processing {len(self.data.positions)} appointments/positions...")
        await self._screenshot("section_b_start")

        # Step 1: Edit existing primary appointment (auto-populated by SciENcv)
        if primary:
            await self._edit_primary_appointment(primary)

        # Step 2: Add remaining positions
        success_count = 0
        for i, pos in enumerate(others):
            is_first = (i == 0) or (success_count == 0)
            is_last = (i == len(others) - 1)
            self._status(f"  [{i+1}/{len(others)}] {pos.get('title', 'Unknown')}")
            try:
                await self._add_appointment_entry(pos, is_first, is_last)
                success_count += 1
            except Exception as e:
                await self._screenshot(f"error_appt_{i}")
                self._status(f"    Error adding entry: {e}")
                # Try to close any open dialog
                try:
                    cancel_btn = self._page.get_by_role("button", name="CANCEL")
                    if await cancel_btn.is_visible():
                        await cancel_btn.click()
                        await self._page.wait_for_timeout(500)
                except Exception:
                    pass

        await self._screenshot("section_b_complete")
        self._status(f"Section B complete! ({success_count}/{len(others)} entries added)")

    async def _edit_primary_appointment(self, pos: Dict[str, Any]):
        """Handle the primary/current appointment.

        SciENcv auto-populates the current appointment from eRA Commons profile.
        Editing it programmatically is fragile (the edit button can match the
        profile section instead of the appointments table). Instead, we skip
        the primary position and notify the user to manually verify it.
        """
        self._status(f"  Primary appointment: {pos.get('title', '')}")
        self._status("  NOTE: SciENcv auto-populates your current appointment from eRA Commons.")
        self._status("  Please verify date, location, and other fields for your current position.")
        self._status("  Skipping primary - will add remaining positions...")

    async def _add_appointment_entry(self, pos: Dict[str, Any], is_first: bool = True, is_last: bool = False):
        """Add a single appointment/position entry."""
        # 1. Click ADD button
        if is_first:
            self._status("    Clicking ADD APPOINTMENT/POSITION...")
            add_button = self._page.get_by_role("button", name="ADD APPOINTMENT/POSITION")
            await add_button.scroll_into_view_if_needed()
            await self._page.wait_for_timeout(500)
            await add_button.click()
            await self._page.wait_for_timeout(1500)
            await self._screenshot("appt_dialog")

        # 2. Wait for dialog
        title_input = self._page.get_by_label("Appointment or Position Title", exact=False)
        await title_input.wait_for(state='visible', timeout=10000)

        # 3. Fill Position Title
        self._status(f"    Title: {pos.get('title', '')}")
        await title_input.fill(pos.get('title', ''))

        # 4. Fill Organization
        self._status(f"    Organization: {pos.get('institution', '')}")
        await self._page.get_by_label("Name of Organization", exact=False).fill(pos.get('institution', ''))

        # 5. Fill City (required by SciENcv)
        location = pos.get('location', '')
        city = location.split(',')[0].strip() if location else ''
        if city:
            self._status(f"    City: {city}")
            await self._page.get_by_label("City", exact=False).first.fill(city)

        # 6. Select State/Province (required by SciENcv)
        state = self._parse_state(location) if location else ''
        if state:
            self._status(f"    State: {state}")
            try:
                state_field = self._page.get_by_label("State/Province", exact=False)
                await state_field.click()
                await self._page.wait_for_timeout(500)
                await self._page.keyboard.type(state[:4])
                await self._page.wait_for_timeout(800)
                try:
                    option = self._page.get_by_role("option", name=state).first
                    await option.wait_for(state='visible', timeout=2000)
                    await option.click()
                except Exception:
                    await self._page.keyboard.press('Enter')
                await self._page.wait_for_timeout(300)
            except Exception as e:
                self._status(f"    Warning: Could not set state: {e}")

        # 7. Parse dates (format: "2021-Present" or "2015-2019")
        dates = pos.get('dates', '').replace('–', '-').replace('—', '-')
        parts = dates.split('-')
        start_year = parts[0].strip() if parts else ''
        end_year = parts[1].strip() if len(parts) > 1 else ''

        # 6. Fill Start Year
        if start_year:
            self._status(f"    Start Year: {start_year}")
            await self._page.locator('input[placeholder="yyyy"]').first.fill(start_year)

        # 7. Fill End Year (if not "Present")
        if end_year and end_year.lower() != 'present':
            self._status(f"    End Year: {end_year}")
            await self._page.locator('input[placeholder="yyyy"]').nth(1).fill(end_year)

        # 8. Save
        await self._page.wait_for_timeout(500)
        if is_last:
            self._status("    Clicking SAVE...")
            await self._page.get_by_role("button", name="SAVE", exact=True).click()
            await self._page.wait_for_timeout(2000)
        else:
            self._status("    Clicking SAVE & ADD ANOTHER ENTRY...")
            await self._page.get_by_role("button", name="SAVE & ADD ANOTHER ENTRY").click()
            await self._page.wait_for_timeout(1500)

    # ==========================================================================
    # SECTION C: PRODUCTS (from section_c_products.js)
    # Selectors:
    #   selectRelatedButton: 'button "SELECT RELATED PRODUCTS"'
    #   selectOtherButton: 'button "SELECT OTHER PRODUCTS"'
    #   searchInput: 'textbox "Search citations"'
    #   citationCheckbox: 'checkbox "Citation for:"'
    #   continueButton: 'button "CONTINUE"'
    # ==========================================================================

    async def _fill_products(self):
        """Fill Section C: Products."""
        related = self.data.products.get('related', [])
        other = self.data.products.get('other', [])

        if not related and not other:
            self._status("No products to add")
            return

        self._status("Adding products...")
        await self._screenshot("section_c_start")

        if related:
            self._status(f"  Adding {len(related)} related products...")
            # Log: await click('button "SELECT RELATED PRODUCTS"')
            await self._add_products_section(related, "SELECT RELATED PRODUCTS")

        if other:
            self._status(f"  Adding {len(other)} other products...")
            # Log: await click('button "SELECT OTHER PRODUCTS"')
            await self._add_products_section(other, "SELECT OTHER PRODUCTS")

        await self._screenshot("section_c_complete")
        self._status("Section C complete!")

    async def _add_products_section(self, products: List[Dict[str, Any]], button_name: str):
        """Add products to a specific section."""
        # 1. Click SELECT button
        self._status(f"    Clicking {button_name}...")
        select_button = self._page.get_by_role("button", name=button_name)
        await select_button.scroll_into_view_if_needed()
        await select_button.click()
        await self._page.wait_for_timeout(1000)
        await self._screenshot("products_dialog")

        for product in products:
            pmid = product.get('pmid', '')
            if pmid:
                self._status(f"    Searching PMID: {pmid}")
                # Log: const searchInput = await find('textbox "Search citations"')
                # Log: await tripleClick(searchInput)
                # Log: await type(product.pmid)
                # Log: await pressKey('Return')
                search_input = self._page.get_by_label("Search citations")
                await search_input.click()
                await search_input.fill('')
                await search_input.fill(pmid)
                await self._page.keyboard.press('Enter')
                await self._page.wait_for_timeout(1500)

                # Log: const checkbox = await find('checkbox "Citation for:"')
                # Log: await click(checkbox)
                try:
                    checkbox = self._page.get_by_role("checkbox").first
                    await checkbox.click()
                    await self._page.wait_for_timeout(300)
                except Exception as e:
                    self._status(f"    Could not select PMID {pmid}: {e}")

        # Log: await click('button "CONTINUE"')
        self._status("    Clicking CONTINUE...")
        await self._page.get_by_role("button", name="CONTINUE").click()
        await self._page.wait_for_timeout(1000)

    # ==========================================================================
    # SUPPLEMENT A: PERSONAL STATEMENT (from supplement_a_personal_statement.js)
    # Selectors:
    #   addButton: 'button "ADD PERSONAL STATEMENT"'
    #   textArea: 'textarea'
    #   saveButton: 'button "SAVE"'
    # ==========================================================================

    async def _fill_personal_statement(self):
        """Fill Supplement A: Personal Statement."""
        ps = self.data.personal_statement
        if not ps or not ps.get('text'):
            self._status("No personal statement to add")
            return

        self._status("Adding personal statement...")
        await self._screenshot("supplement_a_start")

        # Build full text including grants
        text = ps.get('text', '')

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
                text += f"{funder} {number}\t{pi} ({role})\t{dates}\n{title}\n\n"

        # Apply HTML formatting for better readability
        self._status("  Applying HTML formatting...")
        text = HTMLFormatter.format_for_sciencv(text, is_contribution=False)

        # Enforce 3,500 character limit (after formatting)
        if len(text) > 3500:
            self._status(f"  Warning: Text is {len(text)} chars (limit: 3,500), truncating")
            text = text[:3500]

        # Log: await page.click('button:has-text("ADD PERSONAL STATEMENT")')
        self._status("  Clicking ADD PERSONAL STATEMENT...")
        add_button = self._page.get_by_role("button", name="ADD PERSONAL STATEMENT")
        await add_button.scroll_into_view_if_needed()
        await add_button.click()
        await self._page.wait_for_timeout(1000)

        # Log: await page.fill('textarea', personalStatement.text)
        self._status(f"  Filling text ({len(text)} characters)...")
        await self._page.locator('textarea').first.fill(text)
        await self._screenshot("ps_filled")

        # Log: await page.click('button:has-text("SAVE")')
        self._status("  Clicking SAVE...")
        await self._page.get_by_role("button", name="SAVE", exact=True).click()
        await self._page.wait_for_timeout(1000)
        await self._screenshot("supplement_a_complete")
        self._status("Supplement A complete!")

    # ==========================================================================
    # SUPPLEMENT B: HONORS (from supplement_b_honors.js)
    # Selectors:
    #   addButton: 'button "ADD HONOR"'
    #   honorField: label "Honor *"
    #   organizationField: label "Name of Organization *"
    #   yearField: input[placeholder="yyyy"]
    #   saveAndAddButton: 'button "SAVE & ADD ANOTHER"'
    #   saveButton: 'button "SAVE"'
    # ==========================================================================

    async def _fill_honors(self):
        """Fill Supplement B: Honors (max 10)."""
        if not self.data.honors:
            self._status("No honors to add")
            return

        honors = self.data.honors[:10]  # NIH limits to 10
        self._status(f"Adding {len(honors)} honors...")
        await self._screenshot("supplement_b_start")

        for i, honor in enumerate(honors):
            is_first = (i == 0)
            is_last = (i == len(honors) - 1)
            self._status(f"  [{i+1}/{len(honors)}] {honor.get('year', '')} - {honor.get('description', '')[:30]}...")
            await self._add_honor_entry(honor, is_first, is_last)

        await self._screenshot("supplement_b_complete")
        self._status("Supplement B complete!")

    async def _add_honor_entry(self, honor: Dict[str, Any], is_first: bool = True, is_last: bool = False):
        """Add a single honor entry."""
        # 1. Click ADD button
        if is_first:
            self._status("    Clicking ADD HONOR...")
            add_button = self._page.get_by_role("button", name="ADD HONOR")
            await add_button.scroll_into_view_if_needed()
            await add_button.click()
            await self._page.wait_for_timeout(1000)
            await self._screenshot("honor_dialog")

        # 2. Fill Honor field (use "Honor *" with asterisk to uniquely match the input,
        #    not the section or dialog which also match "Honor")
        self._status(f"    Honor: {honor.get('description', '')[:40]}...")
        await self._page.get_by_label("Honor *").fill(honor.get('description', ''))

        # 3. Fill Organization field (use asterisk for unique match)
        org = honor.get('organization', '')
        if org:
            self._status(f"    Organization: {org[:30]}...")
            await self._page.get_by_label("Name of Organization *").fill(org)

        # 4. Fill Year field
        year = honor.get('year', '')
        if year:
            self._status(f"    Year: {year}")
            await self._page.locator('input[placeholder="yyyy"]').first.fill(year)

        # 5. Save
        await self._page.wait_for_timeout(500)
        if is_last:
            self._status("    Clicking SAVE...")
            await self._page.get_by_role("button", name="SAVE", exact=True).click()
            await self._page.wait_for_timeout(2000)
        else:
            # Log: button "SAVE & ADD ANOTHER"
            self._status("    Clicking SAVE & ADD ANOTHER...")
            await self._page.get_by_role("button", name="SAVE & ADD ANOTHER").click()
            await self._page.wait_for_timeout(1500)

    # ==========================================================================
    # SUPPLEMENT C: CONTRIBUTIONS TO SCIENCE (from supplement_c_contributions.js)
    # Selectors:
    #   addButton: 'button "ADD CONTRIBUTION TO SCIENCE"'
    #   addAnotherButton: 'button "ADD ANOTHER CONTRIBUTION TO SCIENCE"'
    #   descriptionField: 'textarea'
    #   saveButton: 'button "SAVE"'
    # ==========================================================================

    async def _fill_contributions(self):
        """Fill Supplement C: Contributions to Science (max 5)."""
        if not self.data.contributions:
            self._status("No contributions to add")
            return

        contributions = self.data.contributions[:5]  # NIH limits to 5
        self._status(f"Adding {len(contributions)} contributions to science...")
        await self._screenshot("supplement_c_start")

        for i, contrib in enumerate(contributions):
            is_first = (i == 0)
            narrative_preview = contrib.get('narrative', '')[:40]
            self._status(f"  [{i+1}/{len(contributions)}] {narrative_preview}...")
            await self._add_contribution_entry(contrib, is_first)

        await self._screenshot("supplement_c_complete")
        self._status("Supplement C complete!")

    async def _add_contribution_entry(self, contrib: Dict[str, Any], is_first: bool = True):
        """Add a single contribution entry."""
        # 1. Click add button
        if is_first:
            # Log: await page.click('button:has-text("ADD CONTRIBUTION TO SCIENCE")')
            self._status("    Clicking ADD CONTRIBUTION TO SCIENCE...")
            add_button = self._page.get_by_role("button", name="ADD CONTRIBUTION TO SCIENCE").first
            await add_button.scroll_into_view_if_needed()
            await add_button.click()
        else:
            # Log: await page.click('button:has-text("ADD ANOTHER CONTRIBUTION TO SCIENCE")')
            # Use .first because multiple buttons may match after adding previous contributions
            self._status("    Clicking ADD ANOTHER CONTRIBUTION TO SCIENCE...")
            add_another = self._page.get_by_role("button", name="ADD ANOTHER CONTRIBUTION TO SCIENCE").first
            await add_another.scroll_into_view_if_needed()
            await add_another.click()
        await self._page.wait_for_timeout(1000)

        # 2. Build narrative with citations included
        # SciENcv contributions don't have a separate citation UI;
        # citations should be embedded in the narrative text.
        narrative = contrib.get('narrative', '')
        citations = contrib.get('citations', [])
        if citations:
            citation_texts = []
            for c in citations:
                text = c.get('text', '')
                pmid = c.get('pmid', '')
                if text:
                    citation_texts.append(text)
                elif pmid:
                    citation_texts.append(f"PMID: {pmid}")
            if citation_texts:
                narrative += "\n\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(citation_texts))

        # Apply HTML formatting for better readability
        self._status("    Applying HTML formatting...")
        narrative = HTMLFormatter.format_for_sciencv(narrative, is_contribution=True)

        # Enforce 2,000 character limit (after formatting)
        if len(narrative) > 2000:
            self._status(f"    Warning: Text is {len(narrative)} chars (limit: 2,000), truncating")
            narrative = narrative[:2000]

        self._status(f"    Filling narrative ({len(narrative)} characters)...")
        await self._page.locator('textarea').first.fill(narrative)

        # 3. Save
        self._status("    Clicking SAVE...")
        await self._page.get_by_role("button", name="SAVE", exact=True).click()
        await self._page.wait_for_timeout(2000)
        await self._screenshot("contrib_saved")

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _parse_state(self, location: str) -> str:
        """Parse state from location string."""
        states = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
        }
        # Also add full names as keys
        full_names = {v: v for v in states.values()}
        states.update(full_names)

        for abbr, full in states.items():
            if abbr in location:
                return full
        return ''  # Return empty if no state found

    def _parse_date_for_sciencv(self, date_str: str) -> str:
        """Parse date to MM/YYYY format for SciENcv."""
        import re

        # Already in correct format
        if re.match(r'^\d{2}/\d{4}$', date_str):
            return date_str

        # Just a year - assume June
        if re.match(r'^\d{4}$', date_str):
            return f"06/{date_str}"

        # Try to parse month names
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
    """Run the SciENcv automation with provided data."""
    data = BiosketchData.from_dict(data_dict)
    automation = SciENcvAutomation(
        data=data,
        headless=headless,
        on_status=on_status
    )
    return await automation.run()


# CLI entry point
if __name__ == '__main__':
    import json
    import sys

    async def main():
        if len(sys.argv) > 1:
            with open(sys.argv[1]) as f:
                data = json.load(f)
        else:
            data = {
                "name": "Test User",
                "era_commons_username": "TESTUSER",
                "position_title": "Assistant Professor",
                "education": [],
                "positions": [],
                "honors": [],
                "personal_statement": {"text": "", "grants": []},
                "contributions": [],
                "products": {"related": [], "other": []}
            }
        await run_automation(data, headless=False)

    asyncio.run(main())
