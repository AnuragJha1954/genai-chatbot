from google import genai

# Only run this block for Gemini Developer API
client = genai.Client(api_key='AIzaSyC2z6JrSJiz2CfbACivW4l8b07wm_Ou3ZY')
query = input("What do you want to ask?: ")
# Stream the responses like on Gemini
response = client.models.generate_content_stream(model="gemini-2.5-flash",contents=query)
for chunk in response:
    print(chunk.text, end="")