from flask import Flask, jsonify, request
import subprocess
from flasgger import Swagger, swag_from
import jwt
import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my_secret_key')

# Define the Swagger template with OpenAPI 3.0
template = {
  "info": {
    "title": "My Python APIs",
    "description": "APIs in Python",
    "contact": {
      "name": "Stanley Ho",
      "email": "me@me.com",
      "url": "http://www.me.com"
    },
    "termsOfService": "http://me.com/terms",
    "version": "0.0.1"
  }
}

swagger = Swagger(app, template=template)

# Helper function to verify JWT
def token_required(f):
    def wrapper(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        
        if not token or not token.startswith('Bearer '):
            return jsonify({'message': 'Token is missing or invalid!'}), 403

        try:
            token = token.split(" ")[1]  # Get the actual token part
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 403

        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Avoids a name collision issue with the decorator
    return wrapper

@app.route('/token', methods=['POST'])
@swag_from('./swagger/token.yaml')
def token():
    auth = request.json
    if auth and auth['username'] == 'user' and auth['password'] == 'pass':
        token = jwt.encode({'user': auth['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'bearertoken': token})
    return jsonify({'message': 'Invalid credentials!'}), 401

@app.route('/data', methods=['GET', 'POST'])
@swag_from('./swagger/data_post.yaml', methods=['POST'])
@swag_from('./swagger/data_get.yaml', methods=['GET'])
def handle_data():
    if request.method == 'POST':
        data = request.get_json()
        return jsonify(data), 201
    else:
        return jsonify({"message": "Send data using POST method"}), 200

@app.route('/run-script', methods=['POST'])
@swag_from('./swagger/run_script.yaml')
@token_required
def run_script():
    script_path = 'script.ps1'  # Local PowerShell script
    try:
        # Run the PowerShell script
        result = subprocess.run(['pwsh', script_path], capture_output=True, text=True, check=True)
        return jsonify({"output": result.stdout, "error": result.stderr}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
