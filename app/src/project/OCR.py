import pytesseract
import unidecode
from PIL import Image, ImageOps
from io import BytesIO
import re

class ImageText:
    def __init__(self, image=BytesIO(), text=""):
        self.image = image
        self.text = {"description_text": text.lower(), "image_text": ""}

    def image_to_text(self):
        """Extract the txt from an image using OCR (Object character recognition). The
                   library pytesseract is being used for that purpose (more details in:
                   https://pytesseract.readthedocs.io/en/latest/ """
        # pytesseract.pytesseract.tesseract_cmd = r'D:\Programas\Tesseract-OCR\tesseract.exe'
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(self.image, config=config, lang="spa")

        # Clean the text for deleting white lines
        new_text = ""
        for line in text.split("\n"):
            if not re.match(r'^\s*$', line):
                new_text += line + "\n"

        # Remove accents
        new_text = unidecode.unidecode(new_text)

        # To lower case
        new_text = new_text.lower()

        self.text["image_text"] = new_text


    def preprocess_image(self):
        """Apply some transformations to the image in order to fit it for the OCR process.
         The process consists of:
            1. Converting the image to B&W, by setting all the pixels over a threshold to be white,
                while the pixels under the threshold be black.
            2. Invert the image. As the bet365 images have grey background, the image will have black
             background and white letter. We want it the other way round as it is easier for the OCR
             to read."""

        pixels = self.image.load()
        # Set to B&W
        th = 120
        for i in range(self.image.size[0]):  # for every pixel:
            for j in range(self.image.size[1]):
                if max(pixels[i, j]) > th:
                    pixels[i, j] = (255, 255, 255)
                else:
                    pixels[i, j] = (0, 0, 0)

        # Invert the image
        self.image = ImageOps.invert(self.image)







# def read_text(image):
#     """Extract the txt from an image using OCR (Object character recognition). The
#             library pytesseract is being used for that purpose (more details in:
#             https://pytesseract.readthedocs.io/en/latest/ """
#     pytesseract.pytesseract.tesseract_cmd = r'D:\Programas\Tesseract-OCR\tesseract.exe'
#
#     text = pytesseract.image_to_string(image, lang="eng")
#     print(text)
#     return text
#
#
# if __name__ == "__main__":
#
#     # Read the image passed through the arguments
#     ap = argparse.ArgumentParser()
#     ap.add_argument("-i", "--image", required=True)
#     args = vars(ap.parse_args())
#     image = Image.open(args["image"])
#
#     # Create object
#     obj = ImageText(image)
#     # Call pre processing image method
#     obj.preprocess_image()
#     # Extract text from the image through OCR
#     obj.image_to_text()
#     text = obj.text
#
#     print(text)
#     # obj = OCR()
#     # obj.image_to_text()
    # read_text()