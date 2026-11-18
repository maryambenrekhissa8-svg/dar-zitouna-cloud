from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def accueil():
    return """
    <html>
      <head><title>Dar Zitouna</title></head>
      <body style="font-family: Arial; text-align: center; margin-top: 80px;">
        <h1>Bienvenue chez Dar Zitouna</h1>
        <p>Produits artisanaux tunisiens : savons, huiles essentielles, cosmetiques naturels</p>
        <p><b>Application Flask conteneurisee avec Docker</b></p>
      </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "dar-zitouna-app"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
