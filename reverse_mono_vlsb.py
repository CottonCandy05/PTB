#go to console and run "python reverse_mono_vlsb.py my_output_data.py output_reconstructed.png 128 64"
from PIL import Image
import sys
import math
import ast # To safely evaluate the bytearray literal from a file

def mono_vlsb_to_image(mono_data, width, height):
    """
    Converts a 1-bit MONO_VLSB byte array back into a PIL Image object.
    MONO_VLSB = Vertical byte orientation, Least Significant Bit first.

    Args:
        mono_data (bytearray): The bytearray in MONO_VLSB format.
        width (int): The width of the original image in pixels.
        height (int): The height of the original image in pixels.

    Returns:
        PIL.Image.Image: The reconstructed 1-bit monochrome image,
                       or None if an error occurs.
    """
    try:
        # --- 1. Validate Input ---
        pages = math.ceil(height / 8)
        expected_bytes = pages * width
        if len(mono_data) != expected_bytes:
            print(f"Error: Input bytearray length ({len(mono_data)}) does not match "
                  f"expected length ({expected_bytes}) for {width}x{height} image.",
                  file=sys.stderr)
            # Optionally, try to proceed if data is longer, but warn
            if len(mono_data) < expected_bytes:
                 return None
            else:
                 print(f"Warning: Input data is longer than expected. Proceeding anyway.",
                      file=sys.stderr)
                 # Clamp data if needed, although iteration limits should handle this
                 # mono_data = mono_data[:expected_bytes]


        print(f"Reconstructing image: {width} x {height} pixels", file=sys.stderr)
        print(f"Using {len(mono_data)} bytes of MONO_VLSB data.", file=sys.stderr)
        print(f"Calculated pages: {pages}", file=sys.stderr)

        # --- 2. Create Output Image ---
        # Create a new black image in 1-bit mode ('1')
        img_out = Image.new('1', (width, height), color=0) # 0 = black

        # --- 3. Reconstruct Pixels from Byte Array ---
        byte_index = 0
        # Iterate column by column, then page by page (same order as creation)
        for page in range(pages):
            for x in range(width):
                # Check if we have enough bytes left (robustness)
                if byte_index >= len(mono_data):
                    print(f"Warning: Reached end of input bytearray prematurely at byte {byte_index}. "
                          f"Expected {expected_bytes} bytes.", file=sys.stderr)
                    # Fill remaining pixels with black (already done by Image.new) or break
                    # Depending on desired behaviour for truncated data
                    break # Stop processing this page if data runs out

                current_byte = mono_data[byte_index]

                # Iterate through the 8 vertical bits for this byte/page
                for y_bit in range(8):
                    # Calculate the actual y-coordinate in the image
                    y = (page * 8) + y_bit

                    # Check if the pixel is within image bounds
                    if y < height:
                        # --- VLSB Extraction ---
                        # Check the bit corresponding to this vertical position (y_bit)
                        # LSB (bit 0) corresponds to y_bit=0 (top pixel in chunk)
                        # MSB (bit 7) corresponds to y_bit=7 (bottom pixel in chunk)
                        if (current_byte >> y_bit) & 1:
                            # If the bit is 1, set pixel to white (255 in '1' mode)
                            img_out.putpixel((x, y), 255)
                        # else: pixel remains black (0), already set by Image.new

                byte_index += 1 # Move to the next byte in the input array
            # End of column loop for the current page
            if byte_index >= len(mono_data) and page < pages -1 :
                 # Break outer loop as well if data ran out mid-image
                 break


        print(f"Image reconstruction finished. Processed {byte_index} bytes.", file=sys.stderr)
        return img_out

    except Exception as e:
        print(f"An error occurred during image reconstruction: {e}", file=sys.stderr)
        return None

def read_bytearray_from_file(filepath):
    """
    Reads a python file and extracts the first bytearray definition.
    Handles UTF-8 (with or without BOM) and potentially UTF-16 LE.
    Prioritizes UTF-8 reading.
    """
    content = None
    used_encoding = None
    # --- MODIFICATION: Prioritize utf-8-sig ---
    # Since the generator script writes utf-8, try that first.
    # 'utf-8-sig' handles both standard utf-8 and utf-8 with BOM.
    encodings_to_try = ['utf-8-sig', 'utf-16']

    for enc in encodings_to_try:
        try:
            print(f"Attempting to read file '{filepath}' with encoding: {enc}", file=sys.stderr)
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                used_encoding = enc
                print(f"Successfully read file using encoding: {enc}", file=sys.stderr)
                break # Stop trying once read successfully
        except UnicodeDecodeError as ude:
            # This encoding didn't work, try the next one
            print(f"Failed to decode using {enc}: {ude}. Trying next...", file=sys.stderr)
            continue
        except FileNotFoundError:
            # File not found is a definite failure, stop trying
            print(f"Error: Input file not found at '{filepath}'", file=sys.stderr)
            return None
        except Exception as e:
            # --- MODIFICATION: Handle other errors less fatally within the loop ---
            # Treat other errors during open/read (like the BOM error for utf-16)
            # as potential encoding mismatches for now, and try the next encoding.
            # If all encodings fail, the check after the loop will handle it.
            print(f"An error occurred opening/reading with {enc}: {e}. Trying next...", file=sys.stderr)
            continue # <<< Allow loop to continue to the next encoding

    # Check if we successfully read the content after trying all encodings
    if content is None:
        print(f"Error: Could not decode file '{filepath}' using any attempted encoding: {encodings_to_try}", file=sys.stderr)
        print(f"Please ensure the file is saved as UTF-8 or UTF-16 text.", file=sys.stderr)
        return None

    # --- Content successfully read, proceed with parsing (No changes below here) ---
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


# --- Main execution ---
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

    # --- Read Bytearray Data ---
    print(f"Reading bytearray from: {input_file}", file=sys.stderr)
    mono_vlsb_data = read_bytearray_from_file(input_file)

    if not mono_vlsb_data:
        sys.exit(1)

    print(f"Successfully read {len(mono_vlsb_data)} bytes.", file=sys.stderr)

    # --- Perform Conversion ---
    reconstructed_image = mono_vlsb_to_image(mono_vlsb_data, img_width, img_height)

    # --- Save Output Image ---
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