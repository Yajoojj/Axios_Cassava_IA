import React, { useMemo, useState } from "react";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/predict";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [imageURL, setImageURL] = useState(null);
  const [compare, setCompare] = useState(false);

  const infectionPercent = useMemo(() => {
    if (!result) return "0.00";
    return (result.probability * 100).toFixed(2);
  }, [result]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) return;

    setLoading(true);
    setResult(null);
    setError("");

    const formData = new FormData();
    formData.append("image", file);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Erro HTTP ${response.status}`);
      }

      setResult(data);
    } catch (requestError) {
      setError(requestError.message || "Nao foi possivel processar a imagem.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event) => {
    const selected = event.target.files[0] || null;
    setFile(selected);
    setResult(null);
    setError("");
    setCompare(false);

    if (imageURL) {
      URL.revokeObjectURL(imageURL);
    }

    setImageURL(selected ? URL.createObjectURL(selected) : null);
  };

  return (
    <main className="app-shell">
      <section className="intro">
        <p className="eyebrow">Axios Cassava IA</p>
        <h1>Deteccao de bacteriose em folhas de mandioca</h1>
        <p>
          Envie uma foto da folha para classificar o risco de infeccao, estimar
          severidade e visualizar o mapa das areas suspeitas.
        </p>
      </section>

      <section className="analysis-panel" aria-label="Analise da folha">
        <form onSubmit={handleSubmit} className="upload-form">
          <label htmlFor="leaf-image">Imagem da folha</label>
          <input
            id="leaf-image"
            type="file"
            accept="image/png,image/jpeg"
            onChange={handleFileChange}
          />
          <button type="submit" disabled={!file || loading}>
            {loading ? "Processando..." : "Analisar"}
          </button>
        </form>

        {error && <p className="status error">{error}</p>}
        {loading && <p className="status">Processando imagem com a IA...</p>}

        {result && (
          <div className="results">
            <div className="result-grid">
              <article>
                <span>Classe prevista</span>
                <strong>{result.class}</strong>
              </article>
              <article>
                <span>Probabilidade</span>
                <strong>{infectionPercent}%</strong>
              </article>
              <article>
                <span>Area infectada</span>
                <strong>{(result.ratio * 100).toFixed(2)}%</strong>
              </article>
              <article>
                <span>Severidade</span>
                <strong>{result.severity}</strong>
              </article>
            </div>

            {result.overlay && (
              <div className="image-results">
                <div className="image-toolbar">
                  <h2>Mapa de infeccao</h2>
                  {imageURL && (
                    <button type="button" onClick={() => setCompare((value) => !value)}>
                      {compare ? "Ver mapa" : "Comparar"}
                    </button>
                  )}
                </div>

                <div className={compare ? "comparison two-columns" : "comparison"}>
                  {compare && imageURL && (
                    <figure>
                      <img src={imageURL} alt="Folha original enviada" />
                      <figcaption>Original</figcaption>
                    </figure>
                  )}
                  <figure>
                    <img src={result.overlay} alt="Mapa de infeccao gerado pela IA" />
                    <figcaption>Sobreposicao</figcaption>
                  </figure>
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
