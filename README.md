# Analisador estatístico em Python

Implementação do trabalho de Probabilidade e Estatística. O programa lê dados digitados ou um CSV e apresenta as três análises solicitadas. Este README serve como relatório técnico, opção aceita pelo enunciado.

## Requisitos

- Python 3.9 ou superior
- Nenhuma dependência externa

## Como executar

No terminal, dentro desta pasta:

```bash
python3 estatistica.py
```

Escolha a entrada manual ou informe o caminho de um CSV. Digite valores separados por vírgulas, ponto e vírgula ou espaços. O CSV pode ter delimitador vírgula ou ponto e vírgula, números com ponto decimal e cabeçalho textual opcional. Os valores numéricos podem ocupar uma ou mais colunas; todos são considerados observações. Exemplo:

```csv
valor
18
22
26
```

## Organização e fórmulas

- **Dados não agrupados:** `ungrouped_summary` usa diretamente `statistics.mode`, `statistics.mean` e `statistics.median`, conforme a regra da Parte 1. Em caso de empate de moda, `statistics.mode` retorna a primeira moda encontrada.
- **Frequência discreta:** `discrete_summary` constrói a tabela ordenada de `xi`, frequência absoluta `fi` e acumulada `Fi`. Média ponderada, mediana por posições acumuladas e moda(s) são obtidas dessa tabela.
- **Classes contínuas:** `build_classes` escolhe `k = ceil(1 + 3.322 log10(n))`, calcula `h = (máximo − mínimo) / k` e inclui o maior valor no último intervalo. O programa exibe `k` e `h`. `continuous_summary` usa pontos médios para a média. Mediana e separatrizes usam `L + ((posição − F_anterior) / fi) h`, com posição `n·p`. A moda usa a interpolação de Czuber: `L + (d1 / (d1 + d2)) h`, em que `d1 = fi − f_anterior` e `d2 = fi − f_seguinte`.

Na Parte 3, os cálculos usam apenas operações e funções matemáticas da biblioteca padrão; não usam `statistics`, NumPy, Pandas ou SciPy. Se todas as observações forem iguais, o programa retorna esse valor para as medidas e separatrizes, evitando divisão por amplitude zero. Se houver empate de classe modal, é usada a primeira classe de maior frequência; com denominador de Czuber igual a zero, usa-se o ponto médio dessa classe.

## Testes

Execute os testes automatizados da biblioteca padrão:

```bash
python3 -m unittest -v
```

Os testes verificam leitura e validação de dados, tabela discreta, classes e frequência acumulada, fórmulas de interpolação e amostra constante.
