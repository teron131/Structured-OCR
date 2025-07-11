import os
from multiprocessing import Pool, cpu_count
from typing import Optional

from dotenv import load_dotenv
from google.cloud import documentai
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.pregel import RetryPolicy
from PIL import Image
from pydantic import BaseModel, Field
from rich import print
from tqdm import tqdm

from ..ocr import run_ocr
from ..utils import image_to_base64, image_to_bytes
from .configuration import Configuration
from .llm import run_llm
from .prompt import CHECKER_PROMPT, TEXT_EXTRACTION_PROMPT
from .schema import CRITERIA_TO_RELATED_FIELDS, TARGET_SCHEMA, Criteria

load_dotenv()


class GraphState(BaseModel):
    model_config = {"arbitrary_types_allowed": True}  # For PIL.Image
    image_path: str
    image: Optional[Image.Image] = Field(default=None, exclude=True)  # Exclude from serialization
    image_bytes: Optional[bytes] = Field(default=None, exclude=True)  # Exclude from serialization
    image_base64: Optional[str] = Field(default=None)
    ocr_text_extraction_result: Optional[documentai.Document] = Field(default=None, exclude=True)  # Exclude from serialization
    llm_text_extraction_result: Optional[TARGET_SCHEMA] = Field(default=None)
    criteria: Optional[Criteria] = Field(default=None)
    correction_attemps: int = Field(default=0)


def format_conversion(state: GraphState, config: RunnableConfig) -> dict[str, bytes | str]:
    """Convert image to bytes and base64."""
    configuration = Configuration.from_runnable_config(config)

    image = Image.open(state.image_path)
    image_bytes = image_to_bytes(image)
    image_base64 = image_to_base64(image)
    print(f"🔄 Format Conversion complete: {state.image_path}")
    return {
        "image": image,
        "image_bytes": image_bytes,
        "image_base64": image_base64,
    }


def ocr_text_extraction(state: GraphState, config: RunnableConfig) -> dict[str, documentai.Document]:
    """Run OCR on the image."""
    configuration = Configuration.from_runnable_config(config)

    ocr_text_extraction_result = run_ocr(state.image_bytes)
    print(f"🔡 OCR complete: {state.image_path}")
    return {"ocr_text_extraction_result": ocr_text_extraction_result}


def llm_text_extraction(state: GraphState, config: RunnableConfig) -> dict[str, TARGET_SCHEMA]:
    """Run LLM for text extraction."""
    configuration = Configuration.from_runnable_config(config)

    llm_text_extraction_result = run_llm(
        model=configuration.llm_ocr,
        prompt=TEXT_EXTRACTION_PROMPT,
        reference_image=state.image,
        reference_text=state.ocr_text_extraction_result.text,
        schema=TARGET_SCHEMA,
    )
    print(f"🧠 LLM Text Extraction complete: {state.image_path}")
    return {"llm_text_extraction_result": llm_text_extraction_result}


def criteria_checker(state: GraphState, config: RunnableConfig) -> dict[str, Criteria]:
    """Check the criteria."""
    configuration = Configuration.from_runnable_config(config)

    print(state.llm_text_extraction_result)
    result_string = state.llm_text_extraction_result.model_dump_json()
    criteria = run_llm(
        model=configuration.llm_checker,
        prompt=CHECKER_PROMPT,
        reference_image=state.image,
        reference_text=result_string,
        schema=Criteria,
    )
    print(criteria)
    print(f"🔍 Criteria Checker {state.correction_attemps} complete: {state.image_path}")
    return {"criteria": criteria}


