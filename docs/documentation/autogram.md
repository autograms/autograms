# Autogram Class Documentation

The `Autogram` class provides a high-level interface for managing chatbot interactions using the Autograms system. It wraps around the root `AutogramsFunction` and handles memory management, serialization, and interaction logic.
# Autogram Class Documentation

The `Autogram` class provides a high-level interface for managing chatbot interactions using the Autograms system. It wraps around the root `AutogramsFunction` and handles memory management, serialization, and interaction logic.

## Class: `Autogram`
Located in `autograms.functional.Autogram`.

### Description

This class acts as a wrapper around the root AutogramsFunction, enabling stateful chatbot management through memory handling, serialization, API integration, and reply generation. It provides a streamlined interface for building conversational agents with dynamic control flows.

### Methods

---

#### `__init__(root_function=None, autogram_config=None, api_keys=None, global_reload_type="persistent_only", test_mode=False)`

**Description:**  
Initializes the Autogram object with a root function, configuration, and API keys.

**Parameters:**  
- `root_function (AutogramsFunction, optional)`: The root function defining the chatbot behavior.
- `autogram_config (AutogramConfig, optional)`: Configuration object for the Autogram.
- `api_keys (dict, optional)`: Dictionary of API keys, with an optional `"load_from_env"` to load keys from environment variables.
- `global_reload_type (str, optional)`: Determines how globals are reloaded. Options:
  - `"persistent_only"`: Restores globals defined with `persistent_globals`.
  - `"full"`: Reloads the parent module of the root function with every call to `use_memory()`.
- `test_mode (bool, optional)`: Enables test mode for automatic, mock responses without calling APIs.

---

#### `use_memory(memory_object=None, memory_dict=None)`

**Description:**  
Sets and manages memory for chatbot sessions or replies, ensuring proper cleanup.

**Parameters:**  
- `memory_object (MemoryObject or SerializableMemory, optional)`: The memory object to use. Defaults to creating a new memory object.
- `memory_dict (dict, optional)`: Dictionary containing serialized memory state.

**Yields:**  
- `memory_object`: The active memory object for the session.

---

#### `use_config()`

**Description:**  
Temporarily sets a simple memory configuration for isolated use. Used for testing or lightweight interactions.

**Yields:**  
- `SimpleMemory`: An isolated memory object based on the current configuration.

---

#### `reply(user_reply="", memory_object=None, memory_dict=None, **kwargs)`

**Description:**  
Generates a chatbot reply based on user input and memory.

**Parameters:**  
- `user_reply (str)`: The user's input message.
- `memory_object (MemoryObject, optional)`: Memory object to use for the reply.
- `memory_dict (dict, optional)`: Serialized memory to initialize a new memory object.
- `**kwargs`: Additional arguments passed to the root function.

**Returns:**  
- `tuple`: A reply message and the updated memory object.

---

#### `add_user_reply(user_reply=None)`

**Description:**  
Adds a user reply to the current memory.

**Parameters:**  
- `user_reply (str)`: The user's reply to be added to memory.

**Raises:**  
- `Exception`: If no memory is set.

---

#### `deserialize(data, serialization_type="partial")`

**Description:**  
Deserializes memory from a given data string.

**Parameters:**  
- `data (str)`: Serialized memory data.
- `serialization_type (str)`: Type of serialization:
  - `"partial"`
  - `"full"`
  - `"json"` (not implemented)

**Returns:**  
- `MemoryObject`: Deserialized memory object.

---

#### `load(file_path, serialization_type="partial")`

**Description:**  
Loads memory from a file.

**Parameters:**  
- `file_path (str)`: Path to the file containing serialized memory.
- `serialization_type (str)`: Type of serialization:
  - `"partial"`
  - `"full"`
  - `"json"` (not implemented)

**Returns:**  
- `MemoryObject`: Loaded memory object.

---

#### `save(file, memory_object=None, serialization_type="partial")`

**Description:**  
Saves the current memory state to a file.

**Parameters:**  
- `file (str)`: Path to the file where memory should be saved.
- `memory_object (MemoryObject, optional)`: Memory object to save. Defaults to the current memory.
- `serialization_type (str)`: Type of serialization:
  - `"partial"`
  - `"full"`
  - `"json"` (not implemented).

---

#### `serialize(memory_object=None, serialization_type="partial")`

**Description:**  
Serializes the current memory state to a string.

**Parameters:**  
- `memory_object (MemoryObject, optional)`: Memory object to serialize. Defaults to the current memory.
- `serialization_type (str)`: Type of serialization:
  - `"partial"`
  - `"full"`
  - `"json"` (not implemented).

**Returns:**  
- `str`: Serialized memory data.
