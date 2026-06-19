# Hallazgos acumulados E1-E4 - GamerBit Store / Lopez

IMPORTANTE: esta seccion debe completarse con tus conclusiones propias. Usa este archivo como estructura y agrega fragmentos reales de JSON, valores exactos y observaciones que hayas visto durante las corridas.

## 1. Descripcion del dominio y las tareas

TODO Zulema:

- Empresa/dominio:
- Publico objetivo:
- Numero de tareas implementadas:
- Tipos de tareas: ventas, cancelaciones, soporte, garantia, SMS, adversariales.
- Numero total aproximado de simulaciones E1-E4:

## 2. Evolucion del agente a lo largo de las entregas

Nota: E1 uso pass^1. E2, E3 y E4 usan pass^5. No compares E1 directamente con E2-E4 sin explicar la diferencia.

| Entrega | Cambio principal | Metrica | Resultado | Delta vs E3 |
|---------|------------------|---------|-----------|-------------|
| E1 | Baseline sin prompt engineering | pass^1 | TODO | - |
| E2 | Prompt engineering / politica clara | pass^5 | TODO | - |
| E3 | Mejoras dirigidas por failure taxonomy | pass^5 | TODO | - |
| E4 | RAG + think, mejor condicion | pass^5 | TODO | TODO |

Para E2-E4: usar pass^5 promedio sobre las mismas 10 tareas de E4.

## 3. Categorias de fallo mas frecuentes

Completar 3-5 categorias con evidencia del JSON.

### Categoria 1: TODO

- Descripcion:
- Ejemplo JSON real:

```json
TODO
```

- Evolucion entre entregas:

### Categoria 2: TODO

- Descripcion:
- Ejemplo JSON real:

```json
TODO
```

- Evolucion entre entregas:

### Categoria 3: TODO

- Descripcion:
- Ejemplo JSON real:

```json
TODO
```

- Evolucion entre entregas:

## 4. Comportamiento especifico de Gemma 3/4 en el dominio

TODO Zulema: escribir observaciones propias. Incluir al menos 2 ejemplos concretos con fragmentos JSON reales.

Preguntas guia:

- El modelo alucina nombres de herramientas o argumentos?
- Confirma acciones sin verificar condiciones?
- Que pasa en conversaciones largas?
- En que tareas mejoro con prompt engineering, RAG o think?

### Ejemplo 1

```json
TODO
```

### Ejemplo 2

```json
TODO
```

## 5. Recomendaciones para un sistema de produccion

TODO Zulema: responder con recomendaciones especificas del dominio.

- Es Gemma suficientemente confiable sin supervision humana?
- Que tareas se pueden automatizar?
- Que tareas requieren humano?
- RAG y think fueron suficientes?
- Umbral minimo aceptable de pass^5 por tipo de tarea:
