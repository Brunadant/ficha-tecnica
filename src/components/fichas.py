"""
Módulo de Fichas Técnicas com cálculo de CMV profissional.
"""

import streamlit as st
from datetime import datetime
from src.services.sheets import (
    ler_todos, inserir, proximo_id, excluir_logico,
    atualizar_campo, get_config
)
from src.utils.cmv import (
    calcular_cmv, calcular_cmv_percentual, sugerir_preco,
    formatar_moeda, formatar_percentual
)


def render_fichas():
    st.markdown("## 📖 Fichas Técnicas")
    st.markdown("---")

    aba = st.tabs(["📋 Listar Fichas", "➕ Nova Ficha", "🧮 Calculadora CMV"])

    with aba[0]:
        _listar_fichas()
    with aba[1]:
        _form_nova_ficha()
    with aba[2]:
        _calculadora_cmv()


def _listar_fichas():
    try:
        fichas = ler_todos("fichas_tecnicas")
    except Exception as e:
        st.error(f"Erro ao carregar fichas: {e}")
        return

    if not fichas:
        st.info("Nenhuma ficha técnica cadastrada ainda.")
        return

    # Filtros
    categorias = list({f.get("Categoria", "Sem categoria") for f in fichas})
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_cat = st.selectbox("Categoria", ["Todas"] + sorted(categorias))
    with col_f2:
        busca = st.text_input("🔍 Buscar prato", placeholder="Nome do prato...")

    if filtro_cat != "Todas":
        fichas = [f for f in fichas if f.get("Categoria") == filtro_cat]
    if busca:
        fichas = [f for f in fichas if busca.lower() in f.get("Nome_Prato", "").lower()]

    st.markdown(f"**{len(fichas)} ficha(s) encontrada(s)**")

    for ficha in fichas:
        ficha_id = str(ficha.get("ID", ""))
        nome = ficha.get("Nome_Prato", "Sem nome")
        categoria = ficha.get("Categoria", "—")
        rendimento = ficha.get("Rendimento_Porcoes", 1)
        preco = float(ficha.get("Preco_Venda", 0) or 0)
        tempo = ficha.get("Tempo_Preparo_Min", "—")

        with st.expander(f"🍽️ {nome} — {categoria}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Rendimento", f"{rendimento} porção(ões)")
            c2.metric("Preço de Venda", formatar_moeda(preco))
            c3.metric("Tempo de Preparo", f"{tempo} min")

            # Ingredientes da ficha
            try:
                ingredientes = [
                    i for i in ler_todos("ficha_ingredientes")
                    if str(i.get("Ficha_ID")) == ficha_id
                ]
            except Exception:
                ingredientes = []

            if ingredientes:
                st.markdown("**Ingredientes:**")
                custo_total_ing = 0.0
                for ing in ingredientes:
                    custo = float(ing.get("Custo_Total", 0) or 0)
                    custo_total_ing += custo
                    st.markdown(
                        f"- {ing.get('Nome_Insumo', '?')} — "
                        f"{ing.get('Quantidade', '?')} {ing.get('Unidade', '')} "
                        f"({formatar_moeda(custo)})"
                    )

                custo_mo = float(ficha.get("Custo_MO", 0) or 0)
                margem = float(ficha.get("Margem_Perda_Pct", 5) or 5)
                cmv = calcular_cmv(custo_total_ing, custo_mo, margem, int(rendimento))
                cmv_pct = calcular_cmv_percentual(cmv["custo_porcao"], preco)

                st.markdown("---")
                cc1, cc2, cc3, cc4 = st.columns(4)
                cc1.metric("Custo Total", formatar_moeda(cmv["custo_total"]))
                cc2.metric("Custo/Porção", formatar_moeda(cmv["custo_porcao"]))
                cc3.metric("CMV%", formatar_percentual(cmv_pct),
                           delta="✅ OK" if cmv_pct <= 35 else "⚠️ Alto",
                           delta_color="normal" if cmv_pct <= 35 else "inverse")
                cc4.metric("Preço Sugerido (30%)", formatar_moeda(sugerir_preco(cmv["custo_porcao"], 30)))

            modo = ficha.get("Modo_Preparo", "")
            if modo:
                st.markdown(f"**Modo de Preparo:**\n{modo}")

            if st.button(f"🗑️ Excluir '{nome}'", key=f"del_ficha_{ficha_id}",
                         help="Exclusão lógica — preserva histórico"):
                if excluir_logico("fichas_tecnicas", ficha_id):
                    st.success("Ficha excluída (exclusão lógica).")
                    st.rerun()


