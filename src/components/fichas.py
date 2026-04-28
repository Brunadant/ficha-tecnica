"""
Módulo de Fichas Técnicas — Design Catálogo estilo SisChef.
Suporte a foto do prato via URL + cálculo CMV profissional.
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

CATEGORIAS = ["Entrada", "Prato Principal", "Sobremesa", "Bebida", "Lanche", "Outro"]

# Cores por categoria
CAT_CORES = {
    "Entrada":        "#29B6F6",
    "Prato Principal": "#E8671A",
    "Sobremesa":      "#F06292",
    "Bebida":         "#66BB6A",
    "Lanche":         "#FFA726",
    "Outro":          "#A07850",
}


def render_fichas():
    st.markdown("## 📖 Fichas Técnicas")
    st.markdown("---")

    aba = st.tabs(["🗂️ Catálogo de Pratos", "➕ Nova Ficha", "🧮 Calculadora CMV"])

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
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#A07850;">
            <div style="font-size:3rem;">📋</div>
            <div style="font-size:1.1rem; font-weight:600; margin-top:0.5rem;">Nenhuma ficha cadastrada</div>
            <div style="font-size:0.85rem; margin-top:0.3rem;">Vá para "Nova Ficha" para começar.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Filtros
    categorias = sorted({f.get("Categoria", "Sem categoria") for f in fichas})
    cf1, cf2, cf3 = st.columns([2, 2, 1])
    with cf1:
        filtro_cat = st.selectbox("Categoria", ["Todas"] + categorias)
    with cf2:
        busca = st.text_input("🔍 Buscar prato", placeholder="Nome do prato...")
    with cf3:
        modo_exib = st.radio("Exibição", ["Cards", "Lista"], horizontal=True)

    if filtro_cat != "Todas":
        fichas = [f for f in fichas if f.get("Categoria") == filtro_cat]
    if busca:
        fichas = [f for f in fichas if busca.lower() in f.get("Nome_Prato", "").lower()]

    st.markdown(f"<div style='color:#A07850; font-size:0.85rem; margin-bottom:1rem;'>{len(fichas)} ficha(s) encontrada(s)</div>",
                unsafe_allow_html=True)

    if modo_exib == "Cards":
        _exibir_cards(fichas)
    else:
        _exibir_lista(fichas)


def _exibir_cards(fichas):
    """Exibe fichas em grade de cards estilo catálogo gastronômico."""
    cols = st.columns(3)
    for idx, ficha in enumerate(fichas):
        ficha_id = str(ficha.get("ID", ""))
        nome = ficha.get("Nome_Prato", "Sem nome")
        categoria = ficha.get("Categoria", "Outro")
        preco = float(ficha.get("Preco_Venda", 0) or 0)
        tempo = ficha.get("Tempo_Preparo_Min", "—")
        rendimento = ficha.get("Rendimento_Porcoes", 1)
        foto_url = ficha.get("Foto_URL", "")
        cor_cat = CAT_CORES.get(categoria, "#A07850")

        with cols[idx % 3]:
            # Card container
            st.markdown(f"""
            <div style="background:#2D1A00; border:1px solid #4A2E10; border-radius:14px;
                        overflow:hidden; margin-bottom:1rem; transition:all 0.2s;">
                <div style="position:relative;">
            """, unsafe_allow_html=True)

            # Foto do prato
            if foto_url and foto_url.startswith("http"):
                try:
                    st.image(foto_url, use_container_width=True)
                except Exception:
                    _placeholder_foto(nome)
            else:
                _placeholder_foto(nome)

            st.markdown(f"""
                </div>
                <div style="padding:0.9rem 1rem 0.5rem;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.4rem;">
                        <div style="color:#F5E6C8; font-weight:700; font-size:1rem; line-height:1.2;">{nome}</div>
                        <span style="background:{cor_cat}22; color:{cor_cat}; font-size:0.65rem; font-weight:700;
                              padding:2px 7px; border-radius:20px; border:1px solid {cor_cat}44;
                              white-space:nowrap; margin-left:0.5rem;">{categoria}</span>
                    </div>
                    <div style="display:flex; gap:1rem; color:#A07850; font-size:0.78rem; margin-bottom:0.5rem;">
                        <span>⏱️ {tempo} min</span>
                        <span>🍽️ {rendimento} porção(ões)</span>
                    </div>
                    <div style="color:#E8671A; font-weight:800; font-size:1.2rem;">
                        {formatar_moeda(preco)}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Botão de detalhes
            with st.expander("Ver detalhes / Editar"):
                _detalhes_ficha(ficha, ficha_id, nome, preco, int(rendimento))


def _placeholder_foto(nome):
    """Exibe placeholder quando não há foto."""
    inicial = nome[0].upper() if nome else "?"
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#3D2000,#2D1A00); height:160px;
                display:flex; align-items:center; justify-content:center;">
        <div style="text-align:center; color:#4A2E10;">
            <div style="font-size:3rem;">🍽️</div>
            <div style="font-size:0.75rem; margin-top:0.3rem; color:#A07850;">Sem foto</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _exibir_lista(fichas):
    """Exibe fichas em lista expandível."""
    for ficha in fichas:
        ficha_id = str(ficha.get("ID", ""))
        nome = ficha.get("Nome_Prato", "Sem nome")
        categoria = ficha.get("Categoria", "—")
        preco = float(ficha.get("Preco_Venda", 0) or 0)
        rendimento = ficha.get("Rendimento_Porcoes", 1)
        cor_cat = CAT_CORES.get(categoria, "#A07850")

        with st.expander(f"🍽️ **{nome}** — {categoria} · {formatar_moeda(preco)}"):
            _detalhes_ficha(ficha, ficha_id, nome, preco, int(rendimento))


