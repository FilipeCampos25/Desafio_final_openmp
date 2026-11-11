#!/usr/bin/env python3
"""Benchmark reproduzivel das versoes sequencial e OpenMP.

O cronometro mede o processo completo: criacao do processo, inicializacao,
leitura do arquivo, construcao dos histogramas, calculos e escrita da saida.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import math
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RESULTADO_RE = re.compile(
    r"^(estatura|peso) media=([-+0-9.eE]+) (?:cm|kg) "
    r"desvio_padrao=([-+0-9.eE]+) (?:cm|kg) cv=([-+0-9.eE]+) %$"
)


def executavel(caminho: Path) -> Path:
    if caminho.is_file():
        return caminho
    if os.name == "nt" and caminho.with_suffix(".exe").is_file():
        return caminho.with_suffix(".exe")
    raise FileNotFoundError(f"executavel nao encontrado: {caminho}")


def sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def executar_comando(comando: list[str]) -> str:
    try:
        processo = subprocess.run(
            comando, cwd=ROOT, capture_output=True, text=True,
            timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as erro:
        return f"indisponivel ({erro})"
    texto = (processo.stdout or processo.stderr).strip()
    return texto.splitlines()[0] if texto else f"codigo {processo.returncode}"


def cpu_modelo() -> str:
    if os.name == "nt":
        comando = [
            "powershell", "-NoProfile", "-Command",
            "(Get-CimInstance Win32_Processor | Select-Object -First 1 "
            "-ExpandProperty Name).Trim()",
        ]
        modelo = executar_comando(comando)
        if not modelo.startswith("indisponivel"):
            return modelo
    if Path("/proc/cpuinfo").is_file():
        for linha in Path("/proc/cpuinfo").read_text(
                encoding="utf-8", errors="replace").splitlines():
            if linha.lower().startswith("model name"):
                return linha.split(":", 1)[1].strip()
    return platform.processor() or "nao informado pelo sistema"


def analisar_saida(saida: str) -> dict[str, dict[str, float]]:
    resultado: dict[str, dict[str, float]] = {}
    for linha in saida.splitlines():
        correspondencia = RESULTADO_RE.fullmatch(linha.strip())
        if correspondencia is None:
            raise RuntimeError(f"saida inesperada do executavel: {linha!r}")
        variavel, media, desvio, cv = correspondencia.groups()
        resultado[variavel] = {
            "media": float(media),
            "desvio_padrao": float(desvio),
            "cv": float(cv),
        }
    if set(resultado) != {"estatura", "peso"}:
        raise RuntimeError("saida nao contem estatura e peso exatamente uma vez")
    return resultado


def medir(caminho_executavel: Path, dados: Path,
          threads: int | None) -> tuple[int, dict[str, dict[str, float]]]:
    ambiente = os.environ.copy()
    if threads is not None:
        ambiente["OMP_NUM_THREADS"] = str(threads)
        ambiente["OMP_DYNAMIC"] = "FALSE"
    inicio = time.perf_counter_ns()
    processo = subprocess.run(
        [str(caminho_executavel), str(dados)], cwd=ROOT, env=ambiente,
        capture_output=True, text=True, timeout=30, check=False,
    )
    fim = time.perf_counter_ns()
    if processo.returncode != 0:
        raise RuntimeError(
            f"{caminho_executavel} falhou (codigo {processo.returncode})\n"
            f"stdout: {processo.stdout}\nstderr: {processo.stderr}"
        )
    return fim - inicio, analisar_saida(processo.stdout)


def estatisticas_consistentes(
        referencia: dict[str, dict[str, float]],
        atual: dict[str, dict[str, float]]) -> bool:
    return all(
        math.isclose(referencia[variavel][medida], atual[variavel][medida],
                     rel_tol=1e-9, abs_tol=5e-7)
        for variavel in ("estatura", "peso")
        for medida in ("media", "desvio_padrao", "cv")
    )


def escrever_csv(caminho: Path, campos: list[str], linhas: list[dict]) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("dados/pessoas.txt"))
    parser.add_argument("--sequential", type=Path,
                        default=Path("bin/base/cv_sequencial"))
    parser.add_argument("--openmp", type=Path,
                        default=Path("bin/openmp/cv_openmp"))
    parser.add_argument("--threads", default="1,2,4")
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=Path("resultados"))
    parser.add_argument("--compiler", default=os.environ.get("CXX", "g++"))
    parser.add_argument(
        "--compiler-flags",
        default="-O2 -std=c++17 -Wall -Wextra -Wpedantic; OpenMP: -fopenmp",
    )
    return parser.parse_args()


def main() -> int:
    args = argumentos()
    if args.repetitions < 2 or args.warmups < 0:
        raise ValueError("repetitions deve ser >= 2 e warmups deve ser >= 0")
    threads = [int(item) for item in args.threads.split(",")]
    if not threads or any(item <= 0 for item in threads):
        raise ValueError("threads deve conter inteiros positivos separados por virgula")

    dados = args.data.resolve()
    sequencial = executavel(args.sequential.resolve())
    openmp = executavel(args.openmp.resolve())
    if not dados.is_file():
        raise FileNotFoundError(f"arquivo de dados nao encontrado: {dados}")

    configuracoes = [("sequencial", sequencial, None)] + [
        (f"openmp_{quantidade}_thread" + ("" if quantidade == 1 else "s"),
         openmp, quantidade)
        for quantidade in threads
    ]

    referencia = None
    resultados_configuracao: dict[str, dict[str, dict[str, float]]] = {}
    for nome, caminho, quantidade in configuracoes:
        for _ in range(args.warmups):
            _, atual = medir(caminho, dados, quantidade)
        if referencia is None:
            referencia = atual
        if not estatisticas_consistentes(referencia, atual):
            raise RuntimeError(f"estatisticas divergentes no aquecimento: {nome}")
        resultados_configuracao[nome] = atual

    instante = datetime.now(timezone.utc).isoformat(timespec="seconds")
    hash_dados = sha256(dados)
    medicoes: list[dict] = []
    # Rotacionar a ordem reduz o vies sistematico de aquecimento/temperatura.
    for repeticao in range(1, args.repetitions + 1):
        deslocamento = (repeticao - 1) % len(configuracoes)
        ordem = configuracoes[deslocamento:] + configuracoes[:deslocamento]
        for ordem_rodada, (nome, caminho, quantidade) in enumerate(ordem, start=1):
            duracao_ns, atual = medir(caminho, dados, quantidade)
            if not estatisticas_consistentes(referencia, atual):
                raise RuntimeError(
                    f"estatisticas divergentes: {nome}, repeticao {repeticao}"
                )
            medicoes.append({
                "timestamp_utc": instante,
                "configuracao": nome,
                "implementacao": "sequencial" if quantidade is None else "openmp",
                "threads": 1 if quantidade is None else quantidade,
                "repeticao": repeticao,
                "ordem_na_rodada": ordem_rodada,
                "tempo_ns": duracao_ns,
                "tempo_ms": f"{duracao_ns / 1_000_000:.6f}",
                "dados_sha256": hash_dados,
            })

    por_configuracao = {
        nome: [linha["tempo_ns"] for linha in medicoes
               if linha["configuracao"] == nome]
        for nome, _, _ in configuracoes
    }
    media_sequencial = statistics.mean(por_configuracao["sequencial"])
    resumo: list[dict] = []
    for nome, _, quantidade in configuracoes:
        valores = por_configuracao[nome]
        media = statistics.mean(valores)
        resumo.append({
            "configuracao": nome,
            "implementacao": "sequencial" if quantidade is None else "openmp",
            "threads": 1 if quantidade is None else quantidade,
            "n": len(valores),
            "media_ns": f"{media:.3f}",
            "mediana_ns": f"{statistics.median(valores):.3f}",
            "desvio_padrao_amostral_ns": f"{statistics.stdev(valores):.3f}",
            "minimo_ns": min(valores),
            "maximo_ns": max(valores),
            "media_ms": f"{media / 1_000_000:.6f}",
            "mediana_ms": f"{statistics.median(valores) / 1_000_000:.6f}",
            "desvio_padrao_amostral_ms":
                f"{statistics.stdev(valores) / 1_000_000:.6f}",
            "speedup_vs_sequencial": f"{media_sequencial / media:.6f}",
        })

    estatisticas_saida: list[dict] = []
    for nome, _, quantidade in configuracoes:
        for variavel in ("estatura", "peso"):
            valores = resultados_configuracao[nome][variavel]
            estatisticas_saida.append({
                "configuracao": nome,
                "threads": 1 if quantidade is None else quantidade,
                "variavel": variavel,
                "media_ponderada": f"{valores['media']:.6f}",
                "desvio_padrao_populacional": f"{valores['desvio_padrao']:.6f}",
                "cv_percentual": f"{valores['cv']:.6f}",
            })

    saida = args.output_dir.resolve()
    saida.mkdir(parents=True, exist_ok=True)
    escrever_csv(
        saida / "benchmark_medicoes.csv",
        ["timestamp_utc", "configuracao", "implementacao", "threads",
         "repeticao", "ordem_na_rodada", "tempo_ns", "tempo_ms",
         "dados_sha256"],
        medicoes,
    )
    escrever_csv(
        saida / "benchmark_resumo.csv",
        ["configuracao", "implementacao", "threads", "n", "media_ns",
         "mediana_ns", "desvio_padrao_amostral_ns", "minimo_ns",
         "maximo_ns", "media_ms", "mediana_ms",
         "desvio_padrao_amostral_ms", "speedup_vs_sequencial"],
        resumo,
    )
    escrever_csv(
        saida / "estatisticas.csv",
        ["configuracao", "threads", "variavel", "media_ponderada",
         "desvio_padrao_populacional", "cv_percentual"],
        estatisticas_saida,
    )

    git_commit = executar_comando(["git", "rev-parse", "HEAD"])
    git_status = executar_comando(["git", "status", "--short"])
    compilador = executar_comando([args.compiler, "--version"])
    docker = (executar_comando(["docker", "version", "--format",
                               "client={{.Client.Version}} server={{.Server.Version}}"])
              if shutil.which("docker") else "indisponivel no PATH; benchmark fora de Docker")
    ambiente = [
        f"timestamp_utc={instante}",
        f"escopo_tempo=processo completo: criacao, inicializacao, leitura de {dados.name}, "
        "histogramas, calculos e escrita em stdout capturado",
        "relogio=time.perf_counter_ns() (monotonico, alta resolucao)",
        f"repeticoes_por_configuracao={args.repetitions}",
        f"aquecimentos_nao_registrados_por_configuracao={args.warmups}",
        f"threads_openmp={','.join(map(str, threads))}",
        "OMP_DYNAMIC=FALSE",
        f"sistema={platform.platform()}",
        f"arquitetura={platform.machine()}",
        f"processador={cpu_modelo()}",
        f"cpus_logicas={os.cpu_count()}",
        f"python={platform.python_version()}",
        f"compilador={compilador}",
        f"flags_compilacao={args.compiler_flags}",
        f"docker={docker}",
        f"git_commit={git_commit}",
        f"git_status_antes_dos_resultados={git_status or 'limpo'}",
        f"dados={dados}",
        f"dados_sha256={hash_dados}",
        f"sequencial={sequencial}",
        f"sequencial_sha256={sha256(sequencial)}",
        f"openmp={openmp}",
        f"openmp_sha256={sha256(openmp)}",
    ]
    (saida / "benchmark_ambiente.txt").write_text(
        "\n".join(ambiente) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"Benchmark concluido: {len(medicoes)} medicoes em {saida}")
    for linha in resumo:
        print(
            f"{linha['configuracao']}: media={linha['media_ms']} ms, "
            f"mediana={linha['mediana_ms']} ms, "
            f"speedup={linha['speedup_vs_sequencial']}x"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        raise SystemExit(1)
