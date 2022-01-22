"""Это лаунчер для запуска подпроцессов для сервера и клиентов"""

import subprocess

PROCESS = []


if __name__ == "__main__":
    while True:
        ACTION = input('Выберите действие: q - выход, '
                       's - запустить сервер,  c - запустить клиенты, x - закрыть все окна: ')

        if ACTION == 'q':
            break
        elif ACTION == 's':
            PROCESS.append(subprocess.Popen('python server.py',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif ACTION == 'c':

            PROCESS.append(subprocess.Popen('python client.py -n user_1 -p 123456',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
            PROCESS.append(subprocess.Popen('python client.py -n user_2 -p 123456',
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif ACTION == 'x':
            while PROCESS:
                VICTIM = PROCESS.pop()
                VICTIM.kill()
