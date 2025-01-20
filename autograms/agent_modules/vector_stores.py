
import numpy as np


try:
    import faiss
    faiss_available=True
except:
    faiss_available=False



import numpy as np
from ..functional import get_batch_embeddings

class AutogramsIndex:
    def __init__(self,**kwargs):
        pass


        #

class AutoIndex(AutogramsIndex):
    def __init__(self, index_library="auto", **kwargs):
        super().__init__()
        
        if index_library=="auto":
            if faiss_available:
                index_library="faiss"
            else:
                index_library="numpy"
        if index_library=="faiss":
            self.wrapped_index = FAISSIndex(**kwargs)
        elif index_library=="numpy":
            self.wrapped_index = NumpyIndex(**kwargs)
        else:
            raise Exception(f"invalid index library '{index_library}'")



    def __getattr__(self, name):
        """
        Delegate attribute access to the underlying index.
        """
        return getattr(self.index, name)
    @classmethod
    def from_texts(cls, docs, index_library="auto", return_wrapped=True, **kwargs):
        """
        Create an AutoIndex instance and initialize it with documents.
        :param docs: List of strings or dictionaries (with 'text' and optional 'metadata').
        :param index_library: 'auto', 'faiss', or 'numpy'. Determines which index library to use.
        :param return_wrapped: If True, return the wrapped index directly.
        :param kwargs: Additional arguments for the index initialization.
        :return: Initialized AutoIndex or wrapped index instance.
        """
        instance = cls(index_library=index_library, **kwargs)
        instance.wrapped_index.add_texts(docs)

        if return_wrapped:
            return instance.wrapped_index
        return instance

