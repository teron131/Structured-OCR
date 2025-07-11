import os
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

load_dotenv()


class Configuration(BaseModel):
    use_ocr: bool = Field(default=False, description="Whether to use Google Document AI OCR")
    llm_ocr: str = Field(default=os.getenv("LLM_OCR"), description="The LLM model to use for OCR")
    llm_checker: str = Field(default=os.getenv("LLM_CHECKER"), description="The LLM model to use for checking the criteria")
    max_correction: int = Field(default=3, description="The maximum number of corrections to attempt")
    criteria_met_perc: int = Field(default=80, description="The percentage of criteria that must be met to consider the result valid")
    criterion_score_threshold: int = Field(default=7, description="The score threshold for a criterion to be considered valid")

    class Config:
        env_prefix = ""
        case_sensitive = False

    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        if not config or "configurable" not in config:
            return cls()

        configurable = config["configurable"]

        # Get field names and their defaults from the model
        field_names = cls.model_fields.keys()

        # Build values dict from environment variables and configurable
        values: dict[str, Any] = {}
        for field_name in field_names:
            env_value = os.environ.get(field_name.upper())
            config_value = configurable.get(field_name)

            if env_value is not None:
                values[field_name] = env_value
            elif config_value is not None:
                values[field_name] = config_value
            # If neither env nor config value exists, the field's default will be used

        return cls(**values)
