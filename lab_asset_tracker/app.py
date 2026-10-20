from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_lab_key'

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="langberry14", # Thay mật khẩu CSDL của bạn
        database="lab_asset_tracker"
    )

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM personnel WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['personnel_id']
            session['full_name'] = user['full_name']
            session['role'] = user['role']

            if user['role'] in ['Lab Manager', 'PI', 'Admin', 'Lecturer']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            return render_template('login.html', error="Email hoặc mật khẩu không chính xác!")

    return render_template('login.html', error=None)

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] not in ['Lab Manager', 'PI', 'Admin', 'Lecturer']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Thống kê nhanh
    cursor.execute("SELECT COUNT(*) AS total FROM asset")
    total_assets = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS in_use FROM asset WHERE status = 'In Use'")
    in_use_assets = cursor.fetchone()['in_use']

    cursor.execute("SELECT COUNT(*) AS total FROM view_overdue_assets")
    overdue_count = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS maint FROM asset WHERE status = 'Under Maintenance'")
    maint_assets = cursor.fetchone()['maint']

    # 1. Danh sách YÊU CẦU ĐANG CHỜ PHÊ DUYỆT (Pending)
    cursor.execute("""
        SELECT al.loan_id, al.loan_code, a.asset_id, a.asset_name, a.hazard_level, p.full_name AS borrower_name, p.role AS borrower_role, al.checkout_date
        FROM asset_loan al
        JOIN asset a ON al.asset_id = a.asset_id
        JOIN personnel p ON al.personnel_id = p.personnel_id
        WHERE al.status = 'Pending'
        ORDER BY al.checkout_date DESC
    """)
    pending_loans = cursor.fetchall()

    # 2. Danh sách ĐANG CHO MƯỢN (Active)
    cursor.execute("""
        SELECT al.loan_id, al.loan_code, a.asset_id, a.asset_name, p.full_name AS borrower_name, al.checkout_date, al.due_date
        FROM asset_loan al
        JOIN asset a ON al.asset_id = a.asset_id
        JOIN personnel p ON al.personnel_id = p.personnel_id
        WHERE al.status = 'Active'
        ORDER BY al.checkout_date DESC LIMIT 50
    """)
    active_loans = cursor.fetchall()

    # 3. Danh sách Quá Hạn & Thống kê
    cursor.execute("SELECT * FROM view_overdue_assets LIMIT 50")
    overdue_list = cursor.fetchall()

    cursor.execute("SELECT * FROM view_asset_summary_by_lab")
    lab_summary = cursor.fetchall()

    cursor.execute("""
        SELECT a.asset_id, a.asset_code, a.asset_name, a.category, a.hazard_level, a.status, a.purchase_price, l.lab_name 
        FROM asset a JOIN lab l ON a.lab_id = l.lab_id 
        ORDER BY a.asset_id DESC LIMIT 50
    """)
    all_assets = cursor.fetchall()

    cursor.execute("SELECT lab_id, lab_name FROM lab")
    labs = cursor.fetchall()

    cursor.execute("SELECT supplier_id, supplier_name FROM supplier")
    suppliers = cursor.fetchall()

    cursor.close()
    conn.close()

    stats = {
        'total': total_assets, 
        'in_use': in_use_assets, 
        'overdue': overdue_count, 
        'maintenance': maint_assets,
        'pending': len(pending_loans)
    }

    return render_template(
        'admin_dashboard.html', 
        user=session, stats=stats, overdue=overdue_list, 
        summary=lab_summary, assets=all_assets, labs=labs, 
        suppliers=suppliers, active_loans=active_loans, pending_loans=pending_loans
    )

# --- API PHÊ DUYỆT / TỪ CHỐI MƯỢN ---
@app.route('/admin/approve_loan/<int:loan_id>')
def approve_loan(loan_id):
    if 'role' not in session or session['role'] not in ['Lab Manager', 'PI', 'Admin', 'Lecturer']:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT asset_id FROM asset_loan WHERE loan_id = %s", (loan_id,))
    loan = cursor.fetchone()
    
    if loan:
        asset_id = loan['asset_id']
        # Chuyển trạng thái phiếu mượn sang Active và tính hạn trả 48 giờ từ thời điểm duyệt
        cursor.execute("""
            UPDATE asset_loan 
            SET status = 'Active', checkout_date = NOW(), due_date = DATE_ADD(NOW(), INTERVAL 2 DAY) 
            WHERE loan_id = %s
        """, (loan_id,))
        
        # Chuyển trạng thái thiết bị sang 'In Use'
        cursor.execute("UPDATE asset SET status = 'In Use' WHERE asset_id = %s", (asset_id,))
        conn.commit()
        
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_loan/<int:loan_id>')
def reject_loan(loan_id):
    if 'role' not in session or session['role'] not in ['Lab Manager', 'PI', 'Admin', 'Lecturer']:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE asset_loan SET status = 'Rejected' WHERE loan_id = %s", (loan_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# --- THU HỒI THIẾT BỊ ĐÃ TRẢ ---
