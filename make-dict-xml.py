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
    print("Usage: %s  <warodai path>" % sys.argv[0])


def get_index_xml(value: str, title: str, yomi=None) -> str:
    if yomi:
        return f"""<d:index d:value="{value}" d:title="{title}" d:yomi="{yomi}"/>"""
    else:
        return f"""<d:index d:value="{value}" d:title="{title}"/>"""


def get_lines_xml(lines: list[str]) -> str:
    is_list = False
    ret = ""
    for line in lines:
        # fixup links
        line = line.replace('href="#', 'href="x-dictionary:d:')
        # add some decorations
        if line.startswith('1.'):
            is_list = True
            ret += f"""<div class="list">{line}</div>"""
        elif line.startswith('～'):
            match = re.search('^(～.+?) .+', line)
            if match:
                line = line.replace(match.group(1), f"<b>{match.group(1)}</b>")
            ret += f"""<div>{line}</div>"""
        elif line.startswith(': ～'):
            match = re.search('^: (～.+?) .+', line)
            if match:
                line = line.replace(match.group(1), f"<b>{match.group(1)}</b>")
            ret += f"""<div>{line}</div>"""
        elif re.match('\d+\): (～.+?) .+', line):
            match = re.search('\d+\): (～.+?) .+', line)
            if match:
                line = line.replace(match.group(1), f"<b>{match.group(1)}</b>")
            ret += f"""<div>{line}</div>"""
        else:
            ret += f"""<div>{line}</div>"""
        if is_list:
            # TODO close <ol>
            pass

    return ret


def get_entry_xml(title: str, file_id: str, index_xml: str, transcription: str, content: str, domain: str = None) -> str:
    return f"""<d:entry id="{file_id}" d:title="{title}">
        {index_xml}
        <div class="entry">
        <h1>{title} <small>{transcription}</small></h1>
        {'''<p class="domain">[''' + domain + "]</p>" if domain else ""}
        <p>{content}</p>
        </div>
        </d:entry>"""          


def get_entry_xml_from(path) -> str:
    file_id = pathlib.Path(path).stem
    with io.open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # とうきょう【東京】(То:кё:) [геогр.]〔005-28-71〕
        # TODO リューチューとう【リューチュー島･琉球島】(Рю:тю:-то:) [геогр.]〔008-71-42〕
        header = re.search('^(.+?)【(.+?)】\((.+?)\) \[(.+?)]〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
        if header:
            (hiragana, kanji, transcription, domain) = header.groups()[0:-1]
            title = f"{hiragana}【{kanji}】"
            index_xml = get_index_xml(hiragana, title)
            for k in kanji.split('･'):
                index_xml += get_index_xml(k, k, hiragana)
            return get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]), domain)
        else:
            # しょしょ【処々･所々･諸所･処処･所所】(сёсё)〔004-99-20〕
            # TODO ちょうへん, ちょうへんしょうせつ【長篇･長編, 長篇小説･長編小説】(тё:хэн, тё:хэн-сё:сэцу)〔009-26-70〕
            header = re.search('^(.+?)【(.+?)】\((.+?)\)〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
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
                header = re.search('^(.+?)\((.+?)\) \[(.+?)]〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                if header:
                    (katakana, transcription, domain) = header.groups()[0:-1]
                    title = f"{katakana}"
                    index_xml = ""
                    index_xml += get_index_xml(katakana, title)
                    if "・" in katakana:
                        index_xml += get_index_xml(katakana.replace("・", ""), title)
                    # TODO add hiragana to index
                    if file_id == "005-28-71":
                        sys.stderr.write(get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]), domain))
                    return get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]), domain)
                else:
                    # ボヘミア(бохэмиа)〔000-40-00〕
                    # TODO :スプリント, スプリント・レース(сўпуринто, сўпуринто-рэ:су)〔003-01-61〕
                    header = re.search('^(.+?)\((.+?)\)〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                    if header:
                        (katakana, transcription) = header.groups()[0:-1]
                        title = f"{katakana}"
                        index_xml = ""
                        index_xml += get_index_xml(katakana, title)
                        if "・" in katakana:
                            index_xml += get_index_xml(katakana.replace("・", ""), title)
                        # TODO add hiragana to index
                        return get_entry_xml(title, file_id, index_xml, transcription, get_lines_xml(lines[1:]))
                    else:
                        print("regex mismatch")
                        print(lines)
                        exit(1)
        return None


def iterate_files(path) -> None:
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
