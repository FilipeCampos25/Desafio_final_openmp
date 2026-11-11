#!/usr/bin/env python3
"""Testes de ponta a ponta das versoes sequencial e OpenMP.

A referencia e independente do C++: monta histogramas com ``math.floor`` e
aplica diretamente as formulas das estatisticas agrupadas.
"""

from collections import Counter
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def caminho_executavel(caminho):
    """Usa o sufixo nativo no Windows sem alterar os caminhos do Makefile."""
    if os.name == "nt":
        return caminho.with_suffix(".exe")
    return caminho


SEQUENCIAL = caminho_executavel(ROOT / "bin" / "base" / "cv_sequencial")
OPENMP = caminho_executavel(ROOT / "bin" / "openmp" / "cv_openmp")
QUANTIDADE = 1000
REPETICOES = 10
THREADS = (1, 2, 4)

# A saida tem seis casas. 5e-7 cobre o arredondamento da ultima casa; 1e-9
# relativo cobre pequenas diferencas de ordem nas reducoes para valores maiores.
TOLERANCIA_ABSOLUTA = 5e-7
TOLERANCIA_RELATIVA = 1e-9

LINHA_RESULTADO = re.compile(
    r"^(estatura|peso) media=([-+0-9.eE]+) (?:cm|kg) "
    r"desvio_padrao=([-+0-9.eE]+) (?:cm|kg) cv=([-+0-9.eE]+) %$"
)


def histograma_referencia(valores, largura):
    """Retorna classes presentes como (inferior, superior, ponto medio, fi)."""
    frequencias = Counter(math.floor(valor / largura) for valor in valores)
    return [
        (indice * largura, (indice + 1) * largura,
         indice * largura + largura / 2.0, frequencias[indice])
        for indice in sorted(frequencias)
    ]


def estatisticas_referencia(classes):
    total = sum(classe[3] for classe in classes)
    if total != QUANTIDADE:
        raise ValueError(f"esperados {QUANTIDADE} valores; recebidos {total}")
    media = sum(meio * frequencia for _, _, meio, frequencia in classes) / total
    variancia = sum(
        frequencia * (meio - media) ** 2
        for _, _, meio, frequencia in classes
    ) / total
    desvio = math.sqrt(variancia)
    return {"media": media, "desvio_padrao": desvio, "cv": desvio / media * 100.0}


def referencia(registros):
    return {
        "estatura": estatisticas_referencia(
            histograma_referencia([item[0] for item in registros], 8.0)),
        "peso": estatisticas_referencia(
            histograma_referencia([item[1] for item in registros], 4.0)),
    }


def massa_fronteiras():
    # Abaixo, exatamente sobre e acima das fronteiras; exatamente 1000 itens.
    estaturas = (159.999, 160.0, 160.001, 167.999, 168.0,
                 168.001, 175.999, 176.0, 176.001, 183.999)
    pesos = (59.999, 60.0, 60.001, 63.999, 64.0,
             64.001, 67.999, 68.0, 68.001, 71.999)
    return [(estaturas[i % 10], pesos[(i * 3) % 10]) for i in range(QUANTIDADE)]


def massa_multiclasse():
    # Frequencias desiguais revelam erros de ponderacao mascarados por simetria.
    padrao = (
        [(145.25, 48.5)] * 7
        + [(153.75, 55.9)] * 11
        + [(162.2, 63.0)] * 13
        + [(171.8, 72.1)] * 17
        + [(188.4, 91.7)] * 19
    )
    return [padrao[i % len(padrao)] for i in range(QUANTIDADE)]


def massa_classe_unica():
    # Confirma pontos medios e o caso de desvio/CV zero.
    return [(161.0, 61.0)] * QUANTIDADE


class CorretudeExecutaveisTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        ausentes = [str(p) for p in (SEQUENCIAL, OPENMP) if not p.is_file()]
        if ausentes:
            raise RuntimeError(
                "compile os executaveis antes dos testes: " + ", ".join(ausentes)
            )

    def executar(self, executavel, caminho, threads=None):
        ambiente = os.environ.copy()
        if threads is not None:
            ambiente["OMP_NUM_THREADS"] = str(threads)
            ambiente["OMP_DYNAMIC"] = "FALSE"
        return subprocess.run(
            [str(executavel), str(caminho)], cwd=ROOT, env=ambiente,
            capture_output=True, text=True, timeout=15, check=False,
        )

    def analisar_saida(self, processo):
        self.assertEqual(
            processo.returncode, 0,
            msg=f"execucao falhou\nstdout: {processo.stdout}\nstderr: {processo.stderr}",
        )
        resultados = {}
        for linha in processo.stdout.splitlines():
            correspondencia = LINHA_RESULTADO.fullmatch(linha.strip())
            self.assertIsNotNone(
                correspondencia, msg=f"linha de saida inesperada: {linha!r}"
            )
            variavel, media, desvio, cv = correspondencia.groups()
            self.assertNotIn(variavel, resultados)
            resultados[variavel] = {
                "media": float(media), "desvio_padrao": float(desvio),
                "cv": float(cv),
            }
        self.assertEqual(set(resultados), {"estatura", "peso"})
        return resultados

    def assert_estatisticas(self, obtido, esperado, contexto):
        for variavel in ("estatura", "peso"):
            for medida in ("media", "desvio_padrao", "cv"):
                atual = obtido[variavel][medida]
                valor_esperado = esperado[variavel][medida]
                self.assertTrue(
                    math.isclose(atual, valor_esperado,
                                 rel_tol=TOLERANCIA_RELATIVA,
                                 abs_tol=TOLERANCIA_ABSOLUTA),
                    msg=(f"{contexto}: {variavel}.{medida}: obtido {atual}, "
                         f"esperado {valor_esperado}"),
                )

    def validar_massa(self, registros, nome):
        self.assertEqual(len(registros), QUANTIDADE)
        esperado = referencia(registros)
        with tempfile.TemporaryDirectory(prefix="cv_openmp_") as diretorio:
            caminho = Path(diretorio) / f"{nome}.txt"
            caminho.write_text(
                "".join(f"{e:.12g} {p:.12g}\n" for e, p in registros),
                encoding="utf-8",
            )
            sequencial = self.analisar_saida(self.executar(SEQUENCIAL, caminho))
            self.assert_estatisticas(sequencial, esperado, f"{nome}/sequencial")
            for threads in THREADS:
                for repeticao in range(1, REPETICOES + 1):
                    paralelo = self.analisar_saida(
                        self.executar(OPENMP, caminho, threads=threads)
                    )
                    contexto = f"{nome}/OpenMP/{threads} threads/repeticao {repeticao}"
                    self.assert_estatisticas(paralelo, esperado, contexto)
                    self.assert_estatisticas(paralelo, sequencial, contexto + "/vs seq")

    def test_referencia_e_fronteiras_das_classes(self):
        estatura = histograma_referencia(
            [159.999, 160.0, 160.001, 167.999, 168.0, 168.001], 8.0)
        peso = histograma_referencia(
            [59.999, 60.0, 60.001, 63.999, 64.0, 64.001], 4.0)
        self.assertEqual(
            estatura, [(152.0, 160.0, 156.0, 1),
                       (160.0, 168.0, 164.0, 3),
                       (168.0, 176.0, 172.0, 2)])
        self.assertEqual(
            peso, [(56.0, 60.0, 58.0, 1),
                   (60.0, 64.0, 62.0, 3),
                   (64.0, 68.0, 66.0, 2)])

    def test_massa_de_fronteiras(self):
        self.validar_massa(massa_fronteiras(), "fronteiras")

    def test_massa_multiclasse_com_frequencias_desiguais(self):
        self.validar_massa(massa_multiclasse(), "multiclasse")

    def test_massa_de_classe_unica(self):
        self.validar_massa(massa_classe_unica(), "classe_unica")

    def validar_rejeicao(self, linhas, nome):
        with tempfile.TemporaryDirectory(prefix="cv_invalido_") as diretorio:
            caminho = Path(diretorio) / f"{nome}.txt"
            if linhas is not None:
                caminho.write_text("".join(linhas), encoding="utf-8")
            for executavel, threads in ((SEQUENCIAL, None), (OPENMP, 4)):
                processo = self.executar(executavel, caminho, threads=threads)
                self.assertNotEqual(
                    processo.returncode, 0,
                    msg=(f"{executavel.name} aceitou entrada invalida {nome}\n"
                         f"stdout: {processo.stdout}\nstderr: {processo.stderr}"),
                )

    @staticmethod
    def linhas_validas():
        return ["168 64\n"] * QUANTIDADE


def adicionar_teste_invalido(nome, transformacao):
    def teste(self):
        linhas = None if transformacao is None else transformacao(self.linhas_validas())
        self.validar_rejeicao(linhas, nome)
    setattr(CorretudeExecutaveisTest, f"test_rejeita_{nome}", teste)


def substituir_primeira(valor):
    def transformar(linhas):
        linhas[0] = valor
        return linhas
    return transformar


CASOS_INVALIDOS = {
    "arquivo_inexistente": None,
    "999_registros": lambda linhas: linhas[:-1],
    "1001_registros": lambda linhas: linhas + ["168 64\n"],
    "linha_vazia": substituir_primeira("\n"),
    "campo_ausente": substituir_primeira("168\n"),
    "campo_excedente": substituir_primeira("168 64 extra\n"),
    "estatura_nao_numerica": substituir_primeira("abc 64\n"),
    "peso_nao_numerico": substituir_primeira("168 abc\n"),
    "estatura_zero": substituir_primeira("0 64\n"),
    "peso_zero": substituir_primeira("168 0\n"),
    "estatura_negativa": substituir_primeira("-1 64\n"),
    "peso_negativo": substituir_primeira("168 -1\n"),
    "nan": substituir_primeira("nan 64\n"),
    "infinito": substituir_primeira("168 inf\n"),
    "infinito_negativo": substituir_primeira("-inf 64\n"),
    "overflow_numerico": substituir_primeira("1e309 64\n"),
    "underflow_para_zero": substituir_primeira("1e-999 64\n"),
    "magnitude_fora_do_histograma": substituir_primeira("1e308 64\n"),
}

for _nome, _transformacao in CASOS_INVALIDOS.items():
    adicionar_teste_invalido(_nome, _transformacao)


if __name__ == "__main__":
    unittest.main(verbosity=2)
