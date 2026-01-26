import requests

def api(target, path, params={}):
    return requests.get(url=f'https://{target}/api/{path}', params=params, verify=False, auth=requests.auth.HTTPBasicAuth('pytest', 'cats2023')).json()
