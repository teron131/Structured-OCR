import re
from typing import Literal, Optional

import opencc
from pydantic import BaseModel, Field, field_validator, model_validator


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
    level: int = Field(description="The level of the player where MAX is 1000", ge=1, le=1000)
    kills: int = Field(description="The number of kills the player has", ge=0, le=35)
    deaths: int = Field(description="The number of deaths the player has", ge=0, le=35)
    assists: int = Field(description="The number of assists the player has", ge=0, le=35)
    kd: float = Field(description="The K/D ratio of the player as shown", ge=0.00, le=35.00)
    score: int = Field(description="The score of the player", ge=0, le=100000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:

        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Name must contain only English letters, numbers, '_', and '-' without spaces")
        return v


class Match(BaseModel):
    side: Literal["Heroes", "Villains"] = Field(description="The side of the match as shown on top")
    me: Player = Field(description="The player who is in yellow highlight as in squad, or white as solo")
    squad: list[Player] = Field(description="The players who are in green highlight")
    teammates: list[Player] = Field(description="The players who are in the same side as the me")
    enemies: list[Player] = Field(description="The players who are in the opposite side")

    @field_validator("enemies")
    @classmethod
    def validate_enemies_count(cls, v: list[Player]) -> list[Player]:
        if len(v) > 4:
            raise ValueError("Number of enemies cannot exceed 4")
        return v

    @field_validator("squad")
    @classmethod
    def validate_squad_count(cls, v: list[Player]) -> list[Player]:
        if len(v) > 3:
            raise ValueError("Squad size cannot exceed 3 players (excluding me)")
        return v

    @field_validator("teammates")
    @classmethod
    def validate_teammates_count(cls, v: list[Player]) -> list[Player]:
        if len(v) > 4:
            raise ValueError("Number of teammates cannot exceed 4 (including squad)")
        return v

    @model_validator(mode="after")
    def validate_team_composition(self) -> "Match":
        # Ensure enemies list is not empty (there should always be opponents)
        if not self.enemies:
            raise ValueError("Enemies list cannot be empty")

        # Teammates list should not be empty (player should have team members)
        if not self.teammates:
            raise ValueError("Teammates list cannot be empty")

        # Squad can be empty (solo player scenario)
        # Squad and teammates are separate groups - squad members should not overlap with teammates
        if self.squad and self.teammates:
            squad_names = {player.name for player in self.squad}
            teammate_names = {player.name for player in self.teammates}
            if squad_names.intersection(teammate_names):
                raise ValueError("Squad members and teammates should be separate groups with no overlap")

        if len(self.teammates) + len(self.squad) > 3:
            raise ValueError("Total teammates and squad size cannot exceed 3 players")

        # Ensure me is not in any of the lists
        me_name = self.me.name
        if any(player.name == me_name for player in self.teammates):
            raise ValueError("Player 'me' should not be in teammates list")
        if any(player.name == me_name for player in self.squad):
            raise ValueError("Player 'me' should not be in squad list")
        if any(player.name == me_name for player in self.enemies):
            raise ValueError("Player 'me' should not be in enemies list")

        return self


class Criteria(BaseModel):
    """Criteria for LLM checker."""

    team_names: int = Field(description="Verify team names 'Heroes' and 'Villains' are correctly identified", ge=0, le=10)
    highlighted_player: int = Field(description="Confirm the 'me' player is correctly identified", ge=0, le=10)
    player_data_accuracy: int = Field(description="Check each player's name, level, kills, assists, deaths, K/D ratio, and score are accurately extracted", ge=0, le=10)
    grouping: int = Field(description="Ensure teammates and enemies are correctly grouped relative to 'me'", ge=0, le=10)

    reasons: Optional[str] = Field(description="Provide detailed reasons for any criteria not met, with specific examples of errors or omissions")


# Mapping to whitelisting mutables for LLM checker
CRITERIA_TO_RELATED_FIELDS: dict[str, list[str]] = {
    "team_names": ["side"],
    "highlighted_player": ["me"],
    "player_data_accuracy": ["me", "teammates", "enemies"],
    "grouping": ["me", "teammates", "enemies"],
}

# For dynamic usage
TARGET_SCHEMA = Match
