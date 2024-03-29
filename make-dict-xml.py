#!/usr/bin/env python3
import io
import os
import pathlib
import re
import sys


def print_xml_header() -> None:
    print(
        """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:wd="http://www.wadoku.de/xml/entry"
            xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">""")


def print_xml_footer() -> None:
    print("""</d:dictionary>""")


def print_usage() -> None:
    print("Converts a directory of warodai files to xml data")
    print("suitable for Apple's Dictionary Development Kit.")
    print("Usage: %s  <warodai path>" % sys.argv[0])


def get_index_xml(value: str, title: str, yomi: str = None) -> str:
    if yomi:
        return f"""<d:index d:value="{value}" d:title="{title}" d:yomi="{yomi}"/>"""
    else:
        return f"""<d:index d:value="{value}" d:title="{title}"/>"""


def get_lines_xml(lines: list[str]) -> str:
    is_list = False
    ret: str = ""
    for line in lines:
        # fixup links
        line = line.replace('href="#', 'href="x-dictionary:r:')
        # add some decorations
        if line.startswith('1.'):
            is_list = True
            ret += f"""<div class="list">{line}</div>"""
        elif line.startswith('～'):
            match = re.search(r'^(～.+?) .+', line)
            if match:
                line = line.replace(match.group(1), f"<b>{match.group(1)}</b>")
            ret += f"""<div>{line}</div>"""
        elif line.startswith(': ～'):
            match = re.search(r'^: (～.+?) .+', line)
            if match:
                line = line.replace(match.group(1), f"<b>{match.group(1)}</b>")
            ret += f"""<div>{line}</div>"""
        elif re.match(r'\d+\): (～.+?) .+', line):
            match = re.search(r'\d+\): (～.+?) .+', line)
            if match:
                line = line.replace(match.group(1), f"<b>{match.group(1)}</b>")
            ret += f"""<div>{line}</div>"""
        else:
            ret += f"""<div>{line}</div>"""
        if is_list:
            # TODO close <ol>
            pass

    return ret


def get_entry_xml(title: str,
                  file_id: str,
                  index_xml: str,
                  transcription: str,
                  content: str,
                  domain: str = None) -> str:
    return f"""<d:entry id="{file_id}" d:title="{title}">
        {index_xml}
        <div class="entry">
        <h1>{title} <small>{transcription}</small></h1>
        {f'''<p class="domain">[{domain}]</p>''' if domain else ""}
        <p>{content}</p>
        </div>
        </d:entry>"""


def is_katakana(char: chr) -> bool:
    return ord(u'\u30a0') <= ord(char) <= ord(u"\u30ff")


def contains_katakana(text: str) -> bool:
    for char in text:
        if is_katakana(char):
            return True
    return False


def katakana_to_hiragana(text: str) -> str:
    result: str = ""
    for i in range(len(text)):
        result += chr(ord(text[i]) - 0x60) if is_katakana(text[i]) else text[i]
    return result


def get_entry_xml_from(path: str) -> str:
    file_id = pathlib.Path(path).stem
    with io.open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # とうきょう【東京】(То:кё:) [геогр.]〔005-28-71〕
        # リューチューとう【リューチュー島･琉球島】(Рю:тю:-то:) [геогр.]〔008-71-42〕
        header = re.search(r'^(.+?)【(.+?)】\((.+?)\) \[(.+?)]〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
        if header:
            (hiragana, kanji, transcription, domain) = header.groups()[0:-1]
            if contains_katakana(hiragana):
                hiragana = katakana_to_hiragana(hiragana)
            title = f"{hiragana}【{kanji}】"
            index_xml = get_index_xml(hiragana, title)
            for k in kanji.split('･'):
                index_xml += get_index_xml(k, k, hiragana)
            return get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]), domain)
        else:
            # しょしょ【処々･所々･諸所･処処･所所】(сёсё)〔004-99-20〕
            # TODO ちょうへん, ちょうへんしょうせつ【長篇･長編, 長篇小説･長編小説】(тё:хэн, тё:хэн-сё:сэцу)〔009-26-70〕
            header = re.search(r'^(.+?)【(.+?)】\((.+?)\)〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
            if not header:
                # leniently handle format errors
                header = re.search(r'^(.+?)【(.+?)】\((.+?)\)\s*〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                if header:
                    print("format error detected", file=sys.stderr)
                    print(lines, file=sys.stderr)
            if header:
                (hiragana, kanji, transcription) = header.groups()[0:-1]
                title = f"{hiragana}【{kanji}】"
                index_xml = get_index_xml(hiragana, title)
                for k in kanji.split('･'):
                    index_xml += get_index_xml(k, k, hiragana)
                return get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]))
            else:
                # カルカッタ(Карукатта) [геогр.]〔000-28-00〕
                # TODO ケソン, ケソン・シティー(Кэсон, Кэсон-Сити:) [геогр.]〔005-06-52〕
                header = re.search(r'^(.+?)\((.+?)\) \[(.+?)]〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                if header:
                    (katakana, transcription, domain) = header.groups()[0:-1]
                    hiragana: str = katakana_to_hiragana(katakana)
                    title: str = f"{katakana}"
                    index_xml: str = ""
                    index_xml += get_index_xml(katakana, title)
                    index_xml += get_index_xml(hiragana, title)
                    if "・" in katakana:
                        index_xml += get_index_xml(katakana.replace("・", ""), title)
                        index_xml += get_index_xml(hiragana.replace("・", ""), title)
                    if file_id == "005-28-71":
                        print(
                            get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]), domain),
                            file=sys.stderr)
                    return get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]), domain)
                else:
                    # ボヘミア(бохэмиа)〔000-40-00〕
                    # TODO :スプリント, スプリント・レース(сўпуринто, сўпуринто-рэ:су)〔003-01-61〕
                    header = re.search(r'^(.+?)\((.+?)\)〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                    if header:
                        (katakana, transcription) = header.groups()[0:-1]
                        hiragana: str = katakana_to_hiragana(katakana)
                        title: str = f"{katakana}"
                        index_xml: str = ""
                        index_xml += get_index_xml(katakana, title)
                        index_xml += get_index_xml(hiragana, title)
                        if "・" in katakana:
                            index_xml += get_index_xml(katakana.replace("・", ""), title)
                            index_xml += get_index_xml(hiragana.replace("・", ""), title)
                        return get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]))
                    else:
                        print("regex mismatch", file=sys.stderr)
                        print(lines, file=sys.stderr)
                        exit(2)
        return None


def iterate_files(path: str) -> None:
    with os.scandir(path) as it:
        for entry in it:
            if entry.name.endswith(".txt") and entry.is_file():
                xml = get_entry_xml_from(entry.path)
                if xml:
                    print(xml)

            elif entry.is_dir():
                iterate_files(entry.path)


# main program

if len(sys.argv) < 2:
    print_usage()
    exit(1)

directory = sys.argv[1]

print_xml_header()
iterate_files(directory)
print_xml_footer()
