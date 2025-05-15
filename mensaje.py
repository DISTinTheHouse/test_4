import requests

url = "https://graph.facebook.com/v17.0/683402724847602/messages"
headers = {
    "Authorization": "Bearer EAARDEZAVONqsBOZChYeZBaG9TFpz35WzvGEhuFa77sxBy9eJjSI6CzYDgpuvJahl83ZAwKaxeIa8geTBei1dC6Wahy6ZCEWhn1M0vzSAz0OkXkW8kAIWrBXl8QxKbaQjyXAhvSzcUCZAiNj7YTjDTrKyQYSdp6ZBcTKj2aBvaQPR6pZCOAZAesj4Bup9dMaEiZCjRKeKStwQ1z4RfOrIJgBigOi0Ui",
    "Content-Type": "application/json"
}
payload = {
    "messaging_product": "whatsapp",
    "to": "523338449486",  # tu número verificado
    "type": "template",
    "template": {
        "name": "confirmacion_reserva",
        "language": {"code": "es_MX"}
    }
}

response = requests.post(url, headers=headers, json=payload)
print(response.status_code)
print(response.text)
