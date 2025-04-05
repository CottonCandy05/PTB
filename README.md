Open a command prompt and install Pillow:
pip install pillow

Prepare the image:

Ensure the image is a PNG.

The image should be black and white only with a black background.(anything except black gets converted to pure 1 bit white)

Place the image in the same folder as the Python programs.

#PngToBytearray.py
To convert the PNG to a bytearray, type in the command prompt:
python PngToBytearray.py your_png.png my_output_data.py

Copy and use the bytearray generated in the newly created my_output_data.py file.

#BytearrayToPng.py
To reconstruct the image from the bytearray, open a command prompt and type:
python BytearrayToPng.py my_output_data.py output_reconstructed.png W H
(Replace W and H with the original resolution in pixels.)
(example: if my original png was 128x64 the prompt would be > python BytearrayToPng.py my_output_data.py output_reconstructed.png 128 64)
