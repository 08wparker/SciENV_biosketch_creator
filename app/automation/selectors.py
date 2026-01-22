"""CSS Selectors for SciENcv web interface.

These selectors may need to be updated if the SciENcv interface changes.
Keep all selectors in one place for easy maintenance.
"""


class SciENcvSelectors:
    """CSS selectors for SciENcv elements."""

    # ============ Authentication ============
    LOGIN_BUTTON = 'button:has-text("Log In"), a:has-text("Log In")'
    LOGGED_IN_INDICATOR = 'text=My Documents, text=My NCBI'

    # ============ Document Management ============
    MY_DOCUMENTS = 'text=My Documents'
    NEW_DOCUMENT = 'button:has-text("New Document"), a:has-text("New Document")'
    NIH_BIOSKETCH = 'text=NIH Biographical Sketch'
    DOCUMENT_TITLE_INPUT = 'input[name="documentTitle"], input[placeholder*="title"]'

    # ============ General Form Elements ============
    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'
    ADD_BUTTON = 'button:has-text("Add")'
    EDIT_BUTTON = 'button:has-text("Edit")'
    DELETE_BUTTON = 'button:has-text("Delete")'
    NEXT_BUTTON = 'button:has-text("Next")'
    DONE_BUTTON = 'button:has-text("Done")'

    # ============ Education/Training Section ============
    EDUCATION_SECTION = 'text=Education/Training'
    ADD_EDUCATION = 'button:has-text("Add Education"), button:has-text("Add Training")'
    INSTITUTION_INPUT = 'input[name*="institution"], input[placeholder*="Institution"]'
    DEGREE_INPUT = 'input[name*="degree"], select[name*="degree"]'
    COMPLETION_DATE_INPUT = 'input[name*="date"], input[placeholder*="MM/YYYY"]'
    FIELD_OF_STUDY_INPUT = 'input[name*="field"], input[placeholder*="Field"]'

    # ============ Personal Statement Section ============
    PERSONAL_STATEMENT_SECTION = 'text=Personal Statement'
    PERSONAL_STATEMENT_TEXTAREA = 'textarea[name*="personalStatement"], textarea[placeholder*="Personal Statement"]'

    # ============ Positions Section ============
    POSITIONS_SECTION = 'text=Positions'
    ADD_POSITION = 'button:has-text("Add Position")'
    POSITION_TITLE_INPUT = 'input[name*="title"], input[placeholder*="Title"]'
    POSITION_ORG_INPUT = 'input[name*="organization"], input[placeholder*="Organization"]'
    POSITION_START_DATE = 'input[name*="startDate"]'
    POSITION_END_DATE = 'input[name*="endDate"]'

    # ============ Honors Section ============
    HONORS_SECTION = 'text=Honors'
    ADD_HONOR = 'button:has-text("Add Honor")'
    HONOR_YEAR_INPUT = 'input[name*="year"]'
    HONOR_DESCRIPTION_INPUT = 'input[name*="description"], textarea[name*="description"]'

    # ============ Contributions Section ============
    CONTRIBUTIONS_SECTION = 'text=Contributions to Science'
    ADD_CONTRIBUTION = 'button:has-text("Add Contribution")'
    CONTRIBUTION_NARRATIVE = 'textarea[name*="contribution"], textarea[name*="narrative"]'

    # ============ Citations Section ============
    ADD_CITATION = 'button:has-text("Add Citation"), button:has-text("Add Publication")'
    CITATION_SEARCH = 'input[name*="citation"], input[placeholder*="Search"]'
    PMID_INPUT = 'input[name*="pmid"], input[placeholder*="PMID"]'

    # ============ Navigation ============
    SECTIONS_NAV = '.sections-nav, nav.document-sections'
    SECTION_LINK_TEMPLATE = 'a:has-text("{section_name}")'

    @classmethod
    def section_link(cls, section_name: str) -> str:
        """Get selector for a specific section navigation link."""
        return cls.SECTION_LINK_TEMPLATE.format(section_name=section_name)
