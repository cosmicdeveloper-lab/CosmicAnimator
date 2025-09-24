# src/cosmicanimator/application/narration/contracts.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WordTiming:
    word: str
    start: float
    end: float


@dataclass
class NarrationResult:
    """
    Output of the 'sync' layer (Orchestra). No rendering decisions here.
    """
    text: str
    start_time: float       # scene time when speech starts
    duration: float         # total TTS duration in seconds
    word_timings: Optional[List[WordTiming]] = None  # optional fine alignment
