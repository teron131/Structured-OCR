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


class TextContent(BaseModel):
    content: str = Field(description="The content of the text")
    # ...


class Criteria(BaseModel):
    """Criteria for the results."""

    # Page Metadata criteria
    all_text_included: int = Field(description="Verify all text from the newspaper page is completely extracted without missing any paragraphs or sections", ge=0, le=10)
    text_headers: int = Field(description="Check that all titles or headers are properly identified and formatted with double asterisks (e.g., **Title**)", ge=0, le=10)
    all_text_correct: int = Field(description="Verify all text from the newspaper page is completely extracted without missing any paragraphs or sections", ge=0, le=10)

    # Overall Assessment
    reasons: str = Field(description="Provide detailed reasons for any criteria not met, with specific examples of errors or omissions")


CRITERIA_TO_RELATED_FIELDS: dict[str, list[str]] = {
    "all_text_included": ["content"],
    "text_headers": ["content"],
    "all_text_correct": ["content"],
}
