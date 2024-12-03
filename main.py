from flask import Flask, request, jsonify
# from db import get_db_connection  # Import the function to get database connection
import os
import psycopg2

app = Flask(__name__)

def get_db_connection():
    db_params = {
        'host': 'localhost',
        'port': '5433',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'msdthala2019'
    }
    return psycopg2.connect(**db_params)
    
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

@app.route('/getaccount', methods=['GET'])
def get_account():
    user_id = request.args.get('id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if user_id:
            print(f"Fetching user with id (name): {user_id}")
            query = "SELECT name, active, profile, mail, sid FROM users WHERE name = %s;"
            cur.execute(query, (user_id,))
        else:
            query = "SELECT name, active, profile, mail, sid FROM users;"
            cur.execute(query)

        rows = cur.fetchall()
        for row in rows:
            print(f"{row}")
        # Prepare the response
        requests = [
            {
                'name': row[0],
                'active': row[1],
                'profile': row[2],
                'mail': row[3],
                'sid': row[4]
            }
            for row in rows
        ]
        print(requests)
        if not requests:
            return jsonify({"message": "No data found for the given ID"}), 404

        return jsonify(requests), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

@app.route('/gop_check_in_perimeter', methods=['GET'])
def gop_check_in_perimeter():
    profile = request.args.get('profile')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if profile:
            print(f"Fetching profile: {[profile]}")
            query = "SELECT gop FROM gop_perimeter WHERE profile = %s;"
            cur.execute(query, (profile,))
        else:
            query = "SELECT gop FROM gop_perimeter;"
            cur.execute(query)

        rows = cur.fetchall()
        for row in rows:
            print(f"{row}")
        # Prepare the response
        requests = [row[0] for row in rows]
        print(requests)
        if not requests:
            return jsonify({"message": "No data found for the given profile"}), 404

        return jsonify(requests), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

@app.route('/get_gop_using_ptf', methods=['GET'])
def get_gop_using_ptf():
    ptf = request.args.get('ptf')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if ptf:
            print(f"Fetching gop using ptf: {[ptf]}")
            query = "SELECT gop_name FROM ptf_data WHERE portfolio = %s;"
            cur.execute(query, (ptf,))

        rows = cur.fetchall()
        for row in rows:
            print(f"{row}")
        # Prepare the response
        requests = [row[0] for row in rows]
        print(requests)
        if not requests:
            return jsonify({"message": "No data found for the given profile"}), 404

        return jsonify(requests), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

@app.route('/goat', methods=['GET'])
def goat():
    deal_id = request.args.get('deal_id')
    print(deal_id)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if deal_id:
            print(f"Fetching all results required to debug goat: {deal_id}")
            # Initialize response parts
            response_parts = []

            # Execute Query 1
            query1 = "SELECT deal, ldate, qty, portfolio, status, market, unit_price, type, date_stop FROM ABC WHERE deal = %s;"
            cur.execute(query1, (deal_id,))
            result1 = cur.fetchall()
            response_parts.append(f"Query: {query1.replace('%s', str(deal_id))}\nResult:\n{format_result(result1)}")

            # Execute Query 2
            query2 = "SELECT deal, ldate, tax_amount FROM TAX WHERE deal = %s;"
            cur.execute(query2, (deal_id,))
            result2 = cur.fetchall()
            response_parts.append(f"Query: {query2.replace('%s', str(deal_id))}\nResult:\n{format_result(result2)}")

            # Combine all response parts
            combined_results = "\n".join(response_parts)

            print(f"Combined Results: {combined_results}")

            if not combined_results:
                return jsonify({"message": "No data found for the given deal ID"}), 404

            return jsonify({"data": combined_results}), 200

        else:
            return jsonify({"message": "deal_id parameter is missing"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

# Helper function to format the result into a readable string
def format_result(result):
    if not result:
        return "No results found."
    formatted = []
    for row in result:
        formatted.append(" ; ".join(str(val) for val in row))  # Join columns with a separator for clarity
    return "\n".join(formatted)

@app.route('/get_matching_role', methods=['GET'])
def get_matching_role():
    conn = get_db_connection()
    cur = conn.cursor()
    try:        
        query = "SELECT role FROM roles_data"
        cur.execute(query)
        rows = cur.fetchall()
        for row in rows:
            print(f"{row}")
        # Prepare the response
        requests = [row[0] for row in rows]
        print(requests)
        if not requests:
            return jsonify({"message": "No results found"}), 404

        return jsonify(requests), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

@app.route('/gop_perimeter', methods=['GET'])
def gop_perimeter():
    profile = request.args.get('profile')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if profile:
            print(f"Fetching perimter for this profile: {[profile]}")
            query = "SELECT distinct(perimeter) FROM gop_perimeter WHERE profile = %s;"
            cur.execute(query, (profile,))

        rows = cur.fetchall()
        for row in rows:
            print(f"{row}")
        # Prepare the response
        requests = [row[0] for row in rows]
        print(requests)
        if not requests:
            return jsonify({"message": "No data found for the given profile"}), 404

        return jsonify(requests), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

@app.route('/get_ptf', methods=['GET'])
def get_ptf():
    ptf = request.args.get('ptf')
    conn = get_db_connection()
    cur = conn.cursor()
    print(ptf)
    try:
        if ptf:
            print(f"Fetching portfolio status: {[ptf]}")
            query = "SELECT status FROM ptf_data WHERE portfolio = %s;"
            cur.execute(query, (ptf,))

        rows = cur.fetchall()
        for row in rows:
            print(f"{row}")
        # Prepare the response
        requests = [row[0] for row in rows]
        print(requests)
        if not requests:
            return jsonify({"message": "No data found for the given portfolio"}), 404

        return jsonify(requests), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

@app.route('/gop_data', methods=['GET'])
def gop_data():
    gop = request.args.get('gop')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if gop:
            print(f"Fetching gop: {[gop]}")
            query = "SELECT gop, perimeter, status, rdb, zone FROM gop_data WHERE gop = %s;"
            cur.execute(query, (gop,))
        else:
            query = "SELECT gop, perimeter, status, rdb, zone FROM gop_data;"
            cur.execute(query)

        rows = cur.fetchall()
        for row in rows:
            print(f"{row}")
        # Prepare the response
        requests = [
            {
                'gop': row[0],
                'perimeter': row[1],
                'status': row[2],
                'rdb': row[3],
                'zone': row[4]
            }
            for row in rows
        ]
        print(requests)
        if not requests:
            return jsonify({"message": "No data found for the given gop"}), 404

        return jsonify(requests), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

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
