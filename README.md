# Desafio Final 009 - Coeficiente de Variação com OpenMP

Projeto da disciplina **Programação Paralela (CCO085), IESB 2026/2**, do
professor **Rodrigo Gonçalves Pinto**. O programa calcula estatísticas agrupadas
de estatura e peso para 1000 pessoas e compara uma implementação sequencial com
uma implementação C++17/OpenMP.

> **Origem dos dados:** `dados/pessoas.txt` contém 1000 registros **sintéticos**,
> determinísticos e destinados apenas ao exercício. Eles foram gerados por
> `scripts/gerar_dados_sinteticos.py`, com semente `20261110`, e não são uma
> base oficial fornecida pelo professor nem representam pessoas reais.

O enunciado `009_desafio_final_openmp_prof_rodrigo (1).pdf` é referenciado pelo
material inicial, mas não está versionado neste repositório.

## Resultados finais

As classes são semiabertas `[limite_inferior, limite_superior)`, com largura de
8 cm para estatura e de 4 kg para peso. As duas implementações e todas as
configurações OpenMP produziram os mesmos resultados, com seis casas decimais:

| Variável | Média ponderada | Desvio padrão populacional | CV |
|---|---:|---:|---:|
| Estatura | 172,608000 cm | 15,964408 cm | 9,248939% |
| Peso | 82,420000 kg | 21,799073 kg | 26,448767% |

O benchmark versionado contém 30 medições por configuração e mede o processo
completo: criação e inicialização, leitura do arquivo, histogramas, cálculos e
escrita da saída capturada. No ambiente registrado, as médias foram:

| Configuração | Média | Mediana | Desvio padrão amostral | Speedup |
|---|---:|---:|---:|---:|
| Sequencial | 16,856280 ms | 16,521450 ms | 1,672749 ms | 1,000000x |
| OpenMP, 1 thread | 17,140990 ms | 16,895100 ms | 0,651562 ms | 0,983390x |
| OpenMP, 2 threads | 18,322650 ms | 17,829400 ms | 2,090454 ms | 0,919970x |
| OpenMP, 4 threads | 18,348070 ms | 17,937350 ms | 1,651019 ms | 0,918695x |

Para apenas 1000 registros, o trabalho por região paralela é pequeno. Nesse
ensaio, a inicialização, o agendamento e as barreiras do OpenMP custaram mais
que o ganho computacional, portanto não houve aceleração. Os números são
específicos do ambiente documentado em `resultados/benchmark_ambiente.txt`.

## Requisitos

O fluxo recomendado usa o ambiente da disciplina, com GCC, C++17, OpenMP,
Python 3 e GNU Make:

```bash
docker compose build
docker compose run --rm desafio-openmp
```

Também é possível executar diretamente em um Linux que tenha essas ferramentas.
MPI existe na imagem da disciplina, mas não é usado neste projeto.

## Compilação e validação dos dados

Na raiz do repositório:

```bash
make                         # compila as duas versões
make check-data              # valida formato, valores e os 1000 registros
make generate-data           # recria a entrada sintética com a semente fixa
```

As flags padrão são `-O2 -std=c++17 -Wall -Wextra -Wpedantic`; a versão
paralela acrescenta `-fopenmp`.

## Execução

```bash
make run-base
make run-openmp THREADS=1
make run-openmp THREADS=2
make run-openmp THREADS=4
```

`DATA` permite escolher outro arquivo válido sem alterar o padrão:

```bash
make run-base DATA=caminho/entrada.txt
make run-openmp DATA=caminho/entrada.txt THREADS=4
```

## Testes automatizados

```bash
make test-data
make test
```

`make test` valida leitura, entradas inválidas, limites de classe, frequências,
fórmulas e equivalência com uma referência Python independente. A versão
OpenMP é exercitada 10 vezes com 1, 2 e 4 threads em cada massa controlada.

## Benchmark reproduzível

Depois de os testes passarem:

```bash
make benchmark
```

O padrão executa três aquecimentos não registrados e 30 medições para a versão
sequencial e para OpenMP com 1, 2 e 4 threads. Parâmetros opcionais:

```bash
make benchmark DATA=dados/pessoas.txt \
  BENCHMARK_REPETITIONS=30 BENCHMARK_WARMUPS=3 \
  BENCHMARK_THREADS=1,2,4
```

O script usa `time.perf_counter_ns()`, compara os resultados numéricos a cada
execução e só grava os arquivos se todas as configurações forem consistentes.
As saídas são:

- `resultados/benchmark_medicoes.csv`: cada tempo individual em ns e ms;
- `resultados/benchmark_resumo.csv`: média, mediana, desvio padrão, extremos e
  speedup em relação à média sequencial;
- `resultados/estatisticas.csv`: média, desvio populacional e CV de cada versão;
- `resultados/benchmark_ambiente.txt`: compilador, flags, CPU, sistema, hashes,
  escopo da medição e disponibilidade do Docker.

## Relatório e entregáveis

O relatório final está em `docs/relatorio_desempenho_openmp.pdf`. Para recriá-lo
após atualizar os CSVs (requer o pacote Python `reportlab`):

```bash
python3 scripts/gerar_relatorio.py
```

Os quatro itens pedidos estão disponíveis:

1. código-fonte completo em C++17, incluindo diretivas OpenMP;
2. relatório breve em PDF explicando a paralelização;
3. CV final da estatura e do peso;
4. medições e análise sequencial versus paralelo.

## Estrutura principal

```text
codigos/baselines_sequenciais_CCO085/cv_sequencial.cpp
codigos/01_openmp/cv_openmp.cpp
dados/pessoas.txt
docs/relatorio_desempenho_openmp.pdf
include/dados.hpp
resultados/
scripts/benchmark.py
scripts/gerar_relatorio.py
src/dados.cpp
tests/
```

Use `make help` para listar os alvos e `make clean` para remover os binários.
