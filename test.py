import time
from openai import OpenAI
from tabulate import tabulate

# Paste your NVIDIA API key here
NVIDIA_API_KEY = "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"

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

TEST_PROMPT = "What is 357 + 326? State only the exact final number."

def get_all_chat_models():
    """Fetches all models from NVIDIA NIM and filters for chat/text models."""
    print("Fetching available models from NVIDIA NIM...")
    try:
        models_response = client.models.list()
        all_models = [model.id for model in models_response.data]
        
        # Filter out models that are obviously for embeddings, images, or audio
        # to ensure we only test text-generation models
        excluded_keywords = ["embed", "vision", "nemo", "tts", "asr", "sdxl", "clip"]
        chat_models = [
            m for m in all_models 
            if not any(keyword in m.lower() for keyword in excluded_keywords)
        ]
        
        print(f"Found {len(all_models)} total models. Testing {len(chat_models)} compatible text models.\n")
        return chat_models
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def test_model(model_name):
    print(f"Testing: {model_name}... ", end="", flush=True)
    start_time = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a concise calculator assistant."},
                {"role": "user", "content": TEST_PROMPT}
            ],
            temperature=0.1,
            max_tokens=20,
            timeout=8.0  # Strict timeout so it skips slow/unresponsive models fast
        )
        latency = round(time.perf_counter() - start_time, 2)
        answer = response.choices[0].message.content.strip().replace("\n", " ")
        print(f"DONE ({latency}s)")
        
        return {
            "Model": model_name,
            "Status": "Working",
            "Latency (s)": latency,
            "Response": answer[:40]
        }
    except Exception as e:
        latency = round(time.perf_counter() - start_time, 2)
        err_msg = str(e).split("\n")[0] # Get just the first line of the error
        print(f"FAILED ({latency}s)")
        
        return {
            "Model": model_name,
            "Status": "Failed",
            "Latency (s)": latency,
            "Response": err_msg[:40]
        }

def main():
    models_to_test = get_all_chat_models()
    
    if not models_to_test:
        print("No models to test. Check your API key.")
        return

    print("=" * 70)
    print("Testing NVIDIA NIM Endpoints (This may take a few minutes)")
    print("=" * 70)

    results = []
    # Test up to a maximum number to prevent API rate limit bans (NVIDIA limits free RPM)
    for model in models_to_test[:30]: 
        result = test_model(model)
        results.append(result)
        time.sleep(1) # 1-second delay to avoid hitting rate limits

    # Sort results: working models first, ordered by fastest latency
    working = sorted([r for r in results if r["Status"] == "Working"], key=lambda x: x["Latency (s)"])
    failed = [r for r in results if r["Status"] != "Working"]
    final_table = working + failed

    print("\n" + "=" * 80)
    print("RESULTS (Ranked from Fastest to Slowest):")
    print("=" * 80)
    print(tabulate(final_table, headers="keys", tablefmt="grid"))
    
    if working:
        print(f"\n🏆 The fastest model is: {working[0]['Model']} at {working[0]['Latency (s)']} seconds!")
        print("Copy this model name into your voice calculator script.")

if __name__ == "__main__":
    main()