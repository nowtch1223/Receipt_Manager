import os
from flask import Flask, render_template
from flask import request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np

from datetime import date
import cv2
import matplotlib.pyplot as plt
import matplotlib
import io
import csv
from datetime import datetime as dt


from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///beginners.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO']=True
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    student_id = db.Column(db.String(4))
    password = db.Column(db.String(12))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    store = db.Column(db.String(50))
    num = db.Column(db.Integer)
    natural_price = db.Column(db.Integer)
    sell_price = db.Column(db.Integer)
    buy_date =db.Column(db.String(30))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))
    # User_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
db.create_all()

@app.route('/products')
def product_list():
    products = Product.query.all()
    return render_template('price.html', products=products)

@app.route('/addReceipt', methods=['GET', 'POST'])
def addReceipt():
    if request.method == 'GET':
        return render_template('addReceipt.html')
    if request.method == 'POST':
        form_title = request.form.get('title')
        form_store=request.form.get('store')
        form_num=request.form.get('num')
        form_natural_price=request.form.get('natural_price')
        form_buy_date=request.form.get('buy_date')
        form_sell_price=request.form.get('sell_price')

        product = Product(
            buy_date=form_buy_date,
            store=form_store,
            title=form_title,
            num=form_num,
            natural_price=form_natural_price,
            sell_price=form_sell_price
            
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('product_list'))




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        student_id = request.form.get('student_id')
        password = request.form.get('password')

        user = User(username=username, student_id=student_id, 
                    password=generate_password_hash(password, method='sha256'))

        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        student_id = request.form.get('student_id')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/scan')
    else:
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

img_path = "static/imgs/.jpg"
@app.route('/scan', methods=["GET", "POST"])
def scan():
    global img_path
    img_dir = "static/imgs/"
    if request.method == 'GET': img_path=None
    elif request.method == 'POST':
        #### POSTにより受け取った画像を読み込む
        stream = request.files['img'].stream
        img_array = np.asarray(bytearray(stream.read()), dtype=np.uint8)
        img = cv2.imdecode(img_array, 1)
        #### 現在時刻を名前として「imgs/」に保存する
        #dt_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        img_path = img_dir +  ".jpg"
        cv2.imwrite(img_path, img)
        return redirect('/table')
    #### 保存した画像ファイルのpathをHTMLに渡す
    return render_template('scan.html') 


csv_path = "csvfile"
@app.route('/table', methods=["GET", "POST"])
def table():
    global csv_path
    if request.method == 'GET': 
        csv_path=None
    elif request.method == 'POST':
        with open('csvfile/scan_1.csv') as f:
            reader = csv.reader(f)
        return render_template('table.html',csv_path=csv_path)
    return render_template('table.html') 


##################################################################
input_file = img_path


from google.cloud import vision

client = vision.ImageAnnotatorClient()
with io.open(input_file, 'rb') as image_file:
    content = image_file.read()
image = vision.Image(content=content)
response = client.document_text_detection(image=image)

print(response.text_annotations[0].description)

def get_sorted_lines(response):
    document = response.full_text_annotation
    bounds = []
    for page in document.pages:
      for block in page.blocks:
        for paragraph in block.paragraphs:
          for word in paragraph.words:
            for symbol in word.symbols:
              x = symbol.bounding_box.vertices[0].x
              y = symbol.bounding_box.vertices[0].y
              text = symbol.text
              bounds.append([x, y, text, symbol.bounding_box])
    bounds.sort(key=lambda x: x[1])
    old_y = -1
    line = []
    lines = []
    threshold = 1
    for bound in bounds:
      x = bound[0]
      y = bound[1]
      if old_y == -1:
        old_y = y
      elif old_y-threshold <= y <= old_y+threshold:
        old_y = y
      else:
        old_y = -1
        line.sort(key=lambda x: x[0])
        lines.append(line)
        line = []
      line.append(bound)
    line.sort(key=lambda x: x[0])
    lines.append(line)
    return lines

img = cv2.imread(input_file, cv2.IMREAD_COLOR)

lines = get_sorted_lines(response)
for line in lines:
  texts = [i[2] for i in line]
  texts = ''.join(texts)
  bounds = [i[3] for i in line]
  print(texts)
  for bound in bounds:
    p1 = (bounds[0].vertices[0].x, bounds[0].vertices[0].y)   # top left
    p2 = (bounds[-1].vertices[1].x, bounds[-1].vertices[1].y) # top right
    p3 = (bounds[-1].vertices[2].x, bounds[-1].vertices[2].y) # bottom right
    p4 = (bounds[0].vertices[3].x, bounds[0].vertices[3].y)   # bottom left
    cv2.line(img, p1, p2, (0, 255, 0), thickness=1, lineType=cv2.LINE_AA)
    cv2.line(img, p2, p3, (0, 255, 0), thickness=1, lineType=cv2.LINE_AA)
    cv2.line(img, p3, p4, (0, 255, 0), thickness=1, lineType=cv2.LINE_AA)
    cv2.line(img, p4, p1, (0, 255, 0), thickness=1, lineType=cv2.LINE_AA)

plt.figure(figsize=[10,10])
plt.axis('off')
plt.imshow(img[:,:,::-1]);plt.title("img_by_line")
plt.show()

import re

def get_matched_string(pattern, string):
    prog = re.compile(pattern)
    result = prog.search(string)
    if result:
        return result.group()
    else:
        return False

pattern_dict = {}
pattern_dict['date'] = r'[12]\d{3}[/\-年](0?[1-9]|1[0-2])[/\-月](0?[1-9]|[12][0-9]|3[01])日?'
#pattern_dict['time'] = r'((0?|1)[0-9]|2[0-3])[:時][0-5][0-9]分?'
pattern_dict['item_name'] = r'^(?=.*\d)(?!.*税)(?!.*nanaco)(?!.*年)(?!.*電)(?!.*合計)(?!.*Edy)(?!.*残高)(?!.*\d\d\d\d)(?!.*セブン)(?!.*栃木)(?!.*お預り)(?!.*釣).*$'

mylist = []
header = ['date','item_name','price'] 
j = 0
for line in lines:
  texts = [i[2] for i in line]
  texts = ''.join(texts)
  for key, pattern in pattern_dict.items():
    if key == 'date' and get_matched_string(pattern, texts):
       date_string = get_matched_string(pattern, texts)
    else:
       matched_string = get_matched_string(pattern, texts)
       if matched_string :
        if key == 'item_name':
          mylist.append([ date_string+"日",matched_string[:-3],matched_string[-3:]])
        print(mylist)

#CSV出力
from pathlib import Path
def print_lines():
    print(Path('csvfile').read_text())


# csvモジュールを使って複数行の内容をCSVファイルに書き込み
with open('scan_1.csv', 'w', newline='', encoding='utf_8_sig') as f:
    writer = csv.writer(f)
    writer.writerows(mylist)


if __name__ == '__main__':
    app.run(debug=True)

