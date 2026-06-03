# Sistema de Reconstrução 3D

### Introdução
Este sistema automatiza o fluxo de fotogrametria, permitindo transformar vídeos e sequências de fotos em modelos tridimensionais. Ele integra ferramentas de visão computacional e algoritmos de reconstrução em uma interface unificada via Python, facilitando o processo desde a captura até a visualização final.

### Módulos do Sistema
O software é estruturado em etapas lógicas baseadas nos scripts contidos em `src/`:

1. **Aquisição (`acquisition.py`):** Converte vídeos em sequências de frames para processamento.
2. **Calibração (`camera_calibration.py`):** Calcula os parâmetros da câmera para corrigir distorções de lente.
3. **Reconstrução (`reconstruction.py`):** Motor principal que utiliza o COLMAP para gerar a nuvem de pontos e a malha 3D.
4. **Normalização:** Organiza e padroniza os dados para otimizar a triangulação.
5. **Visualização (`visualization.py`):** Interface para inspeção dos modelos 3D gerados.

---

### Preparação do Ambiente (Conda)

O uso do Conda é a forma recomendada para garantir a aceleração por hardware (GPU/CUDA) e a compatibilidade das bibliotecas de sistema.

#### 1. Criar e Ativar o Ambiente
Abra o terminal na pasta raiz do projeto e execute:
```bash
# Cria o ambiente isolado com Python 3.12
conda create -n condaVenv python=3.12 -y

# ATIVA o ambiente (Obrigatório antes dos próximos passos)
conda activate condaVenv
```

#### 2. Instalar o Motor de Reconstrução (COLMAP)
Instale a versão estável compatível com o pipeline de automação:
```bash
conda install -c conda-forge colmap=3.12.6 -y
```

#### 3. Instalar Dependências do Sistema (Pip)
Com o ambiente `condaVenv` ativo, instale os pacotes Python necessários para a interface e processamento de imagem:
```bash
pip install -r requirements.txt
```

---

### Como Executar

Toda a operação é centralizada no arquivo `main.py` e controlada pelo `config.yaml`.

1. **Configuração:** Ajuste as pastas e parâmetros no `config.yaml` (ex: `remote_mode`, `desired_fps`).
2. **Execução:**
   ```bash
   # Certifique-se de que o ambiente está ativo
   conda activate condaVenv
   
   # Inicie o pipeline
   python main.py
   ```

### Logs e Resultados
- Os modelos gerados serão salvos em `data/out/reconstructions/`.
- O histórico de processamento pode ser consultado nos arquivos `.log` dentro da pasta de cada teste.