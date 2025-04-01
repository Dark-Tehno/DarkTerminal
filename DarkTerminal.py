import datetime
import os
import shutil
import socket
import zipfile
import subprocess
import platform
import re
import locale
import hashlib
import threading
import signal
import sys


colors = {
    1: "white",
    2: "black",
    3: "red",
    4: "green",
    5: "yellow",
    6: "blue"
}

rgb = {
    "white": (37),
    "black": (30),
    "red": (31),
    "green": (32),
    "yellow": (33),
    "blue": (34)
}

color = 0


def DarkPrint(text='', end='\n'):
    """
    Выводит текст заданным цветом.

    Args:
        text (str): Текст для вывода.
        color (int): Номер цвета из словаря `colors`.
    """
    global color
    if color == 0:
        print(text, end=end)
        return

    if color > 6 or color < 0:
        print(f"Недопустимый номер цвета: {color}. Используется стандартный цвет.", end=end)
        color = 0
        return

    curent_color = colors[color]
    color_code = rgb[curent_color]
    print(f"\033[1;{color_code}m{text}\033[0m", end=end)


def get_executable_path():
    """
    Gets the path to the original executable, even when running from a temporary directory.
    """
    if getattr(sys, 'frozen', False):
        return os.path.abspath(sys.executable)
    else:
        return os.path.abspath(__file__)

def add_to_path(exe_path):
    """
    Копирует исполняемый файл в папку, находящуюся в PATH.

    Args:
        exe_path (str): Полный путь к исполняемому файлу (DarkTerminal.exe).
    """

    system = platform.system()
    if system == "Windows":
        path_dirs = os.environ["PATH"].split(";")
        target_dir = None
        for dir in path_dirs:
            if "Users" in dir and "AppData" in dir and "Roaming" in dir:
                target_dir = dir
                break
        if target_dir is None:
            target_dir = "C:\\Windows\\System32"

        if not os.path.exists(target_dir):
            print(f"Ошибка: Папка {target_dir} не существует.")
            return

        target_path = os.path.join(target_dir, "DarkTerminal.exe")

        try:
            shutil.copy2(exe_path, target_path)
        except Exception as e:
            print(f"Ошибка при копировании файла: {e}")

    elif system == "Linux" or system == "Darwin":  
        target_dir = "/usr/local/bin"
        if not os.path.exists(target_dir):
            print(f"Ошибка: Папка {target_dir} не существует.")
            return
        target_path = os.path.join(target_dir, "DarkTerminal")
        try:
            shutil.copy2(exe_path, target_path)
            os.chmod(target_path, 0o755) 
        except Exception as e:
            print(f"Ошибка при копировании файла: {e}")
    else:
        print(f"Неподдерживаемая операционная система: {system}")

def DarkTerminal():
    """Основная функция терминала."""
    global color
    aliases_file = os.path.join(os.path.expanduser("~"), ".dark_aliases")
    dark_terminal = os.path.join(os.path.expanduser("~"), ".dark_terminal")

    first_run = not os.path.exists(dark_terminal)

    defined_functions = {}

    if os.path.exists(aliases_file):
        with open(aliases_file, "r", encoding="utf-8") as aliases_file:
            aliases = aliases_file.readlines()
            aliases = [alias.strip() for alias in aliases if alias.strip() and not alias.strip().startswith("#")]
            for alias in aliases:
                try:
                    alias_name, command = alias.split("=", 1)
                    defined_functions[alias_name] = command
                except ValueError:
                    print(f"DarkTerminal: Ошибка в формате алиаса: {alias}")
    if os.path.exists(dark_terminal):
        with open(dark_terminal, "r", encoding="utf-8") as dark_terminal:
            lines = dark_terminal.readlines()
            for line in lines:
                if line.startswith("standart_color="):
                    standart_color = line.split("=")[1].strip()
                    if standart_color.isdigit():
                        color = int(standart_color)        
    else:
        DarkPrint("Добро пожаловать в DarkTerminal!")
        username = input("Введите ваше имя: ")
        password = input("Придумайте кодовое слово для зашиты: ")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with open(dark_terminal, "w", encoding="utf-8") as dark_terminal:
            dark_terminal.write("# Dark terminal configuration\n")
            dark_terminal.write(f"username={username}\n")
            dark_terminal.write(f"password={password_hash}\n")
        DarkPrint("Ваша учетная запись DarkTerminal успешно создана!")

    # Добавляем DarkTerminal.exe в PATH при первом запуске
    if first_run:
        executable_path = get_executable_path()
        executable_dir = os.path.dirname(executable_path)
        exe_path = os.path.join(executable_dir, "DarkTerminal.exe")
        if os.path.exists(exe_path):
            add_to_path(exe_path)
        else:
            print(f"Предупреждение: Файл DarkTerminal.exe не найден по пути {exe_path}. Он не будет добавлен в PATH.")

    current_env = {}

    while True:
        DarkPrint(f"{os.getcwd()}> ", end='')
        try:
            user_input = input()
        except KeyboardInterrupt:
            print("^C")
            continue
        if user_input.lower() == "exit":
            break
        
        
        process_command(user_input, current_env, defined_functions)
        

