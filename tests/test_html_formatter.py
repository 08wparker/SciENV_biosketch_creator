"""Tests for HTMLFormatter class."""

import pytest
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.automation.sciencv_filler import HTMLFormatter


class TestContributionHeader:
    """Tests for contribution header formatting."""

    def test_formats_contribution_header(self):
        text = "Contribution 1: Bayesian approaches to clinical trial design. My work has focused on..."
        result = HTMLFormatter.format_contribution_header(text)
        assert result == "<b>Contribution 1: Bayesian approaches to clinical trial design.</b><br>My work has focused on..."

    def test_handles_contribution_without_number(self):
        text = "My work has focused on developing adaptive trial methods."
        result = HTMLFormatter.format_contribution_header(text)
        assert result == text  # No change

    def test_case_insensitive(self):
        text = "CONTRIBUTION 2: Machine learning. This contribution..."
        result = HTMLFormatter.format_contribution_header(text)
        assert "<b>CONTRIBUTION 2: Machine learning.</b>" in result


class TestSectionHeaders:
    """Tests for section header formatting."""

    def test_formats_overview_header(self):
        text = "Overview: I am a clinical trialist with training in biostatistics."
        result = HTMLFormatter.format_section_headers(text)
        assert result == "<b>Overview:</b> I am a clinical trialist with training in biostatistics."

    def test_formats_multiple_headers(self):
        text = "Overview: First section. Expertise: Second section. Commitment: Third section."
        result = HTMLFormatter.format_section_headers(text)
        assert "<b>Overview:</b>" in result
        assert "<b>Expertise:</b>" in result
        assert "<b>Commitment:</b>" in result

    def test_preserves_case(self):
        text = "OVERVIEW: uppercase header"
        result = HTMLFormatter.format_section_headers(text)
        assert "<b>OVERVIEW:</b>" in result


class TestScientificNotation:
    """Tests for scientific notation formatting."""

    def test_formats_exponent(self):
        text = "We observed viral titers of 10^8 copies/mL."
        result = HTMLFormatter.format_scientific_notation(text)
        assert "10<sup>8</sup>" in result

    def test_formats_r_squared(self):
        text = "Analysis showed R2 = 0.91, p < 0.001."
        result = HTMLFormatter.format_scientific_notation(text)
        assert "R<sup>2</sup>" in result

    def test_formats_r_squared_with_caret(self):
        text = "The R^2 value was significant."
        result = HTMLFormatter.format_scientific_notation(text)
        assert "R<sup>2</sup>" in result

    def test_formats_negative_exponent(self):
        text = "p < 10^-5"
        result = HTMLFormatter.format_scientific_notation(text)
        assert "10<sup>-5</sup>" in result

    def test_formats_co2(self):
        text = "CO2 levels were measured."
        result = HTMLFormatter.format_scientific_notation(text)
        assert "CO<sub>2</sub>" in result

    def test_formats_h2o(self):
        text = "H2O content was analyzed."
        result = HTMLFormatter.format_scientific_notation(text)
        assert "H<sub>2</sub>O" in result


class TestGeneNames:
    """Tests for gene name formatting."""

    def test_italicizes_ace2(self):
        text = "The ACE2 receptor expression was elevated."
        result = HTMLFormatter.format_gene_names(text)
        assert "<i>ACE2</i>" in result

    def test_italicizes_brca1(self):
        text = "BRCA1 mutations are associated with cancer risk."
        result = HTMLFormatter.format_gene_names(text)
        assert "<i>BRCA1</i>" in result

    def test_does_not_match_partial(self):
        text = "The SPACE2 gene is not ACE2."
        result = HTMLFormatter.format_gene_names(text)
        assert "SPACE2" in result  # SPACE2 should not be changed
        assert "<i>ACE2</i>" in result


class TestParagraphBreaks:
    """Tests for paragraph break formatting."""

    def test_converts_double_newlines(self):
        text = "First paragraph.\n\nSecond paragraph."
        result = HTMLFormatter.format_paragraph_breaks(text)
        assert result == "First paragraph.<br><br>Second paragraph."

    def test_converts_single_newlines(self):
        text = "Line one.\nLine two."
        result = HTMLFormatter.format_paragraph_breaks(text)
        assert result == "Line one.<br>Line two."

    def test_handles_mixed_newlines(self):
        text = "Para one.\n\nPara two.\nLine in para two."
        result = HTMLFormatter.format_paragraph_breaks(text)
        assert result == "Para one.<br><br>Para two.<br>Line in para two."


class TestFormatForSciencv:
    """Tests for the main format_for_sciencv method."""

    def test_formats_contribution(self):
        text = "Contribution 1: Bayesian trial design. We observed R2 = 0.91 with ACE2 expression."
        result = HTMLFormatter.format_for_sciencv(text, is_contribution=True)
        assert "<b>Contribution 1: Bayesian trial design.</b><br>" in result
        assert "R<sup>2</sup>" in result
        assert "<i>ACE2</i>" in result

    def test_formats_personal_statement(self):
        text = "Overview: I am a researcher.\n\nExpertise: My work involves ACE2 studies with R2 > 0.9."
        result = HTMLFormatter.format_for_sciencv(text, is_contribution=False)
        assert "<b>Overview:</b>" in result
        assert "<b>Expertise:</b>" in result
        assert "<br><br>" in result
        assert "<i>ACE2</i>" in result
        assert "R<sup>2</sup>" in result

    def test_handles_empty_text(self):
        result = HTMLFormatter.format_for_sciencv("", is_contribution=True)
        assert result == ""

    def test_handles_none(self):
        result = HTMLFormatter.format_for_sciencv(None, is_contribution=True)
        assert result is None
