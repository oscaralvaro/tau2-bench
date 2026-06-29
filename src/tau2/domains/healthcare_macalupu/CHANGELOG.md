# Cambios realizados para entrega 2 y 3.

## Cambios en la autenticación de usuarios.

- Ahora todos los usuarios (doctores o pacientes) se identifican por RUN.
- Se cambió el flujo de autenticación:
  1. El agente solicita el RUN y número de teléfono de verificación al usuario.
  2. El usuario ingresa su RUN y su número de teléfono.
  3. El agente envía un código de verificación al número de teléfono asociado con dicho RUN (si coincide con el ingresado).
  4. El agente solicita el código de verificación al usuario.
  5. El usuario ingresa el código de verificación para autenticarse.
    - Sí el código es correcto: responde con un mensaje de confirmación y continúa la conversación.
    - Si el código es incorrecto: responde con un mensaje de error.
- En ningun momento se envía información del agente al usuario.

## Cambios en la base de datos.

- Se unificaron los usuarios bajo el modelo "User". Ya no existen las clases segregadas "Doctor" y "Patient".
-
