import requests

print("=== Octoparse API Tester ===")
username = input("Enter Octoparse Username/Email: ")
password = input("Enter Octoparse Password: ")

print("\nKnocking on Octoparse's server...")
token_payload = {"grant_type": "password", "username": username, "password": password}
response = requests.post("https://dataapi.octoparse.com/token", data=token_payload)

print("\n--- OCTOPARSE RESPONSE ---")
print(response.json())
print("--------------------------")