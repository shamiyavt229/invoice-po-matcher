import google.generativeai as genai

genai.configure(api_key="AIzaSyCga-46XDgqLQ7QZvM_bopX1sq0b69Pa-A")

for m in genai.list_models():
    print(m.name)
