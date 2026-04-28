"""
Serviço de autenticação com login/senha.
Senhas armazenadas como SHA-256 hash no Google Sheets.
"""

import hashlib
import streamlit as st
from datetime import datetime
from src.services.sheets import ler_todos_raw, atualizar_campo


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def autenticar(email: str, senha: str) -> dict | None:
    """
    Verifica credenciais contra a aba 'usuarios'.
    Retorna o dict do usuário se válido, None caso contrário.
    """
    try:
        usuarios = ler_todos_raw("usuarios")
        senha_hash = hash_senha(senha)
        for u in usuarios:
            if (str(u.get("Email", "")).strip().lower() == email.strip().lower()
                    and str(u.get("Senha_Hash", "")).strip() == senha_hash
                    and str(u.get("Status", "")).strip() == "Ativo"):
                # Atualiza último acesso
                atualizar_campo("usuarios", str(u["ID"]), "Ultimo_Acesso",
                                datetime.now().strftime("%d/%m/%Y %H:%M"))
                return u
    except Exception as e:
        st.error(f"Erro ao autenticar: {e}")
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
    """Decorator/guard: redireciona para login se não autenticado."""
    if not esta_logado():
        st.stop()


def e_admin() -> bool:
    u = get_usuario()
    return u is not None and str(u.get("Perfil", "")).lower() == "admin"
