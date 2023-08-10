FROM initobject/chatgpt-webot-env:latest
COPY . .
CMD [ "python", "main.py"]
