import requests
from requests.api import request
from sqlalchemy import create_engine
import time
import json
import re
import random
import datetime
from requests_toolbelt import MultipartEncoder
from PIL import Image, ImageDraw, ImageFont
import os
import matplotlib.font_manager as fm

'''
获得租户访问凭证
'''
def get_access():
    
    # 应用凭证
    id = ' '  # please fill in the blank
    secret = ' '  # please fill in the blank
    
    # 自建应用获取 tenant_access_token，以应用的身份操作API
    # 开发文档：https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
    ack = requests.post('https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/?app_id=%s&app_secret=%s' % (id,secret))

    tenant_access_token= ack.json()['tenant_access_token']  # 应用的租户访问凭证
    
    return tenant_access_token

'''
获得24小时群消息
'''
def message_extraction(tenant_access_token,oc):  # 得到24小时消息列表message
    # 截至目前时间，获取24h内的消息
    timeint = int(time.time()-3600*24)
    # etimeint = int(time.time()-3600*24*2)

    # 获取指定群聊“oc”的消息
    header = {
            'Content-Type':'application/json; charset=utf-8', 
            'Authorization':'Bearer %s' % tenant_access_token}  # 获取群聊历史消息的请求头

    page_token=''  # 初始化为空字符串
    messages=[]  # 一条一条读取，用于储存所有message的“items”项目中的一条消息，即信息的json结构（包含body、message_id等一系列信息）

    # 得到一条消息
    response = requests.get('https://open.feishu.cn/open-apis/im/v1/messages?page_size=1&page_token=%s&container_id_type=chat&container_id=%s&start_time=%d'%(page_token,oc,timeint), headers=header).json()
    # response = requests.get('https://open.feishu.cn/open-apis/im/v1/messages?page_size=1&page_token=%s&container_id_type=chat&container_id=%s&start_time=%d&end_time=%d'%(page_token,oc,timeint,etimeint), headers=header).json()

    message = response.get('data')

    if len(message['items'])!=0:  # 第一条消息，不为空时储存
        messages.append(message['items'][0])

    # 有下一条时 继续循环
    while(message['has_more']==True):
        page_token=message['page_token']
        message=requests.get('https://open.feishu.cn/open-apis/im/v1/messages?page_size=1&page_token=%s&container_id_type=chat&container_id=%s&start_time=%d'%(page_token,oc,timeint), headers=header).json().get('data')

        if len(message['items'])!=0:  # 该条信息不为空，则添加到信息列表中
            messages.append(message['items'][0])

    # print(response)
    # print(messages)

    return messages

'''
获取群成员open_id:name字典
'''
def user_name(tenant_access_token,oc):
    page_token=''
    member_list = []

    header = {
        'Content-Type':'application/json; charset=utf-8', 
        'Authorization':'Bearer %s' % tenant_access_token}  # 获取群聊成员的请求头

    members = requests.get('https://open.feishu.cn/open-apis/im/v1/chats/%s/members?member_id_type=open_id&page_token=%s&page_size=20' % (oc,page_token),headers=header).json().get('data')
    member_list += members['items']

    while members["has_more"]==True:
        page_token = members['page_token']  # 获取新页码

        # 翻页
        members = requests.get('https://open.feishu.cn/open-apis/im/v1/chats/%s/members?member_id_type=open_id&page_token=%s' % (oc,page_token),headers=header).json().get('data')
        member_list += members['items']  # 获取新用户

    # 转换为字典格式
    member_dict = {}
    for mem in member_list:
        member_dict[mem['member_id']]=mem['name']

    # print(member_dict)
    return member_dict

