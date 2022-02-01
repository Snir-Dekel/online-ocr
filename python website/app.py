import base64
import io
import os
import re
import time
import cv2
import mysql.connector
import numpy
import pytesseract
import snir
from PIL import Image
from flask import Flask, render_template, request, jsonify
from googletrans import Translator
import tensorflow_hub as hub
import tensorflow as tf

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
sql_query = "INSERT INTO ocr (text) VALUES (%s)"
translator = Translator()
app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
food_101_model = tf.keras.models.load_model(r"final_food101_model.h5")
hebrew_spam_model = tf.keras.models.load_model(r"hebrew_spam_model.h5", custom_objects={"KerasLayer": hub.KerasLayer})
english_spam_model = tf.keras.models.load_model(r"english_spam_model.h5", custom_objects={"KerasLayer": hub.KerasLayer})
english_disaster_model = tf.keras.models.load_model(r"english_disaster_model.h5", custom_objects={"KerasLayer": hub.KerasLayer})
hebrew_disaster_model = tf.keras.models.load_model(r"hebrew_disaster_model")
nlp_models = {"english disaster": english_disaster_model, "hebrew disaster": hebrew_disaster_model, "english spam": english_spam_model, "hebrew spam": hebrew_spam_model}
print(nlp_models)
class_names = ['apple_pie',
               'baby_back_ribs',
               'baklava',
               'beef_carpaccio',
               'beef_tartare',
               'beet_salad',
               'beignets',
               'bibimbap',
               'bread_pudding',
               'breakfast_burrito',
               'bruschetta',
               'caesar_salad',
               'cannoli',
               'caprese_salad',
               'carrot_cake',
               'ceviche',
               'cheesecake',
               'cheese_plate',
               'chicken_curry',
               'chicken_quesadilla',
               'chicken_wings',
               'chocolate_cake',
               'chocolate_mousse',
               'churros',
               'clam_chowder',
               'club_sandwich',
               'crab_cakes',
               'creme_brulee',
               'croque_madame',
               'cup_cakes',
               'deviled_eggs',
               'donuts',
               'dumplings',
               'edamame',
               'eggs_benedict',
               'escargots',
               'falafel',
               'filet_mignon',
               'fish_and_chips',
               'foie_gras',
               'french_fries',
               'french_onion_soup',
               'french_toast',
               'fried_calamari',
               'fried_rice',
               'frozen_yogurt',
               'garlic_bread',
               'gnocchi',
               'greek_salad',
               'grilled_cheese_sandwich',
               'grilled_salmon',
               'guacamole',
               'gyoza',
               'hamburger',
               'hot_and_sour_soup',
               'hot_dog',
               'huevos_rancheros',
               'hummus',
               'ice_cream',
               'lasagna',
               'lobster_bisque',
               'lobster_roll_sandwich',
               'macaroni_and_cheese',
               'macarons',
               'miso_soup',
               'mussels',
               'nachos',
               'omelette',
               'onion_rings',
               'oysters',
               'pad_thai',
               'paella',
               'pancakes',
               'panna_cotta',
               'peking_duck',
               'pho',
               'pizza',
               'pork_chop',
               'poutine',
               'prime_rib',
               'pulled_pork_sandwich',
               'ramen',
               'ravioli',
               'red_velvet_cake',
               'risotto',
               'samosa',
               'sashimi',
               'scallops',
               'seaweed_salad',
               'shrimp_and_grits',
               'spaghetti_bolognese',
               'spaghetti_carbonara',
               'spring_rolls',
               'steak',
               'strawberry_shortcake',
               'sushi',
               'tacos',
               'takoyaki',
               'tiramisu',
               'tuna_tartare',
               'waffles']
MOBILE_AGENT_RE = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)


def is_mobile():
    return MOBILE_AGENT_RE.match(str(request.user_agent))


@app.route('/')
def main():
    return render_template('ocr.jinja2', mobile=is_mobile())


@app.route('/food')
def food_page():
    return render_template('food101.jinja2', mobile=is_mobile())


@app.route('/text')
def nlp_page():
    return render_template('nlp.jinja2')


@app.route('/nlp')
def do_nlp():
    text = request.args.get('text')
    model_type = request.args.get('type')
    language = request.args.get('language')
    print(text, model_type, language)
    print(nlp_models[f"{language} {model_type}"].predict([text])[0][0])
    return jsonify(pred=str(nlp_models[f"{language} {model_type}"].predict([text])[0][0]))


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
    except:
        return "Can't extract text from image"

    print("the text:", snir.header(image_text))
    mydb = mysql.connector.connect(
        host="localhost",
        user="USER",
        password="YOUR_SQL_PASSWORD",
        database="YOUR_DB",
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
    json_request = request.get_json()
    data = json_request["base64_image"]
    data = data[data.index(",") + 1:]
    data = bytes(data, encoding='utf8')
    bytes_image = base64.b64decode(data)
    im = Image.open(io.BytesIO(bytes_image))
    im = im.crop((json_request["x"], json_request["y"], json_request["width"] + json_request["x"], json_request["height"] + json_request["y"]))
    lang = json_request['language']

    try:
        image_text = pytesseract.image_to_string(im, lang=lang).strip()
    except Exception as e:
        print(e)
        return jsonify(error="Can't extract text from image")

    try:
        numpy_image = numpy.array(im)

        img = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

        boxes = pytesseract.image_to_boxes(img)
        height, width, _ = img.shape

        for box in boxes.splitlines():
            box = box.split()
            img = cv2.rectangle(img, (int(box[1]), height - int(box[2])), (int(box[3]), height - int(box[4])), (0, 255, 0), 0)

    except Exception as e:
        print(e)
        return jsonify(error="Can't extract text from image")

    if not image_text:
        print("blank image_text")
        return jsonify(error="Can't extract text from image")

    return jsonify(image_text=image_text)


@app.route('/get_food_class', methods=['POST'])
def do_classify():
    print("in get_food_class")
    start = time.time()

    json_request = request.get_json()
    print(time.time() - start)
    data = json_request["base64_image"]
    data = data[data.index(",") + 1:]
    data = bytes(data, encoding='utf8')

    bytes_image = base64.b64decode(data)
    img_shape = 224
    img = tf.image.decode_image(bytes_image, channels=3)
    print(img.shape)
    img = tf.image.resize(img, size=[img_shape, img_shape])
    img_expanded = tf.expand_dims(img, axis=0)
    pred_prob = food_101_model.predict(img_expanded)
    predicted_class = class_names[numpy.argmax(pred_prob)]
    pred_max_class = pred_prob.max()
    top_5_pred = []
    for num in range(5):
        top_5_pred.append(str(class_names[numpy.argmax(pred_prob)]) + " " + str(round(pred_prob.max() * 100, 2)) + "%")
        pred_prob[0][numpy.argmax(pred_prob)] = 0
    "".split()
    im = Image.fromarray(img.numpy().astype("uint8"))
    raw_bytes = io.BytesIO()
    im.save(raw_bytes, "JPEG")
    raw_bytes.seek(0)
    base64_jpg_data = base64.b64encode(raw_bytes.read())
    print(top_5_pred)
    return jsonify(
        base_64_image=base64_jpg_data.decode("utf-8"),
        predicted_class=predicted_class,
        top_5_pred=top_5_pred,
        probability=str(round(pred_max_class * 100, 2))
    )
