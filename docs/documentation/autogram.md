# Autogram Class Documentation

The `Autogram` class provides a high-level interface for managing chatbot interactions using the Autograms system. It wraps around the root `AutogramsFunction` and it's respective module, and handles memory management, serialization, and interaction logic.

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
Generates a chatbot reply based on user input and memory. It automatically sets the user reply and manages the memory scope, and calls the root function. It also makes sure that (non-user-specific) globals in the module don't change by reloading them from a serialized state. 

**Parameters:**  
- `user_reply (str)`: The user's input message.
- `memory_object (MemoryObject, optional)`: Memory object to use for the reply.
- `memory_dict (dict, optional)`: Serialized memory to initialize a new memory object.
- `**kwargs`: Additional arguments passed to the root function.

**Returns:**  
- `tuple`: A reply message and the updated memory object.

---


#### `apply(self,user_reply=None,memory_object=None,memory_dict=None,func=None,**kwargs)`

**Description:**  
Like reply it is an entry point into the chatbot, but it is general. It still has similar behavior to reply() by default, but it can be used to call other functions besides the root functions, including @autograms_external(). It also gives a more general AutogramReturn object which can include a reply, but can also include other data, or function returns if the called function returns normally without a reply. Uses cases include chatbots that need to return additional (and potentially multi-modal) outputs, or as an entry point to functions that modify the memory of the chatbot externally. 

**Parameters:**  
- `user_reply (str)`: The user's input message.
- `memory_object (MemoryObject, optional)`: Memory object to use for the reply.
- `memory_dict (dict, optional)`: Serialized memory to initialize a new memory object.
- `func (AutogramsFunction,AutogramsExternal, or (normal python) function)` function to be called, defaults to `root_function` of autogram.
- `**kwargs`: arguments passed to the called function

**Returns:**  
- `result`: An `AutogramsReturn` object (`autograms.program_control.AutogramReturn`), which includes fields
   --`reply` - either the reply to user or None if the function returned normally with out a reply
   --`data` - any additional data that was sent back. For instance if the model is programed to reply but also send back another variable such as an image or other information. 
   --`func_return` - the returned value of the function if it returned normally, or None if it returned with a reply.


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

#### `load(file_path)`

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

#### `save(file, memory_object=None)`

**Description:**  
Saves the current memory state to a file.

**Parameters:**  
- `file (str)`: Path to the file where memory should be saved.
- `memory_object (MemoryObject, optional)`: Memory object to save. Defaults to the current memory.

---

#### `serialize(memory_object=None, serialization_type="partial")`

**Description:**  
Serializes the current memory state to a string.

**Parameters:**  
- `memory_object (MemoryObject, optional)`: Memory object to serialize. Defaults to the current memory.

**Returns:**  
- `str`: Serialized memory data.
