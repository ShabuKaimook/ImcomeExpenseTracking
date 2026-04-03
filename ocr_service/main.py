import pytesseract
from PIL import Image

from bank_parsers.parser_factory import ParserFactory

def main():
	img = Image.open('test_imgs/make_des.JPG')
	texts = pytesseract.image_to_string(img, lang='tha+eng').splitlines()
	texts = [text for text in texts if text.strip() != '']  # Remove empty lines
 
	for i, text in enumerate(texts):
		print(f'{i}: {text}')

	# find the parser for the bank
	parser_factory = ParserFactory()
	parser = parser_factory.get_parser(texts)

	# get transaction data from parser by sending texts from ocr
	transaction = parser.parse(texts)
	print(transaction)
 
if __name__ == "__main__":
    main()