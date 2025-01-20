
"""
This example demonstrates how to build a retrieval-augmented chatbot using the AutoGRAMS framework. 
The chatbot can answer user questions about documentation stored in a local docs folder. 

IMPORTANT:
- This file should NOT contain a main entry point or code that starts the chatbot directly. 
- You will import 'chatbot' from this file into your own run script and execute it there.
- Make sure you have installed:
    pip install autograms

"""


import os
from typing import List

from autograms.agent_modules.vector_stores import AutoIndex





# AutoGRAMS imports
from autograms import autograms_function
from autograms.functional import (
    reply,
    reply_instruction,
    multiple_choice,
    yes_or_no,
    set_system_prompt,
    thought,
    silent_thought,
    get_system_prompt,
    GOTO,
    RETURNTO,
    append_system_prompt,
    extract_last_user_reply
)
from autograms.nodes import location
from autograms.memory import init_user_globals


# --------------------
# Global constants and variables
# --------------------
# --------------------
# Global constants and variables
# --------------------
MAX_CHUNK_CHARS = 2048  # The maximum chunk size in characters
CHUNK_OVERLAP_RAW = 64  # Overlap for chunk_raw
DOC_HEADING_TOKEN = "##"  # We consider '##' any heading marker (common in Markdown)
MAX_SEARCH_ITERATIONS = 1

# 
# doc_description: A short summary of what the docs are about
# docs: A list of all raw text from our documentation
# index: Our FAISS/Numpy index for vector search (depending on if faiss is installed)
#
doc_description = "Documentation for the codebase."
docs = []
index = None  # Will be set by init_chatbot()






# --------------------
# Initialization function (NOT an @autograms_function)
# This is called externally AFTER the Autogram config is set up, 
#  before the conversation starts.
# --------------------
def init_chatbot(docs_folder="docs", doc_summary="Documentation for the autograms codebase."):
    """
    Initializes the global variables for doc-related RAG.
    This function is optional, but it allows you to configure your 
    document indexing after the AutoGRAMS environment is ready.
    
    :param docs_folder: Path to the folder containing docs to be indexed.
    :param doc_summary: Short text description of your docs.
    """
    global doc_description
    global docs
    global index

    doc_description = doc_summary


    # 1) Read the raw text of each doc
    docs = read_docs(docs_folder)
    chunked_docs = []
    for file_data in docs:
        # file_data is a dict with {'file_path':..., 'content':...}
        new_chunks = chunk_document(file_data['text'], file_data['metadata'])
        for chunk in new_chunks:
          

            chunked_docs.append(chunk)

    index = AutoIndex.from_texts(chunked_docs)



# --------------------
# Helper functions for reading docs
# --------------------
def read_docs(docs_folder="docs",ext_list=[".md",".txt"]):
    """
    Given a directory path, read the text of each file and return a list of strings.
    This is a simplistic example that reads .md and .txt files, 
    but you can adapt for your own file types and doc parsing.
    """
    all_texts = []

    for root, _, files in os.walk(docs_folder):
        
        
        
        for file_name in files:
            
            if any([file_name.endswith(ext) for ext in ext_list]):
                path = os.path.join(root, file_name)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    all_texts.append({"text":content,"metadata":{"file_name":path}})

        
    return all_texts




