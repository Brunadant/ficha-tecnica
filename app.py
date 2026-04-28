"""
Ficha Técnica — Sistema de Gestão de Cozinha
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Ficha Técnica | Gestão de Cozinha",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS Global
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-deep:      #1A0F00;
    --bg-card:      #2D1A00;
    --bg-hover:     #3D2500;
    --accent:       #E8671A;
    --accent-light: #F5A050;
    --amber:        #D4A017;
    --cream:        #F5E6C8;
    --muted:        #A07850;
    --border:       #4A2E10;
    --success:      #4CAF50;
    --warning:      #FFC107;
    --danger:       #F44336;
    --info:         #29B6F6;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-deep) !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2D1A00 0%, #1A0F00 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--cream) !important; }

h1 { color: var(--cream) !important; font-weight: 800 !important; }
h2 { color: var(--accent-light) !important; font-weight: 700 !important; }
h3 { color: var(--amber) !important; font-weight: 600 !important; }

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #E8671A, #D4580A) !important;
    border: none !important; color: #fff !important;
    font-weight: 700 !important; border-radius: 10px !important;
    box-shadow: 0 4px 15px rgba(232,103,26,0.35) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--cream) !important; border-radius: 10px !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important; color: var(--cream) !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.8rem !important; font-weight: 800 !important;
    color: var(--accent-light) !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.8rem !important; }
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important; padding: 1rem !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important; border-radius: 10px !important;
    padding: 4px !important; gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--muted) !important;
    border-radius: 8px !important; font-weight: 600 !important;
}
.stTabs [aria-selected="true"] { background: var(--accent) !important; color: #fff !important; }

[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important; border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: var(--cream) !important; font-weight: 600 !important; }

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important; border-radius: 10px !important;
}

.stSuccess { background: rgba(76,175,80,0.15) !important; border-left: 4px solid #4CAF50 !important; border-radius: 8px !important; }
.stError   { background: rgba(244,67,54,0.15) !important; border-left: 4px solid #F44336 !important; border-radius: 8px !important; }
.stWarning { background: rgba(255,193,7,0.15) !important; border-left: 4px solid #FFC107 !important; border-radius: 8px !important; }
.stInfo    { background: rgba(41,182,246,0.15) !important; border-left: 4px solid #29B6F6 !important; border-radius: 8px !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

hr { border-color: var(--border) !important; }

[data-testid="stForm"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important; padding: 1.5rem !important;
}

.stCheckbox label { color: var(--cream) !important; }
[data-baseweb="select"] > div { background: var(--bg-card) !important; border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# Autenticação
from src.services.auth import esta_logado, get_usuario, fazer_logout
from src.components.login import render_login

if not esta_logado():
    render_login()
    st.stop()

usuario = get_usuario()
nome_usuario = usuario.get("Nome", "Usuário") if usuario else "Usuário"
perfil = usuario.get("Perfil", "user") if usuario else "user"

PERFIL_ATENDENTE = perfil == "atendente"
PERFIL_ADMIN = perfil == "admin"

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:1.5rem 0 1rem;">
        <div style="font-size:1.6rem; font-weight:800; color:#F5A050; letter-spacing:-0.5px;">
            Ficha Tecnica
        </div>
        <div style="color:#A07850; font-size:0.75rem; letter-spacing:1px; text-transform:uppercase;">
            Gestao de Cozinha
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#4A2E10; margin:0 0 1rem;">', unsafe_allow_html=True)

    badge_color = {"admin": "#E8671A", "cozinheiro": "#D4A017", "atendente": "#4CAF50"}.get(perfil, "#A07850")
    st.markdown(f"""
    <div style="background:#2D1A00; border:1px solid #4A2E10; border-radius:10px;
                padding:0.8rem 1rem; margin-bottom:1rem;">
        <div style="color:#A07850; font-size:0.7rem; letter-spacing:1px;
                    text-transform:uppercase; margin-bottom:0.3rem;">USUARIO</div>
        <div style="color:#F5E6C8; font-weight:700; font-size:1rem;">{nome_usuario}</div>
        <span style="background:{badge_color}22; color:{badge_color}; font-size:0.7rem;
              font-weight:700; padding:2px 8px; border-radius:20px;
              border:1px solid {badge_color}44; text-transform:uppercase; letter-spacing:0.5px;">
            {perfil}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if PERFIL_ATENDENTE:
        paginas = {
            "Painel de Producao": "painel",
            "Checklist Diario": "checklist",
        }
    else:
        paginas = {
            "Painel de Producao": "painel",
            "Fichas Tecnicas": "fichas",
            "Insumos e Estoque": "insumos",
            "Checklist Diario": "checklist",
        }
        if PERFIL_ADMIN:
            paginas["Configuracoes"] = "config"

    pagina_sel = st.radio("Navegacao", list(paginas.keys()), label_visibility="collapsed")
    pagina_atual = paginas[pagina_sel]

    st.markdown('<hr style="border-color:#4A2E10; margin:1rem 0;">', unsafe_allow_html=True)

    if st.button("Sair", use_container_width=True):
        fazer_logout()
        st.rerun()

    st.markdown("""
    <div style="text-align:center; color:#4A2E10; font-size:0.65rem; margin-top:1.5rem;">
        v1.2.0 · Ficha Tecnica Pro
    </div>
    """, unsafe_allow_html=True)

