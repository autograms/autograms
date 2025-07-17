



from openai import OpenAI
import os


DEFAULT_HYPERPARAMETERS = {
    "n_epochs":1
  }



def finetune_openai_jsonl(training_file,model="gpt-4o-mini-2024-07-18",hyperparameters=None,use_dpo=False,api_key=None):

    if hyperparameters is None:
        hyperparameters =DEFAULT_HYPERPARAMETERS

    if api_key is None:
        api_key=os.environ["OPENAI_API_KEY"]

    client = OpenAI(api_key=api_key)

    response=client.files.create(
    file=open(training_file, "rb"),
    purpose="fine-tune"
    )


    training_file=response.id 

    if use_dpo:
        if hyperparameters is None:
            hyperparameters={"beta": 0.1}


        response = client.fine_tuning.jobs.create(
        training_file=training_file,
        model=model,
        method={
            "type": "dpo",
            "dpo": {
                "hyperparameters": hyperparameters,
            },
        }
        )

    else:
        response = client.fine_tuning.jobs.create(
        training_file=training_file,
        model=model,
        hyperparameters=hyperparameters
        )
    return response


