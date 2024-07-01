from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType
from quart import Quart, request, jsonify, redirect, render_template, session, url_for
from urllib.parse import quote
from collections import defaultdict
import logging, httpx, subprocess, datetime

#Declacación de variables

app = Quart(__name__)

commerce_code = '597055555532' 
api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'  

options = WebpayOptions(commerce_code, api_key, IntegrationType.TEST)
transaction = Transaction(options)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

#Creación de filtros para formatear a valor monetario o fecha
def format_datetime(transaction_date, format='%d-%m-%Y %H:%M:%S'):
    """Formatea una fecha según el formato especificado."""
    if transaction_date is None:
        return ""
    date = datetime.datetime.strptime(transaction_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    # Formatear la fecha según el formato dado
    return date.strftime(format)

def format_currency(amount):
    return "{:,.0f}".format(amount).replace(",", ".")

app.jinja_env.filters['format_currency'] = format_currency
app.jinja_env.filters['format_datetime'] = format_datetime

#Variables para API's
BDD_API = 'http://127.0.0.1:8000/api/'
api_url= ''
fecha_hoy = datetime.date.today()
fecha_formateada = fecha_hoy.strftime("%Y-%m-%d")
user='jfbadilla.mo@hotmail.com'
password='Contraseña1'

async def actualizar_stock_productos(productos):
    async with httpx.AsyncClient() as client:
        for p in productos:
            response_stock= await client.get(f"{BDD_API}stock/{p}")
            stock=response_stock.json()
            for i in stock:
                cantidad_stock = i['cantidad_stock']
                print(f'Stock: {cantidad_stock}')
                update_data_stock={
                    'cantidad_stock' : cantidad_stock-1
                }
                update_response_stock = await client.put(f"{BDD_API}stock/{p}/actualizar", json=update_data_stock)
        
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
        session['divisa']=tipo_divisa
        if response.status_code == 200:
            productos = response.json()
            api_url = construir_api_url(tipo_divisa)
            if api_url == 'sin API':
                return await render_template('index.html', productos=productos, valor=valor)
            valor = valor_conversion(api_url)
            session['valor_conversion']=valor
            return await render_template('index.html', productos=productos, valor=valor, tipo_divisa=tipo_divisa)
        else:
            return await jsonify({"error": "Error al obtener productos de la API de Django"}), response.status_code
    except httpx.HTTPError as http_err:
        return jsonify({"error": f"HTTP error occurred: {http_err}"})
    except Exception as e:
        return jsonify({"error": f"Error occurred: {e}"}), 500

#Creación de la transacción Webpay
@app.route('/createWebpayTransaction', methods=['POST'])
async def create_webpay_transaction():
    form = await request.form
    amount = form['webpay_total']
    buy_order = 'orden12345678'
    session_id = 'session12345678'
    return_url = 'http://localhost:5000/getWebpayReturn'
    nombre_producto = form['nombre_producto']
    productos = nombre_producto.split(',')

    session['productos'] = productos

    try:
        response = transaction.create(buy_order, session_id, amount, return_url)
        return redirect(response['url'] + '?token_ws=' + response['token'])
    except Exception as error:
        logging.error('Error creating Webpay transaction: %s', error)
        return jsonify({"error": "Error creating Webpay transaction"}), 500


#Retorno de transacción Webpay
@app.route('/getWebpayReturn', methods=['GET'])
async def get_webpay_return():
    token_ws = request.args.get('token_ws')
    if not token_ws:
        return jsonify({"error": "token_ws es requerido"}), 400

    try:
        commit_response = transaction.commit(token_ws)
        status=commit_response['status']
        session['status']=status
        session['resultado']=commit_response
        return redirect(url_for('resultado')+f'?status={status}')
    except Exception as error:
        logging.error('Error handling Webpay return: %s', error)
        return jsonify({"error": "Error handling Webpay return", "a":f'error {error}'}), 500

#Manejo de resultado para cliente
@app.route('/resultado.html', methods=['GET','POST'])
async def resultado():
    status= session.get('status')
    resultado= session.get('resultado')
    productos=session.get('productos')
    divisa=session.get('divisa')
    valor=session.get('valor_conversion')
    productos_count = defaultdict(int)

    if status=='AUTHORIZED':
        await actualizar_stock_productos(productos)

    for producto in productos:
        productos_count[producto] += 1
    productos_con_contador = [(producto, count) for producto, count in productos_count.items()]
    return await render_template('resultado.html', resultado=resultado, status=status, productos=productos_con_contador, divisa=divisa, valor=valor)

#Opciones para crud de producto
@app.route('/producto', methods=['GET','POST'])
async def producto():
    return await render_template('producto.html')

#Creación de producto
@app.route('/createproducto', methods=['GET', 'POST'])
async def createproducto():
    try:
        data = await request.form
        nombre_producto=data.get('nombre_producto')
        valor_producto=data.get('valor_producto')
        descripcion_producto=data.get('descripcion_producto')
        tipo_producto=data.get('tipo_producto')

        create_data={
            'nombre_producto':nombre_producto,
            'valor_producto':valor_producto,
            'descripcion_producto':descripcion_producto,
            'tipo_producto':tipo_producto
        }

        create_stock_data={
            'cantidad_stock':0,
            'nombre_producto':nombre_producto,
        }

        print(create_stock_data)
        async with httpx.AsyncClient() as client:
            response_tp = await client.get(BDD_API + 'tipo_producto/')
            response = await client.post(BDD_API + 'producto/agregar', json=create_data)
            create_response_stock = await client.post(f"{BDD_API}stock/", json=create_stock_data)
        if response_tp.status_code == 200:
            tipo_producto = response_tp.json()
            return await render_template('createproducto.html', tipo_producto=tipo_producto)
        
        if response.status_code == 200 and create_response_stock.status_code == 200:
            return jsonify({"Se ha creado correctamente el producto":f"{response}"})
    except Exception as e:
        return jsonify({"error": f"Error occurred: {e}"}), 500

#Elección de producto para modificar
@app.route('/updateproducto', methods=['GET', 'POST'])
async def updateproducto():
    try:
        data = await request.form
        async with httpx.AsyncClient() as client:
            response = await client.get(BDD_API + 'producto/')
        productos = response.json()

        id_producto = data.get('id_producto')
        nombre_producto = data.get('nombre_producto')

        session['id_producto'] = id_producto
        session['nombre_producto'] = nombre_producto
        if "submit_button" in data:
            return redirect(url_for('update') + '?producto='+nombre_producto)
        return await render_template('updateproducto.html', productos=productos)
    except Exception as e:
        return jsonify({'error':f'Error: {e}'})

#Modificación de producto y stock por ID y Nombre
@app.route('/update', methods=['GET', 'POST', 'PUT'])
async def update():
    try:
        id_producto=session.get('id_producto')
        nombre_producto=session.get('nombre_producto')
        data = await request.form

        valor_producto=data.get('valor_producto')
        descripcion_producto=data.get('descripcion_producto')
        cantidad_stock=data.get('cantidad_stock')

        update_data_producto={
            'valor_producto':valor_producto,
            'descripcion_producto':descripcion_producto,
        }

        update_data_stock={
            'cantidad_stock':cantidad_stock
        }
        if not id_producto:
            return jsonify({'error': 'No product ID in session'})
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BDD_API}producto/{id_producto}")
            update_response_producto = await client.put(f"{BDD_API}producto/{id_producto}/actualizar", json=update_data_producto)
            update_response_stock = await client.put(f"{BDD_API}stock/{nombre_producto}/actualizar", json=update_data_stock)

        if response.status_code == 200:
            producto=response.json()

            if update_response_producto.status_code == 200 and update_response_stock.status_code == 200:
               return await render_template('update.html', producto=producto) 
            
            return await render_template('update.html', producto=producto)
    except Exception as e:
        return jsonify({'error':f'Error: {e}'})
    
#Eliminación de producto por ID
@app.route('/deleteproducto', methods=['GET', 'POST'])
async def deleteproducto():
    try:
        data = await request.form
        id_producto = data.get('id_producto')
        async with httpx.AsyncClient() as client:
            response = await client.get(BDD_API + 'producto/')
            delete_response = await client.delete(f"{BDD_API}producto/{id_producto}/eliminar")
        if response.status_code == 200:
            productos = response.json()
            if delete_response.status_code == 204:
                return await render_template('deleteproducto.html', productos=productos)
            return await render_template('deleteproducto.html', productos=productos)
        else:
            return jsonify({"error": "Failed to fetch products"}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Error occurred: {e}"}), 500

@app.route('/prueba')
async def prueba():
    return await render_template('prueba.html')
if __name__ == '__main__':
    app.run(debug=True)

