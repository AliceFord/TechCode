import png
import random
import enum
from PIL import Image


class EncodeModes(enum.Enum):
	BYTES = 0


def writeData(data, palette, filename="data.png", writeMetadata=True):
	f = open(filename, 'wb')
	w = png.Writer(17, 17, greyscale=False)

	paletteCounter = 0

	if writeMetadata:
		for i in range(16):
			if i % 2 == 1:
				data[i] = palette[paletteCounter] + data[i]
				paletteCounter += 1
			else:
				data[i] = (0, 0, 0) + data[i]

		data.append([])
		for i in range(17):
			if i % 2 == 1:
				data[16].extend(palette[paletteCounter])
				paletteCounter += 1
			else:
				data[16].append(0)
				data[16].append(0)
				data[16].append(0)

		data[16] = tuple(data[16])

	w.write(f, data)
	f.close()


def encodeData(data, palette, encodeMode, bml, size):  # bml = bitmask lambda
	if encodeMode == EncodeModes.BYTES:
		hexData = "".join([str(hex(ord(c))).replace("0x", "") for c in data])
		hexData += "".join(["0" for _ in range(256 - len(hexData))])
		finalData = [[] for _ in range(16)]
		for i in range(16):
			for j in range(16):
				finalData[i].extend(palette[int(hexData[i * 16 + j], base=16)])

	for i in range(16):  # Static bitmask for now
		for j in range(16):
			if bml(i, j):
				tempData = [finalData[i][j*3], finalData[i][j*3+1], finalData[i][j*3+2]]
				tempData = tempData[1:] + tempData[:1]
				finalData[i][j*3] = tempData[0]
				finalData[i][j*3+1] = tempData[1]
				finalData[i][j*3+2] = tempData[2]

	for i in range(16):
		finalData[i] = tuple(finalData[i])

	return finalData


def decodeData(pixels, bml):
	# Get palette
	palette = []
	for i in range(8):
		palette.append(pixels[17 * (i * 2 + 1)])
	for i in range(8):
		palette.append(pixels[16 * 17 + (i * 2 + 1)])

	dataWithoutMeta = []
	for i in range(16):
		for j in range(1, 17):
			dataWithoutMeta.append(pixels[i*17+j])

	for i in range(16):  # Static bitmask for now
		for j in range(16):
			if bml(i, j):
				temp = dataWithoutMeta[i*16+j]
				temp = temp[2:] + temp[:2]
				dataWithoutMeta[i*16+j] = tuple(temp)

	output = ""

	for i in range(16):
		for j in range(8):
			output += chr(colourPalette.index(dataWithoutMeta[i*16+j*2]) * 16 + colourPalette.index(dataWithoutMeta[i*16+j*2+1]))

	return output


if __name__ == '__main__':
	colourPalette = [(0, 0, 128), (0, 128, 0), (0, 128, 128), (128, 0, 0), (128, 0, 128), (128, 128, 0), (128, 128, 128), (128, 128, 255), (128, 255, 128), (128, 255, 255), (255, 128, 128), (255, 128, 255), (255, 255, 128), (0, 128, 255), (128, 255, 0), (255, 0, 128)]

	bitmaskLambda = lambda i, j: (((i + j) % 2) + ((i * j) % 3)) % 2 == 0

	currentData = encodeData(input("Enter the data to be encoded: "), colourPalette, EncodeModes.BYTES, bitmaskLambda, (int(input("X axis size (min 17): ")), int(input("Y axis size (min 17): "))))

	writeData(currentData, colourPalette)

	print(decodeData(list(Image.open('data.png', 'r').getdata()), bitmaskLambda))
