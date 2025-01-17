

### Embedding Functions
Embedding functions generate vector representations of text, which is most often used for retrieval and memory within the chatbot.

#### **get_single_embedding(text, `**kwargs`)**
`autograms.functional.get_single_embedding`
Fetches a single embedding for the given text.

- **Parameters**:
  - `text` (str): The input text to generate an embedding for.
  - `model_type` (str, default='openai'): The type of model to use for embedding.

- **Returns**:
  - `list[float]`: A vector representation of the input text.

#### **get_batch_embedding(texts,`**kwargs`)**
`autograms.functional.get_batch_embedding`
Fetches embeddings for a batch of texts.

- **Parameters**:
  - `texts` (list[str]): A list of input texts.
  - `model_type` (str, default='openai'): The type of model to use for embeddings.

- **Returns**:
  - `list[list[float]]`: A list of vector representations for each input text.