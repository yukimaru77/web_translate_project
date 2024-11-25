# Web サイト翻訳プロジェクト

このプロジェクトは、Web サイトの翻訳を行うためのものです。最近、ChatGPT の API オプションで Structured Output が出たのでこれを使えばできるんじゃない…？と思い、作成しました。

## 前提条件

以下のツールがローカル環境にインストールされていることを前提としています。

- [VSCode](https://code.visualstudio.com/) と [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) 拡張機能
- Docker（Dev Container を使用するため）

## 開発環境のセットアップ手順

このプロジェクトでは、VSCode の Dev Containers 機能を使用して、簡単に開発環境をセットアップできます。以下の手順でセットアップを行ってください。

1. **リポジトリのクローン**:
   プロジェクトをローカルにクローンします。
   ```bash
   git clone https://github.com/yukimaru77/web_translate_project.git
   cd web_translate_project
   ```
2. **VSCode でプロジェクトを開く**：
   VSCode でこのプロジェクトフォルダを開きます。

3. **Dev Container の起動**： VSCode のコマンドパレット（Ctrl+Shift+P）で「Reopen in Container」と入力し、開発コンテナ内でプロジェクトを再度開きます。これにより、開発環境が自動的にセットアップされます。

4. **依存関係のインストール**： コンテナ内で poetry install が自動的に実行され、プロジェクトの依存関係がインストールされます。依存関係に問題がある場合は、以下のコマンドで確認できます。
   ```bash
   poetry check
   poetry show
   ```

## 環境変数の設定

ルートディレクトリ直下に`.env`ファイルを作成します。`.env`ファイルには、以下の環境変数を設定する必要があります。

```bash
OPENAI_API_KEY = **************
```

## ディレクトリ構成

```bash
web_translate_project
├── README.md
├── data #テスト用のhtmlファイル
│   └── test_html
├── notebooks #notebookファイルを保存
├── poetry.lock
├── pyproject.toml
└── src
    └── utils.py
```

## 実行方法

### Poetry の仮想環境

開発中は Poetry の仮想環境が使われます。以下のコマンドを使用して仮想環境内でスクリプトを実行できます。

```bash
poetry run python your_script.py
```

依存関係の追加
新しい依存関係を追加する場合は、以下のコマンドを使用します。

```bash
poetry add package-name
```

開発用依存関係の追加
開発用依存関係を追加する場合は、`--group dev`オプションを付けます。

```bash
poetry add package-name --group dev
```

### 仮想環境の手動起動とスクリプトの実行

以下の手順で、Poetry の仮想環境を手動でアクティブにして、スクリプトを実行することもできます。

1. **仮想環境に入る**：
   Poetry の仮想環境を手動でアクティブにしたい場合、以下のコマンドを実行します。

   ```bash
   poetry shell
   ```

2. **スクリプトの実行**：
   以下のコマンドでスクリプトを実行します。

   ```bash
   python hoge.py
   ```

## 実行方法

現状は HTML を入力すると、翻訳された HTML が出力される関数`translate_html`が実装されています。デモは`notebooks/test.ipynb`にあります。

実行結果は HTML で吐き出されるため、現状は開発者ツールからコピペしないといけません。この辺りに操作は、Selenium や Chorome の拡張機能による自動化を検討しています。

## 実行例

web ページを丸々書き換えると、リロードが発生する場合(ChatGPT さん曰く meta タグの影響…？)があるので、現状は`<article class="markdown-body entry-content container-lg" itemprop="text">`の中身を翻訳した結果を表示します。(`data/test_html/test3.html`と`data/test_html/test3_translated.html`)

https://github.com/facebookresearch/sam2?tab=readme-ov-file#installation

翻訳後
![alt text](image.png)
