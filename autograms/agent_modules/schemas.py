from typing import Any, Dict, List, Union,get_origin,get_args
from autograms.functional import generate_object
from autograms import use_config,AutogramConfig
import json

# class SchemaItem:
#     """Base interface for all schema items (fields or containers)."""
#     def _to_schema(self) -> Dict[str, Any]:
#         raise NotImplementedError("Subclasses must implement _to_schema.")



# class Schema(SchemaItem):
#     """
#     High-level container that wraps a nested structure
#     (dict, list, string literal, or Field).
#     """

#     def __init__(self, structure: Any):
#         """
#         structure can be:
#           - a dict (mapping -> sub-schema)
#           - a list (fixed or variable-length)
#           - a string literal (treated as an enum of size 1)
#           - a Field object (StringField, EnumField, etc.)
#         """
#         self.structure = structure

#     def to_schema(self) -> Dict[str, Any]:
#         return parse_schema(self.structure)
    

# def parse_schema(obj: Any) -> Dict[str, Any]:
#     """
#     Convert a Python object (dict, list, string literal, or Field)
#     into a JSON Schema dict. Recurses as needed.
#     """

#     # 1) If it's a string literal => treat as an enum of size 1
#     if isinstance(obj, str):
#         return {
#             "type": "string",
#             "enum": [obj]
#         }

#     # 2) If it's already a Field or SchemaItem, call its to_schema method
#     if isinstance(obj, SchemaItem):
#         return obj.to_schema()

#     # 3) If it's a dict => interpret each key => value as properties
#     if isinstance(obj, dict):
#         properties = {}
#         required_keys = []
#         for k, v in obj.items():
#             properties[k] = parse_schema(v)
#             required_keys.append(k)
#         return {
#             "type": "object",
#             "properties": properties,
#             "required": required_keys,
#             "additionalProperties": False
#         }

#     # 4) If it's a list => interpret it as a fixed-length array
#     #    (or variable-length—depending on your design).
#     #
#     # For a "variable length array" approach, see note below.
#     # For a "fixed length" approach, we generate item schemas by index.
#     if isinstance(obj, list):
#         # Let's keep it simple: "fixed length" array
#         # each element in 'obj' is a sub-schema for that index.
#         item_schemas = [parse_schema(x) for x in obj]
#         return {
#             "type": "array",
#             "items": item_schemas,
#             "minItems": len(obj),
#             "maxItems": len(obj)
#         }

#     # 5) If it's an int/float => treat as a fixed numeric literal (or handle differently).
#     if isinstance(obj, (int, float)):
#         return {
#             "type": "number",
#             "enum": [obj]
#         }

#     # 6) Otherwise, raise an error or handle more types...
#     raise TypeError(f"Unsupported type in schema: {type(obj)} -> {repr(obj)}")

# class StringField(SchemaItem):
#     """Forcing the model to generate a free-form string."""
#     def to_schema(self) -> Dict[str, Any]:
#         return {
#             "type": "string"
#         }

# class EnumField(SchemaItem):
#     """Forcing the model to pick from a fixed set of string choices."""
#     def __init__(self, choices):
#         self.choices = choices

#     def to_schema(self) -> Dict[str, Any]:
#         return {
#             "type": "string",
#             "enum": self.choices
#         }

# class ListField(SchemaItem):
#     """
#     A variable-length array whose items all follow the same sub-schema.
#     """
#     def __init__(self, sub_schema: Union[SchemaItem, dict, list, str]):
#         """
#         sub_schema can be another field, or a dict, or so on.
#         We'll parse it recursively.
#         """
#         self.sub_schema = sub_schema

#     def to_schema(self) -> Dict[str, Any]:
#         item_schema = parse_schema(self.sub_schema)
#         return {
#             "type": "array",
#             "items": item_schema
#         }
    

# class DecisionField(SchemaItem):
#     def __init__(self, question: str, branches: Dict[str, Any]):
#         self.question = question
#         self.branches = branches

