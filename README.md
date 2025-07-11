# Structured-OCR

A streamlined tool for extracting structured data from scanned documents using OCR and LLM techniques. Outputs are delivered as Pydantic models for easy integration.

## Architecture

The tool uses a graph-based processing pipeline that combines OCR and LLM techniques:

![Processing Graph](graph.png)

The pipeline includes:
1. **Format Conversion**: Prepare image for processing
2. **OCR Text Extraction**: Extract raw text using Google Document AI (optional)
3. **LLM Text Extraction**: Structure data using language models
4. **Criteria Checker**: Validate extraction quality
5. **Corrector**: Fix issues based on validation feedback


## Key Features

- **Custom Schemas**: Define your own Pydantic schemas for tailored data extraction.
- **OCR & LLM Extraction**: Combine OCR with LLM prompts for accurate text and table parsing.
- **Automated Validation**: Criteria-based checks with targeted corrections (up to 3 attempts).
- **Image Processing**: Preprocessing (e.g., deskew, white balance) for better OCR quality.
- **Structured Output**: Results as Pydantic objects, ready for downstream use.

## Installation

```bash
git clone https://github.com/teron131/structured-ocr.git
cd Structured-OCR
uv sync
cp .env.example .env       # Set your API keys and config
```

## Quick Start

```python
from structured_ocr.llm_ocr import run_graph

# Extract structured data from an image
result = run_graph("path/to/document.jpg")
print(result)
```

For advanced configuration, refer to the `schema.py` and `prompt.py` files to customize schemas and prompts as needed.

