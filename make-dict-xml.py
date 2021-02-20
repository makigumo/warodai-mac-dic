#!/usr/bin/env python3
import io
import os
import pathlib
import re
import sys


def print_xml_header():
    print(
        """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:wd="http://www.wadoku.de/xml/entry"
            xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">""")


def print_xml_footer():
    print("""</d:dictionary>""")


def print_usage():
    print("Usage: %s  <warodai path> [<output file>]" % sys.argv[0])


def get_index_xml(value, title, yomi=None):
    if yomi:
        return f"""<d:index d:value="{value}" d:title="{title}" d:yomi="{yomi}"/>"""
    else:
        return f"""<d:index d:value="{value}" d:title="{title}"/>"""


def get_lines_xml(lines: list[str]):
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


def get_entry_xml(path):
    file_id = pathlib.Path(path).stem
    with io.open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        header = re.search('^(.+?)【(.+?)】\((.+?)\)〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
        if header:
            (hiragana, kanji, transcription) = header.groups()[0:-1]
            title = f"{hiragana}【{kanji}】"
            kanji_index_xml = ""
            for k in kanji.split('･'):
                kanji_index_xml += get_index_xml(k, k, hiragana)
            ret = f"""<d:entry id="{file_id}" d:title="{title}">
{get_index_xml(hiragana, title)}{kanji_index_xml}
<div class="entry">
<h1>{title} <small>{transcription}</small></h1>
<p>{get_lines_xml(lines[1:])}</p>
</div>
</d:entry>"""
            return ret
        else:
            # カルカッタ(Карукатта) [геогр.]〔000-28-00〕
            header = re.search('^(.+?)\((.+?)\) \[(.+?)]〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
            if header:
                (katakana, transcription, domain) = header.groups()[0:-1]
                title = f"{katakana}"
                hiragana = katakana  # TODO add hiragana to index
                ret = f"""<d:entry id="{file_id}" d:title="{title}">
{get_index_xml(hiragana, title)}
<h1>{title} <small>{transcription}</small></h1>
<p>[{domain}]</p>
<p>{get_lines_xml(lines[1:])}</p>
</d:entry>"""
                return ret
            else:
                # ボヘミア(бохэмиа)〔000-40-00〕
                header = re.search('^(.+?)\((.+?)\)〔(\d{3}-\d{2}-\d{2})〕$', lines[0])
                if header:
                    (katakana, transcription) = header.groups()[0:-1]
                    title = f"{katakana}"
                    hiragana = katakana  # TODO
                    ret = f"""<d:entry id="{file_id}" d:title="{title}">
    {get_index_xml(hiragana, title)}
    <h1>{title} <small>{transcription}</small></h1>
    <p>{get_lines_xml(lines[1:])}</p>
    </d:entry>"""
                    return ret
                else:
                    print("regex mismatch")
                    print(lines)
                    exit(1)
        return None


def iterate_files(path):
    with os.scandir(path) as it:
        for entry in it:
            if entry.name.endswith(".txt") and entry.is_file():
                xml = get_entry_xml(entry.path)
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
