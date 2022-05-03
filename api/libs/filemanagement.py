import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def filecopy(from_path, to_path):
    with default_storage.open(from_path) as original_file:
        default_storage.save(to_path, ContentFile(original_file.read()))


def delfolder(path):

    # list folders and files
    (folders, files) = default_storage.listdir(path)

    # first delete files at current path
    for file in files:
        file_path = os.path.join(path, file)
        default_storage.delete(file_path)

    # now delete folders recursively
    for folder in folders:
        folder_path = os.path.join(path, folder)
        delfolder(folder_path)


def get_subfolders(path, intsort=False):

    # list sessions (folders, not files)
    (folders, _) = default_storage.listdir(path)

    # convert to int and sort
    if intsort:
        sessions = [int(i) for i in folders]
        sessions.sort()

    return folders
