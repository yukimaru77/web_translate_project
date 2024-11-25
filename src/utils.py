from bs4 import BeautifulSoup, NavigableString
from bs4.element import Comment
import re
import json
from bs4 import NavigableString, Comment
from openai import OpenAI
from bs4.element import NavigableString

# .envファイルからAPI_KEYを取得
import os
from dotenv import load_dotenv

load_dotenv()


# ブロック要素とインライン要素のリストを定義
BLOCK_ELEMENTS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "details",
    "dialog",
    "dir",
    "div",
    "dl",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hgroup",
    "hr",
    "li",
    "main",
    "menu",
    "nav",
    "noscript",
    "ol",
    "p",
    "section",
    "table",
    "tbody",
    "tfoot",
    "thead",
    "tr",
    "ul",
}

INLINE_ELEMENTS = {
    "a",
    "abbr",
    "b",
    "bdi",
    "bdo",
    "br",
    "cite",
    "data",
    "dfn",
    "em",
    "embed",
    "i",
    "iframe",
    "img",
    "input",
    "ins",
    "kbd",
    "label",
    "mark",
    "meter",
    "object",
    "output",
    "picture",
    "progress",
    "q",
    "ruby",
    "rp",
    "rt",
    "s",
    "samp",
    "script",
    "small",
    "span",
    "strong",
    "sub",
    "summary",
    "sup",
    "time",
    "u",
    "var",
    "video",
    "wbr",
}

ignored_tags = {
    "script",
    "style",
    "svg",
    "canvas",
    "iframe",
    "noscript",
    "embed",
    "object",
    "applet",
    "video",
    "audio",
    "picture",
    "source",
    "track",
    "head",
    "meta",
    "pre",
}


def iterate_nodes(node, ignored_tags=None):
    """カスタムノードイテレーター"""
    if ignored_tags is None:
        ignored_tags = {
            "script",
            "style",
            "svg",
            "canvas",
            "iframe",
            "noscript",
            "embed",
            "object",
            "applet",
            "video",
            "audio",
            "picture",
            "source",
            "track",
            "head",
            "meta",
            "pre",
            # "code",
        }

    # 自身が無視するタグの場合、再帰を中断
    if node.name in ignored_tags:
        return

    # 自身がNavigableStringの場合、yield
    if isinstance(node, NavigableString):
        yield node

    # 子ノードを再帰的に処理
    if hasattr(node, "children"):  # 子ノードを持つ場合のみ処理
        for child in node.children:
            yield from iterate_nodes(child, ignored_tags)


def contains_meaningful_characters(text):
    # 正規表現で a-z, A-Z, 0-9 の文字が含まれているか確認
    return bool(re.search(r"[a-zA-Z0-9\(\)（）]", text))


def create_text_nodes_map(soup, char_check=False):
    # soupのコピーを作成
    soup_copy = BeautifulSoup(str(soup), "html.parser")

    # テキストノードのマッピングを作成
    text_nodes_map = {}
    counter = 0

    # descendantsをzipで回す
    for node, node_copy in zip(
        iterate_nodes(soup.body if soup.body else soup),
        iterate_nodes(soup_copy.body if soup_copy.body else soup_copy),
    ):
        if char_check:
            if (
                isinstance(node, NavigableString)
                and isinstance(node_copy, NavigableString)
                and not isinstance(node, Comment)
                and not isinstance(node_copy, Comment)
                and node.text.strip()
                and contains_meaningful_characters(node.text)
                and contains_meaningful_characters(node_copy.text)
            ):
                text_nodes_map[f"node{counter}"] = (node, node_copy)
                counter += 1
        else:
            # 両方がテキストノードで、かつコメントではなく、空白でもない場合
            if (
                isinstance(node, NavigableString)
                and isinstance(node_copy, NavigableString)
                and not isinstance(node, Comment)
                and not isinstance(node_copy, Comment)
                and node.text.strip()
            ):
                text_nodes_map[f"node{counter}"] = (node, node_copy)
                counter += 1

    return soup_copy, text_nodes_map


def simplify_structure(node):
    """
    再帰的にHTMLの構造を簡略化する。
    子ノードの内容（innerHTML）を親ノードに移行する。
    """
    strongs = ["h1", "h2", "h3", "h4", "h5", "h6", "a", "p"]
    weaks = ["div", "span"]
    while True:
        # 実質的な子ノードを取得（空白テキストノードを除外）
        children = [child for child in node.children if not is_empty_text_node(child)]

        # 子要素が1つの場合、その内容を親ノードに移行
        if len(children) == 1:
            only_child = children[0]
            if only_child.name:  # タグの場合のみ処理
                # ブロック要素とインライン要素の変換が発生するかチェック
                if should_keep_structure(node, only_child):
                    break  # 変換が発生する場合は削除せず終了
                tag_name = node.name
                if node.name in strongs or only_child.name in weaks:
                    tag_name = node.name
                elif node.name in weaks or only_child.name in strongs:
                    tag_name = only_child.name
                # 子ノードのタグを削除
                node.clear()
                for child in list(only_child.children):
                    node.append(child)
                only_child.extract()
                node.name = tag_name
            else:
                break  # 子要素がタグでない場合、処理終了
        else:
            break  # 子ノードが1つでない場合、処理終了

    # 再帰処理: 子ノードに対して同じ操作を適用
    for child in list(node.children):  # リスト化して変更の影響を回避
        if child.name:  # タグの場合のみ再帰処理
            simplify_structure(child)


