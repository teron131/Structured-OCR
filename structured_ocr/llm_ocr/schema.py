from datetime import date
from typing import Generator, Literal, Optional

import opencc
from pydantic import BaseModel, Field, field_validator


def s2hk(v: Optional[str]) -> Optional[str]:
    """Convert text to traditional Chinese (Hong Kong standard) if not None.

    Args:
        v (Optional[str]): Text to convert.

    Returns:
        Optional[str]: Converted text or None.
    """
    if v is not None:
        converter = opencc.OpenCC("s2hk")
        return converter.convert(v)
    return v


class Player(BaseModel):
    name: str = Field(description="The name of the player")
    level: int = Field(description="The level of the player where MAX is 1000")
    kills: int = Field(description="The number of kills the player has")
    deaths: int = Field(description="The number of deaths the player has")
    assists: int = Field(description="The number of assists the player has")
    kd: float = Field(description="The K/D ratio of the player as shown")
    score: int = Field(description="The score of the player")


class Match(BaseModel):
    side: Literal["Heroes", "Villains"] = Field(description="The side of the match as shown on top")
    me: Player = Field(description="The player who is in yellow highlight as in squad, or white as solo")
    squad: list[Player] = Field(description="The players who are in green highlight")
    teammates: list[Player] = Field(description="The players who are in the same side as the me")
    enemies: list[Player] = Field(description="The players who are in the opposite side")


class Criteria(BaseModel):
    """Criteria for LLM checker."""

    team_names: int = Field(description="Verify team names 'Heroes' and 'Villains' are correctly identified", ge=0, le=10)
    highlighted_player: int = Field(description="Confirm the 'me' player is correctly identified", ge=0, le=10)
    player_data_accuracy: int = Field(description="Check each player's name, level, kills, assists, deaths, K/D ratio, and score are accurately extracted", ge=0, le=10)
    grouping: int = Field(description="Ensure teammates and enemies are correctly grouped relative to 'me'", ge=0, le=10)

    reasons: str = Field(description="Provide detailed reasons for any criteria not met, with specific examples of errors or omissions")


# Mapping to whitelisting mutables for LLM checker
CRITERIA_TO_RELATED_FIELDS: dict[str, list[str]] = {
    "team_names": ["side"],
    "highlighted_player": ["me"],
    "player_data_accuracy": ["me", "teammates", "enemies"],
    "grouping": ["me", "teammates", "enemies"],
}

# For dynamic usage
TARGET_SCHEMA = Match
