# Checklist de implementação — 009_desafio_final_openmp

Referência: **Exercício Final: Análise de Dados com OpenMP**, Prof. Rodrigo. Foco: coeficiente de variação de **estatura (cm)** e **peso (kg)** de **1000 pessoas**, por classes.

- [x] **1. Entrada e classes:** fornecer `dados/pessoas.txt` com 1000 linhas `estatura peso`; validar leitura; construir classes de **8 cm** e **4 kg**, definir claramente os limites e apurar as frequências (soma de cada variável = 1000). A entrada incluída é sintética e reproduzível, não fornecida pelo professor.
- [x] **2. Versão sequencial:** implementar `cv_sequencial.cpp` com pontos médios e frequência de cada classe; calcular **média ponderada (µ)**, **desvio padrão populacional (σ)** e **CV = (σ/µ) × 100%** para as duas variáveis.
- [x] **3. Versão OpenMP:** implementar `cv_openmp.cpp`, paralelizando laços relevantes de soma/média/desvio com `reduction` e garantindo contagem segura das frequências, sem corrida de dados.
- [x] **4. Corretude:** `make test` cria massas controladas de exatamente 1000 registros, testa valores imediatamente abaixo, exatamente na fronteira e imediatamente acima das classes de 8 cm e 4 kg, e usa uma referência Python independente para histogramas, pontos médios, média ponderada, desvio padrão populacional e CV. As versões sequencial e OpenMP são comparadas com `math.isclose` (`rel_tol=1e-9`, `abs_tol=5e-7`); o OpenMP roda 10 vezes com 1, 2 e 4 threads. Arquivo ausente, quantidades diferentes de 1000, linhas malformadas e valores não numéricos, não positivos, NaN, infinitos ou fora da faixa suportada devem retornar erro.
- [ ] **5. Desempenho:** medir tempos sequencial e paralelo **com a mesma entrada**, repetindo execuções, registrar threads/ambiente e analisar ganho ou sobrecarga (mesmo se OpenMP não for mais rápido).
- [ ] **6. Entrega:** incluir **código-fonte C/C++ com OpenMP**, **CV final de estatura e peso**, **comparação de tempos** e **relatório breve em PDF** explicando as partes paralelizadas e por quê.

> A entrada, as versões sequencial e OpenMP e a equivalência numérica estão validadas. As medições de desempenho e o relatório PDF permanecem pendentes.
