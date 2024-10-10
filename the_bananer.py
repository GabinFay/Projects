import os

import pangea.exceptions as pe
from pangea.config import PangeaConfig
from pangea.services import Redact

token = os.getenv("PANGEA_REDACT_TOKEN")
assert token

config = PangeaConfig(domain="aws.us.pangea.cloud")
redact = Redact(token=token, config=config)


# text = "John's email is john.doe@example.com, and his IP address is 192.168.1.1. He lives in New York, which is a busy LOCATION. His meeting is scheduled for 2024-09-11T14:30:00. His SSN is 123-45-6789, and his credit card number is 4111 1111 1111 1111. Also, his phone number is (555) 123-4567, and his IBAN is DE89 3704 0044 0532 0130 00."

# New text variable containing the content of to_redact.txt
text = """Subject: Q3 Sales Report and Client Updates

Hi Team,

I wanted to provide an update on our recent sales progress and share some key client information that may be relevant for our upcoming strategy meeting. Please review the details below and let me know if you have any questions.

Client: Johnson & Sons

Meeting Date: September 25, 2024, 2:00 PM
Location: 123 Main St, Springfield, IL
Contact: John Johnson
Email: john.johnson@johnsons.com
Phone: +1-312-555-7890
Contract Number: 4321-JOHN-6789
Quarterly Sales Figures
We achieved a 12% growth in Q3, thanks to the new advertising campaign. See the attached sales report for full details.
Please review the forecast for Q4 to ensure we stay on track with our goals.

Payment Information

Bank Transfer: IBAN DE44 5001 0517 5407 3249 31
SSN: 123-45-6789
Credit Card: 4111 1111 1111 1111
IP Address Logged: 192.168.0.1
For security reasons, we've logged all access related to the shared client portal. Ensure any external parties are vetted.

Best regards,
Jane Doe
Marketing Manager
jane.doe@company.com"""


try:
    redact_response = redact.redact(text=text)
    print(f"Redacted text: {redact_response.result.redacted_text}")
except pe.PangeaAPIException as e:
    print(f"Embargo Request Error: {e.response.summary}")
    for err in e.errors:
        print(f"\t{err.detail} \n")

redacted_text = redact_response.result.redacted_text

import requests


API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/9c804fd3d02d1b4718dfe1981cd536ab/ai/run/"
headers = {"Authorization": "Bearer qYZQgHKAkrufmTynRimbZ4JnDbqmL7kunxVVonYM"}


def run(model, inputs):
    input = { "messages": inputs }
    response = requests.post(f"{API_BASE_URL}{model}", headers=headers, json=input)
    return response.json()


inputs = [
    { "role": "system", "content": f"You will answer questions related to this document :  {redacted_text}" },
    { "role": "user", "content": "How many times was the word Banana in the document ?"}
]
output = run("@cf/meta/llama-3-8b-instruct", inputs)
# print(output)
print('\n\n')

print(output['result']['response'])