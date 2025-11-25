# Frontend – Cassava Blight Detection

Esta pasta contém a aplicação **React** responsável por fornecer uma interface gráfica
em português para o sistema de detecção de bacteriose em folhas de mandioca.

## 📦 Instalação

1. Navegue até o diretório `frontend`:

   ```bash
   cd frontend
   ```

2. Instale as dependências do Node:

   ```bash
   npm install
   ```

## 🚀 Execução

Inicie o servidor de desenvolvimento com:

```bash
npm start
```

O comando abrirá automaticamente o navegador padrão no endereço
`http://localhost:3000`. Se a porta 3000 já estiver em uso, o
npm perguntará se deseja usar outra porta.

## 🔗 Configurando o endpoint da API

Por padrão, o frontend faz requisições para `http://localhost:8000/predict`.
Caso o backend esteja hospedado em um endereço diferente, edite a
constante `API_URL` definida no início de `src/App.js` para apontar para
o novo endereço.

## 🧾 Descrição da interface

A aplicação exibe:

- Um campo para upload de uma imagem de folha (`input type="file"`)
- Um botão **Enviar** que envia a imagem para o backend
- Uma área de resultados mostrando:
  - **Probabilidade de infecção** (em porcentagem)
  - **Classe prevista** (Saudável ou Infectado)
  - **Proporção de área infectada**
  - **Severidade** da doença
- Um **mapa de infecção** em que a parte saudável da folha é colorida de
  verde e as áreas infectadas aparecem em vermelho. A imagem retorna em
  base64 diretamente da API.
