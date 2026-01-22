"""Tests for biosketch parser."""

import os
import pytest

from app.parser.models import (
    BiosketchData,
    Education,
    Position,
    Honor,
    Citation,
    Contribution,
    PersonalStatement,
)
from app.parser.biosketch_parser import BiosketchParser
from app.parser.citation_parser import CitationParser


class TestCitationParser:
    """Tests for CitationParser class."""

    def test_extract_pmid(self):
        """Test PMID extraction from citation text."""
        text = "Parker WF et al. Some title. Journal. 2020. PMID: 12345678"
        pmid = CitationParser.extract_pmid(text)
        assert pmid == "12345678"

    def test_extract_pmid_no_match(self):
        """Test PMID extraction when no PMID present."""
        text = "Parker WF et al. Some title. Journal. 2020."
        pmid = CitationParser.extract_pmid(text)
        assert pmid is None

    def test_extract_pmcid(self):
        """Test PMCID extraction from citation text."""
        text = "Some citation text PMCID: PMC7654321"
        pmcid = CitationParser.extract_pmcid(text)
        assert pmcid == "PMC7654321"

    def test_extract_doi(self):
        """Test DOI extraction from citation text."""
        text = "Some citation doi: 10.1001/jama.2020.12345"
        doi = CitationParser.extract_doi(text)
        assert doi == "10.1001/jama.2020.12345"

    def test_parse_citation(self):
        """Test full citation parsing."""
        text = "Parker WF et al. Title. JAMA. 2020. PMID: 12345678; PMCID: PMC7654321"
        citation = CitationParser.parse_citation(text)

        assert citation.text == text
        assert citation.pmid == "12345678"
        assert citation.pmcid == "PMC7654321"

    def test_is_citation_line_with_pmid(self):
        """Test citation detection with PMID."""
        text = "Parker WF et al. Title. JAMA. 2020. PMID: 12345678"
        assert CitationParser.is_citation_line(text) is True

    def test_is_citation_line_empty(self):
        """Test citation detection with empty string."""
        assert CitationParser.is_citation_line("") is False
        assert CitationParser.is_citation_line("   ") is False


class TestModels:
    """Tests for data model classes."""

    def test_citation_to_dict(self):
        """Test Citation serialization."""
        citation = Citation(
            text="Test citation",
            pmid="12345",
            pmcid="PMC67890",
            doi="10.1234/test"
        )
        d = citation.to_dict()
        assert d['text'] == "Test citation"
        assert d['pmid'] == "12345"
        assert d['pmcid'] == "PMC67890"
        assert d['doi'] == "10.1234/test"

    def test_citation_from_dict(self):
        """Test Citation deserialization."""
        d = {'text': 'Test', 'pmid': '123', 'pmcid': None, 'doi': None}
        citation = Citation.from_dict(d)
        assert citation.text == 'Test'
        assert citation.pmid == '123'

    def test_education_to_dict(self):
        """Test Education serialization."""
        edu = Education(
            institution="Test University",
            degree="Ph.D.",
            completion_date="06/2020",
            field_of_study="Computer Science"
        )
        d = edu.to_dict()
        assert d['institution'] == "Test University"
        assert d['degree'] == "Ph.D."

    def test_biosketch_data_to_json(self):
        """Test BiosketchData JSON serialization."""
        data = BiosketchData(
            name="John Doe",
            era_commons_username="JOHNDOE",
            position_title="Professor"
        )
        json_str = data.to_json()
        assert '"name": "John Doe"' in json_str
        assert '"era_commons_username": "JOHNDOE"' in json_str

    def test_biosketch_data_from_dict(self):
        """Test BiosketchData deserialization."""
        d = {
            'name': 'Jane Doe',
            'era_commons_username': 'JANEDOE',
            'position_title': 'Researcher',
            'education': [
                {
                    'institution': 'MIT',
                    'degree': 'B.S.',
                    'completion_date': '06/2010',
                    'field_of_study': 'Biology'
                }
            ],
            'personal_statement': None,
            'positions': [],
            'honors': [],
            'contributions': []
        }
        data = BiosketchData.from_dict(d)
        assert data.name == 'Jane Doe'
        assert len(data.education) == 1
        assert data.education[0].institution == 'MIT'


class TestBiosketchParser:
    """Tests for BiosketchParser class."""

    @pytest.fixture
    def sample_biosketch_path(self):
        """Path to sample biosketch for testing."""
        # Use the example biosketch in the project
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'biosketch_example',
            'Parker_Biosketch_MASTER.docx'
        )
        if os.path.exists(path):
            return path
        pytest.skip("Sample biosketch not found")

    def test_parse_header(self, sample_biosketch_path):
        """Test header parsing."""
        parser = BiosketchParser(sample_biosketch_path)
        data = parser.parse()

        assert data.name == "William F Parker"
        assert data.era_commons_username == "WILLIAMFPARKER"
        assert "Professor" in data.position_title or "Medicine" in data.position_title

    def test_parse_education(self, sample_biosketch_path):
        """Test education table parsing."""
        parser = BiosketchParser(sample_biosketch_path)
        data = parser.parse()

        assert len(data.education) > 0
        # Check first education entry
        first_edu = data.education[0]
        assert first_edu.institution
        assert first_edu.degree
        assert first_edu.completion_date

    def test_parse_positions(self, sample_biosketch_path):
        """Test positions parsing."""
        parser = BiosketchParser(sample_biosketch_path)
        data = parser.parse()

        assert len(data.positions) > 0
        for pos in data.positions:
            assert pos.dates
            assert pos.title

    def test_parse_honors(self, sample_biosketch_path):
        """Test honors parsing."""
        parser = BiosketchParser(sample_biosketch_path)
        data = parser.parse()

        assert len(data.honors) > 0
        for honor in data.honors:
            assert honor.year
            assert honor.description

    def test_parse_contributions(self, sample_biosketch_path):
        """Test contributions parsing."""
        parser = BiosketchParser(sample_biosketch_path)
        data = parser.parse()

        assert len(data.contributions) > 0

    def test_parse_personal_statement(self, sample_biosketch_path):
        """Test personal statement parsing."""
        parser = BiosketchParser(sample_biosketch_path)
        data = parser.parse()

        assert data.personal_statement is not None
        assert data.personal_statement.text

    def test_full_parse(self, sample_biosketch_path):
        """Test complete parsing and serialization."""
        parser = BiosketchParser(sample_biosketch_path)
        data = parser.parse()

        # Convert to dict and back
        d = data.to_dict()
        restored = BiosketchData.from_dict(d)

        assert restored.name == data.name
        assert len(restored.education) == len(data.education)
        assert len(restored.positions) == len(data.positions)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