def _detalhes_ficha(ficha, ficha_id, nome, preco, rendimento):
    """Renderiza detalhes completos de uma ficha."""
    categoria = ficha.get("Categoria", "—")
    tempo = ficha.get("Tempo_Preparo_Min", "—")
    custo_mo = float(ficha.get("Custo_MO", 0) or 0)
    margem = float(ficha.get("Margem_Perda_Pct", 5) or 5)
    foto_url = ficha.get("Foto_URL", "")

    c1, c2, c3 = st.columns(3)
    c1.metric("Rendimento", f"{rendimento} porção(ões)")
    c2.metric("Preço de Venda", formatar_moeda(preco))
    c3.metric("Tempo de Preparo", f"{tempo} min")

    # Atualizar foto
    st.markdown("**📸 Foto do Prato:**")
    col_foto, col_url = st.columns([1, 2])
    with col_foto:
        if foto_url and foto_url.startswith("http"):
            try:
                st.image(foto_url, width=180)
            except Exception:
                st.caption("Foto inválida")
        else:
            st.caption("Sem foto cadastrada")
    with col_url:
        nova_url = st.text_input(
            "URL da foto (link direto da imagem)",
            value=foto_url,
            placeholder="https://exemplo.com/foto-prato.jpg",
            key=f"foto_url_{ficha_id}"
        )
        if st.button("💾 Salvar Foto", key=f"salvar_foto_{ficha_id}"):
            atualizar_campo("fichas_tecnicas", ficha_id, "Foto_URL", nova_url)
            st.success("✅ Foto atualizada!")
            st.rerun()

    # Ingredientes
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

        cmv = calcular_cmv(custo_total_ing, custo_mo, margem, rendimento)
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

    st.markdown("---")
    if st.button(f"🗑️ Excluir '{nome}'", key=f"del_ficha_{ficha_id}",
                 help="Exclusão lógica — preserva histórico"):
        if excluir_logico("fichas_tecnicas", ficha_id):
            st.success("Ficha excluída (exclusão lógica).")
            st.rerun()


def _form_nova_ficha():
    st.markdown("### Nova Ficha Técnica")

    try:
        insumos = ler_todos("insumos")
        mapa_insumos = {i["Nome"]: i for i in insumos if i.get("Nome")}
    except Exception:
        mapa_insumos = {}

    with st.form("form_nova_ficha", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            nome_prato = st.text_input("Nome do Prato *")
            categoria = st.selectbox("Categoria", CATEGORIAS)
            rendimento = st.number_input("Rendimento (porções)", min_value=1, value=1)
        with c2:
            tempo_preparo = st.number_input("Tempo de Preparo (min)", min_value=0, value=30)
            preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0,
                                          value=0.0, format="%.2f")
            custo_mo = st.number_input("Custo Mão de Obra (R$)", min_value=0.0,
                                       value=float(get_config("custo_mo_hora") or 0),
                                       format="%.2f")

        foto_url_nova = st.text_input(
            "📸 URL da Foto do Prato (opcional)",
            placeholder="https://exemplo.com/foto-prato.jpg",
            help="Cole o link direto de uma imagem do prato"
        )

        margem_perda = st.slider(
            "Margem de Perda (%)", min_value=0, max_value=30,
            value=int(get_config("margem_perda_padrao") or 5)
        )
        modo_preparo = st.text_area("Modo de Preparo", height=120,
                                    placeholder="Descreva o passo a passo...")

        st.markdown("#### Ingredientes")
        num_ing = st.number_input("Quantos ingredientes?", min_value=1, max_value=20, value=3)

        ingredientes_form = []
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
            tempo_preparo, modo_preparo, foto_url_nova,
            custo_mo, margem_perda, preco_venda,
            "Ativo", agora, agora
        ])

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

        # Indicador visual de saúde do CMV
        if cmv_pct <= 30:
            status_cmv = "🟢 Excelente"
            cor_cmv = "#4CAF50"
        elif cmv_pct <= 35:
            status_cmv = "🟡 Aceitável"
            cor_cmv = "#FFC107"
        else:
            status_cmv = "🔴 Acima do ideal"
            cor_cmv = "#F44336"

        st.markdown(f"""
        <div style="background:#2D1A00; border:1px solid #4A2E10; border-radius:12px; padding:1.2rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#A07850; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px;">CMV Calculado</div>
                    <div style="color:{cor_cmv}; font-size:2.5rem; font-weight:800;">{formatar_percentual(cmv_pct)}</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:{cor_cmv}; font-size:1rem; font-weight:700;">{status_cmv}</div>
                    <div style="color:#A07850; font-size:0.8rem;">Meta ideal: até 35%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        r1, r2 = st.columns(2)
        r1.metric("Custo Total", formatar_moeda(resultado["custo_total"]))
        r2.metric("Custo/Porção", formatar_moeda(resultado["custo_porcao"]))

        st.markdown("**Detalhamento:**")
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
