## \file /src/utils/string/__init__.py
# -*- coding: utf-8 -*-

#! .pyenv/bin/python3

"""
.. module:: src.utils.string 
	:platform: Windows, Unix
	:synopsis:

"""


from .validator import ProductFieldsValidator
from .normalizer import (
						normalize_string,
						normalize_int,
						normalize_float,
						normalize_boolean,
						normalize_sql_date,
					)
from .ai_string_utils import string_for_train, normalize_answer
from .html_simplification import simplify_html


