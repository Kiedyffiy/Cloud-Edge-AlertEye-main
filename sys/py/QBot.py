import json
import os
import traceback
import uuid
import base64
from copy import deepcopy
from flask import request, Flask,render_template, Response
import cv2
import openai
import requests
from text_to_image import text_to_image
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import tiktoken
from text_to_speech import gen_speech
import asyncio
from weather import weather
from new_bing import chat_whit_nb, reset_nb_session
from stable_diffusion import get_stable_diffusion_img
from img2prompt import img_to_prompt
from config_file import config_data
import ssl
from bs4 import BeautifulSoup
from selenium import webdriver
import urllib
import re
import sys
import hashlib
import pynvml
from importlib import reload
import psutil
import time
import random
from playsound import playsound
from subprocess import call
from queue import deque
import subprocess
import signal
qq_no = config_data['qq_bot']['qq_no']
session_config = {
    'msg': [
        {"role": "system", "content": config_data['chatgpt']['preset'][0]}
    ],
    'send_voice': False,
    'new_bing': False,     
    'send_voice_private': False,  ##
    'send_emoticon' : True,   ##
    'send_answer' : True,
    'prompt_index' : 0,
    'models_index' : 0,
    'group_reply' :False,
    'message_history': {
        
        }
}
camera = cv2.VideoCapture(0)
camera_process = None
RM_LS = 6
keyword = ("为什么","怎么","小iws","呜呜","嘿嘿","好可爱","原神","小kiedy","小Kiedy")#特判   ##
rootword = ("禁言","机型变更","撤回","全体禁言-f","灯火管制","失温管制","红茶","醒醒","repeat","岁月史书","kiss me","运行状态","trans","scrp")
keyword1 = ("小iws","嘿嘿","好可爱")   ##
models_pro = ("任何可爱的anime模型v4(手部优化,nosexy)",
              "任何可爱的anime模型v3-better",
              "水彩风格可爱anime suki模型",
              "写实风格（IWS不推荐）")
safe_group = ("1061777689","764457414","114514")
sessions = {}
current_key_index = 0     ##

openai.api_base = "https://gpt.lucent.blog/v1"
URL1 = "https://chat-gpt.aurorax.cloud/v1"

# 创建一个服务，把当前这个python文件当做一个服务
server = Flask(__name__)



@server.route('/')
def index():
    return render_template('index.html')

@server.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# 测试接口，可以测试本代码是否正常启动
#@server.route('/', methods=["GET"])
#def index():
#    return f"你好，世界!<br/>"

# LED接口/震动等
@server.route('/led', methods=["POST"])
def ledlight():
    msg_text = request.get_json().get('class')
    
    os.popen("/home/rock/GPIO/"+ msg_text +".sh")
    
    return "have lighted"



# 测试发送本地图片利用python服务器
@server.route('/emo', methods=["GET"])
def emco():
    msg_text = "[CQ:image,file=" + "http://192.168.97.243:13578/4.jpg" + "]"
    res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_private_msg",
                            params={'user_id': int(1950916064), 'message': msg_text}).json()    
    if res["status"] == "ok":
        print("私聊消息发送成功")
    else:
        print(res)
        print("私聊消息发送失败，错误信息：" + str(res['wording']))    
    return "sendtest"

# 普适发送消息给QQ端的接口
@server.route('/postword', methods=["POST"])
def posttest():
    msg_text = request.get_json().get('word')
    if msg_text == None:
        msg_text = '我无话可说'
    qq_num = request.get_json().get('qq_num')
    if qq_num == None:
        qq_num = '1950916064'
    send_private_message(str(qq_num), msg_text, False , False)
    return "YES!MAN!"



@server.route('/warn', methods=["POST"])
def warn():
    msg_text = request.get_json().get('class')
    if msg_text == None:
        msg_text = "5"
        #msg_text = "不当的"
    #phrase = "检测到您现在有" + msg_text +"的驾驶行为"
    os.popen("sudo sh /home/rock/GPIO/"+ "ledOff" +".sh")
    os.popen("sudo sh /home/rock/GPIO/"+ "ledR" +".sh")
    os.popen("sudo sh /home/rock/GPIO/"+ "vibrate" +".sh")
    #voice_path = asyncio.run(
        #gen_speech(phrase, "zh-CN-XiaoyiNeural", config_data['qq_bot']['voice_path']))
    #print(voice_path)
    voice_path = "/home/rock/py/py/voice/"+ msg_text + ".mp3"
    playsound(voice_path)
    os.popen("sudo sh /home/rock/GPIO/"+ "ledOff" +".sh")
    os.popen("sudo sh /home/rock/GPIO/"+ "ledG" +".sh")
    #call(["python", "speak.py", phrase])
    return "已经播报了警告信息！<br/>"

@server.route('/playsound', methods=["POST"])
def plays():
    msg_text = request.get_json().get('class')
    voice_path = "/home/rock/py/py/voice/"+ msg_text + ".mp3"
    playsound(voice_path)
    return "已经播放了声音！"

@server.route('/speak', methods=["POST"])
def speak():
    msg_text = request.get_json().get('word')
    if msg_text == None:
        msg_text = '我无话可说'
    phrase = msg_text
    print(phrase)
    voice_path = asyncio.run(
        gen_speech(phrase, "zh-CN-XiaoyiNeural", config_data['qq_bot']['voice_path']))
    #print(voice_path)
    playsound(voice_path)
    #call(["python", "speak.py", phrase])
    return "已经播报了信息！<br/>"

@server.route('/weather', methods=["GET"])
def ret_wea():
    phrase = weather_get()
    voice_path = asyncio.run(
        gen_speech(phrase, "zh-CN-XiaoyiNeural", config_data['qq_bot']['voice_path']))
    playsound(voice_path)
    return "已经播报了天气！"

@server.route('/goodnight', methods=["GET"])
def Goodnight():
    goodnight()
    return "已经晚安1"
@server.route('/goodnighttoall', methods=["GET"])
def Goodnighttoall():
    goodnighttoall()
    return "已经晚安2"

# 获取账号余额接口
@server.route('/credit_summary', methods=["GET"])
def credit_summary():
    return get_credit_summary()