'''
获得生成的img_path
'''
def create_image(color):
    # 创建渐变背景图片
    width, height = 580, 200
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    # 定义起始颜色和结束颜色
    if color == 'orange' or color == 'yellow' or color == 'red' or color == 'carmine':
        start_color = (255, 160, 122)  # 粉色
        end_color = (240, 230, 140)   # 黄色
    if color == 'wathet' or color == 'indigo' or color == 'blue':
        end_color = (224,238,238)  # 
        start_color = (176,196,222)  # 
    if color == 'turquoise':
        start_color = (193,205,193)  # 
        end_color = (161,233,228)  # 
    if color == 'green':
        start_color = (193,255,193)  # 
        end_color = (143,188,143)  # 
    if color == 'purple' or color == 'violet':
        start_color = (230,230,250)  # 
        end_color = (176,196,222)  # 

    # 生成渐变色
    for y in range(height):
        r, g, b = [
            int(start + (end - start) * y / height)
            for start, end in zip(start_color, end_color)
        ]
        for x in range(width):
            draw.point((x, y), fill=(r, g, b))

    # 获取当前日期，用于自动改日期
    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%m%d")

    # 添加文字并调整文本大小和粗细
    text = "[Notifications--" + formatted_date + "]"
    font_size = 43  # 调整字体大小

    # 替换成你要搜索的字体名称
    font_name = "arialbd.ttf"

    # 获取系统字体列表
    system_fonts = fm.findSystemFonts()
    # print(system_fonts)

    find_font = 0

    for font_path in system_fonts:
        # print(font_path)
        if font_name in font_path:
            find_font = 1
            # print(font_path)
            break 

    # find_font = 0
    if find_font!=1:
        font_path = system_fonts[0]
    
    # print(find_font)
    # print(font_path)


    font = ImageFont.truetype(font_path, font_size)  # 使用arialbd.ttf选择粗体字体
    # font = ImageFont.load_default()

    # 获取文本的边界框（bbox）
    text_bbox = draw.textbbox((0, 0), text, font=font)

    # 计算文本的位置
    text_x = (width - text_bbox[2] - text_bbox[0]) / 2
    text_y = (height - text_bbox[3] - text_bbox[1]) / 2

    draw.text((text_x, text_y), text, fill='white', font=font)

    img_name = 'Notifications.png'
    image.save(img_name)

    # 获取当前工作目录
    current_directory = os.getcwd()

    # 构建图像文件的绝对路径
    image_path = os.path.join(current_directory, img_name)

    # 显示图片（可选）
    # image.show()
    # os.remove('high_resolution_image.png')

    return image_path    

'''
获得img_key
'''
def uploadImage(img_path,tenant_access_token):
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    form = {'image_type': 'message',
            'image': (open(img_path,'rb'))}  # 需要替换具体的path 
    multi_form = MultipartEncoder(form)
    headers = {
        'Authorization': 'Bearer %s' % tenant_access_token,  ## 获取tenant_access_token, 需要替换为实际的token
    }
    headers['Content-Type'] = multi_form.content_type
    response = requests.request("POST", url, headers=headers, data=multi_form).content
    # print(response.headers['X-Tt-Logid'])  # for debug or oncall
    # print(response)  # Print Response
    
    # 将 bytes 转换为字符串
    json_str = response.decode('utf-8')
    # 解析字符串为字典
    my_dict = json.loads(json_str)['data']['image_key']
    
    return my_dict


