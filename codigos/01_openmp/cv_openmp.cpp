#include "dados.hpp"

#include <climits>
#include <cmath>
#include <cstddef>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#include <omp.h>

namespace {

struct Estatisticas {
    double media;
    double desvio_padrao;
    double coeficiente_variacao;
};

std::vector<dados::ClasseFrequencia> construir_histograma_paralelo(
    const std::vector<double>& valores, double largura_classe) {
    if (valores.empty()) {
        return {};
    }
    if (!std::isfinite(largura_classe) || largura_classe <= 0.0) {
        throw std::invalid_argument(
            "largura da classe deve ser positiva e finita");
    }

    // A leitura compartilhada ja garante valores positivos e finitos. Este
    // teste preserva tambem a protecao contra conversoes fora de long long da
    // implementacao compartilhada do histograma sequencial.
    for (double valor : valores) {
        const double indice_real = std::floor(valor / largura_classe);
        if (indice_real < static_cast<double>(LLONG_MIN) ||
            indice_real >= static_cast<double>(LLONG_MAX)) {
            throw std::overflow_error("valor fora do intervalo suportado");
        }
    }

    // Esta regiao calcula, em paralelo, o indice da classe de cada valor.
    // Cada iteracao escreve em uma posicao diferente de indices, portanto nao
    // ha escrita concorrente. As reducoes min/max mantem copias privadas por
    // thread e o OpenMP as combina ao final para determinar a faixa de classes.
    std::vector<long long> indices(valores.size());
    long long indice_minimo = LLONG_MAX;
    long long indice_maximo = LLONG_MIN;

    #pragma omp parallel for reduction(min:indice_minimo) reduction(max:indice_maximo)
    for (std::ptrdiff_t i = 0;
         i < static_cast<std::ptrdiff_t>(valores.size()); ++i) {
        const double indice_real = std::floor(
            valores[static_cast<std::size_t>(i)] / largura_classe);
        const long long indice = static_cast<long long>(indice_real);
        indices[static_cast<std::size_t>(i)] = indice;
        if (indice < indice_minimo) {
            indice_minimo = indice;
        }
        if (indice > indice_maximo) {
            indice_maximo = indice;
        }
    }

    const auto amplitude =
        static_cast<unsigned long long>(indice_maximo) -
        static_cast<unsigned long long>(indice_minimo);
    if (amplitude >= std::numeric_limits<std::size_t>::max()) {
        throw std::overflow_error("quantidade de classes fora do suportado");
    }
    const std::size_t quantidade_classes =
        static_cast<std::size_t>(amplitude) + 1;

    // Cada thread incrementa exclusivamente o seu proprio histograma. Assim,
    // nao ha corrida nas frequencias e nao e necessario usar critical/atomic.
    // omp_get_max_threads apenas dimensiona o armazenamento; a quantidade real
    // continua sendo definida pelo ambiente, inclusive por OMP_NUM_THREADS.
    const int capacidade_threads = omp_get_max_threads();
    std::vector<std::vector<std::size_t>> histogramas_locais(
        static_cast<std::size_t>(capacidade_threads),
        std::vector<std::size_t>(quantidade_classes, 0));

    #pragma omp parallel
    {
        const int id_thread = omp_get_thread_num();
        auto& histograma_local =
            histogramas_locais[static_cast<std::size_t>(id_thread)];

        #pragma omp for
        for (std::ptrdiff_t i = 0;
             i < static_cast<std::ptrdiff_t>(indices.size()); ++i) {
            const std::size_t classe = static_cast<std::size_t>(
                indices[static_cast<std::size_t>(i)] - indice_minimo);
            ++histograma_local[classe];
        }
    }

    // Na consolidacao, cada iteracao e dona de uma classe distinta e soma as
    // parcelas privadas das threads. Logo, frequencias_consolidadas tambem nao
    // recebe duas escritas simultaneas na mesma posicao.
    std::vector<std::size_t> frequencias_consolidadas(
        quantidade_classes, 0);
    #pragma omp parallel for
    for (std::ptrdiff_t classe = 0;
         classe < static_cast<std::ptrdiff_t>(quantidade_classes); ++classe) {
        std::size_t frequencia = 0;
        for (const auto& histograma_local : histogramas_locais) {
            frequencia += histograma_local[static_cast<std::size_t>(classe)];
        }
        frequencias_consolidadas[static_cast<std::size_t>(classe)] =
            frequencia;
    }

    // A criacao do vetor final e sequencial porque push_back alteraria a mesma
    // estrutura compartilhada. Mantemos somente classes presentes, em ordem,
    // exatamente como dados::construir_histograma.
    std::vector<dados::ClasseFrequencia> classes;
    classes.reserve(quantidade_classes);
    for (std::size_t classe = 0; classe < quantidade_classes; ++classe) {
        const std::size_t frequencia = frequencias_consolidadas[classe];
        if (frequencia == 0) {
            continue;
        }
        const long long indice =
            indice_minimo + static_cast<long long>(classe);
        const double inferior =
            static_cast<double>(indice) * largura_classe;
        classes.push_back({inferior, inferior + largura_classe,
                           inferior + largura_classe / 2.0, frequencia});
    }
    return classes;
}

Estatisticas calcular_estatisticas(
    const std::vector<dados::ClasseFrequencia>& classes,
    const std::string& variavel) {
    const std::size_t total = dados::total_frequencias(classes);
    if (total != dados::kQuantidadePessoas) {
        throw std::runtime_error(
            "frequencias de " + variavel + " somam " +
            std::to_string(total) + "; esperado " +
            std::to_string(dados::kQuantidadePessoas));
    }

    // As iteracoes sao independentes: cada classe apenas fornece xi * fi.
    // reduction cria uma soma_ponderada privada por thread e combina todas com
    // adicao ao final do parallel for, evitando corrida no acumulador.
    double soma_ponderada = 0.0;
    #pragma omp parallel for reduction(+:soma_ponderada)
    for (std::ptrdiff_t i = 0;
         i < static_cast<std::ptrdiff_t>(classes.size()); ++i) {
        const auto& classe = classes[static_cast<std::size_t>(i)];
        soma_ponderada +=
            classe.ponto_medio * static_cast<double>(classe.frequencia);
    }
    const double media =
        soma_ponderada / static_cast<double>(dados::kQuantidadePessoas);

    if (media == 0.0) {
        throw std::runtime_error(
            "nao e possivel calcular o CV de " + variavel +
            ": media igual a zero");
    }

    // Com a media pronta e somente lida, os desvios de cada classe podem ser
    // calculados independentemente. A segunda reduction soma fi*(xi-media)^2
    // sem critical e preserva a formula populacional do professor (divisao N).
    double soma_desvios_ponderados = 0.0;
    #pragma omp parallel for reduction(+:soma_desvios_ponderados)
    for (std::ptrdiff_t i = 0;
         i < static_cast<std::ptrdiff_t>(classes.size()); ++i) {
        const auto& classe = classes[static_cast<std::size_t>(i)];
        const double diferenca = classe.ponto_medio - media;
        soma_desvios_ponderados +=
            static_cast<double>(classe.frequencia) * diferenca * diferenca;
    }
    const double desvio_padrao = std::sqrt(
        soma_desvios_ponderados /
        static_cast<double>(dados::kQuantidadePessoas));

    return {media, desvio_padrao, (desvio_padrao / media) * 100.0};
}

void exibir_resultado(const std::string& variavel,
                      const std::string& unidade,
                      const Estatisticas& estatisticas) {
    std::cout << variavel << " media=" << estatisticas.media << ' ' << unidade
              << " desvio_padrao=" << estatisticas.desvio_padrao << ' '
              << unidade << " cv=" << estatisticas.coeficiente_variacao
              << " %\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Uso: " << argv[0] << " <arquivo_txt>\n";
        return 1;
    }

