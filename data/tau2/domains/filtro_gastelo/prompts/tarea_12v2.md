{
    "id": "12",
    "description": {
      "purpose": "Caso de flujo complejo con verificacion de historial: equivalente agotado, consulta de cliente con ID conocido y pedido a proveedor por 2 unidades.",
      "relevant_policies": "Reglas 2, 3, 4 y 7",
      "notes": "Prueba exhaustiva de ramificacion logica y consulta previa. El agente debe verificar stock del principal, verificar equivalente, consultar el historial del cliente usando su ID para evaluar condiciones y finalmente ejecutar pedido a proveedor solicitando activamente los datos para 2 unidades."
    },
    "user_scenario": {
      "persona": "Encargada de compras logisticas de una empresa, cooperativa y dispuesta a brindar informacion conforme el agente la solicite.",
      "instructions": {
        "domain": "filtro_gastelo",
        "reason_for_call": "Necesito 2 filtros KOM-000 para mi maquinaria.",
        "known_info": "ID del filtro: KOM-000, Nombre: Maria Abad, Celular: 920111222, Cantidad: 2, ID de Cliente: C-003",
        "unknown_info": null,
        "task_instructions": "Pregunta por el estado del filtro KOM-000 indicando que necesitas 2 unidades. Si el agente te indica que no hay stock local ni reemplazos equivalentes disponibles, acepta la opcion de registrar un pedido especial a proveedor. Espera a que el agente te solicite activamente tus datos de contacto para proporcionarle tu nombre (Maria Abad), telefono (920111222) e ID de cliente (CLI-920) de manera ordenada."
      }
    },
    "initial_state": null,
    "evaluation_criteria": {
      "actions": [
        {
          "action_id": "12_0",
          "name": "get_filter_status",
          "arguments": { "item_id": "KOM-000" },
          "compare_args": [ "item_id" ]
        },
        {
          "action_id": "12_1",
          "name": "get_equivalent_filter",
          "arguments": { "item_id": "KOM-000" },
          "compare_args": [ "item_id" ]
        },
        {
          "action_id": "12_2",
          "name": "get_customer_details",
          "arguments": { "customer_id": "C-003" },
          "compare_args": [ "customer_id" ]
        },
        {
          "action_id": "12_3",
          "name": "register_provider_order",
          "arguments": {
            "customer_name": "Maria Abad",
            "customer_phone": "920111222",
            "item_id": "KOM-000",
            "quantity": 2
          },
          "compare_args": [ "item_id", "customer_name", "customer_phone", "quantity" ]
        }
      ],
      "nl_assertions": [
        "El agente debe verificar primero si hay stock del KOM-000.",
        "El agente debe llamar obligatoriamente a la herramienta get_equivalent_filter antes de dar por perdida la venta en tienda.",
        "El agente debe informar transparentemente que el equivalente tampoco registra unidades en el inventario.",
        "El agente debe consultar obligatoriamente el historial del cliente (get_customer_details) usando su ID antes de proceder con el registro a proveedor.",
        "El agente debe solicitar y guardar con total precisión los datos de contacto en register_provider_order con la cantidad de 2 unidades e informar el plazo normativo de 3 a 5 días hábiles."
      ],
      "reward_basis": [ "DB", "COMMUNICATE" ]
    }
  }