#     def to_schema(self) -> Dict[str, Any]:
#         top_props = {
#             "question": parse_schema(self.question),
#             "answer": {
#                 "type": "object",
#                 "additionalProperties": False  # IMPORTANT
#             }
#         }
#         required = ["question", "answer"]

#         one_of_list = []
#         for choice, sub_schema in self.branches.items():
#             parsed_sub = parse_schema(sub_schema)
#             branch_obj = {
#                 "properties": {
#                     "answer": {
#                         "type": "object",
#                         "properties": {
#                             "decision": {
#                                 "type": "string",
#                                 "enum": [choice]
#                             }
#                         },
#                         "required": ["decision"],
#                         "additionalProperties": False
#                     }
#                 }
#             }
#             # Merge in sub_schema...
#             if parsed_sub.get("type") == "object":
#                 branch_obj["properties"]["answer"]["properties"].update(
#                     parsed_sub.get("properties", {})
#                 )
#                 branch_obj["properties"]["answer"]["required"].extend(
#                     parsed_sub.get("required", [])
#                 )
#             else:
#                 # If not an object, store it in a "result" field
#                 branch_obj["properties"]["answer"]["properties"]["result"] = parsed_sub
#                 branch_obj["properties"]["answer"]["required"].append("result")

#             one_of_list.append(branch_obj)

#         return {
#             "type": "object",
#             "properties": top_props,
#             "required": required,
#             "additionalProperties": False,
#             "OneOf": one_of_list  # use lowercase oneOf
#         }


# import json
# from typing import Any, Dict, List, Union

# ###############################################################################
# # Base Classes / Utilities
# ###############################################################################

# class SchemaItem:
#     """Base interface for all schema items (fields or containers)."""
#     def _to_schema(self) -> Dict[str, Any]:
#         raise NotImplementedError("Subclasses must implement to_schema.")


# def parse_schema(obj: Any) -> Dict[str, Any]:
#     """
#     Convert a Python object (dict, list, string literal, or Field)
#     into a JSON Schema dict. Recurses as needed.
#     """

#     # 1) If it's a string literal => treat as an enum of size 1
#     if isinstance(obj, str):
#         return {
#             "type": "string",
#             "enum": [obj]
#         }

#     # 2) If it's already a Field or SchemaItem, call its to_schema method
#     if isinstance(obj, SchemaItem):
#         return obj._to_schema()

#     # 3) If it's a dict => interpret each key => value as properties
#     if isinstance(obj, dict):
#         properties = {}
#         required_keys = []
#         for k, v in obj.items():
#             properties[k] = parse_schema(v)
#             required_keys.append(k)
#         return {
#             "type": "object",
#             "properties": properties,
#             "required": required_keys,
#             "additionalProperties": False
#         }

#     # 4) If it's a list => interpret it as a "fixed-length" array
#     if isinstance(obj, list):
#         item_schemas = [parse_schema(x) for x in obj]
#         return {
#             "type": "array",
#             "items": item_schemas,
#             "minItems": len(obj),
#             "maxItems": len(obj)
#         }

#     # 5) If it's an int/float => treat as a fixed numeric literal
#     if isinstance(obj, (int, float)):
#         return {
#             "type": "number",
#             "enum": [obj]
#         }

#     # 6) Otherwise, raise an error or handle more types...
#     raise TypeError(f"Unsupported type in schema: {type(obj)} -> {repr(obj)}")


# ###############################################################################
# # Field Classes
# ###############################################################################

# class Schema(SchemaItem):
#     """
#     High-level container that wraps a nested structure
#     (dict, list, string literal, or Field).
#     """

#     def __init__(self, structure: Any):
#         """
#         structure can be:
#           - a dict (mapping -> sub-schema)
#           - a list (fixed or variable-length)
#           - a string literal (treated as an enum of size 1)
#           - a Field object (StringField, EnumField, etc.)
#         """
#         self.structure = structure
#     def to_schema(self):

