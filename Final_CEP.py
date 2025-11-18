
import heapq
import json
import os
import io
import zipfile

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_table(text):
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    return freq

def build_huffman_tree(freq_table):
    if not freq_table:
        return None
    heap = [Node(char, freq) for char, freq in freq_table.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)
    return heap[0]

def generate_codes(node, code="", codes=None):
    if codes is None:
        codes = {}
    if node is None:
        return codes
    if node.char is not None:
        if code == "":
            code = "0"
        codes[node.char] = code
        return codes
    generate_codes(node.left, code + "0", codes)
    generate_codes(node.right, code + "1", codes)
    return codes

def encode_text(text, codes):
    return "".join(codes[ch] for ch in text)

def pad_encoded(encoded):
    extra = (8 - len(encoded) % 8) % 8
    padded_info = f"{extra:08b}"
    encoded += "0" * extra
    return padded_info + encoded, extra

def write_binary_file(encoded_str, output_file):
    b = bytearray()
    for i in range(0, len(encoded_str), 8):
        b.append(int(encoded_str[i:i+8], 2))
    with open(output_file, "wb") as f:
        f.write(b)

def remove_padding(encoded_data):
    padded_info = encoded_data[:8]
    extra_padding = int(padded_info, 2)
    encoded_data = encoded_data[8:]
    if extra_padding > 0:
        encoded_data = encoded_data[:-extra_padding]
    return encoded_data

def decode_text(encoded_data, codes):
    reverse_codes = {v: k for k, v in codes.items()}
    current = ""
    decoded = []
    for bit in encoded_data:
        current += bit
        if current in reverse_codes:
            decoded.append(reverse_codes[current])
            current = ""
    return "".join(decoded)

def read_binary_as_bits(input_file):
    with open(input_file, "rb") as f:
        byte_data = f.read()
    return "".join(f"{byte:08b}" for byte in byte_data)

def compress(input_file):
    print("\n--- COMPRESSION ---")
    if not os.path.exists(input_file):
        print("File not found.")
        return
    with open(input_file, "r") as f:
        text = f.read()
    if not text:
        print("File empty.")
        return
    freq = build_frequency_table(text)
    root = build_huffman_tree(freq)
    codes = generate_codes(root)
    encoded = encode_text(text, codes)
    padded_encoded, _ = pad_encoded(encoded)
    out_name = input("Output .bin file name (default output.bin): ").strip() or "output.bin"
    write_binary_file(padded_encoded, out_name)
    with open(out_name + "_codes.json", "w") as f:
        json.dump(codes, f, indent=2)
    print("Done.")

def decompress(encoded_file, codes_file):
    print("\n--- DECOMPRESSION ---")
    if not (os.path.exists(encoded_file) and os.path.exists(codes_file)):
        print("Missing file.")
        return
    bits = read_binary_as_bits(encoded_file)
    bits = remove_padding(bits)
    with open(codes_file, "r") as f:
        codes = json.load(f)
    text = decode_text(bits, codes)
    out_name = input("Output .txt file name (default decompressed.txt): ").strip() or "decompressed.txt"
    with open(out_name, "w") as f:
        f.write(text)
    print("Done.")

# -------------
# STREAMLIT UI 
# -------------

import streamlit as st
import io
import zipfile
import json

st.set_page_config(page_title="File Compressor", page_icon="📦", layout="wide")


st.sidebar.markdown("<h2 style='color:lightblue;'>📦 File Compressor</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.info("Welcome! This tool allows you to compress text files or decompress previously compressed files.", icon="ℹ️")


st.sidebar.markdown("1️⃣ Choose Compress or Decompress  <br>""2️⃣ Upload your file  <br>""3️⃣ Download the result  <br>""4️⃣ View file stats below", unsafe_allow_html=True)


st.markdown("<h1 style='text-align: center; color:lightblue;'>📦 File Compressor / Decompressor</h1>", unsafe_allow_html=True)
st.markdown("<hr style='height:2px;border:none;color:gray;background-color:gray;' />", unsafe_allow_html=True)


tab1, tab2 = st.tabs(["🟢 Compress File", "🔵 Decompress File"])


with tab1:
    st.subheader("Compress a File")

    uploaded_file = st.file_uploader("Upload a file (.txt, .py)", type=["txt", "py"], key="compress_uploader", help="Select a file to compress")

    if uploaded_file:
        try:
            try:
                text = uploaded_file.read().decode("utf-8")
            except:
                text = str(uploaded_file.read())

            st.text_area(
                "Original File Preview",
                text[:1000] + ("..." if len(text) > 1000 else ""),
                height=200
            )

            freq_table = build_frequency_table(text)
            root = build_huffman_tree(freq_table)
            codes = generate_codes(root)
            encoded_data = encode_text(text, codes)
            padded_encoded_data, _ = pad_encoded(encoded_data)

            original_bits = len(text) * 8
            compressed_bits = len(padded_encoded_data)
            compression_ratio = (1 - compressed_bits / original_bits) * 100

            col1, col2, col3 = st.columns(3)
            col1.metric("Original Size (bits)", f"{original_bits}")
            col2.metric("Compressed Size (bits)", f"{compressed_bits}")
            col3.metric("Compression Ratio", f"{compression_ratio:.2f}%")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr("compressed.bin", padded_encoded_data)
                zf.writestr("codes.json", json.dumps(codes))

            zip_buffer.seek(0)

            st.download_button("⬇️ Download Compressed File (ZIP)", zip_buffer, file_name=f"{uploaded_file.name.replace('.txt','').replace('.py','')}_huffman.zip", use_container_width=True, type="primary")

            st.success("✅ Compression Successful!", icon="🎉")

        except Exception as e:
            st.error(f"Error during compression: {e}")

with tab2:
    st.subheader("Decompress a ZIP File")

    uploaded_file = st.file_uploader("Upload a Compressed ZIP file", type=["zip"], key="decompress_uploader", help="ZIP must contain compressed.bin and codes.json")

    if uploaded_file:
        try:
            zip_bytes = io.BytesIO(uploaded_file.read())

            with zipfile.ZipFile(zip_bytes, "r") as zf:
                required = {"compressed.bin", "codes.json"}

                if not required.issubset(zf.namelist()):
                    st.error("ZIP must contain: compressed.bin AND codes.json")
                else:
                    compressed_data = zf.read("compressed.bin").decode("utf-8")
                    codes = json.loads(zf.read("codes.json").decode("utf-8"))

                    unpadded = remove_padding(compressed_data)
                    decoded_text = decode_text(unpadded, codes)

                    st.text_area("Decompressed Text", decoded_text, height=250)

                    st.download_button("⬇️ Download Decompressed File (Text)", decoded_text, file_name="decompressed_output.txt", use_container_width=True, type="secondary")

                    st.success("✅ Decompression Successful!", icon="🎉")

        except Exception as e:
            st.error(f"Error while decompressing: {e}")


st.markdown("<hr style='height:1px;border:none;color:gray;background-color:gray;' />", unsafe_allow_html=True)
st.info("Use the tabs above to Compress a file or Decompress a ZIP file.", icon="ℹ️")

