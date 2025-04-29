# Implementation Guide: DDQ Chat Azure Function

This guide explains the implementation details of the DDQ Chat Azure Function, including the project structure, code logic, and interaction between components.

## 1. Project Structure

The project is organized as follows:

```
/home/ubuntu/ddq-function-app/
├── DdqChatFunction/           # Main Azure Function directory
│   ├── __init__.py            # Function entry point code
│   └── function.json          # Function bindings configuration
├── shared_code/               # Directory for shared Python modules
│   ├── openai_service.py      # Handles Azure OpenAI interaction
│   ├── search_service.py      # Handles Azure AI Search interaction
│   ├── blob_storage_service.py # Handles Azure Blob Storage interaction
│   └── document_generator.py  # Handles DOCX document generation
├── documentation/             # Contains all documentation files
│   ├── deployment_guide.md
│   ├── security_guide.md
│   └── implementation_guide.md (this file)
├── .venv/                     # Python virtual environment (excluded from deployment)
├── host.json                  # Function host configuration
├── local.settings.json        # Local development settings (contains secrets, excluded from source control)
├── requirements.txt           # Python package dependencies
└── system_prompt.txt          # System prompt for the Azure OpenAI model
```

## 2. Configuration Files

### `host.json`

This file configures the Azure Functions host runtime.
- **`version: "2.0"`**: Specifies the schema version.
- **`logging`**: Configures logging behavior, including Application Insights integration and sampling.
- **`extensionBundle`**: Specifies the Microsoft Azure Functions Extension Bundle, required for triggers like HTTP.

### `local.settings.json`

This file stores application settings used during local development. **It should not be committed to source control** as it contains sensitive information.
- **`IsEncrypted: false`**: Indicates settings are not encrypted locally.
- **`Values`**: A dictionary containing key-value pairs for environment variables:
  - `AzureWebJobsStorage`: Connection string for the storage account used by the Functions runtime.
  - `FUNCTIONS_WORKER_RUNTIME`: Set to `"python"`.
  - `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`: For service principal authentication if needed (e.g., SharePoint/Graph).
  - `AZURE_OAI_ENDPOINT`, `AZURE_OAI_MODEL_NAME`: Azure OpenAI service details.
  - `AZURE_SEARCH_SERVICE_NAME`, `AZURE_SEARCH_INDEX_NAME`, `AZURE_SEARCH_API_KEY`: Azure AI Search service details.
  - `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_CONTAINER_NAME`: Blob storage details for generated documents.
  - `SHAREPOINT_SITE_URL`, `SHAREPOINT_SITE_NAME`, `SHAREPOINT_DOCUMENT_LIBRARY`: SharePoint details if directly accessed (though primarily used via AI Search indexer in this setup).
  - `AZURE_MONITOR_CONNECTION_STRING`: For Application Insights.

**Note:** When deployed to Azure, these settings must be configured as **Application Settings** in the Function App configuration.

### `requirements.txt`

Lists all Python dependencies required by the function. Generated using `pip freeze > requirements.txt` from the virtual environment.

## 3. Function Code (`DdqChatFunction/`)

### `function.json`

Defines the triggers and bindings for the `DdqChatFunction`.
- **`scriptFile: "__init__.py"`**: Specifies the entry point script.
- **`bindings`**: An array defining inputs and outputs:
  - **HTTP Trigger (`req`)**: 
    - `authLevel: "anonymous"`: Allows public access without API keys.
    - `type: "httpTrigger"`: Defines it as an HTTP-triggered function.
    - `direction: "in"`: Input binding.
    - `name: "req"`: Name used to access the request object in the Python code.
    - `methods: ["post"]`: Restricts the function to only accept HTTP POST requests.
  - **HTTP Output (`$return`)**: 
    - `type: "http"`: Defines the output as an HTTP response.
    - `direction: "out"`: Output binding.
    - `name: "$return"`: The return value of the Python function (`main`) will be used as the HTTP response.

### `__init__.py`

This is the main script executed when the function is triggered.

1.  **Imports:** Imports necessary libraries (`logging`, `json`, `azure.functions`, `os`, `sys`) and the shared code modules (`openai_service`, `search_service`, `blob_storage_service`, `document_generator`). It modifies `sys.path` to ensure the `shared_code` directory is discoverable.
2.  **Load System Prompt:** Reads the `system_prompt.txt` file into the `SYSTEM_PROMPT` variable. Includes error handling and a fallback prompt.
3.  **Initialize Services (Global Scope):** Initializes `AzureSearchService` and `BlobStorageService` outside the `main` function. This allows potential reuse across function invocations (improving performance by reducing cold starts for these clients). Initialization errors are caught and logged, setting the service variables to `None`.
4.  **`main(req: func.HttpRequest)` Function:**
    *   **Entry Point:** The function triggered by the HTTP request.
    *   **Service Check:** Checks if the globally initialized services (`search_service`, `blob_service`) are available. If not (due to initialization errors), it returns a 503 Service Unavailable error.
    *   **Get Request Body:** Parses the incoming JSON request body.
    *   **Extract Input:** Retrieves the `"prompt"` (user question) from the JSON body. Includes basic validation.
    *   **Core Logic (try/except block):**
        *   **Search:** Calls `search_service.search_documents()` with the user question. Formats the results (content snippets and source file names) into a `search_context` string.
        *   **Prepare Messages:** Creates a list of messages for the OpenAI API, including the `SYSTEM_PROMPT` (combined with `search_context`) and the `UserMessage` containing the `user_question`.
        *   **Call OpenAI:** Calls `openai_service.get_openai_completion()` with the prepared messages.
        *   **Generate & Upload Document:** Calls `document_generator.generate_and_upload_docx()` with the question, AI answer, source file list, and the initialized `blob_service` instance. Stores the returned document URL.
        *   **Prepare Response:** Creates a JSON dictionary containing `ai_response`, `document_url`, and `sources`.
        *   **Return HTTP Response:** Returns a `func.HttpResponse` with the JSON payload, `application/json` mimetype, and a 200 status code.
    *   **Error Handling:** Includes try/except blocks around service calls and the main processing logic to catch errors, log them, and return appropriate HTTP error responses (e.g., 400 for bad requests, 500/503 for internal server errors).

