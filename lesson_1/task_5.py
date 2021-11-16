# Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из байтовового в строковый
# тип на кириллице.

import subprocess
import chardet


def decode_result(result):
    result_codepage = chardet.detect(result)
    result = result.decode(result_codepage['encoding']).encode('utf-8')
    return result.decode('utf-8')


if __name__ == "__main__":
    args = ['ping', '-n', '3', 'yandex.ru']
    YA_ping = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in YA_ping.stdout:
        print(decode_result(line))

    args = ['ping', '-n', '3', 'youtube.com']
    YT_ping = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in YT_ping.stdout:
        print(decode_result(line))
