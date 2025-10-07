import time, os
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.llms import OpenAI
from app.config import settings
from app.schemas import AskResponse, Citation
import pickle

def load_vectorstore():
    # prefer Pinecone in prod; here we load FAISS fallback
    path = "storage/faiss_store.pkl"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    raise FileNotFoundError("No vectorstore found. Run ingestion.")

def ask_question(question: str, filters: dict = None, top_k: int = 5):
    start = time.time()
    vs = load_vectorstore()
    embed_model = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, openai_api_key=os.getenv("OPENAI_API_KEY"))
    # Retrieve
    docs_and_scores = vs.similarity_search_with_score(question, k=top_k)
    # Compose context snippets and citations
    citations = []
    combined_ctx = ""
    for doc, score in docs_and_scores:
        meta = getattr(doc, "metadata", {}) or {}
        doc_id = meta.get("doc_id", "unknown")
        section = meta.get("section", meta.get("chunk", "section"))
        snippet = doc.page_content[:1000]
        citations.append(Citation(doc_id=doc_id, section=section, snippet=snippet[:500], page=meta.get("page")))
        combined_ctx += "\n\n" + snippet
    # call LLM with guardrails
    llm = OpenAI(model=settings.LLM_MODEL, openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
    system_prompt = (
        "You are a precise HR policy assistant. Answer only from the provided policy context.\n"
        "- Cite at least one source section with doc id and section header.\n"
        "- If the answer is not clearly in the context, say 'I don't have that in policy' and suggest contacting HR.\n"
        "- Keep the answer under 200 words unless asked for details.\n        "
    )
    qa_input = f"Context:\n{combined_ctx}\n\nQuestion: {question}\n\nProvide a concise answer and include JSON: answer, policy_matches, confidence, disclaimer."
    resp_text = llm(f"{system_prompt}\n\n{qa_input}")
    time_ms = int((time.time()-start)*1000)
    # Basic parsing — in prod: validate with PydanticOutputParser or JSON schema.
    answer = resp_text.strip().split("\n")[0][:1000]
    policy_matches = list({c.doc_id for c in citations})
    out = AskResponse(
        answer=answer,
        citations=citations,
        policy_matches=policy_matches,
        confidence="medium",
        disclaimer="If your contract specifies otherwise, the contract prevails.",
        metadata={"latency_ms": time_ms, "retriever_k": top_k, "model": settings.LLM_MODEL}
    )
    return out
