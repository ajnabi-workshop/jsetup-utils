import sys
import base64


def convert_hash(hash_string):
    """
    Converts hash strings from Nix error output to the correct format to add to Nix files.
    Used for adding extensions to Nix-installed VS Code/Codium which aren't in nixpkgs. 
    """
    # Remove 'sha256-' prefix
    if hash_string.startswith('sha256-'):
        hash_string = hash_string[len('sha256-'):]

    # Decode base64 and print as hex
    try:
        decoded_bytes = base64.b64decode(hash_string)
        hex_string = decoded_bytes.hex()
        print(hex_string)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <hash_string>")
    else:
        hash_string = sys.argv[1]
        convert_hash(hash_string)
