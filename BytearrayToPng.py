# Recommended filename: PngToBytearray.py
# Usage: go to console and run "python BytearrayToPng.py my_output_data.py output_reconstructed.png W H (Replace W and H with the original resolution in pixels.)"

from PIL import Image
import sys
import math
import ast

def mono_vlsb_to_image(mono_data, width, height):
    try:
        pages = math.ceil(height / 8)
        expected_bytes = pages * width
        if len(mono_data) != expected_bytes:
            print(f"Error: Input bytearray length ({len(mono_data)}) does not match expected length ({expected_bytes}) for {width}x{height} image.", file=sys.stderr)
            if len(mono_data) < expected_bytes:
                return None
            else:
                print(f"Warning: Input data is longer than expected. Proceeding anyway.", file=sys.stderr)
        print(f"Reconstructing image: {width} x {height} pixels", file=sys.stderr)
        print(f"Using {len(mono_data)} bytes of MONO_VLSB data.", file=sys.stderr)
        print(f"Calculated pages: {pages}", file=sys.stderr)
        img_out = Image.new('1', (width, height), color=0)
        byte_index = 0
        for page in range(pages):
            for x in range(width):
                if byte_index >= len(mono_data):
                    print(f"Warning: Reached end of input bytearray prematurely at byte {byte_index}. Expected {expected_bytes} bytes.", file=sys.stderr)
                    break
                current_byte = mono_data[byte_index]
                for y_bit in range(8):
                    y = (page * 8) + y_bit
                    if y < height:
                        if (current_byte >> y_bit) & 1:
                            img_out.putpixel((x, y), 255)
                byte_index += 1
            if byte_index >= len(mono_data) and page < pages - 1:
                break
        print(f"Image reconstruction finished. Processed {byte_index} bytes.", file=sys.stderr)
        return img_out
    except Exception as e:
        print(f"An error occurred during image reconstruction: {e}", file=sys.stderr)
        return None

def read_bytearray_from_file(filepath):
    content = None
    used_encoding = None
    encodings_to_try = ['utf-8-sig', 'utf-16']
    for enc in encodings_to_try:
        try:
            print(f"Attempting to read file '{filepath}' with encoding: {enc}", file=sys.stderr)
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                used_encoding = enc
                print(f"Successfully read file using encoding: {enc}", file=sys.stderr)
                break
        except UnicodeDecodeError as ude:
            print(f"Failed to decode using {enc}: {ude}. Trying next...", file=sys.stderr)
            continue
        except FileNotFoundError:
            print(f"Error: Input file not found at '{filepath}'", file=sys.stderr)
            return None
        except Exception as e:
            print(f"An error occurred opening/reading with {enc}: {e}. Trying next...", file=sys.stderr)
            continue
    if content is None:
        print(f"Error: Could not decode file '{filepath}' using any attempted encoding: {encodings_to_try}", file=sys.stderr)
        print(f"Please ensure the file is saved as UTF-8 or UTF-16 text.", file=sys.stderr)
        return None
    try:
        start_marker = "bytearray(["
        end_marker = "])"
        start_index = content.find(start_marker)
        if start_index == -1:
            print(f"Error: Could not find '{start_marker}' in the content of {filepath} (read using {used_encoding}).", file=sys.stderr)
            print(f"First 100 characters read:\n'''{content[:100]}'''", file=sys.stderr)
            return None
        search_start_for_end = start_index + len(start_marker)
        end_index = content.find(end_marker, search_start_for_end)
        if end_index == -1:
            print(f"Error: Could not find closing '{end_marker}' after '{start_marker}' definition in {filepath} (read using {used_encoding}).", file=sys.stderr)
            context_start = max(0, start_index - 20)
            context_end = min(len(content), start_index + len(start_marker) + 50)
            print(f"Debug context around start marker:\n'''{content[context_start:context_end]}...'''", file=sys.stderr)
            return None
        bytearray_list_str = content[start_index + len(start_marker) - 1 : end_index + 1]
        try:
            byte_list = ast.literal_eval(bytearray_list_str)
        except Exception as parse_error:
            print(f"Error parsing the bytearray content with ast.literal_eval: {parse_error}", file=sys.stderr)
            print(f"Problematic string section (first 200 chars):\n'''{bytearray_list_str[:200]}...'''", file=sys.stderr)
            return None
        return bytearray(byte_list)
    except Exception as e:
        print(f"An unexpected error occurred during parsing after reading the file: {e}", file=sys.stderr)
        print(f"Exception type: {type(e).__name__}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python reverse_mono_vlsb.py <input_bytearray.py> <output_image.png> <width> <height>", file=sys.stderr)
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    try:
        img_width = int(sys.argv[3])
        img_height = int(sys.argv[4])
    except ValueError:
        print("Error: Width and height must be integers.", file=sys.stderr)
        sys.exit(1)
    if img_width <= 0 or img_height <= 0:
        print("Error: Width and height must be positive.", file=sys.stderr)
        sys.exit(1)
    print(f"Reading bytearray from: {input_file}", file=sys.stderr)
    mono_vlsb_data = read_bytearray_from_file(input_file)
    if not mono_vlsb_data:
        sys.exit(1)
    print(f"Successfully read {len(mono_vlsb_data)} bytes.", file=sys.stderr)
    reconstructed_image = mono_vlsb_to_image(mono_vlsb_data, img_width, img_height)
    if reconstructed_image:
        try:
            reconstructed_image.save(output_file, "PNG")
            print(f"Successfully saved reconstructed image to '{output_file}'")
        except Exception as e:
            print(f"Error saving image to '{output_file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Image reconstruction failed.", file=sys.stderr)
        sys.exit(1)
        