def chunk_document(text, file_path):
    """
    Chunk a single document based on:
      1) Markdown section headings (starting with DOC_HEADING_TOKEN),
      2) If a chunk is still too large or there's no headings, chunk by newline,
      3) Fallback: chunk raw size.
    
    We produce a list of chunk dicts with:
        {
          'text': chunk_text,
          'metadata': file_path
        }
    """
    # If the text is short, just return as a single chunk
    if len(text) <= MAX_CHUNK_CHARS:
        return [{"text": text, "metadata": file_path}]

    # 1) Attempt chunk_by_sections if we have markdown headings
    if DOC_HEADING_TOKEN in text:
        sections = chunk_by_sections(text)
        final_chunks = []
        for sec in sections:
            if len(sec) <= MAX_CHUNK_CHARS:
                # This entire section fits in one chunk
                final_chunks.append(sec)
            else:
                # This section alone is bigger than MAX_CHUNK_CHARS => 
                # we revert to chunk_by_newline for this section
                # chunk_by_newline returns a list of smaller chunks
                newline_chunks = chunk_by_newline(sec)
                final_chunks.extend(newline_chunks)
        # now we have final_chunks as a list of strings,
        # but we still need to respect the MAX_CHUNK_CHARS
        # We'll group them into final segments
        grouped_sections = group_chunks(final_chunks, MAX_CHUNK_CHARS)
        return [{"text": chunk, "metadata": file_path} for chunk in grouped_sections]

    # 2) If no headings or doesn't appear to be Markdown, 
    #    let's chunk by newline
    #    (This step also covers extremely large plain text).
    newline_chunks = chunk_by_newline(text)
    # Some of them might be bigger than max chunk size, so group them
    # or raw-chunk them if needed
    grouped_sections = []
    for chunk in newline_chunks:
        if len(chunk) <= MAX_CHUNK_CHARS:
            grouped_sections.append(chunk)
        else:
            # Fallback to chunk_raw for this piece
            raw_chunks = chunk_raw(chunk, MAX_CHUNK_CHARS, CHUNK_OVERLAP_RAW)
            grouped_sections.extend(raw_chunks)

    # If everything is smaller, we still want to group consecutive chunks 
    # until we approach MAX_CHUNK_CHARS
    final_groups = group_chunks(grouped_sections, MAX_CHUNK_CHARS)
    return [{"text": c, "metadata": file_path} for c in final_groups]


def chunk_by_sections(text: str) -> List[str]:
    """
    Split text by '###' headings into sections. 
    Return a list of section strings (with headings included).
    Each heading + content up to the next heading is a "section".
    """
    # If there's no heading token, just return entire text as single section
    if DOC_HEADING_TOKEN not in text:
        return [text]

    # We'll split on the heading token, but we want to keep the heading 
    # with the associated chunk. 
    # Trick: re-insert the heading token at the start of each chunk.
    parts = text.split(DOC_HEADING_TOKEN)
    # The first part might not have a heading 
    # (text before the first heading). We'll treat that as well.
    sections = []
    for idx, part in enumerate(parts):
        if idx == 0:
            # text before the first heading
            if part.strip():
                sections.append(part.strip())
        else:
            # re-add the heading token
            chunk_text = DOC_HEADING_TOKEN + part
            sections.append(chunk_text.strip())

    return sections


def chunk_by_newline(text: str) -> List[str]:
    """
    Split text by newline markers. 
    Return a list of chunks (strings), each chunk is one paragraph block 
    (defined by a blank line or single line).
    For continuous lines, we combine them into a single chunk if possible, 
    but do not exceed MAX_CHUNK_CHARS. 
    (But if a single line is bigger than max chunk size, 
     we'll fallback in the caller to chunk_raw).
    """
    lines = text.splitlines(keepends=True)  # keep newlines to preserve formatting
    chunks = []
    current_chunk = []

    for line in lines:
        # If we add line to current_chunk, how big would it be?
        prospective_size = sum(len(ln) for ln in current_chunk) + len(line)
        if prospective_size > MAX_CHUNK_CHARS:
            # we flush the current_chunk
            if current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = []
        current_chunk.append(line)

    if current_chunk:
        chunks.append("".join(current_chunk))
    return chunks


def chunk_raw(text: str, max_chars: int, overlap: int) -> List[str]:
    """
    Raw chunking: we break the text every `max_chars` characters, 
    overlapping by `overlap` characters. 
    This is the last resort if no better splitting strategies apply.
    """
    result = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        result.append(chunk)
        # move forward with overlap
        start = end - overlap  # negative overlap => re-process some text
        if start < 0:
            start = 0
        if start >= len(text):
            break
        if start == end:
            # no progress possible -> break
            break
    return result


