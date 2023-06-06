import torch
from transformers import AutoTokenizer, AutoModel
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

class BertTiny2Embedding(EmbeddingFunction):

    def __init__(self) -> None:
        self._tokenizer = AutoTokenizer.from_pretrained("cointegrated/rubert-tiny2")
        self._model = AutoModel.from_pretrained("cointegrated/rubert-tiny2")
        
    def _embed_bert_cls(self, text):
        t = self._tokenizer(text, padding=True, truncation=True, return_tensors='pt')
        with torch.no_grad():
            model_output = self._model(**{k: v.to(self._model.device) for k, v in t.items()})
        embeddings = model_output.last_hidden_state[:, 0, :]
        embeddings = torch.nn.functional.normalize(embeddings)
        return embeddings[0].cpu().numpy()
    
    def __call__(self, texts: Documents) -> Embeddings:
        return [self._embed_bert_cls(text) for text in texts]