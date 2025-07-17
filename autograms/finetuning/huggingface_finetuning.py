import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM
from torch.optim import Adam
from transformers import BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

DEFAULT_MODULES = ["q_proj", "k_proj", "v_proj"]
MODULE_MAP = {"tiiuae/falcon-7b-instruct": ["query_key_value"]}

BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 4
EPOCHS = 1
MAX_TOKENS = 4096
LEARNING_RATE = 1e-5


def get_cache_path():
    return os.getenv(
        "TRANSFORMERS_CACHE",
        os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface")),
    )

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


def finetune_huggingface_jsonl(
    jsonl_path=None,
    model_name="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    output_dir=None,
):
    # Set cache and output paths
    if output_dir is None:
        cache_path = get_cache_path()
        output_dir = os.path.join(cache_path, model_name.replace("/", "_") + "_finetuned")
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
    tokenized_dataset = tokenize_and_mask(dataset, tokenizer)
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
         
            input_ids = torch.LongTensor(batch["input_ids"]).to(model.device)
            attention_mask = torch.LongTensor(batch["attention_mask"]).to(model.device)
            labels = torch.LongTensor(batch["labels"]).to(model.device)

            # Forward pass
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss / GRADIENT_ACCUMULATION_STEPS  # Normalize by gradient accumulation steps
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


