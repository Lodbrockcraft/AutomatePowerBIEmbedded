# Required: create service principal 
# how to create a service principal: link https://www.youtube.com/watch?v=bJz7LIVNCgE&t=357s&ab_channel=DhruvinShah
# microsoft documentation, step 1 and 2: link https://docs.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal
# Step 3 - Enable the Power BI service admin settings: link https://docs.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal

# API permissions required for service principal: Tenant.Read.All, Tenant.ReadWrite.All, Workspace.Read.All, Workspace.ReadWrite.All, Capacity.Read.All, Capacity.ReadWrite.All, 
#        User.Read, offline_access, Dataset.Read.All, Dataset.ReadWrite.All

# API documentation for connecting Power BI Embedded
# https://docs.microsoft.com/pt-br/rest/api/power-bi-embedded/capacities/resume

# API documentation for turning off Power BI Embedded
# https://docs.microsoft.com/pt-br/rest/api/power-bi-embedded/capacities/suspend

# API documentation for moving and taking a workspace out of Power BI Embedded capacity
# https://docs.microsoft.com/en-us/rest/api/power-bi/capacities/groups-assign-to-capacity

# API documentation to update a power bi dataset
# https://docs.microsoft.com/en-us/rest/api/power-bi/datasets/refresh-dataset-in-group

# API documentation to see the current status and update history of a dataset
# https://docs.microsoft.com/en-us/rest/api/power-bi/datasets/get-refresh-history-in-group

# API documentation to cancel a power bi dataset update
# https://docs.microsoft.com/en-us/rest/api/power-bi/datasets/cancel-refresh

# # Import packages
import requests
import adal
import json


# #  Setup  Parameters
tenant_id = ''

authority_url = f'https://login.microsoftonline.com/{tenant_id}'
resource_url = 'https://analysis.windows.net/powerbi/api'
resource_azure_url = 'https://management.azure.com/'

client_id = ''
client_secret = ''

subscriptionId = ''
resourceGroupName = ''
dedicatedCapacityName = ''

capacidadeId = ''
groupId = ''
datasetId = ''

# # Check if the dataset is updating.
# 
# If the dataset is refreshing(statusrefresh == 'Unknown' ) and the refresh type is other than OnDemand(refreshType != 'OnDemand'), we run an API to cancel the dataset refresh.
# If the dataset is refreshing(statusrefresh == 'Unknown' ) and the refresh type is equal to OnDemand(refreshType == 'OnDemand'), the process stops.
# After we receive one of these statuses, we proceed with the code.
# 
# Necessary to interrupt the process due to an api limitation that cancels the dataset update, according to the documentation, OnDemand type updates cannot be canceled.

# Generate token for accessing Power BI APIs
def access_token():
    context = adal.AuthenticationContext(authority=authority_url,
                                        validate_authority=True,
                                        api_version=None)

    token = context.acquire_token_with_client_credentials(resource_url, client_id, client_secret)
    access_token = token.get('accessToken')
    return access_token

# # Generate the token to turn on the embedded capacity
def access_token_azure():
    context_start = adal.AuthenticationContext(authority=authority_url,
                                        validate_authority=True,
                                        api_version=None)

    token = context_start.acquire_token_with_client_credentials(resource_azure_url, client_id, client_secret)

    access_token_azure = token.get('accessToken')
    return access_token_azure

header = {'Authorization': f'Bearer {access_token()}'}

#  Get status dataset
statuspbi_url = f'https://api.powerbi.com/v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes?$top=1'

statuspbi = requests.get(url=statuspbi_url, headers=header)
statuspbi = json.loads(statuspbi.content)['value'][0]

statusrefresh = statuspbi['status']
refreshId = statuspbi['requestId']
refreshType = statuspbi['refreshType']
statuswhile = ''

# set course according to dataset conditions
cancel_url = f'https://api.powerbi.com/v1.0/myorg/datasets/{datasetId}/refreshes/{refreshId}'

if (statusrefresh == 'Unknown') and (refreshType != 'OnDemand'):
    cancel_refresh = requests.delete(url=cancel_url, headers=header)
elif (statusrefresh == 'Unknown') and (refreshType == 'OnDemand'):
    print('Dataset com uma atualização OnDemand, parando os processos')
    exit()

print('Ok')


# # Turn on Power BI Embedded Capacity
start_url = f'https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.PowerBIDedicated/capacities/{dedicatedCapacityName}/resume?api-version=2021-01-01'

header_start = {'Authorization': f'Bearer {access_token_azure()}'}

capacity_start = requests.post(url=start_url, headers=header_start)

print(capacity_start.raise_for_status())


# # Creates a loop that checks if the capacity is active, before running the rest of the code
status_url = f'https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.PowerBIDedicated/capacities?api-version=2021-01-01'

status = ''

while status != 'Succeeded':
    status_capacity = requests.get(url=status_url, headers=header_start)
    status_capacity = json.loads(status_capacity.content)
    status = status_capacity['value'][0]['properties']['state']
print('Active capacity')

# # Move workspace to embedded capacity
headeraply = {'Authorization': f'Bearer {access_token()}', 'Content-Type': 'application/json'}

body_capacity = json.dumps({'capacityId':f'{capacidadeId}'})

capacity_url = f'https://api.powerbi.com/v1.0/myorg/groups/{groupId}/AssignToCapacity'

move_workspace = requests.post(url=capacity_url, headers=headeraply, data=body_capacity)

print(move_workspace.raise_for_status())

# # Refresh Power BI Dataset in Server
refresh_url = f'https://api.powerbi.com/v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes'

header = {'Authorization': f'Bearer {access_token()}'}

r = requests.post(url=refresh_url, headers=header)

print(r.raise_for_status())


# # Check dataset update status
statuspbi_url = f'https://api.powerbi.com/v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes?$top=1'

statuswhile = 'Unknown'

while statuswhile == 'Unknown':
    getstatus = requests.get(url=statuspbi_url, headers=header)
    getstatus = json.loads(getstatus.content)['value'][0]
    statuswhile = getstatus['status']

print('Refresh completed')

# # Takes workspace out of embedded capacity
headeraply = {'Authorization': f'Bearer {access_token()}', 'Content-Type': 'application/json'}

capacity_body_remove = json.dumps({'capacityId':'00000000-0000-0000-0000-000000000000'})

capacity_url = f'https://api.powerbi.com/v1.0/myorg/groups/{groupId}/AssignToCapacity'

detach_capacity = requests.post(url=capacity_url, headers=headeraply, data=capacity_body_remove)

print(detach_capacity.raise_for_status())

# # Stop the Power BI Embedded Capacity
stop_url =  f'https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.PowerBIDedicated/capacities/{dedicatedCapacityName}/suspend?api-version=2021-01-01'

header = {'Authorization': f'Bearer {access_token_azure()}'}

capacity_status = requests.post(url=stop_url, headers=header)

print(capacity_status.content)