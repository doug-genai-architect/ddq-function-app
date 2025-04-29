# shared_code/blob_storage_service.py

import os
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.identity import DefaultAzureCredential

class BlobStorageService:
    def __init__(self, storage_account_name=None, container_name=None, connection_string=None):
        """Initialize the Azure Blob Storage service.
        
        Args:
            storage_account_name: The name of the Azure Storage account.
            container_name: The name of the blob container.
            connection_string: Optional connection string (if not using DefaultAzureCredential).
        """
        # These will come from environment variables in the Azure Function settings
        self.storage_account_name = storage_account_name or os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
        self.container_name = container_name or os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
        self.connection_string = connection_string or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        
        if not self.container_name:
            logging.error("Missing required Blob Storage container name.")
            raise ValueError("Missing required Blob Storage container name")
        
        # Initialize the blob service client
        try:
            if self.connection_string:
                # Use connection string if provided
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                logging.info(f"Blob Storage client initialized using connection string for container: {self.container_name}")
            elif self.storage_account_name:
                # Use DefaultAzureCredential if storage account name is provided
                account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
                logging.info(f"Blob Storage client initialized using DefaultAzureCredential for account: {self.storage_account_name}, container: {self.container_name}")
            else:
                logging.error("Either storage_account_name or connection_string must be provided.")
                raise ValueError("Either storage_account_name or connection_string must be provided")
            
            # Get a reference to the container
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Create the container if it doesn't exist
            try:
                self.container_client.get_container_properties()
                logging.info(f"Container '{self.container_name}' exists.")
            except Exception:
                logging.info(f"Container '{self.container_name}' does not exist. Creating...")
                self.container_client.create_container()
                logging.info(f"Container '{self.container_name}' created successfully.")
        except Exception as e:
            logging.error(f"Error initializing Blob Storage client: {e}")
            raise
    
    def upload_document(self, document_content, blob_name, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        """Upload a document to Azure Blob Storage.
        
        Args:
            document_content: The content of the document (bytes).
            blob_name: The name of the blob.
            content_type: The content type of the document.
            
        Returns:
            The URL of the uploaded document if successful, None otherwise.
        """
        try:
            logging.info(f"Uploading document to blob: {blob_name}")
            # Get a blob client
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Set content settings
            content_settings = ContentSettings(content_type=content_type)
            
            # Upload the document
            blob_client.upload_blob(document_content, overwrite=True, content_settings=content_settings)
            
            # Return the URL of the uploaded document
            logging.info(f"Document uploaded successfully. URL: {blob_client.url}")
            return blob_client.url
        except Exception as e:
            logging.error(f"Error uploading document: {e}")
            return None
    
    def download_document(self, blob_name):
        """Download a document from Azure Blob Storage.
        
        Args:
            blob_name: The name of the blob.
            
        Returns:
            The content of the document if successful, None otherwise.
        """
        try:
            logging.info(f"Downloading document from blob: {blob_name}")
            # Get a blob client
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Download the document
            download = blob_client.download_blob()
            
            # Return the content
            logging.info(f"Document downloaded successfully.")
            return download.readall()
        except Exception as e:
            logging.error(f"Error downloading document: {e}")
            return None
    
    def list_documents(self, prefix=None):
        """List documents in Azure Blob Storage.
        
        Args:
            prefix: Optional prefix to filter blobs.
            
        Returns:
            A list of blob names if successful, None otherwise.
        """
        try:
            logging.info(f"Listing documents with prefix: {prefix or 'None'}")
            # List the blobs
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            
            # Return the blob names
            blob_names = [blob.name for blob in blobs]
            logging.info(f"Found {len(blob_names)} documents.")
            return blob_names
        except Exception as e:
            logging.error(f"Error listing documents: {e}")
            return None
    
    def get_document_url(self, blob_name):
        """Get the URL of a document in Azure Blob Storage.
        
        Args:
            blob_name: The name of the blob.
            
        Returns:
            The URL of the document if successful, None otherwise.
        """
        try:
            logging.info(f"Getting URL for blob: {blob_name}")
            # Get a blob client
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Return the URL
            logging.info(f"URL: {blob_client.url}")
            return blob_client.url
        except Exception as e:
            logging.error(f"Error getting document URL: {e}")
            return None

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Configure logging for local testing
    logging.basicConfig(level=logging.INFO)
    try:
        # This requires environment variables to be set
        # Set them in your local environment for testing
        # export AZURE_STORAGE_ACCOUNT_NAME="your_storage_account_name"
        # export AZURE_STORAGE_CONTAINER_NAME="your_container_name"
        # Or use connection string:
        # export AZURE_STORAGE_CONNECTION_STRING="your_connection_string"
        
        print("Attempting to initialize Blob Storage Service...")
        blob_storage_service = BlobStorageService()
        
        # Example: List documents
        print("\nListing documents...")
        documents = blob_storage_service.list_documents()
        
        if documents:
            print(f"\nFound {len(documents)} documents:")
            for doc in documents:
                print(f"  Name: {doc}")
                print(f"  URL: {blob_storage_service.get_document_url(doc)}")
                print()
        else:
            print("\nNo documents found or error occurred.")
            
        # Example: Upload a test document
        print("\nUploading a test document...")
        test_content = b"This is a test document content."
        test_blob_name = "test_document.txt"
        upload_url = blob_storage_service.upload_document(
            test_content, 
            test_blob_name,
            content_type="text/plain"
        )
        
        if upload_url:
            print(f"Test document uploaded successfully.")
            print(f"URL: {upload_url}")
        else:
            print("Failed to upload test document.")
            
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure Azure Blob Storage environment variables (AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_CONTAINER_NAME) are set.")
    except Exception as e:
        print(f"An unexpected error occurred during example run: {e}")
