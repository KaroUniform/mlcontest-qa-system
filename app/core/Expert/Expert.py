from app.core.Expert.BertTiny2Embedding import BertTiny2Embedding
import chromadb
from chromadb.config import Settings
import pygsheets

class Expert():
    
    word_blacklist = []
    
    def __init__(self, path_to_google_api_key: str) -> None:
        self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="qa-expert"))
        self.qa_collection = self.client.get_or_create_collection(
            name="qa-expert", 
            embedding_function=BertTiny2Embedding()
        )
        self._gc = pygsheets.authorize(service_file= 'app/settings/bask-google.json')
        self._sheet = self._gc.open_by_key("1r730Gc8KM6_4gRK8r4kyG2m_IzWIVdNYF9p4JOzt82o")
    
    
    def check_stopwords(self, target_string: str, blacklist: list = None) -> bool:
        if(not blacklist): blacklist = self.word_blacklist
        return any(word in target_string for word in blacklist)
        
        
    def get_answer(self, text: str) -> str | bool:
        result = self.qa_collection.query(
            query_texts=[text.lower()],
            n_results=1,
        )
        if(result['distances'][0][0] <0.1):
            return result['metadatas'][0][0]['answer']
        else:
            return False
    
    def add_question(self, question: str, answer: str) -> None:
        self.qa_collection.add(
            documents=[question.lower()], 
            metadatas=[{"answer":answer}], 
            ids=[str(self.qa_collection.count())]
        )
        self._add_question_to_google([question, answer])
    
    def _add_question_to_google(self, qa_pair: list) -> None:
        wks = self._sheet.worksheet_by_title('QA')
        wks.append_table(values=qa_pair)
    
    def _flatten_list(self, nested_list:list):
        flat_list = []
        for item in nested_list:
            if isinstance(item, list):
                flat_list.extend(self._flatten_list(item))
            else:
                flat_list.append(item)
        return flat_list
    
    def update_qa_from_sheet(self) -> None:
        self.client.reset()
        wks = self._sheet.worksheet_by_title('QA')
        qa_pairs = wks.get_values_batch(["A2:B1000"])[0]
        for pair, id in zip(qa_pairs, range(len(qa_pairs))):
            self.qa_collection.add(ids=str(id), documents=pair[0], metadatas={'answer':pair[1]})
    
    def sync_stopwords_with_sheet(self) -> bool:
        wks = self._sheet.worksheet_by_title('Stopwords')
        column_values = wks.get_values_batch(["A2:A1000"])
        self.word_blacklist = self._flatten_list(column_values)
    
    
