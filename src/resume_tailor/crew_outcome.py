"""Return type for kickoff_crew when score targets and refinement rounds apply."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CrewRunOutcome:
    """Result of one or more full crew kickoffs until score targets or max rounds."""

    result: Any
    rounds_run: int
    score_targets_met: bool
