def ask(prompt: str, system: str | None = None, max_tokens: int = 1500) -> str:
    return (
        "[Demo mode]\n"
        "I can summarize, plan, and quiz, but the live AI API is temporarily disabled.\n\n"
        f"Your request was:\n{prompt}"
    )


def ask_with_tools(messages: list, tools: list, system: str | None = None, max_tokens: int = 1500):
    last_user = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user = msg.get("content", "")
            break

    class FakeBlock:
        def __init__(self, type_, text=None):
            self.type = type_
            self.text = text

    class FakeResponse:
        def __init__(self, text):
            self.content = [FakeBlock("text", text)]

    text = (
        "[Demo mode]\n"
        "The live AI API is currently disabled.\n\n"
        f"Latest user request:\n{last_user}\n\n"
        "Next step: we can still test the app structure, storage, and UI."
    )
    return FakeResponse(text)