# Desafio Final 009 — Coeficiente de Variação com OpenMP

Estrutura inicial derivada de [Multiplicacao_de_matrizes_densas_pp](https://github.com/FilipeCampos25/Multiplicacao_de_matrizes_densas_pp), branch `main`, para o enunciado `009_desafio_final_openmp_prof_rodrigo(1).pdf`.

## O que foi preservado

- `Dockerfile`, `docker-compose.yml`, `.devcontainer/devcontainer.json` e `.gitignore`: copiados sem alteração do repositório de referência.
- Compilador `g++`; flags `-O2 -std=c++17 -Wall -Wextra -Wpedantic` e `-fopenmp` só para a versão paralela.
- Diretórios `codigos/baselines_sequenciais_CCO085/`, `codigos/01_openmp/` e binários em `bin/`.
- `referencia_original/Makefile`: cópia integral do Makefile do projeto de matrizes. O `Makefile` da raiz é adaptado ao exercício de CV, já que o original aponta para multiplicação de matrizes e MPI.

## Uso do ambiente

Na raiz desta pasta:

```bash
docker compose build
docker compose run --rm pp-lab
make                         # hoje: avisa fontes ainda pendentes
make help
```

Crie os futuros fontes nos caminhos:

- `codigos/baselines_sequenciais_CCO085/cv_sequencial.cpp`
- `codigos/01_openmp/cv_openmp.cpp`

As versões deverão aceitar como primeiro argumento o caminho do arquivo TXT, por exemplo `dados/pessoas.txt`. Esse contrato é do **projeto inicial**, não do enunciado do professor.

O arquivo **não foi fornecido** no enunciado PDF. Quando você tiver a entrada real de 1000 pessoas, coloque-a em `dados/pessoas.txt` (uma linha: `estatura peso`, separados por espaço).

```bash
make check-data
make base
make openmp
make run-base
make run-openmp THREADS=4
make test                  # smoke test; ainda sem comparacao numerica
make benchmark THREADS=4   # tempos simples; repetir para analise final
make clean
```

Atenção: o Compose original usa `container_name: pp-lab`. Se o contêiner do projeto de matrizes estiver ativo, pare-o antes de iniciar este projeto, ou haverá conflito de nomes. O Docker original contém MPI, mas o desafio 009 **não exige MPI**.

## Entregáveis ainda pendentes

Confira `CHECKLIST.md`. A infraestrutura não substitui o código C/C++ com OpenMP, os dois CVs, a análise de tempos e o relatório PDF exigidos na atividade.
