# Experimento 3: Few-Shot de verificación de identidad

Agregar ejemplos breves de diálogo correcto para validación de SMS:

Usuario: quiero saber mi deuda del suministro S-1001.
Agente: Para darle esa información, necesito verificar su identidad. Enviaré un código SMS.
Herramienta: enviar_codigo_sms(user_id="48912304")
Usuario: mi código es 123456.
Herramienta: read_sms_code()
Agente: Identidad verificada. Su deuda es de 150.0 soles.

Técnica: Few-shot learning para flujos estrictos de autenticación.