import os
from flask import Flask, request, jsonify
app = Flask(__name__)
@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    # authentication logic here
    return jsonify({'message': 'Logged in successfully'})
if __name__ == '__main__':
    app.run(debug=True)