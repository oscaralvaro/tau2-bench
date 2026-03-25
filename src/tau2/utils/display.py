import json
from typing import Any, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tau2.data_model.message import (
    AssistantMessage,
    Message,
    SystemMessage,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from tau2.data_model.simulation import RunConfig, SimulationRun
from tau2.data_model.tasks import Action, Task
from tau2.evaluator.evaluator_communicate import CommunicateEvaluator
from tau2.registry import registry
from tau2.metrics.agent_metrics import AgentMetrics, is_successful


def _extract_tool_calls(messages: list[Message]) -> list[dict[str, Any]]:
    tool_calls = []
    for message in messages:
        if isinstance(message, AssistantMessage) or isinstance(message, UserMessage):
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append(
                        {
                            "requestor": message.role,
                            "name": tool_call.name,
                            "arguments": tool_call.arguments,
                        }
                    )
    return tool_calls


def _format_tool_call(call: dict[str, Any]) -> str:
    return f"{call['requestor']}::{call['name']}({json.dumps(call['arguments'], indent=2)})"


def _diff_values(
    expected: Any, actual: Any, path: str, diffs: list[str], max_items: int
) -> None:
    if len(diffs) >= max_items:
        return
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())
        for key in sorted(expected_keys | actual_keys):
            new_path = f"{path}.{key}" if path else str(key)
            if key not in expected:
                diffs.append(f"{new_path}: expected=<missing>, actual={actual[key]}")
            elif key not in actual:
                diffs.append(f"{new_path}: expected={expected[key]}, actual=<missing>")
            else:
                _diff_values(expected[key], actual[key], new_path, diffs, max_items)
        return
    if isinstance(expected, list) and isinstance(actual, list):
        min_len = min(len(expected), len(actual))
        for i in range(min_len):
            new_path = f"{path}[{i}]"
            _diff_values(expected[i], actual[i], new_path, diffs, max_items)
            if len(diffs) >= max_items:
                return
        if len(expected) != len(actual):
            diffs.append(
                f"{path}: expected_length={len(expected)}, actual_length={len(actual)}"
            )
        return
    if expected != actual:
        diffs.append(f"{path}: expected={expected}, actual={actual}")


def _get_db_dump(env, requestor: str) -> Optional[dict]:
    tools = env.tools if requestor == "assistant" else env.user_tools
    if tools is None or getattr(tools, "db", None) is None:
        return None
    return tools.db.model_dump()


def _compute_db_diff(
    domain: str,
    task: Task,
    simulation: SimulationRun,
    solo_mode: bool = False,
    max_items: int = 50,
) -> dict[str, list[str]]:
    env_constructor = registry.get_env_constructor(domain)
    try:
        predicted_env = (
            env_constructor(solo_mode=solo_mode) if solo_mode else env_constructor()
        )
        gold_env = env_constructor()
    except Exception:
        return {}

    initial_state = task.initial_state
    initialization_data = (
        initial_state.initialization_data if initial_state is not None else None
    )
    initialization_actions = (
        initial_state.initialization_actions if initial_state is not None else None
    )
    message_history = (
        initial_state.message_history
        if initial_state is not None and initial_state.message_history is not None
        else []
    )

    try:
        predicted_env.set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=simulation.messages,
        )
        gold_env.set_state(
            initialization_data=initialization_data,
            initialization_actions=initialization_actions,
            message_history=message_history,
        )
        golden_actions = task.evaluation_criteria.actions or []
        for action in golden_actions:
            try:
                gold_env.make_tool_call(
                    tool_name=action.name,
                    requestor=action.requestor,
                    **action.arguments,
                )
            except Exception:
                continue
    except Exception:
        return {}

    diffs: dict[str, list[str]] = {}
    for requestor in ["assistant", "user"]:
        expected = _get_db_dump(gold_env, requestor=requestor)
        actual = _get_db_dump(predicted_env, requestor=requestor)
        if expected is None or actual is None:
            continue
        diff_items: list[str] = []
        _diff_values(expected, actual, path="", diffs=diff_items, max_items=max_items)
        if diff_items:
            diffs[requestor] = diff_items
    return diffs


class ConsoleDisplay:
    console = Console()

    @classmethod
    def display_run_config(cls, config: RunConfig):
        # Create layout
        layout = Layout()

        # Split layout into sections
        layout.split(Layout(name="header"), Layout(name="body"))

        # Split body into columns
        layout["body"].split_row(
            Layout(name="agent", ratio=1),
            Layout(name="user", ratio=1),
            Layout(name="settings", ratio=1),
        )

        # Create content for each section
        header_content = Panel(
            f"[white]Domain:[/] {config.domain}\n"
            f"[white]Task Set:[/] {config.task_set_name if config.task_set_name else 'Default'}\n"
            f"[white]Task IDs:[/] {', '.join(map(str, config.task_ids)) if config.task_ids else 'All'}\n"
            f"[white]Number of trials:[/] {config.num_trials}\n"
            f"[white]Max steps:[/] {config.max_steps}\n"
            f"[white]Max errors:[/] {config.max_errors}",
            title="[bold blue]Simulation Configuration",
            border_style="blue",
        )

        agent_content = Panel(
            f"[white]Implementation:[/] {config.agent}\n"
            f"[white]Model:[/] {config.llm_agent}\n"
            "[white]LLM Arguments:[/]\n"
            f"{json.dumps(config.llm_args_agent, indent=2)}",
            title="[bold cyan]Agent Configuration",
            border_style="cyan",
        )

        user_content = Panel(
            f"[white]Implementation:[/] {config.user}\n"
            f"[white]Model:[/] {config.llm_user}\n"
            "[white]LLM Arguments:[/]\n"
            f"{json.dumps(config.llm_args_user, indent=2)}",
            title="[bold cyan]User Configuration",
            border_style="cyan",
        )

        settings_content = Panel(
            f"[white]Save To:[/] {config.save_to or 'Not specified'}\n"
            f"[white]Max Concurrency:[/] {config.max_concurrency}",
            title="[bold cyan]Additional Settings",
            border_style="cyan",
        )

        # Assign content to layout sections
        layout["header"].update(header_content)
        layout["agent"].update(agent_content)
        layout["user"].update(user_content)
        layout["body"]["settings"].update(settings_content)

        # Print the layout
        cls.console.print(layout)

    @classmethod
    def display_task(cls, task: Task):
        # Build content string showing only non-None fields
        content_parts = []

        if task.id is not None:
            content_parts.append(f"[white]ID:[/] {task.id}")

        if task.description:
            if task.description.purpose:
                content_parts.append(f"[white]Purpose:[/] {task.description.purpose}")
            if task.description.relevant_policies:
                content_parts.append(
                    f"[white]Relevant Policies:[/] {task.description.relevant_policies}"
                )
            if task.description.notes:
                content_parts.append(f"[white]Notes:[/] {task.description.notes}")

        # User Scenario section
        scenario_parts = []
        # Persona
        if task.user_scenario.persona:
            scenario_parts.append(f"[white]Persona:[/] {task.user_scenario.persona}")

        # User Instruction
        scenario_parts.append(
            f"[white]Task Instructions:[/] {task.user_scenario.instructions}"
        )

        if scenario_parts:
            content_parts.append(
                "[bold cyan]User Scenario:[/]\n" + "\n".join(scenario_parts)
            )

        # Initial State section
        if task.initial_state:
            initial_state_parts = []
            if task.initial_state.initialization_data:
                initial_state_parts.append(
                    f"[white]Initialization Data:[/]\n{task.initial_state.initialization_data.model_dump_json(indent=2)}"
                )
            if task.initial_state.initialization_actions:
                initial_state_parts.append(
                    f"[white]Initialization Actions:[/]\n{json.dumps([a.model_dump() for a in task.initial_state.initialization_actions], indent=2)}"
                )
            if task.initial_state.message_history:
                initial_state_parts.append(
                    f"[white]Message History:[/]\n{json.dumps([m.model_dump() for m in task.initial_state.message_history], indent=2)}"
                )

            if initial_state_parts:
                content_parts.append(
                    "[bold cyan]Initial State:[/]\n" + "\n".join(initial_state_parts)
                )

        # Evaluation Criteria section
        if task.evaluation_criteria:
            eval_parts = []
            if task.evaluation_criteria.actions:
                eval_parts.append(
                    f"[white]Required Actions:[/]\n{json.dumps([a.model_dump() for a in task.evaluation_criteria.actions], indent=2)}"
                )
            if task.evaluation_criteria.env_assertions:
                eval_parts.append(
                    f"[white]Env Assertions:[/]\n{json.dumps([a.model_dump() for a in task.evaluation_criteria.env_assertions], indent=2)}"
                )
            if task.evaluation_criteria.communicate_info:
                eval_parts.append(
                    f"[white]Information to Communicate:[/]\n{json.dumps(task.evaluation_criteria.communicate_info, indent=2)}"
                )
            if task.evaluation_criteria.nl_assertions:
                eval_parts.append(
                    f"[white]NL Assertions:[/]\n{json.dumps(task.evaluation_criteria.nl_assertions, indent=2)}"
                )
            if eval_parts:
                content_parts.append(
                    "[bold cyan]Evaluation Criteria:[/]\n" + "\n".join(eval_parts)
                )
        content = "\n\n".join(content_parts)

        # Create and display panel
        task_panel = Panel(
            content, title="[bold blue]Task Details", border_style="blue", expand=True
        )

        cls.console.print(task_panel)

    @classmethod
    def display_simulation(
        cls,
        simulation: SimulationRun,
        show_details: bool = True,
        task: Optional[Task] = None,
        domain: Optional[str] = None,
        solo_mode: bool = False,
    ):
        """
        Display the simulation content in a formatted way using Rich library.

        Args:
            simulation: The simulation object to display
            show_details: Whether to show detailed information
        """
        # Create main simulation info panel
        sim_info = Text()
        if show_details:
            sim_info.append("Simulation ID: ", style="bold cyan")
            sim_info.append(f"{simulation.id}\n")
        sim_info.append("Task ID: ", style="bold cyan")
        sim_info.append(f"{simulation.task_id}\n")
        sim_info.append("Trial: ", style="bold cyan")
        sim_info.append(f"{simulation.trial}\n")
        if show_details:
            sim_info.append("Start Time: ", style="bold cyan")
            sim_info.append(f"{simulation.start_time}\n")
            sim_info.append("End Time: ", style="bold cyan")
            sim_info.append(f"{simulation.end_time}\n")
        sim_info.append("Duration: ", style="bold cyan")
        sim_info.append(f"{simulation.duration:.2f}s\n")
        sim_info.append("Termination Reason: ", style="bold cyan")
        sim_info.append(f"{simulation.termination_reason}\n")
        if simulation.agent_cost is not None:
            sim_info.append("Agent Cost: ", style="bold cyan")
            sim_info.append(f"${simulation.agent_cost:.4f}\n")
        if simulation.user_cost is not None:
            sim_info.append("User Cost: ", style="bold cyan")
            sim_info.append(f"${simulation.user_cost:.4f}\n")
        if simulation.reward_info:
            marker = "✅" if is_successful(simulation.reward_info.reward) else "❌"
            sim_info.append("Reward: ", style="bold cyan")
            if simulation.reward_info.reward_breakdown:
                breakdown = sorted(
                    [
                        f"{k.value}: {v:.1f}"
                        for k, v in simulation.reward_info.reward_breakdown.items()
                    ]
                )
            else:
                breakdown = []

            sim_info.append(
                f"{marker} {simulation.reward_info.reward:.4f} ({', '.join(breakdown)})\n"
            )

            # Add DB check info if present
            if simulation.reward_info.db_check:
                sim_info.append("\nDB Check:", style="bold magenta")
                sim_info.append(
                    f"{'✅' if simulation.reward_info.db_check.db_match else '❌'} {simulation.reward_info.db_check.db_reward}\n"
                )

            # Add env assertions if present
            if simulation.reward_info.env_assertions:
                sim_info.append("\nEnv Assertions:\n", style="bold magenta")
                for i, assertion in enumerate(simulation.reward_info.env_assertions):
                    sim_info.append(
                        f"- {i}: {assertion.env_assertion.env_type} {assertion.env_assertion.func_name} {'✅' if assertion.met else '❌'} {assertion.reward}\n"
                    )

            # Add action checks if present
            if simulation.reward_info.action_checks:
                sim_info.append("\nAction Checks:\n", style="bold magenta")
                for i, check in enumerate(simulation.reward_info.action_checks):
                    sim_info.append(
                        f"- {i}: {check.action.name} {'✅' if check.action_match else '❌'} {check.action_reward}\n"
                    )

            # Add communication checks if present
            if simulation.reward_info.communicate_checks:
                sim_info.append("\nCommunicate Checks:\n", style="bold magenta")
                for i, check in enumerate(simulation.reward_info.communicate_checks):
                    sim_info.append(
                        f"- {i}: {check.info} {'✅' if check.met else '❌'}\n"
                    )

            # Add NL assertions if present
            if simulation.reward_info.nl_assertions:
                sim_info.append("\nNL Assertions:\n", style="bold magenta")
                for i, assertion in enumerate(simulation.reward_info.nl_assertions):
                    sim_info.append(
                        f"- {i}: {assertion.nl_assertion} {'✅' if assertion.met else '❌'}\n\t{assertion.justification}\n"
                    )

            # Add additional info if present
            if simulation.reward_info.info:
                sim_info.append("\nAdditional Info:\n", style="bold magenta")
                for key, value in simulation.reward_info.info.items():
                    sim_info.append(f"{key}: {value}\n")

        if task is not None and task.evaluation_criteria is not None:
            tool_calls = _extract_tool_calls(simulation.messages)
            sim_info.append("\nExpected vs Observed:\n", style="bold magenta")

            # Expected actions vs observed tool calls
            expected_actions = task.evaluation_criteria.actions or []
            if expected_actions:
                sim_info.append("Actions (expected):\n", style="bold magenta")
                for i, action in enumerate(expected_actions):
                    matched_call = None
                    for call in tool_calls:
                        if call["requestor"] != action.requestor:
                            continue
                        if action.compare_with_tool_call(
                            ToolCall(
                                id="",
                                name=call["name"],
                                arguments=call["arguments"],
                                requestor=action.requestor,
                            )
                        ):
                            matched_call = call
                            break
                    status = "✅" if matched_call else "❌"
                    expected_str = action.get_func_format()
                    sim_info.append(
                        f"- {i}: {action.requestor}::{expected_str} {status}\n"
                    )
                    sim_info.append("  expected args:\n")
                    sim_info.append(f"  {json.dumps(action.arguments, indent=2)}\n")
                    if matched_call is None:
                        sim_info.append("  matched args:\n")
                        sim_info.append("  <missing>\n")
                    else:
                        sim_info.append("  matched args:\n")
                        sim_info.append(
                            f"  {json.dumps(matched_call['arguments'], indent=2)}\n"
                        )
                sim_info.append("Observed tool calls:\n", style="bold magenta")
                for i, call in enumerate(tool_calls):
                    sim_info.append(f"- {i}: {_format_tool_call(call)}\n")

            # Expected communication vs observed messages
            expected_comm = task.evaluation_criteria.communicate_info or []
            if expected_comm:
                sim_info.append("\nCommunication (expected):\n", style="bold magenta")
                comm_checks = CommunicateEvaluator.evaluate_communicate_info(
                    simulation.messages, expected_comm
                )
                for i, check in enumerate(comm_checks):
                    status = "✅" if check.met else "❌"
                    sim_info.append(f"- {i}: {check.info} {status}\n")
                    sim_info.append(f"  {check.justification}\n")

            # DB diff if mismatch
            if (
                simulation.reward_info
                and simulation.reward_info.db_check
                and not simulation.reward_info.db_check.db_match
                and domain is not None
            ):
                db_diffs = _compute_db_diff(
                    domain=domain,
                    task=task,
                    simulation=simulation,
                    solo_mode=solo_mode,
                )
                if db_diffs:
                    sim_info.append("\nDB Diff (expected vs actual):\n", style="bold red")
                    for requestor, diffs in db_diffs.items():
                        sim_info.append(f"{requestor} DB differences:\n")
                        for diff in diffs:
                            sim_info.append(f"- {diff}\n")

        cls.console.print(
            Panel(sim_info, title="Simulation Overview", border_style="blue")
        )

        # Create messages table
        if simulation.messages:
            table = Table(
                title="Messages",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,  # Add horizontal lines between rows
            )
            table.add_column("Role", style="cyan", no_wrap=True)
            table.add_column("Content", style="green")
            table.add_column("Details", style="yellow")
            table.add_column("Turn", style="yellow", no_wrap=True)

            current_turn = None
            for msg in simulation.messages:
                content = msg.content if msg.content is not None else ""
                details = ""

                # Set different colors based on message type
                if isinstance(msg, AssistantMessage):
                    role_style = "bold blue"
                    content_style = "blue"
                    tool_style = "bright_blue"  # Lighter shade of blue
                elif isinstance(msg, UserMessage):
                    role_style = "bold green"
                    content_style = "green"
                    tool_style = "bright_green"  # Lighter shade of green
                elif isinstance(msg, ToolMessage):
                    # For tool messages, use the color of the requestor's tool style
                    if msg.requestor == "user":
                        role_style = "bold green"
                        content_style = "bright_green"  # Match user's tool style
                    else:  # assistant
                        role_style = "bold blue"
                        content_style = "bright_blue"  # Match assistant's tool style
                else:  # SystemMessage
                    role_style = "bold magenta"
                    content_style = "magenta"

                if isinstance(msg, AssistantMessage) or isinstance(msg, UserMessage):
                    if msg.tool_calls:
                        tool_calls = []
                        for tool in msg.tool_calls:
                            tool_calls.append(
                                f"[{tool_style}]Tool: {tool.name}[/]\n[{tool_style}]Args: {json.dumps(tool.arguments, indent=2)}[/]"
                            )
                        details = "\n".join(tool_calls)
                elif isinstance(msg, ToolMessage):
                    details = f"[{content_style}]Tool ID: {msg.id}. Requestor: {msg.requestor}[/]"
                    if msg.error:
                        details += " [bold red](Error)[/]"

                # Add empty row between turns
                if current_turn is not None and msg.turn_idx != current_turn:
                    table.add_row("", "", "", "")
                current_turn = msg.turn_idx

                table.add_row(
                    f"[{role_style}]{msg.role}[/]",
                    f"[{content_style}]{content}[/]",
                    details,
                    str(msg.turn_idx) if msg.turn_idx is not None else "",
                )
            if show_details:
                cls.console.print(table)

    @classmethod
    def display_agent_metrics(cls, metrics: AgentMetrics):
        # Create content for metrics panel
        content = Text()

        # Add average reward section
        content.append("🏆 Average Reward: ", style="bold cyan")
        content.append(f"{metrics.avg_reward:.4f}\n\n")

        # Add average reward breakdown section
        if metrics.avg_reward_breakdown:
            content.append("🧩 Average Reward Breakdown:\n", style="bold cyan")
            for key in sorted(metrics.avg_reward_breakdown.keys()):
                content.append(f"- {key}: ", style="bold white")
                content.append(f"{metrics.avg_reward_breakdown[key]:.3f}\n")
            content.append("\n")

        # Add Pass^k metrics section
        content.append("📈 Pass^k Metrics:", style="bold cyan")
        for k, pass_hat_k in metrics.pass_hat_ks.items():
            content.append(f"\nk={k}: ", style="bold white")
            content.append(f"{pass_hat_k:.3f}")

        # Add average agent cost section
        content.append("\n\n💰 Average Cost per Conversation: ", style="bold cyan")
        content.append(f"${metrics.avg_agent_cost:.4f}\n\n")

        # Create and display panel
        metrics_panel = Panel(
            content,
            title="[bold blue]Agent Metrics",
            border_style="blue",
            expand=True,
        )

        cls.console.print(metrics_panel)


