# Dados de entrada

`pessoas.txt` contém **dados sintéticos**, gerados apenas para desenvolvimento e
testes. Eles não foram fornecidos pelo professor e não representam pessoas reais.

O arquivo tem 1000 registros determinísticos no formato `estatura_cm peso_kg` e
pode ser reproduzido, a partir da raiz do projeto, com:

```bash
make generate-data
```

O gerador `scripts/gerar_dados_sinteticos.py` usa a semente fixa `20261110`.