'''
生成消息卡片
'''
def message_structure(messages,member_dict,img_key,color):
    true = True

    ###### 卡片参数设置 ######
    # color_list=['blue','wathet','turquoise',
    #             'green','yellow','orange','red','carmine','violet','purple','indigo']  ## 颜色
    
    motto_list=[
        '——君子生非异也，善假于物也。',
        '——天行健，君子以自强不息。',
        '——见贤思齐焉，见不贤而内自省也。',
        '——君子欲讷于言而敏于行。',
        '——君子务本，本立而道生。',
        '——学而不思则罔，思而不学则殆。'
        ]  ## 格言列表
    

    # 重要信息提取判断字数阈值
    num_threshold = 150

    ###### 卡片组件 ######
    # 分割线组件
    devisionline = {
        "tag":"hr"
    }

    # “本日通知”组件
    part1head={
    "tag": "markdown",
    "content": "🍗**今日通知**"
    }

    # 获取当前日期，用于自动改日期
    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%m%d")

    ###### 初始化卡片 ######
    # color = random.choice(color_list)  # 随机选择颜色

    # 初始化卡片内容：题目，前言
    card = {
        "config": {
        "wide_screen_mode": true
        },
        "header": {
        "template": color,
        "title": {
            "tag": "plain_text",
            "i18n": {
            "zh_cn": "📣UCS群重点消息汇总-"+formatted_date
            }
        }
        },
        "i18n_elements": {
        "zh_cn":[
        {
            "alt": {
            "content": "",
            "tag": "plain_text"
            },
            "img_key": img_key,
            "tag": "img"
        },
        {
            "tag": "div",
            "text": {
            "content": "<at id=all></at> 一天结束啦！\n快来看看今天群里发生了什么吧！",
            "tag": "lark_md"
            }
        }
        ]
        }
    }
    
    # 插入分割符
    card['i18n_elements']['zh_cn'].append(devisionline)

    '''
    提取每日通知:
    @所有人的消息，包括text、图像、链接等，其中链接需要标蓝
    '''    
    ###### 本日通知提取 ######
    global text_flag
    global post_flag

    for message in messages:
        # "text"类型
        if message['msg_type']=='text' and message['deleted']==False:
            # 查询content中有无“@_all”的字段，若有则加入本日通知中
            # 格式转换
            text = message['body']['content']

            if text!='' and text!=None:
                text = json.loads(text)  # json格式，方便提取
                text = text['text']  # string格式

                if ("@_all" in text or len(text)>num_threshold):  # @全员或大于100字
                    # print(message)
                    # 去除“@_all”字样
                    result_string = text.replace("@_all", "")
                    
                    # 去除表情(以[]为标志)
                    result_string = re.sub(r'\[.*?\]', ' ', result_string)

                    # 识别、替换网址为markdown格式
                    url_pattern = r'https?://\S+|www.\.\S+'
                    urls = re.findall(url_pattern,result_string)

                    for url in urls:
                        alt_string = '<a href=\'%s\'></a>'% url
                        result_string = result_string.replace(url,alt_string)

                    # 识别、替换飞书视频会议链接
                    vc_pattern = r'vc\.feishu\.cn/j/\d{9}'
                    vcs = re.findall(vc_pattern, result_string)
                    for vc in vcs:
                        # alt_string = '<a href=\'%s\'></a>' % vc
                        alt_string = '[加入会议](%s)' % (vc)
                        result_string = result_string.replace(vc,alt_string)

                    # 识别、替换@usr_1为@name格式
                    if 'mentions' in message:
                        for mention in message['mentions']:
                            mention_name = mention['name']
                            mention_key = mention['key']
                            result_string = result_string.replace(mention_key,mention_name)

                    # 添加到卡片中
                    if result_string!='':
                        text = "🥁"+ result_string
                        card['i18n_elements']['zh_cn'].append({"tag":"markdown","content":text})
                        text_flag = 1
                    
                        # 添加作者名
                        m_key = message['sender']['id']
                        m_name = member_dict[m_key]
                        card['i18n_elements']['zh_cn'].append({
                                                                "tag": "markdown",
                                                                "content": " From "+ m_name,
                                                                "text_align": "right"
                                                            })
                        card['i18n_elements']['zh_cn'].append(devisionline)
        

        # "post"类型（参考数据结构：队列）
        if message['msg_type']=='post' and message['deleted']==False:
            
            # 统计字数
            num_flag = 0
            temp_text = ''
            temp_message = json.loads(message['body']['content'])['content']  # 一个数组
            for i in temp_message:
                for j in i:
                    if (j['tag']=='text') or (j['tag']=='a'):
                        temp_text += j['text']

            if len(temp_text)>num_threshold:
                num_flag = 1
            
            # 如果有“@所有人”的字样，或字数大于100，则开始处理此条信息
            if ("@所有人" in message['body']['content']) or ("@_all" in message['body']['content']) or num_flag==1:
                # 查询作者名
                m_key = message['sender']['id']
                m_name = member_dict[m_key]

                message = json.loads(message['body']['content'])  # 转换为json格式，方便提取
                title = message['title']
                message = message['content']  # 一个列表

                if (title!='') and (title!=' '):
                    united_text = '🥁**'+ title +'**\n'
                else:
                    united_text = '🥁'
                
                have_text = 1  # 用于标记目前是否有未输出的text
                
                for i in message:  # message为大列表，一条信息，i为小列表，内为字典
                    for j in i:  # 拆分为字典j，按照字典依次转换消息为卡片
                        if j['tag']=='text':
                            if (j['text']!='') and (j['text']!='- ') and (j['text'].isspace()!=True):  # 不填空的text
                                text = j['text']  # 提取文本内容
                                style = j['style']  # text的样式列表
                                
                                if 'bold' in style:  # 根据不同格式添加text
                                    united_text += '**'+ text +'** '
                                elif 'underline' in style:
                                    united_text += '<u>'+ text +'</u> '
                                elif 'lineThrough' in style:
                                    united_text += '~~'+ text +'~~ '
                                elif 'italic' in style:
                                    united_text += '*'+ text +'* '
                                else:
                                    united_text += text +' '

                                have_text = 1
                        
                        if j['tag']=='a':
                            url = j['href']  # 提取链接

                            if j['text']==url:
                                # 整理格式为markdown超链接
                                alt_string = '<a href=\'%s\'></a>'% url
                                url = url.replace(url,alt_string)
                                if len(united_text)!=0:
                                    united_text += '\n'
                                    united_text += url + '\n'
                            else:
                                # 或整理格式为文字链接
                                alt_string = '[%s](%s)' % (j['text'],url)
                                url = url.replace(url,alt_string)
                                united_text += url

                            have_text = 1

                        if j['tag']=='img':  # 为图片类型，则输出储存的文本，
                            if have_text:  # 若不为空，则将目前储存的文字写入消息卡片
                                card['i18n_elements']['zh_cn'].append({
                                    "tag":"markdown",
                                    "content":united_text
                                    })
                                # 文字清零
                                united_text = ''
                                have_text = 0
                            
                            # 将图片写入卡片
                            img_key = j['image_key']
                            if j['width']<278:  # 控制小图
                                card['i18n_elements']['zh_cn'].append({
                                    "tag":"img",
                                    "img_key":img_key,
                                    "alt": {
                                            "tag": "plain_text",
                                            "content": ""
                                            },
                                    "preview":true,
                                    "custom_width":278
                                })
                            else:
                                card['i18n_elements']['zh_cn'].append({
                                    "tag":"img",
                                    "img_key":img_key,
                                    "alt": {
                                            "tag": "plain_text",
                                            "content": ""
                                            },
                                    "preview":true,
                                    "custom_width":j['width']
                                })
                            
                    if (have_text) and (united_text.endswith('\n')==False):
                        united_text+='\n'

                # 若还有文本写入消息卡片
                if have_text:
                    card['i18n_elements']['zh_cn'].append({"tag":"markdown","content":united_text})
                
                # 最后加入发送者名
                card['i18n_elements']['zh_cn'].append({
                                                        "tag": "markdown",
                                                        "content": " From "+ m_name,
                                                        "text_align": "right"
                                                    })
                card['i18n_elements']['zh_cn'].append(devisionline)
                post_flag=1
        

    # # 模块结束后插入分割符
    # card['i18n_elements']['zh_cn'].append(devisionline)


    # 添加格言
    # 加入格言
    rmotto = random.choice(motto_list)
    motto = {
        "tag":"markdown",
        "content":"*" + rmotto + "*",
        "text_align":"right"
    }

    card['i18n_elements']['zh_cn'].append(motto)

    '''
    后续功能待完善...
    '''

    return card

