import os
import boto3
import streamlit as st
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────
AWS_REGION = os.getenv("AWS_REGION")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NUM_RESULTS = 5

# ─── PAGE SETUP ───────────────────────────────────────────
st.set_page_config(
    page_title="HR Policy Assistant",
    page_icon="📋",
    layout="wide"
)

# ─── SESSION STATE (chat history) ─────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ─── BOTO3 CLIENT ─────────────────────────────────────────
@st.cache_resource
def get_bedrock_client():
    return boto3.client(
        service_name="bedrock-agent-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://img.icons8.com/color/96/documents.png", width=60)
    st.title("HR Policy Assistant")
    st.divider()

    # Document info
    st.markdown("### 📄 Document")
    st.info(
        "**HR Policy & Procedure Template**\n\n"
        "Community Foundations of Canada\n\n"
        "53 pages · 8 sections"
    )

    st.divider()

    # Sample questions
    st.markdown("### 💡 Sample Questions")
    sample_questions = [
        "How many sick days do employees get?",
        "What is the vacation policy?",
        "What is the dress code policy?",
        "How does the hiring process work?",
        "What are the overtime rules?",
        "What is the harassment policy?",
        "How are performance reviews conducted?",
        "What is the resignation procedure?",
    ]

    for q in sample_questions:
        if st.button(q, use_container_width=True):
            st.session_state.prefill_question = q

    st.divider()

    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # About section
    st.markdown("### ℹ️ About")
    st.caption(
        "This assistant only answers questions "
        "based on the HR Policy document. "
        "It cannot answer general questions "
        "outside this document."
    )
    st.caption("Built with Amazon Bedrock + Gemini 2.5 Flash")

# ══════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════
st.title("📋 HR Policy Assistant")
st.caption(
    "Ask questions about company HR policies. "
    "All answers are strictly based on the HR Policy document only."
)
st.divider()

# ─── DISPLAY CHAT HISTORY ─────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

        # Show citations only for HR answers
        if message["role"] == "assistant" and "citations" in message:
            if message["citations"]:
                with st.expander("📑 Citations from HR Document"):
                    for i, citation in enumerate(message["citations"], 1):
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

# ─── QUESTION INPUT ───────────────────────────────────────
prefill = st.session_state.get("prefill_question", "")
if prefill:
    del st.session_state["prefill_question"]

question = st.chat_input("Ask a question about HR policies...")

if prefill and not question:
    question = prefill

# ══════════════════════════════════════════════════════════
# PROCESS QUESTION
# ══════════════════════════════════════════════════════════
if question:

    # Detect if question is conversational or HR related
    conversational_keywords = [
        "hi", "hello", "hey", "how are you", "thank you",
        "thanks", "bye", "goodbye", "who are you", "what are you",
        "good morning", "good evening", "good afternoon", "ok",
        "okay", "sure", "great", "awesome", "cool", "nice",
        "what can you do", "help me", "what do you do"
    ]
    is_conversational = any(
        kw in question.lower()
        for kw in conversational_keywords
    )

    # Add user message to chat history
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    # Display user message
    with st.chat_message("user"):
        st.write(question)

    # Display assistant response
    with st.chat_message("assistant"):

        # ── CONVERSATIONAL MODE ──────────────────────────
        if is_conversational:
            with st.spinner("Thinking..."):
                client = genai.Client(api_key=GEMINI_API_KEY)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"""You are a friendly HR Policy Assistant 
for a company. Respond naturally to this greeting 
or casual message. Keep it short, warm and professional.
Let the user know you can help with HR policy questions.

Message: {question}

Response:"""
                )
            answer = response.text
            st.write(answer)

            # Save to history without citations
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "citations": []
            })

        # ── HR POLICY MODE ───────────────────────────────
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

                # STEP 2: Extract chunks + citations
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

            # STEP 3: Nothing retrieved
            if not chunks:
                answer = (
                    "I couldn't find any relevant information "
                    "in the HR Policy document for your question. "
                    "Please try rephrasing or ask about a "
                    "different HR policy topic."
                )
                st.warning(answer)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "citations": []
                })

            else:
                # STEP 4: Build strict HR prompt
                prompt = f"""You are a strict HR Policy assistant.

STRICT RULES:
1. Answer ONLY using the context provided below
2. NEVER use your own knowledge or training data
3. If the answer is not in the context, say exactly:
   "This information is not covered in the HR Policy document."
4. Always be specific and quote relevant details from context
5. Keep answers clear and professional
6. At the end mention which section the answer came from

Context from HR Policy Document:
{context}

Employee Question: {question}

Answer (based strictly on the HR Policy document):"""

                # STEP 5: Send to Gemini
                with st.spinner("Generating answer..."):
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )

                answer = response.text

                # STEP 6: Display answer
                st.write(answer)

                # STEP 7: Confidence indicator
                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(
                        f"📊 **Confidence:** "
                        f"{'🟢 High' if len(chunks) >= 4 else '🟡 Medium' if len(chunks) >= 2 else '🔴 Low'}"
                    )
                with col2:
                    st.caption(
                        f"📄 **Sections found:** {len(chunks)}"
                    )

                # STEP 8: Citations
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

                # STEP 9: Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "citations": citations
                })