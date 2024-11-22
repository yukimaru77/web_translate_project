# ベースイメージとしてPython 3.10を使用
FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

# 必要なツールのインストール
RUN apt-get update && apt-get install -y curl

# Node.js v20.xのインストール (特定バージョン: 20.18.0)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs=20.18.0-1nodesource1

# npmの指定バージョン (10.9.1) に更新
RUN npm install -g npm@10.9.1

# prettierのインストール (グローバル)
RUN npm install -g prettier
