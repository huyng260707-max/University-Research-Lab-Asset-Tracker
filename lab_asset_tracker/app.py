from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
import bcrypt
import uuid

app = Flask(__name__)
app.secret_key = 'lab_asset_tracker_secret_key_2026_xyz'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'langberry14',
    'database': 'lab_asset_tracker'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'Student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('admin_teacher_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
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

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['personnel_id']
            session['role'] = user['role']
            session['full_name'] = ("Giảng viên " + user['full_name']) if user['role'] in ['Lecturer', 'PI'] else user['full_name']
            return redirect(url_for('index'))
        else:
            flash('Sai email hoặc mật khẩu!', 'danger')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/student')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'Student':
        return redirect(url_for('index'))
    
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    
    try:
        # 1. Lấy toàn bộ danh sách thiết bị
        cursor.execute("SELECT asset_id, asset_name, status FROM asset")
        assets = cursor.fetchall()
        
        # 2. Lấy danh sách dự án sinh viên tham gia (phục vụ mượn > 48h)
        cursor.execute("""
            SELECT rp.project_id, rp.title 
            FROM research_project rp
            JOIN project_assignment pa ON rp.project_id = pa.project_id
            WHERE pa.personnel_id = %s
        """, (student_id,))
        projects = cursor.fetchall()

        # 3. Lấy lịch sử mượn thiết bị của sinh viên
        cursor.execute("""
            SELECT al.loan_id, al.loan_code, a.asset_name, al.checkout_date, al.due_date, al.status, al.loan_reason
            FROM asset_loan al
            JOIN asset a ON al.asset_id = a.asset_id
            WHERE al.personnel_id = %s
            ORDER BY al.loan_id DESC
        """, (student_id,))
        my_loans = cursor.fetchall()
    except Error as e:
        flash(f"Lỗi CSDL: {e.msg}", "danger")
        assets, projects, my_loans = [], [], []
    finally:
        cursor.close()
        conn.close()
        
    return render_template('student.html', assets=assets, projects=projects, my_loans=my_loans)

@app.route('/create_loan', methods=['POST'])
def create_loan():
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('index'))

    asset_id = request.form['asset_id']
    project_id = request.form.get('project_id') or None
    loan_reason = request.form.get('loan_reason', 'Mượn thiết bị học tập/nghiên cứu')
    checkout_date = request.form.get('checkout_date') or request.form.get('start_time')
    due_date = request.form.get('due_date') or request.form.get('end_time')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO asset_loan (asset_id, personnel_id, project_id, loan_reason, checkout_date, due_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (asset_id, session['user_id'], project_id, loan_reason, checkout_date, due_date))
        conn.commit()
        flash('Tạo phiếu mượn thành công! Đang chờ duyệt.', 'success')
        
    except Error as e:
        if e.errno == 1644:
            flash(f"LỖI NGHIỆP VỤ: {e.msg}", 'danger')
        else:
            flash(f"LỖI HỆ THỐNG: {e.msg}", 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('student_dashboard'))

@app.route('/dashboard')
def admin_teacher_dashboard():
    if 'user_id' not in session or session['role'] == 'Student':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Đơn Pending
    if session['role'] == 'Lab Manager':
        cursor.execute("""
            SELECT al.*, a.asset_name, p.full_name as student_name 
            FROM asset_loan al
            JOIN asset a ON al.asset_id = a.asset_id
            JOIN personnel p ON al.personnel_id = p.personnel_id
            WHERE al.status = 'Pending'
        """)
    else:
        cursor.execute("""
            SELECT al.*, a.asset_name, p.full_name as student_name 
            FROM asset_loan al
            JOIN asset a ON al.asset_id = a.asset_id
            JOIN personnel p ON al.personnel_id = p.personnel_id
            JOIN research_project rp ON al.project_id = rp.project_id
            WHERE al.status = 'Pending' AND rp.pi_id = %s
        """, (session['user_id'],))
    pending_loans = cursor.fetchall()

    # 2. Đơn Active (Đang mượn)
    cursor.execute("""
        SELECT al.*, a.asset_name, p.full_name as student_name 
        FROM asset_loan al
        JOIN asset a ON al.asset_id = a.asset_id
        JOIN personnel p ON al.personnel_id = p.personnel_id
        WHERE al.status = 'Active'
    """)
    active_loans = cursor.fetchall()

    # 3. Đơn Quá hạn (Từ View view_overdue_assets)
    cursor.execute("SELECT * FROM view_overdue_assets")
    overdue_loans = cursor.fetchall()

    # 4. Kho thiết bị
    cursor.execute("SELECT a.*, l.lab_name FROM asset a JOIN lab l ON a.lab_id = l.lab_id ORDER BY a.asset_id DESC")
    assets = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template('admin_teacher.html', pending_loans=pending_loans, active_loans=active_loans, overdue_loans=overdue_loans, assets=assets)

@app.route('/approve/<int:loan_id>', methods=['POST'])
def approve_loan(loan_id):
    action = request.form.get('action', 'Approve')
    new_status = 'Active' if action == 'Approve' else 'Rejected'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE asset_loan SET status = %s WHERE loan_id = %s", (new_status, loan_id))
        conn.commit()
        flash(f'Đã {new_status} đơn mượn thành công!', 'success')
    except Error as e:
        flash(f"LỖI: {e.msg}", 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_teacher_dashboard'))

@app.route('/admin/return_loan/<int:loan_id>', methods=['POST'])
def admin_return_loan(loan_id):
    if 'user_id' not in session or session.get('role') != 'Lab Manager':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Trigger trg_after_update_asset_loan tự chuyển trạng thái máy về Available
        cursor.execute("UPDATE asset_loan SET status = 'Returned', return_date = NOW() WHERE loan_id = %s", (loan_id,))
        conn.commit()
        flash('Đã xác nhận thu hồi thiết bị thành công!', 'success')
    except Error as e:
        conn.rollback()
        flash(f'Lỗi khi trả thiết bị: {e.msg}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_teacher_dashboard'))

@app.route('/admin/maintenance/<int:asset_id>', methods=['POST'])
def admin_maintenance_asset(asset_id):
    if 'user_id' not in session or session.get('role') != 'Lab Manager':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE asset SET status = 'Under Maintenance' WHERE asset_id = %s", (asset_id,))
        conn.commit()
        flash(f'Đã chuyển thiết bị ID {asset_id} sang trạng thái bảo trì.', 'warning')
    except Error as e:
        conn.rollback()
        flash(f'Lỗi CSDL: {e.msg}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_teacher_dashboard'))

@app.route('/admin/finish_maintenance/<int:asset_id>', methods=['POST'])
def admin_finish_maintenance(asset_id):
    # Chỉ Lab Manager (hoặc Technician) mới được hoàn tất bảo trì
    if 'user_id' not in session or session.get('role') not in ['Lab Manager', 'Technician']:
        flash('Bạn không có quyền xác nhận hoàn tất bảo trì!', 'danger')
        return redirect(url_for('admin_teacher_dashboard'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE asset SET status = 'Available' WHERE asset_id = %s", (asset_id,))
        conn.commit()
        flash(f'Đã hoàn tất bảo trì! Thiết bị (ID: {asset_id}) đã sẵn sàng để mượn.', 'success')
    except Error as e:
        conn.rollback()
        flash(f'Lỗi CSDL: {e.msg}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_teacher_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)