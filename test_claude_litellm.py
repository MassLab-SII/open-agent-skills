import openai

client = openai.OpenAI(
	api_key="sk-3blkZv71U7lH1TQbVNOX6A",
	base_url="http://101.47.31.49:4000"
)

# Example with text only
response = client.chat.completions.create(
    model="gzy/claude-4.5-sonnet",
    messages=[
    {
        "role": "user",
        "content": "Hi"
    }
]
)

print(response)

