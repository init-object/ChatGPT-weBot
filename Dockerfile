FROM initobject/chatgpt-webot-env:1.0 
COPY . .
CMD [ "python", "main.py"]
