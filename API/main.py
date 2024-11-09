from flask import Flask, request, jsonify
from db import get_db_connection  # Import the function to get database connection
import os
import psycopg2

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the API!"

@app.route('/storegop', methods=['POST'])
def store_gop():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided."}), 400
    
    user_id = data.get('user_id')
    profile = data.get('profile')
    gop_name = data.get('gop_name')
    perimeter = data.get('perimeter')
    read = data.get('read')
    write = data.get('write')
    
    if not user_id or not profile or not gop_name or not perimeter or not read or not write:
        return jsonify({"message": "Missing data fields."}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO gop (user_id,profile,gop_name,perimeter,read,write)
        VALUES (%s, %s, %s,%s, %s, %s)
    ''', (user_id,profile,gop_name,perimeter,read,write))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Request information stored successfully.", "data": data}), 200

@app.route('/getgop', methods=['GET'])
def get_gop():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM gop')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    requests = []
    for row in rows:
        user_id,profile,gop_name,perimeter,read,write = row
        requests.append({
            'user_id': user_id,
            'profile': profile,
            'gop_name': gop_name,
            'perimeter': perimeter,
            'read': read,
            'write': write
        })
    
    return jsonify(requests), 200

@app.route('/storerole', methods=['POST'])
def store_role():
    data = request.json
    if not data:
        return jsonify({"message": "No data provided."}), 400
    
    user_id = data.get('user_id')
    role = data.get('role')
    description = data.get('description')
    
    if not user_id or not role or not description:
        return jsonify({"message": "Missing data fields."}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO role (user_id,role,description)
        VALUES (%s, %s, %s)
    ''', (user_id,role,description))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Request information stored successfully.", "data": data}), 200

@app.route('/getrole', methods=['GET'])
def get_role():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM role')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    requests = []
    for row in rows:
        user_id, role, description = row
        requests.append({
            'user_id': user_id,
            'role': role,
            'description': description
        })
    
    return jsonify(requests), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
