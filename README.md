### Sistema de Reconstrução 3D Introdução

Este sistema automatiza o fluxo de fotogrametria, permitindo transformar vídeos e sequências de fotos em modelos tridimensionais. Ele integra ferramentas de visão computacional (OpenCV) e algoritmos de reconstrução (COLMAP) em uma interface unificada via Python. O projeto foi estruturado para facilitar o processamento de dados desde a correção da lente até a visualização final do modelo.

### Módulos do Sistema

O software é dividido em quatro etapas lógicas que devem ser executadas em sequência:

    Calibração (CameraCalibration): Processa fotos de um padrão de xadrez para calcular a matriz intrínseca da câmera e corrigir distorções da lente.

    Extração de Frames (OpenCV): Converte vídeos de entrada em uma sequência de imagens estáticas (frames) com base na taxa de quadros (FPS) configurada.

    Reconstrução 3D (Reconstruction): Utiliza o motor do COLMAP para realizar a triangulação de pontos, estimar a posição das câmeras e gerar a nuvem de pontos.

    Visualização (Visualization): Interface para renderizar e inspecionar o modelo final nos formatos .ply ou .obj.

### Preparação do Ambiente (VENV)

O projeto conta com um script de automação para configurar todo o ambiente de desenvolvimento, garantindo que todas as dependências estejam na versão correta.

Para configurar o ambiente:

    Abra o terminal na pasta raiz do projeto.

    Execute o script de setup:
    Bash

    python setup_venv.py

    O script irá criar a pasta .venv, ativar o ambiente virtual e instalar todas as bibliotecas do arquivo requirements.txt automaticamente.