def should_keep_structure(parent, child):
    """
    ブロック要素とインライン要素の変換が発生するかを判定。
    """
    parent_tag = parent.name.lower() if parent.name else None
    child_tag = child.name.lower() if child.name else None
    # ただし、ul→li, ol→li, table→tr, tr→td, tbody→tr, thead→tr, tfoot→tr、pre→codeは例外(keep_structure=True)
    exceptions = {
        "ul": "li",
        "ol": "li",
        "table": "tr",
        "tr": "td",
        "tbody": "tr",
        "thead": "tr",
        "tfoot": "tr",
    }
    for key, value in exceptions.items():
        if parent_tag == key and child_tag == value:
            return True

    # ブロック要素からインライン要素、またはその逆の変換を判定
    ALL_ELEMENTS = BLOCK_ELEMENTS | INLINE_ELEMENTS
    # そもそも未知のタグ(またｈcodeやpreは意図的に未知にしている)や、ブロック要素とインライン要素の変換が発生するかチェック。発生するなら消さないのでTrue
    if not (parent_tag in ALL_ELEMENTS and child_tag in ALL_ELEMENTS) or (
        (parent_tag in BLOCK_ELEMENTS and child_tag in INLINE_ELEMENTS)
        or (parent_tag in INLINE_ELEMENTS and child_tag in BLOCK_ELEMENTS)
    ):
        return True
    return False


def is_empty_text_node(node):
    """
    テキストノードが空か（空白や改行のみか）を判定する。
    """
    return node.string is not None and node.string.strip() == ""


def crean_soup(soup):
    for tag in soup.find_all(ignored_tags):
        tag.decompose()
    for tag in soup.find_all(True):
        tag.attrs = {}
    simplify_structure(soup.body if soup.body else soup)
    # soup_copyから全てのタグを再帰的に取得し、.text.strip()が空なら削除
    for tag in soup.find_all(True):
        if tag.text.strip() == "":
            tag.decompose()
    simplify_structure(soup.body if soup.body else soup)


def make_Simplify_HTML(html, char_check=False):
    soup = BeautifulSoup(html, "html.parser")
    soup_copy, text_nodes_map = create_text_nodes_map(soup, char_check=char_check)
    crean_soup(soup_copy)
    return soup, soup_copy, text_nodes_map


from pydantic import BaseModel, Field
from typing import Annotated, Union, Literal, List, Dict

from pydantic import BaseModel, Field, root_validator, ValidationError


def create_translated_texts_class(elements: Dict) -> BaseModel:
    if len(elements) > 80:
        # 80個ごとに分割
        items = list(elements.items())
        elements_splits = [dict(items[i : i + 80]) for i in range(0, len(items), 80)]
    else:
        elements_splits = [elements]
    result = []
    for elements in elements_splits:
        # フィールド定義を動的に生成
        fields = {
            f"node{i}": (
                str,
                Field(
                    ...,
                    description=f"テキストノード(node{i})に対応する翻訳後テキストを格納するフィールド",
                ),
            )
            for i in range(len(elements))
        }

        # 型アノテーションとデフォルト値を分離
        annotations = {key: value[0] for key, value in fields.items()}  # 型
        defaults = {key: value[1] for key, value in fields.items()}  # デフォルト値

        # 動的にクラスを作成
        TranslatedHTML = type(
            "TranslatedHTML",
            (BaseModel,),
            {
                "__annotations__": annotations,  # 型アノテーション
                **defaults,  # フィールド定義
            },
        )
        result.append(TranslatedHTML)
    return result, elements_splits


def contains_meaningful_characters(text):
    # 正規表現で a-z, A-Z, 0-9 の文字が含まれているか確認
    return bool(re.search(r"[a-zA-Z0-9]", text))


