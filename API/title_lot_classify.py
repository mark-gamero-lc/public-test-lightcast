import pandas as pd
import requests
from os import environ
import config
import time
from tqdm import tqdm
tqdm.pandas()

class APIAuth:
    def __init__(self, client_id, client_secret, scope):
        self.url = "https://auth.emsicloud.com/connect/token"
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.token = ""
        self.expiry_time = time.time() - 1

    def get_token(self):
        # If we have no token or if the token has expired, request a new one
        if not self.token or time.time() > self.expiry_time:
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": self.scope,
            }
            headers = {"content-type": "application/x-www-form-urlencoded"}
            response = requests.request("POST", self.url, data=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.expiry_time = time.time() + data["expires_in"]
            else:
                print(response.status_code,response.reason)
        return self.token


# I reference my API credentials via a config file, but feel free to adjust to your preferred means of authentication
api_auth = APIAuth(config.lightcast_client_id, config.lightcast_client_secret, config.scopes)
print("set authentication")

# Read csv into a pandas dataframe - insert a file path here
titles_df = pd.read_csv(r"FILE_PATH_HERE")
titles_df

# define the function to classify a raw title to an lot
def normalize_title_to_lot(TITLE_RAW):
    url = "https://classification.emsicloud.com/classifications/2024.14/lot/classify"
    headers = {"Authorization": f"Bearer {api_auth.get_token()}"}

    payload = {
        "title": TITLE_RAW,
         "limit": 5,
         "fields": [
            "level",
             "id",
            "name",
            "parentId"
  ]
}

    response = requests.request("POST", url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()['data'][0]
        return [
            data['concept']['name'],
            data['confidence']
        ]
    else:
        return response.reason

print("normalizing titles")
# Function to normalize every title and description to an LOT name and
titles_df[['lot_name', 'confidence']] = titles_df.progress_apply(lambda x: pd.Series(normalize_title_to_lot(str(x['TITLE_RAW']))), axis = 1)
titles_df

# Saving the results to a csv
titles_df.to_csv("title_to_lot.csv", index=False)
print("saved results to csv")
