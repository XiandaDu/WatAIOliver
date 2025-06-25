import os
import google.generativeai as genai


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")
    genai.configure(api_key=api_key, transport="rest")
    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    response = model.generate_content("Say hello")
    print(response.text)


if __name__ == "__main__":
    main()
