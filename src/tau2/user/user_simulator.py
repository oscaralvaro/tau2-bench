import re
import uuid
from typing import Optional, Tuple

from loguru import logger

from tau2.data_model.message import (
    AssistantMessage,
    Message,
    MultiToolMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from tau2.data_model.tasks import UserInstructions
from tau2.environment.tool import Tool
from tau2.user.base import (
    OUT_OF_SCOPE,
    STOP,
    TRANSFER,
    BaseUser,
    UserState,
    ValidUserInputMessage,
    is_valid_user_history_message,
)
from tau2.utils import DATA_DIR
from tau2.utils.llm_utils import generate

GLOBAL_USER_SIM_GUIDELINES_DIR = DATA_DIR / "tau2" / "user_simulator"


GLOBAL_USER_SIM_GUIDELINES_PATH = (
    GLOBAL_USER_SIM_GUIDELINES_DIR / "simulation_guidelines.md"
)

GLOBAL_USER_SIM_GUIDELINES_PATH_TOOLS = (
    GLOBAL_USER_SIM_GUIDELINES_DIR / "simulation_guidelines_tools.md"
)


def get_global_user_sim_guidelines(use_tools: bool = False) -> str:
    """
    Get the global user simulator guidelines.

    Args:
        use_tools: Whether to use the tools guidelines.

    Returns:
        The global user simulator guidelines.
    """
    if use_tools:
        with open(GLOBAL_USER_SIM_GUIDELINES_PATH_TOOLS, "r", encoding="utf-8") as fp:
            user_sim_guidelines = fp.read()
    else:
        with open(GLOBAL_USER_SIM_GUIDELINES_PATH, "r", encoding="utf-8") as fp:
            user_sim_guidelines = fp.read()
    return user_sim_guidelines


SYSTEM_PROMPT = """
{global_user_sim_guidelines}

<scenario>
{instructions}
</scenario>
""".strip()

SMS_TOOL_NAMES = {"check_verification_sms", "check_phone_messages"}
SMS_REQUEST_PATTERN = re.compile(
    r"(c[oó]digo|sms|verificaci[oó]n|6\s*d[ií]gitos)",
    re.IGNORECASE,
)
SMS_CODE_PATTERN = re.compile(r"\b\d{6}\b")
STUDENT_ID_PATTERN = re.compile(r"\bu\d{7}\b", re.IGNORECASE)


class UserSimulator(BaseUser):
    """Stateless implementation of a user simulator."""

    def __init__(
        self,
        tools: Optional[list[Tool]] = None,
        instructions: Optional[UserInstructions] = None,
        llm: Optional[str] = None,
        llm_args: Optional[dict] = None,
    ):
        super().__init__(instructions=instructions, llm=llm, llm_args=llm_args)
        self.tools = tools

    @property
    def global_simulation_guidelines(self) -> str:
        """
        The simulation guidelines for the user simulator.
        """
        use_tools = self.tools is not None
        return get_global_user_sim_guidelines(use_tools=use_tools)

    @property
    def system_prompt(self) -> str:
        """
        The system prompt for the user simulator.
        """
        if self.instructions is None:
            logger.warning("No instructions provided for user simulator")

        system_prompt = SYSTEM_PROMPT.format(
            global_user_sim_guidelines=self.global_simulation_guidelines,
            instructions=self.instructions,
        )
        return system_prompt

    def get_init_state(
        self, message_history: Optional[list[Message]] = None
    ) -> UserState:
        """
        Get the initial state of the user simulator.
        """
        if message_history is None:
            message_history = []
        assert all(is_valid_user_history_message(m) for m in message_history), (
            "Invalid user message history. User messages must be of type UserMessage, AssistantMessage, or ToolMessage to User."
        )

        user_state = UserState(
            system_messages=[SystemMessage(role="system", content=self.system_prompt)],
            messages=message_history,
        )
        return user_state

    @classmethod
    def is_stop(cls, message: UserMessage) -> bool:
        """
        Check if the message is a stop message.
        """
        if message.is_tool_call():
            return False
        assert message.content is not None
        return (
            STOP in message.content
            or TRANSFER in message.content
            or OUT_OF_SCOPE in message.content
        )

    def generate_next_message(
        self, message: ValidUserInputMessage, state: UserState
    ) -> Tuple[UserMessage, UserState]:
        return self._generate_next_message(message, state)

    def _generate_next_message(
        self, message: ValidUserInputMessage, state: UserState
    ) -> Tuple[UserMessage, UserState]:
        """Get the response from the user simulator.

        Args:
            message: The assistant or tool message.
            state: The user simulator's state.

        Returns:
            A tuple containing the user message and the updated user state.
        """
        # Updating state with new message
        if isinstance(message, MultiToolMessage):
            state.messages.extend(message.tool_messages)
        else:
            state.messages.append(message)

        auto_message = self._maybe_handle_sms_verification(message, state)
        if auto_message is not None:
            state.messages.append(auto_message)
            return auto_message, state

        messages = state.system_messages + state.flip_roles()

        # Generate response
        assistant_message = generate(
            model=self.llm,
            messages=messages,
            tools=self.tools,
            **self.llm_args,
        )

        user_response = assistant_message.content
        logger.debug(f"Response: {user_response}")

        user_message = UserMessage(
            role="user",
            content=user_response,
            cost=assistant_message.cost,
            usage=assistant_message.usage,
            raw_data=assistant_message.raw_data,
        )

        # flip the requestor of the tool calls
        if assistant_message.tool_calls is not None:
            user_message.tool_calls = []
            for tool_call in assistant_message.tool_calls:
                user_message.tool_calls.append(
                    ToolCall(
                        id=tool_call.id,
                        name=tool_call.name,
                        arguments=tool_call.arguments,
                        requestor="user",
                    )
                )

        # Updating state with response
        state.messages.append(user_message)
        return user_message, state

    def _maybe_handle_sms_verification(
        self, message: ValidUserInputMessage, state: UserState
    ) -> Optional[UserMessage]:
        if self.tools is None:
            return None

        if isinstance(message, AssistantMessage):
            return self._maybe_call_sms_tool(message, state)
        if isinstance(message, ToolMessage):
            return self._maybe_answer_from_sms_tool(message, state)
        return None

    def _maybe_call_sms_tool(
        self, message: AssistantMessage, state: UserState
    ) -> Optional[UserMessage]:
        if not self._has_user_tool("check_verification_sms"):
            return None
        if not message.content or not SMS_REQUEST_PATTERN.search(message.content):
            return None

        student_id = self._extract_student_id(state)
        if student_id is None:
            return None

        return UserMessage(
            role="user",
            tool_calls=[
                ToolCall(
                    id=f"call_{uuid.uuid4().hex[:8]}",
                    name="check_verification_sms",
                    arguments={"student_id": student_id},
                    requestor="user",
                )
            ],
        )

    def _maybe_answer_from_sms_tool(
        self, message: ToolMessage, state: UserState
    ) -> Optional[UserMessage]:
        if message.requestor != "user" or message.content is None:
            return None
        if not self._is_response_to_sms_tool(message, state):
            return None

        code_match = SMS_CODE_PATTERN.search(message.content)
        if code_match is None:
            return UserMessage(
                role="user",
                content="No tengo ningún código de verificación nuevo.",
            )

        return UserMessage(
            role="user",
            content=f"El código de verificación que recibí es {code_match.group(0)}.",
        )

    def _has_user_tool(self, tool_name: str) -> bool:
        return any(tool.name == tool_name for tool in self.tools or [])

    def _extract_student_id(self, state: UserState) -> Optional[str]:
        candidate_texts = [str(self.instructions or "")]
        candidate_texts.extend(
            message.content
            for message in reversed(state.messages)
            if getattr(message, "content", None)
        )
        for text in candidate_texts:
            match = STUDENT_ID_PATTERN.search(text)
            if match:
                return match.group(0).lower()
        return None

    def _is_response_to_sms_tool(self, message: ToolMessage, state: UserState) -> bool:
        for previous_message in reversed(state.messages[:-1]):
            if not isinstance(previous_message, UserMessage):
                continue
            if previous_message.tool_calls is None:
                continue
            return any(
                tool_call.id == message.id and tool_call.name in SMS_TOOL_NAMES
                for tool_call in previous_message.tool_calls
            )
        return False


class DummyUser(UserSimulator):
    """A dummy user to run a agent solo simulation."""

    def get_init_state(
        self, message_history: Optional[list[Message]] = None
    ) -> UserState:
        return UserState(messages=[], system_messages=[])

    def is_stop(cls, message: UserMessage) -> bool:
        raise NotImplementedError("DummyUser does not support stop messages")

    def set_seed(self, seed: int):
        pass

    def generate_next_message(
        self, message: ValidUserInputMessage, state: UserState
    ) -> tuple[UserMessage, UserState]:
        raise NotImplementedError("DummyUser does not support generate_next_message")
