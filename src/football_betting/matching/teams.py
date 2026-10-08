"""Reusable conservative team/fixture identity matching.

Promoted from the legacy team_map_index.py / match_live_fixtures.py lessons.
Identity matching never uses odds or price movement.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_DROP = re.compile(
    r"\b(fc|afc|sc|sk|cf|sv|bv|vfb|vfl|tsg|ss|us|as|ssc|ac|rc|cd|ud|ad|"
    r"real|club|deportivo|atletico|athletic|united|utd|city|town|rovers|"
    r"wanderers|albion|county)\b",
    re.I,
)


def normalize_english_name(value: str | None) -> str:
    """Normalize English/Latin team names without fuzzy guessing."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = _DROP.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


class TeamNameMap:
    """Chinese Sporttery name -> unique legacy English identity."""

    def __init__(self, mapping_path: str | Path) -> None:
        raw = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
        rev: dict[str, set[str]] = {}
        for league, teams in raw.items():
            if league == "_meta" or not isinstance(teams, list):
                continue
            for item in teams:
                if not isinstance(item, dict):
                    continue
                english = str(item.get("en") or "").strip()
                if not english:
                    continue
                keys = [item.get("cn"), item.get("cn_full"), *(item.get("aliases") or [])]
                for key in keys:
                    key_text = str(key or "").strip()
                    if key_text:
                        rev.setdefault(key_text, set()).add(english)
        self._rev = rev

    @staticmethod
    def _one(values: set[str]) -> str | None:
        normalized = {normalize_english_name(value) for value in values if value}
        normalized.discard("")
        if len(normalized) != 1:
            return None
        wanted = next(iter(normalized))
        originals = sorted(value for value in values if normalize_english_name(value) == wanted)
        return originals[0] if originals else None

    def english(self, chinese_name: str | None) -> str | None:
        name = str(chinese_name or "").strip()
        if not name or re.search(r"[\[\]]|取消|延期|VS|待定", name):
            return None
        if name in self._rev:
            return self._one(self._rev[name])

        prefix: set[str] = set()
        for key, values in self._rev.items():
            if len(name) >= 2 and key.startswith(name):
                prefix.update(values)
        match = self._one(prefix)
        if match:
            return match

        reverse: set[str] = set()
        for key, values in self._rev.items():
            if len(key) >= 2 and name.startswith(key):
                reverse.update(values)
        return self._one(reverse)


@dataclass(frozen=True, slots=True)
class ReferenceFixture:
    event_id: str
    home: str
    away: str
    kickoff_utc: datetime


@dataclass(frozen=True, slots=True)
class SportteryFixture:
    match_id: str
    home_cn: str
    away_cn: str
    kickoff: datetime


@dataclass(frozen=True, slots=True)
class FixtureMatch:
    event_id: str
    match_id: str
    kickoff_delta_seconds: float


def match_fixture(
    reference: ReferenceFixture,
    sporttery: list[SportteryFixture],
    team_map: TeamNameMap,
    *,
    tolerance_seconds: float = 15 * 60,
) -> FixtureMatch | None:
    """Return one unique identity match or None."""
    ref_home = normalize_english_name(reference.home)
    ref_away = normalize_english_name(reference.away)
    if not ref_home or not ref_away or reference.kickoff_utc.tzinfo is None:
        return None

    candidates: list[FixtureMatch] = []
    for item in sporttery:
        if item.kickoff.tzinfo is None:
            continue
        home_en = team_map.english(item.home_cn)
        away_en = team_map.english(item.away_cn)
        if home_en is None or away_en is None:
            continue
        if normalize_english_name(home_en) != ref_home:
            continue
        if normalize_english_name(away_en) != ref_away:
            continue
        delta = abs(
            (
                item.kickoff.astimezone(reference.kickoff_utc.tzinfo)
                - reference.kickoff_utc
            ).total_seconds()
        )
        if delta <= tolerance_seconds:
            candidates.append(
                FixtureMatch(
                    event_id=reference.event_id,
                    match_id=item.match_id,
                    kickoff_delta_seconds=delta,
                )
            )
    if len(candidates) != 1:
        return None
    return candidates[0]
