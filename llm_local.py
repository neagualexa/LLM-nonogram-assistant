from gpt4all import GPT4All
import time

model_name = 'llama-2-7b-chat.Q4_0.gguf'
model_path = './models/' 

question = "What are Nonograms and give me 3 tips to solve them."

model = GPT4All(model_name = model_name, model_path=model_path)
system_template = 'You are a helpful instructor and assistant.'
prompt_template = 'USER: {0}\nASSISTANT: '
        
def callLLM(user_message, past_user_inputs=[], generated_responses=[]):
    start_time = time.time()
    prompts = [user_message]
    first_input = system_template + prompt_template.format(prompts[0])
    response = model.generate(first_input, temp=0, max_tokens=100)
    end_time = time.time()
    latency = end_time - start_time
    print(f"Latency: {latency} seconds")
    print(response)
    return response
    # for prompt in prompts[1:]:
    #     response = model.generate(prompt_template.format(prompt), temp=0)
    #     print(response)

# callLLM(question)
# callLLM("Can you repeat the first tip?")

# ##### LANGCHAIN #####
# from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
# from langchain.chains import LLMChain
# from langchain.prompts import PromptTemplate
# from langchain_community.llms import GPT4All

# template = """Question: {question}

# Answer: Let's think step by step."""

# prompt = PromptTemplate(template=template, input_variables=["question"])

# local_path = (
#     model_path + model_name
# )

# # Callbacks support token-wise streaming
# callbacks = [StreamingStdOutCallbackHandler()]

# # Verbose is required to pass to the callback manager
# llm = GPT4All(model=local_path, callbacks=callbacks, verbose=True)

# # If you want to use a custom model add the backend parameter
# # Check https://docs.gpt4all.io/gpt4all_python.html for supported backends
# # llm = GPT4All(model=local_path, backend="gptj", callbacks=callbacks, verbose=True)

# llm_chain = LLMChain(prompt=prompt, llm=llm)

# llm_chain.invoke(question)