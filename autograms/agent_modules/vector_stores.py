
import numpy as np
from collections import OrderedDict,defaultdict

try:
    import faiss
    faiss_available=True
except:
    faiss_available=False



import numpy as np
from ..functional import get_batch_embeddings

class Index:
    def __init__(self,**kwargs):
        pass


        #

class AutoIndex(Index):
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

class FAISSIndex(Index):
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
    
class NumpyIndex(Index):
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

    def similarity_search(self, query_text, k=5):
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
        return self.similarity_search_vector(query_embedding, k)

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
    
    def similarity_search_restricted(self, query_text, k=5,indices=None):
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
        query_vector = get_batch_embeddings([query_text], **self.embedding_kwargs)[0]

        # Compute L2 distances between query vector and stored embeddings
        query_vector = np.array(query_vector, dtype="float32")
        embeddings_array = np.array(self.embeddings, dtype="float32")

        embeddings_array=embeddings_array[indices]

        # Calculate L2 distance (Euclidean distance)
        distances = np.linalg.norm(embeddings_array - query_vector, axis=1)

        # Get indices of the top k distances
        top_k_indices = np.argsort(distances)[:k]
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



from typing import List, Dict, Any,Union
# from .base_index import Index
# from .embedding_utils import get_batch_embeddings


class FieldIndex:
    """
    A dynamic Numpy-based index that:
      - Assigns stable doc IDs
      - Tracks embeddings for similarity search
      - Allows add, remove, replace
      - Also tracks certain metadata fields in a dictionary of sets (field_maps),
        letting you quickly retrieve all doc_ids for a particular field-value pair.
      - If a tracked field's value is a list, we treat the doc as belonging to
        each item in that list.
    """

    def __init__(self, tracked_fields=None, **embedding_kwargs):
        """
        :param tracked_fields: list of metadata field names we want to track 
               for restricted searching, e.g. ["section", "tags"].
        :param embedding_kwargs: additional arguments for get_batch_embeddings, etc.
        """
        if tracked_fields is None:
            tracked_fields = []
        self.tracked_fields = tracked_fields

        # For each field in tracked_fields, we keep field_maps[field][value] = set(doc_ids).
        # If a doc has "metadata[field] = value", doc_id is in that set.
        # If value is a list, doc_id goes into each item in that list.
        self.field_maps: Dict[str, Dict[Any, Set[int]]] = {}
        for f in tracked_fields:
            self.field_maps[f] = defaultdict(set)

        self.texts: List[Dict[str, Any]] = []      # each entry: {"text": ..., "metadata": {...}}
        self.embeddings: List[np.ndarray] = []     # each entry: numpy array for the doc
        self.embedding_dim = None
        self.embedding_kwargs = embedding_kwargs

        # doc ID management
        self.doc_id_to_pos: Dict[int, int] = {}    # doc_id -> index in texts/embeddings
        self.pos_to_doc_id: List[int] = []         # index -> doc_id
        self.next_id = 0

    # ----------------------------------------------------------------
    #  Core indexing operations
    # ----------------------------------------------------------------
    def add_texts(self, docs: List[Union[str, Dict[str, Any]]]):
        """
        Add one or more documents to the index.
        :param docs: list of (string or dict with 'text', 'metadata')
        :return: list of newly assigned doc_ids in order.
        """
        new_doc_strs = []
        new_doc_metas = []

        for doc in docs:
            if isinstance(doc, str):
                text = doc
                meta = {}
            elif isinstance(doc, dict) and 'text' in doc:
                text = doc['text']
                meta = doc.get('metadata', {})
            else:
                raise ValueError("Each doc must be a string or dict with 'text' field.")

            new_doc_strs.append(text)
            new_doc_metas.append(meta)

        # Embed them
        new_embs = get_batch_embeddings(new_doc_strs, **self.embedding_kwargs)
        if not new_embs:
            return []

        if self.embedding_dim is None:
            self.embedding_dim = len(new_embs[0])

        assigned_ids = []
        for i, emb in enumerate(new_embs):
            doc_id = self.next_id
            self.next_id += 1

            pos = len(self.texts)
      
            self.texts.append({"text": new_doc_strs[i], "metadata": new_doc_metas[i]})
          
            self.embeddings.append(np.array(emb, dtype="float32"))

            self.doc_id_to_pos[doc_id] = pos
            self.pos_to_doc_id.append(doc_id)

            # Update field_maps
            self._add_to_field_maps(doc_id, new_doc_metas[i])

            assigned_ids.append(doc_id)

        return assigned_ids

    def remove(self, doc_id: int):
        """
        Swap-and-pop removal to keep arrays compact. Also updates field_maps.
        """
        if doc_id not in self.doc_id_to_pos:
            return

        pos = self.doc_id_to_pos[doc_id]
        last_pos = len(self.texts) - 1

        # remove from field maps first
        old_meta = self.texts[pos]["metadata"]
        self._remove_from_field_maps(doc_id, old_meta)

        if pos != last_pos:
            # swap
            self.texts[pos], self.texts[last_pos] = self.texts[last_pos], self.texts[pos]
            self.embeddings[pos], self.embeddings[last_pos] = (
                self.embeddings[last_pos],
                self.embeddings[pos],
            )
            swapped_id = self.pos_to_doc_id[last_pos]
            self.pos_to_doc_id[pos] = swapped_id
            self.pos_to_doc_id[last_pos] = doc_id
            self.doc_id_to_pos[swapped_id] = pos

        # pop
        self.texts.pop()
        self.embeddings.pop()
        self.pos_to_doc_id.pop()
        del self.doc_id_to_pos[doc_id]

    def replace(self, doc_id: int, new_doc: Union[str, Dict[str, Any]]):
        """
        Replace doc text & metadata, re-embed, update field_maps.
        """
        if doc_id not in self.doc_id_to_pos:
            return

        pos = self.doc_id_to_pos[doc_id]
        if isinstance(new_doc, str):
            new_text = new_doc
            new_meta = {}
        elif isinstance(new_doc, dict) and "text" in new_doc:
            new_text = new_doc["text"]
            new_meta = new_doc.get("metadata", {})
        else:
            raise ValueError("new_doc must be string or dict with 'text' field.")

        # re-embed
        new_emb = get_batch_embeddings([new_text], **self.embedding_kwargs)[0]
        if self.embedding_dim and len(new_emb) != self.embedding_dim:
            raise RuntimeError("Embedding dimension mismatch in replace.")

        # remove from old metadata sets
        old_meta = self.texts[pos]["metadata"]
        self._remove_from_field_maps(doc_id, old_meta)

        # update
        self.texts[pos] = {"text": new_text, "metadata": new_meta}
        self.embeddings[pos] = np.array(new_emb, dtype="float32")

        # add to new metadata sets
        self._add_to_field_maps(doc_id, new_meta)

    def get_document(self, doc_id: int):
        if doc_id not in self.doc_id_to_pos:
            return None
        pos = self.doc_id_to_pos[doc_id]
        return self.texts[pos]

    # ----------------------------------------------------------------
    #  Core similarity search
    # ----------------------------------------------------------------
    def similarity_search(self, query_text: str, k=5):
        if not self.embeddings:
            return []
        query_vec = get_batch_embeddings([query_text], **self.embedding_kwargs)[0]
        return self.similarity_search_vector(query_vec, k)

    def similarity_search_vector(self, query_vector: np.ndarray, k=5):
        arr = np.array(self.embeddings, dtype="float32")
        dists = np.linalg.norm(arr - query_vector, axis=1)
        top_k = np.argsort(dists)[:k]
        results = []
        for i in top_k:
            doc_id = self.pos_to_doc_id[i]
            results.append({
                "doc_id": doc_id,
                "text": self.texts[i]["text"],
                "metadata": self.texts[i]["metadata"],
                "distance": dists[i],
            })
        return results

    # ----------------------------------------------------------------
    #  Subset search
    # ----------------------------------------------------------------
    def similarity_search_subset(self, query_text: str, doc_ids: List[int], k=5):
        if not doc_ids:
            return []
        query_vec = get_batch_embeddings([query_text], **self.embedding_kwargs)[0]
        return self.similarity_search_vector_subset(query_vec, doc_ids, k)

    def similarity_search_vector_subset(self, query_vector: np.ndarray, doc_ids: List[int], k=5):
        valid_positions = []
        for d_id in doc_ids:
            if d_id in self.doc_id_to_pos:
                valid_positions.append(self.doc_id_to_pos[d_id])
        if not valid_positions:
            return []
        arr_subset = np.array([self.embeddings[pos] for pos in valid_positions], dtype="float32")
        dists = np.linalg.norm(arr_subset - query_vector, axis=1)

        top_k_local = np.argsort(dists)[:k]
        results = []
        for local_i in top_k_local:
            pos = valid_positions[local_i]
            doc_id = self.pos_to_doc_id[pos]
            results.append({
                "doc_id": doc_id,
                "text": self.texts[pos]["text"],
                "metadata": self.texts[pos]["metadata"],
                "distance": dists[local_i]
            })
        return results

    # ----------------------------------------------------------------
    #  Field-based search
    # ----------------------------------------------------------------
    def similarity_search_by_metadata(self, query_text: str, field: str, value: Any, k=5):
        """
        Retrieve doc_ids from field_maps[field][value] (if tracked), then do subset search.
        If the field or the value is unknown, returns empty list.
        """
        if field not in self.field_maps:
            return []
        doc_ids_set = self.field_maps[field].get(value, set())
        if not doc_ids_set:
            return []
        return self.similarity_search_subset(query_text, list(doc_ids_set), k)

    # or if you want direct vector input
    def similarity_search_vector_by_metadata(self, query_vector: np.ndarray, field: str, value: Any, k=5):
        if field not in self.field_maps:
            return []
        doc_ids_set = self.field_maps[field].get(value, set())
        if not doc_ids_set:
            return []
        return self.similarity_search_vector_subset(query_vector, list(doc_ids_set), k)

    # ----------------------------------------------------------------
    #  Internal helpers for field_maps
    # ----------------------------------------------------------------
    def _add_to_field_maps(self, doc_id: int, metadata: dict):
        """
        For each tracked field in self.tracked_fields, if it exists in metadata:
          - If the value is a list, add doc_id to each item in that list
          - Otherwise, treat it as a single value
        """
        for f in self.tracked_fields:
            if f not in metadata:
                continue
            val = metadata[f]
            if isinstance(val, list):
                # for each item in the list
                for v in val:
                    self.field_maps[f][v].add(doc_id)
            else:
                # single value
                self.field_maps[f][val].add(doc_id)

    def _remove_from_field_maps(self, doc_id: int, metadata: dict):
        """
        Removes doc_id from the set for each relevant field+value.
        Also checks if the value is a list or single item.
        """
        for f in self.tracked_fields:
            if f not in metadata:
                continue
            val = metadata[f]
            if isinstance(val, list):
                for v in val:
                    self.field_maps[f][v].discard(doc_id)
            else:
                self.field_maps[f][val].discard(doc_id)