# qq消息上报接口，qq机器人监听到的消息内容将被上报到这里
@server.route('/', methods=["POST"])
def get_message():
    if request.get_json().get('message_type') == 'private':  # 如果是私聊信息
        uid = request.get_json().get('sender').get('user_id')  # 获取信息发送者的 QQ号码
        message = request.get_json().get('raw_message')  # 获取原始信息
        sender = request.get_json().get('sender')  # 消息发送者的资料
        print("siliao")   ##
        print("收到私聊消息：")
        print(message)
        # 下面你可以执行更多逻辑，这里只演示与ChatGPT对话
        if message.strip().startswith('生成图像'):
            message = str(message).replace('生成图像', '')
            session = get_chat_session('P' + str(uid))
            msg_text = chat(message, session)  # 将消息转发给ChatGPT处理
            # 将ChatGPT的描述转换为图画
            print('开始生成图像')
            pic_path = get_openai_image(msg_text)
            send_private_message_image(uid, pic_path, msg_text)
        elif message.strip().startswith('直接生成图像'):
            message = str(message).replace('直接生成图像', '')
            print('开始直接生成图像')
            pic_path = get_openai_image(message)
            send_private_message_image(uid, pic_path, '')
        elif message.strip().startswith('/draw'):
            print("开始stable-diffusion生成")
            session = get_chat_session('P' + str(uid))
            pic_url = ""
            try:
                pic_url = sd_img(message.replace("/draw", "").strip(),session)
            except Exception as e:
                print("stable-diffusion 接口报错: " + str(e))
                send_private_message(uid, "Stable Diffusion 接口报错: " + str(e), False)
            print("stable-diffusion 生成图像: " + pic_url)
            send_private_message_image(uid, pic_url, '')
        elif message.strip().startswith('[CQ:image'):  
            print("开始分析图像")
            # 定义正则表达式
            print(message.strip())
            pattern = r'url=([^ ]+)'
            # 使用正则表达式查找匹配的字符串
            match = re.search(pattern, message.strip())
            print(match)
            prompt = img_to_prompt(match.group(1))
            send_private_message(uid, prompt, False, False)  # 将消息返回的内容发送给用户
        else:
            # 获得对话session
            session = get_chat_session('P' + str(uid))
            if session['new_bing']:
                msg_text = chat_nb(message, session)  # 将消息转发给new bing 处理
            else:
                msg_text = chat(message, session,uid)  # 将消息转发给ChatGPT处理
            if msg_text != '!no!ans!':
                send_private_message(uid, msg_text, session['send_voice_private'],session['send_emoticon'])  # 将消息返回的内容发送给用户

    if request.get_json().get('message_type') == 'group':  # 如果是群消息
        gid = request.get_json().get('group_id')  # 群号
        uid = request.get_json().get('sender').get('user_id')  # 发言者的qq号
        message = request.get_json().get('raw_message')  # 获取原始信息
        message_id = request.get_json().get('message_id') 
        #print("message_id: ",message_id)
        # 判断当被@时才回答
        session_g = get_chat_session('G' + str(gid))
        record_gmsg(session_g, uid, message, message_id)
        if session_g['group_reply'] == False:
            safe_check(session_g,gid)
        if ((str("[CQ:at,qq=%s]" % qq_no) in message) or keyword_check(message,uid)) and (session_g['group_reply'] == True or join_in_chat(uid, message)): 
            sender = request.get_json().get('sender')  # 消息发送者的资料
            print("收到群聊消息：")
            print(message)
            message = str(message).replace(str("[CQ:at,qq=%s]" % qq_no), '')
            if message.strip().startswith('生成图像'):
                message = str(message).replace('生成图像', '')
                session = get_chat_session('G' + str(gid))
                msg_text = chat(message, session,uid)  # 将消息转发给ChatGPT处理
                # 将ChatGPT的描述转换为图画
                print('开始生成图像')
                pic_path = get_openai_image(msg_text)
                send_group_message_image(gid, pic_path, uid, msg_text)
            elif message.strip().startswith('直接生成图像'):
                message = str(message).replace('直接生成图像', '')
                print('开始直接生成图像')
                pic_path = get_openai_image(message)
                send_group_message_image(gid, pic_path, uid, '')
            elif message.strip().startswith('/draw'):
                print("开始stable-diffusion生成")
                session = get_chat_session('G' + str(gid))
                try:
                    pic_url = sd_img(message.replace("/draw", "").strip(),session)
                except Exception as e:
                    print("stable-diffusion 接口报错: " + str(e))
                    send_group_message(gid, "Stable Diffusion 接口报错: " + str(e), uid, False)
                print("stable-diffusion 生成图像: " + pic_url)
                send_group_message_image(gid, pic_url, uid, '')
            elif message.strip().startswith('[CQ:image'):  
                print("开始分析图像")
                # 定义正则表达式
                print(message.strip())
                pattern = r'url=([^ ]+)'
                # 使用正则表达式查找匹配的字符串
                match = re.search(pattern, message.strip())
                print(match)
                prompt = img_to_prompt(match.group(1))
                send_group_message(gid, prompt,uid,  False, False)  # 将消息返回的内容发送给用户
            else:
                # 下面你可以执行更多逻辑，这里只演示与ChatGPT对话
                # 获得对话session
                session = get_chat_session('G' + str(gid))
                if session['new_bing']:
                    msg_text = chat_nb(message, session)  # 将消息转发给new bing处理
                else:
                    msg_text = chat(message, session,uid,gid)  # 将消息转发给ChatGPT处理
                if msg_text != '!no!ans!':
                    send_group_message(gid, msg_text, uid, session['send_voice'],session['send_emoticon'])  # 将消息转发到群里

    if request.get_json().get('post_type') == 'request':  # 收到请求消息
        print("收到请求消息")
        request_type = request.get_json().get('request_type')  # group
        uid = request.get_json().get('user_id')
        flag = request.get_json().get('flag')
        comment = request.get_json().get('comment')
        print("配置文件 auto_confirm:" + str(config_data['qq_bot']['auto_confirm']) + " admin_qq: " + str(
            config_data['qq_bot']['admin_qq']))
        if request_type == "friend":
            print("收到加好友申请")
            print("QQ：", uid)
            print("验证信息", comment)
            # 如果配置文件里auto_confirm为 TRUE，则自动通过
            if config_data['qq_bot']['auto_confirm']:
                set_friend_add_request(flag, "true")
            else:
                for j in range(len(config_data['qq_bot']['admin_qq'])):    ##
                    if str(uid) == config_data['qq_bot']['admin_qq'][j]:  # 否则只有管理员的好友请求会通过   ##
                        print("管理员加好友请求，通过")
                        set_friend_add_request(flag, "true")
        if request_type == "group":
            print("收到群请求")
            sub_type = request.get_json().get('sub_type')  # 两种，一种的加群(当机器人为管理员的情况下)，一种是邀请入群
            gid = request.get_json().get('group_id')
            if sub_type == "add":
                # 如果机器人是管理员，会收到这种请求，请自行处理
                print("收到加群申请，不进行处理")
            elif sub_type == "invite":
                print("收到邀请入群申请")
                print("群号：", gid)
                # 如果配置文件里auto_confirm为 TRUE，则自动通过
                if config_data['qq_bot']['auto_confirm']:
                    set_group_invite_request(flag, "true")
                else:
                    if str(uid) == config_data['qq_bot']['admin_qq'][0]:  # 否则只有管理员的拉群请求会通过
                        set_group_invite_request(flag, "true")
    return "ok"


# 测试接口，可以用来测试与ChatGPT的交互是否正常，用来排查问题
@server.route('/chat', methods=['post'])
def chatapi():
    requestJson = request.get_data()
    if requestJson is None or requestJson == "" or requestJson == {}:
        resu = {'code': 1, 'msg': '请求内容不能为空'}
        return json.dumps(resu, ensure_ascii=False)
    data = json.loads(requestJson)
    if data.get('id') is None or data['id'] == "":
        resu = {'code': 1, 'msg': '会话id不能为空'}
        return json.dumps(resu, ensure_ascii=False)
    print(data)
    try:
        s = get_chat_session(data['id'])
        msg = chat(data['msg'], s)
        if '查询余额' == data['msg'].strip():
            msg = msg.replace('\n', '<br/>')
        resu = {'code': 0, 'data': msg, 'id': data['id']}
        return json.dumps(resu, ensure_ascii=False)
    except Exception as error:
        print("接口报错")
        resu = {'code': 1, 'msg': '请求异常: ' + str(error)}
        return json.dumps(resu, ensure_ascii=False)


# 重置会话接口
@server.route('/reset_chat', methods=['post'])
def reset_chat():
    requestJson = request.get_data()
    if requestJson is None or requestJson == "" or requestJson == {}:
        resu = {'code': 1, 'msg': '请求内容不能为空'}
        return json.dumps(resu, ensure_ascii=False)
    data = json.loads(requestJson)
    if data['id'] is None or data['id'] == "":
        resu = {'code': 1, 'msg': '会话id不能为空'}
        return json.dumps(resu, ensure_ascii=False)
    # 获得对话session
    session = get_chat_session(data['id'])
    # 清除对话内容但保留人设
    del session['msg'][1:len(session['msg'])]
    resu = {'code': 0, 'msg': '重置成功'}
    return json.dumps(resu, ensure_ascii=False)

