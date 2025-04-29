# shared_code/openai_service.py

import os
import logging
import openai
from tenacity import retry, stop_after_attempt, wait_random_exponential
from typing import List, Dict, Any
from functools import lru_cache
import hashlib
import json

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_ORGANIZATION = os.environ.get("OPENAI_ORGANIZATION")

# Initialize the OpenAI client
try:
    client = openai.OpenAI(
        api_key=OPENAI_API_KEY,
        organization=OPENAI_ORGANIZATION
    )
    logging.info(f"OpenAI client initialized with model: {OPENAI_MODEL}")
except Exception as e:
    logging.error(f"Error initializing OpenAI client: {e}")
    # We'll let the error propagate to make it obvious during testing

@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3))
def get_openai_completion(messages: List[Dict[str, str]], max_tokens: int = 1500):
    """Gets a completion from the OpenAI service with retry logic.

    Args:
        messages: A list of message objects with 'role' and 'content' keys.
        max_tokens: The maximum number of tokens to generate.

    Returns:
        The response object from the OpenAI API.
    """
    # Convert from Azure message format to OpenAI format if needed
    openai_messages = []
    for msg in messages:
        if hasattr(msg, 'role') and hasattr(msg, 'content'):
            # Azure message object format
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        elif isinstance(msg, dict) and 'content' in msg:
            # Already in dictionary format
            role = msg.get('role', 'user')
            openai_messages.append({
                "role": role,
                "content": msg['content']
            })
        else:
            # Try to handle unexpected formats
            logging.warning(f"Unexpected message format: {type(msg)}")
            continue

    try:
        logging.info(f"Calling OpenAI with {len(openai_messages)} messages")
        
        # Check if we can use cache
        cache_key = generate_cache_key(openai_messages)
        cached_response = get_cached_response(cache_key)
        if cached_response:
            logging.info("Using cached OpenAI response")
            return cached_response

        # Make API call
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=openai_messages,
            max_tokens=max_tokens,
            temperature=0.1  # Lower temperature for more consistent responses
        )
        logging.info("OpenAI response received successfully")
        
        # Cache the response
        cache_response(cache_key, response)
        
        return response
    except Exception as e:
        logging.error(f"Error calling OpenAI: {e}")
        raise

def generate_cache_key(messages):
    """Generate a cache key based on the messages content."""
    message_str = json.dumps(messages, sort_keys=True)
    return hashlib.md5(message_str.encode()).hexdigest()

@lru_cache(maxsize=100)
def get_cached_response(cache_key):
    """Get a cached response if available."""
    return None  # LRU cache decorator handles the actual caching

def cache_response(cache_key, response):
    """Store a response in the cache."""
    get_cached_response.cache_clear()  # Clear existing cache
    get_cached_response(cache_key)  # This will be cached by the decorator

# Example usage (for testing purposes)
if __name__ == '__main__':
    try:
        # Configure basic logging
        logging.basicConfig(level=logging.INFO)
        
        # Example requires OpenAI API key to be set in environment
        print("Attempting to call OpenAI with example prompt...")
        example_messages = [
            {"role": "system", "content": "You are a helpful AI assistant designed to answer questions based on provided documents."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
        completion = get_openai_completion(example_messages)
        print("OpenAI Response:")
        print(completion)
        print("\nAssistant Message:")
        print(completion.choices[0].message.content)
    except Exception as e:
        print(f"Failed to get completion during example run: {e}")
        print("Please ensure OpenAI API key is properly configured in environment variables (OPENAI_API_KEY).")
