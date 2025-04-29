# DdqChatFunction/__init__.py

import logging
import json
import azure.functions as func
import os
import sys
import time
from datetime import datetime

# Add shared code directory to path
SHARED_CODE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared_code"))
if SHARED_CODE_DIR not in sys.path:
    sys.path.append(SHARED_CODE_DIR)

# Import shared code modules
from openai_service import get_openai_completion
from search_service import AzureSearchService
from blob_storage_service import BlobStorageService
from document_generator import generate_and_upload_docx

# --- Configuration Validation ---
def validate_env_vars():
    """Validate required environment variables."""
    required_vars = [
        "OPENAI_API_KEY",
        "AZURE_SEARCH_SERVICE_NAME",
        "AZURE_SEARCH_INDEX_NAME",
        "AZURE_SEARCH_API_KEY",
        "AZURE_STORAGE_ACCOUNT_NAME",
        "AZURE_STORAGE_CONTAINER_NAME"
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        logging.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    return True

# --- Load System Prompt ---
try:
    prompt_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "system_prompt.txt"))
    with open(prompt_file_path, "r") as f:
        SYSTEM_PROMPT = f.read()
    logging.info("System prompt loaded successfully.")
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a helpful AI assistant." # Fallback prompt
    logging.warning("Warning: system_prompt.txt not found. Using default prompt.")
except Exception as e:
    SYSTEM_PROMPT = "You are a helpful AI assistant." # Fallback prompt
    logging.error(f"Error loading system_prompt.txt: {e}. Using default prompt.")

# --- Initialize Services (Consider potential cold start implications) ---
# Initialize outside the main function for potential reuse across invocations
# Handle initialization errors gracefully
validate_env_vars()

try:
    search_service = AzureSearchService()
    logging.info("Azure AI Search service initialized globally.")
except ValueError as e:
    logging.error(f"Global initialization failed for Azure AI Search: {e}")
    search_service = None # Mark as failed
except Exception as e:
    logging.error(f"Unexpected global initialization error for Azure AI Search: {e}")
    search_service = None # Mark as failed

try:
    blob_service = BlobStorageService()
    logging.info("Azure Blob Storage service initialized globally.")
except ValueError as e:
    logging.error(f"Global initialization failed for Azure Blob Storage: {e}")
    blob_service = None # Mark as failed
except Exception as e:
    logging.error(f"Unexpected global initialization error for Azure Blob Storage: {e}")
    blob_service = None # Mark as failed

# --- Helper Functions ---
def validate_input(req_body):
    """Validate the input request body."""
    errors = []
    prompt = req_body.get("prompt", "")
    
    if not prompt.strip():
        errors.append("Prompt is empty")
    
    if len(prompt) > 5000:  # Prevent excessively long inputs
        errors.append("Prompt exceeds maximum length of 5000 characters")
    
    return errors

def sanitize_for_logging(text, max_length=50):
    """Sanitize text for logging to avoid exposing sensitive information."""
    if not text:
        return "<empty>"
    if len(text) > max_length:
        return f"{text[:max_length]}..."
    return text

def process_search_results(results, query):
    """Process search results and extract context and sources."""
    context = ""
    sources = set()
    
    if results and results.get("results"):
        context += "\n\nRelevant Document Snippets:\n"
        for result in results["results"]:
            content_snippet = result.get("content", "")
            source_file = result.get("sourceFile", "Unknown Source")
            context += f"\n---\nSource: {source_file}\nSnippet: {content_snippet}\n---"
            sources.add(source_file)
        logging.info(f"Added context from {len(sources)} sources.")
    else:
        context = "\n\nNo relevant documents found in the search index for this query."
        logging.info("No relevant documents found by search.")
    
    return context, sources

def prepare_openai_messages(system_prompt, search_context, user_question, history=None):
    """Prepare messages for OpenAI in the correct format."""
    messages = [
        {"role": "system", "content": system_prompt + search_context},
        {"role": "user", "content": user_question}
    ]
    
    # Add conversation history if provided
    if history and isinstance(history, list):
        # Insert history messages before the current user question
        history_messages = []
        for h in history:
            if isinstance(h, dict) and "role" in h and "content" in h:
                if h["role"] in ["user", "assistant", "system"]:
                    history_messages.append({"role": h["role"], "content": h["content"]})
        
        if history_messages:
            # Insert history between system message and current user message
            messages = [messages[0]] + history_messages + [messages[-1]]
    
    return messages

def track_metrics(prompt_length, sources_count, response_length, processing_time_ms):
    """Track metrics for the function execution."""
    # In a production environment, this would send metrics to a monitoring system
    # For now, we'll just log them
    logging.info(f"Metrics - Prompt Length: {prompt_length}, Sources: {sources_count}, " + 
                f"Response Length: {response_length}, Processing Time: {processing_time_ms}ms")

