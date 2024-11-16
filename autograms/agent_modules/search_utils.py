import numpy as np

class SimpleIndex:
    def __init__(self):
        self.texts = []
        self.vectors = np.array([]).reshape(0, 0)
        self.category_dict=dict()

    def add(self, vector,text,category):
        """
        Add a single text and its corresponding vector to the storage.
        
        :param text: Text string to be stored.
        :param vector: Vector corresponding to the text.
        """
        vector = np.array(vector)
        if self.vectors.size == 0:
            self.vectors = vector.reshape(1, -1)
        else:
            self.vectors = np.vstack([self.vectors, vector])
        self.texts.append(text)
        if category in self.category_dict:
            self.category_dict[category].append(len(self.texts)-1)
        else:
            self.category_dict[category]=[len(self.texts)-1]



        
    def search(self, query_vector, n=5,chron=True):
        """
        Search for the top n closest vectors to the query vector using cosine similarity.
        
        :param query_vector: Vector to search for.
        :param n: Number of top results to return.
        :return: List of tuples (text, similarity) where similarity is the cosine similarity.
        """

        query_vector = np.array(query_vector)
        # Normalize query vector
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            raise ValueError("Query vector norm is zero.")
        query_vector /= query_norm
        
        # Normalize stored vectors
        norms = np.linalg.norm(self.vectors, axis=1)
        norms[norms == 0] = 1  # Prevent division by zero
        normalized_vectors = self.vectors / norms[:, np.newaxis]
        
        # Compute cosine similarities
        similarities = np.dot(normalized_vectors, query_vector)
        
        # Get indices of the top n similarities
        top_n_indices = np.argsort(-similarities)[:n]

        if chron:

            top_n_indices = list(sorted(top_n_indices))


        
        # Return the top n texts and their similarities
        top_n_texts = [self.texts[i] for i in top_n_indices]
        return top_n_texts
    
    def get_category(self, category,last_n=10):
        if category in self.category_dict:
            indices = self.category_dict[category]
            texts = [self.texts[i] for i in indices]
            return texts[last_n:]
        else:
            return None
