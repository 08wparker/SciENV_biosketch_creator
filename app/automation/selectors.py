"""Accessibility-based selectors for SciENcv web interface.

These selectors are derived from Claude in Chrome browser extension inspection
of the SciENcv website. They use ARIA roles and labels for reliability.

Playwright methods to use:
- page.get_by_role("button", name="...")
- page.get_by_role("textbox", name="...")
- page.get_by_role("combobox", name="...")
- page.get_by_role("radio", name="...")
- page.get_by_role("checkbox", name="...")
- page.get_by_role("option", name="...")
"""


class Selectors:
    """Accessibility-based selectors organized by section."""

    # ============ Authentication ============
    class Auth:
        LOGGED_IN_INDICATOR = 'text="My Documents"'
        SCIENCV_URL = 'https://www.ncbi.nlm.nih.gov/labs/sciencv/'

    # ============ Create New Document ============
    class CreateDocument:
        # Buttons
        NEW_DOCUMENT_BUTTON = ("button", "NEW DOCUMENT")
        CREATE_BUTTON = ("button", "CREATE")

        # Form fields
        DOCUMENT_NAME = ("textbox", "Document Name *")
        DOCUMENT_TYPE = ("button", "Document type")  # Opens dropdown

        # Radio buttons for data source
        EXTERNAL_SOURCE = ("radio", "Use an external source")
        EXISTING_DOCUMENT = ("radio", "Use an existing document in SciENcv")
        BLANK_DOCUMENT = ("radio", "Start with a blank document")

        # Dropdowns (when data source selected)
        SOURCE_DROPDOWN = ("combobox", "Source *")
        DOCUMENT_DROPDOWN = ("combobox", "Document *")

        # Document type option
        NIH_BIOSKETCH_OPTION = "NIH Biographical Sketch Common Form"

    # ============ A. Professional Preparation (Education) ============
    class Education:
        ADD_BUTTON = ("button", "ADD PROFESSIONAL PREPARATION")

        # Type selection
        DEGREE_RADIO = ("radio", "Degree")  # Default
        TRAINING_RADIO = ("radio", "Training")

        # Form fields
        ORGANIZATION = ("textbox", "Organization *")
        CITY = ("textbox", "City *")
        COUNTRY = ("combobox", "Country *")
        STATE = ("combobox", "State/Province *")
        DEGREE = ("combobox", "Degree *")
        FIELD_OF_STUDY = ("textbox", "Field of Study *")
        START_DATE = ("textbox", "Start Date")
        END_DATE = ("textbox", "End Date")

        # Save buttons
        SAVE_BUTTON = ("button", "SAVE")
        SAVE_AND_ADD_BUTTON = ("button", "SAVE & ADD ANOTHER ENTRY")

    # ============ B. Appointments and Positions ============
    class Appointments:
        ADD_BUTTON = ("button", "ADD APPOINTMENT/POSITION")

        # Form fields
        TITLE = ("textbox", "Title *")
        ORGANIZATION = ("textbox", "Organization/Department *")
        CITY = ("textbox", "City")
        COUNTRY = ("combobox", "Country")
        STATE = ("combobox", "State/Province")
        START_YEAR = ("textbox", "Start Year *")
        END_YEAR = ("textbox", "End Year")
        CURRENT_POSITION = ("checkbox", "Current Position")

        # Save buttons
        SAVE_BUTTON = ("button", "SAVE")
        SAVE_AND_ADD_BUTTON = ("button", "SAVE & ADD ANOTHER")

    # ============ C. Products ============
    class Products:
        # Selection buttons
        SELECT_RELATED_BUTTON = ("button", "SELECT RELATED PRODUCTS")
        SELECT_OTHER_BUTTON = ("button", "SELECT OTHER PRODUCTS")

        # Search and selection
        SEARCH_INPUT = ("textbox", "Search citations")
        CITATION_CHECKBOX = ("checkbox", "Citation for:")

        # Save
        CONTINUE_BUTTON = ("button", "CONTINUE")

    # ============ Supplement A. Personal Statement ============
    class PersonalStatement:
        ADD_BUTTON = ("button", "ADD PERSONAL STATEMENT")

        # Form field - character limit is 3,500
        TEXT_AREA = ("textbox", "Personal Statement *")

        # Save buttons
        SAVE_BUTTON = ("button", "SAVE")
        CANCEL_BUTTON = ("button", "CANCEL")

    # ============ Supplement B. Honors ============
    class Honors:
        ADD_BUTTON = ("button", "ADD HONOR")

        # Form fields
        HONOR = ("textbox", "Honor *")
        ORGANIZATION = ("textbox", "Name of Organization *")
        YEAR = ("textbox", "Year *")  # Format: yyyy
        END_YEAR = ("textbox", "End Year")  # Optional, for date ranges

        # Save buttons
        SAVE_BUTTON = ("button", "SAVE")
        SAVE_AND_ADD_BUTTON = ("button", "SAVE & ADD ANOTHER")

    # ============ Supplement C. Contributions to Science ============
    class Contributions:
        ADD_BUTTON = ("button", "ADD CONTRIBUTION TO SCIENCE")
        ADD_ANOTHER_BUTTON = ("button", "ADD ANOTHER CONTRIBUTION TO SCIENCE")

        # Form field - character limit is 2,000 per contribution
        DESCRIPTION = ("textbox", "Description")  # or textarea

        # Save buttons
        SAVE_BUTTON = ("button", "SAVE")
        CANCEL_BUTTON = ("button", "CANCEL")

        # After saving, citation buttons appear
        ADD_CITATION_BUTTON = ("button", "ADD CITATION")

    # ============ Citation Selection (shared) ============
    class Citations:
        SEARCH_INPUT = ("textbox", "Search")
        PMID_INPUT = ("textbox", "PMID")
        CITATION_CHECKBOX = ("checkbox", "")  # Dynamic based on citation
        SELECT_BUTTON = ("button", "SELECT")
        CANCEL_BUTTON = ("button", "CANCEL")


# Legacy class for backwards compatibility
class SciENcvSelectors:
    """Legacy selectors - deprecated, use Selectors class instead."""

    LOGGED_IN_INDICATOR = 'text="My Documents"'
    MY_DOCUMENTS = 'text="My Documents"'
    NEW_DOCUMENT = 'button:has-text("NEW DOCUMENT")'
    SAVE_BUTTON = 'button:has-text("SAVE")'