class FAISSIndex(AutogramsIndex):
    def __init__(self, index_type="flat", nlist=None, m=None, nbits=None, ef_construction=None, **embedding_kwargs):
        """
        Initialize the wrapper without requiring embedding_dim upfront.
        :param index_type: Type of FAISS index ("flat", "ivf", "pq", "hnsw", "ivfpq").
        :param nlist: Number of clusters for IVF-based indexes.
        :param m: Number of subquantizers for PQ-based indexes.
        :param nbits: Number of bits for PQ-based indexes.
        :param ef_construction: Construction parameter for HNSW index.
        :param embedding_kwargs: Additional parameters for embedding generation.
        """
        super().__init__()

        self.index_type = index_type
        self.embedding_dim = None  # Determined dynamically
        self.index = None  # Delayed initialization
        self.docs = []  # Store documents (each doc includes text and metadata)
        self.embeddings = []  # Cache embeddings for delayed index initialization
        self.nlist = nlist
        self.m = m
        self.nbits = nbits
        self.ef_construction = ef_construction
        self.embedding_kwargs = embedding_kwargs  # Embedding-specific settings

    def _initialize_index(self):
        """
        Initialize the FAISS index based on the specified type and add cached embeddings.
        """
        if self.index is not None:
            raise RuntimeError("Index is already initialized.")
        if self.embedding_dim is None:
            raise RuntimeError("Embedding dimension is unknown. Add texts first to determine embedding size.")

        # Intelligent default hyperparameters
        n = len(self.embeddings)
        if self.nlist is None and n > 0:
            self.nlist = max(10, int(pow(n, 1/3)))  # Default: cube root of the number of documents

        if self.index_type == "flat":
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        elif self.index_type == "ivf":
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, self.nlist)
        elif self.index_type == "pq":
            self.m = self.m or 4
            self.nbits = self.nbits or 8
            self.index = faiss.IndexPQ(self.embedding_dim, self.m, self.nbits)
        elif self.index_type == "ivfpq":
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self.m = self.m or 8
            self.nbits = self.nbits or 8
            self.index = faiss.IndexIVFPQ(quantizer, self.embedding_dim, self.nlist, self.m, self.nbits)
        elif self.index_type == "hnsw":
            ef_construction = self.ef_construction or 40
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, ef_construction)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")

        # Train the index if needed
        if isinstance(self.index, faiss.IndexIVF) and not self.index.is_trained:
            embeddings_array = np.array(self.embeddings, dtype="float32")
            self.index.train(embeddings_array)

        # Add cached embeddings to the index
        embeddings_array = np.array(self.embeddings, dtype="float32")
        self.index.add(embeddings_array)

    def add_texts(self, docs, init_after_add=True):
        """
        Add documents to the wrapper and generate embeddings using Autograms.
        :param docs: List of texts or dicts (each dict must have 'text' and optional 'metadata').
        :param init_after_add: Whether to initialize the index after adding documents.
        """
        # Handle both string and dict inputs
        for doc in docs:
            if isinstance(doc, str):
                self.docs.append({"text": doc, "metadata": {}})
            elif isinstance(doc, dict) and "text" in doc:
                self.docs.append({"text": doc["text"], "metadata": doc.get("metadata", {})})
            else:
                raise ValueError("Each document must be a string or a dictionary with a 'text' field.")

        # Generate embeddings
        new_texts = [doc["text"] for doc in self.docs[len(self.embeddings):]]
        new_embeddings = get_batch_embeddings(new_texts, **self.embedding_kwargs)

        # Set embedding dimension dynamically
        if self.embedding_dim is None:
            self.embedding_dim = len(new_embeddings[0])

        self.embeddings.extend(new_embeddings)

        if init_after_add and self.index is None:
            self._initialize_index()

    def similarity_search(self, query_text, k=5):
        """
        Perform similarity search on the FAISS index for a given text.
        :param query_text: Input query text.
        :param k: Number of nearest neighbors to return.
        :return: List of dicts with 'text', 'metadata', and 'distance'.
        """
        if self.index is None:
            raise RuntimeError("Index is not initialized. Add texts and initialize the index first.")

        # Generate embedding for the query text
        query_embedding = get_batch_embeddings([query_text], **self.embedding_kwargs)[0]
        return self.similarity_search_vector(query_embedding, k)

    def similarity_search_vector(self, query_embedding, k):
        """
        Perform similarity search using a precomputed query embedding.
        :param query_embedding: The embedding of the query.
        :param k: Number of nearest neighbors to return.
        :return: List of dicts with 'text', 'metadata', and 'distance'.
        """
        query_array = np.array([query_embedding], dtype="float32")
        distances, indices = self.index.search(query_array, k)

        # Convert results to a list of dictionaries
        results = [
            {
                "text": self.docs[idx]["text"],
                "metadata": self.docs[idx]["metadata"],
                "distance": distances[0][i],
            }
            for i, idx in enumerate(indices[0]) if idx != -1
        ]
        return results

    def save_index(self, filepath):
        """Save the FAISS index to a file."""
        if self.index is None:
            raise RuntimeError("Index is not initialized.")
        faiss.write_index(self.index, filepath)

    def load_index(self, filepath):
        """Load a FAISS index from a file."""
        self.index = faiss.read_index(filepath)

    def reset_index(self):
        """Clear the FAISS index and reset texts and embeddings."""
        self.index = None
        self.docs = []
        self.embeddings = []
        self.embedding_dim = None

    #for serialization -- should work without this but faiss.serialize_index is likely more robust
    def __getstate__(self):


        state = self.__dict__.copy()


        if self.index is not None:
            state["index"] = faiss.serialize_index(self.index)

        return state
    
    #for deserialization -- should work without this but faiss.deserialize_index is likely more robust
    def __setstate__(self, state):

        self.__dict__.update(state)
        if self.index is not None:
            self.index = faiss.deserialize_index(self.index)

    @classmethod
    def from_texts(cls, texts, index_type="flat", nlist=None, m=None, nbits=None, ef_construction=None, **embedding_kwargs):
        """
        Create an AdvancedFAISSWrapper instance and initialize it with texts.
        :param texts: List of texts to index.
        :param index_type: Type of FAISS index ("flat", "ivf", "pq", "hnsw", "ivfpq").
        :param nlist: Number of clusters for IVF-based indexes.
        :param m: Number of subquantizers for PQ-based indexes.
        :param nbits: Number of bits for PQ-based indexes.
        :param ef_construction: Construction parameter for HNSW index.
        :param embedding_kwargs: Additional parameters for embedding generation.
        :return: Initialized AdvancedFAISSWrapper instance.
        """
        wrapper = cls(index_type=index_type, nlist=nlist, m=m, nbits=nbits, ef_construction=ef_construction, **embedding_kwargs)
        wrapper.add_texts(texts, init_after_add=True)
        return wrapper
    
