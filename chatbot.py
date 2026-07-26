import json
import string


# Load all chatbot topics, example phrases, follow-up phrases, and replies
# from intents.json so the answers can be edited without changing app.py.
with open("intents.json", "r") as file:
    intents = json.load(file)


def clean_text(text):
    # Convert the user's message to lowercase and remove extra spaces.
    # This makes "  Refund   " and "refund" behave the same way.
    return " ".join(text.lower().split())


def words_in(text):
    # Remove punctuation before checking short words.
    # Example: "hi?" becomes "hi", so greetings still work with punctuation.
    clean_words = text.translate(str.maketrans("", "", string.punctuation))
    return clean_words.split()


def has_any(text, phrases):
    # Check whether the user's message contains any phrase from a list.
    # This helper is reused for topics like refund, shipping, hours, and contact.
    text_words = words_in(text)

    for phrase in phrases:
        # Very short words must match as whole words.
        # This prevents "hi" from matching inside "shipping".
        if len(phrase) <= 3 and phrase.isalpha():
            if phrase in text_words:
                return True
            continue

        # Longer phrases are checked directly inside the message.
        # Example: "how long" can match "how long is shipping?"
        if phrase in text:
            return True

    # If none of the phrases matched, return False.
    return False


def detect_explicit_intent(text):
    # These keywords identify the main topic the user is asking about.
    # If a user says "how long is shipping?" while refund was the previous
    # topic, this step correctly switches the active topic to shipping.
    topic_keywords = {
        "refund": ["refund", "refunded", "return", "money back"],
        "shipping": ["shipping", "delivery", "deliver", "order arrive"],
        "hours": ["hours", "open", "opening", "close", "closing"],
        "contact": ["contact", "support", "email", "phone", "call", "number"],
        "greeting": ["hi", "hello", "hey"],
        "goodbye": ["bye", "goodbye"],
    }

    for intent, keywords in topic_keywords.items():
        # Return the first topic whose keywords appear in the user's message.
        if has_any(text, keywords):
            return intent

    # No clear topic was named in the message.
    return None


def detect_follow_up(intent, text):
    # Match a user's message against follow-up questions for a known topic.
    # For example, after "refund", a short message like "how" should mean
    # "how do I request a refund?"
    if intent == "refund":
        # Refund timing questions.
        if has_any(text, [
            "how many day",
            "how long",
            "when",
            "timeline",
            "processing time",
            "refund time",
            "receive it",
            "get it",
        ]):
            return intents["refund"]["follow_up"]["time"]["response"]

        # Refund process questions.
        if has_any(text, ["how", "process", "step", "procedure"]):
            return intents["refund"]["follow_up"]["process"]["response"]

        # Refund eligibility questions.
        if has_any(text, ["eligible", "damaged", "return this"]):
            return intents["refund"]["follow_up"]["eligibility"]["response"]

    if intent == "shipping":
        # Shipping tracking questions.
        if has_any(text, ["track", "tracking", "where is my order"]):
            return intents["shipping"]["follow_up"]["tracking"]["response"]

        # Shipping process questions.
        if has_any(text, [
            "process",
            "shipping process",
            "delivery process",
            "how does shipping work",
            "how do you ship",
            "procedure",
            "steps",
        ]):
            return intents["shipping"]["follow_up"]["process"]["response"]

        # Shipping delivery-time questions.
        if has_any(text, [
            "how long",
            "when",
            "arrive",
            "delivery time",
            "shipping time",
            "how many day",
            "days",
        ]):
            return intents["shipping"]["follow_up"]["time"]["response"]

    if intent == "hours":
        # Full business-hours questions.
        if has_any(text, [
            "what are the hours",
            "business hours",
            "working hours",
            "timings",
            "store timings",
            "what time are you open",
        ]):
            return intents["hours"]["follow_up"]["full"]["response"]

        # Closing-time questions.
        if has_any(text, ["close", "closing"]):
            return intents["hours"]["follow_up"]["closing"]["response"]

        # Opening-time questions.
        if has_any(text, ["when", "opening", "open"]):
            return intents["hours"]["follow_up"]["opening"]["response"]

    if intent == "contact":
        # General contact questions where the user wants all contact options.
        if has_any(text, [
            "how to connect you",
            "how can i contact you",
            "contact information",
            "contact details",
            "customer service contact",
        ]):
            return intents["contact"]["follow_up"]["general"]["response"]

        # Email-only contact questions.
        if has_any(text, ["email", "mail"]):
            return intents["contact"]["follow_up"]["email"]["response"]

        # Phone-only contact questions.
        if has_any(text, ["phone", "call", "number"]):
            return intents["contact"]["follow_up"]["phone"]["response"]

    # The message did not match any follow-up for this topic.
    return None


def detect_parent_intent(text):
    # Check the main topic patterns from intents.json.
    # This handles simple topic messages like "refund" or "shipping".
    for intent, data in intents.items():
        if has_any(text, data["patterns"]):
            return intent

    # No parent topic matched.
    return None


def chatbot_response(user_question, last_intent=None):
    # This is the main function used by app.py.
    # It returns two things:
    # 1. the bot's answer
    # 2. the current topic, so the next message can be understood as a follow-up
    user_question = clean_text(user_question)

    # If the user sends an empty message, keep the previous topic but ask again.
    if not user_question:
        return "Sorry, I don't understand that.", last_intent

    # First, check if the user clearly named a new topic.
    # This prevents old context from causing wrong answers.
    # Example: after "refund", "how long is shipping?" should answer shipping.
    explicit_intent = detect_explicit_intent(user_question)

    if explicit_intent:
        # If the message names a topic and also asks a specific follow-up,
        # answer the specific follow-up directly.
        follow_up_response = detect_follow_up(explicit_intent, user_question)

        if follow_up_response:
            return follow_up_response, explicit_intent

        # If the user only named the topic, return that topic's main response.
        return intents[explicit_intent]["response"], explicit_intent

    # If no new topic was named, use the previous topic as context.
    # Example: "refund" followed by "how" should answer the refund process.
    if last_intent:
        follow_up_response = detect_follow_up(last_intent, user_question)

        if follow_up_response:
            return follow_up_response, last_intent

    # If there is no useful previous context, try matching a main topic.
    parent_intent = detect_parent_intent(user_question)

    if parent_intent:
        return intents[parent_intent]["response"], parent_intent

    # Final fallback when the bot cannot understand the message.
    # Keep last_intent so the conversation context is not lost immediately.
    return "Sorry, I don't understand that.", last_intent