def select_color(arguments):
    """Изменяет цвет вывода текста."""
    global color
    color = int(arguments[0])


def source_command(arguments, current_env, defined_functions):
    """
    Имитирует команду 'source' в терминале, выполняя скрипт в текущем окружении.

    Args:
        arguments (list): Список аргументов, где первый аргумент - путь к скрипту.
        current_env (dict): Текущее окружение (словарь переменных).
        defined_functions (dict): Словарь определенных функций.
    """
    if not arguments:
        print("DarkTerminal: source: не указан файл для выполнения")
        return

    script_path = arguments[0]

    if not os.path.exists(script_path):
        print(f"DarkTerminal: source: файл не найден: {script_path}")
        return

    if not os.path.isfile(script_path):
        print(f"DarkTerminal: source: указанный путь не является файлом: {script_path}")
        return

    try:

        with open(script_path, "r", encoding="utf-8") as f:
            script_content = f.read()

        for line in script_content.splitlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            match = re.match(r"export\s+([a-zA-Z_][a-zA-Z0-9_]*)=(.*)", line)
            if match:
                var_name, var_value = match.groups()

                var_value = var_value.strip('"\'')
                current_env[var_name] = var_value
                print(f"Переменная окружения {var_name} установлена в {var_value}")
                continue

            match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)\s*\{", line)
            if match:
                func_name = match.group(1)
                func_body = ""
                in_func = True
                func_start_index = script_content.splitlines().index(line) + 1
                for subline in script_content.splitlines()[func_start_index:]:
                    if subline.strip() == "}":
                        in_func = False
                        break
                    func_body += subline + "\n"
                if in_func:
                    print(
                        f"DarkTerminal: source: ошибка при определении функции {func_name}: не найден закрывающий символ '}}'")
                    return
                defined_functions[func_name] = func_body
                print(f"Функция {func_name} определена")
                continue

            match = re.match(r"cd\s+(.*)", line)
            if match:
                dir_path = match.group(1)
                try:
                    os.chdir(dir_path)
                    print(f"Текущая директория изменена на {dir_path}")
                except FileNotFoundError:
                    print(f"DarkTerminal: source: cd: директория не найдена: {dir_path}")
                except NotADirectoryError:
                    print(f"DarkTerminal: source: cd: {dir_path} не является директорией")
                except OSError as e:
                    print(f"DarkTerminal: source: cd: ошибка при смене директории: {e}")
                continue

            if not script_path.endswith(".py"):
                try:

                    if line == "}":
                        continue

                    subprocess.run(["chcp", "65001"], shell=True, check=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
                    process = subprocess.Popen(line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                               text=True, encoding="utf-8", errors='backslashreplace')
                    stdout, stderr = process.communicate()
                    if process.returncode != 0:
                        print(f"DarkTerminal: source: ошибка при выполнении команды: {line}")
                        print(stderr)
                    else:
                        print(stdout, end="")
                except UnicodeDecodeError as e:
                    print(f"DarkTerminal: source: ошибка декодирования вывода команды: {line}")
                    print(f"Ошибка: {e}")
                except FileNotFoundError as e:
                    print(f"DarkTerminal: source: ошибка при выполнении команды: {line}")
                    print(f"Ошибка: {e}")
                except subprocess.CalledProcessError as e:
                    print(f"DarkTerminal: source: ошибка при выполнении команды chcp: {e}")
                continue

            if script_path.endswith(".py"):
                process = subprocess.Popen(["python", script_path], shell=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True,
                                           encoding=locale.getpreferredencoding(), errors='backslashreplace')
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    print(f"DarkTerminal: source: ошибка при выполнении скрипта: {script_path}")
                    print(stderr)
                else:
                    print(stdout)
                continue

            print(f"DarkTerminal: source: строка не распознана: {line}")

    except Exception as e:
        print(f"DarkTerminal: source: произошла ошибка: {e}")


def is_executable(filepath):
    """Проверяет, является ли файл исполняемым."""
    return os.path.isfile(filepath) and os.access(filepath, os.X_OK)


def find_executable_in_path(command):
    """
    Ищет исполняемый файл в директориях, указанных в переменной PATH.

    Args:
        command (str): Имя команды (исполняемого файла).

    Returns:
        str: Полный путь к исполняемому файлу, если найден, иначе None.
    """
    system = platform.system()
    if system == "Windows" and "." not in command and not command.endswith(".exe"):
        command += ".exe"

    path_dirs = os.environ["PATH"].split(os.pathsep)
    for path_dir in path_dirs:
        filepath = os.path.join(path_dir, command)
        if is_executable(filepath):
            return filepath
    return None


def list_files():
    """Выводит список файлов в текущей директории."""
    files = os.listdir()
    for file in files:
        if os.path.isdir(file):
            DarkPrint(f"{file}/", end="    ")
        elif os.path.isfile(file):
            DarkPrint(file, end="    ")
    DarkPrint()


def make_directory(arguments):
    """Создает новую директорию."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: mkdir: не указано имя директории")
        return
    os.mkdir(arguments[0])
    DarkPrint(f"Директория {arguments[0]} успешно создана")


def remove(arguments):
    """Удаляет файл или директорию."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: rm: не указано имя файла или директории")
        return
    path = os.path.join(os.getcwd(), arguments[0])
    if os.path.isdir(path):
        try:
            os.rmdir(path)
            DarkPrint(f"Директория {arguments[0]} успешно удалена")
        except OSError:
            DarkPrint(f"DarkTerminal: rm: не удалось удалить директорию {arguments[0]}")
    elif os.path.isfile(path):
        try:
            os.remove(path)
            DarkPrint(f"Файл {arguments[0]} успешно удален")
        except OSError:
            DarkPrint(f"DarkTerminal: rm: не удалось удалить файл {arguments[0]}")
            return
        if os.path.exists(path):
            DarkPrint(f"DarkTerminal: rm: не удалось удалить файл {arguments[0]} (остается)")
            return
        DarkPrint(f"Файл {arguments[0]} успешно удален")
    else:
        DarkPrint(f"DarkTerminal: rm: {arguments[0]}: нет такого файла или директории")
        return


def move_files(arguments):
    """Перемещает файлы или директории."""
    if len(arguments) < 2:
        DarkPrint("DarkTerminal: move: не указано имя файла или директории")
        return
    try:
        source = arguments[0]
        destination = arguments[1]

        if not os.path.exists(source):
            DarkPrint(f"Исходный путь '{source}' не существует.")
            return

        shutil.move(source, destination)
        DarkPrint(f"'{source}' успешно перемещен в '{destination}'.")

    except Exception as e:
        DarkPrint(f"Произошла ошибка: {e}")


def rename_file(arguments):
    """Переименовывает файл."""
    if len(arguments) < 2:
        DarkPrint("DarkTerminal: ren: не указано имя файла или директории")
        return
    try:
        source = arguments[0]
        destination = arguments[1]

        if not os.path.exists(source):
            DarkPrint(f"Исходный путь '{source}' не существует.")
            return

        os.rename(source, destination)
        DarkPrint(f"'{source}' успешно переименован в '{destination}'.")

    except Exception as e:
        DarkPrint(f"Произошла ошибка: {e}")


def create_file(arguments):
    """Создает новый файл."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: touch: не указано имя файла")
        return
    try:
        file_path = os.path.join(os.getcwd(), arguments[0])
        with open(file_path, "w", encoding='utf-8') as file:
            file.write("")
        DarkPrint(f"Файл {arguments[0]} успешно создан")
    except Exception as e:
        DarkPrint(f"Произошла ошибка: {e}")
        return


def cat_file(arguments):
    """Выводит содержимое файла."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: cat: не указано имя файла")
        return
    file_path = os.path.join(os.getcwd(), arguments[0])
    if not os.path.exists(file_path):
        DarkPrint(f"Файл {arguments[0]} не найден")
        return
    with open(file_path, "r", encoding='utf-8') as file:
        DarkPrint(file.read())
        file.close()


