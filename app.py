from flask import Flask, jsonify
from controllers.client_controller import client_bp
from controllers.auth_controller import auth_bp

# Initialize Flask app
app = Flask(__name__)

# Register Blueprints
app.register_blueprint(client_bp, url_prefix="/client")
app.register_blueprint(auth_bp, url_prefix="/auth")

@app.route('/routes', methods=['GET'])
def list_routes():
    return jsonify([
        {
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "route": rule.rule
        }
        for rule in app.url_map.iter_rules()
    ])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
