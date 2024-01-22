import requests

API_TOKEN = "gP2CVXklJFBVazLlSQ4M1t0lhIdEZM5w"
API_URL = "https://fyp-workspace-dialogpt.eastus2.inference.ml.azure.com/score"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()
	
output = query({
	"inputs": {
		"past_user_inputs": [],
		"generated_responses": [],
		"text": "Who are you?"
	},
})

print(output)


