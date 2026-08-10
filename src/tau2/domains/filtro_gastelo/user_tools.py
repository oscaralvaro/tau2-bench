import json
import os

# Ruta temporal para simular el canal de comunicación (red celular)
SMS_STORAGE_PATH = "data/tau2/domains/filtro_gastelo/simulations/sms_gateway.json"

def leer_sms_recibido(phone_number: str) -> str:

    if not os.path.exists(SMS_STORAGE_PATH):
        return json.dumps({"error": "No hay mensajes SMS en la bandeja de entrada para este número."})
    
    try:
        with open(SMS_STORAGE_PATH, "r", encoding="utf-8") as f:
            database = json.load(f)
        
        if phone_number in database:
            return json.dumps({
                "status": "success",
                "phone_number": phone_number,
                "message": f"Código de verificación de Filtro Gastelo: {database[phone_number]}"
            })
        else:
            return json.dumps({"error": f"No se encontraron SMS dirigidos al número {phone_number}."})
            
    except Exception as e:
        return json.dumps({"error": f"Error al acceder al dispositivo SMS: {str(e)}"})