@app.route('/admin/return_asset/<int:loan_id>/<int:asset_id>')
def return_asset(loan_id, asset_id):
    if 'role' not in session or session['role'] not in ['Lab Manager', 'PI', 'Admin', 'Lecturer', 'Technician']:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE asset_loan SET status = 'Returned', return_date = NOW() WHERE loan_id = %s", (loan_id,))
    cursor.execute("UPDATE asset SET status = 'Available' WHERE asset_id = %s", (asset_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/student')
def student_dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT asset_id, asset_code, asset_name, category, hazard_level FROM asset WHERE status = 'Available' ORDER BY asset_id DESC LIMIT 50")
    available_assets = cursor.fetchall()

    cursor.execute("""
        SELECT a.asset_name, a.asset_code, al.checkout_date, al.due_date, al.status 
        FROM asset_loan al JOIN asset a ON al.asset_id = a.asset_id 
        WHERE al.personnel_id = %s ORDER BY al.checkout_date DESC
    """, (session['user_id'],))
    my_loans = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('student_dashboard.html', user=session, assets=available_assets, loans=my_loans)

@app.route('/admin/add_asset', methods=['POST'])
def add_asset():
    if 'role' not in session or session['role'] not in ['Lab Manager', 'Admin']:
        return jsonify({'success': False, 'message': 'Không có quyền'}), 403

    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO asset (lab_id, supplier_id, asset_name, category, hazard_level, serial_number, purchase_price, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Available')
        """, (data['lab_id'], data['supplier_id'], data['asset_name'], data['category'], 
              data['hazard_level'], data['serial_number'], data['purchase_price']))
        conn.commit()
        return redirect(url_for('admin_dashboard'))
    except mysql.connector.Error as err:
        return f"Lỗi CSDL: {err.msg}", 400
    finally:
        cursor.close()
        conn.close()

# --- TẠO PHIẾU MƯỢN TRẠNG THÁI PENDING ---
@app.route('/api/loan', methods=['POST'])
def create_loan():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Chưa đăng nhập'}), 401
    
    data = request.get_json()
    asset_id = data.get('asset_id')
    user_id = session['user_id']
    user_role = session.get('role', 'Student')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. TRUY VẤN XEM THIẾT BỊ NÀY CÓ YÊU CẦU CHỨNG CHỈ AN TOÀN NÀO KHÔNG
        cursor.execute("""
            SELECT sc.cert_id, sc.cert_name
            FROM asset_required_certification arc
            JOIN safety_certification sc ON arc.cert_id = sc.cert_id
            WHERE arc.asset_id = %s
        """, (asset_id,))
        required_certs = cursor.fetchall()

        # 2. NẾU THIẾT BỊ CÓ YÊU CẦU, KIỂM TRA CHỨNG CHỈ CỦA NGƯỜI MƯỢN
        if required_certs:
            missing_certs = []
            for cert in required_certs:
                cursor.execute("""
                    SELECT * FROM personnel_certification
                    WHERE personnel_id = %s AND cert_id = %s
                    AND (expiry_date IS NULL OR expiry_date >= CURDATE())
                """, (user_id, cert['cert_id']))
                has_cert = cursor.fetchone()
                
                if not has_cert:
                    missing_certs.append(cert['cert_name'])

            # Bị thiếu chứng chỉ -> Chặn không cho mượn
            if missing_certs:
                cert_list_str = ", ".join(missing_certs)
                return jsonify({
                    'success': False, 
                    'message': f'BỊ CHẶN: Thiết bị này yêu cầu Chứng chỉ An toàn [{cert_list_str}]. Bạn chưa được cấp hoặc chứng chỉ đã hết hạn!'
                })

        # 3. NẾU ĐỦ CHỨNG CHỈ -> TẠO PHIẾU MƯỢN PENDING
        interval_sql = "INTERVAL 2 DAY" if user_role == 'Student' else "INTERVAL 7 DAY"
        query = f"""
            INSERT INTO asset_loan (asset_id, personnel_id, checkout_date, due_date, status)
            VALUES (%s, %s, NOW(), DATE_ADD(NOW(), {interval_sql}), 'Pending')
        """
        cursor.execute(query, (asset_id, user_id))
        conn.commit()
        msg = "Gửi yêu cầu mượn thành công! Đã xác minh đủ chứng chỉ an toàn. Vui lòng chờ phê duyệt."
        success = True

    except mysql.connector.Error as err:
        msg = f"Lỗi nghiệp vụ CSDL: {err.msg}"
        success = False
    finally:
        cursor.close()
        conn.close()

    return jsonify({'success': success, 'message': msg})

@app.route('/admin/update_status/<int:asset_id>/<new_status>')
def update_asset_status(asset_id, new_status):
    if 'role' not in session or session['role'] not in ['Lab Manager', 'Admin', 'Technician']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE asset SET status = %s WHERE asset_id = %s", (new_status, asset_id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)