# 与new bing交互
def chat_nb(msg, session):
    try:
        if '红茶' == msg.strip():
            session['send_answer'] = False
            return '困困，我要睡觉了'
        if '醒醒' == msg.strip():
            session['send_answer'] = True
            return '我可是高性能的喵！'
        if  session['send_answer'] == False :
            return '!no!ans!'
        if msg.strip() == '':
            return '您好，我是人工智能助手，如果您有任何问题，请随时告诉我，我将尽力回答。\n如果您需要重置我们的会话，请回复`重置会话`'
        if '语音开启' == msg.strip():
            session['send_voice'] = True
            session['send_voice_private'] = True
            return '语音回复已开启'
        if '语音关闭' == msg.strip():
            session['send_voice'] = False
            session['send_voice_private'] = False
            return '语音回复已关闭'
        if '重置对话' == msg.strip() or '重置会话' == msg.strip():
            reset_nb_session(session['id'])
            return '会话已重置'
        if '指令说明' == msg.strip():
            return "指令如下(群内需@机器人)：\n1.[重置会话] 请发送 重置会话\n2.[设置人格] 请发送 设置人格+人格描述\n3.[重置人格] 请发送 重置人格\n4.[指令说明] 请发送 " \
                   "指令说明\n注意：\n重置会话不会清空人格,重置人格会重置会话!\n设置人格后人格将一直存在，除非重置人格或重启逻辑端!"
        if "懒散模式" == msg.strip():
            session['new_bing'] = False
            return "哈~~（打哈欠）我感觉睡意爬上了我的脊背（已切换至ChatGPT）" + "[CQ:image,file=file:///" + config_data['qq_bot']['emoticon_path'] +"\\special\\stupid\\1.jpg" +"]"
        print("问: " + msg)
        replay = asyncio.run(chat_whit_nb(session['id'], msg))
        print("New Bing 返回: " + replay)
        return replay
    except Exception as e:
        traceback.print_exc()
        return str('异常: ' + str(e))
    
    
    
#函数说明
my_functions = [
    {
        "name": "search_internet",
        "description": "通过互联网搜索信息的方法",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                }
            },
            "required": ["query"],
        },
    }
]   
# 搜索互联网
def search_internet(query):
    res = requests.post(url="https://duck.lucent.blog/search", json=query).json()
    return res
# 与ChatGPT交互的方法
def chat(msg, session, uid, gid = '0' ):
    try:
        global camera_process
        sys_cmd = "!noroot"
        if gid != '0':
           sys_cmd = system_command(msg, session,uid,gid) 
        if sys_cmd != "!noroot":
            return sys_cmd
        if '启动'== msg.strip():
            camera_process = sys_det_start()
            return "已经启动了疲劳驾驶检测系统！"
        if '停止'== msg.strip():
            sys_det_end()
            return "已经结束了疲劳驾驶检测系统！"            
        if '红茶' == msg.strip():
            session['send_answer'] = False
            return '困困，我要睡觉了'
        if '醒醒' == msg.strip():
            session['send_answer'] = True
            return '我可是高性能的喵！'
        if check_share(msg.strip()) == True:
            resmsg = share_read(msg.strip())          
            return resmsg
        if '运行状态' == msg.strip():
            if admin_check(uid) == True :
                return "该版本暂时不支持运行状态查询"
            else :
                return "[CQ:image,file=file:///" + rand_zayu() +"]"
        if  session['send_answer'] == False :
            return '!no!ans!'
        if msg.strip() == '':
            return '您好，我是人工智能助手，如果您有任何问题，请随时告诉我，我将尽力回答。\n如果您需要重置我们的会话，请回复`重置会话`'
        if '语音开启' == msg.strip():
            session['send_voice'] = True
            session['send_voice_private'] = True
            return '语音回复已开启'
        if '语音关闭' == msg.strip():
            session['send_voice'] = False
            session['send_voice_private'] = False
            return '语音回复已关闭'
        if '表情管理' ==  msg.strip():
            session['send_emoticon'] = False
            return '我会好好控制自己'
        if '表情放纵' ==  msg.strip():
            session['send_emoticon'] = True
            return '我会在合适的时候表达感情'   
        if '模型展示' == msg.strip():
            models_txt = ""
            for i in range(len(models_pro)):
                models_txt = models_txt + "Index["+str(i)+"]: "+models_pro[i]+"\n"
            return models_txt
        if msg.strip().startswith('模型切换'):
            msg = msg.strip();
            index = int(msg.strip('模型切换').strip())
            if index < 0 or index >= len(models_pro):
                return '下标越界！！或者请参考格式：  模型切换（空格）模型下标'
            else:
                session['models_index'] = index
                return 'Already Executed'            
        if ('嘿嘿' in msg or '的狗' in msg) or '好想' in msg :
            return "（ᗜ`‸´ᗜ )别在这里发癫！！！\n"+"[CQ:image,file=file:///"+ config_data['qq_bot']['emoticon_path'] +"\\special\\fadian\\1.jpg]"
        if '涩涩' in msg or '色色' in msg:
            return "色色是不好的哦，如果需要色色你可以私聊群主，他可懂了，还可以教你登大人【微笑】" + str('[CQ:at,qq=%s]\n' % "1187265066")
        if '重置对话' == msg.strip() or '重置会话' == msg.strip():
            # 清除对话内容但保留人设
            del session['msg'][1:len(session['msg'])]
            return "会话已重置"
        if '重置人格' == msg.strip():
            # 清空对话内容并恢复预设人设
            index = session['prompt_index']
            session['msg'] = [
                {"role": "system", "content": config_data['chatgpt']['preset'][index]}
            ]
            return '人格已重置'
        if msg.strip().startswith('预设人格'):
            # 预设已有人格
            #print(msg)
            #print(msg.strip('预设人格').strip())
            msg = msg.strip();
            index = int(msg.strip('预设人格').strip())
            if index < 0 or index >= len(config_data['chatgpt']['preset']):
                return '下标越界！！或者请参考格式：  预设人格（空格）预设下标'
            else:
                session['prompt_index'] = index
                session['msg'] = [
                    {"role": "system", "content": config_data['chatgpt']['preset'][index]}
                ]
                return 'Already Executed'
        if msg.strip().startswith('helptrans'):
            return '（微笑）如下为主人可能用得上的热门语种代号：\n'\
                   '1.汉语 zh 2.西班牙语 es\n'\
                       '3.英语 en 4.阿拉伯语 ar\n'\
                           '5.印地语 hi 6.孟加拉语 bn\n'\
                               '7.葡萄牙语 pt 8.俄语 ru\n'\
                                   '9.日语 ja 10.韩语 ko\n'\
                                       '11.德语 de 12.法语 fr'
                                  
        if msg.strip().startswith('settrans'):
            msg = msg.strip()
            STR = str(msg.replace('settrans','',1).strip())
            print(STR)
            if STR == 'zh':
                STR = 'zh-CHS'
            TR.set_to(STR)
            return "小iws已经成功切换翻译目标语言为："+STR+" 的喵！"
        if msg.strip().startswith('trans'):
            msg = msg.strip()
            if "[CQ:image,file=" in msg :
                pattern = re.compile(r'url=(.*?)\]')
                result = pattern.findall(msg)
                txt = "我很努力地翻译了喵 ：\n"
                for item,index in zip(result,range(len(result))) :
                    txt += "Index[" + str(index) + "] :\n" 
                    Group = TRP.connect(item)
                    for line,index_2 in zip(Group,range(len(Group))):
                        txt += "Line(" + str(index_2) + ") : " + line + "\n"
                return txt
            else :
                STR = str(msg.replace('trans','',1).strip())
                print(STR)
                text = TR.connect(STR)[0]
                txt = "我很努力地翻译了喵 ：" + text
                print(txt)
                return txt
        if msg.strip().startswith('scrp'):
            msg = msg.strip()
            excute_qq = re.match(r'scrp\[CQ:at,qq=(.*)\]',msg)
            qq_uid = excute_qq.groups()[0]
            return scraper_all(session, qq_uid)
        if '查询余额' == msg.strip():
            text = ""
            for i in range(len(config_data['openai']['api_key'])):
                text = text + get_credit_new(i)
                #text = text + "Key_" + str(i + 1) + " 余额: " + str(round(get_credit_summary_by_index(i), 2)) + "美元\n"
            return text
        if 'system command' == msg.strip():
            return "==========CMD=========\n"\
                   "1.[重置会话]  2.[设置人格]\n3.[重置人格]  4.[预设人格]\n5.[表情管理]  6.[表情放纵]\n" \
                   "7.[语音开启]  8.[语音关闭]\n9.[模型展示]  A.[模型切换]\nB.[红茶]        C.[醒醒]      \n"\
                   "D.[认真模式]  E.[懒散模式]\nF.[查询余额]  G.[/draw +p]\nH.[trans +any]  \n"\
                   "I.[settrans +languageType]\nJ.[helptrans]\n"\
                   "==========END========="
        if msg.strip().startswith('/img'):
            msg = str(msg).replace('/img', '')
            print('开始直接生成图像')
            pic_path = get_openai_image(msg)
            return "![](" + pic_path + ")"
        if msg.strip().startswith('设置人格'):
            # 清空对话并设置人设
            session['msg'] = [
                {"role": "system", "content": msg.strip().replace('设置人格', '')}
            ]
            return '人格设置成功'
        if "认真模式" == msg.strip():
            session['new_bing'] = True
            return "我感觉自己充满了决心！(已切换至New Bing)"+"[CQ:image,file=file:///" + config_data['qq_bot']['emoticon_path'] +"\\special\\serious\\1.jpg"+"]"
        # 设置本次对话内容
        session['msg'].append({"role": "user", "content": msg})
        # 设置时间
        session['msg'][1] = {"role": "system", "content": "current time is:" + get_bj_time()}
        # 检查是否超过tokens限制
        while num_tokens_from_messages(session['msg']) > config_data['chatgpt']['max_tokens']:
            # 当超过记忆保存最大量时，清理一条
            del session['msg'][2:3]
        # 与ChatGPT交互获得对话内容
        #message = "非常抱歉，IWS主人正在与错误代号： <502>  进行斗争，请等待服务恢复！\n"\
                #  "这段时间内，newbing服务仍将继续，请使用认真模式来操作。小iws依旧爱您！"
        message = chat_with_gpt(session['msg'])
        # 记录上下文
        session['msg'].append({"role": "assistant", "content": message})
        print("ChatGPT返回内容: ")
        if message.strip().startswith('HTTP'):
            print("已代替返回了温和的报错")
            return "小iws的小cpu有点超载呀，请再问我一遍吧【委屈】（原因可能是iws没给够零花钱）" + "[CQ:image,file=file:///" + rand_sorry() +"]"
        return message
    except Exception as error:
        traceback.print_exc()
        return str('异常: ' + str(error))
    
