# Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое программирование», «сокет»,
# «декоратор». Проверить кодировку файла по умолчанию.
# Принудительно открыть файл в формате Unicode и вывести его содержимое.

import locale
import chardet

print(locale.getpreferredencoding())

with open('test_file.txt', 'rb') as f:
    text = f.read()
    print(text)
    print(chardet.detect(text))

with open('test_file.txt', encoding='utf-8') as f:
    print(f.read())
