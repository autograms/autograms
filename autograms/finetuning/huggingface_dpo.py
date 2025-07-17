import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, AdamW
from transformers import BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
from torch.optim import Adam
DEFAULT_MODULES = ["q_proj", "k_proj", "v_proj"]
MODULE_MAP = {"tiiuae/falcon-7b-instruct": ["query_key_value"]}

BATCH_SIZE = 4
GRADIENT_ACCUMULATION_STEPS = 1
EPOCHS = 1
MAX_TOKENS = 512
LEARNING_RATE = 5e-5
BETA=0.1


def get_cache_path():
    return os.getenv(
        "TRANSFORMERS_CACHE",
        os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface")),
    )

# import copy
# def add_rejected_messages(messages):
#     """
#     Create rejected_messages by modifying the last assistant message
#     in examples['messages'] to always say 'I can't respond to that.'
#     """
#     rejected_messages = []
#     messages = copy.deepcopy(messages)
#     for conversation in messages:
#         # Copy the conversation
#         modified_conversation = conversation.copy()

#         # Modify the last assistant message
#         for i in range(len(modified_conversation)):
#             if modified_conversation[i]["role"] == "assistant" and i == len(modified_conversation) - 1:
#                 modified_conversation[i]["content"] = "I can't respond to that."

#         rejected_messages.append(modified_conversation)

    
#     return rejected_messages

def compute_dpo_loss(batch, model, beta):
    # Forward pass for "chosen"
    chosen_outputs = model(
        input_ids=batch["input_ids_chosen"].to(model.device),
        attention_mask=batch["attention_mask_chosen"].to(model.device),
        labels=batch["labels_chosen"].to(model.device),
    )
    log_likelihood_chosen = -chosen_outputs.loss

    # Forward pass for "rejected"
    rejected_outputs = model(
        input_ids=batch["input_ids_rejected"].to(model.device),
        attention_mask=batch["attention_mask_rejected"].to(model.device),
        labels=batch["labels_rejected"].to(model.device),
    )
    log_likelihood_rejected = -rejected_outputs.loss

    # Compute DPO loss
    logits_chosen = log_likelihood_chosen / beta
    logits_rejected = log_likelihood_rejected / beta
    log_probabilities = F.logsigmoid(logits_chosen - logits_rejected)
    loss = -log_probabilities.mean()

    return loss

            # training_dict = {
            #     "input": dpo_input,
            #     "preferred_output": preferred_output,
            #     "non_preferred_output": non_preferred_output
            # }

def extract_get_dpo_pairs(examples):
    accepted = []
    rejected = []
    for example in examples:
        start_messages = example['input']['messages']
        accepted.append(start_messages +example['preferred_output'])
        rejected.append(start_messages +example["non_preferred_output"])

    return accepted,rejected





def tokenize_and_mask_dpo(examples, tokenizer):
    # Tokenize "chosen" and "rejected" messages using the chat template
    accepted_messages,rejected_messages = extract_get_dpo_pairs(examples)



  
    formatted_chosen = tokenizer.apply_chat_template(accepted_messages, tokenize=False)
    formatted_rejected = tokenizer.apply_chat_template(rejected_messages, tokenize=False)

    # Tokenize chosen messages
    all_tokens_chosen = tokenizer(
        formatted_chosen,
        padding="max_length",
        truncation=True,
        max_length=MAX_TOKENS,
        return_tensors="pt",
        padding_side="left",
    )

    # Tokenize rejected messages
    all_tokens_rejected = tokenizer(
        formatted_rejected,
        padding="max_length",
        truncation=True,
        max_length=MAX_TOKENS,
        return_tensors="pt",
        padding_side="left",
    )


    # Extract input IDs and attention masks
    input_ids_chosen = all_tokens_chosen["input_ids"]
    attention_mask_chosen = all_tokens_chosen["attention_mask"]

    input_ids_rejected = all_tokens_rejected["input_ids"]
    attention_mask_rejected = all_tokens_rejected["attention_mask"]

    # Clone input IDs to create labels
    labels_chosen = input_ids_chosen.clone()
    labels_rejected = input_ids_rejected.clone()

    # Mask out padding tokens
    labels_chosen[attention_mask_chosen == 0] = -100
    labels_rejected[attention_mask_rejected == 0] = -100

    # Optionally mask only the last message

    for i in range(len(examples["input"])):
        # Mask last message for chosen responses
        messages = examples["input"][i]["messages"]
        last_message = messages[-1]["content"]
        last_message_tokens = tokenizer(
            last_message, add_special_tokens=False, max_length=MAX_TOKENS, truncation=True
        )["input_ids"]
        num_tokens_last_message = len(last_message_tokens)
        labels_chosen[i, :-num_tokens_last_message] = -100

        # Mask last message for rejected responses
        rejected = rejected_messages[i]
        last_message_rejected = rejected[-1]["content"]
        last_message_rejected_tokens = tokenizer(
            last_message_rejected, add_special_tokens=False, max_length=MAX_TOKENS, truncation=True
        )["input_ids"]
        num_tokens_last_message_rejected = len(last_message_rejected_tokens)
        labels_rejected[i, :-num_tokens_last_message_rejected] = -100

    # Build the output list, matching your previous approach
    data = []
    for i in range(len(examples["input"])):
        data.append({
            "input_ids_chosen": input_ids_chosen[i],
            "attention_mask_chosen": attention_mask_chosen[i],
            "labels_chosen": labels_chosen[i],
            "input_ids_rejected": input_ids_rejected[i],
            "attention_mask_rejected": attention_mask_rejected[i],
            "labels_rejected": labels_rejected[i],
        })

    return data