class DynamicNumpyIndex:
    """
    A Numpy-based dynamic index that assigns stable doc IDs,
    supports add/remove/replace, and can search among subsets of doc IDs.
    """

    def __init__(self, **embedding_kwargs):
        self.texts: List[Dict[str, Any]] = []     # each entry: { 'text': str, 'metadata': dict }
        self.embeddings: List[np.ndarray] = []    # each entry: embedding vector
        self.embedding_dim = None
        self.embedding_kwargs = embedding_kwargs

        self.doc_id_to_pos: Dict[int, int] = {}   # doc_id -> index in self.texts/embeddings
        self.pos_to_doc_id: List[int] = []        # index -> doc_id
        self.next_id = 0

    @classmethod
    def from_texts(cls, docs, **embedding_kwargs):
        index = cls(**embedding_kwargs)
        index.add_texts(docs)
        return index

    def add_texts(self, docs):
        """
        Add documents to the index.
        :param docs: List of strings or dicts {'text': str, 'metadata': dict}.
        :return: list of newly assigned doc_ids
        """
        new_doc_strs = []
        new_doc_metas = []
        for doc in docs:
            if isinstance(doc, str):
                text = doc
                meta = {}
            elif isinstance(doc, dict) and 'text' in doc:
                text = doc['text']
                meta = doc.get('metadata', {})
            else:
                raise ValueError("Document must be a string or dict with 'text' field.")

            new_doc_strs.append(text)
            new_doc_metas.append(meta)

        # Embed in batch
        new_embs = get_batch_embeddings(new_doc_strs, **self.embedding_kwargs)
        if not new_embs:
            return []

        if self.embedding_dim is None:
            self.embedding_dim = len(new_embs[0])

        assigned_ids = []
        for i, emb in enumerate(new_embs):
            doc_id = self.next_id
            self.next_id += 1

            pos = len(self.texts)
            self.texts.append({"text": new_doc_strs[i], "metadata": new_doc_metas[i]})
            self.embeddings.append(np.array(emb, dtype="float32"))

            self.doc_id_to_pos[doc_id] = pos
            self.pos_to_doc_id.append(doc_id)

            assigned_ids.append(doc_id)

        return assigned_ids

    def remove(self, doc_id):
        """
        Swap-and-pop removal to keep arrays compact.
        """
        if doc_id not in self.doc_id_to_pos:
            return

        pos = self.doc_id_to_pos[doc_id]
        last_pos = len(self.texts) - 1

        if pos != last_pos:
            # swap
            self.texts[pos], self.texts[last_pos] = self.texts[last_pos], self.texts[pos]
            self.embeddings[pos], self.embeddings[last_pos] = (
                self.embeddings[last_pos],
                self.embeddings[pos],
            )
            swapped_id = self.pos_to_doc_id[last_pos]
            self.pos_to_doc_id[pos] = swapped_id
            self.pos_to_doc_id[last_pos] = doc_id
            self.doc_id_to_pos[swapped_id] = pos

        # pop
        self.texts.pop()
        self.embeddings.pop()
        self.pos_to_doc_id.pop()
        del self.doc_id_to_pos[doc_id]

    def replace(self, doc_id, new_doc):
        """
        Replace doc text & metadata, re-embed.
        """
        if doc_id not in self.doc_id_to_pos:
            return

        pos = self.doc_id_to_pos[doc_id]
        if isinstance(new_doc, str):
            new_text = new_doc
            new_meta = {}
        elif isinstance(new_doc, dict) and "text" in new_doc:
            new_text = new_doc["text"]
            new_meta = new_doc.get("metadata", {})
        else:
            raise ValueError("new_doc must be string or dict with 'text' field.")

        new_emb = get_batch_embeddings([new_text], **self.embedding_kwargs)[0]
        if self.embedding_dim and len(new_emb) != self.embedding_dim:
            raise RuntimeError("Embedding dim mismatch in replace.")

        # update
        self.texts[pos] = {"text": new_text, "metadata": new_meta}
        self.embeddings[pos] = np.array(new_emb, dtype="float32")

    def get_document(self, doc_id):
        if doc_id not in self.doc_id_to_pos:
            return None
        pos = self.doc_id_to_pos[doc_id]
        return self.texts[pos]

    def similarity_search(self, query_text, k=5):
        if not self.embeddings:
            return []
        query_emb = get_batch_embeddings([query_text], **self.embedding_kwargs)[0]
        return self.similarity_search_vector(query_emb, k)

    def similarity_search_vector(self, query_vector, k=5):
        arr = np.array(self.embeddings, dtype="float32")
        q_vec = np.array(query_vector, dtype="float32")
        dists = np.linalg.norm(arr - q_vec, axis=1)
        top_k = np.argsort(dists)[:k]
        results = []
        for i in top_k:
            doc_id = self.pos_to_doc_id[i]
            results.append({
                "doc_id": doc_id,
                "text": self.texts[i]["text"],
                "metadata": self.texts[i]["metadata"],
                "distance": dists[i],
            })
        return results

    # ----------------------------------------------------------------
    # NEW: restricted search
    # ----------------------------------------------------------------
    def similarity_search_subset(self, query_text, doc_ids, k=5):
        """
        Search only among the given doc_ids.
        """
        if not doc_ids:
            return []
        query_emb = get_batch_embeddings([query_text], **self.embedding_kwargs)[0]
        return self.similarity_search_vector_subset(query_emb, doc_ids, k)

    def similarity_search_vector_subset(self, query_vector, doc_ids, k=5):
        """
        Same as similarity_search_vector, but restricted to doc_ids.
        """
        valid_positions = []
        for d_id in doc_ids:
            if d_id in self.doc_id_to_pos:
                valid_positions.append(self.doc_id_to_pos[d_id])
        if not valid_positions:
            return []

        arr_subset = np.array([self.embeddings[pos] for pos in valid_positions], dtype="float32")
        q_vec = np.array(query_vector, dtype="float32")
        dists = np.linalg.norm(arr_subset - q_vec, axis=1)

        # top k in subset
        top_k_local = np.argsort(dists)[:k]
        results = []
        for local_i in top_k_local:
            pos = valid_positions[local_i]
            doc_id = self.pos_to_doc_id[pos]
            results.append({
                "doc_id": doc_id,
                "text": self.texts[pos]["text"],
                "metadata": self.texts[pos]["metadata"],
                "distance": dists[local_i]
            })
        return results

    def _embed_query(self, text):
        """
        Helper if you need direct access to embedding for external calls.
        """
        e = get_batch_embeddings([text], **self.embedding_kwargs)
        return e[0] if e else None


class TwoLevelCabinet:
    """
    A "filing cabinet" that organizes docs by a 'section' metadata field,
    providing:
      - doc-level search (via doc_index)
      - section-level search (via section_index)

    Each doc is stored in doc_index with a doc_id.
    Each section is stored in section_index as a single "doc" representing
      the concatenation (or some aggregator) of all doc texts in that section.
    The 'metadata_section_field' param is the name of the metadata field used
      to identify the doc's section (e.g. 'folder', 'cabinet_section').

    Naive approach:
      - whenever we add or remove a doc, we re-generate the entire text for that doc's section
        and re-embed it in the section_index.
      - for big sections, consider incremental or partial re-embedding.

    Usage:
      cabinet = TwoLevelCabinet(
         doc_index=DynamicNumpyIndex(...),
         section_index=DynamicNumpyIndex(...),
         metadata_section_field="folder"
      )

      # Add doc
      doc_id = cabinet.add_document("Hello world", {"folder": "greetings"})

      # doc-level search
      doc_results = cabinet.search_docs("hello")

      # section-level search
      section_results = cabinet.search_sections("general greetings")
    """

    def __init__(self, doc_index, section_index, metadata_section_field="folder"):
        self.doc_index = doc_index
        self.section_index = section_index
        self.metadata_section_field = metadata_section_field

        # keep an in-memory map of section_name -> set of doc_ids
        self.section_map = {}  # e.g. { "sectionA": set([doc_id1, doc_id2, ...]) }

    def add_document(self, text, metadata=None):
        if metadata is None:
            metadata = {}
        # Insert doc into doc_index
        doc_obj = {"text": text, "metadata": metadata}
        new_ids = self.doc_index.add_texts([doc_obj])
        if not new_ids:
            return -1
        doc_id = new_ids[0]

        # Identify the section from the doc's metadata
        section_name = metadata.get(self.metadata_section_field, None)
        if section_name:
            self._add_doc_to_section(doc_id, section_name)

        return doc_id

    def remove_document(self, doc_id):
        # find which section it belongs to
        doc_data = self.doc_index.get_document(doc_id)
        if not doc_data:
            return  # doc doesn't exist
        section_name = doc_data["metadata"].get(self.metadata_section_field, None)
        if section_name and section_name in self.section_map:
            if doc_id in self.section_map[section_name]:
                self.section_map[section_name].remove(doc_id)
                # re-embed that section
                self._update_section_embedding(section_name)

        # remove doc from doc_index
        self.doc_index.remove(doc_id)

    def replace_document(self, doc_id, new_text, new_metadata=None):
        """
        Re-embed doc in doc_index, possibly reassign its section if changed.
        """
        if new_metadata is None:
            new_metadata = {}
        old_data = self.doc_index.get_document(doc_id)
        if not old_data:
            return
        old_section = old_data["metadata"].get(self.metadata_section_field, None)

        # do the replace
        replaced_obj = {"text": new_text, "metadata": new_metadata}
        self.doc_index.replace(doc_id, replaced_obj)

        # check new section
        new_section = new_metadata.get(self.metadata_section_field, None)
        if new_section != old_section:
            # remove from old
            if old_section and doc_id in self.section_map.get(old_section, set()):
                self.section_map[old_section].remove(doc_id)
                self._update_section_embedding(old_section)

            # add to new
            if new_section:
                self._add_doc_to_section(doc_id, new_section)

    # -------------------------------------------------------------------
    # Doc-level search
    # -------------------------------------------------------------------
    def search_docs(self, query, k=5, restricted_doc_ids=None):
        """
        Search individual docs. If restricted_doc_ids is provided,
        we do a subset search. Otherwise, we do a full search.
        """
        if restricted_doc_ids is not None:
            return self.doc_index.similarity_search_subset(query, restricted_doc_ids, k)
        else:
            return self.doc_index.similarity_search(query, k)

    # -------------------------------------------------------------------
    # Section-level search
    # -------------------------------------------------------------------
    def search_sections(self, query, k=5, restricted_sections=None):
        """
        Search among entire sections. If restricted_sections is provided,
        we do a subset search among only those sections' embeddings.
        """
        if not restricted_sections:
            return self.section_index.similarity_search(query, k)
        else:
            # gather doc_ids for those sections in section_index
            # in naive approach, each section is a single doc_id in section_index
            # so we can do subset search. But we must map section_name -> doc_id
            doc_ids = []
            for s in restricted_sections:
                doc_id = self._get_section_doc_id(s)
                if doc_id is not None:
                    doc_ids.append(doc_id)

            return self.section_index.similarity_search_subset(query, doc_ids, k)

    # -------------------------------------------------------------------
    # Private / Utility
    # -------------------------------------------------------------------
    def _add_doc_to_section(self, doc_id, section_name):
        """
        Add doc_id to section map, re-embed the entire section if needed.
        """
        if section_name not in self.section_map:
            self.section_map[section_name] = set()
        self.section_map[section_name].add(doc_id)
        self._update_section_embedding(section_name)

    def _update_section_embedding(self, section_name):
        """
        Rebuild the entire text for a section from doc_index data,
        store it in the section_index by a single doc_id representing that section.
        For simplicity, we do:  doc_id = hash(section_name) or something stable.
        Or we keep a map section->section_doc_id. We'll do the latter.
        """
        # gather all docs
        doc_ids = list(self.section_map.get(section_name, []))
        # build combined text
        all_texts = []
        for d_id in doc_ids:
            data = self.doc_index.get_document(d_id)
            if data:
                all_texts.append(data["text"])
        combined_text = "\n".join(all_texts)

        # find or create the doc_id for that section in the section_index
        section_doc_id = self._get_section_doc_id(section_name)
        if section_doc_id is None:
            # create
            # we can store metadata with e.g. { "section_name": section_name }
            section_obj = {
                "text": combined_text,
                "metadata": {"_type": "section", "section_name": section_name}
            }
            new_ids = self.section_index.add_texts([section_obj])
            if new_ids:
                s_id = new_ids[0]
                self._set_section_doc_id(section_name, s_id)
        else:
            # replace
            new_doc = {
                "text": combined_text,
                "metadata": {"_type": "section", "section_name": section_name}
            }
            self.section_index.replace(section_doc_id, new_doc)

    def _get_section_doc_id(self, section_name) -> int:
        """
        Return an integer doc_id representing that section in section_index,
        or None if not found. We'll keep an internal map:
          self.section_name_to_doc_id: dict
        """
        if not hasattr(self, 'section_name_to_doc_id'):
            self.section_name_to_doc_id = {}
        return self.section_name_to_doc_id.get(section_name, None)

    def _set_section_doc_id(self, section_name, doc_id):
        if not hasattr(self, 'section_name_to_doc_id'):
            self.section_name_to_doc_id = {}
        self.section_name_to_doc_id[section_name] = doc_id



