import os

from google.genai import Client, types
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from PIL import Image
from pydantic import BaseModel

from ..utils import image_to_base64


def run_llm_langchain(
    model: str,
    prompt: str,
    reference_image: Image.Image = None,
    reference_text: str = None,
    schema: BaseModel = None,
) -> BaseModel:
    """Run a LLM with a system prompt, reference image, and reference text, and return a structured output.

    Args:
        model (str): The model to use.
        prompt (str): The prompt to pass to the LLM.
        reference_image (Image.Image): The image to pass to the LLM.
        reference_text (str): The text to pass to the LLM.
        schema (BaseModel): The schema to use for the structured output.

    Returns:
        BaseModel: The structured output of the LLM.
    """
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

    messages = [SystemMessage(prompt)]

    content = []
    if reference_image:
        image_base64 = image_to_base64(reference_image)
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            }
        )
    if reference_text:
        content.append(
            {
                "type": "text",
                "text": reference_text,
            }
        )

    messages.append(HumanMessage(content))

    # Upon langchain_openai==0.3.0, the default method changed from “function_calling” to “json_schema”. Pydantic model would cause error and thus it requires to specify to "function_calling". Other BaseChatModel does not support the argument `method` and thus it remains no argument.
    structured_llm = llm.with_structured_output(schema, method="function_calling")

    return structured_llm.invoke(messages)


def run_llm_gemini(
    model: str,
    prompt: str,
    reference_image: Image.Image = None,
    reference_text: str = None,
    schema: BaseModel = None,
) -> BaseModel:
    """Run a LLM with a system prompt, reference image, and reference text, and return a structured output."""
    client = Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options={"timeout": 600000},  # 10 minutes
    )

    contents = [prompt]
    if reference_image:
        contents.append(types.Part.from_bytes(data=image_to_base64(reference_image), mime_type="image/jpeg"))
    if reference_text:
        contents.append(reference_text)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0,
            response_modalities=["TEXT"],
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )

    return response.parsed


def run_llm(
    model: str,
    prompt: str,
    reference_image: Image.Image = None,
    reference_text: str = None,
    schema: BaseModel = None,
) -> BaseModel:
    """Route the LLM call to the appropriate function based on the model name."""
    if "/" in model:
        return run_llm_langchain(model, prompt, reference_image, reference_text, schema)
    else:
        return run_llm_gemini(model, prompt, reference_image, reference_text, schema)
