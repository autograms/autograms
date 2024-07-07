



def generate_image(prompt,model="dall-e-3",size="1024x1024"):

    
    from openai import OpenAI

    from . import api_key
    client =  OpenAI(api_key=api_key)

    
    image = client.images.generate(
    model=model,
    prompt=prompt,
    n=1,
    size=size
    )
    return image.data[0]