class TaggedIndex(Index):
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
        self.tags = dict()
        self.tag_descriptions = dict()

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
    def add_tag_description(tag,description):
        self.tag_description = description


    def add_texts(self, docs):
        """
        Add documents to the index.
        :param docs: List of strings or dictionaries (with 'text' and optional 'metadata').
        """
        for doc in docs:
            self.texts.append({"text": doc["text"], "tags":doc['tags'],"metadata": doc.get("metadata", {})})
            for tag in doc['tags']:
                if doc['tags'] in self.tags[doc['tag']]:
                    self.tags[doc['tag']].append(self.texts[-1])

            else:
                self.tags[doc['tag']] = [self.texts[-1]]

        # Generate embeddings for new texts
        new_texts = [doc["text"] for doc in self.texts[len(self.embeddings):]]
        new_embeddings = get_batch_embeddings(new_texts, **self.embedding_kwargs)

        # Set embedding dimension dynamically
        if self.embedding_dim is None:
            self.embedding_dim = len(new_embeddings[0])

        # Store the embeddings
        self.embeddings.extend(new_embeddings)

    def similarity_search(self, query_text, k=5):
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
        return self.similarity_search_vector(query_embedding, k)

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
                "tag": self.texts[i]["tag"],
                "metadata": self.texts[i]["metadata"],
                "distance": distances[i],
            }
            for i in top_k_indices
        ]
        return results
    
    def similarity_search_restricted(self, query_text, k=5,indices=None):
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
        query_vector = get_batch_embeddings([query_text], **self.embedding_kwargs)[0]

        # Compute L2 distances between query vector and stored embeddings
        query_vector = np.array(query_vector, dtype="float32")
        embeddings_array = np.array(self.embeddings, dtype="float32")

        embeddings_array=embeddings_array[indices]

        # Calculate L2 distance (Euclidean distance)
        distances = np.linalg.norm(embeddings_array - query_vector, axis=1)

        # Get indices of the top k distances
        top_k_indices = np.argsort(distances)[:k]
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

