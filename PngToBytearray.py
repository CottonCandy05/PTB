# Recommended filename: PngToBytearray.py
# Usage: go to console and run "python PngToBytearray.py your_png.png my_output_data.py"

from PIL import Image, ImageColor
import sys
import math
import os

def image_to_mono_vlsb_alpha_safe(image_path, debug_dir=None):
    try:
        if debug_dir and not os.path.exists(debug_dir):
            try:
                os.makedirs(debug_dir)
                print(f"Created debug directory: {debug_dir}", file=sys.stderr)
            except OSError as e:
                print(f"Warning: Could not create debug directory '{debug_dir}': {e}", file=sys.stderr)
                debug_dir = None

        def save_debug_image(img, filename_suffix):
            if debug_dir:
                base = os.path.splitext(os.path.basename(image_path))[0]
                save_path = os.path.join(debug_dir, f"{base}_{filename_suffix}.png")
                try:
                    if 'A' in img.mode:
                        img.save(save_path, 'PNG')
                    else:
                        img.save(save_path)
                    print(f"Saved debug image: {save_path}", file=sys.stderr)
                except Exception as e:
                    print(f"Warning: Failed to save debug image '{save_path}': {e}", file=sys.stderr)

        img = Image.open(image_path)
        print(f"Opened image '{image_path}' with mode: {img.mode}", file=sys.stderr)
        save_debug_image(img, "0_original_opened")

        if 'A' in img.mode:
            print("Alpha channel detected, blending onto white background...", file=sys.stderr)
            bg_white = Image.new('RGB', img.size, ImageColor.getrgb("white"))
            alpha = img.split()[-1]
            bg_white.paste(img, mask=alpha)
            img_processed = bg_white
            save_debug_image(img_processed, "1a_blended_on_white_RGB")
        elif img.mode != 'L' and img.mode != '1':
            print(f"Converting mode {img.mode} to RGB before grayscale.", file=sys.stderr)
            img_processed = img.convert('RGB')
            save_debug_image(img_processed, "1a_converted_to_RGB")
        else:
            img_processed = img
            print(f"Image mode {img.mode} suitable for direct grayscale conversion.", file=sys.stderr)

        img_gray = img_processed.convert('L')
        print(f"Image converted to grayscale mode: {img_gray.mode}", file=sys.stderr)
        save_debug_image(img_gray, "1b_grayscale")

        img_mapped = img_gray.point(lambda p: 255 if p > 0 else 0, mode='L')
        print(f"Applied custom threshold (non-black -> white)", file=sys.stderr)
        save_debug_image(img_mapped, "2_mapped_nonblack_is_white_L")

        img_mono = img_mapped.convert('1')
        print(f"Image successfully converted to final 1-bit mode: {img_mono.mode}", file=sys.stderr)
        save_debug_image(img_mono, "3_final_1bit")

        width, height = img_mono.size
        print(f"Processing image: {width} x {height} pixels", file=sys.stderr)

        output_bytearray = bytearray()
        pages = math.ceil(height / 8)
        buffer_size = pages * width
        print(f"Pages: {pages}, Bytes per page row: {width}", file=sys.stderr)

        for page in range(pages):
            for x in range(width):
                current_byte = 0
                for y_bit in range(8):
                    y = (page * 8) + y_bit
                    if y < height:
                        pixel = img_mono.getpixel((x, y))
                        bit = 1 if pixel == 255 else 0
                        current_byte |= (bit << y_bit)
                output_bytearray.append(current_byte)

        print(f"Total bytes generated: {len(output_bytearray)}", file=sys.stderr)
        if len(output_bytearray) != buffer_size:
            print(f"Warning: Generated byte array size ({len(output_bytearray)}) does not match expected size ({buffer_size}).", file=sys.stderr)

        return output_bytearray, width, height

    except FileNotFoundError:
        print(f"Error: Image file not found at '{image_path}'", file=sys.stderr)
        return None, 0, 0
    except Exception as e:
        print(f"An error occurred during conversion: {e}", file=sys.stderr)
        return None, 0, 0

def save_bytearray_to_py_file(byte_data, width, height, output_filename):
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            print(f"Writing bytearray definition to '{output_filename}'...", file=sys.stderr)
            f.write(f"# Image: {width}x{height}, Format: MONO_VLSB (Alpha-Safe Non-Black=White), Bytes: {len(byte_data)}\n")
            f.write(f"image_data = bytearray([\n")
            f.write("    ")
            for i, byte in enumerate(byte_data):
                f.write(f"0x{byte:02X}")
                if i < len(byte_data) - 1:
                    f.write(", ")
                if (i + 1) % 16 == 0 and i < len(byte_data) - 1:
                    f.write("\n    ")
            f.write("\n])\n")
        print(f"Successfully saved bytearray to '{output_filename}'.", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Error writing to output file '{output_filename}': {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        script_name = sys.argv[0]
        print(f"\nUsage: python {script_name} <input_image.png> <output_file.py> [--debug]\n", file=sys.stderr)
        print("  <input_image.png>: Path to the source image file.", file=sys.stderr)
        print("  <output_file.py>:  Path to save the generated Python bytearray file.", file=sys.stderr)
        print("  --debug (optional): Save intermediate processing steps as images in './debug_images'.\n", file=sys.stderr)
        sys.exit(1)

    image_file = sys.argv[1]
    output_py_file = sys.argv[2]
    enable_debug = False
    debug_directory = "debug_images"

    if len(sys.argv) == 4 and sys.argv[3] == '--debug':
        enable_debug = True
        print("Debug mode enabled. Intermediate images will be saved.", file=sys.stderr)
    elif len(sys.argv) == 4:
        print(f"Warning: Unknown third argument '{sys.argv[3]}'. Ignoring. Use --debug to enable debug images.", file=sys.stderr)

    debug_dir_param = debug_directory if enable_debug else None
    mono_data, width, height = image_to_mono_vlsb_alpha_safe(image_file, debug_dir=debug_dir_param)

    if mono_data:
        if not save_bytearray_to_py_file(mono_data, width, height, output_py_file):
            sys.exit(1)
        else:
            print("\nConversion and saving complete.", file=sys.stderr)
    else:
        print("\nConversion failed, bytearray not generated.", file=sys.stderr)
        sys.exit(1)
