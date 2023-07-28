import os
import openai
import logging
import requests
import json

openai.api_key = os.environ.get('OPENAI_KEY')

subscription = os.environ['AZURE_SUBSCRIPTION']
asae_instance = os.environ['ASAE_INSTANCE']
directory_id = os.environ['AZURE_DIRECTORYID']
app_id = os.environ['AZURE_APPID']
app_value_id = os.environ['AZURE_APP_VALUEID']
azure_rgo = os.environ['AZURE_RGO']
#debug
logging.info("chatbot started")
completion = openai.ChatCompletion()

messages=[
        {"role": "system", "content": "Your name is Jarvis. You are a personal AI helper for Azure Spring Apps Enterprise."},
        {"role": "user", "content": "How many apps are deployed in production?"},
        {"role": "assistant", "content": "Three: Blue, Cyan, and Jarvis."},
    ]

def get_data_with_authentication(url, token):
    print("Running GET with auth...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    print(response)
    return response

def post_data_with_authentication(url, token, payload):
    print("Running POST with auth...")

    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    print(response.text)
    return response

def azure_auth():
    url = "https://login.microsoftonline.com/{}/oauth2/token".format(directory_id)

    payload = "grant_type=client_credentials&client_id={}&client_secret={}&resource=https%3A%2F%2Fmanagement.azure.com%2F".format(app_id,app_value_id)

    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': 'fpc=AjtfSXJH2GxLg3UqoXUjQlmGw70iAwAAAITpVNwOAAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print("Azure auth response: {}".format(str(response.text)))
    bearer_token = response.json()["access_token"]

    return bearer_token

def fetch_app_names():
    url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance)

    azure_token = azure_auth()
    print(azure_token)

    try:
        print("Authenticating...")
        response = get_data_with_authentication(url, azure_token)


        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print("going into if statement")
            data = response.json()["value"]
            print(data)
            print("/////////////")
            app_list = []
            for i in data:
                app_list.append(i["name"])
            return str(app_list).strip("[").strip("]")
            # parsed = data
        else:
            error_message = f"Failed to fetch data. Status code: {response.status_code}"
            print(error_message)

    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        print(error_message)

def set_production(app):
    query_url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps/{}/deployments/green?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance, app)
    set_url = "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.AppPlatform/Spring/{}/apps/{}/setActiveDeployments?api-version=2023-05-01-preview".format(subscription, azure_rgo, asae_instance, app)

    azure_token = azure_auth()
    print(azure_token)

    try:
        print("Authenticating...")
        response = get_data_with_authentication(query_url, azure_token)
        print("///////")
        print(response.text)
        print("//////////")
        active = response.json()["properties"]["active"]
        print(active)
        if active:
            # Green is active, so need to set Blue to production
            print("green is active, switching to blue")
            payload = {
            "activeDeploymentNames": [
                "blue"
                ]
            }

            post_data_with_authentication(set_url, azure_token, payload)
            print("Done")
        else:
            # Blue is active, so need to set Green to production
            print("blue is active, switching to green")
            payload = {
            "activeDeploymentNames": [
                "green"
                ]
            }

            post_data_with_authentication(set_url, azure_token, payload)
            print("Done")
    except requests.exceptions.RequestException as e:
        error_message = f"Error occurred: {e}"
        print(error_message)

def ask(question, chat_log=None):

    if chat_log is None:
        chat_log = messages
        chat_log = messages.append({"role":"user","content":question})
    chat_log = messages.append({"role":"user","content":question})
    functions = [
        {
            "name": "fetch_app_names",
            "description": "Get current app names deployed into production",
            "parameters": {
                "type": "object"
            }
        }
    ]
    if "promote" and "production" in question:
        set_production("cyan")
        response_message = "I've promoted staging into production."
        return response_message

    if "apps" and ("many" or "which") in question:
        apps = fetch_app_names()
        response_message = "The apps currently created are {}".format(apps)
        return response_message


    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo-0613",
        messages = messages
        # TODO: Get function working... (this part is broken?)
        # functions = functions,
        # function_call="auto",
    )

    response_message = response["choices"][0]["message"]["content"]

    # TODO: Get function working.
    # if response_message.get("function_call"):
    #     available_functions = {
    #         "fetch_app_names": fetch_app_names
    #     } 
    #     function_name = response_message["function_call"]["name"]
    #     fuction_to_call = available_functions[function_name]
    #     function_response = fuction_to_call()

    #     messages.append(response_message)  # extend conversation with assistant's reply
    #     messages.append(
    #         {
    #             "role": "function",
    #             "name": function_name,
    #             "content": function_response,
    #         }
    #     )  # extend conversation with function response
    #     second_response = openai.ChatCompletion.create(
    #         model="gpt-3.5-turbo-0613",
    #         messages=messages,
    #     )  # get a new response from GPT where it can see the function response
    #     return second_response
    return response_message

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = messages
    chat_log = messages.append({"role":"assistant","content":answer})
    return chat_log