# Roteamento
if pagina_atual == "painel":
    from src.components.painel_producao import render_painel_producao
    render_painel_producao()

elif pagina_atual == "fichas":
    if PERFIL_ATENDENTE:
        st.error("Acesso nao autorizado.")
        st.stop()
    from src.components.fichas import render_fichas
    render_fichas()

elif pagina_atual == "insumos":
    if PERFIL_ATENDENTE:
        st.error("Acesso nao autorizado.")
        st.stop()
    from src.components.insumos import render_insumos
    render_insumos()

elif pagina_atual == "checklist":
    from src.components.checklist import render_checklist
    render_checklist()

elif pagina_atual == "config":
    if not PERFIL_ADMIN:
        st.error("Acesso nao autorizado.")
        st.stop()
    else:
        _CONFIG_PENDENTE = True
else:
    _CONFIG_PENDENTE = False


def _render_configuracoes_admin():
    from src.services.sheets import ler_todos, ler_todos_raw, atualizar_campo, proximo_id, inserir, invalidar_cache
    from datetime import datetime
    import hashlib
    import pandas as pd

    st.markdown("## Configuracoes do Sistema")
    st.markdown("---")

    aba_cfg = st.tabs(["Parametros", "Usuarios", "Funcionarios"])

    # ── Aba Parâmetros ──────────────────────────────────────────────────────────
    with aba_cfg[0]:
        st.markdown("### Parametros do Sistema")
        try:
            configs = ler_todos_raw("config_sistema")
        except Exception as e:
            st.error(f"Erro ao carregar configuracoes: {e}")
            configs = []

        if configs:
            with st.form("form_config"):
                valores_novos = {}
                cols = st.columns(2)
                for i, cfg in enumerate(configs):
                    chave = cfg.get("Chave", "")
                    valor_atual = cfg.get("Valor", "")
                    descricao = cfg.get("Descricao", "")
                    if chave:
                        with cols[i % 2]:
                            novo_val = st.text_input(
                                chave, value=str(valor_atual),
                                help=descricao, key=f"cfg_{chave}"
                            )
                            valores_novos[chave] = novo_val

                salvar_cfg = st.form_submit_button("Salvar Configuracoes",
                                                   type="primary", use_container_width=True)

            if salvar_cfg:
                erros = 0
                for chave, valor in valores_novos.items():
                    try:
                        atualizar_campo("config_sistema", chave, "Valor", valor, col_id="Chave")
                    except Exception:
                        erros += 1
                invalidar_cache("config_sistema")
                if erros == 0:
                    st.success("Configuracoes salvas com sucesso!")
                else:
                    st.warning(f"{erros} configuracao(oes) nao puderam ser salvas.")
                st.rerun()
        else:
            st.info("Nenhuma configuracao encontrada. Execute setup_sheets.py.")

    # ── Aba Usuários ────────────────────────────────────────────────────────────
    with aba_cfg[1]:
        st.markdown("### Usuarios do Sistema")
        try:
            usuarios_list = ler_todos("usuarios")
            if usuarios_list:
                df_users = pd.DataFrame([{
                    "ID": u.get("ID"), "Nome": u.get("Nome"),
                    "E-mail": u.get("Email"), "Perfil": u.get("Perfil"),
                    "Status": u.get("Status"), "Ultimo Acesso": u.get("Ultimo_Acesso"),
                } for u in usuarios_list])
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum usuario cadastrado.")
        except Exception as e:
            st.error(f"Erro ao carregar usuarios: {e}")

        st.markdown("---")
        st.markdown("### Novo Usuario")
        with st.form("form_novo_usuario", clear_on_submit=True):
            cu1, cu2 = st.columns(2)
            with cu1:
                novo_nome = st.text_input("Nome *")
                novo_email = st.text_input("E-mail *")
            with cu2:
                novo_perfil = st.selectbox("Perfil", ["user", "admin", "cozinheiro", "atendente"])
                nova_senha = st.text_input("Senha *", type="password")
            criar_user = st.form_submit_button("Criar Usuario", type="primary",
                                               use_container_width=True)

        if criar_user:
            if not novo_nome or not novo_email or not nova_senha:
                st.error("Nome, e-mail e senha sao obrigatorios.")
            else:
                uid = proximo_id("usuarios")
                senha_h = hashlib.sha256(nova_senha.encode()).hexdigest()
                agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                inserir("usuarios", [uid, novo_nome, novo_email, senha_h,
                                     novo_perfil, "Ativo", agora, ""])
                st.success(f"Usuario '{novo_nome}' criado com sucesso!")
                st.rerun()

    # ── Aba Funcionários ────────────────────────────────────────────────────────
    with aba_cfg[2]:
        st.markdown("### Funcionarios da Cozinha")
        st.caption("Cadastre os funcionarios para atribuicao no checklist diario.")

        try:
            funcs = ler_todos("funcionarios")
            if funcs:
                df_funcs = pd.DataFrame([{
                    "ID": f.get("ID"), "Nome": f.get("Nome"),
                    "Cargo": f.get("Cargo"), "Turno": f.get("Turno"),
                    "Telefone": f.get("Telefone"), "Status": f.get("Status"),
                } for f in funcs])
                st.dataframe(df_funcs, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum funcionario cadastrado ainda.")
        except Exception as e:
            st.warning(f"Aba 'funcionarios' nao encontrada. Execute setup_sheets.py para criar. ({e})")

        st.markdown("---")
        st.markdown("### Novo Funcionario")
        with st.form("form_novo_func", clear_on_submit=True):
            ff1, ff2 = st.columns(2)
            with ff1:
                func_nome = st.text_input("Nome completo *")
                func_cargo = st.selectbox("Cargo", [
                    "Cozinheiro", "Auxiliar de Cozinha", "Confeiteiro",
                    "Garcom", "Atendente", "Gerente", "Outro"
                ])
            with ff2:
                func_turno = st.selectbox("Turno", ["Manha", "Tarde", "Noite", "Integral"])
                func_tel = st.text_input("Telefone (WhatsApp)", placeholder="5511999999999")
            criar_func = st.form_submit_button("Cadastrar Funcionario", type="primary",
                                               use_container_width=True)

        if criar_func:
            if not func_nome:
                st.error("Nome e obrigatorio.")
            else:
                try:
                    fid = proximo_id("funcionarios")
                    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    inserir("funcionarios", [fid, func_nome, func_cargo,
                                             func_turno, func_tel, "Ativo", agora])
                    st.success(f"Funcionario '{func_nome}' cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}. Verifique se a aba 'funcionarios' existe na planilha.")


# Chama configuracoes (definida apos o roteamento para evitar NameError)
if pagina_atual == "config" and PERFIL_ADMIN:
    _render_configuracoes_admin()
