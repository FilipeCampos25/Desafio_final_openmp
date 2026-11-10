#!/usr/bin/env python3
"""Gera a entrada sintetica e deterministica usada no desenvolvimento."""
from pathlib import Path
import argparse
import random


QUANTIDADE = 1000
SEMENTE = 20261110


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('saida', nargs='?', default='dados/pessoas.txt')
    args = parser.parse_args()

    gerador = random.Random(SEMENTE)
    linhas = []
    for _ in range(QUANTIDADE):
        # Faixas plausiveis apenas para exercitar o programa; nao sao dados reais.
        estatura = round(145.0 + gerador.random() * 55.0, 2)
        peso = round(45.0 + gerador.random() * 75.0, 2)
        linhas.append(f'{estatura:.2f} {peso:.2f}\n')

    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(''.join(linhas), encoding='utf-8')
    print(f'Gerados {QUANTIDADE} registros sinteticos em {destino} (semente {SEMENTE}).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
