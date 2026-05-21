from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class DivemotorUserTools(ToolKitBase):
    @is_tool(ToolType.READ)
    def recibir_codigo_sms(self, cliente_id: str):
        registro = self.db.codigos_sms.get(cliente_id)

        if not registro:
            return "No hay codigo SMS para este cliente"

        return {
            "cliente_id": cliente_id,
            "codigo": registro.codigo,
            "rol_requerido": registro.rol_requerido,
        }

    @is_tool(ToolType.READ)
    def dar_codigo_sms_incorrecto(self, cliente_id: str):
        registro = self.db.codigos_sms.get(cliente_id)

        if not registro:
            return "No hay codigo SMS para este cliente"

        return {
            "cliente_id": cliente_id,
            "codigo": "000000",
            "rol_requerido": registro.rol_requerido,
        }
