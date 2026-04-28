"""
Utilitário para geração de links WhatsApp pré-preenchidos.
"""

import urllib.parse
from datetime import datetime


def gerar_link_whatsapp(numero: str, mensagem: str) -> str:
    """
    Gera link wa.me com mensagem pré-preenchida.
    numero: apenas dígitos, com DDI (ex: 5511999999999)
    """
    numero_limpo = "".join(filter(str.isdigit, numero))
    mensagem_encoded = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero_limpo}?text={mensagem_encoded}"


def link_pedido_pronto(numero_cozinha: str, numero_pedido: str,
                       mesa: str, prato: str) -> str:
    """Link de alerta 'Pedido Pronto' para o garçom."""
    msg = (
        f"✅ *PEDIDO PRONTO* ✅\n\n"
        f"🍽️ Prato: *{prato}*\n"
        f"🪑 Mesa: *{mesa}*\n"
        f"📋 Pedido: *#{numero_pedido}*\n"
        f"⏰ {datetime.now().strftime('%H:%M')}\n\n"
        f"_Favor retirar na cozinha._"
    )
    return gerar_link_whatsapp(numero_cozinha, msg)


def link_checklist_cozinha(numero: str, data: str, turno: str,
                            itens_concluidos: list[str],
                            itens_pendentes: list[str]) -> str:
    """Link com resumo do checklist diário da cozinha."""
    concluidos = "\n".join([f"  ✅ {item}" for item in itens_concluidos])
    pendentes = "\n".join([f"  ⚠️ {item}" for item in itens_pendentes])

    msg = (
        f"📋 *CHECKLIST COZINHA* - {data}\n"
        f"🕐 Turno: {turno}\n\n"
    )
    if concluidos:
        msg += f"*Concluídos:*\n{concluidos}\n\n"
    if pendentes:
        msg += f"*Pendentes:*\n{pendentes}\n\n"

    total = len(itens_concluidos) + len(itens_pendentes)
    pct = int(len(itens_concluidos) / total * 100) if total > 0 else 0
    msg += f"📊 Progresso: {len(itens_concluidos)}/{total} ({pct}%)"

    return gerar_link_whatsapp(numero, msg)


def link_alerta_estoque(numero: str, insumo: str, estoque_atual: float,
                         estoque_minimo: float, unidade: str) -> str:
    """Link de alerta de estoque baixo."""
    msg = (
        f"⚠️ *ALERTA DE ESTOQUE BAIXO* ⚠️\n\n"
        f"📦 Insumo: *{insumo}*\n"
        f"📉 Estoque atual: *{estoque_atual} {unidade}*\n"
        f"🔴 Estoque mínimo: *{estoque_minimo} {unidade}*\n\n"
        f"_Providenciar reposição imediatamente._"
    )
    return gerar_link_whatsapp(numero, msg)
