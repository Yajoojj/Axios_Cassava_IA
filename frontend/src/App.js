import React, { useState } from "react";

// URL da API. Altere para o endereço do seu backend caso não seja localhost.
const API_URL = "http://localhost:8000/predict";

/**
 * Componente principal da aplicação.
 *
 * Permite ao usuário selecionar uma imagem de folha de mandioca, enviar para o
 * backend e visualizar a probabilidade de infecção, a classe prevista, a
 * proporção de área infectada e a severidade da doença. Também exibe a
 * sobreposição de cores retornada pela API.
 */
function App() {
  const [file, setFile] = useState(null); // arquivo selecionado pelo usuário
  const [result, setResult] = useState(null); // resultados retornados pela API
  const [loading, setLoading] = useState(false); // estado de carregamento
  // URL da imagem original para exibição
  const [imageURL, setImageURL] = useState(null);
  // Estado para controlar se devemos mostrar a comparação lado a lado
  const [compare, setCompare] = useState(false);

  /**
   * Função disparada ao enviar o formulário.
   * Cria um FormData com o arquivo e faz a requisição POST para a API.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("image", file);
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(`Erro na requisição: ${response.statusText}`);
      }
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Erro ao enviar imagem:", error);
      alert("Ocorreu um erro ao processar a imagem. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  /**
   * Atualiza o arquivo selecionado e gera uma URL local para pré-visualização.
   * Isso permite exibir a imagem original ao lado da sobreposição retornada
   * pelo backend. O URL é liberado ao selecionar uma nova imagem.
   */
  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    setFile(selected);
    setResult(null);
    if (selected) {
      const url = URL.createObjectURL(selected);
      setImageURL(url);
    } else {
      setImageURL(null);
    }
  };

  return (
    <div className="container py-5">
      <h1 className="text-center mb-4 display-6">
        Detecção de Bacteriose em Mandioca
      </h1>
      <div className="card shadow-sm mx-auto" style={{ maxWidth: "500px" }}>
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label">Escolha uma imagem de folha:</label>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="form-control"
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary w-100"
              disabled={!file || loading}
            >
              {loading ? "Processando..." : "Enviar"}
            </button>
            {loading && (
              <div className="d-flex justify-content-center my-3">
                <div className="spinner-border" role="status">
                  <span className="visually-hidden">Processando...</span>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>
      {result && (
        <div className="card mt-4 shadow-sm mx-auto" style={{ maxWidth: "900px" }}>
          <div className="card-body">
            <h2 className="h5 mb-3">Resultados</h2>
            <p>
              <strong>Probabilidade de infecção:</strong> {(
                result.probability * 100
              ).toFixed(2)}%
            </p>
            <p>
              <strong>Classe prevista:</strong> {result.class}
            </p>
            <p>
              <strong>Proporção de área infectada:</strong> {(
                result.ratio * 100
              ).toFixed(2)}%
            </p>
            <p>
              <strong>Severidade:</strong> {result.severity}
            </p>
            {/* Botão para alternar modo de comparação */}
            {result.overlay && (
              <div className="mt-3">
                <button
                  type="button"
                  className="btn btn-secondary mb-3"
                  onClick={() => setCompare(!compare)}
                >
                  {compare ? "Mostrar apenas sobreposição" : "Comparar com imagem original"}
                </button>
                {/* Se compare estiver ativo, mostra as duas imagens lado a lado */}
                {compare && imageURL ? (
                  <div className="row g-3">
                    <div className="col-md-6">
                      <h3 className="h6">Imagem original</h3>
                      <img
                        src={imageURL}
                        alt="Imagem original"
                        className="img-fluid rounded shadow"
                      />
                    </div>
                    <div className="col-md-6">
                      <h3 className="h6">Mapa de infecção</h3>
                      <img
                        src={result.overlay}
                        alt="Mapa de infecção"
                        className="img-fluid rounded shadow"
                      />
                    </div>
                  </div>
                ) : (
                  // Caso contrário, mostra somente a sobreposição
                  <div className="mt-3">
                    <h3 className="h6">Mapa de infecção</h3>
                    <img
                      src={result.overlay}
                      alt="Mapa de infecção"
                      className="img-fluid rounded shadow"
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
