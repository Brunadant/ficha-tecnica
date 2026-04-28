"""
Módulo de Gestão de Insumos e Estoque.
"""

import streamlit as st
from datetime import datetime
from src.services.sheets import ler_todos, inserir, proximo_id, excluir_logico, atualizar_campo
from src.utils.cmv import formatar_moeda


def render_insumos():
    st.markdown("## 📦 Gestão de Insumos")
    st.markdown("---")

    aba = st.tabs(["📋 Estoque Atual", "➕ Novo Insumo", "📊 Movimentações"])

    with aba[0]:
        _listar_insumos()
    with aba[1]:
        _form_novo_insumo()
    with aba[2]:
        _movimentacoes()


def _listar_insumos():
    try:
        insumos = ler_todos("insumos")
    except Exception as e:
        st.error(f"Erro ao carregar insumos: {e}")
        return

    if not insumos:
        st.info("Nenhum insumo cadastrado ainda.")
        return

    # Alertas de estoque baixo
    alertas = [
        i for i in insumos
        if float(i.get("Estoque_Atual", 0) or 0) <= float(i.get("Estoque_Minimo", 0) or 0)
        and float(i.get("Estoque_Minimo", 0) or 0) > 0
    ]
    if alertas:
        st.warning(f"⚠️ **{len(alertas)} insumo(s) com estoque abaixo do mínimo!**")
        for a in alertas:
            st.markdown(
                f"🔴 **{a.get('Nome')}** — Atual: {a.get('Estoque_Atual')} {a.get('Unidade_Uso')} "
                f"| Mínimo: {a.get('Estoque_Minimo')} {a.get('Unidade_Uso')}"
            )
        st.markdown("---")

    # Filtros
    categorias = list({i.get("Categoria", "Sem categoria") for i in insumos})
    filtro_cat = st.selectbox("Filtrar por categoria", ["Todas"] + sorted(categorias))
    if filtro_cat != "Todas":
        insumos = [i for i in insumos if i.get("Categoria") == filtro_cat]

    # Tabela
    import pandas as pd
    df = pd.DataFrame([{
        "Nome": i.get("Nome", ""),
        "Categoria": i.get("Categoria", ""),
        "Un. Uso": i.get("Unidade_Uso", ""),
        "Estoque": i.get("Estoque_Atual", 0),
        "Mínimo": i.get("Estoque_Minimo", 0),
        "Custo Unit.": formatar_moeda(float(i.get("Custo_Unitario", 0) or 0)),
        "Fornecedor": i.get("Fornecedor", ""),
        "Status": "🔴 Baixo" if float(i.get("Estoque_Atual", 0) or 0) <= float(i.get("Estoque_Minimo", 0) or 0) and float(i.get("Estoque_Minimo", 0) or 0) > 0 else "🟢 OK",
    } for i in insumos])

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Atualizar estoque
    st.markdown("---")
    st.markdown("### Atualizar Estoque")
    nomes = [i.get("Nome") for i in insumos]
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        insumo_sel = st.selectbox("Insumo", nomes, key="upd_insumo")
    with col_a2:
        novo_estoque = st.number_input("Novo Estoque", min_value=0.0, format="%.3f", key="upd_est")
    with col_a3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Atualizar", key="btn_upd_est"):
            insumo_obj = next((i for i in insumos if i.get("Nome") == insumo_sel), None)
            if insumo_obj:
                atualizar_campo("insumos", str(insumo_obj["ID"]), "Estoque_Atual", str(novo_estoque))
                atualizar_campo("insumos", str(insumo_obj["ID"]), "Atualizado_Em",
                                datetime.now().strftime("%d/%m/%Y %H:%M"))
                st.success(f"Estoque de '{insumo_sel}' atualizado para {novo_estoque}!")
                st.rerun()


