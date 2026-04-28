"""
Painel de Produção KDS - Visual "Status de Voo".
Cards grandes com cores: Vermelho/Pendente, Amarelo/Preparo, Verde/Pronto.
"""

import streamlit as st
from datetime import datetime
from src.services.sheets import ler_todos, atualizar_campo, inserir, proximo_id, get_config
from src.utils.whatsapp import link_pedido_pronto

STATUS_CORES = {
    "Pendente":  {"bg": "#7f1d1d", "borda": "#ef4444", "emoji": "🔴", "label": "PENDENTE"},
    "Preparo":   {"bg": "#713f12", "borda": "#f59e0b", "emoji": "🟡", "label": "EM PREPARO"},
    "Pronto":    {"bg": "#14532d", "borda": "#22c55e", "emoji": "🟢", "label": "PRONTO"},
    "Entregue":  {"bg": "#1e3a5f", "borda": "#38bdf8", "emoji": "✅", "label": "ENTREGUE"},
}


def render_painel_producao():
    st.markdown("## 🖥️ Painel de Produção — KDS")
    st.markdown("---")

    # CSS dos cards KDS
    st.markdown("""
    <style>
    .kds-card {
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 5px solid;
        transition: all 0.2s;
    }
    .kds-card:hover { transform: translateX(3px); }
    .kds-header { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.3rem; }
    .kds-meta { font-size: 0.8rem; color: #94a3b8; }
    .kds-timer { font-size: 1.5rem; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

    # Barra de ações
    col_novo, col_filtro, col_refresh = st.columns([2, 2, 1])
    with col_novo:
        if st.button("➕ Novo Pedido", type="primary", use_container_width=True):
            st.session_state["modal_novo_pedido"] = True
    with col_filtro:
        filtro_status = st.selectbox(
            "Filtrar por status",
            ["Todos", "Pendente", "Preparo", "Pronto", "Entregue"],
            label_visibility="collapsed"
        )
    with col_refresh:
        if st.button("🔄", help="Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Modal novo pedido
    if st.session_state.get("modal_novo_pedido"):
        _form_novo_pedido()

    # Carregar pedidos
    try:
        pedidos = ler_todos("pedidos")
    except Exception as e:
        st.error(f"Erro ao carregar pedidos: {e}")
        return

    # Filtrar
    if filtro_status != "Todos":
        pedidos = [p for p in pedidos if p.get("Status") == filtro_status]

    # Ordenar: Pendente → Preparo → Pronto → Entregue
    ordem = {"Pendente": 0, "Preparo": 1, "Pronto": 2, "Entregue": 3}
    pedidos.sort(key=lambda p: ordem.get(p.get("Status", ""), 9))

    if not pedidos:
        st.info("Nenhum pedido encontrado para o filtro selecionado.")
        return

    # Métricas rápidas
    total = len(ler_todos("pedidos"))
    pendentes = sum(1 for p in ler_todos("pedidos") if p.get("Status") == "Pendente")
    em_preparo = sum(1 for p in ler_todos("pedidos") if p.get("Status") == "Preparo")
    prontos = sum(1 for p in ler_todos("pedidos") if p.get("Status") == "Pronto")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Hoje", total)
    m2.metric("🔴 Pendentes", pendentes)
    m3.metric("🟡 Em Preparo", em_preparo)
    m4.metric("🟢 Prontos", prontos)

    st.markdown("---")

    # Cards dos pedidos
    cols = st.columns(3)
    for idx, pedido in enumerate(pedidos):
        status = pedido.get("Status", "Pendente")
        cor = STATUS_CORES.get(status, STATUS_CORES["Pendente"])
        pedido_id = str(pedido.get("ID", ""))
        numero = pedido.get("Numero_Pedido", "?")
        mesa = pedido.get("Mesa", "?")
        prato = pedido.get("Nome_Prato", "?")
        qtd = pedido.get("Quantidade", 1)
        obs = pedido.get("Observacao", "")
        criado = pedido.get("Criado_Em", "")

        with cols[idx % 3]:
            st.markdown(f"""
            <div class="kds-card" style="background:{cor['bg']}; border-color:{cor['borda']};">
                <div class="kds-header">{cor['emoji']} #{numero} — Mesa {mesa}</div>
                <div style="font-size:1rem; margin:0.4rem 0;">🍽️ {prato} × {qtd}</div>
                {f'<div class="kds-meta">📝 {obs}</div>' if obs else ''}
                <div class="kds-meta">⏰ {criado}</div>
                <div style="margin-top:0.5rem;">
                    <span style="background:{cor['borda']}22; color:{cor['borda']};
                    padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:700;">
                    {cor['label']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Botões de ação
            btn_cols = st.columns(2)
            with btn_cols[0]:
                if status == "Pendente":
                    if st.button("▶ Iniciar", key=f"iniciar_{pedido_id}", use_container_width=True):
                        atualizar_campo("pedidos", pedido_id, "Status", "Preparo")
                        atualizar_campo("pedidos", pedido_id, "Atualizado_Em",
                                        datetime.now().strftime("%d/%m/%Y %H:%M"))
                        st.rerun()
                elif status == "Preparo":
                    if st.button("✅ Pronto", key=f"pronto_{pedido_id}",
                                 use_container_width=True, type="primary"):
                        atualizar_campo("pedidos", pedido_id, "Status", "Pronto")
                        atualizar_campo("pedidos", pedido_id, "Atualizado_Em",
                                        datetime.now().strftime("%d/%m/%Y %H:%M"))
                        st.rerun()
                elif status == "Pronto":
                    if st.button("📦 Entregue", key=f"entregue_{pedido_id}", use_container_width=True):
                        atualizar_campo("pedidos", pedido_id, "Status", "Entregue")
                        atualizar_campo("pedidos", pedido_id, "Concluido_Em",
                                        datetime.now().strftime("%d/%m/%Y %H:%M"))
                        st.rerun()

            with btn_cols[1]:
                if status == "Pronto":
                    numero_cozinha = get_config("whatsapp_cozinha")
                    if numero_cozinha:
                        link = link_pedido_pronto(numero_cozinha, numero, mesa, prato)
                        st.link_button("📲 WhatsApp", link, use_container_width=True)
                    else:
                        st.caption("Configure WhatsApp nas configurações")


def _form_novo_pedido():
    """Formulário para criar novo pedido."""
    with st.expander("📋 Novo Pedido", expanded=True):
        # Carregar fichas técnicas disponíveis
        try:
            fichas = ler_todos("fichas_tecnicas")
            opcoes_pratos = {f["Nome_Prato"]: f["ID"] for f in fichas if f.get("Nome_Prato")}
        except Exception:
            opcoes_pratos = {}

        with st.form("form_pedido"):
            c1, c2 = st.columns(2)
            with c1:
                mesa = st.text_input("Mesa *", placeholder="Ex: 5")
                garcom = st.text_input("Garçom", placeholder="Nome do garçom")
            with c2:
                if opcoes_pratos:
                    prato_nome = st.selectbox("Prato *", list(opcoes_pratos.keys()))
                else:
                    prato_nome = st.text_input("Prato *", placeholder="Nome do prato")
                quantidade = st.number_input("Quantidade", min_value=1, value=1)

            observacao = st.text_area("Observações", placeholder="Sem cebola, bem passado...")

            col_s, col_c = st.columns(2)
            with col_s:
                salvar = st.form_submit_button("💾 Salvar Pedido", type="primary",
                                               use_container_width=True)
            with col_c:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
            if not mesa or not prato_nome:
                st.error("Mesa e Prato são obrigatórios.")
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
                st.success(f"✅ Pedido #{numero_pedido} criado!")
                st.session_state["modal_novo_pedido"] = False
                st.rerun()

        if cancelar:
            st.session_state["modal_novo_pedido"] = False
            st.rerun()
