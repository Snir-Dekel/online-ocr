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

    try:
        data = request.form['image']
        data = data[data.index(",") + 1:]
        data = bytes(data, encoding='utf8')
        bytes_image = base64.b64decode(data)
        im = Image.open(io.BytesIO(bytes_image))
        lang = request.form['language']
        image_text = pytesseract.image_to_string(im, lang=lang).strip()
        numpy_image = numpy.array(im)

        img = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

        boxes = pytesseract.image_to_boxes(img)
        height, width, _ = img.shape

        for box in boxes.splitlines():
            box = box.split()
            img = cv2.rectangle(img, (int(box[1]), height - int(box[2])), (int(box[3]), height - int(box[4])), (0, 255, 0), 0)

        ret, frame_buff = cv2.imencode('.png', img)
        frame_b64 = base64.b64encode(frame_buff)
        # print(frame_b64)
    except:
        return "Can't extract text from image"

    print("the text:", snir.header(image_text))
    mydb = mysql.connector.connect(
        host=os.environ["mysql_host"],
        user=os.environ["root"],
        password=os.environ["sql_password"],
        database=os.environ["database"],
    )


    mycursor = mydb.cursor()

    mycursor.execute(sql_query, (image_text,))

    mydb.commit()
    mydb.close()
    if not image_text:
        return "Can't extract text from image"


    return jsonify(
        image_text=image_text,
        base_64_image=frame_b64.decode("utf-8"),
    )

@app.route('/translate', methods=['POST'])
def do_translate():
    try:
        text_to_translate = request.get_json()
        print("text_to_translate:", text_to_translate)
        return jsonify(translation=translator.translate(text_to_translate, dest='he').text)

    except Exception as e:
        print("Error:", e.with_traceback(None))
        return jsonify(translation="Cant translate text")
    
    
    
    
    @app.route('/crop', methods=['POST'])
def do_crop():
    # try:
        json_request = request.get_json()
        # print(json_request["base64_image"])
        data = json_request["base64_image"]
        data = data[data.index(",") + 1:]
        data = bytes(data, encoding='utf8')
        bytes_image = base64.b64decode(data)
        im = Image.open(io.BytesIO(bytes_image))
        im = im.crop((json_request["x"], json_request["y"], json_request["width"]+json_request["x"], json_request["height"]+json_request["y"]))
        # im.show()
        lang = json_request['language']

        try:
            image_text = pytesseract.image_to_string(im, lang=lang).strip()
        except Exception as e:
            print(e)
            return jsonify(image_text="Can't extract text from image")

        try:
            numpy_image = numpy.array(im)

            img = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

            boxes = pytesseract.image_to_boxes(img)
            height, width, _ = img.shape

            for box in boxes.splitlines():
                box = box.split()
                img = cv2.rectangle(img, (int(box[1]), height - int(box[2])), (int(box[3]), height - int(box[4])), (0, 255, 0), 0)

            ret, frame_buff = cv2.imencode('.png', img)
            frame_b64 = base64.b64encode(frame_buff)
            # print(frame_b64)
        except Exception as e:
            print(e)
            return jsonify(image_text="Can't extract text from image")

        if not image_text:
            print("blank image_text")
            return jsonify(image_text="Can't extract text from image")

        return jsonify(image_text=image_text)


app.run()
