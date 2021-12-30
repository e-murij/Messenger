"""Программа-клиент"""
import argparse
import sys
import json
import socket
import threading
import time
import logging
import log.client_log_config
from Messenger.errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from Messenger.common.variables import *
from Messenger.common.utils import get_message, send_message
from Messenger.descriptors import Port
from Messenger.metaclasses import ClientMaker
from Messenger.db_client import ClientStorage

# Объект блокировки сокета и работы с базой данных
sock_lock = threading.Lock()
database_lock = threading.Lock()


def print_help():
    """Функция выводящяя справку по использованию"""
    print('Поддерживаемые команды:')
    print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
    print('help - вывести подсказки по командам')
    print('exit - выход из программы')
    print('history - история сообщений')
    print('contacts - список контактов')
    print('edit - редактирование списка контактов')


# Класс поток взаимодействия с пользователем, запрашивает команды, отправляет сообщения
class UserInterfaceThread(threading.Thread, metaclass=ClientMaker):
    def __init__(self, sock, username, database):
        super().__init__()
        self.CLIENT_LOGGER = logging.getLogger('client')
        self.daemon = True
        self.sock = sock
        self.username = username
        self.database = database

    def run(self):
        print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                print_help()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except Exception as err:
                        print(err)
                        pass
                    print('Завершение соединения.')
                    self.CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            # Список контактов
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()
            # история сообщений.
            elif command == 'history':
                self.print_history()
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def create_message(self):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер
        :return:
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        # Проверим, что получатель существует
        with database_lock:
            if not self.database.check_user(to_user):
                self.CLIENT_LOGGER.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_user}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        self.CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        # Сохраняем сообщения для истории
        with database_lock:
            self.database.save_message(self.username, to_user, message)
        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                self.CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
            except OSError as err:
                if err.errno:
                    self.CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    self.CLIENT_LOGGER.error('Не удалось передать сообщение. Таймаут соединения')

    def create_exit_message(self):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }

    # Функция выводящяя историю сообщений
    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.username)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.username)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    # Функция изменеия контактов
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    self.CLIENT_LOGGER.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        self.add_contact(edit)
                    except ServerError:
                        self.CLIENT_LOGGER.error('Не удалось отправить информацию на сервер.')

    # Функция добавления пользователя в контакт лист
    def add_contact(self, contact):
        self.CLIENT_LOGGER.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        send_message(self.sock, req)
        ans = get_message(self.sock)
        if RESPONSE in ans and ans[RESPONSE] == 200:
            pass
        else:
            raise ServerError('Ошибка создания контакта')
        print('Удачное создание контакта.')


# Класс поток - обработчик сообщений других пользователей, поступающих с сервера
class ReceiverThread(threading.Thread, metaclass=ClientMaker):
    def __init__(self, sock, username, database):
        super().__init__()
        self.CLIENT_LOGGER = logging.getLogger('client')
        self.daemon = True
        self.sock = sock
        self.username = username
        self.database = database

    def run(self):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то второй поток может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                except IncorrectDataRecivedError:
                    self.CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    if err.errno:
                        self.CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError):
                    self.CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                    break
                    # Если пакет корретно получен выводим в консоль и записываем в базу.
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                            and MESSAGE_TEXT in message and message[DESTINATION] == self.username:
                        print(f'\n Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        # Захватываем работу с базой данных и сохраняем в неё сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER], self.username, message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                self.CLIENT_LOGGER.error('Ошибка взаимодействия с базой данных')
                        self.CLIENT_LOGGER.info(
                            f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    else:
                        self.CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')


class Client:
    server_port = Port()

    def __init__(self):
        self.CLIENT_LOGGER = logging.getLogger('client')
        self.server_address, self.server_port, self.client_name = self.arg_parser()
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

        return server_address, server_port, client_name

    def client_running(self):
        if not self.client_name:
            self.client_name = input('Введите имя пользователя: ')
        print(f'Имя пользователя: {self.client_name}')
        self.CLIENT_LOGGER.info(
            f'Запущен клиент с парамертами: адрес сервера: {self.server_address}, '
            f'порт: {self.server_port}, имя пользовотеля: {self.client_name}')
        try:
            self.transport.settimeout(1)
            self.transport.connect((self.server_address, self.server_port))
            message_to_server = self.create_presence()
            send_message(self.transport, message_to_server)
            message_from_server = get_message(self.transport)
            answer = self.process_ans(message_from_server)
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
            # Инициализация БД
            self.database = ClientStorage(self.client_name)
            self.database_load()
            # Если соединение с сервером установлено корректно,
            # запускаем процесс приёма сообщений
            receiver = ReceiverThread(self.transport, self.client_name, self.database)
            receiver.start()

            # затем запускаем отправку сообщений и взаимодействие с пользователем.
            user_interface = UserInterfaceThread(self.transport, self.client_name, self.database)
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

    def create_presence(self):
        """
        Функция генерирует запрос о присутствии клиента
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

    # Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера.
    def database_load(self):
        # Загружаем список известных пользователей
        try:
            users_list = self.user_list_request()
        except ServerError:
            self.CLIENT_LOGGER.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users(users_list)

        # Загружаем список контактов
        try:
            contacts_list = self.contacts_list_request()
        except ServerError:
            self.CLIENT_LOGGER.error('Ошибка запроса списка контактов.')
        else:
            for contact in contacts_list:
                self.database.add_contact(contact)

    # Функция запроса списка известных пользователей
    def user_list_request(self):
        self.CLIENT_LOGGER.debug(f'Запрос списка известных пользователей {self.client_name}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }
        send_message(self.transport, req)
        ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            return ans[LIST_INFO]
        else:
            raise ServerError

    # Функция запрос контакт листа
    def contacts_list_request(self):
        self.CLIENT_LOGGER.debug(f'Запрос контакт листа для пользователя {self.client_name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.client_name
        }
        self.CLIENT_LOGGER.debug(f'Сформирован запрос {req}')
        send_message(self.transport, req)
        ans = get_message(self.transport)
        self.CLIENT_LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            return ans[LIST_INFO]
        else:
            raise ServerError


if __name__ == '__main__':
    client = Client()
    client.client_running()