class ContextualIndex:
    def __init__(self):
        """
        Initialize the ContextualIndex.
        """
        self.contextual_data = {}  # Map unit names to lists of contextual subunits
        self.vector_index = NumpyIndex()  # Vector index for contextual subunits


    def add_context(self, unit_name, text):
        """
        Add a contextual subunit for a specific memory unit.
        :param unit_name: Name of the memory unit.
        :param text: Text for the new contextual subunit.
        """
        if unit_name not in self.contextual_data:
            self.contextual_data[unit_name] = []

        self.contextual_data[unit_name].append(text)

        # Add to vector index
        self.vector_index.add_texts({
            "text": text,
            "metadata": {"unit_name": unit_name}
        })

    def get_context(self, unit):
        """
        Retrieve all contextual subunits for a specific memory unit.
        :param unit: The MemoryUnit to retrieve context for.
        :return: List of ContextualSubunits.
        """
        return self.contextual_data.get(unit.name, [])

    def search_contexts(self, query, k=5):
        """
        Perform a vector-based search over all contextual subunits.
        :param query: Query text for the search.
        :param k: Number of top results to return.
        :return: List of matching contextual subunits with metadata.
        """
        results = self.vector_index.similarity_search(query, k)
        return [
            {
                "unit_name": result["metadata"]["unit_name"],
                "distance": result["distance"],
                "text": result["text"]
            }
            for result in results
        ]

class MemoryKey:
    def __init__(self, text, unit, category=None):
        self.text = text
        self.unit = unit
        self.category = category
        self.name = self.unit.name
        self.id = self.unit.index.init_memory_key(self)
    def get_text(self):
        return self.text

    def get_unit(self):
        return self.unit

    def get_id(self):
        return self.id

    def __str__(self):
        return self.text



class MemoryUnit:
    def __init__(self,  name, index, text, description=None, data=None,memory_keys=None):
        

        
        self.data = data
   
        self.index = index
        self.name=name

        self.memory_keys = []  

        self.text = MemoryKey(text, self, category="text")
     
       
        self.description = MemoryKey(description, self, category="description") if description else None
        if not memory_keys is None:
            for unit in memory_keys:
                if type(unit)==str:
                    self._add_key(unit)
                else:
                    self._add_key(unit['text'],unit['category'])

    def get_name(self):
        return self.name
    
    def get_description(self):
        """Return the main description of the memory unit."""
        return self.description.text if self.description else None

    def get_text(self):
        """Return the main text content of the memory unit."""
        return self.text.text

    def get_data(self):
        """Return general or complex data."""
        return self.data


    def _add_key(self,text,category):
     
        self.memory_keys.append(MemoryKey(text,self,category))
    def _get_keys(self):
        return self.memory_keys


    def __str__(self):
        return self.text


class MultiKeyIndex:
    def __init__(self):
        """Initialize the MemoryIndex."""
        self.units = dict()  # Store all MemoryUnits
        self.memory_name_index=dict() # store key ids by memory name

        self.memory_keys = OrderedDict()  # Flat list of MemorySubunit references for indexing
   
     
    
        self.category_index = OrderedDict() 


        self.vector_index = NumpyIndex()  

        #total units and subunits ever in existence
        self.num_memory_keys=0
        self.num_units=0
        self.static=False

    def set_static(self):
        """Mark the index as static."""
        self.static = True



    def add_unit_from_dict(self, unit):
        """Add a unit to the index, preventing changes if static."""
        if self.static:
            raise RuntimeError("Cannot modify a static index. Static indexes are meant to be constant after initialization so that they can be shared between all users.")
    
        self.num_units+=1
        name=unit['name']

        new_unit = MemoryUnit(index=self,**unit)

        if name in self.units:
            print(f"Warning, overwriting unit with name {name}")
        self.units[name]=new_unit

    def add_unit(self, text, name=None, description=None, data=None,core_subunits=None):
        if self.static:
            raise RuntimeError("Cannot modify a static index. Static indexes are meant to be constant after initialization so that they can be shared between all users.")

        new_unit = MemoryUnit(name,text,self,name=name, description=description, data=data,core_subunits=core_subunits)
        self.memory_units.append(new_unit)
        if name in self.units:
            print(f"Warning, overwriting unit with name {name}")
        self.units[name]=new_unit

    def init_memory_key(self,memory_key):
        if self.static:
            raise RuntimeError("Cannot modify a static index. Static indexes are meant to be constant after initialization so that they can be shared between all users.")
        new_id =self.num_memory_keys
        self.num_memory_keys+=1

        if memory_key.name in self.memory_name_index:

            self.memory_name_index[memory_key.name].append(new_id)
        else:
            self.memory_name_index[memory_key.name]=[new_id]

        if not memory_key.category is None:
            if memory_key.category in self.category_index:

                self.category_index[memory_key.category].append(new_id)
            else:
                self.category_index[memory_key.category]=[new_id]

        self.vector_index.add_texts([{"text":memory_key.get_text(),"metadata":new_id}])
  
        self.memory_keys[new_id]=memory_key
        


    @staticmethod
    def from_list(data,static=True):
        """
        Initialize a MemoryIndex from a list of dictionaries or plain texts.
        :param data: List of dictionaries or strings representing memory units.
        :return: A fully initialized MemoryIndex.
        """
        index = MultiKeyIndex()
        for unit_data in data:



            index.add_unit_from_dict(unit_data)

        if static:
            index.set_static()
        return index

        

    def search_all(self, query, k=5):
        """
        Search all memories by text query.
        :param query: The search query.
        :param k: Number of top results to return.
        :return: List of unique MemoryUnits sorted by minimum distance.
        """
        indices = list(range(len(self.memory_keys)))  # Ensure all indices are included
        raw_results = self.vector_index.similarity_search_restricted(query, k, indices)

        # Deduplicate by MemoryUnit and take the minimum distance for each
        unit_distances = {}
        for result in raw_results:
            key_id = result["metadata"]
            distance = result["distance"]
            parent_unit = self.memory_keys[key_id].get_unit()

            if parent_unit not in unit_distances or distance < unit_distances[parent_unit]:
                unit_distances[parent_unit] = distance

        # Sort results by distance
        sorted_results = sorted(unit_distances.items(), key=lambda x: x[1])

        return [{"memory_unit": unit, "distance": distance} for unit, distance in sorted_results[:k]]

    def search_filtered(self, query=None, k=5, name_prefix=None, category=None):
        """
        Search memories by category and optionally by text query.
        :param query: The search query.
        :param k: Number of top results to return.
        :param categories: List of categories to filter by (exact match).
        :param category: Subcategory to filter by.
        :return: List of unique MemoryUnits sorted by minimum distance.
        """
        # Create a mapping from subunit IDs to contiguous indices
    
        index_map = {key: idx for idx, key in enumerate(self.memory_keys.keys())}

        # Collect indices for categories and subcategories
    
        prefix_indices = set()

        if name_prefix:
            selected_memories = self.check_prefix(name_prefix)
            for key in selected_memories: 
                prefix_indices.update(self.memory_name_index.get(key, []))
        else:
            prefix_indices = list(range(len(self.memory_keys)))



        subcategory_indices = set(self.memory_keys.keys())
        if category:
            subcategory_indices.update(self.category_index.get(category, []))


        # Intersect indices
        filtered_keys = prefix_indices & subcategory_indices

        # Map to contiguous indices
        mapped_indices = [index_map[i] for i in filtered_keys if i in index_map]

        # Perform vector search if query is provided
        if query:

            raw_results = self.vector_index.similarity_search_restricted(query, k, mapped_indices)
        else:
            raw_results = [{"metadata": idx, "distance": 0} for idx in mapped_indices]

        # Deduplicate by MemoryUnit and take the minimum distance for each
        unit_distances = {}
        for result in raw_results:
            key_id = result["metadata"]
            distance = result["distance"]
            parent_unit = self.memory_keys[key_id].get_unit()

            if parent_unit not in unit_distances or distance < unit_distances[parent_unit]:
                unit_distances[parent_unit] = distance

        # Sort results by distance
        sorted_results = sorted(unit_distances.items(), key=lambda x: x[1])

        return [{"memory_unit": unit, "distance": distance} for unit, distance in sorted_results[:k]]


    def check_prefix(self, prefix):
        keys=[]
        for memory_name in self.memory_name_index.keys():
            if memory_name[:len(prefix)]==prefix:
                keys.append(memory_name)
        return keys

    # def search_by_subcategories(self, query=None, k=5, subcategories=None):
    #     """
    #     Search memories by category and optionally by text query.
    #     :param query: The search query.
    #     :param k: Number of top results to return.
    #     :param categories: List of categories to filter by (exact match).
    #     :return: List of matching MemoryUnits.
    #     """
    #     indices = []
    #     if subcategories:
    #         for category in subcategories:
    #             if category in self.keys:
    #                 indices.extend([self.memories.index(mem) for mem in self.keys[category]])
    #     else:
    #         indices = list(range(len(self.memories)))

    #     if query:
    #         return self.similarity_search_restricted(query, k, indices)
    #     return [self.memories[i] for i in indices[:k]] if k else [self.memories[i] for i in indices]


    # def get_memory_by_id(self, memory_id):
    #     """Retrieve a MemoryUnit by its unique ID."""
    #     return self.memory_units[memory_id] if 0 <= memory_id < len(self.memory_units) else None




# class MemoryIndexOrig:
#     def __init__(self):
#         """
#         Initialize the MemoryIndex.
#         """

#         self.memories = []  # Store all MemoryUnits
#         self.keys = {}  # Optional: Map categories to MemoryUnits
#         self.vector_index = NumpyIndex()  # Index for vector-based search


#     def add_memory(self, memory_unit):
#         """
#         Add a MemoryUnit to the index.
#         :param memory_unit: The MemoryUnit to add.
#         """
#         self.memories.append(memory_unit)

#         # Add to category index
#         if memory_unit.category:
#             self.keys.setdefault(memory_unit.category, []).append(memory_unit)

