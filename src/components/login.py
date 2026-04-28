"""
Componente de tela de Login com design Dark/Slate.
"""

import streamlit as st
from src.services.auth import autenticar, fazer_login


def render_login():
    """Renderiza a tela de login. Retorna True se autenticado com sucesso."""

    # CSS customizado para a tela de login
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 2rem;
    }
    .login-logo {
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-logo h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -1px;
    }
    .login-logo p {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: -0.5rem;
    }
    .login-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.4);
    }
    .stTextInput > div > div > input {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 3px rgba(56,189,248,0.15) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-logo">
            <h1>🍽️ Ficha Técnica</h1>
            <p>Sistema de Gestão de Cozinha</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("### Acesso ao Sistema")
            st.markdown("---")

            with st.form("form_login", clear_on_submit=False):
                email = st.text_input(
                    "📧 E-mail",
                    placeholder="seu@email.com",
                    key="login_email"
                )
                senha = st.text_input(
                    "🔒 Senha",
                    type="password",
                    placeholder="••••••••",
                    key="login_senha"
                )

                col_btn1, col_btn2 = st.columns([3, 1])
                with col_btn1:
                    entrar = st.form_submit_button(
                        "Entrar →",
                        use_container_width=True,
                        type="primary"
                    )

            if entrar:
                if not email or not senha:
                    st.error("Preencha e-mail e senha.")
                else:
                    with st.spinner("Verificando credenciais..."):
                        usuario = autenticar(email, senha)
                    if usuario:
                        fazer_login(usuario)
                        st.success(f"Bem-vinda, {usuario.get('Nome', 'Usuária')}! 👋")
                        st.rerun()
                    else:
                        st.error("❌ E-mail ou senha incorretos.")

            st.markdown("---")
            st.markdown(
                "<p style='text-align:center; color:#475569; font-size:0.8rem;'>"
                "Acesso restrito. Em caso de problemas, contate o administrador.</p>",
                unsafe_allow_html=True
            )
