"""Программа-сервер"""
import argparse
import select
import socket
import sys
import logging
import time

import Messenger.log.server_log_config
from Messenger.common.variables import ACTION, ACCOUNT_NAME, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, MESSAGE, SENDER, MESSAGE_TEXT, DESTINATION, RESPONSE_200, RESPONSE_400, \
    EXIT
from Messenger.decorators import Log
from common.utils import get_message, send_message


class Server:
    def __init__(self):
        self.SERVER_LOGGER = logging.getLogger('server')
        self.listen_address, self.listen_port = self.arg_parser()
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @Log()
    def arg_parser(self):
        """Парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-a', default='', nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        listen_address = namespace.a
        listen_port = namespace.p

        # проверка получения корретного номера порта для работы сервера.
        if not 1023 < listen_port < 65536:
            self.SERVER_LOGGER.critical(
                f'Попытка запуска сервера с указанием неподходящего порта '
                f'{listen_port}. Допустимы адреса с 1024 до 65535.')
            sys.exit(1)

        return listen_address, listen_port

    @Log()
    def server_running(self):
        self.transport.bind((self.listen_address, self.listen_port))
        self.transport.settimeout(1)
        self.transport.listen(MAX_CONNECTIONS)
        self.SERVER_LOGGER.info(f'Запущен сервер, порт для подключений: {self.listen_port}, '
                                f'адрес с которого принимаются подключения: {self.listen_address}. '
                                f'Если адрес не указан, принимаются соединения с любых адресов.')
        # список клиентов , очередь сообщений
        clients = []
        messages = []

        # Словарь, содержащий имена пользователей и их сокеты
        names = dict()

        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.transport.accept()
            except OSError:
                pass
            else:
                self.SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
                clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
            except OSError:
                pass
            # принимаем сообщения и если там есть сообщения,
            # кладём в словарь, если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message),
                                                    messages, client_with_message, clients, names)
                    except:
                        self.SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                                f'отключился от сервера.')
                        clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for mes in messages:
                try:
                    self.process_message(mes, names, send_data_lst)
                except Exception:
                    self.SERVER_LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                    clients.remove(names[mes[DESTINATION]])
                    del names[mes[DESTINATION]]
            messages.clear()

    @Log()
    def process_client_message(self, message, messages_list, client, clients, names):
        """
        Обработчик сообщений от клиентов, принимает словарь - сообщение от клинта,
        проверяет корректность, отправляет словарь-ответ для клиента с результатом приёма.
        ::param message:
        :param messages_list:
        :param client:
        :param clients:
        :param names:
        :return:
        """
        self.SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаем и отвечаем, если успех
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если такой пользователь ещё не зарегистрирован,
            # регистрируем, иначе отправляем ответ и завершаем соединение.
            if message[USER][ACCOUNT_NAME] not in names.keys():
                names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято'
                send_message(client, RESPONSE_400)
                clients.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
        elif ACTION in message and message[ACTION] == MESSAGE and \
                TIME in message and MESSAGE_TEXT in message and DESTINATION in message and SENDER in message:
            messages_list.append(message)
            return
        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            clients.remove(names[message[ACCOUNT_NAME]])
            names[message[ACCOUNT_NAME]].close()
            del names[message[ACCOUNT_NAME]]
            return
        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    @Log()
    def process_message(self, message, names, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
        список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
        :param message:
        :param names:
        :param listen_socks:
        :return:
        """
        if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
            send_message(names[message[DESTINATION]], message)
            self.SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                                    f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            self.SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')


if __name__ == '__main__':
    server = Server()
    server.server_running()
