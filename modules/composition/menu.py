from pathlib import Path

from tqdm import tqdm
from whaaaaat import prompt

from modules.composition.pdf import dir_to_pdf
from modules.composition.jpg.stack import dir_to_jpg
from modules.static import Const

from modules.ui.colorize import red

from modules import database
from modules.sorting import numerical_sort

composing_options = {
    Const.PdfDIr: dir_to_pdf,
    Const.JpgDir: dir_to_jpg
}


def compose_menu():
    if len(database.manga.all()) <= 0:
        print(f'[{red("X")}] No mangas downloaded')
        return

    compose_menu_options = {
        'type': 'list',
        'name': 'compose',
        'message': 'Pick composition type.',
        'choices': [str(key) for key in composing_options.keys()]
    }

    response = ''
    try:
        response = prompt(compose_menu_options)['compose']
        response = Path(response)
    except KeyError as e:
        print(e)

    manga, chapters = chapterSelection()
    (manga / Path(response)).mkdir(exist_ok=True)

    for chapter in tqdm(chapters):
        composing_options[response](
            chapter,
            manga / Path(response)
        )


def chapterSelection():
    """
    :returns array os strings pointing to get_chapter_list to be composed
    """

    manga_dir = Path(Const.MangaSavePath)

    mangas = list(manga_dir.iterdir())
    if len(mangas) <= 0:
        return Path, []

    # manga selection
    manga_options = {
        'type': 'list',
        'name': 'manga',
        'message': 'Pick manga',
        'choices': map(lambda path: path.parts[-1], mangas),
        'filter': lambda val: mangas[mangas.index(Path(Const.MangaSavePath) / Path(val))]
    }

    manga: Path = Path()
    try:
        manga = prompt(manga_options)['manga']
        manga = Path(manga)
    except KeyError as e:
        print(e)
        return Path, []

    # select get_chapter_list
    chapter_option = {
        'type': 'checkbox',
        'name': 'get_chapter_list',
        'message': 'Select get_chapter_list to compose',
        'choices': sorted(
            [{'name': i.parts[-1]} for i in manga.iterdir() if not is_folder_static(i.parts[-1])],
            key=lambda val: numerical_sort(val['name'])
        ),
    }

    # if no get_chapter_list
    if len(chapter_option['choices']) <= 0:
        return manga, []

    try:
        chapters = prompt(chapter_option)['get_chapter_list']
        chapters = map(lambda path: manga / Path(path), chapters)
    except KeyError as e:
        print(e)
        return manga, []

    return manga, list(chapters)


def is_folder_static(folder_name) -> bool:
    return folder_name == Const.StructFile or folder_name == Const.JpgDir or folder_name == Const.PdfDIr