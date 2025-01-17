# Memory Module Documentation

In the AutoGRAMS framework, chatbots act like continually running programs, which means that the program's memory represents a memory of a conversation with a user. This section documents the key classes, functions, and patterns used in AutoGRAMS memory management. the main class that represents a memory of a specific instance of the program (conversation) is `MemoryObject`. Instances of memory_object have a `memory_dict` attribute that represents the entire state of the chatbots program, allowing you to load and save the exact state of autograms chatbots in a way that can be serialized to the disk. This enables you to easily switch between users that are active in conversations--you load the program memory for that user, continue executing the instance of the program for that user's conversation, and then save the memory when you pause or give a reply.





## Understanding Globals

- **Module-Level Globals**: Typically constants or system-wide resources, shared by all users. These are not managed by the memory object since they are not user specific. and are reinitialized every time you reload the module in python. You can define these as you normally would in python. After the Autogram class is initialized, module globals are serialized so they can't accidentally be changed in an interaction with a specific user.


- **User-Specific Globals**: Tied to a specific user’s memory object, so each user’s conversation state remains isolated.  
  - Initialized via **`init_user_globals`**.  
  - Accessed through a **`UserGlobals`** instance.

## Thread Safety

AutoGRAMS relies on context vars storage to ensure each thread has the correct **`MemoryObject`**. In multi-user or multi-thread scenarios, each user’s memory context is separate and does not overwrite other users’ states. 

---

## `use_memory(memory_object)`

A context manager for setting the memory in context vars storage within a `with` block. It ensures that the specified `memory_object` is active for the duration of the block and reset afterward.

### **Usage Example**

```python
with use_memory(some_memory_object):
    result = chatbot()
```

- **Where** `chatbot` is an AutoGRAMS function decorated with `@autograms_function`.  
- **Purpose**: Temporarily set the memory context for the thread, so any calls to `get_memory()` within the block return `some_memory_object`.

---

## `get_memory()`

Retrieves the current memory object from thread-local storage.

- **Returns**:  
  - A `SerializableMemory` (or subclass) instance if active in this thread.  
  - `None` if no memory context is set.

This function is widely used within AutoGRAMS functions (`@autograms_function`) to retrieve and manipulate the current conversation and stack state.

---

## `MemoryObject`

The main memory class for managing chatbot applications, extending `SerializableMemory` with:

- **Chatbot-Specific Functionality**: Tracking conversation turns, stack frames, etc.  
- **Serialization**: Enough data to recreate the state after giving/replying.

### **`__init__(...)`**

Initializes a `MemoryObject`.

- **Parameters**:  
  - `config` (object): Configuration object (e.g., `AutogramConfig`) for memory.  
  - `root_function` (function, optional): Root function for this memory context.  
  - `memory_dict` (dict, optional): Initial dictionary for storing memory-related data.

### **`add_user_reply(user_reply)`**

Logs a user’s reply in the conversation. This typically happens automatically if you pass a `user_reply` argument to `autogram.reply` or `autogram.apply`.

- **Parameters**:  
  - `user_reply` (str): The user’s latest reply or message.

### **`serialize(serialization_type)`**

Serializes the memory object for storage or transmission.

- **Parameters**:  
  - `serialization_type` (str): The serialization mode, such as `"full"`, `"partial"`, or `"json"`.
- **Returns**: `str`  
  A serialized representation of this memory.

### **`save(file_name, serialization_type)`**

Saves the memory object to disk.

- **Parameters**:  
  - `file_name` (str): Filename/path for storing the memory.  
  - `serialization_type` (str): Mode of serialization, e.g., `"full"`, `"partial"`, `"json"`.

---

## `SimpleMemory`

A lightweight memory class for managing prompts in simpler chatbot scenarios, without full serialization logic.

### **`__init__(...)`**

Creates a `SimpleMemory` instance:

- **Parameters**:  
  - `config` (object): Configuration object.  
  - `memory_dict` (dict, optional): Optional initial dictionary for memory.

### **`add_user_reply(user_reply)`**

Logs a user’s reply in this simple memory context.

- **Parameters**:  
  - `user_reply` (str): The user’s message.

---

## `init_user_globals()`

Initializes a **user-specific globals dictionary** for the current Python module, ensuring each module can only create one set of user globals:

- **Usage**:
  ```python
  user_globals = init_user_globals()
  user_globals["my_variable"] = 42
  ```
- **Thread/Memory Link**:  
  By using `UserGlobals`, any changes to `user_globals[...]` become tied to the user’s memory context (the current `MemoryObject`).  
- **Error Conditions**:  
  - Throws an exception if user globals were already initialized in this module. This prevents accidental re-initialization.

### **Behavior and Rationale**

- **Module-Specific**:  
  `init_user_globals()` inspects the calling module, creates a unique ID, and ensures only one `UserGlobals` instance per module.  
- **User-Specific**:  
  Values in `UserGlobals` are stored under the current user’s memory context. If a different user’s memory is set (via `use_memory`), they see a different dictionary.

---

## `UserGlobals`

A special dictionary-like container for user-specific globals, ensuring each user’s memory remains isolated. If the memory is `None`, it falls back to a local `init_dict`.


### **Implementation Details**

- **Thread/Memory Linking**:
  - Internally, `UserGlobals` calls `get_memory()` to find the active `MemoryObject` in this thread.  

- **Isolation**:
  - Each user (thread with a distinct memory) sees a different dictionary under `memory.memory_dict['user_globals']`.

---

### Example: Using `UserGlobals`

Below is a typical usage pattern:

```python


user_globals = init_user_globals()

# This initializes user_globals['name'] to None for all new users
user_globals["name"] = None


@autograms_function()
def chatbot():
  
    reply("Hi, can you tell me your name?")

    if yes_or_no("did the user provide their name?"):
      #note that this will only update the name for the active memory object, allowing it to be a user/instance specific variable
      user_globals["name"] =thought_silent("Write down the user's name and nothing else") 

```

- **Explanation**:  
  - `init_user_globals()` returns a `UserGlobals` instance, storing data in the user’s memory.  

---

## Additional Notes

- **`create_module_id(module_globals)`**: A helper function that generates a unique module ID from the file path or name, used internally by `init_user_globals()`.
- **Thread Safety**:  
  - Each user’s memory is separate via `use_memory(...)`, so concurrent calls in different threads do not overlap user-specific globals.  
  - If no memory is set, `UserGlobals` uses a local `init_dict`.

---

## Summary

- **`init_user_globals()`**: Initializes the user-specific global dictionary once per module, throwing an error if re-initialized.  
- **`UserGlobals`**: A dictionary-like interface for storing and retrieving **user-specific** variables, tied to the current memory context.  
- **Isolation**: Ensures each user’s data is kept separate and persists only within their memory scope.  
- **Integration**: Works seamlessly with `use_memory(...)` and `@autograms_function` to maintain consistent state across multi-user or single-user applications.

