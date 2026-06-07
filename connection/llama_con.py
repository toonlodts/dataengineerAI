import requests

class LlamaConnection:
    def __init__(self, ):
        result = None
    
    def perform_llama_api_call(self, prompt, run_dir, layer):
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model":  "llama3",
                "prompt": prompt,
                "stream": False
            }
        )

        # temp_result = response.json()["response"]

        # with open(f"{run_dir}/{layer}/llama_output_temp.txt", "w", encoding="utf-8") as f:
        #     f.write(temp_result)

        # response = requests.post(
        #     "http://localhost:11434/api/generate",
        #     json={
        #         "model":  "llama3",
        #         "prompt": "I have just received this result with SQL code from an LLM. Can you transform this result so that it only contains SQL code which I can execute directly on a datawarehouse? \n\n\n"+temp_result,
        #         "stream": False
        #     }
        # )

        result = response.json()["response"]

        #print(result)

        with open(f"{run_dir}/{layer}/llama_output.txt", "w", encoding="utf-8") as f:
            f.write(result.replace("`", "").replace('sql', ''))
        
        return result.replace("`", "").replace('sql', '')