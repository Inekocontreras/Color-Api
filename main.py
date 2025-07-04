from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO

app = Flask(__name__)

base_colors = {
    "rojo": {"rgb": [255, 0, 0], "freq": 261.63},
    "naranja": {"rgb": [255, 165, 0], "freq": 293.66},
    "amarillo": {"rgb": [255, 255, 0], "freq": 329.63},
    "verde": {"rgb": [0, 128, 0], "freq": 349.23},
    "cian": {"rgb": [0, 255, 255], "freq": 392.00},
    "azul": {"rgb": [0, 0, 255], "freq": 440.00},
    "violeta": {"rgb": [138, 43, 226], "freq": 493.88}
}

def closest_color(rgb):
    def distance(c1, c2):
        return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

    distances = {name: distance(rgb, data["rgb"]) for name, data in base_colors.items()}
    sorted_colors = sorted(distances.items(), key=lambda x: x[1])

    if sorted_colors[0][1] < 60:
        name = sorted_colors[0][0]
        freq = [base_colors[name]["freq"]]
        return name, freq
    else:
        name1, name2 = sorted_colors[0][0], sorted_colors[1][0]
        freq = [base_colors[name1]["freq"], base_colors[name2]["freq"]]
        return f"{name1}-{name2}", freq

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

@app.route("/")
def home():
    return "API activa - Enviar imagen a /analyze"

@app.route("/analyze", methods=["POST"])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files['image']
    image = Image.open(BytesIO(image_file.read()))
    palette = get_palette(image)

    results = []
    for color in palette:
        name, freqs = closest_color(color)
        results.append({
            "color_detectado": color,
            "equivalente": name,
            "frecuencias": freqs
        })

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)