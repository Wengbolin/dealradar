import os
import re

TEMPLATE_DIR = "templates"

def make_key(text):
    key = text.lower()
    key = re.sub(r'[^a-z0-9 ]','',key)
    key = key.replace(" ","_")
    return key[:40]

for root, dirs, files in os.walk(TEMPLATE_DIR):
    for file in files:
        if file.endswith(".html"):

            path = os.path.join(root,file)

            with open(path,"r",encoding="utf8") as f:
                html = f.read()

            matches = re.findall(r">([^<>]{3,60})<",html)

            for m in matches:

                text = m.strip()

                if not text:
                    continue

                if "{%" in text or "{{" in text:
                    continue

                key = make_key(text)

                new = f'data-i18n="{key}">{text}<'

                html = html.replace(f">{text}<",f' {new}')

            with open(path,"w",encoding="utf8") as f:
                f.write(html)

            print("processed:",path)
