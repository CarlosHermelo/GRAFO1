from google.genai import types

print("CLASES DISPONIBLES EN google.genai.types:\n")

for name in dir(types):
    attr = getattr(types, name)
    if isinstance(attr, type):
        print(name)
