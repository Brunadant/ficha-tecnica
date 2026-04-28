"""
Painel de Producao KDS - Visual Status de Voo.
Cards: Vermelho/Pendente, Amarelo/Preparo, Verde/Pronto.
Usa componentes nativos do Streamlit para evitar HTML escapado.
"""

import streamlit as st
from datetime import datetime
from src.services.sheets import ler_todos, atualizar_campo, inserir, proximo_id, get_config, invalidar_cache
from src.utils.whatsapp import link_pedido_pronto

STATUS_CONFIG = {
    "Pendente": {"cor": "#ef4444", "label": "PENDENTE",   "bg": "#3d0000"},
    "Preparo":  {"cor": "#f59e0b", "label": "EM PREPARO", "bg": "#3d2000"},
    "Pronto":   {"cor": "#22c55e", "label": "PRONTO",     "bg": "#003d10"},
    "Entregue": {"cor": "#38bdf8", "label": "ENTREGUE",   "bg": "#00203d"},
}

STATUS_ORDEM = {"Pendente": 0, "Preparo": 1, "Pronto": 2, "Entregue": 3}


def render_painel_producao():
    st.markdown("## Painel de Producao — KDS")
    st.markdown("---")

    # CSS apenas para os cards (sem f-string dentro do markdown)
    st.markdown("""
    <style>
    .kds-card {
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.5rem;
        border-left: 5px solid;
    }
    .kds-title { font-size: 1.05rem; font-weight: 700; color: #F5E6C8; margin-bottom: 0.3rem; }
    .kds-prato { font-size: 0.95rem; color: #F5E6C8; margin-bottom: 0.2rem; }
    .kds-obs   { font-size: 0.78rem; color: #A07850; margin-bottom: 0.2rem; }
    .kds-hora  { font-size: 0.75rem; color: #6B4A28; }
    .kds-badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        margin-top: 0.4rem;
    }
    </style>
    """, unsafe_allow_html=True)

    col_novo, col_filtro, col_refresh = st.columns([2, 2, 1])
    with col_novo:
        if st.button("Novo Pedido", type="primary", use_container_width=True):
            st.session_state["modal_novo_pedido"] = True
    with col_filtro:
        filtro_status = st.selectbox(
            "Filtrar",
            ["Todos", "Pendente", "Preparo", "Pronto", "Entregue"],
            label_visibility="collapsed"
        )
    with col_refresh:
        if st.button("Atualizar", use_container_width=True):
            invalidar_cache("pedidos")
            st.rerun()

    if st.session_state.get("modal_novo_pedido"):
        _form_novo_pedido()

    # Leitura unica com cache
    try:
        todos_pedidos = ler_todos("pedidos")
    except Exception as e:
        st.error(f"Erro ao carregar pedidos: {e}")
        return

    # Metricas
    total    = len(todos_pedidos)
    pendentes = sum(1 for p in todos_pedidos if p.get("Status") == "Pendente")
    preparo   = sum(1 for p in todos_pedidos if p.get("Status") == "Preparo")
    prontos   = sum(1 for p in todos_pedidos if p.get("Status") == "Pronto")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", total)
    m2.metric("Pendentes", pendentes)
    m3.metric("Em Preparo", preparo)
    m4.metric("Prontos", prontos)
    st.markdown("---")

    # Filtrar e ordenar
    pedidos_exibir = todos_pedidos if filtro_status == "Todos" else [
        p for p in todos_pedidos if p.get("Status") == filtro_status
    ]
    pedidos_exibir.sort(key=lambda p: STATUS_ORDEM.get(p.get("Status", ""), 9))

    if not pedidos_exibir:
        st.info("Nenhum pedido encontrado.")
        return

    numero_cozinha = get_config("whatsapp_cozinha")

    cols = st.columns(3)
    for idx, pedido in enumerate(pedidos_exibir):
        status    = pedido.get("Status", "Pendente")
        cfg       = STATUS_CONFIG.get(status, STATUS_CONFIG["Pendente"])
        pedido_id = str(pedido.get("ID", ""))
        numero    = pedido.get("Numero_Pedido", "?")
        mesa      = pedido.get("Mesa", "?")
        prato     = pedido.get("Nome_Prato", "?")
        qtd       = pedido.get("Quantidade", 1)
        obs       = str(pedido.get("Observacao", "")).strip()
        criado    = pedido.get("Criado_Em", "")

        cor   = cfg["cor"]
        bg    = cfg["bg"]
        label = cfg["label"]

        obs_part   = f'<div class="kds-obs">Obs: {obs}</div>' if obs else ""
        hora_part  = f'<div class="kds-hora">{criado}</div>' if criado else ""

        html_card = (
            f'<div class="kds-card" style="background:{bg}; border-color:{cor};">'
            f'<div class="kds-title">#{numero} — Mesa {mesa}</div>'
            f'<div class="kds-prato">{prato} x {qtd}</div>'
            f'{obs_part}'
            f'{hora_part}'
            f'<div class="kds-badge" style="background:{cor}22; color:{cor}; border:1px solid {cor}44;">'
            f'{label}</div>'
            f'</div>'
        )

        with cols[idx % 3]:
            st.markdown(html_card, unsafe_allow_html=True)

            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            btn_cols = st.columns(2)

            with btn_cols[0]:
                if status == "Pendente":
                    if st.button("Iniciar", key=f"ini_{pedido_id}", use_container_width=True):
                        atualizar_campo("pedidos", pedido_id, "Status", "Preparo")
                        atualizar_campo("pedidos", pedido_id, "Atualizado_Em", agora)
                        st.rerun()
                elif status == "Preparo":
                    if st.button("Pronto", key=f"prt_{pedido_id}",
                                 use_container_width=True, type="primary"):
                        atualizar_campo("pedidos", pedido_id, "Status", "Pronto")
                        atualizar_campo("pedidos", pedido_id, "Atualizado_Em", agora)
                        st.rerun()
                elif status == "Pronto":
                    if st.button("Entregue", key=f"ent_{pedido_id}", use_container_width=True):
                        atualizar_campo("pedidos", pedido_id, "Status", "Entregue")
                        atualizar_campo("pedidos", pedido_id, "Concluido_Em", agora)
                        st.rerun()

            with btn_cols[1]:
                if status == "Pronto" and numero_cozinha:
                    link = link_pedido_pronto(numero_cozinha, numero, mesa, prato)
                    st.link_button("WhatsApp", link, use_container_width=True)