def more_file(arguments):
    """Выводит первые 10 строк файла."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: more: не указано имя файла")
        return

    file_path = os.path.join(os.getcwd(), arguments[0])
    if not os.path.exists(file_path):
        DarkPrint(f"Файл {arguments[0]} не найден")
        return
    with open(file_path, "r", encoding='utf-8') as file:
        DarkPrint("".join(file.readlines()[:10]))
        file.close()


def head_file(arguments):
    """Выводит первые N строк файла."""
    if len(arguments) < 1:
        DarkPrint("DarkTerminal: head: не указано имя файла")
        return

    filename = arguments[0]
    lines_to_read = 10
    if len(arguments) > 1:
        try:
            lines_to_read = int(arguments[1])
        except ValueError:
            DarkPrint("DarkTerminal: head: неверное количество строк")
            return

    file_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(file_path):
        DarkPrint(f"Файл {filename} не найден")
        return

    try:
        with open(file_path, "r", encoding='utf-8') as file:
            for i, line in enumerate(file):
                if i >= lines_to_read:
                    break
                DarkPrint(line, end="")
    except Exception as e:
        DarkPrint(f"Произошла ошибка: {e}")


def tail_file(arguments):
    """Выводит последние 10 строк файла."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: tail: не указано имя файла")
        return

    file_path = os.path.join(os.getcwd(), arguments[0])
    if not os.path.exists(file_path):
        DarkPrint(f"Файл {arguments[0]} не найден")
        return
    with open(file_path, "r", encoding='utf-8') as file:
        DarkPrint("".join(file.readlines()[-10:]))
        file.close()


