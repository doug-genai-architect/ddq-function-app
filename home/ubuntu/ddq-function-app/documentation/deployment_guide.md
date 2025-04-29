# Azure Function Deployment Guide: DDQ Chat Function

This guide provides instructions for deploying the Python-based Azure Function app (`ddq-function-app`) to Azure.

## 1. Prerequisites

Before deploying, ensure you have the following:

*   **Azure Account:** An active Azure subscription.
*   **Azure CLI:** Installed and configured. ([Installation Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
*   **Azure Functions Core Tools:** (Optional but recommended for local testing and some deployment methods). Version 4.x is recommended. ([Installation Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=v4%2Cwindows%2Cpython%2Cportal%2Cbash#install-the-azure-functions-core-tools))
*   **Python:** Version 3.9 or later (as supported by Azure Functions Python runtime).
*   **Project Code:** The `ddq-function-app` directory containing the function code, `host.json`, `requirements.txt` (to be generated), and `local.settings.json`.
*   **Required Azure Resources:**
    *   Azure Function App (Consumption or Premium plan, Python runtime)
    *   Azure Storage Account (for Function App and Blob Storage)
    *   Azure OpenAI Service (with the specified model deployed)
    *   Azure AI Search Service (configured with index and API key)
    *   Application Insights (Optional, for monitoring)

## 2. Prepare for Deployment

### 2.1. Generate `requirements.txt`

Navigate to the project root directory (`/home/ubuntu/ddq-function-app`) in your terminal and activate the virtual environment. Then, generate the `requirements.txt` file:

```bash
source venv/bin/activate
pip freeze > requirements.txt
deactivate
```

This file lists all the Python packages required by the function.

### 2.2. Review `local.settings.json`

Ensure all placeholder values in `local.settings.json` (like API keys, service names, etc.) are noted. These will need to be configured as Application Settings in the Azure Function App.

## 3. Deployment Methods

You can deploy the function app using several methods. Choose one:

### Method A: Zip Deployment (Recommended for CI/CD or CLI)

This method involves packaging the project code into a zip file and deploying it.

1.  **Create Zip File:** Navigate *inside* the `/home/ubuntu/ddq-function-app` directory. Create a zip file containing all project files and folders *except* the `venv` directory.

    ```bash
    # Ensure you are in /home/ubuntu/ddq-function-app
    zip -r ../ddq-function-app.zip . -x "venv/*" ".git/*" "__pycache__/*" ".vscode/*"
    ```
    *(Adjust the zip command based on your OS and desired exclusions)*

2.  **Deploy using Azure CLI:**

    ```bash
    az login # Log in to your Azure account
    az account set --subscription "YOUR_SUBSCRIPTION_ID"

    az functionapp deployment source config-zip -g YOUR_RESOURCE_GROUP_NAME -n YOUR_FUNCTION_APP_NAME --src ../ddq-function-app.zip
    ```
    Replace `YOUR_RESOURCE_GROUP_NAME` and `YOUR_FUNCTION_APP_NAME` with your actual Azure resource names.

### Method B: Visual Studio Code Extension

1.  **Install Extensions:** Install the [Azure Account](https://marketplace.visualstudio.com/items?itemName=ms-vscode.azure-account) and [Azure Functions](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions) extensions in VS Code.
2.  **Sign in to Azure:** Use the Azure Account extension to sign in.
3.  **Open Project:** Open the `/home/ubuntu/ddq-function-app` folder in VS Code.
4.  **Deploy:**
    *   Go to the Azure view in VS Code.
    *   Find the Azure Functions section.
    *   Click the "Deploy to Function App..." button (upward arrow icon).
    *   Follow the prompts:
        *   Select the current workspace folder.
        *   Select your Azure subscription.
        *   Choose "+ Create New Function App in Azure..." or select an existing one.
        *   Provide a globally unique name for the new Function App.
        *   Select the Python runtime stack (e.g., Python 3.10).
        *   Select an Azure region.
    *   The extension will package and deploy the code.

## 4. Configure Application Settings

After deployment, you *must* configure the Application Settings in the Azure portal for your Function App. These settings correspond to the values in your `local.settings.json` file.

1.  Navigate to your Function App in the Azure portal.
2.  Go to **Settings -> Configuration**.
3.  Under **Application settings**, click **+ New application setting** for each required setting:
    *   `AZURE_TENANT_ID`
    *   `AZURE_CLIENT_ID` (If using service principal for SharePoint/Graph)
    *   `AZURE_CLIENT_SECRET` (If using service principal for SharePoint/Graph)
    *   `AZURE_OAI_ENDPOINT`
    *   `AZURE_OAI_MODEL_NAME`
    *   `AZURE_SEARCH_SERVICE_NAME`
    *   `AZURE_SEARCH_INDEX_NAME`
    *   `AZURE_SEARCH_API_KEY`
    *   `AZURE_STORAGE_ACCOUNT_NAME` (Or `AzureWebJobsStorage` connection string if different)
    *   `AZURE_STORAGE_CONTAINER_NAME`
    *   `SHAREPOINT_SITE_URL` (If applicable)
    *   `SHAREPOINT_SITE_NAME` (If applicable)
    *   `SHAREPOINT_DOCUMENT_LIBRARY` (If applicable)
    *   `AZURE_MONITOR_CONNECTION_STRING` (Optional, for Application Insights)
    *   `AzureWebJobsStorage` (Usually configured automatically, but verify it points to a valid storage account connection string)
4.  **Important:** If using `DefaultAzureCredential` (as implemented in `openai_service.py` and `blob_storage_service.py`), ensure the Function App has a Managed Identity assigned (System-assigned or User-assigned) and that this identity has the necessary RBAC roles granted on the target Azure OpenAI and Azure Storage resources (e.g., "Cognitive Services User", "Storage Blob Data Contributor"). If using API keys or connection strings, ensure those settings are correctly configured.
5.  Click **Save** after adding/updating settings. The Function App will restart.

## 5. Verification

1.  **Check Deployment Status:** Verify the deployment completed successfully in the Azure portal (Deployment Center) or via the CLI/VS Code output.
2.  **Get Function URL:**
    *   In the Azure portal, navigate to your Function App -> Functions -> DdqChatFunction.
    *   Click **Get Function Url**.
    *   Since the `authLevel` is `anonymous`, no code is needed in the URL.
3.  **Test with HTTP Client (e.g., Postman, curl):**
    *   Send a `POST` request to the Function URL.
    *   Set the `Content-Type` header to `application/json`.
    *   Provide a JSON body like:
        ```json
        {
          "prompt": "What is the fund\'s investment strategy?"
        }
        ```
    *   Check the response. You should receive a JSON payload with `ai_response`, `document_url`, and `sources`.
    *   Verify the `document_url` points to a valid DOCX file in your Blob Storage container.
4.  **Check Logs:** Monitor the Function App's logs (Monitor -> Logs or Application Insights) for any errors during execution.

Your Azure Function should now be deployed and ready to be triggered by your custom GPT.
