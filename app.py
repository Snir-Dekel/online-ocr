import base64
import io
import os
import mysql.connector
import pytesseract
from PIL import Image
from flask import Flask, render_template, request

sql_query = "INSERT INTO ocr (text) VALUES (%s)"


app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


@app.route('/')
def main():
    return render_template('ocr.jinja2')


@app.route('/ocr', methods=['POST'])
def do_ocr():
    data = request.form['image']
    data = data[data.index(",") + 1:]
    data = bytes(data, encoding='utf8')

    base64_image = base64.b64decode(data)
    im = Image.open(io.BytesIO(base64_image))
    lang = request.form['language']

    image_text = pytesseract.image_to_string(im, lang=lang).strip()
    print("the text:", image_text)
    mydb = mysql.connector.connect(
        host=os.environ["mysql_host"],
        user=os.environ["root"],
        password=os.environ["my_sql_password"],
        database=os.environ["login_website"],
    )

    mycursor = mydb.cursor()

    mycursor.execute(sql_query, (image_text,))

    mydb.commit()
    mydb.close()

    return render_template("ocr.jinja2", image_text=image_text, lang=lang)


app.run()