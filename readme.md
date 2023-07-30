
# How to deploy this to Azure Spring Apps Enterprise

```
# Ensure you have the Spring extension installed
az extension add --name spring

# login
az login

# create a resource group
az group create --name ${RESOURCE_GROUP} \
    --location ${REGION}

# pro tip - looking for the location list?
az account list-locations --query "[].{DisplayName:displayName, Name:name}" -o table

# accept the terms
az provider register --namespace Microsoft.SaaS
az term accept --publisher vmware-inc --product azure-spring-cloud-vmware-tanzu-2 --plan asa-ent-hr-mtr

# create an ASA-E instance (give it a globally unique name -- due to DNS reasons)
az spring create --name ${SPRING_APPS_SERVICE} \
    --resource-group ${RESOURCE_GROUP} \
    --location ${REGION} \
    --sku Enterprise \

# set the defaults
az configure --defaults \
    group=${RESOURCE_GROUP} \
    location=${REGION} \
    spring=${SPRING_APPS_SERVICE}

# create the app construct (ex: jarvis)
az spring app create --name jarvis

# Ensure you're in the same directory as this code base and deploy the app (ex: jarvis)
az spring app deploy -n jarvis -d default --source-path . --env OPENAI_KEY="" TWILIO_ACCOUNT_SID="" TWILIO_AUTH_TOKEN="" BOT_NUMBER="" SECRET_KEY="" AZURE_RGO="" AZURE_SUBSCRIPTION="" ASAE_INSTANCE="" AZURE_DIRECTORYID="" AZURE_APPID="" AZURE_APP_VALUEID="" BOT_URL=""
```

# Where to get the keys
- Open AI (req CC): https://platform.openai.com/account/api-keys
- Twilio SID/Auth (req CC): https://console.twilio.com/?frameUrl=/console
- Bot's phone number (Twilio): https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

# App Registration Steps in Azure
- Create an "App Registration" under the `Azure Active Directory` Azure service (see the `+ Add`)
- Within your new App Registration, under `Certificates and Secrets`, create a new `client secrets`. Be sure and grab the `value` and save it. You'll need it for the `AZURE_APP_VALUEID` env var. Under `Overview`, you'll find `AZURE_DIRECTORYID` and `AZURE_APPID` information as well.
- Go to your `Resource Group`, select `Access Control (IAM)`, under `+ Add` create a `custom role`. Role should have full read access to Azure Spring Apps, and write access to "Update the deployment of an app in Azure Spring Apps".
- While still in `Access Control (IAM)`, create (`+ Add`) a `Role Assignment` and assign your custom role with your app registration.

# Twilio Webhook Configuration Steps

- Grab the URL to your app via. If deployed in Azure Spring Apps Enterprise:
    ```
    az spring app show -n (app-name)
    ```
- Navigate to your Twilio's [phone number](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming), click on it, scroll down to the Messaging Configuration section, under the "A message comes in" webhook, paste the URL in and append "/bot" to it.
- Text your bot 😀

# Additional Things
## Required Environment Variables Explained
```
OPENAI_KEY=""
# Required. This is your OpenAI key found here (after signup): https://platform.openai.com/account/api-keys

SECRET_KEY=""
# Required. This is just a random "secret" you use for Flask

TWILIO_ACCOUNT_SID=""
# Required. Your Twilio 'Account SID' can be found here (after signup): https://console.twilio.com/?frameUrl=/console

TWILIO_AUTH_TOKEN=""
# Required. Your Twilio 'Auth Secret' can be found here (under Account SID): https://console.twilio.com/?frameUrl=/console

BOT_NUMBER=""
# Required. This is your Twilio phone number, found here (after signup): https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

BOT_URL=""
# Required. This is this bot's URL. If deployed in Azure Spring Apps Enterprise you can find it using `az spring app show -n <app-name>`. This is used in the callback from Twilio.

AZURE_RGO="" 
# Required to make ASA-E integration to work. This is your Azure Resource Group

AZURE_SUBSCRIPTION="" 
# Required to make ASA-E integration to work. Your Azure Subscription ID

ASAE_INSTANCE="" 
# Required to make ASA-E integration to work. The ASA-E Instance name (for now hard coded to one instance)

AZURE_DIRECTORYID="" 
# Required to make ASA-E integration to work. Your Tenant ID

AZURE_APPID="" 
# Required to make ASA-E integration to work. Your "app registration"'s App ID in Azure Active Directory (used as the "account" for this bot when it's talking to Azure's APIs).

AZURE_APP_VALUEID=""
# Required to make ASA-E integration to work. Your "app registration" client "value" (it's right next to the secret--it becomes hidden after you save it).

LOGGING_LEVEL=""
# Optional. Default is set to INFO.
```

## Steps to Run Locally (Assumes Mac/Linux)

Using Docker:

```
docker build -t llm-chat-python .

docker run -it -v .:/app -p 8080:8080 llm-chat-python
```
In docker terminal:
```
# run all your export commands for env vars mentioned above
# And then run python command

python /app/app.py
```
Outside of docker terminal, in another terminal window:
```
# Install ngrok. This tool gives you a temporarily "published" URL
pip install pyngrok

# Run the ngrok tool
ngrok http 8080

# Grab the public URL that redirects to your localhost:8080
# Put this URL in your Twillio's phone number's messaging webhook
```

# Shout Out
Big shout out and thanks to this tutorial [here](https://www.twilio.com/blog/openai-gpt-3-chatbot-python-twilio-sms). It helped me get started with this project.