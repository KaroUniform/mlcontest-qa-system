from app.core.Expert.BertTiny2Embedding import BertTiny2Embedding
import chromadb
from chromadb.config import Settings
import pygsheets

class Expert():
    
    word_blacklist = []
    
    def __init__(self, path_to_google_api_key: str) -> None:
        """
        Initialize an instance of the class.

        Args:
            path_to_google_api_key (str): The path to the Google API key.

        This method initializes an instance of the class and takes the path to the Google API key as input.
        It performs the following actions:
        - Creates a client using the chromadb library with specified settings for chroma_db_impl and persist_directory.
        - Gets or creates a collection named "qa-expert" with a specified embedding function.
        - Authorizes the pygsheets library using the specified service file for Google authentication.
        - Opens a Google Sheets document with the specified key.
        """
        self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="qa-expert"))
        self.qa_collection = self.client.get_or_create_collection(
            name="qa-expert", 
            embedding_function=BertTiny2Embedding()
        )
        self._gc = pygsheets.authorize(service_file= 'app/settings/bask-google.json')
        self._sheet = self._gc.open_by_key("1r730Gc8KM6_4gRK8r4kyG2m_IzWIVdNYF9p4JOzt82o")
    
    
    def check_stopwords(self, target_string: str, blacklist: list = None) -> bool:
        """
        Check if any words from the blacklist are present in the target string.

        Args:
            target_string (str): The string to check for stop words.
            blacklist (list, optional): The list of stop words. Defaults to None.

        Returns:
            bool: True if any stop words are present, False otherwise.

        This method checks if any words from the blacklist are present in the target string.
        If the blacklist is not provided, the method uses the default word blacklist stored
        in the class attribute. It returns True if any stop words are found in the target string,
        and False otherwise.
        """
        blacklist = blacklist or self.word_blacklist
        return any(word in target_string for word in blacklist)
        
        
    def get_answer(self, text: str) -> str:
        """
        Get the answer for the given text.

        Args:
            text (str): The input text.

        Returns:
            str: The answer corresponding to the input text, or an empty string if no answer is found.

        This method retrieves the answer for the given text from the QA collection. It queries the collection
        with the lowercased version of the text as the query text and specifies to return only one result.
        If a result is found and its distance is less than 0.1, the method returns the answer from the metadata
        of the first result. Otherwise, it returns an empty string.
        """
        result = self.qa_collection.query(
            query_texts=[text.lower()],
            n_results=1,
        )
        if result['distances'][0][0] <0.1 :
            return result['metadatas'][0][0]['answer']
        return ""
    
    def add_question(self, question: str, answer: str) -> None:
        """
        Add a question and its answer to the QA collection.

        Args:
            question (str): The question to add.
            answer (str): The answer corresponding to the question.

        This method adds a question and its answer to the QA collection. It generates a unique question ID
        by counting the number of existing documents in the collection and incrementing it by 1. The lowercased
        version of the question is added as a document, and the answer is added as metadata with the question ID.
        The method also calls a helper method to add the question and answer to Google Sheets.
        """
        question_id = str(self.qa_collection.count())
        self.qa_collection.add(
            documents=[question.lower()], 
            metadatas=[{"answer": answer}], 
            ids=[question_id]
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
        """
        Update the QA collection from the Google Sheets QA worksheet.

        This method updates the QA collection by retrieving the question-answer pairs from the 'QA' worksheet
        in the Google Sheets document. It resets the client to clear the existing collection. It then iterates
        over the QA pairs, assigns a unique ID to each pair, and adds them to the QA collection with the question
        as the document and the answer as metadata. The IDs are assigned sequentially starting from 1.
        """
        self.client.reset()
        wks = self._sheet.worksheet_by_title('QA')
        qa_pairs = wks.get_values_batch(["A2:B1000"])[0]
        for id, pair in enumerate(qa_pairs, start=1):
            self.qa_collection.add(
                ids=str(id),
                documents=pair[0],
                metadatas={'answer': pair[1]}
            )
    
    def sync_stopwords_with_sheet(self) -> bool:
        """
        Synchronize the word blacklist with the 'Stopwords' worksheet in Google Sheets.

        This method synchronizes the word blacklist with the 'Stopwords' worksheet in the Google Sheets document.
        It retrieves the column values from the 'Stopwords' worksheet and updates the word blacklist attribute
        with the flattened list of values. The method returns a boolean indicating the success of the synchronization.
        """
        wks = self._sheet.worksheet_by_title('Stopwords')
        column_values = wks.get_values_batch(["A2:A1000"])
        self.word_blacklist = self._flatten_list(column_values)
    
    