## 4. Shared Code (`shared_code/`)

This directory contains reusable modules for interacting with Azure services.

### `openai_service.py`

- **Purpose:** Interacts with the Azure OpenAI service.
- **Initialization:** Reads endpoint and model name from environment variables (`AZURE_OAI_ENDPOINT`, `AZURE_OAI_MODEL_NAME`). Initializes `ChatCompletionsClient` using `DefaultAzureCredential` (requires Managed Identity on the Function App).
- **`get_openai_completion(messages, max_tokens)`:** Takes a list of message objects (SystemMessage, UserMessage, etc.) and sends them to the configured OpenAI model using `client.complete()`. Returns the completion response.
- **Error Handling:** Includes basic try/except blocks for initialization and API calls.

### `search_service.py`

- **Purpose:** Interacts with the Azure AI Search service.
- **`AzureSearchService` Class:**
  - **`__init__`:** Reads service name, index name, and API key from environment variables. Initializes `SearchClient` using `AzureKeyCredential`.
  - **`search_documents(query_text, filter_condition, top)`:** Performs a semantic search using `search_client.search()`. Extracts relevant fields (`id`, `title`, `content`, `source`, `sourceFile`, `score`, `captions`) from the results and returns a dictionary containing the count and a list of processed results.
  - **`get_document_by_id(document_id)`:** Retrieves a single document by its key (not currently used in the main workflow but available).
- **Error Handling:** Includes try/except blocks for initialization and search operations.

### `blob_storage_service.py`

- **Purpose:** Interacts with Azure Blob Storage.
- **`BlobStorageService` Class:**
  - **`__init__`:** Reads storage account name, container name, and optionally a connection string from environment variables. Initializes `BlobServiceClient` using either `DefaultAzureCredential` (if account name is provided) or `from_connection_string`. Creates the container if it doesn't exist.
  - **`upload_document(document_content, blob_name, content_type)`:** Uploads byte content (`document_content`) to the specified `blob_name` within the container using `blob_client.upload_blob()`. Sets the `Content-Type` and returns the blob URL.
  - **`download_document(blob_name)`:** Downloads a blob's content.
  - **`list_documents(prefix)`:** Lists blobs in the container.
  - **`get_document_url(blob_name)`:** Returns the URL for a given blob name.
- **Error Handling:** Includes try/except blocks for initialization and blob operations.

### `document_generator.py`

- **Purpose:** Creates a DOCX document and uploads it.
- **`generate_and_upload_docx(question, answer, sources, blob_service, blob_prefix)`:**
  - Uses the `python-docx` library to create a new `Document` object.
  - Adds formatted sections for the Title, Question, Answer, and Sources Consulted.
  - Saves the document to an in-memory byte stream (`io.BytesIO`).
  - Generates a unique blob name (e.g., `ddq_responses/response_xxxx.docx`).
  - Calls `blob_service.upload_document()` to upload the byte stream content to Blob Storage.
  - Returns the URL of the uploaded blob.
- **Error Handling:** Includes a try/except block around the generation and upload process.

## 5. System Prompt (`system_prompt.txt`)

- **Purpose:** Provides instructions to the Azure OpenAI model on how to behave.
- **Content:** Defines the AI's role (DDQ assistant for Hudson Advisors), core instructions (use only provided context, cite sources, handle unanswerable questions), workflow context, and examples.
- **Usage:** Loaded by `__init__.py` and combined with search results before being sent to the OpenAI API as the system message.

## 6. Overall Workflow

1.  A custom GPT sends an HTTP POST request to the Azure Function URL with a JSON body containing `{"prompt": "User's DDQ Question"}`.
2.  The Azure Function (`__init__.py`) receives the request.
3.  It calls `search_service.search_documents()` to find relevant document snippets from Azure AI Search.
4.  It constructs a list of messages, including the system prompt (augmented with search results) and the user's question.
5.  It calls `openai_service.get_openai_completion()` to get an answer from the Azure OpenAI model.
6.  It calls `document_generator.generate_and_upload_docx()` to create a DOCX file containing the question, answer, and sources, and uploads it to Azure Blob Storage using `blob_storage_service`.
7.  The function constructs a JSON response containing the AI's text answer, the URL of the generated DOCX file, and the list of source files used.
8.  The function returns this JSON response via HTTP to the custom GPT.
