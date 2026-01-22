# SciENcv Biosketch Creator - Project Rules

## Reference Materials

When working on this project, always refer to these resources for understanding the NIH biosketch format and SciENcv web interface:

### NIH Instructions Document
- **Location**: `NIH_instructions/Common Form NIH Biographical Sketch_FINAL.pdf`
- **Purpose**: Official NIH instructions for the Biographical Sketch Common Form
- **Key sections**:
  - Identifying Information (Name, PID/ORCID, Position Title, Organization)
  - Professional Preparation (education/training in reverse chronological order)
  - Appointments and Positions (reverse chronological order)
  - Products: TWO subsections, each with up to 5 items:
    1. **Products closely related to the proposed project** (up to 5)
    2. **Other Significant Products highlighting Contributions to Science** (up to 5)
  - Certification

### SciENcv Website Screenshots
- **Location**: `screenshots/scienv_webpage_screenshots/`
- **Purpose**: Visual reference for the actual SciENcv web interface at https://www.ncbi.nlm.nih.gov/labs/sciencv/
- **Screenshots show**:
  - Main biosketch form layout
  - Section structure (A. Professional Preparation, B. Appointments and Positions, C. Products)
  - Products section with "SELECT RELATED PRODUCTS" and "SELECT OTHER PRODUCTS" buttons
  - NIH Biographical Sketch Supplement (Personal Statement, Honors, Contributions to Science)
  - Edit/Delete controls for each entry

## Key Implementation Rules

### Products Section
- Products are split into TWO categories (not one):
  1. "Products Closely Related to the Proposed Project" - up to 5
  2. "Other Significant Products Highlighting Contributions to Science" - up to 5
- Citations should be pulled from BOTH:
  - Personal statement citations
  - Contribution citations (from all contributions)
- User selects which citations go into which product category

### SciENcv Sections Mapping
| Our Parser Section | SciENcv Section |
|-------------------|-----------------|
| education | A. Professional Preparation |
| positions | B. Appointments and Positions |
| personal_statement.citations + contributions.citations | C. Products |
| personal_statement | NIH Supplement: A. Personal Statement |
| honors | NIH Supplement: B. Honors |
| contributions | NIH Supplement: C. Contributions to Science |

### Automation Notes
- SciENcv requires Login.gov authentication with 2FA
- Browser automation runs in headed mode so user can manually login
- Each section has "ADD" buttons and Edit/Delete icons for entries
- Products are selected via "SELECT RELATED PRODUCTS" and "SELECT OTHER PRODUCTS" buttons

## Database
- SQLite database located at: `instance/sciencv.db`
- Contains User and SavedBiosketch tables
- Logged-in users can save and resume editing biosketches
