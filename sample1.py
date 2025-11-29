from google import genai

# Only run this block for Gemini Developer API
client = genai.Client(api_key='AIzaSyC2z6JrSJiz2CfbACivW4l8b07wm_Ou3ZY')
query = input("Enter your prompt here: ")
# Send single prompt, wait for the model to return the entire output
response = client.models.generate_content(model="gemini-2.5-flash", contents= query,)
print(response.text)