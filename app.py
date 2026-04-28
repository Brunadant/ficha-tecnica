"""
Ficha Técnica — Sistema de Gestão de Cozinha
Ponto de entrada principal do Streamlit.
"""

import streamlit as st
import sys
import os

# Garantir que o diretório raiz está no path
sys.path.insert(0, os.path.dirname(__file__))

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ficha Técnica | Gestão de Cozinha",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar estilizada */
[data-testid="stSidebar"] {
    background-color: #1e293b;
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    color: #38bdf8;
}
/* Métricas */
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}
/* Botões primários */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0ea5e9, #6366f1);
    border: none;
    font-weight: 600;
    border-radius: 8px;
}
/* Tabs */
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
}
/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Autenticação ──────────────────────────────────────────────────────────────
from src.services.auth import esta_logado, get_usuario, fazer_logout
from src.components.login import render_login

if not esta_logado():
    render_login()
    st.stop()

# ── Usuário autenticado ───────────────────────────────────────────────────────
usuario = get_usuario()
nome_usuario = usuario.get("Nome", "Usuária") if usuario else "Usuária"
perfil = usuario.get("Perfil", "user") if usuario else "user"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-size:2.5rem;">🍽️</div>
        <h2 style="margin:0; color:#38bdf8;">Ficha Técnica</h2>
        <p style="color:#64748b; font-size:0.8rem; margin:0;">Gestão de Cozinha</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Info do usuário
    st.markdown(f"""
    <div style="background:#0f172a; border-radius:8px; padding:0.8rem; margin-bottom:1rem;">
        <div style="color:#94a3b8; font-size:0.75rem;">USUÁRIO</div>
        <div style="color:#f1f5f9; font-weight:600;">{nome_usuario}</div>
        <div style="color:#38bdf8; font-size:0.75rem; text-transform:uppercase;">{perfil}</div>
    </div>
    """, unsafe_allow_html=True)

    # Menu de navegação
    paginas = {
        "🖥️ Painel de Produção": "painel",
        "📖 Fichas Técnicas": "fichas",
        "📦 Insumos & Estoque": "insumos",
        "✅ Checklist Diário": "checklist",
    }

    if perfil == "admin":
        paginas["⚙️ Configurações"] = "config"

    pagina_sel = st.radio(
        "Navegação",
        list(paginas.keys()),
        label_visibility="collapsed"
    )
    pagina_atual = paginas[pagina_sel]

    st.markdown("---")

    # Botão de logout
    if st.button("🚪 Sair", use_container_width=True):
        fazer_logout()
        st.rerun()

    st.markdown("""
    <div style="text-align:center; color:#334155; font-size:0.7rem; margin-top:1rem;">
        v1.0.0 · Ficha Técnica
    </div>
    """, unsafe_allow_html=True)

# ── Roteamento de Páginas ─────────────────────────────────────────────────────
if pagina_atual == "painel":
    from src.components.painel_producao import render_painel_producao
    render_painel_producao()

elif pagina_atual == "fichas":
    from src.components.fichas import render_fichas
    render_fichas()

elif pagina_atual == "insumos":
    from src.components.insumos import render_insumos
    render_insumos()

elif pagina_atual == "checklist":
    from src.components.checklist import render_checklist
    render_checklist()

elif pagina_atual == "config":
    _render_config()


def _render_config():
    pass


# Configurações (apenas admin)
if pagina_atual == "config":
    st.markdown("## ⚙️ Configurações do Sistema")
    st.markdown("---")

    from src.services.sheets import ler_todos_raw, atualizar_campo

    try:
        configs = ler_todos_raw("config_sistema")
    except Exception as e:
        st.error(f"Erro ao carregar configurações: {e}")
        st.stop()

    with st.form("form_config"):
        valores_novos = {}
        for cfg in configs:
            chave = cfg.get("Chave", "")
            valor_atual = cfg.get("Valor", "")
            descricao = cfg.get("Descricao", "")
            if chave:
                novo_val = st.text_input(
                    f"{chave}",
                    value=str(valor_atual),
                    help=descricao,
                    key=f"cfg_{chave}"
                )
                valores_novos[chave] = novo_val

        salvar_cfg = st.form_submit_button("💾 Salvar Configurações", type="primary",
                                           use_container_width=True)

    if salvar_cfg:
        for chave, valor in valores_novos.items():
            atualizar_campo("config_sistema", chave, "Valor", valor, col_id="Chave")
        st.success("✅ Configurações salvas com sucesso!")
        st.rerun()

    # Gestão de usuários (admin)
    st.markdown("---")
    st.markdown("### 👥 Usuários do Sistema")

    try:
        from src.services.sheets import ler_todos
        usuarios = ler_todos("usuarios")
        import pandas as pd
        df_users = pd.DataFrame([{
            "ID": u.get("ID"),
            "Nome": u.get("Nome"),
            "Email": u.get("Email"),
            "Perfil": u.get("Perfil"),
            "Status": u.get("Status"),
            "Último Acesso": u.get("Ultimo_Acesso"),
        } for u in usuarios])
        st.dataframe(df_users, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")

    st.markdown("---")
    st.markdown("### ➕ Novo Usuário")
    with st.form("form_novo_usuario", clear_on_submit=True):
        cu1, cu2 = st.columns(2)
        with cu1:
            novo_nome = st.text_input("Nome *")
            novo_email = st.text_input("E-mail *")
        with cu2:
            novo_perfil = st.selectbox("Perfil", ["user", "admin", "cozinheiro"])
            nova_senha = st.text_input("Senha *", type="password")

        criar_user = st.form_submit_button("Criar Usuário", type="primary",
                                           use_container_width=True)

    if criar_user:
        if not novo_nome or not novo_email or not nova_senha:
            st.error("Nome, e-mail e senha são obrigatórios.")
        else:
            import hashlib
            from src.services.sheets import proximo_id, inserir
            from datetime import datetime
            uid = proximo_id("usuarios")
            senha_h = hashlib.sha256(nova_senha.encode()).hexdigest()
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            inserir("usuarios", [uid, novo_nome, novo_email, senha_h,
                                  novo_perfil, "Ativo", agora, ""])
            st.success(f"✅ Usuário '{novo_nome}' criado com sucesso!")
            st.rerun()
