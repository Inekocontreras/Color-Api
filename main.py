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

import numpy as np
import wave
import os

def generate_audio(freqs, filename):
    sample_rate = 44100
    total_duration = 10 if len(freqs) <= 5 else 15  # segundos totales
    duration_per_freq = total_duration / len(freqs)

    audio_data = []

    for freq in freqs:
        if isinstance(freq, list):
            for sub_freq in freq:
                t = np.linspace(0, duration_per_freq / 2, int(sample_rate * (duration_per_freq / 2)), False)
                tone = np.sin(2 * np.pi * sub_freq * t)
                audio_data.extend(tone)
        else:
            t = np.linspace(0, duration_per_freq, int(sample_rate * duration_per_freq), False)
            tone = np.sin(2 * np.pi * freq * t)
            audio_data.extend(tone)

    audio_data = np.array(audio_data)
    audio_data *= 32767 / np.max(np.abs(audio_data))  # normalización
    audio_data = audio_data.astype(np.int16)

    output_path = os.path.join("static", "audio")
    os.makedirs(output_path, exist_ok=True)
    filepath = os.path.join(output_path, filename)

    with wave.open(filepath, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(audio_data.tobytes())

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
import numpy as np
import wave

def generate_sound(freqs, output_file="static/audio/resultado.wav"):
    sample_rate = 44100
    total_duration = 10 if len(freqs) <= 5 else 15  # segundos
    duration_per_freq = total_duration / len(freqs)
    
    audio_data = []

    for freq_set in freqs:
        if isinstance(freq_set, list):  # mezcla de 2 frecuencias
            # 50% tiempo para cada una
            for freq in freq_set:
                t = np.linspace(0, duration_per_freq / 2, int(sample_rate * (duration_per_freq / 2)), False)
                tone = np.sin(2 * np.pi * freq * t)
                audio_data.extend(tone)
        else:
            t = np.linspace(0, duration_per_freq, int(sample_rate * duration_per_freq), False)
            tone = np.sin(2 * np.pi * freq_set * t)
            audio_data.extend(tone)

    audio_data = np.array(audio_data)
    audio_data *= 32767 / np.max(np.abs(audio_data))
    audio_data = audio_data.astype(np.int16)

    with wave.open(output_file, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(audio_data.tobytes())
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
