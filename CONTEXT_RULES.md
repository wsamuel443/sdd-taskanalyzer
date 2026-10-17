# CONTEXT_RULES — Governança de Contexto para Agentes de IA

Fonte da verdade fornecida aos assistentes de IA. Leia também
`specs/task_analyzer_spec.md` antes de gerar qualquer código.

## 1. Diretrizes Arquiteturais (obrigatórias)

- Python 3.11+ como versão mínima.
- Type hints em 100% das funções, métodos e parâmetros.
- Princípio Single Responsibility (SRP) e PEP 8.
- Docstrings no padrão Google style (módulos, classes, funções).
- Funções pequenas, coesas e com um único propósito.
- Exceções específicas e customizadas, com mensagens claras.
- Logs estruturados com o módulo padrão `logging`.
- Nomes descritivos; sem lógica em scripts soltos.

## 2. Proibições explícitas

- Não usar bibliotecas externas além da biblioteca padrão (e `pytest` nos testes).
- Não alterar, remover ou adaptar os cenários de teste da especificação.
- Não modificar a estrutura de pastas definida na especificação.
- Não persistir dados em arquivos ou bancos: o módulo é analítico e em memória.
- Não alterar a assinatura das funções públicas sem autorização explícita.
- Não gerar código sem testes correspondentes.
- Não inserir código duplicado ou desnecessário; não comentar em excesso.
- Não assumir comportamentos não especificados no contrato de negócio.
- Não retornar valores diferentes do contrato de saída.

## 3. Regras de interação com a IA

1. Fornecer sempre o contexto completo (este arquivo + a especificação) antes de pedir código.
2. Validar se a IA compreendeu o contrato e os testes antes de aceitar a geração.
3. Pedir explicações quando houver dúvida sobre a solução proposta.
4. Revisar criticamente todo código gerado: nenhuma saída é aceita sem revisão humana.
5. Rejeitar respostas que violem as proibições (Seção 2) ou o contrato de negócio.

## 4. Homologação humana (antes de qualquer commit)

1. Executar `pytest` completo.
2. Conferir conformidade com o contrato e com estas regras.
3. Revisar qualidade (legibilidade, tratamento de erros, padrões).
4. Testar manualmente casos de borda (lista vazia, datas-limite).
5. Só então commitar.
