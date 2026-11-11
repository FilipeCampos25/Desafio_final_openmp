#include "dados.hpp"

#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Estatisticas {
    double media;
    double desvio_padrao;
    double coeficiente_variacao;
};

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

    // Cada ponto medio xi representa todos os fi elementos da sua classe.
    // Portanto, fi pondera a contribuicao de xi para a media agrupada.
    double soma_ponderada = 0.0;
    for (const dados::ClasseFrequencia& classe : classes) {
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

    // Desvio populacional para dados agrupados: cada distancia (xi - media)^2
    // tambem aparece fi vezes. A divisao usa N, e nao N - 1.
    double soma_desvios_ponderados = 0.0;
    for (const dados::ClasseFrequencia& classe : classes) {
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
    // Uma linha por variavel e chaves estaveis facilitam a leitura por scripts.
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

        // Reutiliza integralmente a convencao e a construcao dos histogramas
        // da Issue #1: classes semiabertas de 8 cm e 4 kg.
        const auto classes_estatura = dados::histograma_estaturas(pessoas);
        const auto classes_peso = dados::histograma_pesos(pessoas);

        const Estatisticas estatura =
            calcular_estatisticas(classes_estatura, "estatura");
        const Estatisticas peso = calcular_estatisticas(classes_peso, "peso");

        std::cout << std::fixed << std::setprecision(6);
        exibir_resultado("estatura", "cm", estatura);
        exibir_resultado("peso", "kg", peso);
    } catch (const std::exception& erro) {
        std::cerr << "Erro: " << erro.what() << '\n';
        return 1;
    }

    return 0;
}
