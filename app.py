import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from twilio.rest import Client
import csv

app = Flask(__name__, static_folder='static', template_folder='templates')

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
    app.logger.info("Acessando a rota principal")
    return render_template('index.html')

# 🔹 Rota para Receber Respostas do Formulário
@app.route('/confirm', methods=['POST'])
def confirmar():
    nome = request.form['nome']
    confirmacao = request.form['confirmacao']
    app.logger.info(f"Recebendo confirmação: {nome} - {confirmacao}")

    # 🔹 Salvar no Banco de Dados
    with sqlite3.connect("confirmados.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO convidados (nome, confirmacao) VALUES (?, ?)", (nome, confirmacao))
        conn.commit()

    # 🔹 Enviar Notificação por WhatsApp
    mensagem = f"{nome} {'CONFIRMOU' if confirmacao == 'sim' else 'NEGOU'} presença."
    client_twilio.messages.create(body=mensagem, from_=TWILIO_PHONE_NUMBER, to=SEU_NUMERO)

    return "Resposta registrada! Obrigado."

# 🔹 Rota de Administração (Solicitação de Senha)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == os.getenv("SENHA"):
            return redirect(url_for('lista_convidados'))
        else:
            return "Senha incorreta. Tente novamente.", 403
    return render_template('admin.html')

# 🔹 Rota para Exibir e Editar Lista de Convidados
@app.route('/lista_convidados', methods=['GET', 'POST'])
def lista_convidados():
    if request.method == 'POST':
        convidado_id = request.form['id']
        nome = request.form['nome']
        confirmacao = request.form['confirmacao']
        with sqlite3.connect("confirmados.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE convidados SET nome = ?, confirmacao = ? WHERE id = ?", (nome, confirmacao, convidado_id))
            conn.commit()
    with sqlite3.connect("confirmados.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM convidados")
        convidados = cursor.fetchall()
    return render_template('lista_convidados.html', convidados=convidados)

# 🔹 Função para Exportar Dados para CSV
def export_to_csv():
    with sqlite3.connect("confirmados.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM convidados")
        rows = cursor.fetchall()

    with open('confirmados.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Nome', 'Confirmacao'])
        writer.writerows(rows)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)