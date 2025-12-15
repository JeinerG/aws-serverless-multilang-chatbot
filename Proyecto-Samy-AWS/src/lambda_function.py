import json
import boto3
import logging
import random

# --- CONFIGURACIÓN ---
REGION = 'us-east-1'
TABLE_NAME = 'RestauranteMenu'

# Clientes AWS
dynamodb = boto3.resource('dynamodb', region_name=REGION)
comprehend = boto3.client('comprehend', region_name=REGION)
translate = boto3.client('translate', region_name=REGION)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event: " + json.dumps(event))
    
    try:
        # 1. RECUPERAR DATOS
        session_state = event.get('sessionState', {}) or {}
        intent_data = session_state.get('intent', {}) or {}
        intent_name = intent_data.get('name')
        slots = intent_data.get('slots', {}) or {}
        input_text = event.get('inputTranscript', "") or ""

        # --- MEJORA: DETECCIÓN HÍBRIDA (Manual + IA) ---
        idioma_usuario = 'es' # Default
        
        # A. DICCIONARIO RÁPIDO (Para frases cortas que la IA confunde)
        frases_cortas = {
            'oi': 'pt', 'olá': 'pt', 'ola': 'pt', 'bom dia': 'pt', 'tudo bem': 'pt',
            'obrigado': 'pt', 'obrigada': 'pt', 'tchau': 'pt', 'quero': 'pt',
            'hi': 'en', 'hello': 'en', 'thanks': 'en', 'bye': 'en', 'burger': 'en'
        }
        
        texto_lower = input_text.lower().strip()
        # Limpiamos signos de puntuación básicos para buscar
        texto_limpio = texto_lower.replace('!', '').replace('?', '').replace('.', '')
        
        if texto_limpio in frases_cortas:
            idioma_usuario = frases_cortas[texto_limpio]
            logger.info(f"Idioma detectado por DICCIONARIO: {idioma_usuario}")
        
        # B. IA COMPREHEND (Si no estaba en el diccionario y es largo)
        elif len(input_text) > 2:
            try:
                detect_resp = comprehend.detect_dominant_language(Text=input_text)
                idioma_detectado = detect_resp['Languages'][0]['LanguageCode']
                # Comprehend a veces devuelve 'pt' o 'pt-PT'. Usamos los primeros 2 caracteres.
                idioma_usuario = idioma_detectado[:2] 
                logger.info(f"Idioma detectado por IA: {idioma_usuario}")
            except Exception as e:
                logger.error(f"Error detectando idioma: {e}")

        # 2. TRADUCCIÓN DE ENTRADA (Si no es español, pasamos a español)
        texto_procesado = input_text
        sentimiento = 'NEUTRAL'

        if input_text and len(input_text.strip()) > 1:
            try:
                if idioma_usuario != 'es': 
                    trans = translate.translate_text(
                        Text=input_text, 
                        SourceLanguageCode=idioma_usuario, 
                        TargetLanguageCode='es'
                    )
                    texto_procesado = trans['TranslatedText']
                    logger.info(f"Texto traducido a Español: {texto_procesado}")

                # Análisis de Sentimiento
                resp_sent = comprehend.detect_sentiment(Text=texto_procesado, LanguageCode='es')
                sentimiento = resp_sent['Sentiment']
            except Exception as e:
                logger.error(f"Error traducción/sentimiento: {e}")

        # 3. CEREBRO LÓGICO (Siempre en Español)
        mensaje = "Lo siento, tuve un problema técnico."
        if not intent_name: intent_name = 'FallbackIntent'

        if intent_name == 'Saludar':
            if sentimiento == 'NEGATIVE' or any(x in texto_procesado.lower() for x in ['triste', 'mal', 'furioso']):
                mensaje = "Hola. Noto que no es un buen momento. 😟 Seré rápido. ¿Qué deseas comer?"
            else:
                saludos = [
                    "¡Hola! Bienvenido a Restaurante Samy 🍔. ¿Qué deseas pedir?",
                    "¡Buenas! Mesa lista. ¿Qué te traigo?",
                    "¡Hola! Espero que tengas mucha hambre."
                ]
                mensaje = random.choice(saludos)

        elif intent_name == 'InfoRestaurante':
            txt = texto_procesado.lower()
            if 'domicilio' in txt or 'casa' in txt or 'lleva' in txt or 'entrega' in txt:
                 mensaje = "¡Claro que sí! 🛵 Domicilios gratis en 20 minutos."
            elif 'pago' in txt or 'tarjeta' in txt or 'nequi' in txt:
                 mensaje = "Aceptamos Nequi, Daviplata, Efectivo y Tarjetas. 💳"
            elif 'horario' in txt or 'abre' in txt or 'hora' in txt:
                 mensaje = "Abrimos todos los días hasta la medianoche. 🌙"
            else:
                 mensaje = "Estamos en la Zona Rosa, abrimos hasta medianoche."

        elif intent_name == 'VerMenu':
            mensaje = "Menú: Hamburguesa ($18k), Pizza ($25k), Salchipapa ($15k) y Perros ($12k). ¿Cuál prefieres?"

        elif intent_name == 'HacerPedido':
            mensaje = procesar_pedido(slots, texto_procesado, sentimiento, input_text)

        elif intent_name == 'Confirmar' or intent_name == 'ConfirmarPedido':
            mensaje = "¡Pedido Confirmado! ✅ Ya mismo lo pasamos a cocina."

        elif intent_name == 'Despedida':
             mensaje = "¡Gracias por visitarnos! Vuelve pronto. 👋"

        elif intent_name == 'FallbackIntent':
            txt_lower = texto_procesado.lower()
            orig_lower = input_text.lower()
            
            if 'salchipapa' in orig_lower or 'salchipapa' in txt_lower:
                 mensaje = obtener_precio_db('Salchipapa', sentiment)
            elif 'pizza' in txt_lower:
                 mensaje = obtener_precio_db('Pizza', sentiment)
            elif 'hamburguesa' in txt_lower or 'burger' in orig_lower or 'hambúrguer' in orig_lower:
                 mensaje = obtener_precio_db('Hamburguesa', sentiment)
            elif 'perro' in txt_lower or 'cachorro' in orig_lower:
                 mensaje = obtener_precio_db('Perro', sentiment)
            elif 'casa' in txt_lower or 'traigan' in txt_lower:
                 mensaje = "¡Ah, domicilios! Sí, llevamos a tu casa. 🛵 ¿Qué te enviamos?"
            else:
                 mensaje = "No entendí bien. ¿Podrías decirme solo el nombre del plato? (Ej: Pizza)"
        
        else:
             mensaje = f"Entendido {intent_name}, pero no tengo respuesta configurada."

        # 4. TRADUCCIÓN DE SALIDA
        if idioma_usuario != 'es' and mensaje:
            try:
                trans_resp = translate.translate_text(
                    Text=mensaje, 
                    SourceLanguageCode='es', 
                    TargetLanguageCode=idioma_usuario
                )
                mensaje = trans_resp['TranslatedText']
            except Exception as e:
                logger.error(f"Error traduciendo respuesta final: {e}")

        # 5. RETORNO A LEX
        return {
            "sessionState": {
                "dialogAction": { "type": "Close" },
                "intent": { "name": intent_name, "state": "Fulfilled" }
            },
            "messages": [ { "contentType": "PlainText", "content": mensaje } ]
        }

    except Exception as error_critico:
        logger.error(f"CRITICAL ERROR: {str(error_critico)}")
        return {
            "sessionState": {
                "dialogAction": { "type": "Close" },
                "intent": { "name": "FallbackIntent", "state": "Fulfilled" }
            },
            "messages": [ { "contentType": "PlainText", "content": "Error técnico." } ]
        }