#         # Add vectors to vector index
#         if memory_unit.vectors:
#             for vector in memory_unit.vectors:
#                 self.vector_index.add_texts(
#                     [{"text": memory_unit.name, "metadata": {"memory_id": id(memory_unit)}}]
#                 )

#     def remove_memory(self, memory_unit):
#         """
#         Remove a MemoryUnit from the index.
#         :param memory_unit: The MemoryUnit to remove.
#         """
#         self.memories.remove(memory_unit)

#         # Remove from category index
#         if memory_unit.category in self.keys:
#             self.keys[memory_unit.category].remove(memory_unit)

#     def similarity_search_restricted(self, query_text, k=5, indices=None):
#         """
#         Perform a similarity search on the index for a given query text.
#         :param query_text: Input query text.
#         :param k: Number of top results to return.
#         :param indices: List of indices to restrict the search to.
#         :return: List of MemoryUnits matching the query.
#         """
#         results = self.vector_index.similarity_search_restricted(query_text, k, indices)
#         return [self.get_memory_by_id(result["metadata"]["memory_id"]) for result in results]

#     def similarity_search(self, query, k=5):
#         """
#         Search memories by text query.
#         :param query: The search query.
#         :param k: Number of top results to return.
#         :return: List of top matching MemoryUnits.
#         """
#         indices = list(range(len(self.memories)))
#         return self.similarity_search_restricted(query, k, indices)

#     def similarity_search_filtered(self, query=None, k=5, categories=None,sub_categories=None):
#         """
#         Search memories by category and optionally by text query.
#         :param query: The search query.
#         :param k: Number of top results to return.
#         :param categories: List of categories to filter by (exact match).
#         :return: List of matching MemoryUnits.
#         """
#         indices_cat = []
#         if categories:
#             for category in categories:
#                 if category in self.keys:
#                     indices_cat.extend([self.memories.index(mem) for mem in self.keys[category]])
#         else:
#             indices_cat = list(range(len(self.memories)))

#         if query:
#             return self.similarity_search_restricted(query, k, indices)
#         return [self.memories[i] for i in indices[:k]] if k else [self.memories[i] for i in indices]

#     def search_by_regex(self, query_regex, query=None, k=5):
#         """
#         Search memories by regex pattern, narrowing by vector search if query is provided.
#         :param query_regex: The regex pattern to search for.
#         :param query: The text query for vector search.
#         :param k: Number of top results to return.
#         :return: List of matching MemoryUnits.
#         """
#         import re
#         pattern = re.compile(query_regex)
#         indices = [
#             i for i, mem in enumerate(self.memories)
#             if pattern.search(mem.category or "")
#         ]

#         if query:
#             return self.similarity_search_restricted(query, k, indices)
#         return [self.memories[i] for i in indices[:k]] if k else [self.memories[i] for i in indices]

#     def get_memory_by_id(self, memory_id):
#         """Retrieve a MemoryUnit by its unique ID."""
#         for mem in self.memories:
#             if id(mem) == memory_id:
#                 return mem
#         return None


# class FileChunkNode(TreeIndexNode):
#     def __init__(self, name, description=None, text=None, data=None):
#         """
#         Initialize an IndexNode.
#         :param name: Name of the node.
#         :param description: Optional description of the node.
#         :param text: Optional text content of the node.
#         :param data: Optional non-text data of the node.
#         """
        
#         pass

# class FileNode(TreeIndexNode):
#     def __init__(self, name, description=None, text=None, data=None):
#         """
#         Initialize an IndexNode.
#         :param name: Name of the node.
#         :param description: Optional description of the node.
#         :param text: Optional text content of the node.
#         :param data: Optional non-text data of the node.
#         """
        
#         pass

# class PythonCodeNode(TreeFileNode):
#     def __init__(self, name, description=None, text=None, data=None):
#         """
#         Initialize an IndexNode.
#         :param name: Name of the node.
#         :param description: Optional description of the node.
#         :param text: Optional text content of the node.
#         :param data: Optional non-text data of the node.
#         """
#         pass

# class PythonChunkNode(TreeFileChunkNode):
#     def __init__(self, name, description=None, text=None, data=None):
#         """
#         Initialize an IndexNode.
#         :param name: Name of the node.
#         :param description: Optional description of the node.
#         :param text: Optional text content of the node.
#         :param data: Optional non-text data of the node.
#         """
#         pass

# class PythonObjectNode(TreeIndexNode):
#     def __init__(self, name, description=None, text=None, data=None):
#         """
#         Initialize an IndexNode.
#         :param name: Name of the node.
#         :param description: Optional description of the node.
#         :param text: Optional text content of the node.
#         :param data: Optional non-text data of the node.
#         """
#         pass

# class DirectoryNode(TreeIndexNode):
#     def __init__(self, name, description=None, text=None, data=None):
#         """
#         Initialize an IndexNode.
#         :param name: Name of the node.
#         :param description: Optional description of the node.
#         :param text: Optional text content of the node.
#         :param data: Optional non-text data of the node.
#         """
#         pass

# class TreeIndexNode:
#     def __init__(self, name, tree, description=None, text=None, data=None):
#         """
#         Initialize an IndexNode.
#         :param name: Name of the node.
#         :param tree: Reference to the IndexTree managing this node.
#         :param description: Optional description of the node.
#         :param text: Optional text content of the node.
#         :param data: Optional non-text data of the node.
#         """
#         self.name = name
#         self.tree = tree
#         self.description = description
#         self.text = text
#         self.data = data
#         self.children = []
#         self.parent = None
#         self.id = tree.add_node(self)  # Register this node with the tree

#     # Core Methods
#     def get_path(self):
#         """Return the path of this node relative to the root."""
#         if self.parent:
#             return f"{self.parent.get_path()}/{self.name}"
#         return self.name

#     def get_description(self):
#         """Return the description of this node."""
#         return self.description

#     def get_children(self):
#         """Return the children of this node."""
#         return self.children

#     def get_parent(self):
#         """Return the parent of this node."""
#         return self.parent

#     def get_text(self):
#         """Return the text content of this node."""
#         return self.text

#     def get_data(self):
#         """Return the non-text data of this node."""
#         return self.data

