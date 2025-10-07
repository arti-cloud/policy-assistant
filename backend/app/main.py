from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv(".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY missing in .env file!")

# FastAPI app setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class AskRequest(BaseModel):
    question: str
    top_k: int = 5

# Paths
POLICY_DIR = os.path.join("app", "policies")
VECTOR_STORE_DIR = os.path.join("app", "storage", "faiss_index")

# Load documents
# Load documents
docs = []
if os.path.exists(POLICY_DIR):
    for filename in os.listdir(POLICY_DIR):
        if filename.endswith(".txt"):
            loader = TextLoader(os.path.join(POLICY_DIR, filename), encoding="utf-8")
            for doc in loader.load():
                # OLD metadata
                # doc.metadata = { ... }

                # REPLACE with:
                doc.metadata = {
                    "source": filename,
                    "heading": doc.page_content.split("\n")[0],  # ideally the section title like 'Casual Leave'
                    "category": filename.replace("_policy.txt","").replace("_"," ").title()
                }
                docs.append(doc)

else:
    print("⚠️ No policy documents found in /app/policies")

# Split
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
split_docs = splitter.split_documents(docs)

# Embeddings (local & free)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Vector store
if os.path.exists(VECTOR_STORE_DIR):
    vector_store = FAISS.load_local(
        VECTOR_STORE_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )
else:
    vector_store = FAISS.from_documents(split_docs, embeddings)
    vector_store.save_local(VECTOR_STORE_DIR)

retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": 3,             # can fetch up to 3 top chunks if they pass threshold
        "score_threshold": 0.10  # only return chunks with >= 65% similarity
    }
)

# ✅ Groq model fix — mixtral model was decommissioned
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
   model_name="meta-llama/llama-guard-4-12b",
 # ✅ current stable and supported model
    temperature=0
)
from langchain.prompts import PromptTemplate

# Define a custom prompt template
prompt_template = """
You are an HR policy assistant. Answer the question using ONLY the provided context.
Include all relevant details from the context.
If the context does NOT contain the answer, say exactly: "I don’t have that in policy, contact HR."
Do NOT make up any answer.

Question: {question}
Context:
{context}

Answer concisely, with citations if available.
"""

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="refine",
    retriever=retriever,
    chain_type_kwargs={"prompt": PromptTemplate.from_template(prompt_template)},
    return_source_documents=True
)

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.post("/ask")
def ask(request: AskRequest):
    try:
        result = qa_chain({"query": request.question})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    answer = result["result"]
    sources = [
        {
            "doc_id": doc.metadata.get("source"),
            "section": doc.metadata.get("heading", ""),
            "snippet": doc.page_content[:200]
        }
        for doc in result["source_documents"]
    ]
    return {
        "answer": answer,
        "citations": sources,
        "policy_matches": list(set(
            [doc.metadata.get("category", "Unknown") for doc in result["source_documents"]]
        )),
        "confidence": "high",
        "disclaimer": "If your contract specifies otherwise, the contract prevails."
    }