#         final_schema = {
#             "type": "json_schema",
#             "json_schema": {
#                 "name": "play_game_decision",
#                 "strict": True,
#                 "schema": self._to_schema()
#             }
#         }
#         return final_schema
#     def _to_schema(self) -> Dict[str, Any]:
#         return parse_schema(self.structure)
#     def to_schema_list(schema_obj, schema_name_prefix="parallel_part") -> List[Dict]:
#         """
#         Convert a top-level dict-based Schema into multiple partial schemas,
#         one for each top-level property.

#         Return a list of JSON-Schema dicts suitable for your guided decoding.
#         """
#         # 1) First, parse the entire schema to get the raw JSON Schema dict
#         full_parsed = schema_obj._to_schema()
#         # e.g. {
#         #   "type":"object",
#         #   "properties":{
#         #       "data": {
#         #          "type":"object",
#         #          "properties":{
#         #             "keyA": {...},
#         #             "keyB": {...}
#         #          },
#         #          "required":["keyA","keyB"],
#         #          "additionalProperties":false
#         #       }
#         #   },
#         #   "required":["data"],
#         #   "additionalProperties":false
#         # }

#         # 2) Check if the top-level is an object with "data"
#         if (full_parsed.get("type") != "object"
#             or "properties" not in full_parsed
#             or "data" not in full_parsed["properties"]):
#             raise ValueError("Expected top-level to have 'data' object for parallel split.")

#         data_obj = full_parsed["properties"]["data"]
#         if data_obj.get("type") != "object" or "properties" not in data_obj:
#             raise ValueError("'data' must be an object with properties for parallel split.")

#         # 3) We'll iterate over top-level keys in data_obj["properties"]
#         #    building partial schemas for each
#         partial_schemas = []
#         for idx, top_key in enumerate(data_obj["properties"].keys()):
#             sub_schema = data_obj["properties"][top_key]


#             partial = {
#                 "type": "object",
#                 "properties": {
#                     "data": {
#                         "type": "object",
#                         "properties": {
#                             top_key: sub_schema
#                         },
#                         "required": [top_key],
#                         "additionalProperties": False
#                     }
#                 },
#                 "required": ["data"],
#                 "additionalProperties": False
#             }

#             # Wrap it in your usual "type":"json_schema" format
#             partial_schema = {
#                 "type": "json_schema",
#                 "json_schema": {
#                     "name": f"{schema_name_prefix}_{idx}_{top_key}",
#                     "strict": True,
#                     "schema": partial
#                 }
#             }
#             partial_schemas.append(partial_schema)

#         return partial_schemas


# class StringField(SchemaItem):
#     """Forcing the model to generate a free-form string."""
#     def _to_schema(self) -> Dict[str, Any]:
#         return {
#             "type": "string"
#         }


# class EnumField(SchemaItem):
#     """Forcing the model to pick from a fixed set of string choices."""
#     def __init__(self, choices):
#         self.choices = choices

#     def _to_schema(self) -> Dict[str, Any]:
#         return {
#             "type": "string",
#             "enum": self.choices
#         }


# class ListField(SchemaItem):
#     """
#     A variable-length array whose items all follow the same sub-schema.
#     """
#     def __init__(self, sub_schema: Union[SchemaItem, dict, list, str]):
#         """
#         sub_schema can be another field, or a dict, or so on.
#         We'll parse it recursively.
#         """
#         self.sub_schema = sub_schema

#     def _to_schema(self) -> Dict[str, Any]:
#         item_schema = parse_schema(self.sub_schema)
#         return {
#             "type": "array",
#             "items": item_schema
#         }
    




# ###############################################################################
# # DecisionField that produces an object with anyOf
# ###############################################################################

# class DecisionField(SchemaItem):
#     """
#     Produces an object with an `anyOf` array of branches.
#     Each branch has properties: question, answer, result.
#     """

#     def __init__(self, question: str, branches: Dict[str, Any]):
#         """
#         question: A string literal or field (the question).
#         branches: Dict of 'answer_value' -> sub-schema for `result`.
#                   e.g. {
#                     "yes": {"reason": StringField(), "next_step": EnumField(["proceed", "hold"])},
#                     "no":  {"explanation": StringField()}
#                   }
#         """
#         self.question = question
#         self.branches = branches


