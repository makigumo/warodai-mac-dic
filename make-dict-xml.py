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
    ret: str = ""
    for line in lines:
        # fixup links
        line = line.replace('href="#', 'href="x-dictionary:r:')
        # add some decorations
        if line.startswith('1.'):
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

    return ret


def get_entry_xml(title: str | list[str],
                  file_id: str,
                  index_xml: set[str],
                  transcription: str | list[str],
                  content: str,
                  domain: str = None) -> str:
    if type(title) is str:
        titleline: str = f"<h1>{title} <small>{transcription}</small></h1>"
    else:
        titleline: str = ""
        for i in range(len(title)):
            titleline += f"<h1>{title[i]} <small>{transcription[i]}</small></h1>"

    title = title if type(title) is str else ", ".join(title)

    return f"""<d:entry id="{file_id}" d:title="{title}">
        {"\n        ".join(index_xml)}
        <div class="entry">
        {titleline}
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
    for i in text:
        result += chr(ord(i) - 0x60) if is_katakana(i) and i != 'ー' and i != '・' else i
    return result


def get_entry_xml_from(path: str) -> str:
    file_id = pathlib.Path(path).stem
    with io.open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        # とうきょう【東京】(То:кё:) [геогр.]〔005-28-71〕
        # リューチューとう【リューチュー島･琉球島】(Рю:тю:-то:) [геогр.]〔008-71-42〕
        # パリ, パリー【巴里】(Пари, Пари:) [геогр.]〔000-61-85〕
        header = re.search(r'^(.+?)【(.+?)】\((.+?)\) \[(.+?)]〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
        if header:
            (hiraganas, kanjis, transcriptions, domain) = header.groups()[0:-1]
            hiraganas_split = [h.strip() for h in hiraganas.split(',')]
            kanjis_split = [k.strip() for k in kanjis.split(',')]
            transcriptions_split = [t.strip() for t in transcriptions.split(',')]
            if len(hiraganas_split) != len(kanjis_split) != len(transcriptions_split):
                print("format error detected (inequal value count)", file=sys.stderr)
                print(lines, file=sys.stderr)
            if len(hiraganas_split) > len(kanjis_split):
                kanjis_split = [kanjis_split[0]] * len(hiraganas_split)
            if len(hiraganas_split) > len(transcriptions_split):
                transcriptions_split = [transcriptions_split[0]] * len(hiraganas_split)
            if len(kanjis_split) > len(transcriptions_split):
                transcriptions_split = [transcriptions_split[0]] * len(kanjis_split)

            hiraganas_extended = [x for xs in
                                  ([h, katakana_to_hiragana(h)] if contains_katakana(h) else h for h in hiraganas_split)
                                  for x in xs]

            titles = [f"{hiraganas_split[i]}【{kanjis_split[i]}】" for i in range(len(kanjis_split))]
            index_xml = set()
            for hiragana in hiraganas_extended:
                for kanji in kanjis_split:
                    title = f"{hiragana}【{kanji}】"
                    index_xml.add(get_index_xml(hiragana, title))
                    for k in kanji.split('･'):
                        index_xml.add(get_index_xml(k, k, hiragana))
                        index_xml.add(get_index_xml(k, title, hiragana))

            return get_entry_xml(titles, file_id, index_xml, transcriptions_split, get_lines_xml(lines[1:]), domain)
        else:
            # しょしょ【処々･所々･諸所･処処･所所】(сёсё)〔004-99-20〕
            # ちょうへん, ちょうへんしょうせつ【長篇･長編, 長篇小説･長編小説】(тё:хэн, тё:хэн-сё:сэцу)〔009-26-70〕
            # ろくろくび, ろくろっくび【轆轤首】(рокурокуби, рокуроккуби)〔000-15-28〕
            # おおよう, おうよう【大様, 鷹揚】(о:ё:)〔001-54-28〕
            header = re.search(r'^(.+?)【(.+?)】\((.+?)\)〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
            if not header:
                # leniently handle format errors
                header = re.search(r'^(.+?)【(.+?)】\((.+?)\)\s*〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                if header:
                    print("format error detected", file=sys.stderr)
                    print(lines, file=sys.stderr)
            if header:
                (hiraganas, kanjis, transcriptions) = header.groups()[0:-1]
                hiraganas_split = [h.strip() for h in hiraganas.split(',')]
                kanjis_split = [k.strip() for k in kanjis.split(',')]
                transcriptions_split = [t.strip() for t in transcriptions.split(',')]
                if len(hiraganas_split) != len(kanjis_split) != len(transcriptions_split):
                    print("format error detected (inequal value count)", file=sys.stderr)
                    print(lines, file=sys.stderr)
                if len(hiraganas_split) > len(kanjis_split):
                    kanjis_split = [kanjis_split[0]] * len(hiraganas_split)
                if len(hiraganas_split) > len(transcriptions_split):
                    transcriptions_split = [transcriptions_split[0]] * len(hiraganas_split)
                if len(kanjis_split) > len(transcriptions_split):
                    transcriptions_split = [transcriptions_split[0]] * len(kanjis_split)

                titles = [f"{hiraganas_split[i]}【{kanjis_split[i]}】" for i in range(len(kanjis_split))]
                index_xml = set()
                for hiragana in hiraganas_split:
                    for kanji in kanjis_split:
                        title = f"{hiragana}【{kanji}】"
                        index_xml.add(get_index_xml(hiragana, title))
                        for k in kanji.split('･'):
                            index_xml.add(get_index_xml(k, k, hiragana))
                return get_entry_xml(titles, file_id, index_xml, transcriptions_split,
                                     get_lines_xml(lines[1:]))
            else:
                # カルカッタ(Карукатта) [геогр.]〔000-28-00〕
                # ケソン, ケソン・シティー(Кэсон, Кэсон-Сити:) [геогр.]〔005-06-52〕
                header = re.search(r'^(.+?)\((.+?)\) \[(.+?)]〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                if header:
                    (katakanas, transcriptions, domain) = header.groups()[0:-1]
                    katakanas_split = [k.strip() for k in katakanas.split(',')]
                    transcriptions_split = [t.strip() for t in transcriptions.split(',')]
                    if (len(katakanas_split) != len(transcriptions_split)):
                        print("format error detected (inequal value count)", file=sys.stderr)
                        print(lines, file=sys.stderr)

                    index_xml = set()
                    for katakana in katakanas_split:
                        hiragana: str = katakana_to_hiragana(katakana)
                        title: str = f"{katakana}"
                        index_xml.add(get_index_xml(katakana, title))
                        index_xml.add(get_index_xml(hiragana, title))
                        if "・" in katakana:
                            index_xml.add(get_index_xml(katakana.replace("・", ""), title))
                            index_xml.add(get_index_xml(hiragana.replace("・", ""), title))
                    return get_entry_xml(katakanas_split, file_id, index_xml, transcriptions_split,
                                         get_lines_xml(lines[1:]), domain)
                else:
                    # ボヘミア(бохэмиа)〔000-40-00〕
                    # スプリント, スプリント・レース(сўпуринто, сўпуринто-рэ:су)〔003-01-61〕
                    # ぼーっと, ぼうっと(бо:тто)〔000-94-46〕
                    header = re.search(r'^(.+?)\((.+?)\)〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                    if header:
                        (katakanas, transcriptions) = header.groups()[0:-1]
                        katakanas_split = [k.strip() for k in katakanas.split(',')]
                        transcriptions_split = [t.strip() for t in transcriptions.split(',')]
                        if (len(katakanas_split) != len(transcriptions_split)):
                            print("format error detected (inequal value count)", file=sys.stderr)
                            print(lines, file=sys.stderr)
                            transcriptions_split = [transcriptions_split[0]] * len(katakanas_split)

                        index_xml = set()
                        for katakana in katakanas_split:
                            hiragana: str = katakana_to_hiragana(katakana)
                            title: str = f"{katakana}"
                            index_xml.add(get_index_xml(katakana, title))
                            index_xml.add(get_index_xml(hiragana, title))
                            if "・" in katakana:
                                index_xml.add(get_index_xml(katakana.replace("・", ""), title))
                                index_xml.add(get_index_xml(hiragana.replace("・", ""), title))
                        return get_entry_xml(katakanas_split, file_id, index_xml, transcriptions_split,
                                             get_lines_xml(lines[1:]))
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
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        exit(1)

    directory = sys.argv[1]

    print_xml_header()
    iterate_files(directory)
    print_xml_footer()
