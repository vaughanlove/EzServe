



def get_input() -> str:
    print("Insert your text. Enter 'q' or press Ctrl-D (or Ctrl-Z on Windows) to end.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "q":
            break
        contents.append(line)
    return "\n".join(contents)


# Below are all the tools.
HumanInputTool = Tool(
    name = "human_input_tool",
    description = "This tool is for querying human input when there are active failed orders.",
    return_direct=True, 
    func=get_input,
)

