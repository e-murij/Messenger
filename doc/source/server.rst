Server module
=================================================

Серверный модуль мессенджера. Обрабатывает словари - сообщения, хранит публичные ключи клиентов.

Использование

Модуль подерживает аргементы командной стороки:

1. -p - Порт на котором принимаются соединения
2. -a - Адрес с которого принимаются соединения.

Примеры использования:

``python server.py -p 8080``

*Запуск сервера на порту 8080*

``python server.py -a localhost``

*Запуск сервера принимающего только соединения с localhost*

server.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и функционал инициализации приложения.

server. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 2 элементов:

	* адрес с которого принимать соединения
	* порт

server. **config_load** ()
    Функция загрузки параметров конфигурации из ini файла.
    В случае отсутствия файла задаются параметры по умолчанию.

server_core.py
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: server.server_core.Server
	:members:

db_server.py
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: server.db_server.ServerStorage
	:members:

server_gui.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.server_gui.MainWindow
	:members:

.. autoclass:: server.server_gui.HistoryWindow
	:members:

.. autoclass:: server.server_gui.ConfigWindow
	:members:

.. autoclass:: server.server_gui.RegisterUser
	:members:

.. autoclass:: server.server_gui.DelUserDialog
	:members: