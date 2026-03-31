#!/usr/bin/env python3
"""CLI Agent entry point."""

import sys

from agent import Agent
from config import AgentConfig
from tools.screenshot import capture_screenshot
from ui.display import Display


def build_screenshot_message(prompt: str) -> list:
    """Capture a screenshot and build a multimodal content list."""
    display = Display()
    with display.spinner("Capturing screenshot..."):
        b64 = capture_screenshot()

    if b64.startswith("Error:"):
        raise RuntimeError(b64)

    return [
        {"type": "text", "text": prompt or "Please describe what you see on the screen."},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        },
    ]


def _exit_save(agent: "Agent", display: "Display") -> None:
    """Save session and print goodbye on exit."""
    saved = agent.save_session()
    if saved:
        display.show_info(f"Session saved to {saved}")
    display.show_info("Goodbye!")


def main() -> None:
    config = AgentConfig()
    display = Display()
    agent = Agent(config=config, display=display)

    display.show_welcome()

    # Show memory status at startup
    mem = agent.memory.load_long_term()
    if mem:
        display.show_info(f"Long-term memory loaded ({len(mem)} chars) from {agent.memory.long_term_path}")
    else:
        display.show_info(f"No long-term memory yet. Use 'append_memory' or 'update_memory' tool to save notes.")

    while True:
        try:
            user_input = display.prompt(
                used_tokens=agent.last_prompt_tokens,
                max_tokens=config.max_context_tokens,
            ).strip()
        except (EOFError, KeyboardInterrupt):
            _exit_save(agent, display)
            sys.exit(0)

        if not user_input:
            continue

        # --- Built-in commands ---
        lower = user_input.lower()

        if lower in ("/quit", "/exit", "quit", "exit"):
            _exit_save(agent, display)
            sys.exit(0)

        if lower == "/clear":
            saved = agent.clear_history(save=True)
            display.show_cleared()
            if saved:
                display.show_info(f"Session saved to {saved}")
            continue

        if lower == "/help":
            display.show_help()
            continue

        if lower == "/skills":
            skills = agent.skill_manager.list_skills()
            if not skills:
                display.show_info("No skills found. Ask the agent to create one with create_skill.")
            else:
                display.show_info("Available skills:")
                for s in skills:
                    display.show_info(f"  - {s['name']}: {s['description']}")
            continue

        if lower.startswith("/screenshot"):
            # Extract optional prompt after /screenshot
            prompt = user_input[len("/screenshot"):].strip()
            try:
                content = build_screenshot_message(prompt)
            except RuntimeError as e:
                display.show_error(str(e))
                continue
            # Send multimodal message directly to agent
            try:
                answer = agent.chat(content)
                display.show_answer(answer)
            except Exception as e:
                display.show_error(f"Agent error: {e}")
            continue

        # --- Regular text message ---
        try:
            answer = agent.chat(user_input)
            display.show_answer(answer)
        except KeyboardInterrupt:
            display.show_info("\n[Interrupted]")
        except Exception as e:
            display.show_error(f"Agent error: {e}")


if __name__ == "__main__":
    main()