def _form_novo_pedido():
    with st.expander("Novo Pedido", expanded=True):
        try:
            fichas = ler_todos("fichas_tecnicas")
            opcoes_pratos = {f["Nome_Prato"]: f["ID"] for f in fichas if f.get("Nome_Prato")}
        except Exception:
            opcoes_pratos = {}

        with st.form("form_pedido"):
            c1, c2 = st.columns(2)
            with c1:
                mesa = st.text_input("Mesa *", placeholder="Ex: 5")
                garcom = st.text_input("Garcom", placeholder="Nome do garcom")
            with c2:
                if opcoes_pratos:
                    prato_nome = st.selectbox("Prato *", list(opcoes_pratos.keys()))
                else:
                    prato_nome = st.text_input("Prato *", placeholder="Nome do prato")
                quantidade = st.number_input("Quantidade", min_value=1, value=1)

            observacao = st.text_area("Observacoes", placeholder="Sem cebola, bem passado...")

            col_s, col_c = st.columns(2)
            with col_s:
                salvar = st.form_submit_button("Salvar Pedido", type="primary",
                                               use_container_width=True)
            with col_c:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
            if not mesa or not prato_nome:
                st.error("Mesa e Prato sao obrigatorios.")
            else:
                novo_id = proximo_id("pedidos")
                numero_pedido = f"{datetime.now().strftime('%d%m')}{novo_id:03d}"
                prato_id = opcoes_pratos.get(prato_nome, "")
                agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                inserir("pedidos", [
                    novo_id, numero_pedido, mesa, garcom, prato_id,
                    prato_nome, quantidade, observacao,
                    "Pendente", agora, agora, ""
                ])
                st.success(f"Pedido #{numero_pedido} criado!")
                st.session_state["modal_novo_pedido"] = False
                st.rerun()

        if cancelar:
            st.session_state["modal_novo_pedido"] = False
            st.rerun()
