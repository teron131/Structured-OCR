import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from PIL import Image
from pydantic import BaseModel

from ..preprocess import image_to_base64


def run_llm(
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
    if "/" in model:
        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
            api_key=os.getenv("GOOGLE_API_KEY"),
        )
    else:
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
    if isinstance(llm, ChatOpenAI):
        structured_llm = llm.with_structured_output(schema, method="function_calling")
    else:
        structured_llm = llm.with_structured_output(schema)

    return structured_llm.invoke(messages)
