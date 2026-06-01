import os

def mkdir_if_not_exist(path: str):
    """不存在就自动建文件夹"""
    if not os.path.exists(path):
        os.makedirs(path)