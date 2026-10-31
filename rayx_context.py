
from collections import deque
from datetime import datetime


class RayXContext:
    def __init__(self, max_messages=12):
        self.messages = deque(maxlen=max_messages)
        self.current_topic = None
        self.last_intent = None

    def add_message(self, role, content):
        if role not in {"user", "assistant"}:
            raise ValueError("Role must be user or assistant.")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("Message cannot be empty.")

        self.messages.append({
            "role": role,
            "content": content.strip(),
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            )
        })

    def set_topic(self, topic):
        if topic and topic.strip():
            self.current_topic = topic.strip()

    def set_intent(self, intent):
        self.last_intent = intent

    def get_last_user_message(self):
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message["content"]

        return None

    def get_last_assistant_message(self):
        for message in reversed(self.messages):
            if message["role"] == "assistant":
                return message["content"]

        return None

    def is_follow_up(self, text):
        follow_up_phrases = [
            "give me an example",
            "explain more",
            "explain this",
            "tell me more",
            "why",
            "how",
            "show example",
            "aur batao",
            "example do",
            "isko samjhao",
            "iska example",
            "aur explain karo"
        ]

        normalized = text.casefold().strip()

        return any(
            phrase in normalized
            for phrase in follow_up_phrases
        )

    def get_context(self):
        return {
            "current_topic": self.current_topic,
            "last_intent": self.last_intent,
            "last_user_message": self.get_last_user_message(),
            "last_assistant_message": self.get_last_assistant_message(),
            "messages": list(self.messages)
        }

    def clear(self):
        self.messages.clear()
        self.current_topic = None
        self.last_intent = None


if __name__ == "__main__":
    context = RayXContext()

    context.add_message(
        "user",
        "What is Python?"
    )

    context.set_topic("Python")

    context.add_message(
        "assistant",
        "Python is a programming language."
    )

    question = "Give me an example."

    print("Follow-up:", context.is_follow_up(question))
    print("Context:", context.get_context())