class MarkdownDisplay:
    @classmethod
    def display_actions(cls, actions: List[Action]) -> str:
        """Display actions in markdown format."""
        return f"```json\n{json.dumps([action.model_dump() for action in actions], indent=2)}\n```"

    @classmethod
    def display_messages(cls, messages: list[Message]) -> str:
        """Display messages in markdown format."""
        return "\n\n".join(cls.display_message(msg) for msg in messages)

    @classmethod
    def display_simulation(cls, sim: SimulationRun) -> str:
        """Display simulation in markdown format."""
        # Otherwise handle SimulationRun object
        output = []

        # Add basic simulation info
        output.append(f"**Task ID**: {sim.task_id}")
        output.append(f"**Trial**: {sim.trial}")
        output.append(f"**Duration**: {sim.duration:.2f}s")
        output.append(f"**Termination**: {sim.termination_reason}")
        if sim.agent_cost is not None:
            output.append(f"**Agent Cost**: ${sim.agent_cost:.4f}")
        if sim.user_cost is not None:
            output.append(f"**User Cost**: ${sim.user_cost:.4f}")

        # Add reward info if present
        if sim.reward_info:
            breakdown = sorted(
                [
                    f"{k.value}: {v:.1f}"
                    for k, v in sim.reward_info.reward_breakdown.items()
                ]
            )
            output.append(
                f"**Reward**: {sim.reward_info.reward:.4f} ({', '.join(breakdown)})\n"
            )
            output.append(f"**Reward**: {sim.reward_info.reward:.4f}")

            # Add DB check info if present
            if sim.reward_info.db_check:
                output.append("\n**DB Check**")
                output.append(
                    f"- Status: {'✅' if sim.reward_info.db_check.db_match else '❌'} {sim.reward_info.db_check.db_reward}"
                )

            # Add env assertions if present
            if sim.reward_info.env_assertions:
                output.append("\n**Env Assertions**")
                for i, assertion in enumerate(sim.reward_info.env_assertions):
                    output.append(
                        f"- {i}: {assertion.env_assertion.env_type} {assertion.env_assertion.func_name} {'✅' if assertion.met else '❌'} {assertion.reward}"
                    )

            # Add action checks if present
            if sim.reward_info.action_checks:
                output.append("\n**Action Checks**")
                for i, check in enumerate(sim.reward_info.action_checks):
                    output.append(
                        f"- {i}: {check.action.name} {'✅' if check.action_match else '❌'} {check.action_reward}"
                    )

            # Add communication checks if present
            if sim.reward_info.communicate_checks:
                output.append("\n**Communicate Checks**")
                for i, check in enumerate(sim.reward_info.communicate_checks):
                    output.append(
                        f"- {i}: {check.info} {'✅' if check.met else '❌'} {check.justification}"
                    )

            # Add NL assertions if present
            if sim.reward_info.nl_assertions:
                output.append("\n**NL Assertions**")
                for i, assertion in enumerate(sim.reward_info.nl_assertions):
                    output.append(
                        f"- {i}: {assertion.nl_assertion} {'✅' if assertion.met else '❌'} {assertion.justification}"
                    )

            # Add additional info if present
            if sim.reward_info.info:
                output.append("\n**Additional Info**")
                for key, value in sim.reward_info.info.items():
                    output.append(f"- {key}: {value}")

        # Add messages using the display_message method
        if sim.messages:
            output.append("\n**Messages**:")
            output.extend(cls.display_message(msg) for msg in sim.messages)

        return "\n\n".join(output)

    @classmethod
    def display_result(
        cls,
        task: Task,
        sim: SimulationRun,
        reward: Optional[float] = None,
        show_task_id: bool = False,
    ) -> str:
        """Display a single result with all its components in markdown format."""
        output = [
            f"## Task {task.id}" if show_task_id else "## Task",
            "\n### User Instruction",
            task.user_scenario.instructions,
            "\n### Ground Truth Actions",
            cls.display_actions(task.evaluation_criteria.actions),
        ]

        if task.evaluation_criteria.communicate_info:
            output.extend(
                [
                    "\n### Communicate Info",
                    "```\n" + str(task.evaluation_criteria.communicate_info) + "\n```",
                ]
            )

        if reward is not None:
            output.extend(["\n### Reward", f"**{reward:.3f}**"])

        output.extend(["\n### Simulation", cls.display_simulation(sim)])

        return "\n".join(output)

    @classmethod
    def display_message(cls, msg: Message) -> str:
        """Display a single message in markdown format."""
        # Common message components
        parts = []

        # Add turn index if present
        turn_prefix = f"[TURN {msg.turn_idx}] " if msg.turn_idx is not None else ""

        # Format based on message type
        if isinstance(msg, AssistantMessage) or isinstance(msg, UserMessage):
            parts.append(f"{turn_prefix}**{msg.role}**:")
            if msg.content:
                parts.append(msg.content)
            if msg.tool_calls:
                tool_calls = []
                for tool in msg.tool_calls:
                    tool_calls.append(
                        f"**Tool Call**: {tool.name}\n```json\n{json.dumps(tool.arguments, indent=2)}\n```"
                    )
                parts.extend(tool_calls)

        elif isinstance(msg, ToolMessage):
            status = " (Error)" if msg.error else ""
            parts.append(f"{turn_prefix}**tool{status}**:")
            parts.append(f"Reponse to: {msg.requestor}")
            if msg.content:
                parts.append(f"```\n{msg.content}\n```")

        elif isinstance(msg, SystemMessage):
            parts.append(f"{turn_prefix}**system**:")
            if msg.content:
                parts.append(msg.content)

        return "\n".join(parts)
