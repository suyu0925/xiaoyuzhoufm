# xiaoyuzhoufm
小宇宙FM的音频下载，与AI总结

## 准备

使用 python 3.9。

```sh
pip install -r ./requirements.txt
```

安装`ffmpeg`，windows上推荐使用[scoop](https://scoop.sh/)：`scoop install ffmpeg`。

如果有GPU，安装[带cuda的torch](https://pytorch.org/get-started/locally/#start-locally)，运行速度可以快一点。

## 配置

添加环境变量`OPENAI_API_KEY`和`OPENAI_BASE_URL`，可以添加`.env`文件。

## 使用

```sh
python main.py
```

输入小宇宙节目的链接，然后等待运行完毕。
