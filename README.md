# Desafio Final 009 — Coeficiente de Variação com OpenMP

## Objetivo

Calcular o coeficiente de variação (CV) da estatura e do peso de 1000 pessoas,
comparando uma implementação sequencial com uma implementação paralela em
C++17/OpenMP. As estaturas devem ser agrupadas em classes de 8 cm e os pesos em
classes de 4 kg.

A especificação principal é o documento
`009_desafio_final_openmp_prof_rodrigo (1).pdf`, fornecido pelo professor.

## Requisitos do professor

- Ler estatura e peso de 1000 pessoas.
- Agrupar estaturas em classes de 8 cm e pesos em classes de 4 kg.
- Calcular média, desvio padrão e coeficiente de variação a partir das classes.
- Implementar e comparar versões sequencial e paralela com OpenMP.
- Entregar o código C/C++ completo, os CVs obtidos, a análise de desempenho e
  um relatório em PDF que explique as partes paralelizadas e as decisões tomadas.

## Estrutura do repositório

```text
.
├── .devcontainer/                 configuração do ambiente de desenvolvimento
├── codigos/
│   ├── baselines_sequenciais_CCO085/  futura versão sequencial
│   └── 01_openmp/                     futura versão OpenMP
├── dados/                         entrada com os 1000 registros
├── docs/                          relatório final em PDF
├── resultados/                    CVs e medições documentadas
├── scripts/                       validação e automação do projeto
├── CHECKLIST.md                   etapas e entregáveis
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

## Formato da entrada

O caminho padrão é `dados/pessoas.txt`. O arquivo deve conter exatamente 1000
linhas, com a estatura em centímetros e o peso em quilogramas separados por
espaço:

```text
estatura_cm peso_kg
```

O conjunto de dados não acompanha esta estrutura inicial. Não use dados
inventados como se fossem resultados oficiais.

## Configuração e execução

O ambiente fornece `g++`, C++17 e OpenMP. Na raiz do repositório:

```bash
docker compose build
docker compose run --rm desafio-openmp
make
make help
```

Enquanto as implementações estiverem pendentes, `make` apenas informa os fontes
ausentes. Os comandos previstos são:

```bash
make check-data
make base
make openmp
make run-base
make run-openmp THREADS=4
make test
make benchmark THREADS=4
make clean
```

MPI está instalado na imagem da disciplina, mas não é requisito deste desafio e
não é usado pelo Makefile.

## Etapas de implementação

1. Preparar e validar os 1000 registros e definir os limites das classes.
2. Implementar `codigos/baselines_sequenciais_CCO085/cv_sequencial.cpp`.
3. Implementar `codigos/01_openmp/cv_openmp.cpp` com OpenMP.
4. Comparar numericamente as versões e testar diferentes números de threads.
5. Medir o desempenho nas mesmas condições e documentar os resultados.

## Testes e entregáveis

Os testes devem cobrir entrada inválida, fronteiras das classes, total das
frequências, fórmulas estatísticas e equivalência numérica entre as versões. A
medição de desempenho só deve ser executada depois que ambas as implementações
estiverem corretas.

O andamento está em `CHECKLIST.md`. Nesta etapa inicial, os programas, dados,
resultados, medições e relatório continuam pendentes.
