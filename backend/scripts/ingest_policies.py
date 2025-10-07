from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os

load_dotenv()

# -----------------------------
# Paths
# -----------------------------
POLICY_DIR = os.path.join(os.path.dirname(__file__), "..", "policies")
VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "faiss_index")

# -----------------------------
# Load and process docs
# -----------------------------
docs = []
for filename in os.listdir(POLICY_DIR):
    if filename.endswith(".txt"):
        loader = TextLoader(os.path.join(POLICY_DIR, filename), encoding="utf-8")
        for doc in loader.load():
            doc.metadata = {"source": filename, "heading": doc.page_content.split("\n")[0]}
            docs.append(doc)

# -----------------------------
# Split into chunks
# -----------------------------
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_docs = splitter.split_documents(docs)

# -----------------------------
# Use fake embeddings for free testing
# -----------------------------
from langchain_community.embeddings import SentenceTransformerEmbeddings

embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = FAISS.from_documents(split_docs, embeddings)

# Save index
vector_store.save_local(VECTOR_STORE_DIR)
print("Vector store created at", VECTOR_STORE_DIR)
