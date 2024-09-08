import json

with open("config.json", "r",
          encoding='utf-8') as jsonfile:
    config_data = json.load(jsonfile)

session_config = {
    'msg': [
        {"role": "system", "content": config_data['chatgpt']['preset'][0]}
    ],
    'send_voice': False,
    'new_bing': False,     
    'send_voice_private': False,  ##
    'send_emoticon' : True,   ##
    'send_answer' : True,
    'prompt_index' : 0
}