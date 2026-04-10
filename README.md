# Enterprise Knowledge Base Q&A System
### Built with Amazon Bedrock Knowledge Bases (RAG) + Gemini 2.5 Flash

![Python](https://img.shields.io/badge/Python-3.14-blue)
![AWS](https://img.shields.io/badge/AWS-Bedrock-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0-red)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-green)

---

## 📌 Project Overview

A production-ready **Retrieval-Augmented Generation (RAG)** Q&A application that enables employees to ask natural language questions about company HR policies and receive accurate, citation-backed responses.

Traditional keyword search fails to understand meaning. This system combines **Amazon Bedrock Knowledge Bases** for semantic retrieval with **Gemini 2.5 Flash** for intelligent answer generation — grounded strictly in the company document.

---

## 🏗️ Architecture

```
User Question
      ↓
Streamlit UI (EC2)
      ↓
Amazon Bedrock Knowledge Base
      ↓ retrieve()
Top 5 Relevant Chunks (Vector Search)
      ↓
Gemini 2.5 Flash (Generation)
      ↓
Answer + Citations
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **Document Storage** | Amazon S3 |
| **Vector Embeddings** | Amazon Titan Text Embeddings V2 |
| **Knowledge Base** | Amazon Bedrock Knowledge Bases |
| **Vector Store** | Amazon S3 Vectors |
| **LLM Generation** | Gemini 2.5 Flash |
| **AWS SDK** | boto3 |
| **Deployment** | AWS EC2 (eu-north-1) |

---

## ✨ Features

- 💬 **Chat Interface** — full conversation history per session
- 📑 **Citations** — shows exact source chunks from the document
- 📊 **Confidence Indicator** — High / Medium / Low based on chunks retrieved
- 🤖 **Dual Mode** — handles casual conversation + strict HR policy questions
- 📋 **Sample Questions** — clickable questions in sidebar
- 🔒 **Strict Grounding** — Gemini only answers from retrieved context

---

## 📁 Project Structure

```
enterprise-rag-project/
    ├── simple_app.py       # Main Streamlit application
    ├── .env.example        # Environment variables template
    ├── .gitignore          # Git ignore rules
    └── README.md           # Project documentation
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8+
- AWS Account with Bedrock access
- Google Gemini API key

### 1. Clone the repository
```bash
git clone https://github.com/Professional03/enterprise-rag-project.git
cd enterprise-rag-project
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install boto3 streamlit python-dotenv google-genai
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

Fill in your values in `.env`:
```
AWS_REGION=eu-north-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_key
KNOWLEDGE_BASE_ID=your_knowledge_base_id
```

### 5. Run the app
```bash
streamlit run simple_app.py
```

---

## ☁️ AWS Infrastructure Setup

### Step 1 — S3 Bucket
- Create an S3 bucket in `eu-north-1`
- Upload your company document (PDF)

### Step 2 — IAM Role
- Create role `bedrockRAG` with:
  - `AmazonS3FullAccess`
  - `AmazonBedrockFullAccess`

### Step 3 — Bedrock Knowledge Base
- Create Knowledge Base in Amazon Bedrock
- Data source: your S3 bucket
- Embedding model: Titan Text Embeddings V2
- Vector store: Amazon S3 Vectors
- Sync the data source

### Step 4 — EC2 Deployment
- Launch `t2.micro` Ubuntu instance
- Attach IAM role with Bedrock access
- Open port `8501` in security group
- Run app with `nohup` for persistence

---

## 🚀 Deployment on EC2

```bash
# SSH into EC2
ssh -i "key.pem" ubuntu@your-ec2-public-ip

# Setup
cd ~/rag-project
source venv/bin/activate

# Run persistently
nohup streamlit run simple_app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 &
```

Access at: `http://your-ec2-public-ip:8501`

---

## 💡 How RAG Works in This Project

```
1. INDEXING (done once during KB sync)
   PDF → Text Extraction → Chunking →
   Titan Embeddings → Vectors stored in S3

2. RETRIEVAL (every query)
   User Question → Convert to vector →
   Find 5 most similar chunks → Return text

3. GENERATION (every query)
   Context chunks + Question → Gemini →
   Grounded answer with citations
```

---

## 📝 Environment Variables

| Variable | Description |
|---|---|
| `AWS_REGION` | AWS region (eu-north-1) |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `KNOWLEDGE_BASE_ID` | Bedrock Knowledge Base ID |

---

## ⚠️ Important Notes

- Never commit `.env` file to GitHub
- Stop EC2 instance when not in use to avoid charges
- Re-sync Knowledge Base when documents are updated

---

## 👨‍💻 Author

**Professional03**
- GitHub: [@Professional03](https://github.com/Professional03)