# 记录群友当前消息
def record_gmsg(session,uid,raw_message,message_id):
    rem_len = RM_LS*2
    message = str(raw_message).replace(str("[CQ:at,qq=%s]" % qq_no), '')
    if str(uid) not in session['message_history'].keys():
        session['message_history'][str(uid)] = deque([{'message_id':str(message_id),'content':message}])
    elif len(session['message_history'][str(uid)]) == rem_len:
        session['message_history'][str(uid)].popleft()
        session['message_history'][str(uid)].append({'message_id':str(message_id),'content':message})
    else:
        session['message_history'][str(uid)].append({'message_id':str(message_id),'content':message})
    #print(session['message_history'][str(uid)])
    
#爬取群友资源消息
def scraper_all(session, uid):
    sflag = False
    save_path = config_data['scraper']['save_path']
    pattern = re.compile(r'url=(.*?)\]')
    if str(uid) not in session['message_history']:
        return '主人，他还没有发图片和视频，我们无法爬取喵！'
    if len(session['message_history'][str(uid)]) == 0 :
        return '主人，他还没有发图片和视频，我们无法爬取喵！'
    for item in session['message_history'][str(uid)]:
        if '[CQ:image,file' in item['content'] :
            image_path = save_path + "//image"
            all_content=os.listdir(image_path)
            now_index = len(all_content)
            result = pattern.findall(item['content'])
            for index_i in range(len(result)) :
                save_name = "//"+str(now_index+1+index_i)+".jpg"
                image_path += save_name
                r = requests.get(result[index_i])
                with open(image_path, "wb") as ff: 
                    ff.write(r.content)
                sflag = True
                ff.close()
        elif '[CQ:video,file' in item['content'] :
            video_path = save_path + "//video"
            all_content=os.listdir(video_path)
            now_index = len(all_content)
            result = pattern.findall(item['content'])
            for index_i in range(len(result)) :
                save_name = "//"+str(now_index+1+index_i)+".mp4"
                video_path += save_name
                r = requests.get(result[index_i])
                with open(video_path, "wb") as ff: 
                    ff.write(r.content)
                sflag = True
                ff.close()
    if sflag == True :
        return "好的主人我已经成功爬取这位群友的资源了喵！要抱抱奖励的喵！"
    else :
        return "主人，这位群友的消息干巴巴的一点营养都没有，哭哭的喵~"
    
# 群组安全性检查
def safe_check(session,gid):
    for i in range(len(safe_group)):
        if str(gid) == safe_group[i]:
            print("监测到安全群聊")
            session['group_reply'] = True
# 获取北京时间
def get_bj_time():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    SHA_TZ = timezone(
        timedelta(hours=8),
        name='Asia/Shanghai',
    )
    # 北京时间
    beijing_now = utc_now.astimezone(SHA_TZ)
    fmt = '%Y-%m-%d %H:%M:%S'
    now_fmt = beijing_now.strftime(fmt)
    return now_fmt

def rand_sorry():  ##
    target_path = config_data['qq_bot']['emoticon_path']
    target_path = target_path + "\\special\\sorry"
    all_content=os.listdir(target_path)
    choose_tag = random.randint(1,len(all_content))    
    target_path = target_path + "\\" +str(choose_tag) + ".jpg"
    return target_path

def rand_zayu():  ##
    target_path = config_data['qq_bot']['emoticon_path']
    target_path = target_path + "\\special\\zayu"
    all_content=os.listdir(target_path)
    choose_tag = random.randint(1,len(all_content))    
    target_path = target_path + "\\" +str(choose_tag) + ".jpg"
    return target_path

#条件是否满足群聊会话的回复
def join_in_chat(uid,message):
    if admin_check(uid) == True :
        return True
    elif client_check(uid) == True and (str("[CQ:at,qq=%s]" % qq_no) in message) :
        return True
    elif client_check(uid) == True and '运行状态' in message :
        return True
    else :
        return False

def keyword_check(message,uid): #对群消息关键内容进行特判，跳过过程@  ##
    for i in range(len(keyword)):
        if keyword[i] in message :
            print("监测到关键词：" + keyword[i] + "执行特判")
            return True
            break;
    if admin_check(uid) == True or client_check(uid) == True :
        for j in range(len(rootword)):
            if rootword[j] in message :
                print("监测到关键词：" + rootword[j] + "执行特判")
                return True
                break;
    if check_share(message.strip()):
        return True
    return False

# 获取对话session
def get_chat_session(sessionid):
    if sessionid not in sessions:
        config = deepcopy(session_config)
        config['id'] = sessionid
        config['msg'].append({"role": "system", "content": "current time is:" + get_bj_time()})
        sessions[sessionid] = config
    return sessions[sessionid]



