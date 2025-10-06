# -*- coding: utf-8 -*-
"""
Команда отправки связанного изображения и текстового описания в Google Gemini.
"""

import FreeCAD
from PySide import QtGui
from typing import Optional
from ..utils import get_icon, AI_DATA_DIR, save_ai_response_to_history, get_api_key
from ..project_manager import AIProject

# Инициализация проекта
try:
    project = AIProject()
except Exception as ex:
    FreeCAD.Console.PrintError(f'[AIEngineer] Failed to initialize project manager in ask_ai: {ex}\n')
    project = None


class AskAICommand:
    """Команда отправки запроса в Google Gemini с изображением и текстом."""

    def GetResources(self):
        """
        Функция возвращает ресурсы команды (иконка, текст меню, подсказка).
        
        Returns:
            dict: Словарь с ресурсами команды.
        """
        return {
            'MenuText': 'Ask AI',
            'ToolTip': 'Send linked image+text to Google Gemini',
            'Pixmap': get_icon('ai_chat.svg')
        }

    def Activated(self):
        """
        Функция выполняет отправку запроса в Google Gemini при активации команды.
        
        Returns:
            None
        """
        # Проверка наличия связанных данных
        if not project or not project.get_all_links():
            QtGui.QMessageBox.information(
                None, 'No Data', 'First link an image to a text using "Link Content".'
            )
            return

        # Загрузка API-ключа из .env или QSettings
        api_key: str = get_api_key()
        
        if not api_key:
            response = QtGui.QMessageBox.critical(
                None, 
                'Error', 
                'Gemini API key not set.\n\nGo to AI Settings to configure it.',
                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Ignore
            )
            if response == QtGui.QMessageBox.Ok:
                # Открытие диалога настроек
                try:
                    from ..settings_dialog import SettingsDialog
                    dialog = SettingsDialog()
                    dialog.exec_()
                except Exception as ex:
                    FreeCAD.Console.PrintError(f'[AIEngineer] Failed to open settings: {ex}\n')
            return

        # Извлечение первой доступной связки (image → text)
        links: dict = project.get_all_links()
        image_file, text_file = next(iter(links.items()))
        image_path = AI_DATA_DIR / image_file
        text_path = AI_DATA_DIR / text_file

        # Проверка существования текстового файла
        if not text_path.exists():
            QtGui.QMessageBox.critical(None, 'Error', f'Text file not found: {text_path}')
            return

        # Чтение текстового промпта
        prompt: str = ''
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
        except Exception as ex:
            QtGui.QMessageBox.critical(None, 'Error', f'Cannot read text file:\n{str(ex)}')
            return

        FreeCAD.Console.PrintMessage('[AIEngineer] Sending to Google Gemini...\n')
        response: str = 'Failed to get response.'

        # Отправка запроса в Gemini
        try:
            from ..gemini import GoogleGenerativeAi
            
            # Используем новый интегрированный класс
            llm = GoogleGenerativeAi(
                api_key=api_key,
                model_name='gemini-1.5-flash',
                system_instruction='Вы - технический ассистент для инженеров, работающих с FreeCAD. '
                                   'Анализируйте изображения чертежей и предоставляйте точные технические рекомендации.'
            )
            
            # Используем метод describe_image для обработки изображения с промптом
            gemini_response: Optional[str] = llm.describe_image(
                image=image_path,
                mime_type='image/jpeg' if image_path.suffix.lower() in ['.jpg', '.jpeg'] else 'image/png',
                prompt=prompt
            )
            
            response = gemini_response if gemini_response is not None else 'Gemini returned empty response.'
            
        except ValueError as ex:
            # Обработка ошибки отсутствия API-ключа
            QtGui.QMessageBox.critical(
                None,
                'Configuration Error',
                f'API key configuration error:\n{str(ex)}\n\nPlease configure API key in AI Settings.'
            )
            return
            
        except Exception as ex:
            response = f'Gemini error: {str(ex)}'
            FreeCAD.Console.PrintError(f'[AIEngineer] Gemini request failed: {ex}\n')

        # Сохранение в историю
        save_ai_response_to_history(prompt, response)

        # Отображение результата
        try:
            from ..dialogs.ai_response import AIResponseDialog
            dialog = AIResponseDialog(prompt, response)
            dialog.exec_()
        except Exception as ex:
            FreeCAD.Console.PrintError(f'[AIEngineer] Failed to show response dialog: {ex}\n')
            QtGui.QMessageBox.information(
                None,
                'AI Response',
                f'Prompt:\n{prompt[:200]}...\n\nResponse:\n{response[:500]}...'
            )

    def IsActive(self):
        """
        Функция проверяет, активна ли команда (есть ли связанные данные).
        
        Returns:
            bool: True если есть связанные данные, False иначе.
        """
        return project is not None and bool(project.get_all_links())_file, text_file = next(iter(links.items()))
        image_path = AI_DATA_DIR / image_file
        text_path = AI_DATA_DIR / text_file

        # Проверка существования текстового файла
        if not text_path.exists():
            QtGui.QMessageBox.critical(None, 'Error', f'Text file not found: {text_path}')
            return

        # Чтение текстового промпта
        prompt: str = ''
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
        except Exception as ex:
            QtGui.QMessageBox.critical(None, 'Error', f'Cannot read text file:\n{str(ex)}')
            return

        FreeCAD.Console.PrintMessage('[AIEngineer] Sending to Google Gemini...\n')
        response: str = 'Failed to get response.'

        # Отправка запроса в Gemini
        try:
            from ..gemini import GoogleGenerativeAi
            # Используем стабильную модель
            llm = GoogleGenerativeAi(api_key=api_key, model_name='gemini-1.5-flash')
            gemini_response: Optional[str] = llm.ask(q=prompt, image_path=str(image_path), attempts=5)
            response = gemini_response if gemini_response is not None else 'Gemini returned empty response.'
        except Exception as ex:
            response = f'Gemini error: {str(ex)}'
            FreeCAD.Console.PrintError(f'[AIEngineer] Gemini request failed: {ex}\n')

        # Сохранение в историю
        save_ai_response_to_history(prompt, response)

        # Отображение результата
        try:
            from ..dialogs.ai_response import AIResponseDialog
            dialog = AIResponseDialog(prompt, response)
            dialog.exec_()
        except Exception as ex:
            FreeCAD.Console.PrintError(f'[AIEngineer] Failed to show response dialog: {ex}\n')
            QtGui.QMessageBox.information(
                None,
                'AI Response',
                f'Prompt:\n{prompt[:200]}...\n\nResponse:\n{response[:500]}...'
            )

    def IsActive(self):
        """
        Функция проверяет, активна ли команда (есть ли связанные данные).
        
        Returns:
            bool: True если есть связанные данные, False иначе.
        """
        return project is not None and bool(project.get_all_links())