def corrector(state: GraphState, config: RunnableConfig) -> dict[str, TARGET_SCHEMA | int]:
    """Correct the results based on failing criteria."""
    configuration = Configuration.from_runnable_config(config)

    # Early return if max corrections exceeded
    if state.correction_attemps >= configuration.max_correction:
        return {
            "llm_text_extraction_result": state.llm_text_extraction_result,
            "correction_attemps": state.correction_attemps,
        }

    # Get failing criteria and related fields to correct
    criteria_data = state.criteria.model_dump()
    failing_criteria = {criterion: score for criterion, score in criteria_data.items() if criterion != "reasons" and isinstance(score, int) and score < configuration.criterion_score_threshold}

    if not failing_criteria:
        print(f"📝 Corrector {state.correction_attemps + 1} complete (no corrections needed): {state.image_path}")
        return {
            "llm_text_extraction_result": state.llm_text_extraction_result,
            "correction_attemps": configuration.max_correction + 1,  # Skip future attempts
        }

    # Get unique fields that need correction
    fields_to_correct = []
    for criterion in failing_criteria:
        if criterion in CRITERIA_TO_RELATED_FIELDS:
            fields_to_correct.extend(CRITERIA_TO_RELATED_FIELDS[criterion])
    fields_to_correct = list(dict.fromkeys(fields_to_correct))  # Remove duplicates, preserve order

    # Build correction instructions
    field_descriptions = [
        f"{Criteria.model_fields[criterion].description} was found to be inadequate (score: {score}/{configuration.criterion_score_threshold})"
        for criterion, score in failing_criteria.items()
        if criterion in Criteria.model_fields
    ]

    instructions = "\n".join(field_descriptions)
    if state.criteria.reasons:
        instructions += f"\nReasons for correction: {state.criteria.reasons}"

    result_string = state.llm_text_extraction_result.model_dump_json()

    corrected_result = run_llm(
        model=configuration.llm_ocr,
        prompt=instructions,
        reference_image=state.image,
        reference_text=result_string,
        schema=TARGET_SCHEMA,
    )

    # Update only the specified fields
    updated_result = state.llm_text_extraction_result.model_copy()
    for field in fields_to_correct:
        if hasattr(corrected_result, field):
            setattr(updated_result, field, getattr(corrected_result, field))

    correction_attemps = state.correction_attemps + 1
    print(f"📝 Corrector {correction_attemps} complete: {state.image_path}")

    return {
        "llm_text_extraction_result": updated_result,
        "correction_attemps": correction_attemps,
    }


def should_continue(state: GraphState, config: RunnableConfig) -> str:
    """Check if criteria are met or max corrections exceeded."""
    configuration = Configuration.from_runnable_config(config)

    # Early return if max corrections exceeded
    if state.correction_attemps >= configuration.max_correction:
        return "valid"

    # Calculate percentage of criteria met
    criteria_fields = {k: v for k, v in state.criteria.model_dump().items() if k != "reasons" and isinstance(v, int)}
    valid_count = sum(1 for score in criteria_fields.values() if score >= configuration.criterion_score_threshold)
    percentage_met = (valid_count / len(criteria_fields)) * 100
    is_valid = percentage_met >= configuration.criteria_met_perc

    print(f"✅ Criteria check: {percentage_met:.1f}% met, valid={is_valid}: {state.image_path}")

    return "valid" if is_valid else "invalid"


builder = StateGraph(GraphState, config_schema=Configuration)

builder.add_node("format_conversion", format_conversion)
builder.add_node("ocr_text_extraction", ocr_text_extraction)
builder.add_node("llm_text_extraction", llm_text_extraction, retry=RetryPolicy(max_attempts=3))
builder.add_node("criteria_checker", criteria_checker, retry=RetryPolicy(max_attempts=3))
builder.add_node("corrector", corrector, retry=RetryPolicy(max_attempts=3))

builder.add_edge(START, "format_conversion")
builder.add_edge("format_conversion", "ocr_text_extraction")
builder.add_edge("ocr_text_extraction", "llm_text_extraction")
builder.add_edge("llm_text_extraction", "criteria_checker")
builder.add_conditional_edges(
    "criteria_checker",
    should_continue,
    {
        "valid": END,
        "invalid": "corrector",
    },
)
builder.add_edge("corrector", "criteria_checker")

graph = builder.compile()


# Save graph visualization directly to file
# But it is often buggy
if "graph.png" not in os.listdir():
    try:
        graph_image = graph.get_graph().draw_mermaid_png(
            output_file_path="graph.png",
        )
    except Exception as e:
        print(f"Error generating graph image: {e}")
        graph_image = None


def run_graph(image_path: str) -> dict:
    """Run the graph."""
    print(f"🚀 Start processing: {image_path}")
    result = graph.invoke({"image_path": image_path})
    print(f"🎉 Process complete: {image_path}")
    llm_text_extraction_result: TARGET_SCHEMA = result["llm_text_extraction_result"]
    return llm_text_extraction_result.model_dump()


def batch_run_graph(image_paths: list[str]) -> list[dict]:
    """Run the graph for a batch of images using multiprocessing."""

    # Create a pool of workers
    with Pool(processes=cpu_count()) as pool:
        # Map the run_graph function to each image path with progress bar
        results = list(tqdm(pool.imap(run_graph, image_paths), total=len(image_paths), desc="Processing images"))

    return results
