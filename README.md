# Monitoramento Diário — Regulamentação e Parametrização

Sistema web para monitoramento diário de notícias e legislações regulatórias.

## Como publicar no GitHub

1. Extraia o ZIP.
2. No repositório, clique em **Add file > Upload files**.
3. Arraste todos os arquivos e pastas de dentro da pasta extraída.
4. Clique em **Commit changes**.

## Como ativar o site

1. Vá em **Settings > Pages**.
2. Em **Build and deployment**, selecione:
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/root**
3. Clique em **Save**.

## Como rodar o robô manualmente

1. Vá em **Actions**.
2. Clique em **Monitoramento Regulatório Diário**.
3. Clique em **Run workflow**.

O robô também roda automaticamente todos os dias às 07h.

## Observação

Nenhum programa precisa ser instalado nos computadores da equipe. O Python roda apenas na nuvem do GitHub Actions.
