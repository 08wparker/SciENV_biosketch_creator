#!/usr/bin/env python3
"""CLI script to run SciENcv automation with biosketch data.

Usage:
    python run_automation.py                    # Use sample data
    python run_automation.py biosketch.json    # Use JSON file

Prerequisites:
    pip install -r requirements-automation.txt
    playwright install chromium
"""

import asyncio
import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.automation.sciencv_filler import run_automation


# Sample biosketch data for testing
SAMPLE_DATA = {
    "name": "William Parker",
    "era_commons_username": "WILLIAMFPARKER",
    "position_title": "Assistant Professor of Medicine and Public Health Sciences, University of Chicago",
    "education": [
        {
            "institution": "Williams College",
            "degree": "Bachelor of Arts (BA)",
            "start_date": "09/2004",
            "completion_date": "06/2008",
            "field_of_study": "Physics",
            "location": "Williamstown, MA"
        },
        {
            "institution": "University of Chicago",
            "degree": "Doctor of Medicine (MD)",
            "start_date": "09/2008",
            "completion_date": "06/2012",
            "field_of_study": "Medicine",
            "location": "Chicago, IL"
        },
        {
            "institution": "University of Chicago",
            "degree": "PhD",
            "start_date": "09/2016",
            "completion_date": "06/2021",
            "field_of_study": "Public Health Sciences",
            "location": "Chicago, IL"
        },
        {
            "institution": "University of Chicago",
            "degree": "Resident",
            "start_date": "07/2012",
            "completion_date": "06/2015",
            "field_of_study": "Internal Medicine",
            "location": "Chicago, IL"
        },
        {
            "institution": "University of Chicago",
            "degree": "Fellow",
            "start_date": "07/2015",
            "completion_date": "06/2018",
            "field_of_study": "Pulmonary and Critical Care Medicine",
            "location": "Chicago, IL"
        },
        {
            "institution": "University of Chicago",
            "degree": "Fellow",
            "start_date": "07/2013",
            "completion_date": "06/2015",
            "field_of_study": "Clinical Medical Ethics (MacLean Center)",
            "location": "Chicago, IL"
        }
    ],
    "positions": [
        {
            "title": "Associate Professor of Medicine and Public Health Sciences",
            "institution": "University of Chicago",
            "location": "Chicago, IL",
            "dates": "2021-Present",
            "primary": True
        },
        {
            "title": "Co-Chair, Analytic Methods Subcommittee",
            "institution": "Scientific Registry of Transplant Recipients",
            "location": "Minneapolis, MN",
            "dates": "2024-Present"
        },
        {
            "title": "Executive Director, CLIF Consortium",
            "institution": "University of Chicago",
            "location": "Chicago, IL",
            "dates": "2024-Present"
        },
        {
            "title": "Instructor of Medicine",
            "institution": "University of Chicago",
            "location": "Chicago, IL",
            "dates": "2018-2021"
        }
    ],
    "honors": [
        {
            "year": "2024",
            "description": "John D. Arnold, MD Scientific Research Prize for outstanding medical student mentorship (student mentee Lazenby)",
            "organization": "Pritzker School of Medicine, University of Chicago"
        },
        {
            "year": "2023",
            "description": "John D. Arnold, MD Scientific Research Prize for outstanding medical student mentorship (student mentee Chung)",
            "organization": "Pritzker School of Medicine, University of Chicago"
        },
        {
            "year": "2021",
            "description": "Best Dissertation, Department of Public Health Sciences",
            "organization": "University of Chicago"
        },
        {
            "year": "2020",
            "description": "Young Physician-Scientist Award",
            "organization": "American Society for Clinical Investigation"
        },
        {
            "year": "2018",
            "description": "Ziskind Clinical Research Scholar Award",
            "organization": "American Thoracic Society"
        }
    ],
    "personal_statement": {
        "text": "I am a pulmonary and critical care physician, medical ethicist, and health services researcher who studies the allocation of scarce medical resources. My focus is absolute scarcity problems, where demand greatly exceeds supply, forcing healthcare systems to triage life-saving treatments using algorithmic policies. I use my comprehensive empirical and ethical training to evaluate allocation systems for a variety of these problems. My HealthCare Allocation lab's (HCA Lab) work on heart, kidney, life support, and vaccine allocation has led to high-impact publications in JAMA, JACC, AJRCCM, and the American Journal of Transplantation. I have received national recognition through young investigator awards from the American Society for Clinical Investigation and the American Thoracic Society. My original science and normative writing have been featured in USA Today, The Washington Post, and The New York Times. My work has been repeatedly cited by national and state policymakers tasked with creating systems for allocating scarce medical resources, and I am currently co-chair of the Scientific Registry of Transplant Recipients Analytic Methods Subcommittee. I am the founding executive director of the Common Longitudinal ICU data Format (CLIF) consortium, a growing network of ICU data science labs that develop and utilize the open-source CLIF data standard to perform privacy-preserving federated ICU data science.",
        "grants": [
            {
                "funder": "NIH",
                "number": "K08 HL150291",
                "pi": "Parker",
                "role": "PI",
                "dates": "02/01/2020 - 01/31/2025",
                "title": "Mending a Broken Heart Allocation System with Machine Learning"
            },
            {
                "funder": "NIH",
                "number": "R01 LM014263",
                "pi": "Parker",
                "role": "PI",
                "dates": "4/1/2023 - 1/31/2028",
                "title": "Improving the efficiency and equity of critical care allocation during a crisis with place-based disadvantage indices"
            }
        ]
    },
    "contributions": [
        {
            "narrative": "I have developed novel machine learning approaches to improve heart allocation. My work demonstrated significant geographic variation in heart transplant outcomes and identified opportunities to optimize allocation policies. These findings have directly informed policy discussions at UNOS and SRTR.",
            "citations": [
                {"pmid": "29666020", "text": "Geographic Variation in Heart Transplant Outcomes..."},
                {"pmid": "31714985", "text": "Association of Transplant Center Volume..."}
            ]
        },
        {
            "narrative": "I led the development of the CLIF consortium, which has grown to include over 20 academic medical centers. CLIF provides a common data standard for ICU research, enabling federated analyses while preserving patient privacy.",
            "citations": [
                {"pmid": "40080116", "text": "The CLIF Consortium: Standardizing ICU Data..."}
            ]
        }
    ],
    "products": {
        "related": [
            {"pmid": "29666020"},
            {"pmid": "31714985"},
            {"pmid": "32527399"},
            {"pmid": "38349372"},
            {"pmid": "40080116"}
        ],
        "other": [
            {"pmid": "29246896"},
            {"pmid": "33864733"},
            {"pmid": "34951528"},
            {"pmid": "26760565"},
            {"pmid": "39804637"}
        ]
    }
}


def main():
    """Run the automation."""
    print("=" * 60)
    print("SciENcv Biosketch Automation")
    print("=" * 60)

    # Load data from file or use sample
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
        if not json_path.exists():
            print(f"Error: File not found: {json_path}")
            sys.exit(1)

        print(f"Loading data from: {json_path}")
        with open(json_path) as f:
            data = json.load(f)
    else:
        print("Using sample data (pass JSON file as argument for custom data)")
        data = SAMPLE_DATA

    print(f"\nBiosketch for: {data.get('name', 'Unknown')}")
    print(f"Education entries: {len(data.get('education', []))}")
    print(f"Position entries: {len(data.get('positions', []))}")
    print(f"Honor entries: {len(data.get('honors', []))}")
    print(f"Contribution entries: {len(data.get('contributions', []))}")
    print()

    # Run automation
    def status_callback(msg):
        print(msg)

    print("Starting automation...")
    print("A browser window will open. Please log in to SciENcv when prompted.")
    print()

    success = asyncio.run(run_automation(data, headless=False, on_status=status_callback))

    if success:
        print("\n" + "=" * 60)
        print("Automation completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Automation failed. Check the browser for errors.")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