def procesar_pedido(slots, texto_espanol, sentiment, texto_original):
    genericos = ['algo', 'comer', 'hambre', 'menu', 'carta', 'comida', 'food', 'fome']
    if any(x in texto_espanol.lower() for x in genericos):
        return "¡Tenemos de todo! 🍔 Hamburguesas, 🍕 Pizzas y 🌭 Perros. ¿Cuál eliges?"

    val_plato = None
    if slots and slots.get('Comida'):
        val_plato = slots['Comida'].get('value', {}).get('interpretedValue') or slots['Comida'].get('value', {}).get('originalValue')

    item_busqueda = val_plato
    
    if not item_busqueda:
        txt = texto_espanol.lower()
        orig = texto_original.lower()
        if 'salchipapa' in txt: item_busqueda = 'Salchipapa'
        elif 'pizza' in txt: item_busqueda = 'Pizza'
        elif 'hamburguesa' in txt or 'burg' in orig: item_busqueda = 'Hamburguesa'
        elif 'perro' in txt or 'hot' in orig or 'cachorro' in orig: item_busqueda = 'Perro'

    if not item_busqueda:
        return "¿Qué plato deseas? Tenemos Hamburguesa, Pizza y Salchipapa."

    return obtener_precio_db(item_busqueda, sentiment)

def obtener_precio_db(raw_item, sentiment):
    if not raw_item: return "No entendí el plato."
    item = raw_item.capitalize()
    
    if 'hamb' in item.lower() or 'burg' in item.lower(): item = 'Hamburguesa'
    if 'pizz' in item.lower(): item = 'Pizza'
    if 'salch' in item.lower(): item = 'Salchipapa'
    if 'perr' in item.lower() or 'cachorro' in item.lower(): item = 'Perro'
    
    if item.endswith('s') and len(item)>4: item = item[:-1]

    try:
        table = dynamodb.Table(TABLE_NAME)
        resp = table.get_item(Key={'ItemName': item})
        if 'Item' in resp:
            precio = resp['Item'].get('Precio', '0')
            var = resp['Item'].get('Variedades', '')
            txt = f"La {item} vale ${precio}. "
            if var: txt += f"Viene: {var}. "
            txt += "¿Deseas pedirla?"
            return txt
        else:
            return f"Lo siento, no tenemos {item}. ¿Te ofrezco Pizza?"
    except Exception as e:
        return f"Error consultando el menú: {str(e)}"