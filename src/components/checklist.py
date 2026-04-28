"""
Checklist Diário de Cozinha com geração de link WhatsApp.
"""

import streamlit as st
from datetime import datetime, date
from src.services.sheets import ler_todos, inserir, proximo_id, atualizar_campo, get_config
from src.services.auth import get_usuario
from src.utils.whatsapp import link_checklist_cozinha

# Itens padrão do checklist por categoria
ITENS_PADRAO = {
    "Abertura": [
        "Ligar equipamentos (fogão, forno, fritadeira)",
        "Verificar temperatura da câmara fria",
        "Conferir estoque do dia",
        "Higienizar bancadas e utensílios",
        "Verificar validade dos insumos",
    ],
    "Mise en Place": [
        "Cortar e preparar legumes do dia",
        "Descongelar proteínas necessárias",
        "Preparar fundos e molhos base",
        "Separar ingredientes das fichas técnicas",
        "Porcionar e etiquetar preparações",
    ],
    "Higiene": [
        "Lavar e higienizar hortaliças",
        "Trocar água de manutenção de equipamentos",
        "Verificar limpeza dos utensílios",
        "Conferir EPIs da equipe",
    ],
    "Encerramento": [
        "Armazenar sobras corretamente (etiquetar)",
        "Limpar e desligar equipamentos",
        "Varrer e lavar piso da cozinha",
        "Registrar sobras e perdas do dia",
        "Conferir fechamento do estoque",
    ],
}


def render_checklist():
    st.markdown("## ✅ Checklist Diário de Cozinha")
    st.markdown("---")

    usuario = get_usuario()
    responsavel = usuario.get("Nome", "Equipe") if usuario else "Equipe"
    hoje = date.today().strftime("%d/%m/%Y")

    # Verificar se já existe checklist para hoje
    try:
        registros_hoje = [
            r for r in ler_todos("checklist_cozinha")
            if r.get("Data") == hoje
        ]
    except Exception:
        registros_hoje = []

    # Turno
    hora_atual = datetime.now().hour
    turno_padrao = "Manhã" if hora_atual < 14 else ("Tarde" if hora_atual < 20 else "Noite")

    col_info1, col_info2, col_info3 = st.columns(3)
    col_info1.metric("📅 Data", hoje)
    col_info2.metric("👤 Responsável", responsavel)
    col_info3.metric("🕐 Turno", turno_padrao)

    st.markdown("---")

    # Construir estado do checklist
    if "checklist_state" not in st.session_state:
        st.session_state["checklist_state"] = {}

    # Pré-preencher com registros existentes
    for reg in registros_hoje:
        item_key = f"{reg.get('Categoria')}_{reg.get('Item')}"
        st.session_state["checklist_state"][item_key] = reg.get("Concluido", "Não") == "Sim"

    total_itens = sum(len(v) for v in ITENS_PADRAO.values())
    concluidos_count = sum(1 for v in st.session_state["checklist_state"].values() if v)
    progresso = concluidos_count / total_itens if total_itens > 0 else 0

    # Barra de progresso geral
    st.markdown(f"**Progresso: {concluidos_count}/{total_itens} itens concluídos**")
    st.progress(progresso)

    if progresso == 1.0:
        st.success("🎉 Checklist 100% concluído!")

    st.markdown("---")

    # Renderizar por categoria
    for categoria, itens in ITENS_PADRAO.items():
        cat_concluidos = sum(
            1 for item in itens
            if st.session_state["checklist_state"].get(f"{categoria}_{item}", False)
        )
        with st.expander(f"**{categoria}** — {cat_concluidos}/{len(itens)}", expanded=True):
            for item in itens:
                item_key = f"{categoria}_{item}"
                atual = st.session_state["checklist_state"].get(item_key, False)
                novo = st.checkbox(item, value=atual, key=f"chk_{item_key}")
                st.session_state["checklist_state"][item_key] = novo

    st.markdown("---")

    # Botões de ação
    col_salvar, col_whatsapp = st.columns(2)

    with col_salvar:
        if st.button("💾 Salvar Checklist", type="primary", use_container_width=True):
            _salvar_checklist(hoje, turno_padrao, responsavel, registros_hoje)

    with col_whatsapp:
        numero_cozinha = get_config("whatsapp_cozinha")
        if numero_cozinha:
            itens_ok = [
                item for cat, itens in ITENS_PADRAO.items()
                for item in itens
                if st.session_state["checklist_state"].get(f"{cat}_{item}", False)
            ]
            itens_nok = [
                item for cat, itens in ITENS_PADRAO.items()
                for item in itens
                if not st.session_state["checklist_state"].get(f"{cat}_{item}", False)
            ]
            link = link_checklist_cozinha(numero_cozinha, hoje, turno_padrao,
                                          itens_ok, itens_nok)
            st.link_button("📲 Enviar via WhatsApp", link, use_container_width=True)
        else:
            st.caption("Configure o WhatsApp nas configurações do sistema.")

    # Histórico
    st.markdown("---")
    st.markdown("### 📊 Histórico dos Últimos 7 Dias")
    try:
        historico = ler_todos("checklist_cozinha")
        if historico:
            import pandas as pd
            df = pd.DataFrame(historico)
            if not df.empty:
                resumo = df.groupby("Data").apply(
                    lambda x: f"{(x['Concluido']=='Sim').sum()}/{len(x)}"
                ).reset_index()
                resumo.columns = ["Data", "Progresso"]
                st.dataframe(resumo.tail(7), use_container_width=True, hide_index=True)
    except Exception:
        pass


def _salvar_checklist(hoje, turno, responsavel, registros_existentes):
    """Salva ou atualiza os itens do checklist no Google Sheets."""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    itens_existentes = {
        f"{r.get('Categoria')}_{r.get('Item')}": r.get("ID")
        for r in registros_existentes
    }

    salvos = 0
    for categoria, itens in ITENS_PADRAO.items():
        for item in itens:
            item_key = f"{categoria}_{item}"
            concluido = st.session_state["checklist_state"].get(item_key, False)
            concluido_str = "Sim" if concluido else "Não"
            hora_conclusao = agora if concluido else ""

            if item_key in itens_existentes:
                reg_id = str(itens_existentes[item_key])
                atualizar_campo("checklist_cozinha", reg_id, "Concluido", concluido_str)
                atualizar_campo("checklist_cozinha", reg_id, "Hora_Conclusao", hora_conclusao)
            else:
                novo_id = proximo_id("checklist_cozinha")
                inserir("checklist_cozinha", [
                    novo_id, hoje, turno, responsavel,
                    item, categoria, concluido_str, hora_conclusao, "", "Ativo"
                ])
            salvos += 1

    st.success(f"✅ Checklist salvo! {salvos} itens registrados.")
