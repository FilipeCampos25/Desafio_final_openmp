#!/usr/bin/env python3
"""Gera o relatorio final a partir dos resultados CSV versionados."""

from __future__ import annotations

import csv
from pathlib import Path

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, PageBreak, Paragraph, Spacer, Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
RESUMO = ROOT / "resultados" / "benchmark_resumo.csv"
ESTATISTICAS = ROOT / "resultados" / "estatisticas.csv"
AMBIENTE = ROOT / "resultados" / "benchmark_ambiente.txt"
SAIDA = ROOT / "docs" / "relatorio_desempenho_openmp.pdf"

AZUL = colors.HexColor("#173B57")
CIANO = colors.HexColor("#2B7A9B")
CINZA = colors.HexColor("#52606D")
FUNDO = colors.HexColor("#F5F7F9")


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def ler_ambiente() -> dict[str, str]:
    resultado = {}
    for linha in AMBIENTE.read_text(encoding="utf-8").splitlines():
        if "=" in linha:
            chave, valor = linha.split("=", 1)
            resultado[chave] = valor
    return resultado


def estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "Titulo", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=23, leading=28, textColor=AZUL, alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "subtitulo": ParagraphStyle(
            "Subtitulo", parent=base["Normal"], fontName="Helvetica",
            fontSize=12, leading=17, textColor=CINZA, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=15, leading=19, textColor=AZUL, spaceBefore=11,
            spaceAfter=7, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=11.5, leading=15, textColor=CIANO, spaceBefore=8,
            spaceAfter=5, keepWithNext=True,
        ),
        "corpo": ParagraphStyle(
            "Corpo", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.4, leading=13.2, textColor=colors.HexColor("#202A33"),
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "nota": ParagraphStyle(
            "Nota", parent=base["BodyText"], fontName="Helvetica-Oblique",
            fontSize=8.5, leading=12, textColor=CINZA, leftIndent=9,
            rightIndent=9, spaceBefore=3, spaceAfter=8,
        ),
        "formula": ParagraphStyle(
            "Formula", parent=base["BodyText"], fontName="Courier",
            fontSize=9, leading=13, textColor=AZUL, leftIndent=15,
            backColor=FUNDO, borderPadding=7, spaceBefore=4, spaceAfter=7,
        ),
        "celula": ParagraphStyle(
            "Celula", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.8, leading=10, alignment=TA_LEFT,
        ),
        "cabecalho": ParagraphStyle(
            "Cabecalho", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.6, leading=9.5, textColor=colors.white,
            alignment=TA_CENTER,
        ),
    }


def tabela(dados, larguras, estilo_celula, estilo_cabecalho):
    linhas = []
    for indice, linha in enumerate(dados):
        estilo = estilo_cabecalho if indice == 0 else estilo_celula
        linhas.append([Paragraph(str(item), estilo) for item in linha])
    resultado = Table(linhas, colWidths=larguras, repeatRows=1, hAlign="LEFT")
    resultado.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4CC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return resultado


def grafico_tempos(resumo: list[dict[str, str]]) -> Drawing:
    desenho = Drawing(460, 210)
    grafico = VerticalBarChart()
    grafico.x = 48
    grafico.y = 42
    grafico.height = 135
    grafico.width = 380
    grafico.data = [[float(linha["media_ms"]) for linha in resumo]]
    grafico.categoryAxis.categoryNames = ["Seq.", "OMP 1", "OMP 2", "OMP 4"]
    grafico.categoryAxis.labels.fontName = "Helvetica"
    grafico.categoryAxis.labels.fontSize = 8
    grafico.valueAxis.valueMin = 0
    grafico.valueAxis.valueMax = max(grafico.data[0]) * 1.25
    grafico.valueAxis.valueStep = 5
    grafico.valueAxis.labels.fontName = "Helvetica"
    grafico.valueAxis.labels.fontSize = 7
    grafico.bars[0].fillColor = CIANO
    grafico.bars[0].strokeColor = AZUL
    desenho.add(grafico)
    desenho.add(String(15, 105, "Tempo (ms)", fontName="Helvetica", fontSize=8,
                       fillColor=CINZA, angle=90))
    desenho.add(String(155, 8, "Configuracao", fontName="Helvetica",
                       fontSize=8, fillColor=CINZA))
    desenho.add(String(72, 190, "Media de 30 medicoes do processo completo",
                       fontName="Helvetica-Bold", fontSize=9, fillColor=AZUL))
    return desenho


