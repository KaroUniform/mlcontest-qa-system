import openai

class Writer():
    def __init__(self, openai_key: str) -> None:
        openai.api_key = openai_key
    
    def make_prompt(self, question:str, product_cont: str, other_context: str):
        product_cont = product_cont[:3200]
        other_context = other_context[:500]
        return f"""
            Ты менеджер поддержки клиентов компании bask.ru. Будь дружелюбен. Отвечай на вопросы клиентов, используя только информацию из контекста.
            Если ты не можешь ответить на вопрос, напиши "ВЫЗВАТЬ МЕНЕДЖЕРА".
            Контекст o магазине: "{other_context}"
            Контекст o товарах: "{product_cont}"
            Вопрос: {question}
            """
    
    def write_answer(self, prompt:str):
        chat_completion = openai.Completion.create(
            model="text-davinci-003", 
            prompt=prompt,
            temperature=0,
            max_tokens=2000,
            stop=None
        )
        
        return chat_completion['choices'][0]['text']