def ping(arguments):
    """Проверяет доступность хоста."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: ping: не указан хост")
        return
    host = arguments[0]
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', host]

    try:

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            return f"Пинг к {host} успешен:\n{result.stdout}"
        else:
            return f"Ошибка пинга к {host}:\n{result.stderr}"
    except Exception as e:
        return f"Произошла ошибка: {e}"


def zip_file(arguments):
    """Архивирует файлы."""
    file = arguments[0]
    zip_name = arguments[1] if len(arguments) > 1 else file + '.zip'
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isdir(file):
                for root, _, filenames in os.walk(file):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)

                        zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(file)))
            else:

                zipf.write(file, os.path.basename(file))
            DarkPrint(f'Архив "{zip_name}" успешно создан.')
    except FileNotFoundError:
        DarkPrint(f'Файл "{file}" не найден.')


def unzip_file(arguments):
    """Распаковывает архив."""
    zip_name = arguments[0]
    destination = arguments[1] if len(arguments) > 1 else os.getcwd()
    try:
        with zipfile.ZipFile(zip_name, 'r') as zipf:
            zipf.extractall(destination)
        DarkPrint(f'Архив "{zip_name}" успешно распакован.')
    except FileNotFoundError:
        DarkPrint(f'Архив "{zip_name}" не найден.')
        return


def process_command(command, current_env, defined_functions):
    """Обрабатывает введенную команду."""
    if command.strip() == "":
        return

    parts = command.split('#')[0].split(' ')
    if ' '.join(parts) == "":
        return
    command_name = parts[0]
    arguments = parts[1:]

    if command_name in defined_functions:
        
        command_to_execute = defined_functions[command_name]

        
        if arguments:
            command_to_execute += " " + " ".join(arguments)

        
        process_command(command_to_execute, current_env, defined_functions)
        return
    elif command_name in current_env:
        print(current_env[command_name])
        return

    if command_name == "cd":
        change_directory(arguments)
    elif command_name == "pwd":
        DarkPrint(os.getcwd())
    elif command_name == "ls":
        list_files()

    elif command_name == "mkdir":
        make_directory(arguments)
    elif command_name == "rm":
        remove(arguments)
    elif command_name == "move":
        move_files(arguments)
    elif command_name == "ren":
        rename_file(arguments)
    elif command_name == "touch":
        create_file(arguments)
    elif command_name == "cat":
        cat_file(arguments)
    elif command_name == "more":
        more_file(arguments)
    elif command_name == "head":
        head_file(arguments)
    elif command_name == "tail":
        tail_file(arguments)
    elif command_name == "date":
        DarkPrint(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    elif command_name == "time":
        DarkPrint(datetime.datetime.now().strftime("%H:%M:%S"))
    elif command_name == "whoami":
        DarkPrint(os.getlogin())
    elif command_name == "hostname":
        DarkPrint(socket.gethostname())

    elif command_name == "ping":
        ping(arguments)
    elif command_name == "ipconfig":
        DarkPrint(f"IP-адрес: {socket.gethostbyname(socket.gethostname())}")

    elif command_name == "zip":
        zip_file(arguments)
    elif command_name == "unzip":
        unzip_file(arguments)

    elif command_name == "clear":
        clear_screen()
    elif command_name == "color":
        select_color(arguments)
    elif command_name == "source":
        source_command(arguments, current_env, defined_functions)
    elif command_name == "export":
        export_variable(arguments)
    elif command_name == "unset":
        unset_variable(arguments)
    elif command_name == "env":
        print_environment(arguments)
    elif command_name == "alias":
        print_aliases(arguments)
    elif command_name == "unalias":
        unalias_command(arguments)
    elif command_name == "type":
        print_command_type(arguments, defined_functions)
    elif command_name == "bind":
        bind_command(arguments)
    elif command_name == "echo":
        echo_command(arguments)
    
    elif command_name == "run":
        run_command(arguments)
    else:
        executable_path = find_executable_in_path(command_name)
        if executable_path:
            try:
                process = subprocess.Popen([executable_path] + arguments, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True, encoding=locale.getpreferredencoding(), errors='backslashreplace')

                def print_output(stream):
                    while True:
                        line = stream.readline()
                        if not line:
                            break
                        DarkPrint(line, end="")

                stdout_thread = threading.Thread(target=print_output, args=(process.stdout,))
                stderr_thread = threading.Thread(target=print_output, args=(process.stderr,))

                stdout_thread.start()
                stderr_thread.start()

                # Обработка KeyboardInterrupt
                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("^C")
                    # Посылаем сигнал SIGINT дочернему процессу
                    if process.poll() is None:
                        if platform.system() == "Windows":
                            process.send_signal(signal.CTRL_C_EVENT)
                        else:
                            process.send_signal(signal.SIGINT)
                        process.wait()
                    
                    return

                stdout_thread.join()
                stderr_thread.join()

            except FileNotFoundError:
                DarkPrint(f"DarkTerminal: {command_name}: команда не найдена")
        else:
            
            if command_name.endswith(".py") and os.path.exists(command_name):
                try:
                    process = subprocess.Popen(["python", command_name] + arguments, stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate()
                    if process.returncode == 0:
                        print(stdout, end="")
                    else:
                        print(stderr, end="")
                except FileNotFoundError:
                    DarkPrint(f"DarkTerminal: python: команда не найдена")
            else:
                DarkPrint(f"DarkTerminal: {command_name}: команда не найдена")


def export_variable(arguments):
    """Экспортирует переменную окружения."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: export: не указана переменная окружения")
        return
    variable_name = arguments[0]
    if "=" in variable_name:
        DarkPrint("DarkTerminal: export: Неправильный формат переменной окружения")
        return
    os.environ[variable_name] = ""
    DarkPrint(f"Переменная окружения {variable_name} успешно экспортирована")


