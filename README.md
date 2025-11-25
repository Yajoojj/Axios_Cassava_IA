# Projeto Cassava Blight Detection 

Este repositório contém uma solução completa para **detecção de bacteriose em folhas de mandioca**.  
A versão aqui fornecida utiliza **deep learning com TensorFlow e EfficientNet**, conforme sugerido em estudos recentes que combinam o espaço de cores HSV com redes profundas para melhorar a precisão na detecção.  

O projeto está organizado em duas partes principais:

- **backend/** – uma API construída com **FastAPI** que carrega o modelo de rede neural para classificar imagens de folhas, calcula a proporção de área infectada via segmentação HSV e gera sobreposições coloridas.  
- **frontend/** – uma aplicação **React** que permite ao usuário enviar fotos da folha, visualizar os resultados da predição e a imagem com mapa de infecção.

Cada parte possui um README separado com instruções detalhadas de instalação e execução. Este arquivo resume o propósito geral e as considerações principais.

## 🌿 Objetivo

Detectar de forma automatizada se uma folha de mandioca está **saudável** ou **infectada** por bacteriose, indicando também a **severidade** da doença e a **proporção de área infectada**. O sistema foi pensado para rodar tanto em ambiente de desenvolvimento local quanto em servidores, fornecendo uma base extensível para novas funcionalidades.

## 📁 Estrutura do repositório

```
cassava_ultimate/
├── README.md              # Este arquivo
├── backend/               # Código e scripts da API
│   ├── README.md          # Instruções específicas do backend
│   ├── main.py            # Servidor FastAPI com endpoint /predict
│   ├── model_utils_dl.py  # Funções para criação e carregamento do modelo EfficientNet
│   ├── hsv_utils.py       # Rotinas de segmentação HSV e sobreposição
│   ├── train_efficientnet.py  # Script para treinar seu próprio modelo deep learning
│   ├── prepare_dataset.py     # Script para organizar datasets misturados
│   ├── requirements.txt   # Dependências Python
│   └── models/            # (Vazio) Local para salvar modelos treinados (.h5)
└── frontend/              # Aplicação React
    ├── README.md          # Instruções específicas do frontend
    ├── package.json       # Dependências e scripts do frontend
    ├── public/
    │   └── index.html     # HTML base usando Tailwind via CDN
    └── src/
        ├── App.js         # Componente principal com interface em português
        └── index.js       # Ponto de entrada do React
```

## 🧠 Base científica

Os algoritmos implementados seguem o resultado de pesquisas que combinaram técnicas de **segmentação em HSV** com redes **EfficientNet** para detecção de doenças em folhas.  
Segundo Gao et al., a transformação da imagem para o espaço de cor HSV ajuda a realçar diferenças de tonalidade entre tecido saudável e infectado, e a utilização de EfficientNet na classificação melhora significativamente a precisão.  
Os resultados indicam que essa combinação auxilia na detecção precoce e monitoramento de doenças em plantios de mandioca.

