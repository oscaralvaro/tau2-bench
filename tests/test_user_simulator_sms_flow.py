from tau2.data_model.message import AssistantMessage, ToolMessage
from tau2.data_model.tasks import StructuredUserInstructions
from tau2.environment.tool import as_tool
from tau2.user.user_simulator import UserSimulator


def _make_simulator():
    def receive_sms_code(user_id: str) -> dict:
        return {"user_id": user_id, "code": "123456"}

    instructions = StructuredUserInstructions(
        domain="ecommerce_calle",
        reason_for_call="Quiero cancelar mi pedido ORD-001",
        known_info="user_id: U001, order_id: ORD-001",
        task_instructions="Cuando te pidan el codigo SMS, usalo.",
    )
    simulator = UserSimulator(
        tools=[as_tool(receive_sms_code)],
        instructions=instructions,
        llm="gemini/gemma-4-26b-a4b-it",
        llm_args={},
    )
    return simulator


def test_user_simulator_fetches_sms_code_without_llm():
    simulator = _make_simulator()
    state = simulator.get_init_state()
    assistant_message = AssistantMessage(
        role="assistant",
        content="Te envié un SMS. Por favor comparte el código SMS para verificar tu identidad.",
    )

    user_message, _ = simulator.generate_next_message(assistant_message, state)

    assert user_message.tool_calls is not None
    assert len(user_message.tool_calls) == 1
    assert user_message.tool_calls[0].name == "receive_sms_code"
    assert user_message.tool_calls[0].arguments == {"user_id": "U001"}
    assert user_message.tool_calls[0].requestor == "user"


def test_user_simulator_replies_with_code_after_tool_message():
    simulator = _make_simulator()
    state = simulator.get_init_state()
    tool_message = ToolMessage(
        id="user_receive_sms_code",
        role="tool",
        requestor="user",
        content='{"user_id":"U001","code":"123456","message":"Codigo recibido"}',
        error=False,
    )

    user_message, _ = simulator.generate_next_message(tool_message, state)

    assert user_message.tool_calls is None
    assert user_message.content == "123456"
