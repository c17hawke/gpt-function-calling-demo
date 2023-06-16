import openai
from dotenv import load_dotenv
import chainlit as cl
from src.llm import chat_completion_request, messages, functions
from src.sys_config import conv_prompt
from src.utils import get_current_weather
import json
import os

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def execute_function_call(assistant_message):
    if assistant_message.get("function_call").get("name") == "get_current_weather":
        location = json.loads(assistant_message.get("function_call").get("arguments") )["location"]
        results = get_current_weather(location)
    else:
        results = f"Error: function {assistant_message['function_call']['name']} does not exist"

    return results


def get_natural_response(content, message):
    convert_prompt = conv_prompt.replace("<query>", message).replace("<api_result>", content)
    messages.append({"role": "user", "content": convert_prompt})
    convert_prompt_response = chat_completion_request(messages=messages)
    print(f"\n>>>> recieved message: {convert_prompt_response.json()}")
    new_assistant_message = convert_prompt_response.json()["choices"][0]["message"]
    messages.append(new_assistant_message)
    updated_content = new_assistant_message["content"]
    print(f"\n>>>> natural response: \n{updated_content}")
    return updated_content

@cl.on_message
async def main(message: str):
    messages.append({"role": "user", "content": message})
    chat_response = chat_completion_request(messages=messages, functions=functions)
    print(f"\n>>>> complete_chat_response: \n{chat_response.json()}\n")
    
    assistant_message = chat_response.json()["choices"][0]["message"]
    print(f"\n>>>> assistant message: \n{assistant_message}\n")

    if assistant_message.get("function_call"):
        results = execute_function_call(assistant_message)
        print(f"\n>>>> results obtained from executing function call: \n{results}\n")
        content = json.dumps(results)
        content = get_natural_response(content, message)
    else:
        messages.append(assistant_message)
        content = assistant_message["content"]
        print(f"\n>>>> results obtained: \n{content}\n")
    
    print(f"\n>>>> Chat response: {content}\n")

    await cl.Message(
        content=content
    ).send()