#     def _to_schema(self) -> Dict[str, Any]:
#         """
#         We'll produce something like:
#         {
#           "type": "object",
#           "anyOf": [
#             {
#               "properties": {
#                 "question": {...},
#                 "answer": {"type":"string","enum":["yes"]},
#                 "result": {...sub-schema...}
#               },
#               "required": ["question","answer","result"],
#               "additionalProperties": false
#             },
#             {
#               ...
#             }
#           ],
#           "additionalProperties": false
#         }
#         """
#         branch_list = []
#         for choice, sub_schema in self.branches.items():
#             parsed_result = parse_schema(sub_schema)  # sub_schema => object for `result`

#             # Build the branch
#             branch_props = {
#                 "question": parse_schema(self.question),
#                 "answer": {
#                     "type": "string",
#                     "enum": [choice]
#                 },
#                 "result": parsed_result
#             }
#             required_keys = ["question", "answer", "result"]

#             branch_obj = {
#                 "properties": branch_props,
#                 "required": required_keys,
#                 "additionalProperties": False
#             }
#             branch_list.append(branch_obj)

#         # Return an object with anyOf for branching
#         return {
#             "type": "object",
#             "anyOf": branch_list,
#             "additionalProperties": False
#         }
    

TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    dict: "object",
    list: "array"
    # etc. if you have more types
}
def to_json_schema_type(t):
    """
    Converts a Python type or generic (like list[str]) to a JSON Schema dict.
    """
    # First handle the simple built-in types (str, int, etc.)
    TYPE_MAP = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        dict: "object",  # optional
        list: "array"     # optional
    }

    # If it's directly in TYPE_MAP, just return that

    # Otherwise, check for generics
    origin = get_origin(t)     # e.g. list[str] => list
    args   = get_args(t)       # e.g. list[str] => (str,)
    if origin == list:
        # We assume it's something like list[X]
        if len(args) == 1:
            item_schema = to_json_schema_type(args[0])
            return {
                "type": "array",
                "items": item_schema
            }
        else:
            raise Exception("must have single arg for list type")
            # fallback if list has multiple type args (rare)
            return { "type": "array" }

    # 2) Is it a literal enum? e.g. Literal["a","b","c"]
    #    Then we do {"enum":["a","b","c"]} plus "type":"string" (optional)
    if origin == Literal:
        # get_args(t) might be ("a", "b", "c")
        values = args
        # Decide if they are all strings or all ints, etc.
        if all(isinstance(v, str) for v in values):
            return {
                "enum": list(values),
                "type": "string"
            }
        elif all(isinstance(v, int) for v in values):
            return {
                "enum": list(values),
                "type": "integer"
            }
        else:
            # fallback if it's a mix
            return {
                "enum": list(values)
            }
   
    if t in TYPE_MAP:
        return {"type": TYPE_MAP[t]}

    # if origin == list:
    #     # We have list[...] => produce {"type":"array","items":...}
    #     # We assume single argument, e.g. list[str]
    #     item_schema = to_json_schema_type(args[0])  # recursively parse the item type
    #     return {"type": "array", "items": item_schema}

    # e.g. if origin == dict, handle dict[...] => produce object
    # but if you haven't decided how to do dynamic dicts, you can skip or fallback
    # or handle more complicated structures like Union, Tuple, etc.

    # Fallback if nothing matches
    return {"type": "string"}
def is_typing_generic(t):
    """Checks if 't' is e.g. list[str], dict[str,int], etc."""
    import typing
    origin = get_origin(t)
    return origin is not None
# class SchemaEnum:
#     """
#     A dynamic enumeration. 
#     'values' can be a list of strings or ints, discovered at runtime.
#     """
#     def __init__(self, values):
#         self.values = list(values)

#     def to_schema(self) -> dict:
#         """
#         Produces a JSON schema snippet:
#           - If all are strings => {"type":"string","enum":[...]}
#           - If all are ints => {"type":"integer","enum":[...]}
#           - Otherwise => {"enum":[...]} with no type
#         """
#         if all(isinstance(v, str) for v in self.values):
#             return {
#                 "type": "string",
#                 "enum": self.values
#             }
#         elif all(isinstance(v, int) for v in self.values):
#             return {
#                 "type": "integer",
#                 "enum": self.values
#             }
#         else:
#             # fallback if the set is mixed or complex
#             return {
#                 "enum": self.values
#             }
        
