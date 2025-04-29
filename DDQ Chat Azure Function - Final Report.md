# DDQ Chat Azure Function - Final Report

## Project Overview

This project delivers an Azure Function that processes Due Diligence Questionnaire (DDQ) questions using Azure OpenAI, Azure AI Search, and Azure Blob Storage. The function is designed to be triggered by a custom GPT, providing accurate answers based on the organization's documents and returning both a brief response and a link to a generated DOCX document.

## Key Features Implemented

1. **HTTP-Triggered Azure Function**
   - Anonymous authentication for public access by the custom GPT
   - JSON request/response format for seamless integration
   - Robust error handling and logging

2. **Azure OpenAI Integration**
   - Connected to the specified endpoint: `https://bfija-m83d9xpw-eastus2.services.ai.azure.com/models`
   - Using the specified model: `o4-mini-custom-gpt`
   - Implemented with DefaultAzureCredential for secure authentication

3. **Azure AI Search Integration**
   - Semantic search capabilities for better relevance
   - Extraction of content snippets and source metadata
   - Configurable result count and filtering

4. **Document Generation**
   - Professional DOCX document creation using python-docx
   - Structured format with question, answer, and sources sections
   - Automatic upload to Azure Blob Storage

5. **System Prompt**
   - Tailored instructions for the AI model
   - Guidelines for source citation and verbatim answers
   - Context-specific examples and workflow explanation

## Project Structure

The project is organized into the following components:

### Azure Function
- `DdqChatFunction/__init__.py` - Main function code
- `DdqChatFunction/function.json` - HTTP trigger configuration

### Shared Code Modules
- `shared_code/openai_service.py` - Azure OpenAI integration
- `shared_code/search_service.py` - Azure AI Search integration
- `shared_code/blob_storage_service.py` - Azure Blob Storage integration
- `shared_code/document_generator.py` - DOCX document creation

### Configuration
- `host.json` - Function host configuration
- `local.settings.json` - Environment variables and settings
- `system_prompt.txt` - Instructions for the AI model

### Documentation
- `documentation/deployment_guide.md` - Instructions for Azure deployment
- `documentation/security_guide.md` - Security implementation details
- `documentation/implementation_guide.md` - Code structure and workflow explanation

## Workflow

1. The custom GPT sends an HTTP POST request to the Azure Function with a JSON body containing the DDQ question.
2. The function searches for relevant content using Azure AI Search.
3. The function sends the question and search results to Azure OpenAI to generate an answer.
4. The function creates a DOCX document with the question, answer, and sources.
5. The function uploads the document to Azure Blob Storage.
6. The function returns a JSON response with the answer text, document URL, and sources.

## Implementation Details

### Azure Function Configuration

The function is configured with anonymous authentication as requested, making it publicly accessible for the custom GPT. It accepts HTTP POST requests and returns JSON responses.

### Azure OpenAI Integration

The OpenAI service is implemented to use the specified endpoint and model. It uses DefaultAzureCredential for authentication, which supports Managed Identity when deployed to Azure.

### Azure AI Search Integration

The search service is implemented to find relevant document snippets based on the DDQ question. It supports semantic search for better relevance and extracts content and metadata from the search results.

### Document Generation

The document generator creates professionally formatted DOCX files with sections for the question, answer, and sources. It uses the python-docx library and uploads the documents to Azure Blob Storage.

### System Prompt

The system prompt provides detailed instructions to the AI model on how to process DDQ questions. It emphasizes using only the provided context, citing sources, and maintaining a professional tone.

## Security Considerations

The security guide provides detailed recommendations for securing the Azure Function and its dependencies:

1. **Authentication and Authorization**
   - Function access control options
   - Azure service authentication using Managed Identity

2. **Data Protection**
   - Data in transit (HTTPS)
   - Data at rest (Blob Storage encryption)
   - Sensitive information handling

3. **Monitoring and Logging**
   - Application Insights integration
   - Log sanitization and retention

4. **Network Security**
   - Virtual Network integration options
   - Private Endpoints for Azure services

5. **Custom GPT Integration Security**
   - Request validation
   - Response security

## Deployment Instructions

The deployment guide provides step-by-step instructions for deploying the Azure Function to Azure:

1. **Prerequisites**
   - Azure account and required resources
   - Azure CLI or VS Code with Azure Functions extension

2. **Preparation**
   - Generating requirements.txt
   - Reviewing configuration settings

3. **Deployment Methods**
   - Zip deployment (CLI)
   - Visual Studio Code extension

4. **Configuration**
   - Setting up Application Settings
   - Configuring Managed Identity

5. **Verification**
   - Testing the deployed function
   - Monitoring logs

## Next Steps

To fully operationalize this solution:

1. **Deploy to Azure** following the deployment guide
2. **Configure environment variables** with actual service credentials
3. **Set up Azure AI Search** to index the provided documents (PPMs, ESG reports, etc.)
4. **Test with actual DDQ questions** to verify functionality
5. **Integrate with the custom GPT** by providing the function URL
6. **Implement monitoring** for performance and usage tracking

## Conclusion

This Azure Function provides a serverless solution for processing DDQ questions using Azure OpenAI and Azure AI Search. It delivers accurate, source-cited answers in both text format and as professionally formatted DOCX documents. The solution is designed to be easily deployed to Azure and integrated with a custom GPT.

The comprehensive documentation provides all the information needed to understand, deploy, and secure the solution. The modular code structure makes it easy to maintain and extend the functionality as needed.

All deliverables have been packaged in the `ddq_function_app_deliverables.zip` file for easy access and deployment.