def chat_with_gpt(messages):
    global current_key_index
    max_length = len(config_data['openai']['api_key']) - 1
    try:
        if not config_data['openai']['api_key']:
            return "请设置Api Key"
        else:
            if current_key_index > max_length:
                current_key_index = 0
                return "全部Key均已达到速率限制,请等待一分钟后再尝试"
            openai.api_key = config_data['openai']['api_key'][current_key_index]
        resp = openai.ChatCompletion.create(
            model=config_data['chatgpt']['model'],
            messages=messages,
            functions=my_functions
        )
	# stop是正常返回的标识
        if "stop" == resp['choices'][0]['finish_reason']:
            resp = resp['choices'][0]['message']['content']
	# function_call是GPT请求调用函数的标识
        elif "function_call" == resp['choices'][0]['finish_reason']:
	    # GPT请求调用的函数名
            fun_name = resp['choices'][0]['message']['function_call']['name']
	    # GPT想要传递给函数的参数
            param = resp['choices'][0]['message']['function_call']['arguments']
            # 如果你有自己的函数，可以接着写
            if "search_internet" == fun_name:
                query = json.loads(param)
                print("GPT请求调用搜索函数,搜索参数:")
                print(query)
                search_res = search_internet(query)
                print("互联网搜索结果:")
                print(search_res)
                # 函数返回结果交给gpt
                messages.append({"role": "function", "name": fun_name, "content": search_res['data']})
                # 重新与gpt交互
                return chat_with_gpt(messages)
            else:
                resp = "未知函数"
        else:
            resp = "未知错误"
    except openai.OpenAIError as e:
        if str(e).__contains__("Rate limit reached for default-gpt-3.5-turbo") and current_key_index <= max_length:
            # 切换key
            current_key_index = current_key_index + 1
            print("速率限制，尝试切换key")
            return chat_with_gpt(messages)
        elif str(e).__contains__(
                "Your access was terminated due to violation of our policies") and current_key_index <= max_length:
            print("请及时确认该Key: " + str(openai.api_key) + " 是否正常，若异常，请移除")
            if current_key_index + 1 > max_length:
                return str(e)
            else:
                print("访问被阻止，尝试切换Key")
                # 切换key
                current_key_index = current_key_index + 1
                return chat_with_gpt(messages)
        else:
            print('openai 接口报错: ' + str(e))
            resp = str(e)
    return resp

def admin_check(uid):
    for j in range(len(config_data['qq_bot']['admin_qq'])):
        if str(uid) == config_data['qq_bot']['admin_qq'][j]:
            return True
    return False

def client_check(uid):
    for j in range(len(config_data['qq_bot']['client_qq'])):
        if str(uid) == config_data['qq_bot']['client_qq'][j]:
            return True
    return False    


    
#转化url到jj
def transform_url(url):
    in_str = 'jj'
    lis = list(url)
    lis.insert(20, in_str)
    sre = ''.join(lis)
    #print(sre)
    return sre
#检查是否符合分享要求
def check_share(str3):
    if "[CQ:json,data={"in str3 and "b23.tv" in str3 :
        return True
    else:
        return False
#爬取关键信息
def share_read(str3):
    os.environ['NO_PROXY'] = "https://b23.tv"
    os.environ['NO_PROXY'] = "https://www.jijidown.com"
    update_time = ''
    title_v = ''
    pic_url = ''
    desc = ''
    username =''
    coin = '' 
    like = ''
    collect = ''
    pattern = re.compile(r'\"qqdocurl\"\:\"(.*?)\?')
    result = pattern.findall(str3)
    try:
        s = result[0].replace('\\', '')
    except:
        return "主人~这个哔哩哔哩分享有些不同寻常喵，小iws看不懂喵【猫猫困惑】"
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68',
    }
    r = requests.get(s,headers=headers)
    jj = transform_url(r.url)
    start_url = jj
    #part1
    # 控制chrome浏览器
    driver = webdriver.Chrome("./chromedriver/chromedriver.exe")
    # 输入网址
    driver.get(start_url)
    # 停一下，等待加载完毕
    time.sleep(5)
    # 获取网页内容Elements
    content = driver.page_source
    my_page = BeautifulSoup(content, 'lxml')
    for tag in my_page.find_all('img',class_='cover'):
        try:
            pic_url = tag['src']
            print(pic_url)
        except:
            a = 1
    # 结束
    driver.quit()
    #part2
    start_url = r.url
    driver = webdriver.Chrome("./chromedriver/chromedriver.exe")
    driver.get(start_url)
    time.sleep(2)
    content = driver.page_source
    my_page = BeautifulSoup(content, 'lxml')
    for tag in my_page.find_all('meta'):
        try:
            if tag['itemprop'] == 'uploadDate':
                update_time = tag['content']
        except:
            a = 1
    for tag in my_page.find_all('div',class_='right-container is-in-large-ab'):
        try:
            sub_tag = tag.find('a',class_="up-name") 
            username = sub_tag.text.strip()
        except:
            sub_tag = tag.find('a',class_="up-name is_vip")
            username = sub_tag.text.strip()
    for tag in my_page.find_all('div',class_='video-info-v1 video-info-v1-ab report-wrap-module report-scroll-module'):
        sub_tag = tag.find('h1',class_="video-title tit") 
        title_v = sub_tag.text.strip()    
    for tag in my_page.find_all('div',class_='video-desc-v1'):
        sub_tag = tag.find('span',class_="desc-info-text") 
        desc = sub_tag.text.strip()    
    for tag in my_page.find_all('div',class_='video-toolbar-left'):
        sub_tag = tag.find('span',class_="video-like-info video-toolbar-item-text") 
       # sub_sub_tag = sub_tag.find('span',class_='info-text')
        like = sub_tag.text.strip()
        sub_tag = tag.find('span',class_="video-coin-info video-toolbar-item-text") 
      #  sub_sub_tag = sub_tag.find('span',class_='info-text')
        coin = sub_tag.text.strip()
        sub_tag = tag.find('span',class_="video-fav-info video-toolbar-item-text") 
      #  sub_sub_tag = sub_tag.find('span',class_='info-text')
        collect = sub_tag.text.strip()        
        # 结束
    driver.quit()    
    list_res = []
    list_res.append(username) #0
    list_res.append(like)#1
    list_res.append(coin)#2
    list_res.append(collect)#3
    list_res.append(update_time)#4
    list_res.append(title_v)#5
    list_res.append(pic_url)#6
    list_res.append(desc)#7
    list_res.append(str(s))#8
    print(list_res)
    message = sharemsg_to_txt(list_res)
    return message
#列表转化为文字
def sharemsg_to_txt(list_res):
    message = "IWS主人说聪明的猫猫要会翻译JSON的喵！\n"\
              "[CQ:image,file=" + list_res[6] + "]\n" \
              "标题：" + list_res[5] + "\n"\
              "UP主：" + list_res[0] + "\n更新时间：" + list_res[4] +"\n"\
              "点赞：" + list_res[1] + " 投币：" + list_res[2] + "\n收藏：" + list_res[3]+"\n"\
              "简介：" + list_res[7] +"\n"\
              "链接：" + list_res[8] +"\n"\
              "快去捧捧场的喵！不然我要闹了啊！ nya~~\n"    
    return message

