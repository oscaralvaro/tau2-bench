# Experimento 2: few-shot de verificacion SMS

Agregar ejemplos breves de dialogo correcto:

Usuario: quiero aprobar mi cotizacion cot_1.
Agente: Para aprobarla debo verificar tu identidad. Enviare un codigo SMS.
Herramienta: enviar_codigo_sms(cliente_id="c1", rol_requerido="user")
Usuario: mi codigo es 482148.
Herramienta: verificar_codigo_sms(cliente_id="c1", codigo="482148", rol_requerido="user")
Agente: Tu identidad fue verificada. Ahora puedo aprobar la cotizacion.

Tecnica: few-shot learning.
