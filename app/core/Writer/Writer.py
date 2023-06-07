import openai

class Writer():
    def __init__(self, openai_key: str):
        """
        Initialize an instance of the class.

        Args:
            openai_key (str): The OpenAI API key.

        Set the OpenAI API key by assigning it to the `openai.api_key` variable.
        """
        openai.api_key = openai_key
    
    def make_prompt(self, question:str, product_cont: str, other_context: str):
        """
        Generate a prompt for the OpenAI model.

        Args:
            question (str): The question from the customer.
            product_cont (str): The context about products.
            other_context (str): The context about the store.

        Returns:
            str: The generated prompt for the OpenAI model.

        This method takes a customer's question, product context, and other context as input.
        It truncates the question to a maximum of 380 characters, the product context to a maximum
        of 3200 characters, and the other context to a maximum of 500 characters. Then, it generates
        a formatted prompt string that includes the customer's truncated question, the truncated
        product context, and the truncated other context. The prompt instructs the model to be friendly,
        answer customer questions using only the provided context, and prompt for a manager if unable to answer.
        The generated prompt is returned as a string.
        """
        question = question[:380]
        product_cont = product_cont[:3200]
        other_context = other_context[:500]
        return f"""
            Ты менеджер поддержки клиентов компании bask.ru. Будь дружелюбен. Отвечай на вопросы клиентов, используя только информацию из контекста.
            Если ты не можешь ответить на вопрос, напиши "ВЫЗВАТЬ МЕНЕДЖЕРА".
            Контекст o магазине: "{other_context}"
            Контекст o товарах: "{product_cont}"
            Вопрос: {question}
            """
    
    def write_answer(self, prompt:str, model="text-davinci-003"):
        """
        Generate an answer based on the provided prompt.

        Args:
            prompt (str): The prompt for generating the answer.

        Returns:
            str: The generated answer.

        This method uses the OpenAI Completion API to generate an answer based on the provided prompt.
        It sends a request to the API with the specified model, prompt, temperature, max_tokens, and stop
        parameters. The temperature is set to 0 to generate deterministic output. The max_tokens parameter
        limits the length of the generated answer. The API response contains the generated completion, and
        the method extracts the generated answer from the response and returns it as a string.
        """
        chat_completion = openai.Completion.create(
            model=model, 
            prompt=prompt,
            temperature=0,
            max_tokens=2000,
            stop=None
        )
        
        return chat_completion['choices'][0]['text']