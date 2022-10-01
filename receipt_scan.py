import os
import cv2
import pyocr
import matplotlib.pyplot as plt

from PIL import Image

import rectangle_detection

# tesseractのパス設定
TESSERACT_PATH = 'C:\\Program Files\\Tesseract-OCR\\' #インストールしたTesseract-OCRのpath
TESSDATA_PATH = 'C:\\Program Files\\Tesseract-OCR\\tessdata' #tessdataのpath

os.environ["PATH"] = os.environ['PATH'] + TESSERACT_PATH
os.environ["TESSDATA_PREFIX"] = TESSDATA_PATH


def imshow(img):
    plt.imshow(img)
    plt.colorbar()
    plt.show()

# 画像から文字をスキャンする
def receipt_scan(img):
    """

    Args:
        img (PIL.Image): main 関数で読み込んだ画像

    Returns:
        txt: main 関数に取得した文字列を返す
    """

    # OCRエンジンを取得
    engines = pyocr.get_available_tools()
    engine = engines[0]

    # 対応言語取得
    #langs = engine.get_available_languages()

    # 画像の文字を読み込む
    builder = pyocr.builders.TextBuilder(tesseract_layout=6)
    txt = engine.image_to_string(img, lang="jpn", builder=builder)

    return txt

def main():
    # 画像を単枚入力
    # 複数の場合はまだ考えない
    img_path = "./receipt_img"
    #img_path = "./img"
    img_name = "IMG_5534.jpg"
    save_dir = "./result"
    threshold = 128
    ksize = 51

    # 画像を開く
    img = cv2.imread(os.path.join(img_path, img_name))
    #img = Image.fromarray(img)

    # 画像の矩形検出・回転補正・しわ除去
    img = rectangle_detection.process_img(img, threshold, ksize)
    #imshow(img)

    # 画像から文字を読み込む(receipt_scan 関数)
    txt = receipt_scan(img)
    #print(txt)
    
    # テキスト出力
    f = open(os.path.join(save_dir, 'result_{}.txt').format(os.path.splitext(img_name)[0]), 'w')
    f.write(txt)
    f.close()


if __name__ == "__main__":
    main()