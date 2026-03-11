import os

from starlette.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists(os.path.join(BASE_DIR, "src", "presentation")):
    TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "presentation", "templates")
else:
    raise FileNotFoundError("Не найден файл шаблонов")

print(TEMPLATES_DIR)
templates = Jinja2Templates(directory=TEMPLATES_DIR)