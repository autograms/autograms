# Memory Module Documentation

This section provides documentation and usage examples for key memory management components in the Autograms framework. Memory in autograms represents the state of the stack, global variables, and conversation turns. The MemoryObjects contain enough information to recreate the stack trace of a series of calls to @autograms_functions, and this mechanism is used to allow the program to continue after giving and receiving a reply.  

---

## `use_memory`

Context manager for setting memory in thread-local storage. It ensures that memory is properly set for the duration of a block and cleaned up afterward.

### Usage Example

```
with use_memory(memory_object):
    result = chatbot()
```

Where `chatbot` is an Autograms function decorated with `@autograms_function`.

---

## `get_memory`

Retrieves the current memory object from thread-local storage.

- **Returns**: `SerializableMemory` or `None`  
  The memory object if set, or `None` if no memory is active.

---

## `set_persistent_globals`

Context manager for defining persistent globals. These variables will persist across memory reloads, making them ideal for storing universal state.

### Usage Example

```
# Assures that memories_of_user variable will be reloaded instead of redefined if changed
with set_persistent_globals():
    memories_of_user = []
```

---

## `MemoryObject`

The main memory class for managing chatbot applications. Extends `SerializableMemory` with chatbot-specific functionality, including turn management and serialization.

### `__init__`

Initializes a `MemoryObject`.

- **Parameters**:
  - `config` (object): Configuration object for memory.
  - `root_function` (function, optional): Root function for the memory context.
  - `memory_dict` (dict, optional): Initial memory dictionary.

### `add_user_reply`

Logs a user's reply in the conversation.

- **Parameters**:
  - `user_reply` (str): The user's reply.

### `serialize`

Serializes the memory object for storage or transmission.

- **Parameters**:
  - `serialization_type` (str): Type of serialization (`"full"`, `"partial"`, or `"json"`).

- **Returns**: `str`  
  Serialized representation of the memory.

### `save`

Saves the memory object to a file.

- **Parameters**:
  - `file_name` (str): Name of the file to save.
  - `serialization_type` (str): Type of serialization (`"full"`, `"partial"`, or `"json"`).

---

## `SimpleMemory`

A lightweight memory class for managing chatbot prompts without serialization.

### `__init__`

Initializes a `SimpleMemory`.

- **Parameters**:
  - `config` (object): Configuration object for memory.
  - `memory_dict` (dict, optional): Initial memory dictionary.

### `add_user_reply`

Logs a user's reply in the conversation.

- **Parameters**:
  - `user_reply` (str): The user's reply.