# 将字典转换为JSON格式的字符串
def Card_to_JSON(card):
    json_str = json.dumps(card, indent=4, ensure_ascii=False)  # 使用indent参数来格式化输出
    
    return json_str

# 输出dict格式卡片的JSON
def output_json(card):
    json_str = Card_to_JSON(card)  # 可以直接输出
    print(json_str)




if __name__ == "__main__":
    
    tenant_access_token=get_access()
    # 群id（省略获取群id的步骤，可由“获取机器人所在群列表”开发文档得到）
    oc = ' '  # your own, group chat id, fill in the blank

    messages = message_extraction(tenant_access_token,oc)  # 群消息

    text_flag = 0
    post_flag = 0

    member_dict = user_name(tenant_access_token,oc)  # 群成员字典

    # 随机选择颜色，用于生成图片和卡片
    color_list=['blue','wathet','turquoise',
                'green','yellow','orange','red','carmine','violet','purple','indigo']
    color = random.choice(color_list)  # 随机选择颜色
    # color = 'purple'  # 调试用
    
    # 生成并上传图片
    img_path = create_image(color)
    img_key = uploadImage(img_path,tenant_access_token)

    card = message_structure(messages,member_dict,img_key,color)
    
    # 写card文件
    # with open("output.json", "w", encoding="utf-8") as f:
    #     json.dump(card, f, ensure_ascii=False, indent=4)

    # 发送消息卡片
    ## 替换为自定义机器人的webhook地址。
    url = " "  # your_own_webhook_address, fill in the blank

    ## 将消息卡片内容粘贴至此处。
    card = json.dumps(card)
    body =json.dumps({"msg_type": "interactive","card":card})
    headers = {"Content-Type":"application/json"}

    # 发送卡片
    if text_flag or post_flag:  # 至少有一部分不为空
        res = requests.post(url=url, data=body, headers=headers)
        # print(res.text)
    
    os.remove(img_path)