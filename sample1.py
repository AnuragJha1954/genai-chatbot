from google import genai

# Only run this block for Gemini Developer API
client = genai.Client(api_key='')
query = input("Enter your prompt here: ")
# Send single prompt, wait for the model to return the entire output
response = client.models.generate_content(model="gemini-2.5-flash", contents= query,)
print(response.text)