class SchemaList:
    """
    Represents an array field in the final JSON Schema.
    - Could store a single sub-schema (homogeneous array).
    - Or store a 'SchemaEnum' for items, or even a typed array (list[str]).
    """
    def __init__(self, item):
        """
        'item' can be:
          - a single SchemaBuilder (array of sub-objects)
          - a SchemaEnum (array of enumerated items)
          - a Python type hint like list[str] if you want
        """
        self.item = item

    def to_schema(self) -> dict:
        """
        Return {"type":"array","items": ...} appropriate for 'item'.
        """
        if isinstance(self.item, SchemaBuilder):
            return {
                "type": "array",
                "items": self.item.to_schema()
            }
        # 2) If it's a Python list => enumerated array
        elif isinstance(self.item, list):
            # Check if they're all strings or all ints
            if len(self.item) == 0:
                # An empty list => maybe produce an array with empty enum
                return {
                    "type": "array",
                    "items": {
                        "type": "string",  # fallback
                        "enum": []
                    }
                }
            elif all(isinstance(x, str) for x in self.item):
                # Array of enumerated strings
                return {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": self.item
                    }
                }
            elif all(isinstance(x, int) for x in self.item):
                # Array of enumerated integers
                return {
                    "type": "array",
                    "items": {
                        "type": "integer",
                        "enum": self.item
                    }
                }
            else:
                # Mixed or unsupported
                return {
                    "type": "array",
                    "items": {
                        "enum": self.item
                    }
                }
        else:
            # Possibly a type hint, or fallback
            # e.g. if self.item == str => array of strings
            # or do to_json_schema_type(self.item)
            from typing import get_origin, get_args
            # parse it as you see fit
            ...
            return {
                "type":"array",
                "items": {"type":"string"}
            }
