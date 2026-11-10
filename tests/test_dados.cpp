#include "dados.hpp"

#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

int main() {
    const auto classes8 = dados::construir_histograma(
        {7.999, 8.0, 15.999, 16.0, 23.999}, 8.0);
    assert(classes8.size() == 3);
    assert(classes8[0].limite_inferior == 0.0);
    assert(classes8[0].limite_superior == 8.0);
    assert(classes8[0].ponto_medio == 4.0);
    assert(classes8[0].frequencia == 1);
    assert(classes8[1].limite_inferior == 8.0);
    assert(classes8[1].frequencia == 2);
    assert(classes8[2].limite_inferior == 16.0);
    assert(classes8[2].frequencia == 2);

    const auto classes4 = dados::construir_histograma(
        {3.999, 4.0, 7.999, 8.0}, 4.0);
    assert(classes4.size() == 3);
    assert(classes4[0].frequencia == 1);
    assert(classes4[1].frequencia == 2);
    assert(classes4[2].frequencia == 1);
    assert(dados::total_frequencias(classes4) == 4);

    bool rejeitou = false;
    try {
        (void)dados::construir_histograma({1.0, NAN}, 4.0);
    } catch (const std::invalid_argument&) {
        rejeitou = true;
    }
    assert(rejeitou);

    const auto pessoas = dados::ler_pessoas("dados/pessoas.txt");
    assert(pessoas.size() == dados::kQuantidadePessoas);
    const auto estaturas = dados::histograma_estaturas(pessoas);
    const auto pesos = dados::histograma_pesos(pessoas);
    assert(dados::total_frequencias(estaturas) == 1000);
    assert(dados::total_frequencias(pesos) == 1000);
    for (const auto& classe : estaturas) {
        assert(classe.limite_superior - classe.limite_inferior == 8.0);
    }
    for (const auto& classe : pesos) {
        assert(classe.limite_superior - classe.limite_inferior == 4.0);
    }

    std::cout << "OK: leitura, fronteiras e histogramas validados.\n";
}
