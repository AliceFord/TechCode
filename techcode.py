import csv

import png
import random
import enum
from PIL import Image
import math
import string
import unireedsolomon as rs

from tkinter.filedialog import askopenfile
from tkinter import Tk


class EncodeMode(enum.IntEnum):
	BYTES = 0
	NUMERIC = 1


BITMASK_MODES = [lambda i, j: False, lambda i, j: i % 2 == 0, lambda i, j: j % 3 == 0, lambda i, j: (i + j) % 3 == 0, lambda i, j: (i // 2 + j // 3) % 2 == 0, lambda i, j: ((i * j) % 2) + ((i * j) % 3) == 0, lambda i, j: (((i * j) % 2) + ((i * j) % 3)) % 2 == 0, lambda i, j: (((i + j) % 2) + ((i * j) % 3)) % 2 == 0]
EC_LEVEL_CONVERTER = [1.07, 1.15, 1.25, 1.30]


# TODO: Alphanumeric mode


def writeData(data, palette, size, bitmask, encodeMode, ecLevel, filename="data.png", writeMetadata=True):
	f = open(filename, 'wb')
	w = png.Writer(size[0], size[1], greyscale=False)

	paletteCounter = 0

	if writeMetadata:
		for i in range(size[0]-1):
			if i == 2:
				data[i] = palette[ecLevel] + data[i]

			elif i % 2 == 1 and len(palette) != paletteCounter:
				data[i] = palette[paletteCounter] + data[i]
				paletteCounter += 1
			else:
				data[i] = (0, 0, 0) + data[i]

		data.append([])
		for i in range(size[1]):
			if i % 2 == 1 and len(palette) != paletteCounter:
				data[size[1]-1].extend(palette[paletteCounter])
				paletteCounter += 1
			else:
				data[size[1]-1].append(0)
				data[size[1]-1].append(0)
				data[size[1]-1].append(0)

		(data[size[1]-1][4*3], data[size[1]-1][4*3+1], data[size[1]-1][4*3+2]) = palette[bitmask]
		(data[size[1]-1][2*3], data[size[1]-1][2*3+1], data[size[1]-1][2*3+2]) = palette[encodeMode.value]

		data[size[1]-1] = tuple(data[size[1]-1])

	w.write(f, data)
	f.close()


def int2base(x, base):
	digs = string.digits + string.ascii_letters
	if x < 0:
		sign = -1
	elif x == 0:
		return digs[0]
	else:
		sign = 1

	x *= sign
	digits = []

	while x:
		digits.append(digs[int(x % base)])
		x = int(x / base)

	if sign < 0:
		digits.append("-")

	digits.reverse()

	return ''.join(digits)


def encodeData(data, palette, encodeMode, bitmask, size, ecLevel):
	coder = rs.RSCoder(math.ceil(len(data) * EC_LEVEL_CONVERTER[ecLevel]), len(data))
	encData = coder.encode(data)
	encData = bytearray(encData.encode())
	encData.insert(len(data), 0)
	if encodeMode == EncodeMode.BYTES:
		minBits = 0
		counter = 256
		while True:
			counter /= len(palette)
			minBits += 1
			if counter <= 1:
				break
		hexData = "".join(["0"*(minBits-len(str(int2base(c, len(palette))))) + str(int2base(c, len(palette))) for c in encData])

		if size == "auto":
			foundSize = math.ceil(math.sqrt((len(encData) + 4)*minBits)) + 1

			if foundSize < len(palette)+1:
				size = (len(palette)+1, len(palette)+1)
			else:
				size = (foundSize, foundSize)
		else:
			if ((size[0] - 1) * (size[1] - 1)) - len(hexData) <= 4:
				raise Exception("Text too large for chosen size techcode!")

		hexData += "0000"
		hexData += "".join([random.choice((string.digits + string.ascii_letters)[:len(palette)]) for _ in range(((size[0] - 1) * (size[1] - 1)) - len(hexData))])
		finalData = [[] for _ in range(size[0]-1)]
		for i in range(size[0]-1):
			for j in range(size[1]-1):
				finalData[i].extend(palette[int(hexData[i * (size[0]-1) + j], base=len(palette))])

	for i in range(size[0]-1):
		for j in range(size[1]-1):
			if BITMASK_MODES[bitmask](i, j):
				tempData = [finalData[i][j*3], finalData[i][j*3+1], finalData[i][j*3+2]]
				tempData = tempData[1:] + tempData[:1]
				finalData[i][j*3] = tempData[0]
				finalData[i][j*3+1] = tempData[1]
				finalData[i][j*3+2] = tempData[2]

	for i in range(size[0]-1):
		finalData[i] = tuple(finalData[i])

	return finalData


def decodeData(pixels, size):
	# Get palette
	palette = []
	for i in range(size[1]//2):
		if pixels[size[0] * (i * 2 + 1)] != (0, 0, 0):
			palette.append(pixels[size[0] * (i * 2 + 1)])
	for i in range(size[0]//2):
		if pixels[(size[1]-1) * size[0] + (i * 2 + 1)] != (0, 0, 0):
			palette.append(pixels[(size[1]-1) * size[0] + (i * 2 + 1)])

	bml = BITMASK_MODES[palette.index(pixels[size[1] * (size[0] - 1) + 4])]
	encodingMode = EncodeMode(palette.index(pixels[size[1] * (size[0] - 1) + 2]))

	dataWithoutMeta = []
	for i in range(size[0]-1):
		for j in range(1, size[1]):
			dataWithoutMeta.append(pixels[i*size[0]+j])

	for i in range(size[0]-1):
		for j in range(size[1]-1):
			if bml(i, j):
				temp = dataWithoutMeta[i*(size[0]-1)+j]
				temp = temp[2:] + temp[:2]
				dataWithoutMeta[i*(size[0]-1)+j] = tuple(temp)

	minBits = 0
	counter = 256
	while True:
		counter /= len(palette)
		minBits += 1
		if counter <= 1:
			break

	if encodingMode == EncodeMode.BYTES:
		output = bytearray()
		for i in range(0, ((size[0]-1) * (size[1]-1)), minBits):
			if palette.index(dataWithoutMeta[i]) + palette.index(dataWithoutMeta[i+1]) + palette.index(dataWithoutMeta[i+2]) + palette.index(dataWithoutMeta[i+3]) == 0:
				break
			current = 0
			for j in range(minBits):
				current += palette.index(dataWithoutMeta[i + j]) * (len(palette) ** (minBits - j - 1))
			output.append(current)
		ecLevel = EC_LEVEL_CONVERTER[palette.index(pixels[size[0] * 2])]
		coder = rs.RSCoder(math.ceil(len(output[:output.find(b"\x00")]) * ecLevel), len(output[:output.find(b"\x00")]))
		del output[output.index(b"\x00")]
		return coder.decode(output.decode())


if __name__ == '__main__':
	colourPalette = []
	# for _i in range(12):
	# 	colourPalette.append((math.floor((_i/13) * 255), 255, 255))
	# for _i in range(12):
	# 	colourPalette.append((255, math.floor((_i/13) * 255), 255))
	# for _i in range(12):
	# 	colourPalette.append((255, 255, math.floor((_i/13) * 255)))
	openPalette = input("Open previous palette (y/n)? ")
	if "n" in openPalette:
		colourPalette = [(0, 128, 128), (128, 0, 128), (128, 128, 0), (0, 128, 0), (0, 0, 128), (128, 0, 0),
		                 (128, 128, 128), (255, 128, 255), (255, 255, 128), (128, 255, 255), (128, 128, 255),
		                 (128, 255, 128), (255, 128, 128), (0, 128, 255), (128, 255, 0), (255, 0, 128)]
	else:
		Tk().withdraw()
		filepath = askopenfile()
		file = open(filepath.name)
		reader = csv.reader(file, delimiter=" ")
		for row in reader:
			colourPalette.append((int(row[0]), int(row[1]), int(row[2])))

	autoSize = input("Automatically choose techcode size (y/n)? ")
	if "n" in autoSize:
		codeSize = (int(input("X axis size: ")), int(input("Y axis size: ")))
	else:
		codeSize = "auto"
	bitmaskData = 4
	encodeLevel = 3
	currentData = encodeData(input("Enter the data to be encoded: "), colourPalette, EncodeMode.BYTES, bitmaskData, codeSize, encodeLevel)
	print(f"Size chosen: {len(currentData)+1}x{len(currentData[0])//3+1}")
	writeData(currentData, colourPalette, (len(currentData)+1, len(currentData[0])//3+1), bitmaskData, EncodeMode.BYTES, encodeLevel)
	im = Image.open('data.png', 'r')
	print(decodeData(list(im.getdata()), (im.width, im.height))[0])
