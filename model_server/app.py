from flask import Flask, request, jsonify
from llm_local import callLLM 
# Hosting the gguf model on a separate local server

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        print("request.json:: ", request.json)
        data = request.json['input_data']
        print("data:: ", data)
        result = callLLM(data)  # Replace with your actual LLM model prediction function
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