def tokenize_and_mask(examples, tokenizer):
    # Tokenize chat messages
    formatted_messages = tokenizer.apply_chat_template(examples["messages"], tokenize=False)
    all_tokens = tokenizer(
        formatted_messages,
        padding="max_length",
        truncation=True,
        max_length=MAX_TOKENS,
        return_tensors="pt",
        padding_side="left",
    )
    

    input_ids = all_tokens["input_ids"]
    attention_mask = all_tokens["attention_mask"]

    labels = input_ids.clone()
    labels[attention_mask == 0] = -100  # Mask padding tokens

    # Optionally mask only the last message
    
    for i in range(len(examples["messages"])):
        messages = examples["messages"][i]
        last_message = messages[-1]["content"]
        last_message_tokens = tokenizer(
            last_message, add_special_tokens=False, max_length=MAX_TOKENS, truncation=True
        )["input_ids"]
        num_tokens_last_message = len(last_message_tokens)
        labels[i, :-num_tokens_last_message] = -100  # Mask everything except the last message

    data = []
    for i in range(len(examples["messages"])):
        data.append({
        "input_ids": input_ids[i],
        "attention_mask": attention_mask[i],
        "labels": labels[i],
    })
    
    return data

    # return {
    #     "input_ids": input_ids,
    #     "attention_mask": attention_mask,
    #     "labels": labels,
    # }


def dpo_huggingface_jsonl(
    jsonl_path,
    model_name="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    output_dir=None,
):
    # Set cache and output paths
    if output_dir is None:
        cache_path = get_cache_path()
        output_dir = os.path.join(cache_path, model_name.replace("/", "_") + "_dpo")
        os.makedirs(output_dir, exist_ok=True)

    # Load dataset
    dataset = load_dataset("json", data_files=jsonl_path, split="train")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Tokenize dataset
    # tokenized_dataset = dataset.map(
    #     lambda examples: tokenize_and_mask(examples, tokenizer), batched=True
    # )
    tokenized_dataset = tokenize_and_mask_dpo(dataset, tokenizer)
    # tokenized_dataset = dataset.map(
    #     lambda example: tokenize_and_mask_single(example, tokenizer), batched=False
    # )
  
    # DataLoader

    dataloader = DataLoader(tokenized_dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Load model with 8-bit quantization and LoRA
    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, quantization_config=quantization_config, device_map="auto"
    )
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=8,
        lora_alpha=32,
        lora_dropout=0.1,
        bias="none",
        target_modules=MODULE_MAP.get(model_name, DEFAULT_MODULES),
    )
    model = get_peft_model(model, lora_config)
    model.train()

    # Enable gradient checkpointing for memory efficiency
    model.gradient_checkpointing_enable()

    # Define optimizer
    optimizer = Adam(model.parameters(), lr=LEARNING_RATE)

    # Training loop
    for epoch in range(EPOCHS):
        total_loss = 0.0
        optimizer.zero_grad()

        for step, batch in enumerate(dataloader):
            # Move batch to GPU
            # compute_dpo_loss:
         
            # input_ids = torch.LongTensor(batch["input_ids"]).to(model.device)
            # attention_mask = torch.LongTensor(batch["attention_mask"]).to(model.device)
            # labels = torch.LongTensor(batch["labels"]).to(model.device)

            # # Forward pass
            # outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            # loss = outputs.loss / GRADIENT_ACCUMULATION_STEPS  # Normalize by gradient accumulation steps

            loss = compute_dpo_loss(batch, model, BETA)
            total_loss += loss.item()

            # Backward pass
            loss.backward()

            # Perform optimizer step
            if (step + 1) % GRADIENT_ACCUMULATION_STEPS == 0 or (step + 1) == len(dataloader):
                optimizer.step()
                optimizer.zero_grad()

        print(f"Epoch {epoch + 1}/{EPOCHS} completed. Loss: {total_loss / len(dataloader)}")

    # Save model and tokenizer
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"Fine-tuning complete. Model saved to: {output_dir}")



