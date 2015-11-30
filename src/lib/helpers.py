"""
This module contains utility functions that are required by views only.
All views get access to any helper methods through this module.
"""

from boondi.utils import field_format, get_error_template, to_time, yesno, to_json
from boondi.routes import url_for

def safe_id(token):
    return token.lower().replace('/', '_').replace(' ', '_')
