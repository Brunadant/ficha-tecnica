"""
Script de configuração inicial da planilha Google Sheets.
Cria todas as abas e cabeçalhos necessários para o sistema Ficha Técnica.
Execute uma única vez: python3 setup_sheets.py
"""

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1prRiRdNRDtItH56010u7Kcs22x3DLrRGgo-EXyVGukY"
CREDENTIALS_FILE = "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Definição das abas e seus cabeçalhos
SHEETS_CONFIG = {
    "usuarios": [
        "ID", "Nome", "Email", "Senha_Hash", "Perfil",
        "Status", "Criado_Em", "Ultimo_Acesso"
    ],
    "insumos": [
        "ID", "Nome", "Categoria", "Unidade_Compra", "Unidade_Uso",
        "Fator_Conversao", "Custo_Unitario", "Estoque_Atual",
        "Estoque_Minimo", "Fornecedor", "Status", "Atualizado_Em"
    ],
    "fichas_tecnicas": [
        "ID", "Nome_Prato", "Categoria", "Rendimento_Porcoes",
        "Tempo_Preparo_Min", "Modo_Preparo", "Foto_URL",
        "Custo_MO", "Margem_Perda_Pct", "Preco_Venda",
        "Status", "Criado_Em", "Atualizado_Em"
    ],
    "ficha_ingredientes": [
        "ID", "Ficha_ID", "Insumo_ID", "Nome_Insumo",
        "Quantidade", "Unidade", "Custo_Unitario", "Custo_Total", "Observacao"
    ],
    "pedidos": [
        "ID", "Numero_Pedido", "Mesa", "Garcom", "Prato_ID",
        "Nome_Prato", "Quantidade", "Observacao",
        "Status", "Criado_Em", "Atualizado_Em", "Concluido_Em"
    ],
    "checklist_cozinha": [
        "ID", "Data", "Turno", "Responsavel",
        "Item", "Categoria", "Concluido", "Hora_Conclusao", "Observacao", "Status", "Editado_Por"
    ],
    "movimentacao_estoque": [
        "ID", "Data", "Insumo_ID", "Nome_Insumo", "Tipo",
        "Quantidade", "Unidade", "Motivo", "Responsavel", "Status"
    ],
    "cmv_historico": [
        "ID", "Data", "Ficha_ID", "Nome_Prato",
        "Custo_Ingredientes", "Custo_MO", "Custo_Perda",
        "Custo_Total", "Preco_Venda", "CMV_Pct", "Markup", "Status"
    ],
    "config_sistema": [
        "Chave", "Valor", "Descricao", "Atualizado_Em"
    ],
}

# Dados iniciais para config_sistema
CONFIG_INICIAL = [
    ["nome_estabelecimento", "Restaurante", "Nome do estabelecimento", ""],
    ["whatsapp_cozinha", "", "Número WhatsApp da cozinha (ex: 5511999999999)", ""],
    ["margem_perda_padrao", "5", "Margem de perda padrão em %", ""],
    ["custo_mo_hora", "15.00", "Custo da mão de obra por hora (R$)", ""],
    ["versao_sistema", "1.0.0", "Versão atual do sistema", ""],
]

# Usuário admin padrão (senha: admin123 - altere após o primeiro acesso)
import hashlib
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

USUARIO_ADMIN = [
    ["1", "Bruna Marcela", "bruna@fichatecnica.com",
     hash_senha("admin123"), "admin", "Ativo", "", ""]
]


def setup_planilha():
    print("🔗 Conectando ao Google Sheets...")
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)

    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
        print(f"✅ Planilha encontrada: {sh.title}")
    except Exception as e:
        print(f"❌ Erro ao abrir planilha: {e}")
        return

    abas_existentes = [ws.title for ws in sh.worksheets()]
    print(f"📋 Abas existentes: {abas_existentes}")

    for nome_aba, cabecalhos in SHEETS_CONFIG.items():
        if nome_aba in abas_existentes:
            ws = sh.worksheet(nome_aba)
            # Verifica se já tem cabeçalho
            primeira_linha = ws.row_values(1)
            if not primeira_linha:
                ws.append_row(cabecalhos)
                print(f"  ✏️  Cabeçalho adicionado em aba existente: {nome_aba}")
            else:
                print(f"  ⏭️  Aba '{nome_aba}' já possui cabeçalho, pulando.")
        else:
            ws = sh.add_worksheet(title=nome_aba, rows=1000, cols=len(cabecalhos) + 2)
            ws.append_row(cabecalhos)
            print(f"  ✅ Aba criada: {nome_aba} ({len(cabecalhos)} colunas)")

        # Formatar cabeçalho (negrito + cor de fundo)
        try:
            ws = sh.worksheet(nome_aba)
            ws.format("1:1", {
                "backgroundColor": {"red": 0.059, "green": 0.094, "blue": 0.161},
                "textFormat": {"bold": True, "foregroundColor": {"red": 0.22, "green": 0.745, "blue": 0.973}},
                "horizontalAlignment": "CENTER"
            })
        except Exception:
            pass  # Formatação é opcional

    # Popular config_sistema se vazia
    ws_config = sh.worksheet("config_sistema")
    dados_config = ws_config.get_all_values()
    if len(dados_config) <= 1:
        for row in CONFIG_INICIAL:
            ws_config.append_row(row)
        print("  ✅ Configurações iniciais inseridas em config_sistema")

    # Popular usuário admin se vazio
    ws_users = sh.worksheet("usuarios")
    dados_users = ws_users.get_all_values()
    if len(dados_users) <= 1:
        for row in USUARIO_ADMIN:
            ws_users.append_row(row)
        print("  ✅ Usuário admin criado (email: bruna@fichatecnica.com | senha: admin123)")

    print("\n🎉 Setup concluído com sucesso!")
    print(f"🔗 Planilha: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("\n⚠️  IMPORTANTE: Altere a senha do admin após o primeiro acesso!")


if __name__ == "__main__":
    setup_planilha()
