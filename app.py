from flask import Flask, request, redirect, render_template
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType

app = Flask(__name__)

# Configuración de prueba
commerce_code = '597055555532'  # Código de comercio de prueba
api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'  # API Key de prueba

# Configurar el SDK de Transbank para entorno de prueba
options = WebpayOptions(commerce_code, api_key, IntegrationType.TEST)
transaction = Transaction(options)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pagar', methods=['POST'])
def pagar():
    amount = request.form['amount']
    buy_order = 'orden12345678'
    session_id = 'session12345678'
    return_url = 'http://localhost:5000/return-url'

    response = transaction.create(buy_order, session_id, amount, return_url)
    return redirect(response['url'] + '?token_ws=' + response['token'])

@app.route('/return-url', methods=['POST'])
def return_url():
    token_ws = request.form['token_ws']
    response = transaction.commit(token_ws)
    if response['response_code'] == 0:
        return "Pago exitoso"
    else:
        return "Pago rechazado"

if __name__ == '__main__':
    app.run(debug=True)
