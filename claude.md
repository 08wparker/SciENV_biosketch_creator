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

### Design Assets
- **Location**: `website_design_items/`
- **HCA Lab Logo**: `hca_lab_logo.png` - Health Care Allocations Lab logo (used in nav)
- **CLIF Logo**: `CLIF_logo.png` - CLIF Consortium logo (used in nav and footer)

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

## Backend Architecture

### Authentication (Firebase Auth)
- **Provider**: Firebase Authentication
- **Methods**: Email/Password and Google Sign-In
- **Frontend**: Firebase JS SDK (client-side auth)
- **Backend**: Firebase Admin SDK (token verification)
- **Key files**:
  - `app/firebase_config.py` - Firebase Admin SDK initialization and auth decorators
  - `app/api/auth.py` - Auth routes and API endpoints
- **Decorators**:
  - `@firebase_auth_required` - Requires valid Firebase ID token
  - `@firebase_auth_optional` - Works with or without authentication

### Database (Cloud Firestore)
- **Provider**: Google Cloud Firestore
- **Collection**: `biosketches`
- **Document structure**:
  ```
  biosketches/{job_id}
    - job_id: string
    - user_id: string (Firebase Auth UID)
    - name: string
    - data: map (full parsed biosketch)
    - selected_contributions: array
    - selected_products: map { related: array, other: array }
    - created_at: timestamp
    - updated_at: timestamp
  ```
- **Key files**:
  - `app/firestore_models.py` - CRUD operations for Firestore

### Environment Variables
Required in `.env` file:
```
# Flask
SECRET_KEY=your-secret-key
FLASK_ENV=development

# Firebase Admin SDK
FIREBASE_CREDENTIALS=firebase-service-account.json
FIREBASE_PROJECT_ID=sciencv-biosketch

# Firebase Web Config (for frontend)
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=sciencv-biosketch.firebaseapp.com
FIREBASE_STORAGE_BUCKET=sciencv-biosketch.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=...
FIREBASE_APP_ID=...
```

### Deployment
- **Target**: Google Cloud Run
- **Dockerfile**: Configured for Cloud Run with gunicorn
- **Port**: 8080 (Cloud Run default)

## Branding

### Color Scheme
- **Primary**: UChicago Maroon (#800000)
- **Tailwind class**: `maroon-700` (custom color defined in base.html)

### Links
- **HCA Lab**: https://voices.uchicago.edu/healthallocate/
- **CLIF Consortium**: https://clif-icu.com/
