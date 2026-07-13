# Monitoramento Regulatório Diário — versão equipe, custo zero e sem instalação local

## Decisão técnica recomendada
Usar **GitHub Pages + GitHub Actions**.

- A equipe acessa o sistema pelo navegador.
- Nenhum computador precisa instalar Python, Power BI, extensões ou programas.
- O monitoramento roda na nuvem pelo GitHub Actions.
- O resultado fica salvo em `data/resultado_atual.json` e também no histórico diário em `data/historico/`.

## Como a equipe irá usar no dia a dia

### Opção 1 — automático
O robô roda de segunda a sexta, às 07h no horário de Brasília.
Depois disso, basta abrir o sistema e clicar em **Carregar monitoramento do dia**.

### Opção 2 — manual, quando quiserem atualizar na hora
1. Entrar no repositório do GitHub.
2. Clicar em **Actions**.
3. Abrir **Monitoramento Regulatório Diário**.
4. Clicar em **Run workflow**.
5. Aguardar a execução finalizar.
6. Abrir o sistema web e clicar em **Carregar monitoramento do dia**.

No sistema há também o botão **Realizar na nuvem**, que abre a tela correta do GitHub Actions quando o sistema estiver publicado pelo GitHub Pages.

## Passo a passo de implantação

1. Criar um repositório público no GitHub.
2. Enviar todos os arquivos desta pasta para o repositório.
3. Ir em **Settings > Pages**.
4. Em **Build and deployment**, selecionar publicação a partir da branch principal, pasta `/root`.
5. Ir em **Actions** e executar manualmente o workflow pela primeira vez.
6. Abrir o link gerado pelo GitHub Pages.
7. Clicar em **Carregar monitoramento do dia**.

## Observações importantes

- Para manter custo zero com GitHub Actions, o repositório deve ser público.
- Se o repositório for privado, pode haver limite de minutos gratuitos conforme o plano da conta/organização.
- Alguns sites podem bloquear ou mudar a estrutura da página. Quando isso acontecer, o sistema registra erro para validação manual.
- O Diário Oficial da União deve ser tratado em etapa própria, com filtros específicos por termo, porque não funciona como uma página simples de notícias.

## Fontes já incluídas no motor

- ANVISA
- COFEN
- CFM
- CREMERS
- COREN-RS
- CRF-RS
- CRN-2
- CRO-RS
- CRTR-6

## Próxima evolução recomendada

Criar a camada específica do DOU com filtros por termos regulatórios, por exemplo: RDC, Resolução, Portaria, Consulta Pública, medicamento, saneante, produto para saúde, fórmula infantil, hemoterapia, banco de sangue e outros termos definidos pela área.