#有道自然语言翻译
class Trans_Fuc(): 
    
    def __init__(self, APP_KEY = config_data['youdao']['APP_KEY'], APP_SECRET = config_data['youdao']['APP_SECRET']):
        reload(sys)
        self.YOUDAO_URL = 'https://openapi.youdao.com/api'
        self.APP_KEY = APP_KEY
        self.APP_SECRET = APP_SECRET
        os.environ['NO_PROXY'] = "https://openapi.youdao.com/api"
        self._to = 'zh-CHS'
    
    def set_to(self, T_to):
        self._to = T_to
        

    def encrypt(self, signStr):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(signStr.encode('utf-8'))
        return hash_algorithm.hexdigest()


    def truncate(self, q):
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


    def do_request(self, data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        os.environ['NO_PROXY'] = self.YOUDAO_URL
        return requests.post(self.YOUDAO_URL, data=data, headers=headers)


    def connect(self, input_str, _from = 'auto'):
        q = input_str
        data = {}
        data['from'] = _from
        data['to'] = self._to
        data['signType'] = 'v3'
        curtime = str(int(time.time()))
        data['curtime'] = curtime
        salt = str(uuid.uuid1())
        signStr = self.APP_KEY + self.truncate(q) + salt + curtime + self.APP_SECRET
        sign = self.encrypt(signStr)
        data['appKey'] = self.APP_KEY
        data['q'] = q
        data['salt'] = salt
        data['sign'] = sign
        data['vocabId'] = "您的用户词表ID"

        response = self.do_request(data)
        contentType = response.headers['Content-Type']
        if contentType == "audio/mp3":
            millis = int(round(time.time() * 1000))
            filePath = "合成的音频存储路径" + str(millis) + ".mp3"
            fo = open(filePath, 'wb')
            fo.write(response.content)
            fo.close()
        else:
            #print(response.content)
            target_str = response.json()['translation']
            return target_str
            #decoded_str = target_str.decode('utf-8')
            print(target_str)
            #print(decoded_str)

#有道图文
class Tran_Func_pic():

    def __init__(self, APP_KEY = config_data['youdao']['APP_KEY'], APP_SECRET = config_data['youdao']['APP_SECRET']):
        reload(sys)
        self.YOUDAO_URL = 'https://openapi.youdao.com/ocrtransapi'
        self.APP_KEY = APP_KEY
        self.APP_SECRET = APP_SECRET
        os.environ['NO_PROXY'] = "https://openapi.youdao.com/ocrtransapi"
    
    def truncate(self, q):
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


    def encrypt(self, signStr):
        hash_algorithm = hashlib.md5()
        hash_algorithm.update(signStr.encode('utf-8'))
        return hash_algorithm.hexdigest()


    def do_request(self, data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return requests.post(self.YOUDAO_URL, data=data, headers=headers)


    def connect(self, url):
        r = requests.get(url)
        path = config_data['youdao']['temp_path'] + "//tmp.png"
        with open(path, "wb") as ff: #改
            ff.write(r.content)
        ff.close()
        f = open(path, 'rb')  # 二进制方式打开图文件
        q = base64.b64encode(f.read()).decode('utf-8')  # 读取文件内容，转换为base64编码
        f.close()
        data = {}
        data['from'] = "auto"
        data['to'] = "zh-CHS"
        data['type'] = '1'
        data['q'] = q
        salt = str(uuid.uuid1())
        signStr = self.APP_KEY + q + salt + self.APP_SECRET
        sign = self.encrypt(signStr)
        data['appKey'] = self.APP_KEY
        data['salt'] = salt
        data['sign'] = sign

        response = self.do_request(data)
        # print(response.content)
        res = []
        for item in response.json()['resRegions']:
            #print(item["tranContent"])
            res.append(item["tranContent"])
        return res
    
TR = Trans_Fuc()
TRP = Tran_Func_pic()  #file://E://1.gif    file://E://QQ机器人官方API3.5版202303191824//QQ机器人官方API3.5版//QBot//data//emoticon//special//fkiss//1.gif
#管理员指令系统
def system_command(msg,session,uid,gid):
    msg = msg.strip();
    sc_flag = False
    sc_flag = admin_check(uid)
    if msg.startswith('机型变更'):
        if sc_flag:
            requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/_set_model_show",
                      params={'model': "go-cqhttp", 'model_show': "go-cqhttp (黑色)"})
            return "understand"
        else :
            return "您没有权限执行此项root指令！如果您也是管理员，请咨询我的开发者IWS先生，谢谢！"
    elif msg == "kiss me":
        if sc_flag:
            return  "好的主人喵，请您闭上眼睛【害羞】\n"+"[CQ:image,file=file:///" + config_data['qq_bot']['emoticon_path'] +"\\special\\fkiss\\1.gif]"
        else:
            return  "[CQ:image,file=file:///" + rand_zayu() +"]"
    elif msg.startswith('撤回'):
        ban_qq = re.match(r'撤回\[CQ:at,qq=(.*)\]',msg)
        if ban_qq == None:
            return "快点快点撤回啦！"
        ban_qq = int(ban_qq.groups()[0]) 
        if str(ban_qq) not in session['message_history'].keys():
            return "我们要等他说话才能撤回哦！主人~"
        elif len(session['message_history'][str(ban_qq)]) == 0:
            return "我们要等他说话才能撤回哦！主人~"
        if sc_flag and gid != '0':
            message_id = session['message_history'][str(ban_qq)][len(session['message_history'][str(ban_qq)])-1]['message_id']
            session['message_history'][str(ban_qq)].pop()
            print("执行撤回！")
            requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/delete_msg",
                          params={'message_id': int(message_id)})
            return "understand"
        elif gid == '0':
            return "此命令无法执行！"
        else :
            return "您没有权限执行此项root指令！如果您也是管理员，请咨询我的开发者IWS先生，谢谢！"   
    elif msg.startswith('repeat'):
        ban_qq = re.match(r'repeat\[CQ:at,qq=(.*)\]',msg)
        if ban_qq == None:
            return "装傻~【呆滞】"
        ban_qq = int(ban_qq.groups()[0]) 
        if str(ban_qq) not in session['message_history'].keys():
            return "呜~我真的找不到关于这位群友的消息啊，我该怎么办呢，主人【可怜】"
        elif len(session['message_history'][str(ban_qq)]) == 0:
            return "我们要等他说话才能复读哦！主人~"
        if sc_flag and gid != '0':
           # message_id = session['message_history'][str(ban_qq)][len(session['message_history'][str(ban_qq)])-1]['message_id']
            print("执行复读！")
            return  session['message_history'][str(ban_qq)][len(session['message_history'][str(ban_qq)])-1]['content']                  
        elif gid == '0':
            return "此命令无法执行！"
        else :
            return "您没有权限执行此项root指令！如果您也是管理员，请咨询我的开发者IWS先生，谢谢！"
    elif msg.startswith('岁月史书'): 
        rem_len = RM_LS
        ban_qq = re.match(r'岁月史书\[CQ:at,qq=(.*)\] far',msg)
        far_flag = True
        if ban_qq == None:
            far_flag = False
            ban_qq = re.match(r'岁月史书\[CQ:at,qq=(.*)\]',msg)
            if ban_qq == None:
                return "装傻~【呆滞】"
        ban_qq = int(ban_qq.groups()[0]) 
        if str(ban_qq) not in session['message_history'].keys():
            return "呜~我真的找不到关于这位群友的消息啊，我该怎么办呢，主人【可怜】"
        elif len(session['message_history'][str(ban_qq)]) == 0:
            return "我们要等他说话才能记下来哦！主人~"       
        if sc_flag and gid != '0':
            print("执行回忆！")
            history = "好的主人，让我找一下下。（笨拙的翻书声）\n"
            if far_flag == False and len(session['message_history'][str(ban_qq)]) <= rem_len :
                far_flag = True
                history = "好的主人，但是这位群友的记忆我不是很多喵。（笨拙的翻书声）\n"
            for i in range(len(session['message_history'][str(ban_qq)])):
                if far_flag == True and i < rem_len :
                    history = history + "Info["+str(i)+"]:  "+session['message_history'][str(ban_qq)][i]['content']+"\n\n"
                elif far_flag == False and i >= rem_len :
                    history = history + "Info["+str(i)+"]:  "+session['message_history'][str(ban_qq)][i]['content']+"\n\n"
            history = history + "（合上书本）以上就是我关于这位群友的记忆了。但是主人，用我的能力查询这种东西会不会不太好？【担忧】"
            return history
        elif gid == '0':
            return "此命令无法执行！"
        else :
            return "您没有权限执行此项root指令！如果您也是管理员，请咨询我的开发者IWS先生，谢谢！"            
    elif msg.startswith('禁言'):
        #print(msg)
        ban_qq = re.match(r'禁言\[CQ:at,qq=(.*)\]',msg)
        #print(ban_qq)
        if ban_qq == None:
            return "怕怕【委屈】"
        ban_qq = int(ban_qq.groups()[0]) 
        if sc_flag and gid != '0':
            requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/set_group_ban",
                      params={'group_id': int(gid) , 'user_id': ban_qq , 'duration' : 60})
            return "understand"
        elif gid == '0':
            return "此命令无法执行！"
        else :
            return "您没有权限执行此项root指令！如果您也是管理员，请咨询我的开发者IWS先生，谢谢！"
    elif msg.startswith('全体禁言-f'):
        if sc_flag and gid != '0':
            requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/set_group_whole_ban",
                      params={'group_id': int(gid) , 'enable': True})   
        elif gid == '0':
            return "此命令无法执行！"
        else :
            return "您没有权限执行此项root指令！如果您也是管理员，请咨询我的开发者IWS先生，谢谢！"
    elif msg.startswith('灯火管制'):
        if sc_flag:
            session['group_reply'] = False
            return 'understand'
        else :
            return "您没有权限执行此项root指令！如果您也是管理员，请咨询我的开发者IWS先生，谢谢！"
    elif msg.startswith('失温管制'):
        if sc_flag:
            session['group_reply'] = True
            return 'understand'
        else :
            return "您没有权限执行此项root指令！如果您也是管理员，请咨询我的开发者IWS先生，谢谢！"       
    else :
        return "!noroot"
