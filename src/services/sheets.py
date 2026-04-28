"""
Serviço de conexão e CRUD com Google Sheets.
Cache TTL de 60 segundos para evitar erro 429 (quota exceeded).
"""

import os
import time
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from typing import Optional

SPREADSHEET_ID = "1prRiRdNRDtItH56010u7Kcs22x3DLrRGgo-EXyVGukY"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Cache em memória: {aba: (timestamp, dados)}
_cache: dict[str, tuple[float, list]] = {}
CACHE_TTL = 60  # segundos


@st.cache_resource(show_spinner=False)
def get_client() -> gspread.Client:
    """Retorna cliente gspread autenticado (singleton por sessão)."""
    # 1. Streamlit Cloud secrets
    try:
        secrets = st.secrets["gcp_service_account"]
        creds_dict = {
            "type": secrets["type"],
            "project_id": secrets["project_id"],
            "private_key_id": secrets["private_key_id"],
            "private_key": secrets["private_key"],
            "client_email": secrets["client_email"],
            "client_id": secrets["client_id"],
            "auth_uri": secrets["auth_uri"],
            "token_uri": secrets["token_uri"],
            "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": secrets["client_x509_cert_url"],
            "universe_domain": secrets.get("universe_domain", "googleapis.com"),
        }
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception:
        pass

    # 2. Arquivo local (desenvolvimento)
    creds_path = os.path.join(os.path.dirname(__file__), "../../credentials.json")
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        return gspread.authorize(creds)

    raise RuntimeError(
        "Credenciais não encontradas. Configure os Secrets no Streamlit Cloud "
        "ou adicione credentials.json localmente."
    )


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    """Retorna objeto da planilha (singleton — evita abrir múltiplas conexões)."""
    return get_client().open_by_key(SPREADSHEET_ID)


def get_sheet(aba: str) -> gspread.Worksheet:
    """Retorna a aba especificada."""
    return get_spreadsheet().worksheet(aba)


def _cache_valido(aba: str) -> bool:
    if aba not in _cache:
        return False
    ts, _ = _cache[aba]
    return (time.time() - ts) < CACHE_TTL


def _ler_raw_com_cache(aba: str) -> list[dict]:
    """Lê registros com cache TTL para evitar quota 429."""
    if _cache_valido(aba):
        return _cache[aba][1]
    ws = get_sheet(aba)
    dados = ws.get_all_records()
    _cache[aba] = (time.time(), dados)
    return dados


def invalidar_cache(aba: str) -> None:
    """Remove o cache de uma aba após escrita."""
    _cache.pop(aba, None)


def ler_todos(aba: str) -> list[dict]:
    """Lê registros ativos (Status != 'Excluído') com cache."""
    registros = _ler_raw_com_cache(aba)
    return [r for r in registros if str(r.get("Status", "")).strip() != "Excluído"]


def ler_todos_raw(aba: str) -> list[dict]:
    """Lê todos os registros sem filtro, com cache."""
    return _ler_raw_com_cache(aba)


def inserir(aba: str, dados: list) -> None:
    """Insere nova linha e invalida cache da aba."""
    ws = get_sheet(aba)
    ws.append_row(dados, value_input_option="USER_ENTERED")
    invalidar_cache(aba)


def atualizar_linha(aba: str, numero_linha: int, dados: list) -> None:
    """Atualiza linha inteira e invalida cache."""
    ws = get_sheet(aba)
    col_count = len(dados)
    range_notation = f"A{numero_linha}:{chr(64 + col_count)}{numero_linha}"
    ws.update(range_notation, [dados], value_input_option="USER_ENTERED")
    invalidar_cache(aba)


def excluir_logico(aba: str, id_valor: str, col_id: str = "ID",
                   col_status: str = "Status") -> bool:
    """Exclusão lógica: altera Status para 'Excluído'."""
    ws = get_sheet(aba)
    registros = ws.get_all_records()
    cabecalhos = ws.row_values(1)

    try:
        idx_id = cabecalhos.index(col_id)
        idx_status = cabecalhos.index(col_status)
    except ValueError:
        return False

    for i, row in enumerate(registros, start=2):
        if str(row.get(col_id, "")) == str(id_valor):
            ws.update_cell(i, idx_status + 1, "Excluído")
            invalidar_cache(aba)
            return True
    return False


def buscar_por_id(aba: str, id_valor: str, col_id: str = "ID") -> Optional[dict]:
    """Busca registro pelo ID (usa cache)."""
    registros = ler_todos_raw(aba)
    for r in registros:
        if str(r.get(col_id, "")) == str(id_valor):
            return r
    return None


def proximo_id(aba: str, col_id: str = "ID") -> int:
    """Gera próximo ID sequencial (usa cache)."""
    registros = ler_todos_raw(aba)
    if not registros:
        return 1
    ids = [int(r.get(col_id, 0)) for r in registros if str(r.get(col_id, "")).isdigit()]
    return max(ids) + 1 if ids else 1


def atualizar_campo(aba: str, id_valor: str, campo: str, novo_valor: str,
                    col_id: str = "ID") -> bool:
    """Atualiza campo específico pelo ID e invalida cache."""
    ws = get_sheet(aba)
    # Lê direto da API para garantir linha correta (sem cache)
    cabecalhos = ws.row_values(1)
    registros = ws.get_all_records()

    try:
        idx_campo = cabecalhos.index(campo)
    except ValueError:
        # Coluna não existe — adiciona ao cabeçalho
        nova_col = len(cabecalhos) + 1
        ws.update_cell(1, nova_col, campo)
        cabecalhos.append(campo)
        idx_campo = len(cabecalhos) - 1

    for i, row in enumerate(registros, start=2):
        if str(row.get(col_id, "")) == str(id_valor):
            ws.update_cell(i, idx_campo + 1, novo_valor)
            invalidar_cache(aba)
            return True
    return False


def get_config(chave: str) -> str:
    """Lê valor da aba config_sistema (usa cache)."""
    try:
        registros = ler_todos_raw("config_sistema")
        for r in registros:
            if r.get("Chave") == chave:
                return str(r.get("Valor", ""))
    except Exception:
        pass
    return ""
