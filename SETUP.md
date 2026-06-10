# Configuração do Ambiente

## Opção 1: Ambiente Virtual (venv) - Windows/Visual Studio

### 1. Criar o ambiente virtual
```powershell
python -m venv AugmentedRealityEnv
```

### 2. Ativar o ambiente
```powershell
.\AugmentedRealityEnv\Scripts\Activate.ps1
```

### 3. Atualizar pip
```powershell
python -m pip install --upgrade pip
```

### 4. Instalar dependências
```powershell
pip install -r requirements.txt
```

### 5. Configurar no Visual Studio
O Visual Studio deve detectar automaticamente o ambiente. Se não:
- Vá em **Tools > Options > Python > Environments**
- Adicione o caminho: `AugmentedRealityEnv\Scripts\python.exe`

---

## Opção 2: Conda (Recomendado para GPU/CUDA)

### 1. Criar e ativar o ambiente
```bash
conda create -n condaVenv python=3.12 -y
conda activate condaVenv
```

### 2. Instalar COLMAP
```bash
conda install -c conda-forge colmap=3.12.6 -y
```

### 3. Instalar dependências Python
```bash
pip install -r requirements.txt
```

---

## Verificar instalação

```powershell
# Verificar Python
python --version

# Verificar pacotes instalados
pip list

# Testar importações
python -c "import cv2; import yaml; print('OK')"
```

---

## Notas

- **Visual Studio**: Sempre verifique se o interpretador correto está selecionado
- **PowerShell**: Se houver erro de execução de scripts, execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Ambientes separados**: Use venv para desenvolvimento no VS ou conda para processamento com GPU
