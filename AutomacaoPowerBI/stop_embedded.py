# # Import packages
import requests
import adal
import json

# #  Setup  Parameters
tenant_id = ''

client_id = ''
client_secret = ''

subscriptionId = ''
resourceGroupName = ''
dedicatedCapacityName = ''

capacidadeId = ''
groupId = ''
datasetId = ''
capacity_body_remove = json.dumps({'capacityId':'00000000-0000-0000-0000-000000000000'})

authority_url = f'https://login.microsoftonline.com/{tenant_id}'
resource_url = 'https://analysis.windows.net/powerbi/api'
resource_azure_url = 'https://management.azure.com/'
status_url = f'https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.PowerBIDedicated/capacities?api-version=2021-01-01'
stop_url =  f'https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.PowerBIDedicated/capacities/{dedicatedCapacityName}/suspend?api-version=2021-01-01'
capacity_url = f'https://api.powerbi.com/v1.0/myorg/groups/{groupId}/AssignToCapacity'


# # Generate the token to turn on the embedded capacity
context_start = adal.AuthenticationContext(authority=authority_url,
                                     validate_authority=True,
                                     api_version=None)

token = context_start.acquire_token_with_client_credentials(resource_azure_url, client_id, client_secret)

access_token_azure = token.get('accessToken')


# # Generate the token for accessing Power BI APIs
context = adal.AuthenticationContext(authority=authority_url,
                                     validate_authority=True,
                                     api_version=None)

token = context.acquire_token_with_client_credentials(resource_url, client_id, client_secret)

access_token = token.get('accessToken')


# # set header
# Capacity embedded apu
header = {'Authorization': f'Bearer {access_token_azure}'}
# Workspace power bi api
headeraply = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}


# # check capacity status
status_capacity = requests.get(url=status_url, headers=header)
status_capacity = json.loads(status_capacity.content)
status = status_capacity['value'][0]['properties']['state']

# # If the capacity is paused, the code stops. Otherwise, a POST is performed to take the workspace out of capacity (if any) and pause the embedded capacity.

if status == 'Paused':
    print(status)
    print('Embedded was off')
    exit()
elif status == 'Succeeded':
    # remove workspace from capacity
    detach_capacity = requests.post(url=capacity_url, headers=headeraply, data=capacity_body_remove)
    print(detach_capacity.raise_for_status())
    print('Workspace removed from capacity')
    # paused embedded
    print(status)
    capacity_status = requests.post(url=stop_url, headers=header) 
    print('Embedded on, shutdown successfully.') 