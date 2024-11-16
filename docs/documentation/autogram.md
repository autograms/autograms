# Autogram Class Documentation

The `Autogram` class provides a high-level interface for managing chatbot interactions using the Autograms system. It wraps around the root `AutogramsFunction` and handles memory management, serialization, and interaction logic.

## Class: `Autogram`
`located in autograms.autogram.Autogram

### Description

This class acts as a wrapper around the root AutogramsFunction, handling memory management, serialization, and interaction logic for chatbot responses.

### Methods

---

### `__init__(root_function=None, autogram_config=None, api_keys={})`

**Description:**  
Initializes the Autogram object with a root function and configuration.

**Parameters:**  
- `root_function (AutogramsFunction)`: The root function defining the chatbot behavior.  
- `autogram_config (AutogramConfig)`: Configuration object for the Autogram.  
- `api_keys (dict)`: Dictionary of API keys. Optionally includes `"load_from_env"` to load keys from environment variables.

---
### `reply(user_reply="", memory_object=None, memory_dict=None, test_mode=False, **kwargs)`

**Description:**  
Generates a chatbot reply based on user input and memory.

**Parameters:**  
- `user_reply (str)`: The user's input message.  
- `memory_object (MemoryObject, optional)`: Memory object to use for the reply.  
- `memory_dict (dict, optional)`: Serialized memory to initialize a new memory object.  
- `test_mode (bool)`: If `True`, enables test mode for the memory object.  
- `**kwargs`: Additional arguments passed to the root function.

**Returns:**  
- `tuple`: A reply message and the updated memory object.

---

### `use_memory(memory_object=None, memory_dict=None)`

**Description:**  
Sets and manages memory for chatbot sessions, ensuring proper cleanup.

**Parameters:**  
- `memory_object (MemoryObject or SerializableMemory)`: The memory object to use.  
- `memory_dict (dict)`: Dictionary containing serialized memory state.

**Yields:**  
- `memory_object`: The active memory object for the session.

---

### `add_user_reply(user_reply=None)`

**Description:**  
Adds a user reply to the current memory.

**Parameters:**  
- `user_reply (str)`: The user's reply to be added to memory.

**Raises:**  
- `Exception`: If no memory is set.

---

### `deserialize(data, serialization_type="partial")`

**Description:**  
Deserializes memory from a given data string.

**Parameters:**  
- `data (str)`: Serialized memory data.  
- `serialization_type (str)`: Type of serialization (`"partial"`, `"full"`, or `"json"`).

**Returns:**  
- `MemoryObject`: Deserialized memory object.

---

### `load(file_path, serialization_type="partial")`

**Description:**  
Loads memory from a file.

**Parameters:**  
- `file_path (str)`: Path to the file containing serialized memory.  
- `serialization_type (str)`: Type of serialization (`"partial"`, `"full"`, or `"json"`).

**Returns:**  
- `MemoryObject`: Loaded memory object.

---

### `save(file, memory_object=None, serialization_type="partial")`

**Description:**  
Saves the current memory state to a file.

**Parameters:**  
- `file (str)`: Path to the file where memory should be saved.  
- `memory_object (MemoryObject, optional)`: Memory object to save. Defaults to current memory.  
- `serialization_type (str)`: Type of serialization (`"partial"`, `"full"`, or `"json"`).

---

### `serialize(memory_object=None, serialization_type="partial")`

**Description:**  
Serializes the current memory state to a string.

**Parameters:**  
- `memory_object (MemoryObject, optional)`: Memory object to serialize. Defaults to current memory.  
- `serialization_type (str)`: Type of serialization (`"partial"`, `"full"`, or `"json"`).

**Returns:**  
- `str`: Serialized memory data.

---

