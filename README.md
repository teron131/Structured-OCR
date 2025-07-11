# Structured-OCR

A powerful tool for extracting structured data from scanned documents using OCR and LLM techniques. The tool combines traditional OCR with modern language models to deliver highly accurate, structured outputs as Pydantic models.

## Architecture

The tool uses a graph-based processing pipeline that intelligently combines OCR and LLM techniques:

![Processing Graph](graph.png)

The pipeline includes:
1. **Format Conversion**: Prepare image for processing (bytes, base64 encoding)
2. **OCR Text Extraction**: Extract raw text using Google Document AI (optional)
3. **LLM Text Extraction**: Structure data using language models with vision capabilities
4. **Criteria Checker**: Validate extraction quality against predefined criteria
5. **Corrector**: Automatically fix issues based on validation feedback (up to 3 attempts)

## Key Features

- **🎯 Custom Schemas**: Define your own Pydantic schemas for tailored data extraction
- **🔗 Hybrid Approach**: Combine traditional OCR with LLM vision for maximum accuracy
- **✅ Automated Validation**: Criteria-based quality checks with intelligent corrections
- **🖼️ Image Preprocessing**: Built-in image enhancement (deskew, contrast, denoising)
- **📊 Structured Output**: Results as Pydantic objects, ready for downstream processing
- **⚡ Batch Processing**: Process multiple images in parallel
- **🔧 Highly Configurable**: Customize prompts, criteria, and processing parameters

## Installation

```bash
git clone https://github.com/teron131/structured-ocr.git
cd structured-ocr
uv sync
cp .env.example .env       # Set your API keys and configuration
```

### Environment Setup

Create a `.env` file with your API keys:

```env
# LLM Configuration
LLM_OCR=gpt-4o                    # Model for text extraction
LLM_CHECKER=gpt-4o-mini           # Model for criteria validation

# Google Cloud (optional, for OCR)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id
```

## Quick Start

### Basic Usage

```python
from structured_ocr.llm_ocr import run_graph

# Extract structured data from an image
result = run_graph("path/to/document.jpg")
print(result)
```

### Batch Processing

```python
from structured_ocr.llm_ocr import batch_run_graph

# Process multiple images in parallel
image_paths = ["doc1.jpg", "doc2.jpg", "doc3.jpg"]
results = batch_run_graph(image_paths)
```

### Configuration Options

```python
from structured_ocr.llm_ocr import graph
from langchain_core.runnables import RunnableConfig

# Custom configuration
config = RunnableConfig(
    configurable={
        "use_ocr": True,                    # Enable Google Document AI OCR
        "llm_ocr": "gpt-4o",               # LLM model for extraction
        "llm_checker": "gpt-4o-mini",      # LLM model for validation
        "max_correction": 3,               # Maximum correction attempts
        "criteria_met_perc": 80,           # Percentage of criteria that must pass
        "criterion_score_threshold": 7,    # Minimum score per criterion (0-10)
    }
)

result = graph.invoke({"image_path": "document.jpg"}, config=config)
```

## Advanced Customization

### 1. Custom Schemas

Define your own Pydantic models in `structured_ocr/llm_ocr/schema.py`:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class CustomDocument(BaseModel):
    title: str = Field(description="Document title")
    date: Optional[str] = Field(description="Document date in YYYY-MM-DD format")
    amount: float = Field(description="Total amount", ge=0)
    items: List[str] = Field(description="List of items or services")
    
    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        # Add custom validation logic
        return v

# Update the target schema
TARGET_SCHEMA = CustomDocument
```

### 2. Custom Prompts

Modify prompts in `structured_ocr/llm_ocr/prompt.py`:

```python
# Text extraction prompt
TEXT_EXTRACTION_PROMPT = """
You are analyzing a {document_type} document. Extract the following information:

1. Document title (usually at the top)
2. Date (in various formats, convert to YYYY-MM-DD)
3. Total amount (numerical value)
4. List of items or services mentioned

Guidelines:
- Be precise with numerical values
- Handle different date formats gracefully
- Extract all relevant items even if formatting varies
- Return null for missing information rather than guessing
"""