def html_to_dict(element, char_check=False):
    """
    HTMLの要素を辞書構造に変換する関数（attributesなし、空文字列のテキストノードを除外）
    """
    ignored_tags = {
        "script",
        "style",
        "svg",
        "canvas",
        "iframe",
        "noscript",
        "embed",
        "object",
        "applet",
        "video",
        "audio",
        "picture",
        "source",
        "track",
        "head",
        "meta",
        "pre",
        # "code",
    }
    if (
        isinstance(element, NavigableString)
        and not isinstance(element, Comment)
        and (contains_meaningful_characters(element.text) if char_check else True)
    ):
        stripped_text = element.strip()
        stripped_text = {"node_type": "text_node", "text": stripped_text}
        return stripped_text
    elif isinstance(element, NavigableString):
        return None

    node_dict = {f"{element.name}_children": []}

    # 子要素を再帰的に処理
    for child in element.contents:
        if child.name in ignored_tags:
            continue
        child_dict = html_to_dict(child, char_check=char_check)
        if child_dict is not None:  # 空のノードは追加しない
            node_dict[f"{element.name}_children"].append(child_dict)
    if not node_dict[f"{element.name}_children"]:
        return None

    return node_dict


def modify_node_types(data, node_id=0, ancestor_tags=None):
    if ancestor_tags is None:
        ancestor_tags = []
    ignored_tags = {
        "script",
        "style",
        "svg",
        "canvas",
        "iframe",
        "noscript",
        "embed",
        "object",
        "applet",
        "video",
        "audio",
        "picture",
        "source",
        "track",
        "head",
        "meta",
        "pre",
        # "code",
    }
    if isinstance(data, dict):
        # 現在のタグを取得
        current_tag = list(data.keys())[0]
        if "_children" in current_tag:
            current_tag = current_tag.replace("_children", "")
        else:
            current_tag = None
        if current_tag:
            ancestor_tags.append(current_tag)

        if "node_type" in data and "text" in data:
            # 祖先に ignored_tagsのどれかがancestor_tagsに含まれている場合は、"node_without_id_text"キーを追加
            if any(tag in ignored_tags for tag in ancestor_tags):
                data["node_without_id_text"] = data.pop("text")
            else:
                data[f"node_id{node_id}_text"] = data.pop("text")
                node_id += 1
            # "node_type"キーを削除
            data.pop("node_type", None)

        for key, value in data.items():
            if isinstance(value, (dict, list)):
                node_id = modify_node_types(
                    value, node_id, ancestor_tags[:]
                )  # 祖先タグをコピーして渡す

        if current_tag:
            ancestor_tags.pop()  # 処理が終わったらタグを削除

    elif isinstance(data, list):
        for item in data:
            node_id = modify_node_types(
                item, node_id, ancestor_tags[:]
            )  # 祖先タグをコピーして渡す

    return node_id


def remove_empty_children(data, n=1):
    result = data  # 初期データ
    for i in range(n):  # 指定された回数だけ処理を繰り返す
        result = remove_empty_children_once(result)  # 1回分の処理を関数化
    return result


def remove_empty_children_once(data):
    if isinstance(data, dict):
        # 辞書の場合、再帰的に処理
        return {
            k: remove_empty_children_once(v)
            for k, v in data.items()
            if not (k.endswith("_children") and v == [])
        }
    elif isinstance(data, list):
        # リストの場合、再帰的に処理
        return [
            remove_empty_children_once(item)
            for item in data
            if remove_empty_children_once(item) != {}
        ]
    else:
        # その他の場合はそのまま返す
        return data


def remove_keys_from_dict(data, keys_to_remove):
    if isinstance(data, list):
        # リストの場合、各要素を再帰的に処理し、空辞書を削除
        return [
            remove_keys_from_dict(item, keys_to_remove)
            for item in data
            if remove_keys_from_dict(item, keys_to_remove) != {}
        ]
    elif isinstance(data, dict):
        # 辞書の場合、指定のキーを持つ辞書を削除
        if any(key in data for key in keys_to_remove):
            return {}
        else:
            return {
                k: remove_keys_from_dict(v, keys_to_remove) for k, v in data.items()
            }
    else:
        # その他の型はそのまま返す
        return data


def add_(data, keys_to_remove):
    if isinstance(data, list):
        # リストの場合、各要素を再帰的に処理し、空辞書を削除
        return [
            remove_keys_from_dict(item, keys_to_remove)
            for item in data
            if remove_keys_from_dict(item, keys_to_remove) != {}
        ]
    elif isinstance(data, dict):
        # 辞書の場合、指定のキーを持つ辞書を削除
        if any(key in data for key in keys_to_remove):
            return {}
        else:
            return {
                k: remove_keys_from_dict(v, keys_to_remove) for k, v in data.items()
            }
    else:
        # その他の型はそのまま返す
        return data


