"""
Checklist Diario de Cozinha.
- Selecao de responsavel (funcionarios cadastrados ou nome livre)
- Criacao de novo checklist por turno/data
- Rastreio de quem editou cada item (Editado_Por + Hora_Conclusao)
- Link WhatsApp com resumo do checklist
"""

import streamlit as st
from datetime import datetime, date
from src.services.sheets import ler_todos, inserir, proximo_id, atualizar_campo, get_config, ler_todos_raw
from src.utils.whatsapp import link_checklist_cozinha

ITENS_PADRAO = {
    "Abertura": [
        "Ligar equipamentos (fogao, forno, fritadeira)",
        "Verificar temperatura da camara fria",
        "Conferir estoque do dia",
        "Higienizar bancadas e utensilios",
        "Verificar validade dos insumos",
    ],
    "Mise en Place": [
        "Cortar e preparar legumes do dia",
        "Descongelar proteinas necessarias",
        "Preparar fundos e molhos base",
        "Separar ingredientes das fichas tecnicas",
        "Porcionar e etiquetar preparacoes",
    ],
    "Higiene": [
        "Lavar e higienizar hortalicas",
        "Trocar agua de manutencao de equipamentos",
        "Verificar limpeza dos utensilios",
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


def _get_funcionarios() -> list[str]:
    """Retorna lista de nomes de funcionarios ativos."""
    try:
        funcs = ler_todos("funcionarios")
        return [f.get("Nome", "") for f in funcs if f.get("Nome")]
    except Exception:
        return []


def render_checklist():
    st.markdown("## Checklist Diario de Cozinha")
    st.markdown("---")

    # ── Painel de controle do checklist ────────────────────────────────────────
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)

    with col_ctrl1:
        hoje = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
        hoje_str = hoje.strftime("%d/%m/%Y")

    with col_ctrl2:
        hora_atual = datetime.now().hour
        turno_padrao = "Manha" if hora_atual < 14 else ("Tarde" if hora_atual < 20 else "Noite")
        turno = st.selectbox("Turno", ["Manha", "Tarde", "Noite"], index=["Manha", "Tarde", "Noite"].index(turno_padrao))

    with col_ctrl3:
        # Responsavel: funcionarios cadastrados + opcao livre
        lista_funcs = _get_funcionarios()
        opcoes_resp = lista_funcs + ["--- Digitar nome ---"]
        sel_resp = st.selectbox("Responsavel", opcoes_resp)
        if sel_resp == "--- Digitar nome ---":
            responsavel = st.text_input("Nome do responsavel", placeholder="Digite o nome...")
        else:
            responsavel = sel_resp

    if not responsavel:
        st.warning("Selecione ou informe o nome do responsavel para continuar.")
        return

    # ── Carregar registros do checklist para data/turno selecionados ───────────
    try:
        todos_registros = ler_todos_raw("checklist_cozinha")
        registros_filtrados = [
            r for r in todos_registros
            if r.get("Data") == hoje_str and r.get("Turno") == turno
            and str(r.get("Status", "")).strip() != "Excluido"
        ]
    except Exception:
        registros_filtrados = []

    # Mapa: "Categoria_Item" -> registro
    mapa_registros = {
        f"{r.get('Categoria')}_{r.get('Item')}": r
        for r in registros_filtrados
    }

    total_itens = sum(len(v) for v in ITENS_PADRAO.values())
    concluidos_count = sum(
        1 for r in registros_filtrados if r.get("Concluido") == "Sim"
    )
    pct = int(concluidos_count / total_itens * 100) if total_itens > 0 else 0

    # Métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Data", hoje_str)
    m2.metric("Turno", turno)
    m3.metric("Responsavel", responsavel)
    m4.metric("Progresso", f"{pct}%")

    # Barra de progresso
    cor_barra = "#4CAF50" if pct == 100 else "#E8671A"
    st.markdown(f"""
    <div style="margin:0.5rem 0 1rem;">
        <div style="display:flex; justify-content:space-between; color:#A07850;
                    font-size:0.8rem; margin-bottom:4px;">
            <span>{concluidos_count} de {total_itens} itens concluidos</span>
            <span style="color:{cor_barra}; font-weight:700;">{pct}%</span>
        </div>
        <div style="background:#2D1A00; border-radius:8px; height:10px; border:1px solid #4A2E10;">
            <div style="background:{cor_barra}; width:{pct}%; height:100%;
                        border-radius:8px; transition:width 0.5s;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if pct == 100:
        st.success("Checklist 100% concluido! Excelente trabalho!")

    st.markdown("---")

    # ── Estado local dos checkboxes ────────────────────────────────────────────
    estado_key = f"checklist_{hoje_str}_{turno}"
    if estado_key not in st.session_state:
        st.session_state[estado_key] = {}

    # Pré-preencher com dados salvos
    for chave, reg in mapa_registros.items():
        st.session_state[estado_key][chave] = reg.get("Concluido", "Nao") == "Sim"

    estado = st.session_state[estado_key]

    # ── Renderizar categorias ──────────────────────────────────────────────────
    for categoria, itens in ITENS_PADRAO.items():
        cat_ok = sum(1 for item in itens if estado.get(f"{categoria}_{item}", False))
        expandido = cat_ok < len(itens)

        with st.expander(f"**{categoria}** — {cat_ok}/{len(itens)}", expanded=expandido):
            for item in itens:
                item_key = f"{categoria}_{item}"
                atual = estado.get(item_key, False)
                reg_item = mapa_registros.get(item_key)
                editado_por = reg_item.get("Editado_Por", "") if reg_item else ""
                hora_conclusao = reg_item.get("Hora_Conclusao", "") if reg_item else ""

                col_chk, col_info = st.columns([3, 2])
                with col_chk:
                    novo = st.checkbox(item, value=atual, key=f"chk_{estado_key}_{item_key}")
                    estado[item_key] = novo
                with col_info:
                    if editado_por and hora_conclusao:
                        st.markdown(
                            f"<div style='color:#A07850; font-size:0.72rem; padding-top:0.4rem;'>"
                            f"Editado por <b>{editado_por}</b> as {hora_conclusao}</div>",
                            unsafe_allow_html=True
                        )

    st.markdown("---")

    # ── Acoes ──────────────────────────────────────────────────────────────────
    col_salvar, col_limpar, col_whats = st.columns(3)

    with col_salvar:
        if st.button("Salvar Checklist", type="primary", use_container_width=True):
            _salvar_checklist(hoje_str, turno, responsavel, mapa_registros, estado)

    with col_limpar:
        if st.button("Novo Checklist (Limpar)", use_container_width=True):
            # Limpa estado local para recomecar
            st.session_state[estado_key] = {}
            st.rerun()

    with col_whats:
        numero_cozinha = get_config("whatsapp_cozinha")
        if numero_cozinha and numero_cozinha.strip():
            itens_ok = [
                item
                for cat, itens in ITENS_PADRAO.items()
                for item in itens
                if estado.get(f"{cat}_{item}", False)
            ]
            itens_nok = [
                item
                for cat, itens in ITENS_PADRAO.items()
                for item in itens
                if not estado.get(f"{cat}_{item}", False)
            ]
            link = link_checklist_cozinha(numero_cozinha, hoje_str, turno, itens_ok, itens_nok)
            st.link_button("Enviar via WhatsApp", link, use_container_width=True)
        else:
            st.caption("Configure o numero WhatsApp em Configuracoes > Parametros > whatsapp_cozinha")

    # ── Historico ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Historico — Ultimos Registros")

    with st.expander("Ver historico", expanded=False):
        try:
            import pandas as pd
            historico = ler_todos_raw("checklist_cozinha")
            if historico:
                df = pd.DataFrame(historico)
                colunas = ["Data", "Turno", "Responsavel", "Categoria", "Item",
                           "Concluido", "Hora_Conclusao", "Editado_Por"]
                colunas_existentes = [c for c in colunas if c in df.columns]
                df_hist = df[colunas_existentes]
                datas_unicas = sorted(df_hist["Data"].unique(), reverse=True)[:7] if "Data" in df_hist.columns else []
                if datas_unicas:
                    df_hist = df_hist[df_hist["Data"].isin(datas_unicas)]
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum registro encontrado.")
        except Exception as e:
            st.error(f"Erro ao carregar historico: {e}")


def _salvar_checklist(hoje_str, turno, responsavel, mapa_registros, estado):
    """Salva todos os itens do checklist com rastreio de edicao."""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    salvos = 0

    for categoria, itens in ITENS_PADRAO.items():
        for item in itens:
            item_key = f"{categoria}_{item}"
            concluido = estado.get(item_key, False)
            concluido_str = "Sim" if concluido else "Nao"
            hora_conclusao = agora if concluido else ""

            reg_existente = mapa_registros.get(item_key)

            if reg_existente:
                reg_id = str(reg_existente.get("ID", ""))
                atualizar_campo("checklist_cozinha", reg_id, "Concluido", concluido_str)
                atualizar_campo("checklist_cozinha", reg_id, "Hora_Conclusao", hora_conclusao)
                atualizar_campo("checklist_cozinha", reg_id, "Editado_Por", responsavel)
            else:
                novo_id = proximo_id("checklist_cozinha")
                inserir("checklist_cozinha", [
                    novo_id, hoje_str, turno, responsavel,
                    item, categoria, concluido_str, hora_conclusao,
                    "", "Ativo", responsavel
                ])
            salvos += 1

    st.success(f"Checklist salvo por **{responsavel}**! {salvos} itens registrados.")
    st.rerun()
