"""Data models for NIH Biosketch parsing."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
import json


@dataclass
class Citation:
    """Represents a single citation/publication."""
    text: str
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'pmid': self.pmid,
            'pmcid': self.pmcid,
            'doi': self.doi
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Citation':
        return cls(**data)


@dataclass
class Education:
    """Represents an education/training entry."""
    institution: str
    degree: str
    completion_date: str
    field_of_study: str

    def to_dict(self) -> dict:
        return {
            'institution': self.institution,
            'degree': self.degree,
            'completion_date': self.completion_date,
            'field_of_study': self.field_of_study
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Education':
        return cls(**data)


@dataclass
class Position:
    """Represents a position entry."""
    dates: str
    title: str
    institution: str

    def to_dict(self) -> dict:
        return {
            'dates': self.dates,
            'title': self.title,
            'institution': self.institution
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Position':
        return cls(**data)


@dataclass
class Honor:
    """Represents an honor/award entry."""
    year: str
    description: str

    def to_dict(self) -> dict:
        return {
            'year': self.year,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Honor':
        return cls(**data)


@dataclass
class Grant:
    """Represents a research grant/support entry."""
    funder: str = ""
    number: str = ""
    pi: str = ""
    dates: str = ""
    title: str = ""
    role: str = ""  # e.g., "PI", "Co-investigator", etc.

    def to_dict(self) -> dict:
        return {
            'funder': self.funder,
            'number': self.number,
            'pi': self.pi,
            'dates': self.dates,
            'title': self.title,
            'role': self.role
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Grant':
        return cls(**data)


@dataclass
class PersonalStatement:
    """Represents Section A - Personal Statement."""
    text: str
    grants: list[Grant] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'grants': [g.to_dict() for g in self.grants],
            'citations': [c.to_dict() for c in self.citations]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PersonalStatement':
        citations = [Citation.from_dict(c) for c in data.get('citations', [])]
        grants = [Grant.from_dict(g) for g in data.get('grants', [])]
        return cls(
            text=data['text'],
            grants=grants,
            citations=citations
        )


@dataclass
class Contribution:
    """Represents a single Contribution to Science entry."""
    narrative: str
    citations: list[Citation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'narrative': self.narrative,
            'citations': [c.to_dict() for c in self.citations]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Contribution':
        citations = [Citation.from_dict(c) for c in data.get('citations', [])]
        return cls(narrative=data['narrative'], citations=citations)


@dataclass
class BiosketchData:
    """Complete parsed biosketch data."""
    name: str = ""
    era_commons_username: str = ""
    position_title: str = ""
    education: list[Education] = field(default_factory=list)
    personal_statement: Optional[PersonalStatement] = None
    positions: list[Position] = field(default_factory=list)
    honors: list[Honor] = field(default_factory=list)
    contributions: list[Contribution] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'era_commons_username': self.era_commons_username,
            'position_title': self.position_title,
            'education': [e.to_dict() for e in self.education],
            'personal_statement': self.personal_statement.to_dict() if self.personal_statement else None,
            'positions': [p.to_dict() for p in self.positions],
            'honors': [h.to_dict() for h in self.honors],
            'contributions': [c.to_dict() for c in self.contributions]
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> 'BiosketchData':
        personal_statement = None
        if data.get('personal_statement'):
            personal_statement = PersonalStatement.from_dict(data['personal_statement'])

        return cls(
            name=data.get('name', ''),
            era_commons_username=data.get('era_commons_username', ''),
            position_title=data.get('position_title', ''),
            education=[Education.from_dict(e) for e in data.get('education', [])],
            personal_statement=personal_statement,
            positions=[Position.from_dict(p) for p in data.get('positions', [])],
            honors=[Honor.from_dict(h) for h in data.get('honors', [])],
            contributions=[Contribution.from_dict(c) for c in data.get('contributions', [])]
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'BiosketchData':
        return cls.from_dict(json.loads(json_str))
