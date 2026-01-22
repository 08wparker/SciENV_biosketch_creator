#!/usr/bin/env python3
"""Command-line interface for SciENcv Biosketch Creator.

Usage:
    python cli.py parse biosketch.docx          # Parse and show biosketch data
    python cli.py parse biosketch.docx -o out.json  # Parse and save to JSON
    python cli.py automate biosketch.docx       # Parse and automate SciENcv entry
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import directly from modules to avoid Flask dependency
from app.parser.biosketch_parser import BiosketchParser
from app.parser.models import BiosketchData


def parse_biosketch(filepath: str, output: str = None, verbose: bool = False):
    """Parse a biosketch document and optionally save to JSON."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    if not path.suffix.lower() == '.docx':
        print(f"Error: File must be a .docx document")
        sys.exit(1)

    print(f"Parsing: {filepath}")
    parser = BiosketchParser(path)
    data = parser.parse()

    # Display summary
    print(f"\n{'=' * 50}")
    print(f"Name: {data.name}")
    print(f"eRA Commons: {data.era_commons_username}")
    print(f"Position: {data.position_title}")
    print(f"{'=' * 50}")
    print(f"Education entries: {len(data.education)}")
    print(f"Positions: {len(data.positions)}")
    print(f"Honors: {len(data.honors)}")
    print(f"Contributions: {len(data.contributions)}")

    if data.personal_statement:
        print(f"Personal statement citations: {len(data.personal_statement.citations)}")

    if verbose:
        print(f"\n{'=' * 50}")
        print("EDUCATION:")
        for edu in data.education:
            print(f"  - {edu.degree}, {edu.institution} ({edu.completion_date})")

        print(f"\nPOSITIONS:")
        for pos in data.positions:
            print(f"  - {pos.dates}: {pos.title}")

    # Save to file if requested
    if output:
        output_path = Path(output)
        with open(output_path, 'w') as f:
            f.write(data.to_json(indent=2))
        print(f"\nSaved to: {output_path}")
    else:
        print(f"\nUse -o/--output to save to JSON file")

    return data


def automate_sciencv(filepath: str, headless: bool = False):
    """Parse biosketch and automate SciENcv entry creation."""
    # Lazy import to avoid playwright dependency for parse command
    from app.automation.sciencv_filler import SciENcvFiller

    # First parse the document
    data = parse_biosketch(filepath)

    print(f"\n{'=' * 50}")
    print("Starting SciENcv Automation")
    print("=" * 50)
    print("\nA browser window will open.")
    print("Please log in to SciENcv when prompted.")
    print("The automation will fill in your biosketch after login.\n")

    def status_callback(msg):
        print(f"[Automation] {msg}")

    async def run():
        filler = SciENcvFiller(
            data=data,
            headless=headless,
            on_status_update=status_callback
        )
        success = await filler.start()
        return success

    success = asyncio.run(run())

    if success:
        print("\nAutomation completed successfully!")
        print("Please review the entries in your browser.")
    else:
        print("\nAutomation encountered errors.")
        print("Please check the browser and complete manually if needed.")


def main():
    parser = argparse.ArgumentParser(
        description='SciENcv Biosketch Creator CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse a biosketch document')
    parse_parser.add_argument('filepath', help='Path to .docx biosketch file')
    parse_parser.add_argument('-o', '--output', help='Output JSON file path')
    parse_parser.add_argument('-v', '--verbose', action='store_true',
                              help='Show detailed output')

    # Automate command
    auto_parser = subparsers.add_parser('automate', help='Parse and automate SciENcv')
    auto_parser.add_argument('filepath', help='Path to .docx biosketch file')
    auto_parser.add_argument('--headless', action='store_true',
                             help='Run browser in headless mode (not recommended)')

    args = parser.parse_args()

    if args.command == 'parse':
        parse_biosketch(args.filepath, args.output, args.verbose)
    elif args.command == 'automate':
        automate_sciencv(args.filepath, args.headless)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