def _form_nova_ficha():
    st.markdown("### Nova Ficha Técnica")

    # Carregar insumos disponíveis
    try:
        insumos = ler_todos("insumos")
        mapa_insumos = {i["Nome"]: i for i in insumos if i.get("Nome")}
    except Exception:
        mapa_insumos = {}

    with st.form("form_nova_ficha", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            nome_prato = st.text_input("Nome do Prato *")
            categoria = st.selectbox("Categoria", [
                "Entrada", "Prato Principal", "Sobremesa",
                "Bebida", "Lanche", "Outro"
            ])
            rendimento = st.number_input("Rendimento (porções)", min_value=1, value=1)
        with c2:
            tempo_preparo = st.number_input("Tempo de Preparo (min)", min_value=0, value=30)
            preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0,
                                          value=0.0, format="%.2f")
            custo_mo = st.number_input("Custo Mão de Obra (R$)", min_value=0.0,
                                       value=float(get_config("custo_mo_hora") or 0),
                                       format="%.2f")

        margem_perda = st.slider(
            "Margem de Perda (%)",
            min_value=0, max_value=30,
            value=int(get_config("margem_perda_padrao") or 5)
        )
        modo_preparo = st.text_area("Modo de Preparo", height=120,
                                    placeholder="Descreva o passo a passo...")

        st.markdown("#### Ingredientes")
        st.caption("Adicione os ingredientes abaixo. Você pode adicionar mais após salvar a ficha.")

        # Até 10 ingredientes no formulário inicial
        ingredientes_form = []
        num_ing = st.number_input("Quantos ingredientes?", min_value=1, max_value=20, value=3)

        for i in range(int(num_ing)):
            ci1, ci2, ci3 = st.columns([3, 1, 1])
            with ci1:
                if mapa_insumos:
                    ing_nome = st.selectbox(f"Ingrediente {i+1}",
                                            ["— selecione —"] + list(mapa_insumos.keys()),
                                            key=f"ing_nome_{i}")
                else:
                    ing_nome = st.text_input(f"Ingrediente {i+1}", key=f"ing_nome_{i}")
            with ci2:
                qtd = st.number_input("Qtd", min_value=0.0, value=0.0,
                                      format="%.3f", key=f"ing_qtd_{i}")
            with ci3:
                unidade = st.selectbox("Un", ["g", "kg", "ml", "L", "un", "pç"],
                                       key=f"ing_un_{i}")
            ingredientes_form.append((ing_nome, qtd, unidade))

        salvar = st.form_submit_button("💾 Salvar Ficha Técnica", type="primary",
                                       use_container_width=True)

    if salvar:
        if not nome_prato:
            st.error("Nome do prato é obrigatório.")
            return

        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        ficha_id = proximo_id("fichas_tecnicas")

        inserir("fichas_tecnicas", [
            ficha_id, nome_prato, categoria, rendimento,
            tempo_preparo, modo_preparo, "",
            custo_mo, margem_perda, preco_venda,
            "Ativo", agora, agora
        ])

        # Inserir ingredientes
        for ing_nome, qtd, unidade in ingredientes_form:
            if ing_nome and ing_nome != "— selecione —" and qtd > 0:
                insumo = mapa_insumos.get(ing_nome, {})
                insumo_id = insumo.get("ID", "")
                custo_unit = float(insumo.get("Custo_Unitario", 0) or 0)
                custo_total_ing = round(qtd * custo_unit, 4)
                ing_id = proximo_id("ficha_ingredientes")
                inserir("ficha_ingredientes", [
                    ing_id, ficha_id, insumo_id, ing_nome,
                    qtd, unidade, custo_unit, custo_total_ing, ""
                ])

        st.success(f"✅ Ficha técnica '{nome_prato}' criada com sucesso!")
        st.rerun()


def _calculadora_cmv():
    st.markdown("### 🧮 Calculadora CMV Profissional")
    st.caption("Calcule o CMV de qualquer receita sem salvar no sistema.")

    c1, c2 = st.columns(2)
    with c1:
        custo_ing = st.number_input("Custo dos Ingredientes (R$)", min_value=0.0,
                                    value=10.0, format="%.2f")
        custo_mo_calc = st.number_input("Custo Mão de Obra (R$)", min_value=0.0,
                                        value=5.0, format="%.2f")
    with c2:
        margem_calc = st.slider("Margem de Perda (%)", 0, 30, 5)
        rendimento_calc = st.number_input("Rendimento (porções)", min_value=1, value=1)

    preco_calc = st.number_input("Preço de Venda (R$)", min_value=0.0,
                                 value=35.0, format="%.2f")

    if st.button("Calcular CMV", type="primary"):
        resultado = calcular_cmv(custo_ing, custo_mo_calc, margem_calc, rendimento_calc)
        cmv_pct = calcular_cmv_percentual(resultado["custo_porcao"], preco_calc)
        preco_sug_30 = sugerir_preco(resultado["custo_porcao"], 30)
        preco_sug_35 = sugerir_preco(resultado["custo_porcao"], 35)

        st.markdown("---")
        st.markdown("#### Resultado")

        r1, r2, r3 = st.columns(3)
        r1.metric("Custo Total", formatar_moeda(resultado["custo_total"]))
        r2.metric("Custo/Porção", formatar_moeda(resultado["custo_porcao"]))
        r3.metric("CMV%", formatar_percentual(cmv_pct),
                  delta="✅ Saudável" if cmv_pct <= 35 else "⚠️ Acima do ideal",
                  delta_color="normal" if cmv_pct <= 35 else "inverse")

        st.markdown("**Detalhamento do Custo:**")
        st.markdown(f"""
        | Item | Valor |
        |------|-------|
        | Ingredientes | {formatar_moeda(resultado['custo_ingredientes'])} |
        | Mão de Obra | {formatar_moeda(resultado['custo_mo'])} |
        | Perda ({margem_calc}%) | {formatar_moeda(resultado['custo_perda'])} |
        | **Total** | **{formatar_moeda(resultado['custo_total'])}** |
        | **Custo/Porção** | **{formatar_moeda(resultado['custo_porcao'])}** |
        """)

        st.markdown("**Preços Sugeridos:**")
        ps1, ps2 = st.columns(2)
        ps1.metric("Para CMV 30%", formatar_moeda(preco_sug_30))
        ps2.metric("Para CMV 35%", formatar_moeda(preco_sug_35))
