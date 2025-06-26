from flask import Flask, render_template, request, jsonify
from liquidacion import MotorLiquidacion

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    data = request.json
    motor = MotorLiquidacion(data)
    motor.procesar()
    return jsonify(motor.resumen())

if __name__ == '__main__':
    app.run(debug=True)
