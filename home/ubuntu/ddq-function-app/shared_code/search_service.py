# shared_code/search_service.py

import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType

class AzureSearchService:
    def __init__(self, search_service_name=None, search_index_name=None, search_api_key=None):
        """Initialize the Azure AI Search service.

        Args:
            search_service_name: The name of the Azure AI Search service.
            search_index_name: The name of the search index.
            search_api_key: The API key for the search service.
        """
        # These will come from environment variables in the Azure Function settings
        self.search_service_name = search_service_name or os.environ.get("AZURE_SEARCH_SERVICE_NAME")
        self.search_index_name = search_index_name or os.environ.get("AZURE_SEARCH_INDEX_NAME")
        self.search_api_key = search_api_key or os.environ.get("AZURE_SEARCH_API_KEY")

        if not all([self.search_service_name, self.search_index_name, self.search_api_key]):
            logging.error("Missing required Azure AI Search configuration (service name, index name, or API key).")
            raise ValueError("Missing required Azure AI Search configuration")

        # Create the search endpoint
        self.search_endpoint = f"https://{self.search_service_name}.search.windows.net"

        # Initialize the search client
        try:
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index_name,
                credential=AzureKeyCredential(self.search_api_key)
            )
            logging.info(f"Azure AI Search client initialized for endpoint: {self.search_endpoint}, index: {self.search_index_name}")
        except Exception as e:
            logging.error(f"Error initializing Azure AI Search client: {e}")
            raise

    def search_documents(self, query_text, filter_condition=None, top=5):
        """Search for documents in the Azure AI Search index.

        Args:
            query_text: The search query text.
            filter_condition: Optional OData filter condition.
            top: Maximum number of results to return.

        Returns:
            A dictionary containing the count and list of search results.
        """
        try:
            logging.info(f"Performing search for query: 	{query_text}	")
            # Use semantic search with vector capabilities if available and configured
            results = self.search_client.search(
                search_text=query_text,
                query_type=QueryType.SEMANTIC,  # Use semantic search for better results
                query_language="en-us",
                semantic_configuration_name="default", # Assumes a semantic config named 'default' exists
                filter=filter_condition,
                top=top,
                include_total_count=True
            )

            # Process and return the results
            search_results = []
            count = results.get_count()
            logging.info(f"Search returned {count} results.")

            for result in results:
                # Extract relevant fields from the search result
                document = {
                    "id": result.get("id", result.get("metadata_spo_item_id")), # Use common ID fields
                    "title": result.get("title", result.get("metadata_spo_item_name", "Untitled")), # Use common title fields
                    "content": result.get("content", ""),
                    "source": result.get("source", result.get("metadata_spo_item_path", "")), # Use common path fields
                    "sourceFile": result.get("sourceFile", result.get("metadata_spo_item_name", "")), # Use common name fields
                    "score": result["@search.score"],
                    "captions": result.get("@search.captions", [])
                }
                search_results.append(document)

            return {
                "count": count,
                "results": search_results
            }
        except Exception as e:
            logging.error(f"Error searching documents: {e}")
            raise

    def get_document_by_id(self, document_id):
        """Get a document by its ID.

        Args:
            document_id: The ID of the document to retrieve.

        Returns:
            The document if found, None otherwise.
        """
        try:
            logging.info(f"Retrieving document by ID: {document_id}")
            return self.search_client.get_document(key=document_id)
        except Exception as e:
            logging.error(f"Error getting document by ID 	{document_id}	: {e}")
            return None

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Configure logging for local testing
    logging.basicConfig(level=logging.INFO)
    try:
        # This requires environment variables to be set
        # Set them in your local environment for testing
        # export AZURE_SEARCH_SERVICE_NAME="your_service_name"
        # export AZURE_SEARCH_INDEX_NAME="your_index_name"
        # export AZURE_SEARCH_API_KEY="your_api_key"

        print("Attempting to initialize Azure Search Service...")
        search_service = AzureSearchService()

        # Example search query
        print("\nPerforming example search...")
        results = search_service.search_documents("ESG policy")

        print(f"\nFound {results['count']} results:")
        for idx, result in enumerate(results["results"]):
            print(f"\nResult {idx+1}:")
            print(f"  ID: {result['id']}")
            print(f"  Title: {result['title']}")
            print(f"  Source File: {result['sourceFile']}")
            print(f"  Score: {result['score']}")
            # print(f"  Content snippet: {result['content'][:150]}...") # Content can be large
            if result.get('captions'):
                print("  Captions:")
                for caption in result['captions']:
                    print(f"    - {caption.get('text', 'No caption text')}")

    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure Azure AI Search environment variables (AZURE_SEARCH_SERVICE_NAME, AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_API_KEY) are set.")
    except Exception as e:
        print(f"An unexpected error occurred during example run: {e}")

