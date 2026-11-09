# Programacao Paralela (CCO085) - IESB 2026/2
# Adaptado do Makefile de Multiplicacao_de_matrizes_densas_pp.
# Desafio final 009: coeficiente de variacao com OpenMP (sem MPI).

.DEFAULT_GOAL := all

CXX      := g++
CXXFLAGS := -O2 -std=c++17 -Wall -Wextra -Wpedantic
LDLIBS   := -lm

BIN_DIR       := bin
BASE_SOURCE   := codigos/baselines_sequenciais_CCO085/cv_sequencial.cpp
BASE_BINARY   := $(BIN_DIR)/base/cv_sequencial
OPENMP_SOURCE := codigos/01_openmp/cv_openmp.cpp
OPENMP_BINARY := $(BIN_DIR)/openmp/cv_openmp
DATA          ?= dados/pessoas.txt
THREADS       ?= 4

# Compila apenas as implementacoes que ja existirem.
AVAILABLE_TARGETS :=
ifneq ($(wildcard $(BASE_SOURCE)),)
AVAILABLE_TARGETS += base
endif
ifneq ($(wildcard $(OPENMP_SOURCE)),)
AVAILABLE_TARGETS += openmp
endif

all: $(AVAILABLE_TARGETS)
	@if test ! -f "$(BASE_SOURCE)"; then \
		printf '%s\n' "Sequencial pendente: $(BASE_SOURCE)"; \
	fi
	@if test ! -f "$(OPENMP_SOURCE)"; then \
		printf '%s\n' "OpenMP pendente: $(OPENMP_SOURCE)"; \
	fi

base: $(BASE_BINARY)
openmp: $(OPENMP_BINARY)

$(BASE_BINARY): $(BASE_SOURCE)
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDLIBS)

$(OPENMP_BINARY): $(OPENMP_SOURCE)
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) -fopenmp -o $@ $< $(LDLIBS)

check-data:
	python3 scripts/validar_entrada.py "$(DATA)"

# Convenção de interface para os futuros programas C++:
# cada executavel recebe o caminho do TXT como primeiro argumento.
run-base: check-data base
	./$(BASE_BINARY) "$(DATA)"

run-openmp: check-data openmp
	OMP_NUM_THREADS=$(THREADS) ./$(OPENMP_BINARY) "$(DATA)"

# Medicao inicial: executar novamente varias vezes antes da analise final.
benchmark: check-data base openmp
	@printf '%s\n' "== Sequencial =="
	@/usr/bin/time -f 'tempo_real=%e s' ./$(BASE_BINARY) "$(DATA)"
	@printf '%s\n' "== OpenMP ($(THREADS) threads) =="
	@OMP_NUM_THREADS=$(THREADS) /usr/bin/time -f 'tempo_real=%e s' ./$(OPENMP_BINARY) "$(DATA)"

# Smoke test: valida a entrada e executa ambas as versoes.
# A comparacao numerica de resultados ainda deve ser implementada.
test: run-base run-openmp

clean:
	rm -rf $(BIN_DIR)

help:
	@printf '%s\n' 'make all | base | openmp | check-data | test | benchmark | clean'
	@printf '%s\n' 'Exemplo: make benchmark DATA=dados/pessoas.txt THREADS=4'

.PHONY: all base openmp check-data run-base run-openmp benchmark test clean help
