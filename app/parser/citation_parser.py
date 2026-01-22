"""Citation parsing utilities for extracting PMIDs and citation data."""

from __future__ import annotations
import re
from typing import Optional, List
from .models import Citation


class CitationParser:
    """Parser for extracting and processing citations."""

    # Patterns for identifying citation markers
    PMID_PATTERN = re.compile(r'PMID:\s*(\d+)', re.IGNORECASE)
    PMCID_PATTERN = re.compile(r'PMCID:\s*(PMC\d+)', re.IGNORECASE)
    DOI_PATTERN = re.compile(r'(?:doi:\s*|https?://doi\.org/)(10\.\d{4,}/[^\s]+)', re.IGNORECASE)

    # Pattern to detect numbered citations (1., 2., a., b., etc.)
    NUMBERED_CITATION_PATTERN = re.compile(r'^(?:\d+\.|[a-z]\.)?\s*(.+)', re.IGNORECASE)

    @classmethod
    def extract_pmid(cls, text: str) -> Optional[str]:
        """Extract PMID from text."""
        match = cls.PMID_PATTERN.search(text)
        return match.group(1) if match else None

    @classmethod
    def extract_pmcid(cls, text: str) -> Optional[str]:
        """Extract PMCID from text."""
        match = cls.PMCID_PATTERN.search(text)
        return match.group(1) if match else None

    @classmethod
    def extract_doi(cls, text: str) -> Optional[str]:
        """Extract DOI from text."""
        match = cls.DOI_PATTERN.search(text)
        return match.group(1) if match else None

    @classmethod
    def parse_citation(cls, text: str) -> Citation:
        """Parse a citation string into a Citation object."""
        text = text.strip()
        return Citation(
            text=text,
            pmid=cls.extract_pmid(text),
            pmcid=cls.extract_pmcid(text),
            doi=cls.extract_doi(text)
        )

    @classmethod
    def is_citation_line(cls, text: str) -> bool:
        """Check if a line appears to be a citation.

        Citations typically:
        - Start with a number and period (1., 2.)
        - Start with a letter and period (a., b.)
        - Contain author names followed by title
        - Contain PMID, PMCID, or DOI
        """
        text = text.strip()
        if not text:
            return False

        # Check for PMID/PMCID/DOI markers
        if cls.PMID_PATTERN.search(text) or cls.PMCID_PATTERN.search(text) or cls.DOI_PATTERN.search(text):
            return True

        # Check for numbered list format with author-like pattern
        numbered_match = re.match(r'^(?:\d+\.|[a-z]\.)\s*', text)
        if numbered_match:
            remainder = text[numbered_match.end():]
            # Check if it looks like author names (e.g., "Smith AB, Jones CD,")
            if re.match(r'^[A-Z][a-z]+\s+[A-Z]{1,2}[\s,]', remainder):
                return True

        return False

    @classmethod
    def split_citations(cls, text: str) -> list[str]:
        """Split a block of text into individual citations.

        Handles various formats:
        - Numbered lists (1., 2., 3.)
        - Lettered lists (a., b., c.)
        - Line-separated citations
        """
        lines = text.strip().split('\n')
        citations = []
        current_citation = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_citation:
                    citations.append(' '.join(current_citation))
                    current_citation = []
                continue

            # Check if this starts a new citation
            if re.match(r'^(?:\d+\.|[a-z]\.)\s+', line):
                if current_citation:
                    citations.append(' '.join(current_citation))
                current_citation = [line]
            else:
                # Continue previous citation
                current_citation.append(line)

        # Don't forget the last citation
        if current_citation:
            citations.append(' '.join(current_citation))

        return citations

    @classmethod
    def parse_citation_block(cls, text: str) -> list[Citation]:
        """Parse a block of text containing multiple citations."""
        citation_texts = cls.split_citations(text)
        return [cls.parse_citation(ct) for ct in citation_texts if ct.strip()]
