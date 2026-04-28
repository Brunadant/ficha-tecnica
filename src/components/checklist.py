"""
Checklist Diário de Cozinha.
Rastreia quem editou cada item (Editado_Por + Hora_Conclusao).
"""

import streamlit as st
from datetime import datetime, date
from src.services.sheets import ler_todos, inserir, proximo_id, atualizar_campo, get_config
from src.services.auth import get_usuario
from src.utils.whatsapp import link_checklist_cozinha

ITENS_PADRAO = {
    "🌅 Abertura": [
        "Ligar equipamentos (fogão, forno, fritadeira)",
        "Verificar temperatura da câmara fria",
        "Conferir estoque do dia",
        "Higienizar bancadas e utensílios",
        "Verificar validade dos insumos",
    ],
    "🔪 Mise en Place": [
        "Cortar e preparar legumes do dia",
        "Descongelar proteínas necessárias",
        "Preparar fundos e molhos base",
        "Separar ingredientes das fichas técnicas",
        "Porcionar e etiquetar preparações",
    ],
    "🧼 Higiene": [
        "Lavar e higienizar hortaliças",
        "Trocar água de manutenção de equipamentos",
        "Verificar limpeza dos utensílios",
        "Conferir EPIs da equipe",
    ],
    "🌙 Encerramento": [
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
    hora_atual = datetime.now().hour
    turno_padrao = "Manhã" if hora_atual < 14 else ("Tarde" if hora_atual < 20 else "Noite")

    # Métricas de cabeçalho
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 Data", hoje)
    c2.metric("👤 Responsável", responsavel)
    c3.metric("🕐 Turno", turno_padrao)

    # Carregar registros do dia
    try:
        registros_hoje = [r for r in ler_todos("checklist_cozinha") if r.get("Data") == hoje]
    except Exception:
        registros_hoje = []

    total_itens = sum(len(v) for v in ITENS_PADRAO.values())
    concluidos_count = sum(1 for r in registros_hoje if r.get("Concluido") == "Sim")
    pct = int(concluidos_count / total_itens * 100) if total_itens > 0 else 0
    c4.metric("📊 Progresso", f"{pct}%")

    # Barra de progresso
    st.markdown(f"""
    <div style="margin:0.5rem 0 1rem;">
        <div style="display:flex; justify-content:space-between; color:#A07850; font-size:0.8rem; margin-bottom:4px;">
            <span>{concluidos_count} de {total_itens} itens concluídos</span>
            <span style="color:{'#4CAF50' if pct==100 else '#E8671A'}; font-weight:700;">{pct}%</span>
        </div>
        <div style="background:#2D1A00; border-radius:8px; height:10px; border:1px solid #4A2E10;">
            <div style="background:{'linear-gradient(90deg,#4CAF50,#66BB6A)' if pct==100 else 'linear-gradient(90deg,#E8671A,#F5A050)'};
                        width:{pct}%; height:100%; border-radius:8px; transition:width 0.5s;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if pct == 100:
        st.success("🎉 Checklist 100% concluído! Excelente trabalho!")

    st.markdown("---")

    # Estado local
    if "checklist_state" not in st.session_state:
        st.session_state["checklist_state"] = {}

    # Pré-preencher com dados salvos
    for reg in registros_hoje:
        item_key = f"{reg.get('Categoria')}_{reg.get('Item')}"
        st.session_state["checklist_state"][item_key] = reg.get("Concluido", "Não") == "Sim"

    # Renderizar categorias
    for categoria, itens in ITENS_PADRAO.items():
        cat_concluidos = sum(
            1 for item in itens
            if st.session_state["checklist_state"].get(f"{categoria}_{item}", False)
        )
        cor_cat = "#4CAF50" if cat_concluidos == len(itens) else ("#E8671A" if cat_concluidos > 0 else "#A07850")

        with st.expander(
            f"**{categoria}** — {cat_concluidos}/{len(itens)} concluídos",
            expanded=(cat_concluidos < len(itens))
        ):
            for item in itens:
                item_key = f"{categoria}_{item}"
                atual = st.session_state["checklist_state"].get(item_key, False)

                # Buscar quem editou
                reg_item = next(
                    (r for r in registros_hoje
                     if r.get("Categoria") == categoria and r.get("Item") == item),
                    None
                )
                editado_por = reg_item.get("Editado_Por", "") if reg_item else ""
                hora_conclusao = reg_item.get("Hora_Conclusao", "") if reg_item else ""

                col_chk, col_info = st.columns([3, 2])
                with col_chk:
                    novo = st.checkbox(item, value=atual, key=f"chk_{item_key}")
                    st.session_state["checklist_state"][item_key] = novo
                with col_info:
                    if editado_por and hora_conclusao:
                        st.markdown(
                            f"<div style='color:#A07850; font-size:0.72rem; padding-top:0.4rem;'>"
                            f"✏️ <b>{editado_por}</b> · {hora_conclusao}</div>",
                            unsafe_allow_html=True
                        )

    st.markdown("---")

    # Ações
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
            link = link_checklist_cozinha(numero_cozinha, hoje, turno_padrao, itens_ok, itens_nok)
            st.link_button("📲 Enviar via WhatsApp", link, use_container_width=True)
        else:
            st.caption("Configure o WhatsApp nas configurações do sistema.")

    # Histórico com coluna "Editado Por"
    st.markdown("---")
    st.markdown("### 📊 Histórico — Últimos 7 Dias")
    try:
        historico = ler_todos("checklist_cozinha")
        if historico:
            import pandas as pd
            df = pd.DataFrame(historico)
            if not df.empty and "Data" in df.columns:
                colunas_exibir = ["Data", "Turno", "Categoria", "Item", "Concluido", "Hora_Conclusao"]
                if "Editado_Por" in df.columns:
                    colunas_exibir.append("Editado_Por")
                colunas_existentes = [c for c in colunas_exibir if c in df.columns]
                df_hist = df[colunas_existentes].rename(columns={
                    "Hora_Conclusao": "Hora",
                    "Editado_Por": "Editado Por",
                })
                # Últimas 7 datas únicas
                datas_unicas = sorted(df_hist["Data"].unique(), reverse=True)[:7]
                df_hist = df_hist[df_hist["Data"].isin(datas_unicas)]
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
    except Exception:
        pass


def _salvar_checklist(hoje, turno, responsavel, registros_existentes):
    """Salva itens do checklist registrando quem editou."""
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
                # Registra quem editou
                try:
                    atualizar_campo("checklist_cozinha", reg_id, "Editado_Por", responsavel)
                except Exception:
                    pass
            else:
                novo_id = proximo_id("checklist_cozinha")
                inserir("checklist_cozinha", [
                    novo_id, hoje, turno, responsavel,
                    item, categoria, concluido_str, hora_conclusao,
                    "", "Ativo", responsavel  # Editado_Por no final
                ])
            salvos += 1

    st.success(f"✅ Checklist salvo por **{responsavel}**! {salvos} itens registrados.")
    st.rerun()