    try {
        const std::vector<dados::Pessoa> pessoas = dados::ler_pessoas(argv[1]);

        std::vector<double> estaturas;
        std::vector<double> pesos;
        estaturas.reserve(pessoas.size());
        pesos.reserve(pessoas.size());
        for (const dados::Pessoa& pessoa : pessoas) {
            estaturas.push_back(pessoa.estatura_cm);
            pesos.push_back(pessoa.peso_kg);
        }

        // Reutilizamos as larguras e ClasseFrequencia compartilhadas. Os
        // intervalos continuam semiabertos [inferior, superior): 8 cm e 4 kg.
        const auto classes_estatura = construir_histograma_paralelo(
            estaturas, dados::kLarguraClasseEstatura);
        const auto classes_peso = construir_histograma_paralelo(
            pesos, dados::kLarguraClassePeso);

        const Estatisticas estatura =
            calcular_estatisticas(classes_estatura, "estatura");
        const Estatisticas peso =
            calcular_estatisticas(classes_peso, "peso");

        std::cout << std::fixed << std::setprecision(6);
        exibir_resultado("estatura", "cm", estatura);
        exibir_resultado("peso", "kg", peso);
    } catch (const std::exception& erro) {
        std::cerr << "Erro: " << erro.what() << '\n';
        return 1;
    }

    return 0;
}
