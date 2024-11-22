# Webサイト翻訳プロジェクト

このプロジェクトは、Webサイトの翻訳を行うためのものです。最近、ChatGPTのAPIオプションでStructured Outputが出たのでこれを使えばできるんじゃない…？と思い、作成しました。

## 前提条件
以下のツールがローカル環境にインストールされていることを前提としています。
- [VSCode](https://code.visualstudio.com/) と [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) 拡張機能
- Docker（Dev Containerを使用するため）

## 開発環境のセットアップ手順
このプロジェクトでは、VSCodeのDev Containers機能を使用して、簡単に開発環境をセットアップできます。以下の手順でセットアップを行ってください。

1. **リポジトリのクローン**:
   プロジェクトをローカルにクローンします。
   ```bash
   git clone https://github.com/your-repo/s-aci-criteria.git
   cd s-aci-criteria
    ```
2. **VSCodeでプロジェクトを開く**：
 VSCodeでこのプロジェクトフォルダを開きます。

3. **Dev Containerの起動**： VSCodeのコマンドパレット（Ctrl+Shift+P）で「Reopen in Container」と入力し、開発コンテナ内でプロジェクトを再度開きます。これにより、開発環境が自動的にセットアップされます。

4. **依存関係のインストール**： コンテナ内でpoetry installが自動的に実行され、プロジェクトの依存関係がインストールされます。依存関係に問題がある場合は、以下のコマンドで確認できます。
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

### Poetryの仮想環境
開発中はPoetryの仮想環境が使われます。以下のコマンドを使用して仮想環境内でスクリプトを実行できます。

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
以下の手順で、Poetryの仮想環境を手動でアクティブにして、スクリプトを実行することもできます。
1. **仮想環境に入る**：
   Poetryの仮想環境を手動でアクティブにしたい場合、以下のコマンドを実行します。

   ```bash
   poetry shell
    ```
2. **スクリプトの実行**：
    以下のコマンドでスクリプトを実行します。
    
    ```bash
    python hoge.py
    ```
<<<<<<< HEAD