def translate_html(html, code=True, gpt_mini=False, class_name=None):
    soup2, soup_copy2, text_nodes_map2 = make_Simplify_HTML(html, char_check=True)
    BASE_DIR = "/workspaces/web_translate_project"
    # few show用
    html_path = BASE_DIR + "/data/test_html/test1_translated.html"
    with open(html_path, "r") as f:
        html_ = f.read()
    soup_translated, soup_copy_translated, text_nodes_map_translated = (
        make_Simplify_HTML(html_, char_check=True)
    )
    # few show用
    html_path = BASE_DIR + "/data/test_html/test1.html"
    with open(html_path, "r") as f:
        html_ = f.read()
    soup, soup_copy, text_nodes_map = make_Simplify_HTML(html_, char_check=True)
    results, elements_splits = create_translated_texts_class(text_nodes_map2)
    html_dict_soup_copy = html_to_dict(
        soup_copy.body if soup_copy.body else soup_copy, char_check=True
    )
    modify_node_types(html_dict_soup_copy)
    html_dict_soup_copy = remove_empty_children(html_dict_soup_copy)
    json_soup1_node_and_text = json.dumps(
        html_dict_soup_copy, ensure_ascii=False, indent=2
    )
    html_dict_soup_copy_translated = html_to_dict(
        (
            soup_copy_translated.body
            if soup_copy_translated.body
            else soup_copy_translated
        ),
        char_check=True,
    )
    modify_node_types(html_dict_soup_copy_translated)
    html_dict_soup_copy_translated = remove_empty_children(
        html_dict_soup_copy_translated
    )
    json_soup1_translated_node_and_text = json.dumps(
        html_dict_soup_copy_translated, ensure_ascii=False, indent=2
    )
    html_dict_soup_copy2 = html_to_dict(
        soup_copy2.body if soup_copy2.body else soup_copy2, char_check=True
    )
    modify_node_types(html_dict_soup_copy2)
    json_soup2_node_and_text = json.dumps(
        html_dict_soup_copy2, ensure_ascii=False, indent=2
    )
    client = OpenAI()
    events = []
    output = {}
    past_content = ""
    original_nodes = [tmp[1] for tmp in list(text_nodes_map2.values())]
    for i, (result, mini_dict) in enumerate(zip(results, elements_splits)):
        none_nodes = [NavigableString("") for _ in range(len(original_nodes))]
        print(f"{i+1}/{len(results)}")
        lower = i * 80
        upper = (i + 1) * 80 - 1
        max = len(original_nodes)
        upper = upper if upper < max else max
        print(lower, upper)
        for j in range(lower, upper):
            none_nodes[j] = original_nodes[j]
        for original_node, none_node in zip(original_nodes, none_nodes):
            original_node.replace_with(none_node)
        soup_copy3 = BeautifulSoup(str(soup_copy2), "html.parser")
        crean_soup(soup_copy3)
        html_dict_soup_copy3 = html_to_dict(
            soup_copy3.body if soup_copy3.body else soup_copy3, char_check=True
        )
        modify_node_types(html_dict_soup_copy3)
        json_soup3_node_and_text = json.dumps(
            html_dict_soup_copy3, ensure_ascii=False, indent=2
        )
        for original_node, none_node in zip(original_nodes, none_nodes):
            none_node.replace_with(original_node)
        prompt = f"""jsonファイルを翻訳してください。なお、JSONファイルのテキストノードを順番に読んでいった時に意味がつながるように工夫して翻訳してください。まずは具体例を示します。
## ユーザーからのjson入力例

```json
{json_soup1_node_and_text}
```

## 翻訳後のjson出力例

```json
{json_soup1_translated_node_and_text}
```

では、以下のjsonファイルを翻訳してください。なお、出力が長くなってしまうため今回はnodeID{lower}からnodeID{upper}までの翻訳結果を出力してください。なお、nodeIDはテキストノードのIDを示し手織り互いに連続しています。例えば、nodeID{lower}の次はmodeID{lower+1}です。なので、nodeIDを低い方から高い方に読んでいった際に日本語として意味がつながるように翻訳してください。
## ユーザーからの入力htmlと元の構造(json)

## 翻訳して欲しいjsonファイル
```json
{json_soup3_node_and_text}
```

{past_content}
"""
        # print(prompt)
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-11-20" if not gpt_mini else "gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "あなたにはHTMLをjson形式にしたものをユーザーから渡されます。そのjsonファイルのテキストノードを翻訳するのがあなたのタスクです。",
                },
                {"role": "user", "content": prompt},
            ],
            response_format=result,
        )

        event = completion.choices[0].message.parsed
        events.append(event)
        if i == 0:
            past_content = "また、このjsonファイルは以下の内容の続きとなります。文脈を理解するのに必要であれば参照してください。"
        for key in event.__annotations__:
            output[key] = event.__getattribute__(key)
            past_content += event.__getattribute__(key)
            # print(event.__getattribute__(key))
    texts = []
    for event in events:
        for key in event.__annotations__.keys():
            texts.append(event.__getattribute__(key))
    for text, node in zip(texts, text_nodes_map2.values()):
        node_origin = node[0]
        node_origin.replace_with(text)  # テキストを直接編集
    return str(soup2)
