exec_node(
      action = "chat_exact",
      name = "ask_question",
      transitions = ['next', 'ask_user_preference'],
      instruction = "Would you like me to tell you more about the latest advances in AI?",
      transition_question = "Does the user want to talk about ai?",
      transition_choices = ['yes', 'no'],
      )
exec_node(
      action = "chat",
      name = "tell_about_ai",
      transitions = ['before_while'],
       instruction = ("Tell the user about the latest advances in AI. Mention that"
        "a new framework called AutoGRAMS was recently released that allows greater control over AI agents.")
      )

exec_node(
      action = "chat",
      name = "ask_user_preference",
      instruction = "Confirm with the user the user what they would prefer to talk about.",
      )
exec_node(
      action = "transition",
      name = "before_while",
      )

#while loop connects node to itself
while True:
      exec_node(
            action = "chat",
            name = "continue_conversation",
            instruction = "Respond to the user.",
      )