# Criteria validation prompt
CHECKER_PROMPT = """
Evaluate the extraction quality on a scale of 0-10 for each criterion:

1. TITLE_ACCURACY (0-10): Is the document title correctly identified?
2. DATE_FORMAT (0-10): Is the date properly formatted as YYYY-MM-DD?
3. AMOUNT_PRECISION (0-10): Is the numerical amount accurate?
4. ITEMS_COMPLETENESS (0-10): Are all items/services extracted?

Provide detailed feedback for scores below 7.
"""
```

### 3. Custom Criteria

Define validation criteria in your schema:

```python
class CustomCriteria(BaseModel):
    title_accuracy: int = Field(description="Accuracy of title extraction", ge=0, le=10)
    date_format: int = Field(description="Correctness of date format", ge=0, le=10)
    amount_precision: int = Field(description="Precision of amount extraction", ge=0, le=10)
    items_completeness: int = Field(description="Completeness of items list", ge=0, le=10)
    
    reasons: Optional[str] = Field(description="Detailed reasons for low scores")

# Map criteria to schema fields for targeted corrections
CRITERIA_TO_RELATED_FIELDS = {
    "title_accuracy": ["title"],
    "date_format": ["date"],
    "amount_precision": ["amount"],
    "items_completeness": ["items"],
}
```

### 4. Image Preprocessing

Enhance image quality before processing:

```python
from structured_ocr.preprocess import (
    deskew_image,
    adjust_whitebalance,
    adjust_contrast,
    denoise_image
)
from PIL import Image

# Load and preprocess image
image = Image.open("document.jpg")
image = deskew_image(image)
image = adjust_whitebalance(image, percentile=99)
image = adjust_contrast(image, contrast=1.15)
image = denoise_image(image)

# Save preprocessed image
image.save("preprocessed_document.jpg")

# Then process with structured OCR
result = run_graph("preprocessed_document.jpg")
```

## Configuration Reference

### Core Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_ocr` | `False` | Enable Google Document AI OCR |
| `llm_ocr` | `gpt-4o` | LLM model for text extraction |
| `llm_checker` | `gpt-4o-mini` | LLM model for criteria validation |
| `max_correction` | `3` | Maximum correction attempts |
| `criteria_met_perc` | `80` | Percentage of criteria that must pass |
| `criterion_score_threshold` | `7` | Minimum score per criterion (0-10) |

### Model Options

**Recommended LLM Models:**
- `gpt-4o` - Best accuracy for complex documents
- `gpt-4o-mini` - Fast and cost-effective for validation
- `claude-3-haiku` - Alternative with good performance
- `gemini-pro-vision` - Google's vision-language model

## Examples

### Invoice Processing

```python
from structured_ocr.llm_ocr import run_graph

# Process an invoice
result = run_graph("invoice.pdf")

# Access structured data
invoice_data = result
print(f"Invoice Total: ${invoice_data['amount']}")
print(f"Date: {invoice_data['date']}")
print(f"Items: {invoice_data['items']}")
```

### Receipt Analysis

```python
# Custom configuration for receipts
config = RunnableConfig(
    configurable={
        "use_ocr": True,  # OCR helpful for receipts
        "criteria_met_perc": 90,  # Higher accuracy requirement
        "max_correction": 5,  # More correction attempts
    }
)

result = graph.invoke({"image_path": "receipt.jpg"}, config=config)
```

### Document Validation

```python
# Check validation results
result = run_graph("document.jpg")
if result.get('criteria'):
    criteria = result['criteria']
    print(f"Validation scores: {criteria}")
    if criteria.get('reasons'):
        print(f"Issues found: {criteria['reasons']}")
```

## Troubleshooting

### Common Issues

1. **Low Accuracy**: Try enabling OCR or using image preprocessing
2. **Model Errors**: Check API keys and model availability
3. **Validation Failures**: Adjust criteria thresholds or prompts
4. **Processing Slow**: Use lighter models or reduce max_correction

### Performance Tips

- Use `gpt-4o-mini` for validation to reduce costs
- Enable OCR for text-heavy documents
- Preprocess images for better quality
- Use batch processing for multiple documents
- Cache results for repeated processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📖 Documentation: Check the code examples and docstrings
- 🐛 Issues: Report bugs on GitHub Issues
- 💡 Feature Requests: Open a discussion on GitHub
- 📧 Contact: Create an issue for support questions

