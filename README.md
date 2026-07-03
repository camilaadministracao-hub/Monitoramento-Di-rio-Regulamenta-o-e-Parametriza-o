# Monitoramento Diário — Regulamentação e Parametrização

Versão 3.0 do sistema de monitoramento diário de notícias e legislações.

## Como subir no GitHub

1. Abra o repositório no GitHub.
2. Clique em **uploading an existing file**.
3. Extraia este ZIP no computador.
4. Arraste **todo o conteúdo da pasta** para o GitHub, incluindo:
   - `index.html`
   - `scripts/`
   - `data/`
   - `.github/`
   - `.nojekyll`
   - `README.md`
5. Clique em **Commit changes**.

## Como ativar o site

1. No repositório, vá em **Settings**.
2. Clique em **Pages**.
3. Em **Build and deployment**, selecione:
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/root**
4. Clique em **Save**.

Depois de alguns minutos, o GitHub mostrará o link do sistema.

## Como executar o robô

O robô roda automaticamente todos os dias às 07h.

Para executar manualmente:

1. Vá em **Actions**.
2. Clique em **Monitoramento Regulatório Diário**.
3. Clique em **Run workflow**.
4. Aguarde finalizar.
5. Volte ao sistema e clique em **Atualizar tela**.

## Observação importante

Nenhum programa precisa ser instalado no computador da equipe. O Python roda apenas na nuvem do GitHub Actions.
