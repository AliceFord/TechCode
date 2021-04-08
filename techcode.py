import png
import random
import enum
from PIL import Image
import math


class EncodeModes(enum.Enum):
	BYTES = 0


BITMASK_MODES = [lambda i, j: (i + j) % 2 == 0, lambda i, j: i % 2 == 0, lambda i, j: j % 3 == 0, lambda i, j: (i + j) % 3 == 0, lambda i, j: (i // 2 + j // 3) % 2 == 0, lambda i, j: ((i * j) % 2) + ((i * j) % 3) == 0, lambda i, j: (((i * j) % 2) + ((i * j) % 3)) % 2 == 0, lambda i, j: (((i + j) % 2) + ((i * j) % 3)) % 2 == 0]


def writeData(data, palette, size, bitmask, filename="data.png", writeMetadata=True):
	f = open(filename, 'wb')
	w = png.Writer(size[0], size[1], greyscale=False)

	paletteCounter = 0

	if writeMetadata:
		for i in range(16):
			if i % 2 == 1:
				data[i] = palette[paletteCounter] + data[i]
				paletteCounter += 1
			else:
				data[i] = (0, 0, 0) + data[i]

		for i in range(16, size[0]-1):
			data[i] = (0, 0, 0) + data[i]

		data.append([])
		for i in range(16):
			if i % 2 == 1:
				data[size[1]-1].extend(palette[paletteCounter])
				paletteCounter += 1
			else:
				data[size[1]-1].append(0)
				data[size[1]-1].append(0)
				data[size[1]-1].append(0)

		for i in range(16, size[0]):
			data[size[1]-1].append(0)
			data[size[1]-1].append(0)
			data[size[1]-1].append(0)

		(data[size[1]-1][4*3], data[size[1]-1][4*3+1], data[size[1]-1][4*3+2]) = palette[bitmask]

		data[size[1]-1] = tuple(data[size[1]-1])

	w.write(f, data)
	f.close()


def encodeData(data, palette, encodeMode, bitmask, size):
	if encodeMode == EncodeModes.BYTES:
		hexData = "".join([str(hex(ord(c))).replace("0x", "") for c in data])
		if size == "auto":
			foundSize = math.ceil(math.sqrt((len(data) + 4)*2)) + 1

			if foundSize < 17:
				size = (17, 17)
			else:
				size = (foundSize, foundSize)
		else:
			if ((size[0] - 1) * (size[1] - 1)) - len(hexData) <= 4:
				raise Exception("Text too large for chosen size techcode!")

		hexData += "ffff"
		hexData += "".join([random.choice("0123456789abcdef") for _ in range(((size[0] - 1) * (size[1] - 1)) - len(hexData))])
		finalData = [[] for _ in range(size[0]-1)]
		for i in range(size[0]-1):
			for j in range(size[1]-1):
				finalData[i].extend(palette[int(hexData[i * (size[0]-1) + j], base=16)])

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
	for i in range(8):
		palette.append(pixels[size[0] * (i * 2 + 1)])
	for i in range(8):
		palette.append(pixels[(size[1]-1) * size[0] + (i * 2 + 1)])

	bml = BITMASK_MODES[palette.index(pixels[size[1] * (size[0] - 1) + 4])]

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

	output = ""

	finished = False
	jCounter = math.ceil((size[1]-1)/2)
	for i in range(size[0]-1):
		if finished:
			break
		for j in range(jCounter):
			if size[0] % 2 == 0 and i % 2 == 1:
				if j < jCounter-1:
					if colourPalette.index(dataWithoutMeta[i*(size[0]-1)+j*2+1]) * 16 + colourPalette.index(dataWithoutMeta[i*(size[0]-1)+j*2+2]) == 255:
						finished = True
						break
					output += chr(colourPalette.index(dataWithoutMeta[i*(size[0]-1)+j*2+1]) * 16 + colourPalette.index(dataWithoutMeta[i*(size[0]-1)+j*2+2]))
			else:
				try:
					if colourPalette.index(dataWithoutMeta[i*(size[0]-1)+j*2]) * 16 + colourPalette.index(dataWithoutMeta[i*(size[0]-1)+j*2+1]) == 255:
						finished = True
						break
					output += chr(colourPalette.index(dataWithoutMeta[i*(size[0]-1)+j*2]) * 16 + colourPalette.index(dataWithoutMeta[i*(size[0]-1)+j*2+1]))
				except IndexError:
					break

	return output


if __name__ == '__main__':
	colourPalette = [(0, 0, 128), (0, 128, 0), (0, 128, 128), (128, 0, 0), (128, 0, 128), (128, 128, 0), (128, 128, 128), (128, 128, 255), (128, 255, 128), (128, 255, 255), (255, 128, 128), (255, 128, 255), (255, 255, 128), (0, 128, 255), (128, 255, 0), (255, 0, 128)]

	autoSize = input("Automatically choose techcode size (y/n)? ")
	if "n" in autoSize:
		codeSize = (int(input("X axis size (min 17): ")), int(input("Y axis size (min 17): ")))
	else:
		codeSize = "auto"
	bitmaskData = 4
	currentData = encodeData(input("Enter the data to be encoded: "), colourPalette, EncodeModes.BYTES, bitmaskData, codeSize)
	print(f"Size chosen: {len(currentData)+1}x{len(currentData[0])//3+1}")
	writeData(currentData, colourPalette, (len(currentData)+1, len(currentData[0])//3+1), bitmaskData)
	im = Image.open('data.png', 'r')
	print(decodeData(list(im.getdata()), (im.width, im.height)))
