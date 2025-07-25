import os
from google import genai


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="models/gemini-1.5-flash-latest",
        contents="Say hello",
    )
    if response.candidates:
        print(response.candidates[0].text)
    else:
        print("No response")


if __name__ == "__main__":
    main()
