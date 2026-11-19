


from gemini_client import ask_gemini

print("Testing Growth360 Gemini connection...")

response = ask_gemini(
    "You are the AI assistant for Growth360. "
    "Reply with a short greeting to a cafe owner "
    "and explain in one sentence how you can help their business."
)

print("\nGemini Response:")
print("----------------")
print(response)

print("\nGemini connection successful!")
