import os
import json
from flask import Flask, render_template, request
import sqlite3
import gspread
from google.oauth2.service_account import Credentials
from twilio.rest import Client

app = Flask(__name__)

# 🔹 Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
with open("credentials.json") as f:
    credentials_info = json.load(f)
CREDS = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
client_gsheet = gspread.authorize(CREDS)
SHEET_ID = "1SeW6s83IoVm3Jqx_rBcEF779kHHWfZDRBrZrUsHeJws"
sheet = client_gsheet.open_by_key(SHEET_ID).sheet1

# 🔹 Configuração do Twilio (WhatsApp)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
SEU_NUMERO = os.getenv("SEU_NUMERO")

client_twilio = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# 🔹 Criar Banco de Dados
def init_db():
    with sqlite3.connect("confirmados.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS convidados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                confirmacao TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

# 🔹 Rota Principal (Exibir Formulário)
@app.route('/')
def index():
    return render_template('index.html')

# 🔹 Rota para Receber Respostas do Formulário
@app.route('/confirm', methods=['POST'])
def confirmar():
    nome = request.form['nome']
    confirmacao = request.form['confirmacao']

    # 🔹 Salvar no Banco de Dados
    with sqlite3.connect("confirmados.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO convidados (nome, confirmacao) VALUES (?, ?)", (nome, confirmacao))
        conn.commit()

    # 🔹 Adicionar ao Google Sheets
    sheet.append_row([nome, confirmacao])

    # 🔹 Enviar Notificação por WhatsApp
    mensagem = f"{nome} {'CONFIRMOU' if confirmacao == 'sim' else 'NEGOU'} presença."
    client_twilio.messages.create(body=mensagem, from_=TWILIO_PHONE_NUMBER, to=SEU_NUMERO)

    return "Resposta registrada! Obrigado."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
