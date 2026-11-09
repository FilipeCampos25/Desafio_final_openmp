#!/usr/bin/env python3
"""Valida somente o formato exigido no enunciado (nao calcula CV)."""
from pathlib import Path
import math
import sys


def main() -> int:
    caminho = Path(sys.argv[1]) if len(sys.argv) == 2 else Path('dados/pessoas.txt')
    if not caminho.is_file():
        print(f'Erro: arquivo nao encontrado: {caminho}', file=sys.stderr)
        return 1
    linhas = caminho.read_text(encoding='utf-8').splitlines()
    if len(linhas) != 1000:
        print(f'Erro: esperado 1000 linhas; recebido {len(linhas)}.', file=sys.stderr)
        return 1
    for numero, linha in enumerate(linhas, start=1):
        valores = linha.split()
        if len(valores) != 2:
            print(f'Erro na linha {numero}: esperado estatura peso.', file=sys.stderr)
            return 1
        try:
            estatura, peso = map(float, valores)
        except ValueError:
            print(f'Erro na linha {numero}: valores nao numericos.', file=sys.stderr)
            return 1
        if not (math.isfinite(estatura) and math.isfinite(peso) and estatura > 0 and peso > 0):
            print(f'Erro na linha {numero}: estatura e peso devem ser positivos e finitos.', file=sys.stderr)
            return 1
    print(f'OK: 1000 registros validos em {caminho}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
