import os
import boto3
import streamlit as st
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────
AWS_REGION = os.getenv("AWS_REGION")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NUM_RESULTS = 5

# ─── PAGE SETUP ───────────────────────────────────────────
st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="📋"
)

st.title("📋 HR Policy Assistant")
st.write(
    "Ask any question about company HR policies. "
    "Answers are strictly based on the HR Policy document only."
)

# ─── BOTO3 CLIENT ─────────────────────────────────────────
@st.cache_resource
def get_bedrock_client():
    return boto3.client(
        service_name="bedrock-agent-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

# ─── INPUT ────────────────────────────────────────────────
question = st.text_input("Enter your question")

if st.button("Ask"):

    if not question.strip():
        st.error("Please enter a question.")

    else:
        with st.spinner("Searching HR policies..."):

            # STEP 1: Retrieve chunks from Knowledge Base
            bedrock = get_bedrock_client()

            kb_response = bedrock.retrieve(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                retrievalQuery={"text": question},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {
                        "numberOfResults": NUM_RESULTS
                    }
                }
            )

            chunks = []
            citations = []

            for item in kb_response.get("retrievalResults", []):
                text = item.get("content", {}).get("text", "")
                score = item.get("score", 0)
                location = item.get("location", {})

                if text:
                    chunks.append(text)
                    citations.append({
                        "text": text,
                        "score": score,
                        "location": location
                    })

            context = "\n\n".join(chunks)

        prompt = f"""You are an HR Policy Assistant for a company.

You have access to the company HR Policy document context below.

If the question is a greeting or casual conversation,
respond naturally and professionally without using the context.

If the question is about HR policies, answer STRICTLY using
only the context below. NEVER use your own knowledge.
If the answer is not in the context say:
"This information is not covered in the HR Policy document."
At the end mention which section the answer came from.

Context from HR Policy Document:
{context}

Question: {question}

Answer:"""

        with st.spinner("Generating answer..."):
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

        # STEP 5: Display answer
        st.subheader("Answer")
        st.write(response.text)

        if chunks:
            with st.expander("📑 Citations from HR Document"):
                for i, citation in enumerate(citations, 1):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(f"**[{i}]**")
                    with col2:
                        location = citation.get("location", {})
                        s3_uri = location.get(
                            "s3Location", {}
                        ).get("uri", "HR Policy Document")
                        st.caption(f"📄 Source: `{s3_uri}`")
                        st.write(citation["text"])
                    st.divider()