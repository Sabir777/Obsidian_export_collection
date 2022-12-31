import re
from pathlib import Path
import shutil
from collections import deque

class ExportCollection:
    def __init__(self):
        self.first_note = self.input_data()
        self.pictures = set()

# Ввод имени корневой заметки
# Принимается имя в двух форматах: name.md или name (без расширения). Расширения (кроме .md) недопустимы
    @staticmethod
    def input_data():
        print('Для экспорта коллекции введите название корневой заметки')
        pattern_md = r'^[^.]+(?=(?:.md$)|$)'
        match = re.match(pattern_md, input())
        if match:
            name_file = match[0] + '.md'
            path_file = Path.cwd() / name_file
        else:
            raise FileExistsError('Неправильное имя файла.\nДопускается не вводить расширение файла.\nНо подразумевается что данный файл имеет тип *.md')
        if not path_file.is_file():
            raise FileExistsError(f'Файл {name_file} не был найден')
        return name_file

# Поиск картинок в заметке
    @staticmethod
    def find_pictures_note(content):
        pattern1 = r'!\[.+?\]\(([^.]+?\.\w+)(?=\))'  # findall - группа
        pattern2 = r'(?<=\!\[\[)[^.]+\.\w+(?=\]\])'  # без групп
        return re.findall(pattern1, content) + re.findall(pattern2, content)

# Поиск файлов-картинок в хранилище
    @staticmethod
    def find_file_path(name_file):  # метод возвращает путь
        def find_path(folder):  # рекурсивный обход файлов и папок
            for p in folder.iterdir():
                if p.name == name_file:
                    return p
                if p.is_dir():
                    res = find_path(p)
                    if res:
                        return res
            return None
        return find_path(Path.cwd())

# Копирование картинок в папку назначения
    def copy_pictures(self, target):
        res = [path for name in self.pictures if (path := self.find_file_path(name))]
        for file_path in res:
            shutil.copy(file_path, target)

# Получить список файлов из заметки:
# Будут учитываться только те ссылки которые не находятся в заголовке заметки
    def get_ref_list(self, name_file):
        pattern_header_ref = r'# \d{12}\S+\n(?:\*{3}\n)?(?:\[\[\d{12}\S+?\]\]\n)+'
        pattern_ref = r'(?<=\[\[)\d{12}\S+?(?=(?:\]\])|(?:\|))'
        try:
            with open(name_file, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            return []  # файл не был найден, возвращаю пустой список
        match = re.match(pattern_header_ref, content)
        header = match[0] if match else ''
        header_ref_list = re.findall(pattern_ref, header) if header else []
        notes = list(set(re.findall(pattern_ref, content)) - set(header_ref_list))
        self.pictures |= set(self.find_pictures_note(content))  # ищу картинки в заметке
        return notes

# Получаю все имена файлов из всех зависимых файлов
    def get_file_list(self):
        deque_files = deque([self.first_note])
        result = []
        while deque_files:
            name_file = deque_files.popleft()
            if name_file in result:
                continue
            deque_files.extend(f'{name}.md' for name in self.get_ref_list(name_file))   # добавляю расширение '.md' к найденным именам файлов
            result.append(name_file)
        return result

# Копирую все найденные файлы в папку на рабочем столе или в домашний каталог
    def export_files(self):
        name_folder = self.first_note.replace('.md', '')  # удаляю расширение '.md'
        new_folder_path = Path.home() / 'Desktop' / name_folder
        try:
            if Path(new_folder_path).is_dir():
                shutil.rmtree(new_folder_path) # удаляю папку если она уже существует
            new_folder_path.mkdir() # создаю папку на рабочем столе
            messange = f'Папка с коллекцией заметок находится на рабочем столе в папке {name_folder}'
        except FileNotFoundError:
            new_folder_path = Path.home() / name_folder
            if Path(new_folder_path).is_dir():
                shutil.rmtree(new_folder_path)  # удаляю папку если она уже существует
            new_folder_path.mkdir() # создаю папку в домашней директории
            messange = f'Папка с коллекцией заметок находится в домашней директории в папке {name_folder}'

# копирую все найденные файлы в созданную папку
        cwd_path = Path.cwd()
        for file in self.get_file_list():
            try:
                shutil.copy(cwd_path / file, new_folder_path)
            except FileNotFoundError:
                pass
        self.copy_pictures(new_folder_path)  # копирую картинки в папку назначения
        print(messange)


root_note = ExportCollection()
root_note.export_files()
