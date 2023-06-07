from fastapi import FastAPI, Request, HTTPException
import json
from app.core.Expert.Expert import Expert
from app.core.Reader.Reader import Reader
from app.core.Writer.Writer import Writer
from app.settings import settings

app = FastAPI()
expert = Expert('settings/bask-google.json')
reader = Reader()
writer = Writer(settings.OPEN_AI)

#TODO
@app.on_event('startup')
async def startup_event():
    pass

#TODO
@app.on_event('shutdown')
async def shutdown_event():
    pass

@app.get('/answer')
async def get_data(question: str):
    if len(question) > 300:
        raise HTTPException(status_code=400, detail="Question is too long")

    if expert.check_stopwords(question):
        return "There are stop words in the text"

    answer = expert.get_answer(question)
    if answer:
        return answer

    product_context = reader.product_range_maker(question)
    store_context = reader.extra_context_maker(question)
    prompt = writer.make_prompt(question, product_context, store_context)

    return writer.write_answer(prompt)