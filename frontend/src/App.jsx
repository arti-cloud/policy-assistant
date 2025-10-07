import React, { useState } from "react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
console.log("API_BASE:", API_BASE);

function App(){
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dark, setDark] = useState(false);

  async function ask(){
    setError(null);
    setLoading(true);
    setAnswer(null);
    try {
      const resp = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question: q, top_k: 5})
      });
      const json = await resp.json();
      if(!resp.ok) throw new Error(json.detail || "Server error");
      setAnswer(json);
    } catch(e){
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function clearAll(){
    setQ(""); setAnswer(null); setError(null);
  }

  function copyAnswer(){
    if(answer){
      navigator.clipboard.writeText(answer.answer);
      alert("Answer copied");
    }
  }

  return (
    <div className={dark? "app dark":"app"}>
      <header>
        <h1>Policy Assistant</h1>
        <button className="mode-toggle" onClick={()=>setDark(!dark)}>{dark? "Light":"Dark"}</button>
      </header>

      <main>
        <label className="search-label">
          <input
            value={q}
            onChange={(e)=>setQ(e.target.value)}
            placeholder="How many casual leaves do I get per year"
            onKeyDown={(e)=> e.key==="Enter" && ask()}
          />
        </label>

        <div className="btns">
          <button onClick={ask} disabled={loading || !q}>Ask</button>
          <button onClick={clearAll}>Clear</button>
          <button onClick={copyAnswer} disabled={!answer}>Copy Answer</button>
        </div>

        {loading && <div className="status">Loading...</div>}
        {error && <div className="error">{error}</div>}

        {answer && (
          <section className="results">
            <div className="answer-box">
              <h2>Answer</h2>
               {answer.answer ? (
      <p>{answer.answer}</p>
    ) : (
          <div className="escalation">
              <p>Can't find an answer?</p>
              <a href="mailto:hr@company.com?subject=Policy%20Assistance">Contact HR</a>
              {" • "}
              <a href="https://teams.microsoft.com/l/chat/0/0?users=hr@company.com">Open in Teams</a>
            </div>
    )}
  </div>

            <div className="citations">
              <h3>Citations</h3>

              {answer.citations && answer.citations.map((c, idx)=>(
                <div className="citation" key={idx}>
                  <div className="c-title">{c.doc_id}</div>

                  <div className="c-snippet">{c.snippet}</div>

                </div>
                
              ))}
              <small className="meta">Confidence: {answer.confidence} • {answer.disclaimer}</small>

            </div>
            <div className="escalation">
        <p>Can't find an answer?</p>
        <a href="mailto:hr@company.com?subject=Policy%20Assistance">Contact HR</a>
        {" • "}
        <a href="https://teams.microsoft.com/l/chat/0/0?users=hr@company.com">Open in Teams</a>
      </div>
          </section>
        )}
      </main>

      <footer>
        <small>Internal — Do not share externally</small>
      </footer>
    </div>
  );
}

export default App;