# 生成图片
def genImg(message):
    img = text_to_image(message)
    filename = str(uuid.uuid1()) + ".png"
    filepath = config_data['qq_bot']['image_path'] + str(os.path.sep) + filename
    img.save(filepath)
    print("图片生成完毕: " + filepath)
    return filename


# 发送私聊消息方法 uid为qq号，message为消息内容
def send_private_message(uid, message, send_voice_private, send_emoticon):
    try:
        message = message.strip()
        messaget = message
        if send_voice_private:  # 如果开启了语音发送
            voice_path = asyncio.run(
                gen_speech(message, config_data['qq_bot']['voice'], config_data['qq_bot']['voice_path']))
            message = "[CQ:record,file=file:///" + voice_path + "]"
        if len(message) >= config_data['qq_bot']['max_length'] and not send_voice_private:  # 如果消息长度超过限制，转成图片发送
            pic_path = genImg(message)
            message = "[CQ:image,file=" + pic_path + "]"
        if send_voice_private and send_emoticon:#在需要发语音的情况下处理表情包
            messaget = emoticon_add(messaget)
        elif send_emoticon :#在无语音的情况下处理表情包
            message = emoticon_add(message)
        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_private_msg",
                            params={'user_id': int(uid), 'message': message}).json()
        if send_voice_private:
            res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_private_msg", params={'user_id': int(uid), 'message': messaget}
                                ).json()
        if res["status"] == "ok":
            print("私聊消息发送成功")
        else:
            print(res)
            print("私聊消息发送失败，错误信息：" + str(res['wording']))

    except Exception as error:
        print("私聊消息发送失败")
        print(error)


# 发送私聊消息方法 uid为qq号，pic_path为图片地址
def send_private_message_image(uid, pic_path, msg):
    try:
        message = "[CQ:image,file=" + pic_path + "]"
        if msg != "":
            message = msg + '\n' + message
        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_private_msg",
                            params={'user_id': int(uid), 'message': message}).json()
        if res["status"] == "ok":
            print("私聊消息发送成功")
        else:
            print(res)
            print("私聊消息发送失败，错误信息：" + str(res['wording']))

    except Exception as error:
        print("私聊消息发送失败")
        print(error)


# 发送群消息方法
def send_group_message(gid, message, uid, send_voice,send_emoticon):
    try:
        message = message.strip()
        messaget = message
        if send_voice:  # 如果开启了语音发送
            voice_path = asyncio.run(
                gen_speech(message, config_data['qq_bot']['voice'], config_data['qq_bot']['voice_path']))
            message = "[CQ:record,file=file:///" + voice_path + "]"
        if len(message) >= config_data['qq_bot']['max_length'] and not send_voice:  # 如果消息长度超过限制，转成图片发送
            pic_path = genImg(message)
            message = "[CQ:image,file=" + pic_path + "]"
        if send_voice and send_emoticon:#在需要发语音的情况下处理表情包
            messaget = emoticon_add(messaget)
        elif send_emoticon :#在无语音的情况下处理表情包
            message = emoticon_add(message)
        if not send_voice:
            if uid != '':
                message = str('[CQ:at,qq=%s]\n' % uid) + message  # @发言人
        else:
            if uid != '':
                messaget = str('[CQ:at,qq=%s]\n' % uid) + messaget  # @发言人
        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                            params={'group_id': int(gid), 'message': message}).json()
        if send_voice:
            res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                                params={'group_id': int(gid), 'message': messaget}).json()
        if res["status"] == "ok":
            print("群消息发送成功")
        else:
            print("群消息发送失败，错误信息：" + str(res['wording']))
    except Exception as error:
        print("群消息发送失败")
        print(error)
positive_word = ("微笑","愉悦","喜悦","兴奋","舒适","期待","快乐","开心","崇敬","赞许","满足","蹭蹭头","摇尾巴","舒服","好奇","高兴","乐意","愿意","美好","喜欢","享受","幸福","愉快","谢谢","温柔")
awkward_word = ("愣","不理解","不明白","不知道","困惑","疑惑","无奈","惊讶","不太明白","不太理解","不太清楚","不是很清楚","不是很理解","不懂","奇怪")
passive_word = ("心疼","悲伤","低声","难过","关心","害怕","失落",)

def emoticon_add(message): #对消息内容进行再处理，特指表情包 ##
    #case 积极emo
    fix_message = message
    pre_emoticon_path = config_data['qq_bot']['emoticon_path']
    det_path = '/home/rock/py/py/emoticon'
    emoticon_path = config_data['qq_bot']['emoticon_path']
    if '原神' in message :
        emoticon_path = emoticon_path + "\\special\\yuanshen"
        det_path += '/special/yuanshen'
        all_content=os.listdir(det_path)
        choose_tag = random.randint(1,len(all_content))
        emoticon_path = emoticon_path +"//"+ str(choose_tag) + ".jpg"
        return "[CQ:image,file=file:///" + emoticon_path + "]"
    for i in range(len(passive_word)):
        if pre_emoticon_path != emoticon_path :  
            break;
        if awkward_word[i] in message :
            gorj_flag_pos = random.randint(1, 4)
            if gorj_flag_pos == 3 : #如果判定为gif
                det_path += "/passive_gif"
                emoticon_path = emoticon_path + "\\passive_gif"
                all_content=os.listdir(det_path)
                choose_tag = random.randint(1,len(all_content))
                emoticon_path = emoticon_path +"\\"+ str(choose_tag) + ".gif"
            else :
                det_path += "/passive_jpg"
                emoticon_path = emoticon_path + "\\passive_jpg"
                all_content=os.listdir(det_path)
                choose_tag = random.randint(1,len(all_content))
                emoticon_path = emoticon_path +"\\"+ str(choose_tag) + ".jpg"  
            break;  
    for i in range(len(awkward_word)):
        if pre_emoticon_path != emoticon_path :  #与原生串不相同，直接跳过
            break;
        if awkward_word[i] in message :
            gorj_flag_pos = random.randint(1, 4)
            if gorj_flag_pos == 3 : #如果判定为gif
                det_path += "/awkward_gif"
                emoticon_path = emoticon_path + "\\awkward_gif"
                all_content=os.listdir(det_path)
                choose_tag = random.randint(1,len(all_content))
                emoticon_path = emoticon_path +"\\"+ str(choose_tag) + ".gif"
            else :
                det_path += "/awkward_jpg"
                emoticon_path = emoticon_path + "\\awkward_jpg"
                all_content=os.listdir(det_path)
                choose_tag = random.randint(1,len(all_content))
                emoticon_path = emoticon_path +"\\"+ str(choose_tag) + ".jpg"  
            break;
    for i in range(len(positive_word)):
        if pre_emoticon_path != emoticon_path :  #与原生串不相同，直接跳过
            break;
        if positive_word[i] in message :
            gorj_flag_pos = random.randint(1, 4)
            if gorj_flag_pos == 3 : #如果判定为gif
                det_path += "/positive_gif"
                emoticon_path = emoticon_path + "\\positive_gif"
                all_content=os.listdir(det_path)
                choose_tag = random.randint(1,len(all_content))
                emoticon_path = emoticon_path +"\\"+ str(choose_tag) + ".gif"
            else :#如果是jpg
                det_path += "/positive_jpg"
                emoticon_path = emoticon_path + "\\positive_jpg"
                all_content=os.listdir(det_path)
                choose_tag = random.randint(1,len(all_content))
                emoticon_path = emoticon_path +"\\"+ str(choose_tag) + ".jpg"
            break;
    if pre_emoticon_path == emoticon_path :  
        return message
    else :
        fix_message = fix_message + "[CQ:image,file=file:///" + emoticon_path + "]"
        print(fix_message)
        return fix_message
    
    
    
