import os
import re
import json

TEMPLATE_DIR = "templates"
OUTPUT_FILE = "static/lang/en_auto.json"

texts = {}

def make_key(text):
    key = text.lower()
    key = re.sub(r'[^a-z0-9 ]', '', key)
    key = key.replace(" ", "_")
    return key[:40]

for root, dirs, files in os.walk(TEMPLATE_DIR):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)

            with open(path,"r",encoding="utf8") as f:
                html = f.read()

            matches = re.findall(r">([^<>]{3,60})<", html)

            for m in matches:
                text = m.strip()

                if text and not text.startswith("{"):

                    key = make_key(text)

                    texts[key] = text

with open(OUTPUT_FILE,"w",encoding="utf8") as f:
    json.dump(texts,f,indent=2,ensure_ascii=False)

print("Generated:", OUTPUT_FILE)
print("Total keys:", len(texts))