class SchemaBuilder():
    def __init__(self,attributes= None):
        if attributes is None:
            self.attributes=dict()
        else:
            self.attributes=attributes
        #pass

    def add_attribute(self,name,target,overwrite=False):
        if name in self.attributes and not overwrite:
            raise Exception(f"{name} already in attributes" )
        self.attributes[name]=target
    def add_decision(self,name,question):

        self.attributes[f"{name}_question"] = question
        decision_point = BranchPoint(name)
        self.attributes[name] = decision_point
        return decision_point

    def add_child(self,name,child=None):
        if child is None:
            child = SchemaBuilder()
        self.attributes[name]=child
        return child
    def add_child_list(self, name, child=None):
        """
        Creates an array of sub-schemas (homogeneous).
        We only allow exactly one 'child' object, so the array shape is fixed.
        """
        if child is None:
            # If user didn't pass a child, create a new one
            child = SchemaBuilder()
        # We store a list with exactly one item
        self.attributes[name] = SchemaList(child)
        return child  # Return the *schema builder* so they can add fields
    # def add_enum(self, name, values, overwrite=False):
    #     """
    #     A convenience method to attach a dynamic enumerated field.
    #     """
    #     enum_field = SchemaEnum(values)
    #     return self.add_attribute(name, enum_field, overwrite=overwrite)
    def to_json_schema(self):

        final_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "play_game_decision",
                "strict": True,
                "schema": self.to_schema()
            }
        }
        return final_schema
    def to_schema(self):
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
        for key, value in self.attributes.items():
            if isinstance(value, SchemaBuilder):
                schema["properties"][key] = value.to_schema()
            elif isinstance(value, list):
                # Distinguish "list of strings" => enumerated single field
                # vs. "one-element list of sub-schema" => array of sub-objects
                if len(value) == 0:
                    # an empty list => can't be an enum or an array of sub-objects
                    # pick a fallback
                    raise Exception("can't be an empty list")
                elif all(isinstance(x, str) for x in value):
                    # This is an enumerated single field => "type":"string","enum":value
                    schema["properties"][key] = {
                        "type": "string",
                        "enum": value
                    }
                elif len(value) == 1 and isinstance(value[0], SchemaBuilder):
                    # => array of sub-objects
                    sub_schema = value[0].to_schema()
                    schema["properties"][key] = {
                        "type": "array",
                        "items": sub_schema
                    }
                else:
                    # we don't handle multiple sub-schemas or mixed contents
                    raise ValueError(
                        f"'{key}' is a list with {len(value)} elements that are not all strings, "
                        f"or not a single sub-schema. This usage is not allowed."
                    )
            elif isinstance(value, SchemaList):
                # array
                schema["properties"][key] = value.to_schema()
            # elif isinstance(value, list):
            #     # Only 1 item allowed
            #     if len(value) != 1:
            #         raise ValueError(f"List for '{key}' has {len(value)} items, but only 1 is allowed.")
            #     sub = value[0]

            #     if isinstance(sub, SchemaBuilder):
            #         schema["properties"][key] = {
            #             "type": "array",
            #             "items": sub.to_schema()
            #         }
            #     elif isinstance(sub, SchemaEnum):
            #         schema["properties"][key] = {
            #             "type": "array",
            #             "items": sub.to_schema()
            #         }
            #     else:
            #         raise TypeError(
            #             f"List for '{key}' must contain a single SchemaBuilder or SchemaEnum, got {type(sub)}"
            #         )
            elif isinstance(value, BranchPoint):
                schema["properties"][key] = value.to_schema()
            
            elif isinstance(value, type) or is_typing_generic(value):
                # Use our new function to handle built-ins or generics
                schema["properties"][key] = to_json_schema_type(value)
            else:
                # It's a literal
                schema["properties"][key] = {"enum": [value]}

        # "required": [...]
        schema["required"] = list(self.attributes.keys())

        return schema


  #  def to_schema(self):
        # schema = {
        #     "type": "object",
        #     "properties": {},
        #     "additionalProperties": False
        # }
        # for key, value in self.attributes.items():
        #     if isinstance(value, SchemaBuilder):
        #         schema["properties"][key] = value.to_schema()
        #     elif isinstance(value, BranchPoint):
        #         schema["properties"][key] = value.to_schema()
        #     elif isinstance(value, type):
        #         # Use TYPE_MAP for str->string, etc.
        #         if value in TYPE_MAP:
        #             schema["properties"][key] = {"type": TYPE_MAP[value]}
        #         else:
        #             schema["properties"][key] = {"type": "string"}
        #     else:
        #         # It's a literal
        #         schema["properties"][key] = {"enum": [value]}

        # # Add this line:
        # schema["required"] = list(self.attributes.keys())

        # return schema

    # def to_schema(self):
    #     schema = {
    #         "type": "object",
    #         "properties": {},
    #         "additionalProperties": False  # often recommended for strictness
    #     }
    #     for key, value in self.attributes.items():
    #         if isinstance(value, SchemaBuilder):
    #             schema["properties"][key] = value.to_schema()
    #         elif isinstance(value, BranchPoint):
    #             schema["properties"][key] = value.to_schema()
    #         elif isinstance(value, type):
    #             # Use TYPE_MAP instead of value.__name__
    #             if value in TYPE_MAP:
    #                 schema["properties"][key] = {"type": TYPE_MAP[value]}
    #             else:
    #                 # Fallback or error
    #                 schema["properties"][key] = {"type": "string"}  
    #         else:
    #             # It's a literal
    #             schema["properties"][key] = {"enum": [value]}
    #     return schema