def group_chunks(section_list: List[str], max_size: int) -> List[str]:
    """
    We have a list of strings (section_list). We'll combine consecutive 
    sections if possible without exceeding max_size. If adding another 
    section would exceed max_size, we start a new chunk.
    This results in bigger but fewer chunks for improved context usage.
    """
    grouped = []
    current = []
    current_len = 0

    for sec in section_list:
        if current_len + len(sec) <= max_size:
            current.append(sec)
            current_len += len(sec)
        else:
            if current:
                grouped.append("".join(current))
            # start new chunk with sec
            current = [sec]
            current_len = len(sec)

    if current:
        grouped.append("".join(current))
    return grouped


# --------------------
# The main chatbot function
# --------------------
@autograms_function()
def chatbot():
    """
    This is the root function of our doc-QA chatbot. 
    It enters an infinite loop, replying to the user, 
    then deciding if searching the docs is useful, 
    then possibly calling the retrieve() function to handle retrieval.
    """

    # Set a broad system prompt describing the chatbot
    # Set a broad system prompt describing the chatbot
    set_system_prompt(
        "Your role is to give replies in conversational contexts and answer multiple choice questions. Be sure to be follow the INSTRUCTION you are given for your reply. Your main function is to look up and answer questions about a codebase for chatbots called autograms."  
    )

    # Greet the user and enter a loop where we continuously get user input & respond
    reply("Hello! I can answer your questions about autograms. what would you like to know?")
    doc_info=None

    while True:




        user_question = extract_last_user_reply()

        if not(doc_info is None):
            follow_up = yes_or_no(f"Consider the following Information:{doc_info}\nIs this information relevant to the following query '{user_question}'?")
            if follow_up:
                if yes_or_no(f"Consider the following Information:{doc_info}\nDoes this contain enough information to completely answer this query '{user_question}'?"):
                    reply_instruction(f"Using the docs, provide an to the user's question. Include details from:\n{doc_info}")
                    continue
            else:
                doc_info=None




        doc_info = retrieve(user_question,doc_info)  # doc_info is a summary of relevant results
        give_reply(doc_info)

@autograms_function()
def give_reply(doc_info):

    append_system_prompt(f"\n\nThis is additional information that should help answering questions \n{doc_info}")
        # Decide how confident we are that we found an answer

    reply_instruction(
        f"provide an to the user's question."
    )

    




# --------------------
# The retrieval function
# --------------------
@autograms_function(conv_scope="normal")
def retrieve(user_question,previous_context=None):
    """
    This function attempts to search the docs for relevant info to the user's question,
    up to MAX_SEARCH_ITERATIONS times. It returns a text summary of the found info.

    'conv_scope="normal"' means that thoughts in this function do not persist 
    once we return to the calling function. 
    (We don't want the models conversation memory to get filled with many search steps.)
    """
    append_system_prompt(f"\n\nHere is some additional context that may help {previous_context}")
    


    for i in range(MAX_SEARCH_ITERATIONS):
        # Think about how to refine the query
        if i==0 and not previous_context is None :
            refine_prompt = user_question

        else:
            refine_prompt = thought(
                f"What search query should we use next to help find information for the user? "
                "We can refine our query if needed. If it doesn't seem we need more iteration, say 'DONE' to stop early."
            )

 

        # Actually run a search on the doc index
        # (We assume 'index' has been initialized by init_chatbot.)
        search_results = index.similarity_search(refine_prompt, k=4)

        # Summarize the search results text
        for doc in search_results:
            append_system_prompt(f"\n\nHere is some additional context that may help {doc['text']}")
        combined_text = "\n\n".join([doc['text'] for doc in search_results])


        # Decide if we should keep going or not
        cont_search = yes_or_no(
            f"We were originally trying to find out he following information: {user_question}.\n\nDo we need to continue searching (maybe we haven't found a complete answer yet)?"
        )
        if not cont_search:
            break

    # Return the combined doc info to the caller
    return combined_text
