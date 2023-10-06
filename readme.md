# Overview
Jarvis is a larg language model (LLM) chatbot, powered by Azure OpenAI, that's been trained to manipulate an Azure Spring Apps Enterprise instance. This is a demonstration of "the art of the possible".

What Jarvis can currently do:
- Tell you the number of apps deployed
- The name of the apps deployed
- Confirm if an app has been created or deleted
- The app's URL
- Promote what's in staging into production (hard coded currently to the "cyan" app, and two deployments [blue and green])
- Rollback production (hard coded currently to the "cyan" app, and two deployments [blue and green])

Jarvis uses the 🧠 emoji to denote actions that were grounded in fact (namely, the functions used to do the above actions). It also assumes you've turned on Azure's OpenAI [Content Filtering](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter), to prevent both user and Jarvis from using harmful language.

# How to deploy this to Azure Spring Apps Enterprise (Non-Production)

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

# set the defaults
az configure --defaults \
    group=${RESOURCE_GROUP} \
    location=${REGION} \
    spring=${SPRING_APPS_SERVICE}

# example of creating a Standard C1 instance of redis. Note: by default this is publically accessible. Recommend for production use to hide this behind a private vNET.
az redis create --name {redis_name} --sku Standard --vm-size c1

# Grab primary key from the redis instance (aka REDIS_ACCESS_KEY)
az redis list-keys --name {redis_name}

# Grab hostname (aka REDIS_LOC)
az redis show --name jarvis-state --query hostName

# create an ASA-E instance (give it a globally unique name -- due to DNS reasons)
az spring create --name ${SPRING_APPS_SERVICE} \
    --resource-group ${RESOURCE_GROUP} \
    --location ${REGION} \
    --sku Enterprise \

# create the app construct (ex: jarvis)
az spring app create --name jarvis

# Ensure you're in the same directory as this code base and deploy the app (ex: jarvis)
az spring app deploy -n jarvis -d default --source-path . --env OPENAI_KEY="" AZURE_OPENAI_APIBASE="" OPENAI_DEPLOYMENT_NAME="" TWILIO_ACCOUNT_SID="" TWILIO_AUTH_TOKEN="" BOT_NUMBER="" SECRET_KEY="" AZURE_RGO="" AZURE_SUBSCRIPTION="" ASAE_INSTANCE="" AZURE_DIRECTORYID="" AZURE_APPID="" AZURE_APP_VALUEID="" BOT_URL="" REDIS_LOC="" REDIS_ACCESS_KEY=""
```

# Where to get the keys
- Azure Open AI: https://azure.microsoft.com/en-us/products/ai-services/openai-service
    - The AZURE_OPENAI_APIBASE's value should look something like https://XXX.openai.azure.com (where XXX is specific to you)... this can be found in Azure OpenAI Studio, under Completions section, "view code" (see example code, the value in openai.api_base).
    - OPENAI_KEY can be found in same "view code" section mentioned above, under Key.
    - The OPENAI_DEPLOYMENT_NAME is found in Azure OpenAI Studio, under Deployments. This is something you create.
    - Note: Requires 3.5-gpt-turbo or greater (Function support)
- Twilio SID/Auth (req CC): https://console.twilio.com/?frameUrl=/console
- Bot's phone number (Twilio): https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

# App Registration Steps via Azure UI (Custom Role)
- Create an "App Registration" under the `Azure Active Directory` Azure service (see the `+ Add`)
- Within your new App Registration, under `Certificates and Secrets`, create a new `client secrets`. Be sure and grab the `value` and save it. You'll need it for the `AZURE_APP_VALUEID` env var. Under `Overview`, you'll find `AZURE_DIRECTORYID` and `AZURE_APPID` information as well.
- Go to your `Resource Group`, select `Access Control (IAM)`, under `+ Add` create a `custom role`. Role should have full read access to Azure Spring Apps, and write access to "Update the deployment of an app in Azure Spring Apps".
- While still in `Access Control (IAM)`, create (`+ Add`) a `Role Assignment` and assign your custom role with your app registration.

# App Registration Steps via Azure CLI (RG level Contributor Access)
Create a registered app (`tanzu-jarvis`) with Contributor access.


```
export AZURE_SUBSCRIPTION=<Your Azure Subscription ID>
export AZURE_TENANTID=<Your Tenant/Directory ID>
export AZURE_RG=<Your resource group>

# Login
az login

# Set Subscription ID
az account set --subscription $AZURE_SUBSCRIPTION

# Create a Registered App that will be used as the "user" for the script
az ad app create --display-name tanzu-jarvis \
&& AZURE_APP_ID=$(az ad app create --display-name tanzu-jarvis --query appId --output tsv)

# Store this ID for future reference
echo $AZURE_APP_ID

# Grant the App Read-only access to your subscription
spid=$(az ad sp create --id $AZURE_APP_ID --query id --output tsv) \
&& az role assignment create --assignee $spid \
--role "Contributor" \
--subscription $AZURE_SUBSCRIPTION \
--scope /subscriptions/$AZURE_SUBSCRIPTION/resourceGroups/$AZURE_RG

# Create the "password" for the user, this will expire in 2 years
AZURE_APP_VALUEID=$(az ad app credential reset --id $AZURE_APP_ID --append --display-name tanzu-jarvis --years 2 --query password --output tsv)

# Store this password in a safe place (you can't access this again)
echo $AZURE_APP_VALUEID
```

# Twilio Webhook Configuration Steps

- Grab the URL to your app via. If deployed in Azure Spring Apps Enterprise:
    ```
    az spring app show -n (app-name)
    ```
- Navigate to your Twilio's [phone number](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming), click on it, scroll down to the Messaging Configuration section, under the "A message comes in" webhook, paste the URL in and append "/bot" to it.
- Text your bot 😀

# Additional Things
## Twilio Considerations
Due to campaign laws, you must to register your Twilio phone number under a "campaign" assuming a phone number in the USA will be texting it (otherwise it gets blocked). This registration process can take up to 7 weeks.

## Required Environment Variables Explained
```
AZURE_OPENAI_APIBASE=""
# Required. Should look something like https://XXX.openai.azure.com (where XXX is specific to you)... this can be found in Azure OpenAI Studio, under Completions section, "view code" (see example code, the value in openai.api_base).

OPENAI_KEY=""
# Required. Can be found in same "view code" section mentioned above, under Key.

OPENAI_DEPLOYMENT_NAME=""
# Required. Can be found in Azure OpenAI Studio, under Deployments. This is something you create.

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

REDIS_LOC=""
# Required to store the state of the conversation/messages (so you can scale Jarvis out if needed for performance reasons). This is the location (URL) of where redis is.

REDIS_ACCESS_KEY=""
# Required to store the state of the conversation/messages (so you can scale Jarvis out if needed for performance reasons). This is the "password" to accessing the redis instance.

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
export OPENAI_KEY=""
...

# install all app depdenencies
pip install -r requirements

# And then run using gunicorn command
gunicorn -c gunicorn_config.py app:app
```
Outside of docker terminal, in another terminal window:
```
# Install ngrok. This tool gives you a temporarily "published" URL
pip install pyngrok

# Run the ngrok tool
ngrok http 8080

# Grab the public URL that redirects to your localhost:8080 (note: this is temporary, and needs to be refresh occassionally)
# Put this URL in your Twillio's phone number's messaging webhook
```

# Shout Out
Big shout out and thanks to this tutorial [here](https://www.twilio.com/blog/openai-gpt-3-chatbot-python-twilio-sms). It helped me get started with this project.