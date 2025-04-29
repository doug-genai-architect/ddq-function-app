# DDQ GPT Azure Function App

An **Azure Functions** application that leverages **OpenAI**, **Azure Cognitive Search**, and **Azure Blob Storage** to provide document-driven question-and-answer (DDQ) capabilities.  The function ingests corporate documents, indexes them for semantic search, and delivers grounded, reference-backed answers through a simple REST endpoint.

---

## ✨ Key Features

| Capability | Description |
| ----------- | ----------- |
| 📚 Document-Grounded QA | Answers are generated using enterprise documents retrieved from Azure Cognitive Search, ensuring responses are verifiable and relevant. |
| 🔍 Hybrid Search | Combines vector and keyword search for high-precision context retrieval. |
| 🧠 OpenAI Integration | Uses OpenAI Chat Completion API (GPT) to create concise, context-aware answers. |
| 📝 Automatic Source Citations | Each answer includes the document sources and snippets that were used to build the response. |
| 📄 Dynamic DOCX Generation | Optionally generates a well-formatted Word document containing the answer and citations, stored in Azure Blob Storage. |
| 🛡️ Production-Grade Telemetry | Extensive logging and metric collection hooks are included for Application Insights or any observability platform. |

---

## 🏗️ Solution Architecture

```
(Client) ──► HTTP Request ──► Azure Function (Python)
                                │
                                ├─► Azure Cognitive Search ──► (Document Index)
                                │
                                ├─► OpenAI (Chat Completion)
                                │
                                └─► Azure Blob Storage (Generated Docs)
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
# python 3.10+
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Populate **local.settings.json** or environment variables with the following keys:

| Variable | Purpose |
| -------- | ------- |
| `OPENAI_API_KEY` | Your OpenAI API key. |
| `OPENAI_MODEL` | (Optional) OpenAI model to use (e.g., `gpt-4o`). Defaults to `gpt-4o`. |
| `OPENAI_ORGANIZATION` | (Optional) Your OpenAI organization ID. |
| `AZURE_SEARCH_SERVICE_NAME` | Name of the Cognitive Search service. |
| `AZURE_SEARCH_INDEX_NAME` | Target index containing your documents. |
| `AZURE_SEARCH_API_KEY` | Admin/query key for search. |
| `AZURE_STORAGE_ACCOUNT_NAME` | Blob account for generated documents. |
| `AZURE_STORAGE_CONTAINER_NAME` | Container where DOCX files are uploaded. |
| *(optional)* `FUNCTION_API_KEY` | Shared key if you want to secure the endpoint. |

### 3. Run Locally

```bash
func start
```
The function listens on `http://localhost:7071/api/ddq-chat` (see *function.json*).

### 4. Invoke Sample Request

```bash
curl -X POST http://localhost:7071/api/ddq-chat \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "What are the main steps to deploy this solution?",
           "history": [],
           "template": "default"
         }'
```

---

## 🔧 Deployment (Azure)

1. **Create Resources**
   * Azure Storage Account & Container
   * Azure Cognitive Search + Index (vector-enabled)
   * OpenAI API Key (obtain from OpenAI)
2. **Publish Function App**
   ```bash
   func azure functionapp publish <YOUR_FUNCTION_APP_NAME> --python
   ```
3. **Configure App Settings** with the same environment variables shown above.

Detailed instructions are available in the `documentation/deployment_guide.md`.

---

## 📑 API Contract

| Method | URL | Description |
| ------ | --- | ----------- |
| POST | `/api/ddq-chat` | Returns an answer generated from enterprise documents. |

### Request Body
```json
{
  "prompt": "<Your question>",
  "history": [  // optional conversation history
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "template": "default" // optional document template name
}
```

### Response Body
```json
{
  "answer": "<AI response>",
  "sources": ["/docs/Policy.pdf", "/docs/Handbook.pdf"],
  "docx_url": "https://<storage>.blob.core.windows.net/generated-docs/<file>.docx"
}
```

---

## 📝 Contributing

Issues and pull requests are welcome!  For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details. 