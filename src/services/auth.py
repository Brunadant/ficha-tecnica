"""
Servico de autenticacao com login/senha.
Senhas armazenadas como SHA-256 hash no Google Sheets.
A autenticacao SEMPRE le direto da API (sem cache) para garantir seguranca.
"""

import hashlib
import streamlit as st
from datetime import datetime


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def autenticar(email: str, senha: str) -> dict | None:
    """
    Verifica credenciais contra a aba 'usuarios'.
    Le DIRETAMENTE do Google Sheets (sem cache) para garantir dados atuais.
    Retorna o dict do usuario se valido, None caso contrario.
    """
    try:
        from src.services.sheets import get_sheet
        ws = get_sheet("usuarios")
        registros = ws.get_all_records()

        senha_hash = hash_senha(senha)
        email_lower = email.strip().lower()

        for u in registros:
            email_planilha = str(u.get("Email", "")).strip().lower()
            senha_planilha = str(u.get("Senha_Hash", "")).strip()
            status_planilha = str(u.get("Status", "")).strip()

            if (email_planilha == email_lower
                    and senha_planilha == senha_hash
                    and status_planilha == "Ativo"):
                # Atualiza ultimo acesso (nao bloqueia o login se falhar)
                try:
                    from src.services.sheets import atualizar_campo
                    atualizar_campo(
                        "usuarios", str(u["ID"]), "Ultimo_Acesso",
                        datetime.now().strftime("%d/%m/%Y %H:%M")
                    )
                except Exception:
                    pass
                return u

        return None

    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {e}")
        return None


def esta_logado() -> bool:
    return st.session_state.get("usuario_logado") is not None


def get_usuario() -> dict | None:
    return st.session_state.get("usuario_logado")


def fazer_login(usuario: dict) -> None:
    st.session_state["usuario_logado"] = usuario


def fazer_logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def requer_login():
    if not esta_logado():
        st.stop()


def e_admin() -> bool:
    u = get_usuario()
    return u is not None and str(u.get("Perfil", "")).lower() == "admin"
