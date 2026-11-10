#!/usr/bin/env python3
import math
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDADOR = ROOT / 'scripts' / 'validar_entrada.py'


class ValidarEntradaTest(unittest.TestCase):
    def executar(self, linhas=None, inexistente=False):
        caminho = ROOT / 'tests' / '.entrada_temporaria.txt'
        try:
            caminho.unlink(missing_ok=True)
            if not inexistente:
                caminho.write_text(''.join(linhas), encoding='utf-8')
            return subprocess.run(
                [sys.executable, str(VALIDADOR), str(caminho)],
                capture_output=True, text=True, check=False)
        finally:
            caminho.unlink(missing_ok=True)

    @staticmethod
    def validas():
        return ['168.0 64.0\n'] * 1000

    def test_valida(self):
        self.assertEqual(self.executar(self.validas()).returncode, 0)

    def test_arquivo_inexistente(self):
        self.assertNotEqual(self.executar(inexistente=True).returncode, 0)

    def test_quantidade_incorreta(self):
        self.assertNotEqual(self.executar(self.validas()[:-1]).returncode, 0)

    def test_negativo_zero_nan_infinito_e_malformada(self):
        casos = ['-1 60\n', '168 0\n', 'nan 60\n', '168 inf\n', '168\n',
                 '168 60 extra\n', 'abc 60\n']
        for primeira in casos:
            with self.subTest(primeira=primeira.strip()):
                linhas = self.validas()
                linhas[0] = primeira
                self.assertNotEqual(self.executar(linhas).returncode, 0)


if __name__ == '__main__':
    unittest.main()
