from datetime import date
import cv2
import matplotlib.pyplot as plt
import matplotlib
import io
import csv
from datetime import datetime as dt

input_file = '2.jpg'


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
pattern_dict['item_name'] = r'^(?=.*\d)(?!.*税)(?!.*nanaco)(?!.*年)(?!.*電)(?!.*合計)(?!.*Edy)(?!.*残高)(?!.*\d\d\d\d)(?!.*セブン)(?!.*栃木).*$'

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
          mylist.append([date_string+"日", matched_string[:-3],matched_string[-3:]])
        print(mylist)

#CSV出力
from pathlib import Path
def print_lines():
    print(Path('test.csv').read_text())


# csvモジュールを使って複数行の内容をCSVファイルに書き込み
with open('test.csv', 'w', newline='', encoding='utf_8_sig') as f:
    writer = csv.writer(f)
    writer.writerows(mylist)
      