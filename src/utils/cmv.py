"""
Utilitários de cálculo: CMV, Markup e conversão de unidades.
"""

from typing import Optional


# ── Conversão de Unidades ──────────────────────────────────────────────────────

CONVERSOES = {
    # Peso
    ("g", "kg"): 0.001,
    ("kg", "g"): 1000,
    ("mg", "g"): 0.001,
    ("g", "mg"): 1000,
    # Volume
    ("ml", "l"): 0.001,
    ("l", "ml"): 1000,
    ("ml", "L"): 0.001,
    ("L", "ml"): 1000,
    # Unidade (sem conversão)
    ("un", "un"): 1,
    ("pç", "pç"): 1,
}


def converter_unidade(quantidade: float, de: str, para: str) -> float:
    """Converte quantidade entre unidades. Retorna quantidade original se conversão não encontrada."""
    de = de.strip().lower()
    para = para.strip().lower()
    if de == para:
        return quantidade
    fator = CONVERSOES.get((de, para))
    if fator:
        return quantidade * fator
    # Tenta inverso
    fator_inv = CONVERSOES.get((para, de))
    if fator_inv:
        return quantidade / fator_inv
    return quantidade  # sem conversão disponível


# ── Cálculo de CMV ────────────────────────────────────────────────────────────

def calcular_custo_ingrediente(quantidade: float, unidade_uso: str,
                                custo_unitario: float, unidade_compra: str) -> float:
    """
    Calcula o custo de um ingrediente na receita.
    Converte unidade de uso para unidade de compra antes de calcular.
    """
    qtd_convertida = converter_unidade(quantidade, unidade_uso, unidade_compra)
    return round(qtd_convertida * custo_unitario, 4)


def calcular_cmv(
    custo_ingredientes: float,
    custo_mo: float = 0.0,
    margem_perda_pct: float = 5.0,
    rendimento_porcoes: int = 1,
) -> dict:
    """
    Calcula o CMV completo de uma ficha técnica.

    Args:
        custo_ingredientes: Soma do custo de todos os ingredientes (R$)
        custo_mo: Custo de mão de obra (R$)
        margem_perda_pct: Percentual de perda (%)
        rendimento_porcoes: Número de porções que a receita rende

    Returns:
        dict com todos os valores calculados
    """
    custo_perda = custo_ingredientes * (margem_perda_pct / 100)
    custo_total = custo_ingredientes + custo_mo + custo_perda
    custo_porcao = custo_total / rendimento_porcoes if rendimento_porcoes > 0 else 0

    return {
        "custo_ingredientes": round(custo_ingredientes, 2),
        "custo_mo": round(custo_mo, 2),
        "custo_perda": round(custo_perda, 2),
        "custo_total": round(custo_total, 2),
        "custo_porcao": round(custo_porcao, 2),
        "margem_perda_pct": margem_perda_pct,
        "rendimento_porcoes": rendimento_porcoes,
    }


def calcular_preco_venda(custo_porcao: float, markup: float) -> float:
    """
    Calcula o preço de venda pelo markup.
    Markup = Preço / Custo → Preço = Custo × Markup
    """
    return round(custo_porcao * markup, 2)


def calcular_cmv_percentual(custo_porcao: float, preco_venda: float) -> float:
    """CMV% = (Custo / Preço de Venda) × 100"""
    if preco_venda <= 0:
        return 0.0
    return round((custo_porcao / preco_venda) * 100, 2)


def calcular_markup(custo_porcao: float, preco_venda: float) -> float:
    """Markup = Preço de Venda / Custo"""
    if custo_porcao <= 0:
        return 0.0
    return round(preco_venda / custo_porcao, 2)


def sugerir_preco(custo_porcao: float, cmv_alvo_pct: float = 30.0) -> float:
    """
    Sugere preço de venda para atingir o CMV% alvo.
    Preço = Custo / (CMV% / 100)
    """
    if cmv_alvo_pct <= 0:
        return 0.0
    return round(custo_porcao / (cmv_alvo_pct / 100), 2)


# ── Formatação ────────────────────────────────────────────────────────────────

def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor: float) -> str:
    return f"{valor:.1f}%"
