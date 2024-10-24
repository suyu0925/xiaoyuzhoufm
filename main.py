import re
import os

import requests
import whisper
from bs4 import BeautifulSoup
from openai import OpenAI

from config import config


def sanitize_filename(filename):
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized_filename = re.sub(illegal_chars, '', filename)
    return sanitized_filename


def change_file_extension(file_path: str, new_extension: str) -> str:
    directory, filename = os.path.split(file_path)
    name, extension = os.path.splitext(filename)
    new_file_path = os.path.join(directory, name + new_extension)
    return new_file_path


def add_file_surfix(file_path: str, surfix: str) -> str:
    directory, filename = os.path.split(file_path)
    name, extension = os.path.splitext(filename)
    new_file_path = os.path.join(directory, name + '_' + surfix + extension)
    return new_file_path


def parse_url(url: str):
    edge_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
    headers = {
        "User-Agent": edge_user_agent,
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    title_tag = soup.find('meta', {'property': 'og:title'})
    audio_tag = soup.find('meta', {'property': 'og:audio'})

    return {
        'title': title_tag['content'],
        'audio_url': audio_tag['content'],
    }


def download_audio(title: str, audio_url: str):
    response = requests.get(audio_url)
    os.makedirs('workspace', exist_ok=True)
    filename = os.path.join('workspace', f"{sanitize_filename(title)}.m4a")

    open(filename, "wb").write(response.content)

    print(f"音频文件 {filename} 下载完成！")
    return filename


def sst(audio_file: str):
    model = whisper.load_model("turbo")
    result = model.transcribe(audio_file, language="Mandarin")
    text = '\n'.join([x['text'] for x in result['segments']])
    output = change_file_extension(audio_file, ".txt")
    open(output, "w", encoding='utf-8').write(text)
    return audio_file


def proofhead(text_file: str):
    client = OpenAI(
        api_key=config['api_key'],
        base_url=config['base_url'],
    )
    messages = [
        {"role": "system", "content": "你是一个文字处理专家，擅长校正播客节目语音识别后的文章和要点总结。"},
    ]
    messages.append({
        "role": "user",
        "content": f"""
这是一档播客节目的语音识别结果，请将识别出的文字中的错别字修正，加上合适的标点符号，分成合适的段落，并去掉多余的语气词和重复口癖。
文章内容如下：
{open(text_file, "r", encoding='utf-8').read()}
"""})
    proofhead_text = ""
    index = 1
    finished = False
    while index < 30 and not finished:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=1.3,
            max_tokens=1024,
            stream=False,
        )
        messages.append(response.choices[0].message)
        index += 1
        proofhead_text += response.choices[0].message.content
        finished = response.choices[0].finish_reason == "stop"
        if not finished:
            messages.append({
                "role": "user",
                "content": "继续",
            })
        print(index, response)
    proofhead_file = add_file_surfix(text_file, "proofhead")
    open(proofhead_file, "w", encoding='utf-8').write(proofhead_text)
    return proofhead_file


def summary(text_file: str):
    client = OpenAI(
        api_key=config['api_key'],
        base_url=config['base_url'],
    )
    messages = [
        {"role": "system", "content": "你是一个文字处理专家，擅长校正语音识别出的文章和要点总结。"},
    ]
    messages.append({
        "role": "user",
        "content": f"""
总结下面文章中的要点。
文章内容如下：
{open(text_file, "r", encoding='utf-8').read()}
"""})
    summary_text = ""
    index = 1
    finished = False
    while index < 30 and not finished:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=1.3,
            max_tokens=1024,
            stream=False,
        )
        messages.append(response.choices[0].message)
        index += 1
        summary_text += response.choices[0].message.content
        finished = response.choices[0].finish_reason == "stop"
        if not finished:
            messages.append({
                "role": "user",
                "content": "继续",
            })
        print(index, response)
    summary_file = add_file_surfix(text_file, "summary")
    open(summary_file, "w", encoding='utf-8').write(summary_text)
    return summary_file


if "__main__" == __name__:
    url = input("请输入小宇宙链接：")
    data = parse_url(url)
    audio_file = download_audio(data['title'], data['audio_url'])
    text_file = sst(audio_file)
    proofhead_file = proofhead(text_file)
    summary_file = summary(proofhead_file)
