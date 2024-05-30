from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType
from quart import Quart, request, jsonify, redirect, render_template
import logging

app = Quart(__name__)

commerce_code = '597055555532' 
api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'  

options = WebpayOptions(commerce_code, api_key, IntegrationType.TEST)
transaction = Transaction(options)


@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/createWebpayTransaction', methods=['POST'])
async def create_webpay_transaction():
    
    form = await request.form
    amount = form['amount']
    
    buy_order = 'orden12345678'
    session_id = 'session12345678'
    return_url = 'http://localhost:5000/getWebpayReturn'
    
    try:
        response = transaction.create(buy_order, session_id, amount, return_url)
        return redirect(response['url'] + '?token_ws=' + response['token'])
    except Exception as error:
        logging.error('Error creating Webpay transaction: %s', error)
        return jsonify({"error": "Error creating Webpay transaction"}), 500

@app.route('/getWebpayReturn', methods=['GET'])
async def get_webpay_return():
    token_ws = request.args.get('token_ws')

    if not token_ws:
        return jsonify({"error": "token_ws es requerido"}), 400

    try:
        commit_response = transaction.commit(token_ws)
        return jsonify(commit_response)
    except Exception as error:
        logging.error('Error handling Webpay return: %s', error)
        return jsonify({"error": "Error handling Webpay return"}), 500
    
if __name__ == '__main__':
    app.run(debug=True)

