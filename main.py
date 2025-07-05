from flask import Flask, request, jsonify, send_from_directory
from PIL import Image
from io import BytesIO
import os
import numpy as np
from scipy.io.wavfile import write

app = Flask(__name__)
UPLOAD_FOLDER = "audio_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Colores base y sus frecuencias
base_colors = {
    "rojo": {"rgb": [255, 0, 0], "freq": 261.63},
    "naranja": {"rgb": [255, 165, 0], "freq": 293.66},
    "amarillo": {"rgb": [255, 255, 0], "freq": 329.63},
    "verde": {"rgb": [0, 128, 0], "freq": 349.23},
    "cian": {"rgb": [0, 255, 255], "freq": 392.00},
    "azul": {"rgb": [0, 0, 255], "freq": 440.00},
    "violeta": {"rgb": [138, 43, 226], "freq": 493.88}
}

def distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def closest_color(rgb):
    distances = {name: distance(rgb, data["rgb"]) for name, data in base_colors.items()}
    sorted_colors = sorted(distances.items(), key=lambda x: x[1])
    
    if sorted_colors[0][1] < 60:
        name = sorted_colors[0][0]
        freqs = [base_colors[name]["freq"]]
    else:
        name1, name2 = sorted_colors[0][0], sorted_colors[1][0]
        freq1 = base_colors[name1]["freq"]
        freq2 = base_colors[name2]["freq"]
        freqs = [(freq1 + freq2) / 2]

    return freqs

def get_palette(image, num_colors=3):
    image = image.resize((100, 100))
    result = image.convert('P', palette=Image.ADAPTIVE, colors=num_colors)
    palette = result.getpalette()
    color_counts = sorted(result.getcolors(), reverse=True)
    colors = []

    for count, idx in color_counts[:num_colors]:
        r, g, b = palette[idx*3:idx*3+3]
        colors.append([r, g, b])
    return colors

def generate_audio(freqs, filename="resultado.wav"):
    rate = 44100
    duration = 1.5
    audio = np.zeros(int(rate * duration))

    for freq in freqs:
        t = np.linspace(0, duration, int(rate * duration), False)
        tone = np.sin(freq * t * 2 * np.pi)
        audio += tone

    audio = audio / np.max(np.abs(audio))
    audio = np.int16(audio * 32767)

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    write(filepath, rate, audio)
    return filepath

@app.route("/")
def home():
    return "API activa - Enviar imagen a /analyze"

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/analyze", methods=["POST"])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files['image']
    image = Image.open(BytesIO(image_file.read()))
    palette = get_palette(image)

    all_freqs = []
    for color in palette:
        freqs = closest_color(color)
        all_freqs.extend(freqs)

    audio_filename = "resultado.wav"
    filepath = generate_audio(all_freqs, audio_filename)
    audio_url = request.host_url + "audio/" + audio_filename

    return jsonify({
        "frecuencias": all_freqs,
        "audio_url": audio_url
    })
    if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
