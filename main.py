import os
import re

import requests
import whisper
from bs4 import BeautifulSoup
from openai import OpenAI
from tqdm import tqdm

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
    text_file = change_file_extension(audio_file, ".txt")
    open(text_file, "w", encoding='utf-8').write(text)
    return text_file


def _proofread(text: str):
    client = OpenAI(
        api_key=config['api_key'],
        base_url=config['base_url'],
    )
    messages = [
        {
            "role": "user",
            "content": f"""
你是一位精通中文的文稿编辑，擅长对已经记录下来的文字稿进行润色、修改、校对和整理，以确保文稿的准确性、流畅性和专业性。我希望你能帮我将速记员记录下的文字稿调整语法、拼写、标点符号，优化句子结构，甚至对内容进行适当的增删和调整，以使文稿更加清晰、连贯和符合预期的风格要求。

规则：
- 结合上下文修正一些速记员的拼音错误，例如：“它们” -> “他们”。
- 保留特定的英文术语或名字，并在其前后加上空格，例如："中 UN 文"。
- 去除多余的口语外表达，例如：“嗯”，“然后”，“OK”。
- 分成两次编辑，并且打印每一次结果：
1. 只调整语法、拼音错误、标点符号，优化句子结构，但不改变原文的意思，不增加新的内容
2. 根据第一次调整的结果再次编辑，遵守原意的前提下让内容更通俗易懂，去除没必要的换行，符合书面语表达习惯

以下是需要润色的文稿，请按照上面的规则打印两次编辑结果：
{text}
"""
        }]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=1.1,
        stream=False,
    )
    output = response.choices[0].message.content
    proofread_text = output.split("### 第二次编辑结果")[1]
    return proofread_text


def split_text(text: str):
    lines = text.split('\n')
    chunk = ''
    for line in lines:
        chunk += line + '\n'
        if len(chunk) > 1000:
            yield chunk
            chunk = ''
    if chunk:
        yield chunk


def proofread(text_file: str):
    input_text = open(text_file, "r", encoding='utf-8').read()

    proofread_text = ""
    pbar = tqdm(total=len(input_text))
    for chunk in split_text(input_text):
        proofread_text += _proofread(chunk)
        pbar.update(len(chunk))
    pbar.close()

    proofread_file = add_file_surfix(text_file, "proofread")
    open(proofread_file, "w", encoding='utf-8').write(proofread_text)
    return proofread_file


if "__main__" == __name__:
    url = input("请输入小宇宙链接：")
    data = parse_url(url)
    audio_file = download_audio(data['title'], data['audio_url'])
    text_file = sst(audio_file)
    # text_file = 'workspace/No 21 厌学，或许不仅仅是厌学：深入探讨孩子的内心世界.txt'
    proofread_file = proofread(text_file)
    print(f"文稿润色完成，结果保存在 {proofread_file}")
