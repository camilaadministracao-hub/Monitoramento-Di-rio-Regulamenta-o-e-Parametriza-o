# Monitoramento Regulatório Diário — V4.1 — ANS FORA DO ESCOPO

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


## Regra de escopo V4.1
A parte referente à Agência Nacional de Saúde Suplementar (ANS) foi integralmente desconsiderada.
O sistema não consulta, não classifica e não exibe conteúdos de ANS, saúde suplementar, TISS, IDSS,
NIP, Ressarcimento ao SUS ou ROL de Procedimentos.

As regras da IT-SUP-9.0244 aplicadas ao sistema estão registradas em:
`config/regras_it_sup_9_0244_sem_ans.json`.
