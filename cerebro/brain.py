import os
import openai

# Configure a chave da API

class mind:
 
    def __init__(self, key_api):
        
        self.openai.api_key = key_api

    def inteligencia(self, prompt:str):

        # prompt = '171 do codigo penal do brasil'
        # prompt = 'for em python'
        prompt__ = prompt.lstrip()[len(prompt.split()[0]):].lstrip()


        completion = self.openai.Completion.create(
        #   model="code-davinci-002",
        model="text-davinci-003",
        prompt= prompt__,
        temperature=0.6,
        max_tokens=256,
        top_p=0.1,
        frequency_penalty=0.8,
        presence_penalty=0.4
        )

        return completion.choices[0].text

def inteligenciaIA(prompt, key_api): 
    openai.api_key = key_api 
    # prompt = '171 do codigo penal do brasil'
    # prompt = 'for em python'
    prompt__ = prompt.lstrip()[len(prompt.split()[0]):].lstrip()


    completion = openai.Completion.create(
    #   model="code-davinci-002",
    model="text-davinci-003",
    prompt= prompt__,
    temperature=0.8,
    max_tokens=500,
    top_p=0.6,
    frequency_penalty=0.8,
    presence_penalty=0.8
    )

    return completion.choices[0].text

