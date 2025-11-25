# Backend – Cassava Blight Detection (FastAPI & TensorFlow)

Este diretório contém o servidor backend responsável por servir a API de detecção de bacteriose em folhas de mandioca.  
A API foi construída em **FastAPI** e utiliza um modelo **EfficientNet** treinado em TensorFlow para classificar imagens. Também utiliza segmentação em espaço HSV para calcular a área infectada e gerar uma sobreposição colorida.

## 📦 Dependências

Instale as dependências usando o `pip`:

```bash
pip install -r requirements.txt
```

Principais pacotes utilizados:

- **fastapi** e **uvicorn**: framework e servidor para a API.
- **tensorflow**: biblioteca de deep learning utilizada para treinar e carregar o modelo EfficientNet.
- **opencv-python** e **numpy**: manipulação de imagens e matrizes.
- **Pillow**: carregamento de imagens no formato RGB.
- **python-multipart**: permite o upload de arquivos via FastAPI.

## 🚀 Executando o servidor

Inicie o servidor FastAPI com o comando abaixo (utilizando a opção `-m` do Python para garantir o carregamento do módulo Uvicorn no Windows):

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Após a inicialização, a API estará disponível em `http://localhost:8000`.

## 🔗 Endpoint `/predict`

O endpoint principal da aplicação é o **POST `/predict`**. Ele recebe uma imagem de folha via upload multipart/form-data e retorna um JSON com:

- `probability`: probabilidade de a folha estar infectada (0 a 1).
- `class`: classe prevista (`"Saudável"` ou `"Infectado"`).
- `ratio`: proporção de área da folha classificada como infectada.
- `severity`: nível de severidade (`"Leve"`, `"Moderada"` ou `"Grave"`).
- `overlay`: string em base64 com a imagem da folha sobreposta (verde para parte saudável, vermelho para áreas infectadas).

### Exemplo de requisição via cURL

```bash
curl -F "image=@caminho/da/folha.jpg" http://localhost:8000/predict
```

### Exemplo de resposta

```json
{
  "probability": 0.87,
  "class": "Infectado",
  "ratio": 0.31,
  "severity": "Moderada",
  "overlay": "data:image/png;base64,iVBORw0K..."
}
```

## 🛠 Treinando um novo modelo

Para treinar um novo modelo usando a base de imagens, utilize o script `train_efficientnet.py`. Exemplo de uso:

```bash
python train_efficientnet.py \
  --data-dir sorted_dataset \
  --model-path models/cassava_effnet.h5 \
  --epochs 20
```

O script espera que o diretório `data-dir` contenha duas subpastas: `healthy/` e `infected/`, cada uma com as respectivas imagens.

## 🧰 Organizando um dataset misturado

Caso tenha uma pasta com imagens saudáveis e infectadas misturadas, utilize o script `prepare_dataset.py` para pré‑classificar e copiar as fotos em subpastas `healthy/` e `infected/` usando o modelo atual:

```bash
python prepare_dataset.py \
  --input-dir mixed_images \
  --output-dir sorted_dataset \
  --model-path models/cassava_effnet.h5 \
  --threshold 0.5
```

Após a execução, revise as pastas resultantes para corrigir possíveis classificações erradas antes de treinar o modelo.

## 🔍 Estrutura dos arquivos

- **main.py** – define e expõe o endpoint `/predict`. Lê a imagem enviada, processa via modelo, realiza segmentação HSV e retorna os resultados. Todos os comentários e mensagens estão em português.
- **model_utils_dl.py** – fornece funções para construir e carregar o modelo EfficientNet, além de pré‑processar imagens para a predição.
- **hsv_utils.py** – implementa a segmentação da folha e das regiões infectadas em HSV, cálculo da severidade e criação de sobreposições coloridas.
- **train_efficientnet.py** – script de treinamento que cria um dataset a partir de um diretório organizado, aplica data augmentation e salva o modelo treinado.
- **prepare_dataset.py** – script para classificar e separar fotos de um diretório misto em pastas `healthy/` e `infected/` usando o modelo.
- **requirements.txt** – lista as dependências Python necessárias.
- **models/** – diretório onde devem ser armazenados os arquivos `.h5` com modelos treinados.

Sinta-se à vontade para adaptar e estender o backend para sua necessidade específica!
