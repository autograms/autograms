# Utility Functions Documentation

This section documents utility functions in `autograms.functional` that provide additional functionality for code handling, execution, and parallel processing.

---

### **extract_code(input_string, code_type='python')**
`autograms.functional.extract_code`

**Description:**  
Extracts and concatenates code blocks of a specified type (e.g., Python, JavaScript) from the input string.

**Parameters:**  
- `input_string (str)`: The input string containing text and code blocks.  
- `code_type (str)`: The type of code to extract (e.g., `'python'`, `'javascript'`). Defaults to `'python'`.

**Returns:**  
- `str`: The concatenated code from all specified code blocks, separated by newlines.

---

### **execute_code(code, command="firejail --noprofile --quiet --read-only=/home --read-only=/usr python3", timeout=60, code_suffix=".py")**
`autograms.functional.execute_code`

**Description:**  
Executes code in a sandboxed environment using a specified command, such as Firejail.

**Parameters:**  
- `code (str)`: The code to execute.  
- `command (str)`: The command to execute the code, wrapped in a sandbox. Defaults to Firejail.  
- `timeout (int)`: Maximum execution time in seconds before timing out. Defaults to `60`.  
- `code_suffix (str)`: File extension for the temporary code file. Defaults to `".py"`.

**Returns:**  
- `tuple`: A tuple containing:
  - `message (str)`: Output messages, including `stdout`, `stderr`, or timeout messages.  
  - `success (bool)`: `True` if execution completed successfully, `False` otherwise.

---

### **parallel_wrapper(function, arg_list, mem_list=None, with_autograms_memory=True)**
`autograms.functional.parallel_wrapper`

**Description:**  
Runs a function with arguments in parallel using multiple processes. It initializes thread-local memory for each process and returns results along with the final thread-local state.

**Parameters:**  
- `function (callable)`: The function to execute in parallel.  
- `arg_list (list)`: A list of argument dictionaries for each function call.  
- `mem_list (list, optional)`: A list of serialized memory objects for each task. Must match the length of `arg_list` if provided. Defaults to `None`.  
- `with_autograms_memory (bool)`: If `True`, thread-local memory is shared with the parallel processes. Defaults to `True`.

**Returns:**  
- `list`: A list of function results.

**Raises:**  
- `ValueError`: If `mem_list` is provided but its length does not match `arg_list`.  
- `Exception`: If an error occurs during parallel execution.
