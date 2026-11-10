#include "dados.hpp"

#include <cmath>
#include <climits>
#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>

namespace dados {
namespace {

bool positivo_finito(double valor) {
    return std::isfinite(valor) && valor > 0.0;
}

}  // namespace

std::vector<Pessoa> ler_pessoas(const std::string& caminho) {
    std::ifstream entrada(caminho);
    if (!entrada) {
        throw std::runtime_error("arquivo nao encontrado: " + caminho);
    }

    std::vector<Pessoa> pessoas;
    std::string linha;
    std::size_t numero_linha = 0;
    while (std::getline(entrada, linha)) {
        ++numero_linha;
        std::istringstream registro(linha);
        Pessoa pessoa{};
        std::string excedente;
        if (!(registro >> pessoa.estatura_cm >> pessoa.peso_kg) ||
            (registro >> excedente)) {
            throw std::runtime_error("linha " + std::to_string(numero_linha) +
                                     " malformada: esperado estatura peso");
        }
        if (!positivo_finito(pessoa.estatura_cm) ||
            !positivo_finito(pessoa.peso_kg)) {
            throw std::runtime_error("linha " + std::to_string(numero_linha) +
                                     ": valores devem ser positivos e finitos");
        }
        pessoas.push_back(pessoa);
    }

    if (pessoas.size() != kQuantidadePessoas) {
        throw std::runtime_error("esperado 1000 registros; recebido " +
                                 std::to_string(pessoas.size()));
    }
    return pessoas;
}

std::vector<ClasseFrequencia> construir_histograma(
    const std::vector<double>& valores, double largura_classe) {
    if (!std::isfinite(largura_classe) || largura_classe <= 0.0) {
        throw std::invalid_argument("largura da classe deve ser positiva e finita");
    }

    std::map<long long, std::size_t> frequencias;
    for (double valor : valores) {
        if (!positivo_finito(valor)) {
            throw std::invalid_argument("histograma recebeu valor nao positivo ou nao finito");
        }
        const double indice_real = std::floor(valor / largura_classe);
        // O cast de LLONG_MAX para double pode arredondar para 2^63; por isso
        // o limite superior e exclusivo.
        if (indice_real < static_cast<double>(LLONG_MIN) ||
            indice_real >= static_cast<double>(LLONG_MAX)) {
            throw std::overflow_error("valor fora do intervalo suportado");
        }
        ++frequencias[static_cast<long long>(indice_real)];
    }

    std::vector<ClasseFrequencia> classes;
    classes.reserve(frequencias.size());
    for (const auto& [indice, frequencia] : frequencias) {
        const double inferior = static_cast<double>(indice) * largura_classe;
        const double superior = inferior + largura_classe;
        classes.push_back(
            {inferior, superior, inferior + largura_classe / 2.0, frequencia});
    }
    return classes;
}

std::vector<ClasseFrequencia> histograma_estaturas(
    const std::vector<Pessoa>& pessoas) {
    std::vector<double> valores;
    valores.reserve(pessoas.size());
    for (const Pessoa& pessoa : pessoas) {
        valores.push_back(pessoa.estatura_cm);
    }
    return construir_histograma(valores, kLarguraClasseEstatura);
}

std::vector<ClasseFrequencia> histograma_pesos(
    const std::vector<Pessoa>& pessoas) {
    std::vector<double> valores;
    valores.reserve(pessoas.size());
    for (const Pessoa& pessoa : pessoas) {
        valores.push_back(pessoa.peso_kg);
    }
    return construir_histograma(valores, kLarguraClassePeso);
}

std::size_t total_frequencias(
    const std::vector<ClasseFrequencia>& classes) {
    std::size_t total = 0;
    for (const ClasseFrequencia& classe : classes) {
        total += classe.frequencia;
    }
    return total;
}

}  // namespace dados
