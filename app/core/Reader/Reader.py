import spacy
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.qparser import QueryParser
from whoosh.query import And, Or
from whoosh.query import NumericRange
import string
import pygsheets


class Reader():
    
    _extra_context = {}
    
    def __init__(self, ner_model_path = 'core/reader/ner-model', whoosh_schema_path = 'core/reader/bask_products'):
        """
        Initialize an instance of the class.
    
        Args:
            ner_model_path (str): The path to the NER model.
            whoosh_schema_path (str): The path to the Whoosh schema.
    
        This method sets the paths for the NER model and Whoosh schema. It loads the NER model using
        spacy.load() and assigns it to the instance variable self.nlp. It also loads the "ru_core_news_md"
        model from spacy and assigns it to self.lemma. It opens the Whoosh schema directory using open_dir()
        and assigns it to self.ix. It authorizes pygsheets using a service file located at 'app/settings/bask-google.json'
        and assigns it to self._gc. It opens a Google Sheets spreadsheet by key using self._gc and assigns it
        to self._sheet. Finally, it calls the sync_extra_context() method to synchronize extra context from the spreadsheet.
        """
        self.ner_model_path = ner_model_path
        self.whoosh_schema_path = whoosh_schema_path
        self.nlp = spacy.load(self.ner_model_path) 
        self.lemma = spacy.load("ru_core_news_md")
        self.ix = open_dir(self.whoosh_schema_path)
        self._gc = pygsheets.authorize(service_file= 'app/settings/bask-google.json')
        self._sheet = self._gc.open_by_key("1r730Gc8KM6_4gRK8r4kyG2m_IzWIVdNYF9p4JOzt82o")
        self.sync_extra_context()
    
    def product_range_maker(self, user_question:str, limit=2) -> str:
        """
        Perform a search based on the user question and return the content of the search results.

        Args:
            user_question (str): The user's question for the search.
            limit (int): The maximum number of search results to return.

        Returns:
            str: The content of the search results as a string.

        Raises:
            ValueError: If the user_question is empty.
        """
        if not user_question:
            raise ValueError("User question can't be empty")

        doc = self.nlp(user_question)
        with self.ix.searcher() as searcher:
            parser = QueryParser("content", self.ix.schema)
            filter_query = NumericRange("in_stocks", 1, None)  # Search for values where in_stocks > 0
            query = And([
                Or([parser.parse(str(x)) for x in doc.ents if x.label_ == 'Product']),
                Or([parser.parse(str(x)) for x in doc.ents if x.label_ == 'description'])
            ])
            filtered_query = query & filter_query
            results = searcher.search(filtered_query, limit=limit)
        return "\n".join([hit['content'] for hit in results])
    
    def extra_context_maker(self, user_question: str) -> str:
        """
        Create extra context based on the user question.

        Args:
            user_question (str): The user's question.

        Returns:
            str: Extra context about company derived from the user question as a string.

        Raises:
            ValueError: If the user_question is empty.
        """
        if not user_question: 
            raise ValueError("User question can't be empty")
        
        user_question = user_question.translate(str.maketrans("", "", string.punctuation))
        doc = self.lemma(user_question)
        raw_context = [self._extra_context.get(str(token.lemma_), "") for token in doc]
        return "\n".join(set(raw_context))

    def sync_extra_context(self) -> None:
        """
        Synchronize extra context from a worksheet named 'Rules' in a spreadsheet.

        This method retrieves column values from the worksheet and converts them into a dictionary.
        The resulting dictionary is stored as extra context in the instance variable self._extra_context.
        """
        wks = self._sheet.worksheet_by_title('Rules')
        column_values = wks.get_values_batch(["A2:B1000"])
        self._extra_context = self._convert_to_dict(column_values[0])
        
    def _convert_to_dict(self, lst) -> dict:
        result = {}
        for item in lst:
            words, value = item
            words = words.split(', ')
            for word in words:
                result[word] = value
        return result
    
    def _write_to_whoosh(self, x):
        writer = self.ix.writer()
        content = f"number:{x[0]}; модель: {x[2]} ; категория: {x[3]} ; продукт: {x[4]} ; цена: {x[8]} ;  описание: {x[5]} ; пол: {x[10]} ; возраст: {x[11]} особенности: {x[12]}"
        writer.add_document(title=x[0], content=content, path=x[1], in_stocks=int(x[6])+int(x[7]))
    
    def _add_products(self, products: list):
        for row in products:
            self._write_to_whoosh(row)
    
    def clear_db(self) -> None:
        """
        Clear the Whoosh database by deleting all documents.

        This method opens a writer for the index (`self.ix`) and deletes all documents
        by performing a delete by query using the query "*:*" to match all documents.
        """
        with self.ix.writer() as writer:
            query = QueryParser("content", self.ix.schema).parse("*:*")
            writer.delete_by_query(query)

    def _create_schema(self) -> None:
        schema = Schema(
            title=TEXT(stored=True), 
            content=TEXT(stored=True), 
            path=ID(stored=True), 
            in_stocks=NUMERIC(stored=True, sortable=True)
        )
        self.ix = create_in(self.whoosh_schema_path, schema)