class BranchPoint():
    def __init__(self,name):
        self.name=name
        self.branches=dict()


    def init_branch(self,branch):


        self.branches[branch]= SchemaBuilder()

        #self.branches[branch].add_attribute(f"{self.name}_answer",branch)
        self.branches[branch].add_attribute(f"answer",branch)
     

    def add_attribute(self,name,target,branch):
        if not(branch in self.branches):
            self.init_branch(branch)
            
        self.branches[branch].add_attribute(name,target)


    def add_decision(self,name,question,branch):

        if not(branch in self.branches):
            self.init_branch(branch)
            
        return self.branches[branch].add_decision(name,question)
        

    def add_child(self,name,branch):
        if not(branch in self.branches):
            self.init_branch(branch)
        
        return self.branches[branch].add_child(name)
    
    def to_schema(self):
        return {
            "anyOf": [
                {
                    # Merge the dictionary returned by branch.to_schema()
                    # so we do NOT nest "type":"object" again.
                    **branch.to_schema(),
                    "required": list(branch.attributes.keys())
                }
                for branch in self.branches.values()
            ]
        }

                 
    



# class DecisionField(SchemaItem):
#     """
#     A branching schema: includes a 'question' (literal or free string)
#     and multiple 'choices' -> each choice has a sub-schema.
#     """
#     def __init__(self, question: str, branches: Dict[str, Any]):
#         """
#         question: the text of the question (string literal or StringField, etc.)
#         branches: a dict mapping choice_string -> sub_schema
#                   e.g. { "yes": {"reason": StringField(), ...},
#                          "no":  {"explanation": StringField()} }
#         """
#         self.question = question
#         self.branches = branches

#     def _to_schema(self) -> Dict[str, Any]:
#         # We'll produce an object with "question" and "answer" + subfields
#         # but also a oneOf to handle branching.
#         # 
#         # For simplicity, let's define:
#         # {
#         #   "question": <the question literal>,
#         #   "answer": {
#         #       "decision": "yes" or "no",
#         #       ...sub-schema...
#         #   }
#         # }

#         top_props = {
#             "question": parse_schema(self.question),  # might be literal or field
#             "answer": {
#                 "type": "object"
#             }
#         }
#         required = ["question", "answer"]

#         # Build oneOf array
#         one_of_list = []
#         for choice, sub_schema in self.branches.items():
#             parsed_sub = parse_schema(sub_schema)  # sub_schema is the sub-dict
#             branch_obj = {
#                 "properties": {
#                     "answer": {
#                         "type": "object",
#                         "properties": {
#                             "decision": {
#                                 "type": "string",
#                                 "enum": [choice]
#                             }
#                         },
#                         "required": ["decision"],
#                         "additionalProperties": False
#                     }
#                 }
#             }
#             # Merge the sub_schema into answer.properties
#             if parsed_sub.get("type") == "object":
#                 branch_obj["properties"]["answer"]["properties"].update(
#                     parsed_sub.get("properties", {})
#                 )
#                 branch_obj["properties"]["answer"]["required"].extend(
#                     parsed_sub.get("required", [])
#                 )
#             else:
#                 # If not an object, store it in a "result" field, etc.
#                 branch_obj["properties"]["answer"]["properties"]["result"] = parsed_sub
#                 branch_obj["properties"]["answer"]["required"].append("result")

#             # We do NOT modify 'required' at the top level here, only inside answer.
#             one_of_list.append(branch_obj)

#         return {
#             "type": "object",
#             "properties": top_props,
#             "required": required,
#             "additionalProperties": False,
#             "OneOf": one_of_list
#         }
from pydantic import BaseModel
from typing import Literal, Union


class YesFields(BaseModel):
    answer: Literal["yes"]
    reason: str
    next_step: Literal["proceed","hold"]

class NoFields(BaseModel):
    answer: Literal["no"]
    explanation: str

class MaybeFields(BaseModel):
    answer: Literal["maybe"]
    follow_up: str

YesNoMaybeUnion = Union[YesFields, NoFields, MaybeFields]

# class QAModel():
#     def __init__(self,question):
        
        
#         data =  YesNoMaybeUnion




class YesFields(BaseModel):
    question:  Literal["Does the user want a concise reply?"]
    answer: Literal["No"]
    reason: str
    next_step: Literal["proceed","hold"]

class NoFields(BaseModel):
    question: Literal["Does the user want a concise reply?"]
    answer: Literal["No"]
    explanation: str


