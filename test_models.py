if __name__ == "__main__":
    import requests

    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Accept": "application/json",
    }
    prompt = "Reply in exactly one sentence in conversational Tenglish: How are you doing today?"

    model = "meta/llama-3.1-8b-instruct"
    try:
        response = requests.post(
            invoke_url,
            headers=headers,
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 50},
            timeout=5,
        )
        if response.ok:
            print(f"Model {model} output: {response.json()['choices'][0]['message']['content'].strip()}")
        else:
            print(f"Model {model} failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Model {model} exception: {e}")