#     def get_vector(self):
#         """Return the vector embedding for this node."""
#         if self.tree:
#             return self.tree.get_vector_for_node(self)
#         return None

#     # Search and Retrieval Methods
#     def search_children_by_text(self, query_vector, max_results):
#         """Search the children of this node by text using a vector query."""
#         if self.tree:
#             child_indices = [self.tree.get_node_index(child) for child in self.children]
#             return self.tree.similarity_search_restricted(query_vector, max_results, child_indices)
#         return []

#     def search_children_by_description(self, query_vector, max_results):
#         """Search the children of this node by description using a vector query."""
#         # Placeholder for description-based search if descriptions are indexed differently
#         return self.search_children_by_text(query_vector, max_results)

#     def get_full_text(self):
#         """Concatenate and return the full text of this node and its children."""
#         full_text = self.text or ""
#         for child in self.children:
#             child_text = child.get_full_text()
#             if child_text:
#                 full_text += "\n" + child_text
#         return full_text

#     # Editing and Management Methods
#     def append_child(self, child_node):
#         """Add a child node to this node."""
#         if child_node.tree and child_node.tree != self.tree:
#             raise ValueError("Child node belongs to a different tree.")
#         if not child_node.tree:
#             child_node.tree = self.tree
#             child_node.id = self.tree.add_node(child_node)
#         child_node.parent = self
#         self.children.append(child_node)

#     def remove_child(self, child_node):
#         """Remove a child node from this node."""
#         self.children.remove(child_node)
#         child_node.parent = None
#         self.tree.delete_node(child_node)

#     def delete(self):
#         """Delete this node and inform the tree to update its state."""
#         if self.parent:
#             self.parent.remove_child(self)
#         self.tree.delete_node(self)

#     def write_description(self, new_description):
#         """Update the description of this node."""
#         self.description = new_description

#     def write_text(self, new_text):
#         """Update the text content of this node."""
#         self.text = new_text

#     def write_data(self, new_data):
#         """Update the non-text data of this node."""
#         self.data = new_data

#     # Utility Methods
#     def get_depth(self):
#         """Return the depth of this node in the tree."""
#         depth = 0
#         current = self.parent
#         while current:
#             depth += 1
#             current = current.parent
#         return depth

#     def is_leaf(self):
#         """Return True if this node has no children."""
#         return len(self.children) == 0

#     def to_dict(self):
#         """Serialize this node and its children into a dictionary."""
#         return {
#             "name": self.name,
#             "description": self.description,
#             "text": self.text,
#             "data": self.data,
#             "children": [child.to_dict() for child in self.children],
#         }

# class IndexNode:
#     def __init__(self, name, description=None, text=None, data=None):
#         """
#         Initialize an IndexNode.
#         :param name: Name of the node.
#         :param description: Optional description of the node.
#         :param text: Optional text content of the node.
#         :param data: Optional non-text data of the node.
#         """
#         pass

#     # Core Methods
#     def get_path(self):
#         """Return the path of this node relative to the root."""
#         pass

#     def get_description(self):
#         """Return the description of this node."""
#         pass

#     def get_children(self):
#         """Return the children of this node."""
#         pass

#     def get_parent(self):
#         """Return the parent of this node."""
#         pass

#     def get_text(self):
#         """Return the text content of this node."""
#         pass

#     def get_data(self):
#         """Return the non-text data of this node."""
#         pass

#     def get_vector(self):
#         """Return the vector embedding for this node."""
#         pass

#     # Search and Retrieval Methods
#     def search_children_by_text(self, query_vector, max_results):
#         """Search the children of this node by text using a vector query."""
#         pass

#     def search_children_by_description(self, query_vector, max_results):
#         """Search the children of this node by description using a vector query."""
#         pass

    # def get_full_text(self):
    #     """Concatenate and return the full text of this node and its children."""
    #     pass

#     # Editing and Management Methods
#     def append_child(self, child_node):
#         """Add a child node to this node."""
#         pass

#     def remove_child(self, child_node):
#         """Remove a child node from this node."""
#         pass

#     def write_description(self, new_description):
#         """Update the description of this node."""
#         pass

#     def write_text(self, new_text):
#         """Update the text content of this node."""
#         pass

#     def write_data(self, new_data):
#         """Update the non-text data of this node."""
#         pass

#     # Utility Methods
#     def get_depth(self):
#         """Return the depth of this node in the tree."""
#         pass

#     def is_leaf(self):
#         """Return True if this node has no children."""
#         pass

#     def to_dict(self):
#         """Serialize this node and its children into a dictionary."""
#         pass


# class IndexTree:
#     def __init__(self, root_node):
#         """
#         Initialize an IndexTree.
#         :param root_node: The root node of the tree.
#         """
#         pass

#     # Initialization and Management Methods
#     def get_root(self):
#         """Return the root node of the tree."""
#         pass

#     def rebuild_index(self):
#         """Rebuild the global index from all nodes in the tree."""
#         pass

#     # Search Methods
#     def search(self, query_vector, max_results, restrict_to=None):
#         """
#         Search the tree for nodes matching the query vector.
#         :param query_vector: The vector to search for.
#         :param max_results: Maximum number of results to return.
#         :param restrict_to: Optional node or path to restrict the search.
#         """
#         pass

#     def search_by_path(self, path):
#         """Find a node by its path in the tree."""
#         pass

#     # Index Management
#     def add_to_index(self, node):
#         """Add a node's text or description to the index."""
#         pass

#     def remove_from_index(self, node):
#         """Remove a node from the index."""
#         pass

#     def update_index(self, node):
#         """Update the index for a modified node."""
#         pass

#     def get_index_size(self):
#         """Return the current size of the index."""
#         pass

#     # Editing Methods
#     def append_child(self, parent_path, child_node):
#         """Append a child node to the parent specified by parent_path."""
#         pass

#     def remove_child(self, path):
#         """Remove the node at the specified path."""
#         pass

#     # Utility Methods
#     def get_node_count(self):
#         """Return the total number of nodes in the tree."""
#         pass

#     def to_dict(self):
#         """Serialize the tree into a dictionary."""
#         pass