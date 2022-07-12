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

authority_url = f'https://login.microsoftonline.com/{tenant_id}'
resource_url = 'https://analysis.windows.net/powerbi/api'
resource_azure_url = 'https://management.azure.com/'
status_url = f'https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.PowerBIDedicated/capacities?api-version=2021-01-01'
stop_url =  f'https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.PowerBIDedicated/capacities/{dedicatedCapacityName}/suspend?api-version=2021-01-01'


# # Generate the token to turn on the embedded capacity
context_start = adal.AuthenticationContext(authority=authority_url,
                                     validate_authority=True,
                                     api_version=None)

token = context_start.acquire_token_with_client_credentials(resource_azure_url, client_id, client_secret)

access_token_azure = token.get('accessToken')

# # check capacity status
header = {'Authorization': f'Bearer {access_token_azure}'}


status_capacity = requests.get(url=status_url, headers=header)
status_capacity = json.loads(status_capacity.content)
status = status_capacity['value'][0]['properties']['state']

# If the capacity is paused, the code is interrupted. Otherwise, a POST is performed to pause the capacity.

if status == 'Paused':
    print(status)
    print('Embedded was off')
    exit()
elif status == 'Succeeded':
    print(status)
    capacity_status = requests.post(url=stop_url, headers=header) 
    print('Embedded on, shutdown successfully.')