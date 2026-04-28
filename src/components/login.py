"""
Tela de Login — Design Gastronômico Profissional.
Paleta terrosa: laranja queimado, âmbar, marrom escuro, creme.
"""

import streamlit as st
from src.services.auth import autenticar, fazer_login


def render_login():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600;700&display=swap');

    [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse at top, #3D2000 0%, #1A0F00 60%) !important;
    }
    .login-header { text-align: center; padding: 2rem 0 1.5rem; }
    .login-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #F5A050, #E8671A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin-bottom: 0.3rem;
    }
    .login-subtitle { color: #A07850; font-size: 0.85rem; letter-spacing: 2px; text-transform: uppercase; }
    .login-card {
        background: linear-gradient(145deg, #2D1A00, #1A0F00);
        border: 1px solid #4A2E10;
        border-radius: 20px;
        padding: 2.5rem 2rem;
        box-shadow: 0 30px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(245,160,80,0.1);
    }
    .stTextInput > div > div > input {
        background: #1A0F00 !important;
        border: 1px solid #4A2E10 !important;
        border-radius: 10px !important;
        color: #F5E6C8 !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.95rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E8671A !important;
        box-shadow: 0 0 0 3px rgba(232,103,26,0.2) !important;
    }
    .stTextInput label { color: #A07850 !important; font-size: 0.8rem !important; font-weight: 600 !important; letter-spacing: 0.5px !important; }
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #E8671A, #C8500A) !important;
        border: none !important;
        color: #fff !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border-radius: 12px !important;
        padding: 0.75rem !important;
        box-shadow: 0 6px 20px rgba(232,103,26,0.4) !important;
        letter-spacing: 0.5px !important;
    }
    .footer-login { text-align: center; color: #4A2E10; font-size: 0.72rem; margin-top: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

    _, col_mid, _ = st.columns([1, 1.4, 1])
    with col_mid:
        st.markdown("""
        <div class="login-header">
            <div class="login-title">Ficha Tecnica</div>
            <div class="login-subtitle">Sistema de Gestao de Cozinha</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center; margin-bottom:1.5rem;">
            <div style="color:#F5E6C8; font-size:1.1rem; font-weight:700;">Bem-vinda de volta</div>
            <div style="color:#A07850; font-size:0.82rem;">Faca login para acessar o sistema</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_login", clear_on_submit=False):
            email = st.text_input(
                "E-MAIL",
                placeholder="seu@email.com",
                key="login_email"
            )
            senha = st.text_input(
                "SENHA",
                type="password",
                placeholder="••••••••",
                key="login_senha"
            )
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            entrar = st.form_submit_button(
                "Entrar no Sistema",
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
                    st.success(f"Bem-vinda, {usuario.get('Nome', 'Usuario')}!")
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos. Verifique os dados e tente novamente.")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="footer-login">
            Acesso restrito · Em caso de problemas, contate o administrador
        </div>
        """, unsafe_allow_html=True)
