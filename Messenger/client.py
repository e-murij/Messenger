"""Программа-клиент"""
import argparse
import sys
import json
import socket
import threading
import time
import logging
import Messenger.log.client_log_config
from Messenger.decorators import Log
from Messenger.errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from Messenger.common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT
from common.utils import get_message, send_message


def print_help():
    """Функция выводящяя справку по использованию"""
    print('Поддерживаемые команды:')
    print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
    print('help - вывести подсказки по командам')
    print('exit - выход из программы')


class UserInterfaceThread(threading.Thread):
    """Класс поток взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""

    def __init__(self, sock, username):
        super().__init__()
        self.CLIENT_LOGGER = logging.getLogger('client')
        self.daemon = True
        self.sock = sock
        self.username = username

    @Log()
    def run(self):
        print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                print_help()
            elif command == 'exit':
                send_message(self.sock, self.create_exit_message())
                print('Завершение соединения.')
                self.CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    @Log()
    def create_message(self):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер
        :param sock:
        :return:
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        self.CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            self.CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
        except:
            self.CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    @Log()
    def create_exit_message(self):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }


class ReceiverThread(threading.Thread):
    """Класс поток - обработчик сообщений других пользователей, поступающих с сервера"""

    def __init__(self, sock, username):
        super().__init__()
        self.CLIENT_LOGGER = logging.getLogger('client')
        self.daemon = True
        self.sock = sock
        self.username = username

    @Log()
    def run(self):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.username:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    self.CLIENT_LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                            f'\n{message[MESSAGE_TEXT]}')
                else:
                    self.CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                self.CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                self.CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                break


class Client:
    def __init__(self):
        self.CLIENT_LOGGER = logging.getLogger('client')
        self.server_address, self.server_port, self.client_name = self.arg_parser()
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @Log()
    def arg_parser(self):
        """Создаём парсер аргументов коммандной строки
        и читаем параметры, возвращаем 3 параметра
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        server_address = namespace.addr
        server_port = namespace.port
        client_name = namespace.name

        # проверим подходящий номер порта
        if not 1023 < server_port < 65536:
            self.CLIENT_LOGGER.critical(
                f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
                f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
            sys.exit(1)

        return server_address, server_port, client_name

    @Log()
    def client_running(self):
        if not self.client_name:
            self.client_name = input('Введите имя пользователя: ')
        print(f'Имя пользователя: {self.client_name}')
        self.CLIENT_LOGGER.info(
            f'Запущен клиент с парамертами: адрес сервера: {self.server_address}, '
            f'порт: {self.server_port}, имя пользовотеля: {self.client_name}')
        try:
            self.transport.connect((self.server_address, self.server_port))
            message_to_server = self.create_presence()
            send_message(self.transport, message_to_server)
            answer = self.process_ans(get_message(self.transport))
            self.CLIENT_LOGGER.info(f'Принят ответ от сервера {answer}')
        except json.JSONDecodeError:
            self.CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except ConnectionRefusedError:
            self.CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {self.server_address}:{self.server_port}, '
                                        f'конечный компьютер отверг запрос на подключение.')
            sys.exit(1)
        except ReqFieldMissingError as missing_error:
            self.CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле '
                                     f'{missing_error.missing_field}')
            sys.exit(1)
        except ServerError as error:
            self.CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            sys.exit(1)
        else:
            # Если соединение с сервером установлено корректно,
            # запускаем процесс приёма сообщений
            receiver = ReceiverThread(self.transport, self.client_name)
            receiver.start()

            # затем запускаем отправку сообщений и взаимодействие с пользователем.
            user_interface = UserInterfaceThread(self.transport, self.client_name)
            user_interface.start()
            self.CLIENT_LOGGER.debug('Запущены процессы')

            # Watchdog основной цикл, если один из потоков завершён,
            # то значит или потеряно соединение или пользователь
            # ввёл exit. Поскольку все события обработываются в потоках,
            # достаточно просто завершить цикл.
            while True:
                time.sleep(1)
                if receiver.is_alive() and user_interface.is_alive():
                    continue
                break

    @Log()
    def create_presence(self):
        """
        Функция генерирует запрос о присутствии клиента
        :param account_name:
        :return:
        """
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name
            }
        }
        self.CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {self.client_name}')
        return out

    @Log()
    def process_ans(self, message):
        """
        Функция разбирает ответ сервера на сообщение клента о присутствии
        :param message:
        :return:
        """
        self.CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        self.CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле {RESPONSE}')
        raise ReqFieldMissingError(RESPONSE)


if __name__ == '__main__':
    client = Client()
    client.client_running()
