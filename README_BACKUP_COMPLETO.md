# Monitoramento Regulatório Diário — V4.0 FINAL

Este pacote é o backup completo de todo o código-fonte acumulado do projeto.

## Fluxo diário
1. O GitHub Actions executa automaticamente às 07h.
2. A equipe abre o sistema pelo GitHub Pages.
3. Clica em **Carregar resultado do monitoramento**.
4. Revisa Publicações, aprova itens e utiliza Dados para Planilha e Comunicações.

## Execução manual
1. Clique em **Executar monitoramento** no sistema.
2. No GitHub, clique em **Run workflow**.
3. Aguarde o símbolo verde.
4. Volte ao sistema e clique em **Carregar resultado do monitoramento**.

## Estrutura
- `index.html`: interface completa aprovada, regras, fórmulas e áreas.
- `scripts/monitorar.py`: motor das 11 fontes.
- `.github/workflows/monitoramento.yml`: agendamento e execução manual.
- `data/resultado_atual.json`: resultado lido pelo sistema.
- `data/historico/`: histórico de execuções.
- `resultado_atual.json`: cópia de compatibilidade.
