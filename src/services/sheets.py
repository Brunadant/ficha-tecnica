"""
Serviço de conexão e CRUD com Google Sheets.
Todas as operações de banco de dados passam por este módulo.
"""

import os
import json
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Optional

SPREADSHEET_ID = "1prRiRdNRDtItH56010u7Kcs22x3DLrRGgo-EXyVGukY"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def get_client() -> gspread.Client:
    """Retorna cliente gspread autenticado (cached para evitar re-autenticação)."""
    # Tenta carregar de st.secrets (Streamlit Cloud) ou arquivo local
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except Exception:
        # Fallback para arquivo local (desenvolvimento)
        creds_path = os.path.join(os.path.dirname(__file__), "../../credentials.json")
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet(aba: str) -> gspread.Worksheet:
    """Retorna a aba especificada da planilha."""
    gc = get_client()
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.worksheet(aba)


def ler_todos(aba: str) -> list[dict]:
    """Lê todos os registros ativos (Status != 'Excluído') de uma aba."""
    ws = get_sheet(aba)
    registros = ws.get_all_records()
    return [r for r in registros if str(r.get("Status", "")).strip() != "Excluído"]


def ler_todos_raw(aba: str) -> list[dict]:
    """Lê todos os registros sem filtro de status."""
    ws = get_sheet(aba)
    return ws.get_all_records()


def inserir(aba: str, dados: list) -> None:
    """Insere uma nova linha na aba."""
    ws = get_sheet(aba)
    ws.append_row(dados, value_input_option="USER_ENTERED")


def atualizar_linha(aba: str, numero_linha: int, dados: list) -> None:
    """Atualiza uma linha inteira pelo número da linha (1-indexed, linha 1 = cabeçalho)."""
    ws = get_sheet(aba)
    col_count = len(dados)
    range_notation = f"A{numero_linha}:{chr(64 + col_count)}{numero_linha}"
    ws.update(range_notation, [dados], value_input_option="USER_ENTERED")


def excluir_logico(aba: str, id_valor: str, col_id: str = "ID", col_status: str = "Status") -> bool:
    """Exclusão lógica: altera Status para 'Excluído' sem deletar a linha."""
    ws = get_sheet(aba)
    registros = ws.get_all_records()
    cabecalhos = ws.row_values(1)

    try:
        idx_id = cabecalhos.index(col_id)
        idx_status = cabecalhos.index(col_status)
    except ValueError:
        return False

    for i, row in enumerate(registros, start=2):  # linha 2 em diante (1 = cabeçalho)
        if str(row.get(col_id, "")) == str(id_valor):
            ws.update_cell(i, idx_status + 1, "Excluído")
            return True
    return False


def buscar_por_id(aba: str, id_valor: str, col_id: str = "ID") -> Optional[dict]:
    """Busca um registro pelo ID."""
    registros = ler_todos_raw(aba)
    for r in registros:
        if str(r.get(col_id, "")) == str(id_valor):
            return r
    return None


def proximo_id(aba: str, col_id: str = "ID") -> int:
    """Gera o próximo ID sequencial para uma aba."""
    registros = ler_todos_raw(aba)
    if not registros:
        return 1
    ids = [int(r.get(col_id, 0)) for r in registros if str(r.get(col_id, "")).isdigit()]
    return max(ids) + 1 if ids else 1


def atualizar_campo(aba: str, id_valor: str, campo: str, novo_valor: str,
                    col_id: str = "ID") -> bool:
    """Atualiza um campo específico de um registro pelo ID."""
    ws = get_sheet(aba)
    cabecalhos = ws.row_values(1)
    registros = ws.get_all_records()

    try:
        idx_campo = cabecalhos.index(campo)
    except ValueError:
        return False

    for i, row in enumerate(registros, start=2):
        if str(row.get(col_id, "")) == str(id_valor):
            ws.update_cell(i, idx_campo + 1, novo_valor)
            return True
    return False


def get_config(chave: str) -> str:
    """Lê um valor da aba config_sistema."""
    try:
        registros = ler_todos_raw("config_sistema")
        for r in registros:
            if r.get("Chave") == chave:
                return str(r.get("Valor", ""))
    except Exception:
        pass
    return ""