def unset_variable(arguments):
    """Удаляет переменную окружения."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: unset: Не указана переменная окружения")
        return
    variable_name = arguments[0]
    if variable_name in os.environ:
        del os.environ[variable_name]
        DarkPrint(f"Переменная окружения {variable_name} успешно удалена")
    else:
        DarkPrint(f"Переменная окружения {variable_name} не найдена")
        return


def print_environment(arguments):
    """Выводит список переменных окружения."""
    for key, value in os.environ.items():
        DarkPrint(f"{key}={value}")


def print_aliases(arguments):
    """Выводит список алиасов."""
    aliases_file = os.path.join(os.path.expanduser("~"), ".dark_aliases")
    if os.path.exists(aliases_file):
        with open(aliases_file, 'r') as file:
            for line in file:
                parts = line.strip().split('=')
                if len(parts) == 2:
                    alias_name = parts[0]
                    command = parts[1]
                    DarkPrint(f"{alias_name}={command}")
    else:
        DarkPrint("DarkTerminal: Алиасы не найдены")
        return


def unalias_command(arguments):
    """Удаляет алиас."""
    if len(arguments) == 0:
        DarkPrint("DarkTerminal: unalias: Не указан алиас")
        return
    alias_name = arguments[0]
    aliases_file = os.path.join(os.path.expanduser("~"), ".dark_aliases")
    if os.path.exists(aliases_file):
        with open(aliases_file, 'r') as file:
            lines = file.readlines()
            new_lines = []
            for line in lines:
                parts = line.strip().split('=')
                if len(parts) == 2 and parts[0] != alias_name:
                    new_lines.append(line)
            with open(aliases_file, 'w') as file:
                file.write(''.join(new_lines))
        DarkPrint(f"Алиас {alias_name} успешно удален")
    else:
        DarkPrint("DarkTerminal: Алиасы не найдены")
        return


def print_command_type(arguments, defined_functions):
    """Выводит тип определенной команды."""
    if not arguments:
        DarkPrint("DarkTerminal: type: Недостаточно аргументов")
        return
    command_name = arguments[0]
    executable_path = find_executable_in_path(command_name)
    if executable_path:
        DarkPrint(f"{command_name}: Это исполняемый файл")
        return
    elif command_name in defined_functions:
        DarkPrint(f"{command_name}: Это определенный алиас")
        return

    DarkPrint(f"{command_name}: Это команда")
    return


def bind_command(arguments):
    """Создает алиас для команды."""
    if len(arguments) < 2:
        DarkPrint("DarkTerminal: bind: Недостаточно аргументов")
        return
    alias_name = arguments[0]
    command = ''.join(arguments[1:])
    aliases_file = os.path.join(os.path.expanduser("~"), ".dark_aliases")
    if not os.path.exists(aliases_file):
        try:
            with open(aliases_file, 'a') as file:
                file.write(f"{alias_name}={command}\n")
                DarkPrint(f"Алиас {alias_name} успешно создан")
                return
        except FileNotFoundError:
            DarkPrint(f"Ошибка при записи в файл алиасов: {aliases_file}")
            return
    else:
        with open(aliases_file, 'a') as file:
            file.write(f"{alias_name}={command}\n")
            DarkPrint(f"Алиас {alias_name} успешно создан")
            return
        
def echo_command(arguments):
    """Выводит аргументы."""
    print(' '.join(arguments))
    return

def run_command(arguments):
    """Запускает команду."""
    if not arguments:
        DarkPrint("DarkTerminal: run: Недостаточно аргументов")
        return
    ScriptName =''.join(arguments)
    if ScriptName.endswith('.dark'):
        try:
            with open(ScriptName, 'r') as file:
                script_content = file.read().strip().split('\n')
                if script_content[0] == "DarkScript":
                    for line in script_content[1:]:
                        process_command(line, {}, {})
                else:
                    DarkPrint(f"DarkTerminal: {ScriptName}: не подходит формату DarkScript")
        except FileNotFoundError:
            DarkPrint(f"Скрипт не найден: {ScriptName}")


def change_directory(arguments):
    """Изменяет текущую директорию."""
    if not arguments:
        DarkPrint("DarkTerminal: cd: Недостаточно аргументов")
        return
    try:
        os.chdir(arguments[0])
    except FileNotFoundError:
        DarkPrint(f"Директория не найдена: {arguments[0]}")
    except NotADirectoryError:
        DarkPrint(f"{arguments[0]} не является директорией")
    except OSError as e:
        DarkPrint(f"Ошибка при смене директории: {e}")


def clear_screen():
    """Очищает экран терминала."""
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    DarkTerminal()
