from flask import Flask, request, jsonify
from db import get_db_connection  # Import the function to get database connection
import os
import psycopg2

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the API!"

@app.route('/store-request', methods=['POST'])
def store_request():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided."}), 400
    
    request_id = data.get('request_id')
    role_or_gop = data.get('role_or_gop')
    manager_email = data.get('manager_email')
    user_email = data.get('user_email')
    status = data.get('status')
    
    if not request_id or not user_email or not role_or_gop or not manager_email or not status:
        return jsonify({"message": "Missing data fields."}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO requests (request_id, role_or_gop, user_email, manager_email, status)
        VALUES (%s, %s, %s, %s, %s)
    ''', (request_id, role_or_gop, user_email, manager_email, status))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Request information stored successfully.", "data": data}), 200

@app.route('/get-request', methods=['GET'])
def get_request():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM requests')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    requests = []
    for row in rows:
        request_id, role_or_gop, user_email, manager_email, status = row
        requests.append({
            'request_id': request_id,
            'role_or_gop': role_or_gop,
            'user_email': user_email,
            'manager_email': manager_email,
            'status': status
        })
    
    return jsonify(requests), 200

@app.route('/mark-request', methods=['POST'])
def mark_request():
    data = request.json
    request_id = data.get('request_id')
    status = data.get('status')

    if not request_id or not status:
        return jsonify({"message": "Missing request_id or status."}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE requests
        SET status = %s
        WHERE request_id = %s
    ''', (status, request_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Request status updated successfully."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