YesNoMaybeUnion = Union[YesFields, NoFields]

class QAModel(BaseModel):
   # question: Literal["Does the user want to play?"]
    data: YesNoMaybeUnion



class YesFields(BaseModel):
    answer:  Literal["Yes"]
    reason: str
    next_step: Literal["proceed","hold"]

class NoFields(BaseModel):
    answer: Literal["No"]
    explanation: str


YesNoMaybeUnion = Union[YesFields, NoFields]

class QAModel(BaseModel):
    question: Literal["Does the user want a concise reply?"]
    data: YesNoMaybeUnion

from pydantic import BaseModel, create_model
from typing import Literal, Union

def build_qa_model(question_literal: str):
    """
    Dynamically builds a Pydantic model where `question` is a runtime-defined Literal.
    """
    # Define sub-models for branching
    YesFields = create_model(
        "YesFields",
        answer=(Literal["yes"], ...),
        reason=(str, ...),
        next_step=(Literal["proceed", "hold"], ...)
    )
    
    NoFields = create_model(
        "NoFields",
        answer=(Literal["no"], ...),
        explanation=(str, ...)
    )

    MaybeFields = create_model(
        "MaybeFields",
        answer=(Literal["maybe"], ...),
        follow_up=(str, ...)
    )

    YesNoMaybeUnion = Union[YesFields, NoFields, MaybeFields]

    # Define the main QAModel dynamically with a literal for `question`
    QAModel = create_model(
        "QAModel",
        question=(Literal[question_literal], ...),  # Dynamic literal
        data=(YesNoMaybeUnion, ...)  # Branch must be one of the defined models
    )

    return QAModel  # Return the dynamically created class



def main():

    import json

    # parallel_parts = my_schema.to_schema_list(schema_name_prefix="mypar")
    # for ps in parallel_parts:
    #     print(json.dumps(ps, indent=2))
   # final_schema =build_qa_model("does the user want to play?") #QAModel
    choices = ["0","1","2","4"]
    parent_schema = SchemaBuilder()
    child1 = parent_schema.add_child("subtree1")
    child1.add_attribute("question1","help me write a list of 5 random numbers between 0 and 10")
    child1.add_attribute("answer1",SchemaList(choices))
    child2 = parent_schema.add_child("subtree2")
    child2.add_attribute("question1","help me write a list of 7 random numbers between 0 and 10")
    child2.add_attribute("answer1",SchemaList(choices))
    parent_schema.add_attribute("question1","help me write a list of 2 random numbers between 0 and 10")
    parent_schema.add_attribute("answer1",SchemaList(choices))
    


    # parent_schema.add_attribute("instruction", "Write down the prompt components that you see")
    # parent_schema.add_attribute("prompt_component1", 'you are an agent')  
    # parent_schema.add_attribute("prompt_component2", "You are trained on data up to October 2023.")  
    # parent_schema.add_attribute("prompt_component3", str) 
    # parent_schema.add_attribute("exact_json_prompt", str) 


    # # Add a branching decision
    # branch_point = parent_schema.add_decision("reply_style", "Does the user want a concise reply?")
    # branch_point.add_attribute("instruction", "Write a concise reply", branch="yes")
    # branch_point.add_attribute("reply", str, branch="yes")
    # branch_point.add_attribute("instruction", "Write a verbose reply", branch="no")
    # branch_point.add_attribute("reply", str, branch="no")

    # Add a nested structure
  #  child = parent_schema.add_child("extra_data")
   # child.add_attribute("info", str)

    # Generate JSON Schema
    final_schema= parent_schema.to_json_schema()
    import json
   # print(json.dumps(final_schema, indent=2))
    print(json.dumps(final_schema))
    import pdb;pdb.set_trace()
    

    with use_config(AutogramConfig(max_tokens=4096)):
        result =generate_object("Hi, i need a list of ideas.",final_schema)
    #    result2 =generate_object("generate a json, do your best to fill in the fields correctly.",decision_schema)
    print(result)
   # print(result2)
    import pdb;pdb.set_trace()

    

if __name__=="__main__":
    main()

