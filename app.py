from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType
from quart import Quart, request, jsonify, redirect, render_template
from urllib.parse import quote
import logging, httpx, subprocess, datetime

#Declacación de variables

app = Quart(__name__)

commerce_code = '597055555532' 
api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'  

options = WebpayOptions(commerce_code, api_key, IntegrationType.TEST)
transaction = Transaction(options)


#Variables para API's
BDD_API = 'http://localhost:8000/api/'
api_url= ''
fecha_hoy = datetime.date.today()
fecha_formateada = fecha_hoy.strftime("%Y-%m-%d")
user='jfbadilla.mo@hotmail.com'
password='Contraseña1'

#Función para el llamado de la API del Banco Central
def construir_api_url(tipo_divisa):
    fecha_hoy = datetime.date.today()
    fecha_formateada = fecha_hoy.strftime("%Y-%m-%d")

    if tipo_divisa == "dolar":
        api_url = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user={user}&pass={quote(password)}&function=GetSeries&timeseries=F073.TCO.PRE.Z.D&firstdate={fecha_formateada}&lastdate={fecha_formateada}"
    elif tipo_divisa == "euro":
        api_url = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user={user}&pass={quote(password)}&function=GetSeries&timeseries=F072.CLP.EUR.N.O.D&firstdate={fecha_formateada}&lastdate={fecha_formateada}"
    else:
        api_url='sin API'

    return api_url

#Función para recuperar el valor de conversión de la moneda seleccionada
def valor_conversion(api_url):
    response = httpx.get(api_url)
    if httpx.get(api_url)=='sin API':
        valor_conversion=1  
        return valor_conversion
    elif response.status_code == 200:
        data = response.json()
        if "Series" in data and "Obs" in data["Series"]:
            observaciones = data["Series"]["Obs"]
            if len(observaciones) > 0:
                valor_conversion = observaciones[0]["value"]
                return float(valor_conversion)
            else:
                print("No se encontraron observaciones en la respuesta.")
        else:
            print("La estructura de la respuesta no es válida.")
    else:
        print(f"Error al obtener los datos. Código de estado: {response.status_code}")


@app.route('/', methods=['POST', 'GET'])
async def index():
    valor = 1
    try:
        #Llamada a la API de la BDD
        async with httpx.AsyncClient() as client:
            response = await client.get(BDD_API + 'producto/')

        #Se recupera la información del select para tipo de divisa
        data = await request.form
        tipo_divisa = data.get('conversion')
    
        if response.status_code == 200:
            productos = response.json()
            api_url = construir_api_url(tipo_divisa)
            if api_url == 'sin API':
                return await render_template('index.html', productos=productos, valor=valor)
            valor = valor_conversion(api_url)
            return await render_template('index.html', productos=productos, valor=valor)
        else:
            return await jsonify({"error": "Error al obtener productos de la API de Django"}), response.status_code
    except httpx.HTTPError as http_err:
        return jsonify({"error": f"HTTP error occurred: {http_err}"})
    except Exception as err:
        return jsonify({"error": f"Error occurred: {err}"}), 500



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

