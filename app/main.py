import argparse
import os
import sys

from openai import OpenAI
import json

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

def read(file_path):
    if file_path != None and os.path.exists(file_path):
        with open(file_path, "r") as f:
            file_contents = f.read()
            return file_contents
    else:
        return f"File {file_path} does not exist"

def write(file_path, contents):
    with open(file_path, "w") as f:
        f.write(contents)
    return f"Wrote to file {file_path}"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    READ = {
        "type": "function",
        "function": {
            "name": "Read",
            "description": "Read and return the contents of a file",
            "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                "type": "string",
                "description": "The path to the file to read"
                }
            },
            "required": ["file_path"]
            }
        }
    }
    WRITE = {
        "type": "function",
        "function": {
            "name": "Write",
            "description": "Write content to a file",
            "parameters": {
            "type": "object",
            "required": ["file_path", "content"],
            "properties": {
                "file_path": {
                "type": "string",
                "description": "The path of the file to write to"
                },
                "content": {
                "type": "string",
                "description": "The content to write to the file"
                }
            }
            }
        }
        }
    
    messages = [{"role": "user", "content": args.p}]

    while(True):
        
        print(f"Sending request to model {messages}", file=sys.stderr)
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=[READ, WRITE]
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)

        message = chat.choices[0].message
        messages.append(message)
        if message.tool_calls != None:
            for tool_call in message.tool_calls:
                if tool_call.type == "function":
                    function = tool_call.function
                    if function.name == "Read":
                        arguments = json.loads(function.arguments)
                        file_path =  arguments["file_path"]
                        result = read(file_path)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                    if function.name == "Write":
                        arguments = json.loads(function.arguments)
                        file_path =  arguments["file_path"]
                        contents = arguments["content"]
                        result = write(file_path, contents)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
        else:
            print(chat.choices[0].message.content)
            break


if __name__ == "__main__":
    main()
