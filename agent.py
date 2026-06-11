import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import subprocess
import glob

load_dotenv()
client = genai.Client()

def find_skill(prompt: str):
    splits = prompt.split("/")
    skills = [f.name.split('.')[0] for f in os.scandir("./skills") if f.name.endswith('txt')]
    if len(splits) > 1:
        skillsPre = splits[0]
        skillPotentional = splits[1]
        skill = skillPotentional.split(' ')[0]
        if skill in skills:
            return skill

    return None

def read_file(path: str) -> str:
    """Read the contents of a file given its relative or absolute path.
    
    Args:
        path: The path to the file that needs to be read.
    Returns:
        The text content of the file, or an error message if the file is not found.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: The file at '{path}' was not found."
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(path: str, content: str) -> str:
    """Create or modify a file with the provided content.
    
    Args:
        path: The path to the file to create or edit.
        content: The text content to write into the file.
    Returns:
        A success message or an error string.
    """
    # Safety Check
    confirm = input(f"\n[PERMISSION REQUIRED] Agent wants to write to '{path}'. Allow? (y/n): ")
    if confirm.lower() != 'y':
        return "Action denied by user."

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def execute_shell(command: str) -> str:
    """Run a shell command and return its standard output and standard error.
    
    Args:
        command: The shell command string to execute.
    Returns:
        The stdout and stderr output of the command, or an error message.
    """
    # Safety Check

    dangerous_keywords = ["sudo", "su", "shred", "dd", "mkfs", "reboot", "shutdown", "chown", "rm"]

    if not check_if_in_allowed(command.split(" ")[0]):
        if command.split(" ")[0] in dangerous_keywords:
            confirm = input(f"\n[DANGEROUS COMMAND - VERIFY THIS IS CORRECT] Agent wants to run shell command: `{command}`. Allow? (y/n)")
            if confirm.lower() != 'y':
                return "Action denied by user."
        else:
            confirm = input(f"\n[PERMISSION REQUIRED] Agent wants to run shell command: `{command}`. Allow? (y/n) or Always Allow: (a)")
            if confirm.lower() == 'a':
                add_to_allow_list(command.split(" ")[0])
            elif confirm.lower() != 'y':
                return "Action denied by user."

    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30 # Prevent hanging commands
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return output if output else "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

def search_files(pattern: str, directory: str = ".") -> str:
    """Find files matching a specific name pattern within a directory.
    
    Args:
        pattern: The wildcard pattern to search for (e.g., '*.py', '*test*').
        directory: The root directory to start the search from. Defaults to current directory.
    Returns:
        A list of matching file paths as a string, or a message if none are found.
    """
    try:
        search_path = os.path.join(directory, f"**/{pattern}")
        # recursive=True allows searching through subdirectories
        matches = glob.glob(search_path, recursive=True) 
        
        if not matches:
            return f"No files found matching '{pattern}' in '{directory}'."
        return "\n".join(matches)
    except Exception as e:
        return f"Error searching files: {str(e)}"


def codebase_structure(path: str):
    """Generate a detailed structure of the codebase.
    
    Args:
        path: The path to the codebase.
    Returns:
        Returns the directory structure as a string.
    """
    return execute_shell("ls -R")

def check_if_in_allowed(command: str):
    """ Check if command is in allowed list
    Args:
        command: the prefix of the command.
    Returns:
        A success message or an error string.
    """

    try:
        memory_file = read_file("allowed.txt")
        if command in memory_file:
            return True
        else:
            return False
    except Exception as e:
        return f"Error adding to allow list: {str(e)}"

def add_to_allow_list(command: str):
    """ Adds command to the allow list
    Args:
        command: the prefix of the command.
    Returns:
        A success message or an error string.
    """

    try:
        memory_file = read_file("allowed.txt")
        write_file("allowed.txt", memory_file + "\n" + command)
        return "Successfully added to allow list."
    except Exception as e:
        return f"Error adding to allow list: {str(e)}"

def add_to_memory(information: str):
    """Adds new information to the memory file.
    
    Args:
        information: The information to add to the memory file.
    Returns:
        A success message or an error string.
    """

    try:
        memory_file = read_file("memory.txt")
        write_file("memory.txt", memory_file + "\n" + information)
        return "Successfully added to memory."
    except Exception as e:
        return f"Error adding to memory: {str(e)}"


    
def run_agent_with_tool():
    prompt = input("User Prompt: ").strip()
    if not prompt:
        print("No prompt provided. Exiting.")
        return
    print()

    # 1. Initialize a chat session to remember history automatically
    chat = client.chats.create(
        model='gemini-2.5-flash',
        config=types.GenerateContentConfig(
            tools=[read_file, write_file, execute_shell, search_files, add_to_memory, codebase_structure],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0.0
        )
    )

    # load memory.txt into chat history
    memory_file = read_file("memory.txt")
    chat.send_message(f"Here is the memory information associated with this codebase: {memory_file}")

    skill = find_skill(prompt)
    if skill:
        skill_prompt = read_file(f"skills/{skill}.txt")
        chat.send_message(f"Use the following skill information to help complete the task: {skill_prompt}")

    # 2. Send the initial prompt
    response = chat.send_message(prompt)

    # 3. The Agent Loop (capped at 10 iterations to prevent runaway loops)
    for step in range(20):
        if response.function_calls:
            function_responses = []
            
            for call in response.function_calls:
                print(f"\n🤖 Agent decided to call tool: {call.name}")
                # print(f"Arguments: {call.args}")
                
                # Act: Execute locally
                if call.name == "write_file":
                    tool_result = write_file(**call.args)
                elif call.name == "execute_shell":
                    tool_result = execute_shell(**call.args)
                elif call.name == "read_file":
                    tool_result = read_file(**call.args)
                elif call.name == "search_files":
                    tool_result = search_files(**call.args)
                elif call.name == "add_to_memory":
                    tool_result = add_to_memory(**call.args)
                elif call.name == "codebase_structure":
                    tool_result = codebase_structure(**call.args)
                else:
                    tool_result = "Unknown function."

                print(f"🔧 Tool Output:\n{tool_result}")
                
                # Package the result to send back to the LLM
                function_responses.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response={"result": tool_result}
                    )
                )
            
            # Observe/Think: Send the tool results back to the LLM
            response = chat.send_message(function_responses)
            
        else:
            # Check: Task is complete, LLM replied with text
            print("\n✅ Task Complete. Agent says:")
            print(response.text)
            break

        
if __name__ == "__main__":
    run_agent_with_tool()