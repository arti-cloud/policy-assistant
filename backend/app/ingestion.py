import os
from pathlib import Path
from langchain.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import pickle
from app.config import settings
from app.utils import sectionize_text
from tqdm import tqdm

def load_doc(path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix in [".docx", ".doc"]:
        loader = UnstructuredWordDocumentLoader(str(path))
    else:
        loader = TextLoader(str(path), encoding="utf8")
    return loader.load()

def ingest_file(path, metadata=None):
    docs = load_doc(path)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    texts = splitter.split_documents(docs)
    embed_model = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, openai_api_key=os.getenv("OPENAI_API_KEY"))
    if settings.PINECONE_USE and settings.PINECONE_API_KEY:
        # Insert into Pinecone (showing pseudo code — implement in production)
        import pinecone
        pinecone.init(api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENV)
        index = pinecone.Index(settings.VECTORSTORE_NAME)
        # create vectors and upsert here...
        # For quick local dev fallback to FAISS, else implement pinecone upsert logic.
    else:
        faiss_store = FAISS.from_documents(texts, embed_model)
        persist_path = Path("storage/faiss_store.pkl")
        with open(persist_path, "wb") as f:
            pickle.dump(faiss_store, f)
    return len(texts)
