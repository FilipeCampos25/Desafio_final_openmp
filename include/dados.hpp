#ifndef DESAFIO_FINAL_OPENMP_DADOS_HPP
#define DESAFIO_FINAL_OPENMP_DADOS_HPP

#include <cstddef>
#include <string>
#include <vector>

namespace dados {

constexpr std::size_t kQuantidadePessoas = 1000;
constexpr double kLarguraClasseEstatura = 8.0;
constexpr double kLarguraClassePeso = 4.0;

struct Pessoa {
    double estatura_cm;
    double peso_kg;
};

struct ClasseFrequencia {
    double limite_inferior;
    double limite_superior;
    double ponto_medio;
    std::size_t frequencia;
};

// Le exatamente kQuantidadePessoas registros "estatura peso".
// Lanca std::runtime_error se o arquivo ou qualquer registro for invalido.
std::vector<Pessoa> ler_pessoas(const std::string& caminho);

// Constroi classes semiabertas [inferior, superior), alinhadas a largura:
// [..., -largura, 0), [0, largura), [largura, 2*largura), ...
std::vector<ClasseFrequencia> construir_histograma(
    const std::vector<double>& valores, double largura_classe);

std::vector<ClasseFrequencia> histograma_estaturas(
    const std::vector<Pessoa>& pessoas);
std::vector<ClasseFrequencia> histograma_pesos(
    const std::vector<Pessoa>& pessoas);

std::size_t total_frequencias(
    const std::vector<ClasseFrequencia>& classes);

}  // namespace dados

#endif