class NumpyIndex(AutogramsIndex):
    def __init__(self, **embedding_kwargs):
        """
        Initialize the NumpyIndex.
        :param embedding_kwargs: Additional parameters for embedding generation.
        """
        super().__init__()
        self.texts = []  # Store documents as dictionaries with text and metadata
        self.embeddings = []  # Store the embeddings
        self.embedding_dim = None  # Set dynamically after adding texts
        self.embedding_kwargs = embedding_kwargs  # Embedding-specific settings

    @classmethod
    def from_texts(cls, docs, **embedding_kwargs):
        """
        Create a NumpyIndex instance and initialize it with documents.
        :param docs: List of strings or dictionaries (with 'text' and optional 'metadata').
        :param embedding_kwargs: Additional parameters for embedding generation.
        :return: Initialized NumpyIndex instance.
        """
        index = cls(**embedding_kwargs)
        index.add_texts(docs)
        return index

    def add_texts(self, docs):
        """
        Add documents to the index.
        :param docs: List of strings or dictionaries (with 'text' and optional 'metadata').
        """
        for doc in docs:
            if isinstance(doc, str):
                self.texts.append({"text": doc, "metadata": {}})
            elif isinstance(doc, dict) and "text" in doc:
                self.texts.append({"text": doc["text"], "metadata": doc.get("metadata", {})})
            else:
                raise ValueError("Each document must be a string or a dictionary with a 'text' field.")

        # Generate embeddings for new texts
        new_texts = [doc["text"] for doc in self.texts[len(self.embeddings):]]
        new_embeddings = get_batch_embeddings(new_texts, **self.embedding_kwargs)

        # Set embedding dimension dynamically
        if self.embedding_dim is None:
            self.embedding_dim = len(new_embeddings[0])

        # Store the embeddings
        self.embeddings.extend(new_embeddings)

    def similarity_search(self, query_text, k=5, chron=True):
        """
        Perform a similarity search on the index for a given query text.
        :param query_text: Input query text.
        :param k: Number of top results to return.
        :param chron: Whether to return results in chronological order.
        :return: List of dictionaries with 'text', 'metadata', and 'distance'.
        """
        if not self.embeddings:
            raise RuntimeError("Index is empty. Add texts before performing a search.")

        # Generate the query embedding
        query_embedding = get_batch_embeddings([query_text], **self.embedding_kwargs)[0]
        return self.similarity_search_vector(query_embedding, k, chron)

    def similarity_search_vector(self, query_vector, k):
        """
        Perform similarity search using a precomputed query vector.
        :param query_vector: The embedding of the query.
        :param k: Number of top results to return.
        :return: List of dictionaries with 'text', 'metadata', and 'distance'.
        """
        # Compute L2 distances between query vector and stored embeddings
        query_vector = np.array(query_vector, dtype="float32")
        embeddings_array = np.array(self.embeddings, dtype="float32")

        # Calculate L2 distance (Euclidean distance)
        distances = np.linalg.norm(embeddings_array - query_vector, axis=1)

        # Get indices of the top k distances
        top_k_indices = np.argsort(distances)[:k]


        # Return results as a list of dictionaries
        results = [
            {
                "text": self.texts[i]["text"],
                "metadata": self.texts[i]["metadata"],
                "distance": distances[i],
            }
            for i in top_k_indices
        ]
        return results

    def reset_index(self):
        """Clear the index."""
        self.texts = []
        self.embeddings = []
        self.embedding_dim = None
