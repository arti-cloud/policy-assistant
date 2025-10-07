from app.retriever import ask_question
def test_ask_returns_schema():
    resp = ask_question("Test question about leave", top_k=2)
    assert hasattr(resp, "answer")
    assert hasattr(resp, "citations")
    assert isinstance(resp.citations, list)
