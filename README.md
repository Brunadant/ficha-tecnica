# 🍽️ Ficha Técnica — Sistema de Gestão de Cozinha

Sistema profissional para gestão de fichas técnicas, estoque, CMV e painel de produção KDS.

---

## 🚀 Como Publicar (Streamlit Community Cloud — Gratuito)

### Passo 1 — Criar repositório no GitHub

```bash
git init
git add .
git commit -m "feat: sistema ficha tecnica v1.0"
gh repo create ficha-tecnica --private
git push -u origin main
```

> ⚠️ Certifique-se de que `credentials.json` e `.streamlit/secrets.toml` estão no `.gitignore`

### Passo 2 — Publicar no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Clique em **New app**
3. Selecione seu repositório GitHub
4. Defina o arquivo principal: `app.py`
5. Clique em **Advanced settings** → **Secrets**
6. Cole o conteúdo do arquivo `secrets.toml` (com suas credenciais reais)
7. Clique em **Deploy!**

### Passo 3 — Configurar Secrets no Streamlit Cloud

No painel do Streamlit Cloud, em **Settings → Secrets**, adicione:

```toml
[gcp_service_account]
type = "service_account"
project_id = "ficha-tecnica-494713"
private_key_id = "0a5321acd89627e3b28e84f9b44d97632f81b6a0"
private_key = "-----BEGIN PRIVATE KEY-----\n...SUA CHAVE...\n-----END PRIVATE KEY-----\n"
client_email = "fichatecnica@ficha-tecnica-494713.iam.gserviceaccount.com"
client_id = "115430696884022299754"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/fichatecnica%40ficha-tecnica-494713.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

---

## 🔐 Acesso Inicial

| Campo | Valor |
|-------|-------|
| E-mail | `bruna@fichatecnica.com` |
| Senha | `admin123` |

> ⚠️ **Altere a senha imediatamente após o primeiro acesso** em Configurações → Usuários.

---

## 📁 Estrutura do Projeto

```
ficha_tecnica/
├── app.py                          # Ponto de entrada principal
├── requirements.txt                # Dependências Python
├── credentials.json                # ⚠️ NÃO COMMITAR — credenciais locais
├── setup_sheets.py                 # Script de setup inicial da planilha
├── .streamlit/
│   ├── config.toml                 # Tema Dark/Slate
│   └── secrets.toml.template       # Template para secrets de produção
└── src/
    ├── services/
    │   ├── sheets.py               # CRUD Google Sheets
    │   └── auth.py                 # Autenticação login/senha
    ├── components/
    │   ├── login.py                # Tela de login
    │   ├── painel_producao.py      # KDS — Painel de Produção
    │   ├── fichas.py               # Fichas Técnicas + CMV
    │   ├── checklist.py            # Checklist Diário
    │   └── insumos.py              # Gestão de Insumos/Estoque
    └── utils/
        ├── cmv.py                  # Cálculos CMV, Markup, conversão
        └── whatsapp.py             # Links WhatsApp pré-preenchidos
```

---

## 🗄️ Abas da Planilha Google Sheets

| Aba | Descrição |
|-----|-----------|
| `usuarios` | Usuários do sistema com hash de senha |
| `insumos` | Cadastro de insumos com estoque |
| `fichas_tecnicas` | Receitas com dados de CMV |
| `ficha_ingredientes` | Ingredientes de cada ficha |
| `pedidos` | Pedidos do painel KDS |
| `checklist_cozinha` | Checklist diário da cozinha |
| `movimentacao_estoque` | Entradas e saídas de estoque |
| `cmv_historico` | Histórico de cálculos de CMV |
| `config_sistema` | Configurações gerais |

---

## 💡 Regras de Negócio

- **Exclusão Lógica:** Nenhum dado é deletado fisicamente. O campo `Status` é alterado para `Excluído`.
- **CMV Profissional:** Custo = Ingredientes + Mão de Obra + Margem de Perda (%).
- **Painel KDS:** Fluxo Pendente → Em Preparo → Pronto → Entregue.
- **WhatsApp:** Links gerados automaticamente para notificações da cozinha.

---

## 🔧 Executar Localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```