# 发送群消息图片方法
def send_group_message_image(gid, pic_path, uid, msg):
    try:
        message = "[CQ:image,file=" + pic_path + "]"
        if msg != "":
            message = msg + '\n' + message
        message = str('[CQ:at,qq=%s]\n' % uid) + message  # @发言人
        res = requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/send_group_msg",
                            params={'group_id': int(gid), 'message': message}).json()
        if res["status"] == "ok":
            print("群消息发送成功")
        else:
            print("群消息发送失败，错误信息：" + str(res['wording']))
    except Exception as error:
        print("群消息发送失败")
        print(error)


# 处理好友请求
def set_friend_add_request(flag, approve):
    try:
        requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/set_friend_add_request",
                      params={'flag': flag, 'approve': approve})
        print("处理好友申请成功")
    except:
        print("处理好友申请失败")


# 处理邀请加群请求
def set_group_invite_request(flag, approve):
    try:
        requests.post(url=config_data['qq_bot']['cqhttp_url'] + "/set_group_add_request",
                      params={'flag': flag, 'sub_type': 'invite', 'approve': approve})
        print("处理群申请成功")
    except:
        print("处理群申请失败")


# openai生成图片
def get_openai_image(des):
    openai.api_key = config_data['openai']['api_key'][current_key_index]
    response = openai.Image.create(
        prompt=des,
        n=1,
        size=config_data['openai']['img_size']
    )
    image_url = response['data'][0]['url']
    print('图像已生成')
    print(image_url)
    return image_url


# 查询账户余额
def get_credit_summary():
    url = "https://gpt.lucent.blog/dashboard/billing/credit_grants"
    res = requests.get(url, headers={
        "Authorization": f"Bearer " + config_data['openai']['api_key'][current_key_index]
    }, timeout=60).json()
    return res


# 查询账户余额
def get_credit_summary_by_index(index):
    url = "https://gpt.lucent.blog/dashboard/billing/credit_grants"
    res = requests.get(url, headers={
        "Authorization": f"Bearer " + config_data['openai']['api_key'][index]
    }, timeout=60).json()
    return res['total_available']

# 新查询账号余额
def get_credit_new(index):
    apikey = config_data['openai']['api_key'][index]
    subscription_url = "https://gpt.lucent.blog/dashboard/billing/subscription"
    headers = {"Authorization": "Bearer " + apikey,"Content-Type": "application/json"}
    subscription_response = requests.get(subscription_url, headers=headers)
    if subscription_response.status_code == 200:
        data = subscription_response.json()
        total = data.get("hard_limit_usd")
    else:
        return subscription_response.text

    # end_date设置为今天日期+1
    end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(end_date)
    start_date = (datetime.now() + timedelta(days=-30)).strftime("%Y-%m-%d")
    print(start_date)
    billing_url = "https://gpt.lucent.blog/dashboard/billing/usage?start_date="+ start_date + "&end_date=" + end_date
    billing_response = requests.get(billing_url, headers=headers)
    if billing_response.status_code == 200:
        data = billing_response.json()
        total_usage = data.get("total_usage") / 100
        daily_costs = data.get("daily_costs")
        days = min(5, len(daily_costs))
        recent = f"##### 最近{days}天使用情况  \n"
        for i in range(days):
            cur = daily_costs[-i-1]
            date = datetime.fromtimestamp(cur.get("timestamp")).strftime("%Y-%m-%d")
            line_items = cur.get("line_items")
            cost = 0
            for item in line_items:
                cost += item.get("cost")
            recent += f"\t{date}\t{cost / 100} \n"
    else:
        return billing_response.text

    return      "Key"+str(index)+": "\
                f" 总额:\t{total:.4f}  \n" \
                f" 已用:\t{total_usage:.4f}  \n" \
                f" 剩余:\t{total-total_usage:.4f}  \n" \
                f"\n"+recent+"\n"

# 计算消息使用的tokens数量
def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        num_tokens = 0
        for message in messages:
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # 如果name字段存在，role字段会被忽略
                    num_tokens += -1  # role字段是必填项，并且占用1token
        num_tokens += 2
        return num_tokens
    else:
        raise NotImplementedError(f"""当前模型不支持tokens计算: {model}.""")
def get_credit_summary_by_index_(index):
#    url = "https://gpt.lucent.blog/dashboard/billing/credit_grants"
#    res = requests.get(url, headers={
#        "Authorization": f"Bearer " + config_data['openai']['api_key'][index]
#    }, timeout=60).json()
#    return res['total_available']

    apikey = config_data['openai']['api_key'][index]
    subscription_url = "https://api.openai.com/v1/dashboard/billing/subscription"
    headers = {
        "Authorization": "Bearer " + apikey,
        "Content-Type": "application/json"
    }
    subscription_response = requests.get(subscription_url, headers=headers)
    if subscription_response.status_code == 200:
        data = subscription_response.json()
        total = data.get("hard_limit_usd")
    else:
        return subscription_response.text

    # end_date设置为今天日期+1
    end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    billing_url = "https://api.openai.com/v1/dashboard/billing/usage?start_date=2023-01-02&end_date=" + end_date
    billing_response = requests.get(billing_url, headers=headers)
    if billing_response.status_code == 200:
        data = billing_response.json()
        total_usage = data.get("total_usage") / 100
    else:
        return billing_response.text

    return f" 剩余:\t{float(total)-float(total_usage):.4f}  \n"

# sd生成图片,这里只做了正向提示词，其他参数自己加
def sd_img(msg,session):
    res = get_stable_diffusion_img({
        "prompt": msg,
        "width": 768,
        "height": 512,
        "num_inference_steps": 50,
        "guidance_scale": 10,
        "negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, 3 legs, extra limbs",
        "scheduler": "K_EULER_ANCESTRAL",
        "seed": random.randint(1, 9999999)
    }, config_data['replicate']['api_token'],session['models_index'])
    return res[0]

def weather_get():
    session = get_chat_session('P' + str(1950916064))
    msg_text = chat("帮主人分析以下的天气数据并返回一份通俗易懂的猫娘报道" + weather(), session,str(1950916064))  # 将消息转发给ChatGPT处理
    if msg_text != '!no!ans!':
        send_private_message(str(1950916064), msg_text, session['send_voice_private'],session['send_emoticon']) 
    return msg_text
def goodnight():
    session = get_chat_session('P' + str(1950916064))
    msg_text = chat("晚安啦，乖猫猫要早早睡哦！和主人道晚安吧！", session,str(1950916064))  # 将消息转发给ChatGPT处理
    if msg_text != '!no!ans!':
        send_private_message(str(1950916064), msg_text, session['send_voice_private'],session['send_emoticon']) 
def goodnighttoall():
    session = get_chat_session('G' + str(1061777689))
    msg_text = chat("晚安啦，乖猫猫要早早睡哦！和大家道晚安吧！", session,str(1950916064),str(1061777689))  # 将消息转发给ChatGPT处理
    if msg_text != '!no!ans!':
        send_group_message(str(1061777689), msg_text, '', session['send_voice'],session['send_emoticon'])         
        

def sys_det_start():
    try:
        camera_process = subprocess.Popen(["python", "/home/rock/xietong2/demo.py"], stdin=subprocess.PIPE)
        return camera_process
    except Exception as e:
        print(f"Error running camera.py: {str(e)}")
        return None    
def sys_det_end():  
    global camera_process
    if camera_process is not None and camera_process.poll() is None:
        try:
            camera_process.send_signal(signal.SIGUSR1)
            camera_process.wait()
            print("程序已经停止。")
        except AttributeError:
            print("严重错误，无法发送信号给任务进程。")
    else :
        print("程序未在运行中。")

def gen_frames():
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

if __name__ == '__main__':
    server.run(port=5555, host='0.0.0.0', use_reloader=False)

