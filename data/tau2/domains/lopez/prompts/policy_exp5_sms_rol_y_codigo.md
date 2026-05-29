# Experimento 5 - SMS, rol y dependencias

## Tecnica

Estructura del prompt + acciones dependientes en orden fijo.

## Tareas objetivo

- `sms_cancel_pending_verified`
- `sms_order_status_wrong_code`

## Cambio probado

Se estructuro el flujo de SMS como una lista ordenada:

```text
Para operaciones sensibles:
1. enviar_codigo_verificacion_sms
2. esperar que el usuario revise su SMS
3. validar_codigo_verificacion_sms con cliente_id, rol_requerido y codigo
4. continuar solo si la validacion retorna verdadero
```

Ademas:

```text
Si el codigo SMS es incorrecto, no ejecutes la accion solicitada ni reveles informacion sensible. Comunica `codigo incorrecto`.
Cuando el codigo sea valido, comunica `codigo verificado`.
```

## Resultado observado

El flujo positivo `sms_cancel_pending_verified` obtuvo 5/5. El caso negativo `sms_order_status_wrong_code` quedo en 0/5 porque el modelo no siempre produjo exactamente la comunicacion esperada aunque la validacion fallara.
