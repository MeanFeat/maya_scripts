from maya import cmds
import os


def get_file_path():
    split_path = cmds.file(query=True, expandName=True)
    split_path = split_path.split('/')
    split_path.pop()
    path = ""
    for item in split_path:
        path += item + "/"
    return path


def get_file_name():
    file_name = cmds.file(query=True, expandName=True)
    file_name = file_name.split('.')
    file_name = file_name[0].split('/')
    return file_name[-1]


def get_file_extension():
    return get_file_name().split('.')[-1]


def verify_directory(full_path):
    if not os.path.isdir(full_path):
        os.makedirs(full_path)
