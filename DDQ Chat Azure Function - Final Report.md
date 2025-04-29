# DDQ Chat Azure Function - Technical Overview

## 1. Purpose

This Azure Functions application provides a serverless API endpoint for answering Due Diligence Questionnaire (DDQ) questions. It leverages OpenAI for natural language generation, Azure AI Search for retrieving relevant information from indexed corporate documents, and Azure Blob Storage for storing generated response documents.

## 2. Architecture

The core workflow is initiated by an HTTP POST request to the function endpoint:

```
(Client / Custom GPT) ──► HTTP POST Request ──► Azure Function (Python)
                                                │
                                                ├─► Azure AI Search (Semantic Search) ──► (Document Index)
                                                │
                                                ├─► OpenAI (GPT Model) ──► (Answer Generation)
                                                │
                                                └─► Azure Blob Storage ──► (Generated DOCX Upload)
                                                │
                                                ◄── JSON Response (Answer + DOCX URL) ◄──┘
```

## 3. Key Components

The application is structured as follows:

*   **`DdqChatFunction/`**: Contains the main Azure Function trigger (`function.json`) and the core request processing logic (`__init__.py`).
    *   Handles request validation, service orchestration, error handling, and response formatting.
    *   Supports optional API key authentication (`x-api-key` header).
*   **`shared_code/`**: Houses reusable modules for interacting with Azure services:
    *   `openai_service.py`: Interfaces with the OpenAI API (Chat Completion). Includes basic retry logic.
    *   `search_service.py`: Queries the configured Azure AI Search index using semantic search.
    *   `blob_storage_service.py`: Manages interactions with Azure Blob Storage (uploading generated documents).
    *   `document_generator.py`: Creates a `.docx` file containing the question, AI-generated answer, and cited sources using `python-docx`, then uploads it via `blob_storage_service`.
*   **`templates/`**: Contains `.docx` templates (e.g., `standard.docx`) that can be optionally specified in the request to format the generated response document.
*   **`system_prompt.txt`**: Defines the base instructions provided to the OpenAI model to guide its response generation, emphasizing grounding in provided search results.
*   **Configuration Files**:
    *   `requirements.txt`: Lists Python package dependencies.
    *   `host.json`: Configures the Azure Functions host runtime.
    *   `local.settings.json`: Template for local development environment variables (requires user configuration).
    *   `openapi.json`: OpenAPI 3.0 specification describing the function's API contract.
*   **`README.md`**: Provides setup, configuration, and usage instructions.

## 4. Core Functionality

*   **Document-Grounded QA**: Answers are synthesized by OpenAI based on context retrieved from Azure AI Search, ensuring responses are tied to source material.
*   **Hybrid Search**: Leverages Azure AI Search's semantic search capabilities for relevance.
*   **Automatic Source Citation**: Identifies and lists the source documents used by Azure AI Search.
*   **Dynamic DOCX Generation**: Optionally generates a formatted Word document containing the question, answer, and sources, storing it in Azure Blob Storage and returning a URL.
*   **Telemetry Hooks**: Includes logging throughout the request lifecycle, suitable for integration with Application Insights.

## 5. Deployment & Configuration

Refer to the `README.md` for detailed instructions on:
*   Setting up the required Azure resources (Azure Functions App, AI Search, Blob Storage) and obtaining an OpenAI API Key.
*   Configuring necessary environment variables (API keys, service names, endpoints).
*   Deploying the function code to Azure.

## 6. API Contract

See `openapi.json` for the detailed API specification. The primary endpoint is:

*   **`POST /api/ddq-chat`** (or as defined in `function.json` and `host.json`)
    *   **Request Body**: JSON object containing `prompt` (string, required), `history` (array, optional), and `template` (string, optional).
    *   **Response Body**: JSON object containing `ai_response`, `sources`, `document_url`, `request_id`, and `processing_time_ms`.