def cabecalho_rodape(canvas, documento):
    canvas.saveState()
    largura, altura = A4
    if documento.page > 1:
        canvas.setStrokeColor(colors.HexColor("#C8D3DA"))
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, altura - 1.35 * cm, largura - 2 * cm,
                    altura - 1.35 * cm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(CINZA)
        canvas.drawString(2 * cm, altura - 1.1 * cm,
                          "Desafio Final 009 - Analise de Dados com OpenMP")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(CINZA)
    canvas.drawString(2 * cm, 1.05 * cm,
                      "Programacao Paralela (CCO085) - IESB 2026/2")
    canvas.drawRightString(largura - 2 * cm, 1.05 * cm,
                           f"Pagina {documento.page}")
    canvas.restoreState()


def gerar() -> None:
    resumo = ler_csv(RESUMO)
    estatisticas = ler_csv(ESTATISTICAS)
    ambiente = ler_ambiente()
    if len(resumo) != 4 or len(estatisticas) != 8:
        raise RuntimeError("resultados incompletos; execute make benchmark")

    s = estilos()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    documento = BaseDocTemplate(
        str(SAIDA), pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.7 * cm, bottomMargin=1.7 * cm,
        title="Relatorio de desempenho OpenMP - Desafio Final 009",
        author="Responsavel pelo repositorio FilipeCampos25",
        subject="Coeficiente de variacao sequencial e paralelo com OpenMP",
    )
    frame = Frame(documento.leftMargin, documento.bottomMargin,
                  documento.width, documento.height, id="conteudo")
    documento.addPageTemplates([
        PageTemplate(id="padrao", frames=[frame], onPage=cabecalho_rodape)
    ])

    historia = [
        Spacer(1, 3.0 * cm),
        Paragraph("IESB - Programacao Paralela (CCO085)", s["subtitulo"]),
        Spacer(1, 0.5 * cm),
        Paragraph("Desafio Final 009", s["titulo"]),
        Paragraph("Analise de Dados com OpenMP", s["titulo"]),
        Spacer(1, 0.7 * cm),
        Paragraph("Relatorio de implementacao, resultados estatisticos e desempenho",
                  s["subtitulo"]),
        Spacer(1, 2.1 * cm),
        tabela([
            ["Identificacao", "Informacao confirmada"],
            ["Disciplina", "Programacao Paralela (CCO085)"],
            ["Instituicao / periodo", "IESB / 2026-2"],
            ["Professor", "Rodrigo Goncalves Pinto"],
            ["Projeto", "Exercicio Final: Analise de Dados com OpenMP"],
            ["Integrantes", "Nao informados nos arquivos versionados"],
            ["Repositorio", "github.com/FilipeCampos25/Desafio_final_openmp"],
        ], [4.3 * cm, 11.2 * cm], s["celula"], s["cabecalho"]),
        Spacer(1, 1.4 * cm),
        Paragraph("Brasilia - novembro de 2026", s["subtitulo"]),
        PageBreak(),
        Paragraph("1. Objetivo", s["h1"]),
        Paragraph(
            "O objetivo e calcular a media ponderada, o desvio padrao "
            "populacional e o coeficiente de variacao (CV) da estatura e do "
            "peso de 1000 pessoas, agrupando os valores em classes. O exercicio "
            "tambem compara uma implementacao sequencial com uma implementacao "
            "paralela em C++17/OpenMP, verificando corretude e desempenho.",
            s["corpo"]),
        Paragraph("2. Dados e intervalos de classe", s["h1"]),
        Paragraph(
            "A entrada usada possui exatamente 1000 pares estatura-peso. Ela e "
            "sintetica, deterministica, gerada com semente 20261110 e nao foi "
            "fornecida pelo professor. Portanto, os numeros deste relatorio nao "
            "devem ser interpretados como estatisticas de uma populacao real ou "
            "de uma base oficial.", s["corpo"]),
        Paragraph(
            "As classes sao semiabertas [limite inferior, limite superior). A "
            "estatura usa largura de 8 cm e apresenta classes observadas de "
            "[144, 152) ate [192, 200). O peso usa largura de 4 kg e apresenta "
            "classes de [44, 48) ate [116, 120). O ponto medio xi representa "
            "os fi registros de cada classe; a soma das frequencias e 1000 em "
            "ambas as variaveis.", s["corpo"]),
        Paragraph("3. Formulas estatisticas", s["h1"]),
        Paragraph(
            "Para classes com ponto medio xi, frequencia fi e N = 1000, foram "
            "aplicadas as formulas de dados agrupados:", s["corpo"]),
        Paragraph(
            "media = sum(fi * xi) / N<br/>"
            "sigma = sqrt(sum(fi * (xi - media)^2) / N)<br/>"
            "CV(%) = 100 * sigma / media", s["formula"]),
        Paragraph(
            "O denominador da variancia e N, logo o desvio e populacional, nao "
            "amostral. O CV e adimensional e permite comparar a dispersao "
            "relativa de variaveis com unidades e medias diferentes.", s["corpo"]),
        Paragraph("4. Implementacao sequencial", s["h1"]),
        Paragraph(
            "A versao sequencial le e valida os 1000 registros, cria histogramas "
            "ordenados, calcula a soma ponderada, determina a media e percorre "
            "novamente as classes para somar os desvios quadraticos ponderados. "
            "Todas as etapas usam um unico fluxo de execucao.", s["corpo"]),
        Paragraph("5. Implementacao OpenMP", s["h1"]),
        Paragraph(
            "Na versao paralela, um parallel for calcula o indice de classe de "
            "cada registro. Reducoes min e max determinam a faixa dos indices. "
            "Em seguida, cada thread atualiza um histograma privado, eliminando "
            "corridas nas frequencias. A consolidacao percorre as classes em "
            "paralelo; cada iteracao escreve em uma posicao final exclusiva.",
            s["corpo"]),
        Paragraph(
            "As somas da media e da variancia usam reduction(+:acumulador). "
            "O OpenMP cria acumuladores privados por thread e combina os valores "
            "ao final da regiao, evitando atualizacoes concorrentes no mesmo "
            "endereco. Esses lacos podem ser paralelizados porque cada registro "
            "ou classe e processado independentemente; somente os totais precisam "
            "ser combinados. O agendamento padrao divide as iteracoes do for entre "
            "as threads da equipe e aplica uma barreira implicita ao final.",
            s["corpo"]),
        PageBreak(),
        Paragraph("6. Corretude e resultados estatisticos", s["h1"]),
        Paragraph(
            "Antes do benchmark, os testes automatizados validaram formato e "
            "quantidade da entrada, fronteiras das classes, frequencias, casos "
            "invalidos e uma referencia Python independente. O OpenMP foi "
            "executado repetidamente com 1, 2 e 4 threads. Todas as configuracoes "
            "coincidiram com a versao sequencial dentro da tolerancia definida.",
            s["corpo"]),
        tabela([
            ["Variavel", "Media ponderada", "Desvio populacional", "CV (%)"],
            ["Estatura", "172,608000 cm", "15,964408 cm", "9,248939"],
            ["Peso", "82,420000 kg", "21,799073 kg", "26,448767"],
        ], [3.4 * cm, 4.1 * cm, 4.4 * cm, 3.1 * cm], s["celula"], s["cabecalho"]),
        Spacer(1, 0.25 * cm),
        Paragraph(
            "O peso apresenta dispersao relativa maior: seu CV e cerca de 26,45%, "
            "contra 9,25% para a estatura na base sintetica.", s["nota"]),
        Paragraph("7. Metodologia do benchmark", s["h1"]),
        Paragraph(
            "O script scripts/benchmark.py usa time.perf_counter_ns(), relogio "
            "monotonico de alta resolucao. Foram realizados tres aquecimentos "
            "nao registrados e 30 ensaios por configuracao: sequencial e OpenMP "
            "com 1, 2 e 4 threads. A ordem das configuracoes foi rotacionada entre "
            "rodadas para reduzir vies sistematico de aquecimento.", s["corpo"]),
        Paragraph(
            "O tempo inclui a criacao do processo, inicializacao, leitura do "
            "mesmo arquivo pessoas.txt, construcao dos histogramas, calculos e "
            "escrita da saida capturada. OMP_DYNAMIC foi desativado. Cada execucao "
            "tambem teve suas estatisticas conferidas antes de o tempo ser aceito.",
            s["corpo"]),
        Paragraph("8. Comparacao de tempos", s["h1"]),
        tabela([
            ["Configuracao", "n", "Media (ms)", "Mediana (ms)", "DP (ms)",
             "Speedup"],
            *[[
                linha["configuracao"].replace("openmp_", "OpenMP ").replace(
                    "_threads", " threads").replace("_thread", " thread").replace(
                    "sequencial", "Sequencial"),
                linha["n"], linha["media_ms"], linha["mediana_ms"],
                linha["desvio_padrao_amostral_ms"],
                linha["speedup_vs_sequencial"] + "x",
            ] for linha in resumo],
        ], [4.0 * cm, 1.0 * cm, 2.7 * cm, 2.7 * cm, 2.5 * cm, 2.3 * cm],
            s["celula"], s["cabecalho"]),
        Spacer(1, 0.2 * cm),
        grafico_tempos(resumo),
        Paragraph(
            "Figura 1 - Medias reais registradas em benchmark_medicoes.csv. "
            "Barras menores indicam menor tempo.", s["nota"]),
        PageBreak(),
        Paragraph("9. Analise de desempenho e limitacoes", s["h1"]),
        Paragraph(
            "Nenhuma configuracao OpenMP obteve speedup maior que 1. Com uma "
            "thread, o tempo medio foi 1,66% superior ao sequencial. Com duas e "
            "quatro threads, os tempos foram aproximadamente 8,70% e 8,85% "
            "superiores. O resultado e esperado para apenas 1000 registros e "
            "poucas classes: o trabalho aritmetico de cada laco e pequeno, "
            "enquanto cada regiao paralela exige formar a equipe, distribuir "
            "iteracoes, sincronizar barreiras e combinar reducoes.", s["corpo"]),
        Paragraph(
            "A medicao do processo completo e representativa do uso do programa, "
            "mas dilui o trecho computacional no custo de criacao do processo, "
            "leitura e saida. O sistema operacional pode introduzir variacao por "
            "escalonamento, frequencia do processador, cache e tarefas em segundo "
            "plano. A amostra sintetica e pequena; cargas maiores, mais classes "
            "ou mais calculos por registro podem alterar o ponto de equilibrio. "
            "Tambem nao se deve generalizar os tempos deste host para Docker ou "
            "outros compiladores.", s["corpo"]),
        Paragraph("Ambiente medido", s["h2"]),
        tabela([
            ["Item", "Valor registrado"],
            ["Sistema", ambiente.get("sistema", "nao informado")],
            ["Processador", ambiente.get("processador", "nao informado")],
            ["CPUs logicas", ambiente.get("cpus_logicas", "nao informado")],
            ["Compilador", ambiente.get("compilador", "nao informado")],
            ["Flags", ambiente.get("flags_compilacao", "nao informado")],
            ["Docker", ambiente.get("docker", "nao informado")],
            ["Entrada SHA-256", ambiente.get("dados_sha256", "nao informado")],
        ], [3.7 * cm, 11.8 * cm], s["celula"], s["cabecalho"]),
        Paragraph("10. Conclusao", s["h1"]),
        Paragraph(
            "As implementacoes sequencial e OpenMP calcularam corretamente as "
            "estatisticas agrupadas da base sintetica. A paralelizacao e segura "
            "porque usa iteracoes independentes, histogramas privados e reducoes. "
            "Entretanto, neste tamanho de entrada, a sobrecarga foi maior que o "
            "trabalho economizado, e a versao sequencial apresentou o menor tempo "
            "medio. O resultado demonstra que corretude e paralelismo nao "
            "garantem aceleracao: granularidade e custo de coordenacao precisam "
            "ser considerados.", s["corpo"]),
        Paragraph("11. Reprodutibilidade", s["h1"]),
        Paragraph(
            "Os comandos make test e make benchmark recompilam, validam e medem "
            "o projeto. Os tempos individuais, o resumo, as estatisticas, hashes "
            "e o ambiente estao em resultados/. Este PDF pode ser recriado com "
            "python3 scripts/gerar_relatorio.py. O README descreve todo o fluxo.",
            s["corpo"]),
        Paragraph("Arquivos consultados", s["h2"]),
        Paragraph(
            "CHECKLIST.md; README.md; Dockerfile; Makefile; dados/README.md; "
            "include/dados.hpp; src/dados.cpp; cv_sequencial.cpp; cv_openmp.cpp; "
            "tests/; resultados/benchmark_resumo.csv; "
            "resultados/benchmark_ambiente.txt; resultados/estatisticas.csv.",
            s["corpo"]),
    ]
    documento.build(historia)
    print(f"Relatorio gerado em {SAIDA}")


if __name__ == "__main__":
    gerar()
