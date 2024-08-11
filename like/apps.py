from django.apps import AppConfig
from drf import settings
import json

class LikeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'like'
    def ready(self):
        with open("utils/DFAClassified.json", "r") as jsonFile:
            settings.GLOBAL_VARIABLES['DFATree'] = json.load(jsonFile)
        with open('utils/safeWords.json','r') as jsonFile:
            settings.GLOBAL_VARIABLES['safeWords'] = json.load(jsonFile)
        print('后端启动中...')