def _form_novo_insumo():
    st.markdown("### Novo Insumo")

    with st.form("form_novo_insumo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome do Insumo *")
            categoria = st.selectbox("Categoria", [
                "Proteína", "Hortifrúti", "Laticínio", "Grão/Cereal",
                "Tempero/Condimento", "Bebida", "Embalagem", "Outro"
            ])
            unidade_compra = st.selectbox("Unidade de Compra", ["kg", "L", "un", "pç", "cx"])
            unidade_uso = st.selectbox("Unidade de Uso", ["g", "ml", "un", "pç", "kg", "L"])
        with c2:
            fator_conversao = st.number_input("Fator de Conversão", min_value=0.001,
                                               value=1000.0, format="%.3f",
                                               help="Ex: 1 kg = 1000 g → fator = 1000")
            custo_unitario = st.number_input("Custo Unitário (R$/un. compra)",
                                             min_value=0.0, format="%.4f")
            estoque_atual = st.number_input("Estoque Atual", min_value=0.0, format="%.3f")
            estoque_minimo = st.number_input("Estoque Mínimo (alerta)", min_value=0.0, format="%.3f")

        fornecedor = st.text_input("Fornecedor")
        salvar = st.form_submit_button("💾 Salvar Insumo", type="primary", use_container_width=True)

    if salvar:
        if not nome:
            st.error("Nome é obrigatório.")
            return
        novo_id = proximo_id("insumos")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        inserir("insumos", [
            novo_id, nome, categoria, unidade_compra, unidade_uso,
            fator_conversao, custo_unitario, estoque_atual,
            estoque_minimo, fornecedor, "Ativo", agora
        ])
        st.success(f"✅ Insumo '{nome}' cadastrado com sucesso!")
        st.rerun()


def _movimentacoes():
    st.markdown("### Registrar Movimentação de Estoque")

    try:
        insumos = ler_todos("insumos")
        nomes_insumos = {i["Nome"]: i for i in insumos if i.get("Nome")}
    except Exception:
        nomes_insumos = {}

    with st.form("form_movimentacao", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            insumo_sel = st.selectbox("Insumo *", ["— selecione —"] + list(nomes_insumos.keys()))
            tipo = st.selectbox("Tipo", ["Entrada", "Saída", "Ajuste", "Perda"])
            quantidade = st.number_input("Quantidade", min_value=0.0, format="%.3f")
        with c2:
            unidade = st.selectbox("Unidade", ["g", "kg", "ml", "L", "un", "pç"])
            motivo = st.text_input("Motivo", placeholder="Ex: Compra, Uso na produção, Vencimento")
            from src.services.auth import get_usuario
            u = get_usuario()
            responsavel = st.text_input("Responsável", value=u.get("Nome", "") if u else "")

        registrar = st.form_submit_button("📝 Registrar", type="primary", use_container_width=True)

    if registrar:
        if insumo_sel == "— selecione —" or quantidade <= 0:
            st.error("Selecione o insumo e informe a quantidade.")
            return
        novo_id = proximo_id("movimentacao_estoque")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        insumo_obj = nomes_insumos.get(insumo_sel, {})
        inserir("movimentacao_estoque", [
            novo_id, agora, insumo_obj.get("ID", ""), insumo_sel,
            tipo, quantidade, unidade, motivo, responsavel, "Ativo"
        ])
        st.success(f"✅ Movimentação registrada: {tipo} de {quantidade} {unidade} de '{insumo_sel}'")
        st.rerun()

    # Histórico
    st.markdown("---")
    st.markdown("### Histórico de Movimentações")
    try:
        movs = ler_todos("movimentacao_estoque")
        if movs:
            import pandas as pd
            df = pd.DataFrame([{
                "Data": m.get("Data", ""),
                "Insumo": m.get("Nome_Insumo", ""),
                "Tipo": m.get("Tipo", ""),
                "Qtd": f"{m.get('Quantidade', '')} {m.get('Unidade', '')}",
                "Motivo": m.get("Motivo", ""),
                "Responsável": m.get("Responsavel", ""),
            } for m in movs[-30:]])
            st.dataframe(df[::-1], use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar movimentações: {e}")
