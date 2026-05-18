from persona_engine import PersonaBot

print("\nChatbot ready.")
print("Type 'exit' to stop.\n")

bot = PersonaBot()

while True:
    question = input("You: ")

    if question.lower() == "exit":
        break

    answer = bot.ask(question)

    print("\nBot:", answer)
    print()
