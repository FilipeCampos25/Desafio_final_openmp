# Checklist de implementação — 009_desafio_final_openmp

Referência: **Exercício Final: Análise de Dados com OpenMP**, Prof. Rodrigo. Foco: coeficiente de variação de **estatura (cm)** e **peso (kg)** de **1000 pessoas**, por classes.

- [x] **1. Entrada e classes:** fornecer `dados/pessoas.txt` com 1000 linhas `estatura peso`; validar leitura; construir classes de **8 cm** e **4 kg**, definir claramente os limites e apurar as frequências (soma de cada variável = 1000). A entrada incluída é sintética e reproduzível, não fornecida pelo professor.
- [x] **2. Versão sequencial:** implementar `cv_sequencial.cpp` com pontos médios e frequência de cada classe; calcular **média ponderada (µ)**, **desvio padrão populacional (σ)** e **CV = (σ/µ) × 100%** para as duas variáveis.
- [x] **3. Versão OpenMP:** implementar `cv_openmp.cpp`, paralelizando laços relevantes de soma/média/desvio com `reduction` e garantindo contagem segura das frequências, sem corrida de dados.
- [x] **4. Corretude:** testar os limites das classes e dados controlados; verificar 1000 frequências e comparar os CVs sequencial × OpenMP com tolerância numérica, inclusive 1, 2 e 4 threads. Validado com tolerância absoluta de `1e-6` e 10 repetições por quantidade de threads.
- [ ] **5. Desempenho:** medir tempos sequencial e paralelo **com a mesma entrada**, repetindo execuções, registrar threads/ambiente e analisar ganho ou sobrecarga (mesmo se OpenMP não for mais rápido).
- [ ] **6. Entrega:** incluir **código-fonte C/C++ com OpenMP**, **CV final de estatura e peso**, **comparação de tempos** e **relatório breve em PDF** explicando as partes paralelizadas e por quê.

> A entrada, as versões sequencial e OpenMP e a equivalência numérica estão validadas. As medições de desempenho e o relatório PDF permanecem pendentes.
