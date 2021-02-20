# Warodai for macOS

Scripts to convert the [Warodai file data](https://github.com/warodai/warodai-source) into an XML file suitable for Apple’s Dictionary Development Kit (DDK).

## Install

### Requirements

* DDK inside the `$HOME` directory (adjust in `Makefile`).
* a copy of the [Warodai file data](https://github.com/warodai/warodai-source).

### Steps

```sh
./make-dict-xml.py $WARODAI_SOURCE_DIR > warodai.xml
cat Warodai.plist.in | m4 -DYEAR=$(date +%Y) -DVERSION_DATE=$(date +%Y.%m.%d) > Warodai.plist
make
make install
```

## Links/Credits

* [和露大 Большой японско-русский словарь (БЯРС)](https://warodai.ru/)