def main(req: func.HttpRequest) -> func.HttpResponse:
    request_start_time = time.time()
    request_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
    logging.info(f"Request {request_id}: Processing DDQ query")

    # --- API Key Authentication (if configured) ---
    api_key = req.headers.get('x-api-key')
    expected_key = os.environ.get('FUNCTION_API_KEY')
    
    if expected_key and (not api_key or api_key != expected_key):
        logging.warning(f"Request {request_id}: Invalid or missing API key")
        return func.HttpResponse("Unauthorized", status_code=401)

    # --- Check Service Initialization ---
    if not search_service:
        logging.error(f"Request {request_id}: Azure AI Search service is not available due to initialization failure.")
        return func.HttpResponse("Internal Server Error: Search service unavailable.", status_code=503) # Service Unavailable
    if not blob_service:
        logging.error(f"Request {request_id}: Azure Blob Storage service is not available due to initialization failure.")
        return func.HttpResponse("Internal Server Error: Blob service unavailable.", status_code=503) # Service Unavailable

    # --- Get Request Body ---
    try:
        req_body = req.get_json()
    except ValueError:
        logging.error(f"Request {request_id}: Invalid JSON received in request body.")
        return func.HttpResponse(
             "Please pass a valid JSON object in the request body",
             status_code=400
        )

    # --- Extract and Validate Input Data ---
    user_question = req_body.get("prompt")
    history = req_body.get("history", [])  # Support for conversation history
    template_name = req_body.get("template")  # Optional document template name

    # Validate inputs
    validation_errors = validate_input(req_body)
    if validation_errors:
        error_message = "; ".join(validation_errors)
        logging.warning(f"Request {request_id}: Input validation failed - {error_message}")
        return func.HttpResponse(f"Input validation failed: {error_message}", status_code=400)

    logging.info(f"Request {request_id}: Received prompt: {sanitize_for_logging(user_question)}")

    # --- Core DDQ Processing Logic ---
    try:
        # 1. Search for relevant documents
        search_context = ""
        source_files = set()
        try:
            search_results = search_service.search_documents(user_question, top=3)
            search_context, source_files = process_search_results(search_results, user_question)
        except Exception as e:
            logging.error(f"Request {request_id}: Error during Azure AI Search query: {e}")
            search_context = "\n\nError retrieving documents from search index."

        # 2. Prepare messages for OpenAI
        messages = prepare_openai_messages(SYSTEM_PROMPT, search_context, user_question, history)

        # 3. Call OpenAI
        try:
            completion = get_openai_completion(messages)
            ai_response_text = completion.choices[0].message.content if completion.choices else "Sorry, I could not generate a response."
            logging.info(f"Request {request_id}: Received response from OpenAI.")
        except Exception as e:
            logging.error(f"Request {request_id}: Error calling OpenAI: {e}")
            # Don't expose internal error details directly to the caller
            return func.HttpResponse("Internal Server Error: Failed to get response from AI model.", status_code=500)

        # 4. Generate Document and Upload
        document_url = None
        try:
            document_url = generate_and_upload_docx(
                question=user_question,
                answer=ai_response_text,
                sources=list(source_files),
                blob_service=blob_service,
                blob_prefix="ddq_responses",
                template_name=template_name
            )
            if document_url:
                logging.info(f"Request {request_id}: Document generated and uploaded to: {sanitize_for_logging(document_url)}")
            else:
                logging.warning(f"Request {request_id}: Document generation or upload failed.")
        except Exception as e:
            logging.error(f"Request {request_id}: Error during document generation/upload: {e}")
            # Continue without document URL if generation fails, but log it

        # 5. Calculate and track metrics
        request_end_time = time.time()
        processing_time_ms = int((request_end_time - request_start_time) * 1000)
        track_metrics(
            prompt_length=len(user_question),
            sources_count=len(source_files),
            response_length=len(ai_response_text) if ai_response_text else 0,
            processing_time_ms=processing_time_ms
        )

        # 6. Prepare and Return Response
        response_data = {
            "ai_response": ai_response_text,
            "document_url": document_url,  # Will be None if upload failed
            "sources": list(source_files),
            "request_id": request_id,
            "processing_time_ms": processing_time_ms
        }
        logging.info(f"Request {request_id}: Successfully processed request in {processing_time_ms}ms.")
        return func.HttpResponse(
            json.dumps(response_data),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Request {request_id}: An unexpected error occurred: {e}", exc_info=True)
        return func.HttpResponse("Internal Server Error: An unexpected error occurred.", status_code=500)

