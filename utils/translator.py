import json
import os
import sys

class Translator:
    _dict = {}
    _lang = "es"

    @classmethod
    def set_language(cls, lang_code, base_path=None):
        cls._lang = lang_code
        if not base_path:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
        locale_path = os.path.join(base_path, "locales", f"{lang_code}.json")
        if not os.path.exists(locale_path) and lang_code != "es":
            locale_path = os.path.join(base_path, "locales", "es.json") # Fallback to es
            
        try:
            with open(locale_path, 'r', encoding='utf-8') as f:
                cls._dict = json.load(f)
        except Exception as e:
            print(f"Error loading locale {lang_code}: {e}")
            cls._dict = {}

    @classmethod
    def tr(cls, key, default=None):
        return cls._dict.get(key, default if default else key)

    @classmethod
    def get_month_name(cls, month_int):
        months = cls.tr("MONTHS", [
            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ])
        if 1 <= month_int <= 12:
            return months[month_int]
        return ""

def tr(key, default=None):
    return Translator.tr(key, default)
