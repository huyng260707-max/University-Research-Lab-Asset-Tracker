from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import secrets
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'langberry14', 
    'database': 'lab_asset_tracker'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Hàm phụ trợ: Kiểm tra giờ hành chính (7h-11h, 13h-17h)
def is_business_hours(dt_str):
    if not dt_str: return False
    dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M')
    hour = dt.hour
    return (7 <= hour < 11) or (13 <= hour < 17)

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'Student':
            return redirect(url_for('borrow_portal'))
        else:
            return redirect(url_for('admin_teacher_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Sửa thành nhận 'personnel_code' (mã SV/GV) thay vì email
        personnel_code = request.form.get('personnel_code')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Đổi điều kiện WHERE từ email sang personnel_code
        cursor.execute("SELECT * FROM personnel WHERE personnel_code = %s", (personnel_code,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['personnel_id']
            session['role'] = user['role']
            session['full_name'] = ("Giảng viên " + user['full_name']) if user['role'] in ['Lecturer', 'PI'] else user['full_name']
            return redirect(url_for('index'))
        else:
            # Cập nhật lại câu thông báo lỗi
            flash('Sai mã đăng nhập hoặc mật khẩu!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# TRANG MƯỢN THIẾT BỊ (Dùng chung cho Student, PI, Lecturer)
@app.route('/borrow')
def borrow_portal():
    if 'user_id' not in session or session.get('role') == 'Lab Manager':
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    
    try:
        cursor.execute("SELECT asset_id, asset_name,hazard_level, status FROM asset")
        assets = cursor.fetchall()
        
        # Nếu là Student, lấy dự án họ tham gia. Nếu là PI, lấy dự án họ làm chủ nhiệm.
        if session['role'] == 'Student':
            cursor.execute("""
                SELECT rp.project_id, rp.title FROM research_project rp
                JOIN project_assignment pa ON rp.project_id = pa.project_id
                WHERE pa.personnel_id = %s
            """, (user_id,))
        else:
            cursor.execute("SELECT project_id, title FROM research_project WHERE pi_id = %s", (user_id,))
        projects = cursor.fetchall()

        cursor.execute("""
            SELECT al.loan_id, al.loan_code, a.asset_name, al.checkout_date, al.due_date, al.status, al.loan_reason
            FROM asset_loan al JOIN asset a ON al.asset_id = a.asset_id
            WHERE al.personnel_id = %s ORDER BY al.loan_id DESC
        """, (user_id,))
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
    if 'user_id' not in session: return redirect(url_for('index'))

    asset_id = request.form['asset_id']
    project_id = request.form.get('project_id') or None
    loan_reason = request.form.get('loan_reason')
    checkout_date = request.form.get('start_time')
    due_date = request.form.get('end_time')
    
    # Validation giờ hành chính ở Backend
    if not is_business_hours(checkout_date) or not is_business_hours(due_date):
        flash('LỖI: Thời gian mượn/trả phải nằm trong giờ hành chính (7h-11h hoặc 13h-17h)!', 'danger')
        return redirect(url_for('borrow_portal'))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # DB Triggers (BR-04, BR-05, BR-06, BR-07, BR-08) sẽ lo phần kiểm tra còn lại
        cursor.execute("""
            INSERT INTO asset_loan (asset_id, personnel_id, project_id, loan_reason, checkout_date, due_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (asset_id, session['user_id'], project_id, loan_reason, checkout_date, due_date))
        conn.commit()
        flash('Tạo phiếu mượn thành công! Đang chờ duyệt.', 'success')
    except Error as e:
        if e.errno == 1644: # Bắt lỗi từ MySQL Trigger
            flash(f"LỖI NGHIỆP VỤ (Từ CSDL): {e.msg}", 'danger')
        else:
            flash(f"LỖI HỆ THỐNG: {e.msg}", 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('borrow_portal'))

@app.route('/dashboard')
def admin_teacher_dashboard():
    if 'user_id' not in session or session['role'] == 'Student':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Đơn Pending
    if session['role'] == 'Lab Manager':
        cursor.execute("""
            SELECT al.*, a.asset_name, p.full_name as student_name, p.role as borrower_role 
            FROM asset_loan al
            JOIN asset a ON al.asset_id = a.asset_id
            JOIN personnel p ON al.personnel_id = p.personnel_id
            WHERE al.status = 'Pending'
        """)
    elif session['role'] == 'PI':
        # PI chỉ thấy đơn của Student thuộc dự án của mình (không tự thấy đơn của chính mình)
        cursor.execute("""
            SELECT al.*, a.asset_name, p.full_name as student_name, p.role as borrower_role 
            FROM asset_loan al
            JOIN asset a ON al.asset_id = a.asset_id
            JOIN personnel p ON al.personnel_id = p.personnel_id
            JOIN research_project rp ON al.project_id = rp.project_id
            WHERE al.status = 'Pending' AND rp.pi_id = %s AND p.role = 'Student'
        """, (session['user_id'],))
    else: # Lecturer bình thường không có quyền duyệt
        pending_loans = []
        
    if session['role'] in ['Lab Manager', 'PI']:
        pending_loans = cursor.fetchall()

    # 2. Các Đơn Đang Mượn (Chỉ Admin thu hồi được)
    cursor.execute("""
        SELECT al.*, a.asset_name, p.full_name as student_name 
        FROM asset_loan al
        JOIN asset a ON al.asset_id = a.asset_id
        JOIN personnel p ON al.personnel_id = p.personnel_id
        WHERE al.status = 'Active'
    """)
    active_loans = cursor.fetchall()

    # 3 & 4. Quá Hạn & Kho
    cursor.execute("SELECT * FROM view_overdue_assets")
    overdue_loans = cursor.fetchall()
    
    cursor.execute("SELECT a.*, l.lab_name FROM asset a JOIN lab l ON a.lab_id = l.lab_id ORDER BY a.asset_id DESC")
    assets = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template('admin_teacher.html', pending_loans=pending_loans, active_loans=active_loans, overdue_loans=overdue_loans, assets=assets)

def get_asset_form_options(cursor):
    cursor.execute("SELECT department_id, dept_name FROM department ORDER BY dept_name")
    departments = cursor.fetchall()
    cursor.execute("""
        SELECT l.lab_id, l.lab_name, l.department_id, d.dept_name
        FROM lab l
        JOIN department d ON d.department_id = l.department_id
        ORDER BY d.dept_name, l.lab_name
    """)
    labs = cursor.fetchall()
    cursor.execute("SELECT supplier_id, supplier_name FROM supplier ORDER BY supplier_name")
    suppliers = cursor.fetchall()
    return departments, labs, suppliers

@app.route('/admin/add_asset', methods=['GET', 'POST'])
def admin_add_asset():
    if 'user_id' not in session or session.get('role') != 'Lab Manager':
        return redirect(url_for('index'))

    csrf_token = session.setdefault('_csrf_token', secrets.token_urlsafe(32))
    form = request.form if request.method == 'POST' else {}
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        departments, labs, suppliers = get_asset_form_options(cursor)

        if request.method == 'GET':
            return render_template(
                'add_asset.html', departments=departments, labs=labs,
                suppliers=suppliers, form={}, csrf_token=csrf_token,
                today=date.today().isoformat()
            )

        submitted_token = request.form.get('csrf_token', '')
        if not secrets.compare_digest(csrf_token, submitted_token):
            abort(400)

        asset_name = request.form.get('asset_name', '').strip()
        category = request.form.get('category', '').strip()
        hazard_level = request.form.get('hazard_level', '')
        serial_number = request.form.get('serial_number', '').strip()
        department_id = request.form.get('department_id', '')
        lab_id = request.form.get('lab_id', '')
        supplier_id = request.form.get('supplier_id', '')
        purchase_date_text = request.form.get('purchase_date', '')
        warranty_expiry_text = request.form.get('warranty_expiry', '').strip()
        price_text = request.form.get('purchase_price', '').strip()

        errors = []
        if not asset_name or len(asset_name) > 100:
            errors.append('Tên thiết bị là bắt buộc và tối đa 100 ký tự.')
        if not category or len(category) > 50:
            errors.append('Danh mục là bắt buộc và tối đa 50 ký tự.')
        if hazard_level not in ('None', 'Low', 'Medium', 'High'):
            errors.append('Mức độ nguy hiểm không hợp lệ.')
        if not serial_number or len(serial_number) > 50:
            errors.append('Số sê-ri hãng là bắt buộc và tối đa 50 ký tự.')

        try:
            purchase_price = Decimal(price_text)
            if not purchase_price.is_finite() or purchase_price <= 0:
                errors.append('Giá mua phải lớn hơn 0.')
            elif purchase_price > Decimal('9999999999.99'):
                errors.append('Giá mua vượt giới hạn lưu trữ của CSDL.')
        except (InvalidOperation, ValueError):
            purchase_price = None
            errors.append('Giá mua không hợp lệ.')

        try:
            purchase_date = date.fromisoformat(purchase_date_text)
        except ValueError:
            purchase_date = None
            errors.append('Ngày mua không hợp lệ.')

        try:
            warranty_expiry = date.fromisoformat(warranty_expiry_text) if warranty_expiry_text else None
        except ValueError:
            warranty_expiry = None
            errors.append('Ngày hết hạn bảo hành không hợp lệ.')

        if purchase_date and warranty_expiry and warranty_expiry < purchase_date:
            errors.append('Ngày hết hạn bảo hành không được trước ngày mua.')

        if not department_id.isdigit() or not lab_id.isdigit():
            errors.append('Vui lòng chọn Khoa và Phòng Lab.')
        elif not any(str(lab['lab_id']) == lab_id and str(lab['department_id']) == department_id for lab in labs):
            errors.append('Phòng Lab không thuộc Khoa đã chọn.')

        if not supplier_id.isdigit() or not any(str(s['supplier_id']) == supplier_id for s in suppliers):
            errors.append('Vui lòng chọn nhà cung cấp hợp lệ.')

        if errors:
            for message in errors:
                flash(message, 'danger')
            return render_template(
                'add_asset.html', departments=departments, labs=labs,
                suppliers=suppliers, form=form, csrf_token=csrf_token,
                today=date.today().isoformat()
            ), 400

        cursor.execute("""
            INSERT INTO asset (
                asset_code, lab_id, supplier_id, asset_name, category,
                hazard_level, serial_number, purchase_date, purchase_price,
                warranty_expiry, status
            ) VALUES ('', %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Available')
        """, (
            int(lab_id), int(supplier_id), asset_name, category,
            hazard_level, serial_number, purchase_date,
            purchase_price, warranty_expiry
        ))
        conn.commit()
        flash('Đã thêm thiết bị vào kho thành công.', 'success')
        return redirect(url_for('admin_teacher_dashboard') + '#inventory')
    except Error as e:
        if conn:
            conn.rollback()
        if e.errno == 1062:
            flash('Số sê-ri này đã tồn tại. Vui lòng kiểm tra lại.', 'danger')
        else:
            flash('Không thể thêm thiết bị. Hãy kiểm tra kết nối và dữ liệu CSDL.', 'danger')
        return redirect(url_for('admin_teacher_dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/approve/<int:loan_id>', methods=['POST'])
def approve_loan(loan_id):
    if 'user_id' not in session or session['role'] not in ['Lab Manager', 'PI']:
        return redirect(url_for('index'))

    action = request.form.get('action', 'Approve')
    new_status = 'Active' if action == 'Approve' else 'Rejected'
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # BẢO MẬT: Kiểm tra xem user này có quyền duyệt đơn này không
        cursor.execute("SELECT project_id, personnel_id FROM asset_loan WHERE loan_id = %s", (loan_id,))
        loan = cursor.fetchone()
        
        has_permission = False
        if session['role'] == 'Lab Manager':
            has_permission = True
        elif session['role'] == 'PI' and loan['project_id']:
            cursor.execute("SELECT pi_id FROM research_project WHERE project_id = %s", (loan['project_id'],))
            proj = cursor.fetchone()
            # PI được duyệt nếu sở hữu dự án VÀ không phải tự duyệt cho chính mình
            if proj and proj['pi_id'] == session['user_id'] and loan['personnel_id'] != session['user_id']:
                has_permission = True

        if not has_permission:
            flash('LỖI BẢO MẬT: Bạn không có quyền duyệt phiếu mượn này!', 'danger')
            return redirect(url_for('admin_teacher_dashboard'))

        cursor.execute("UPDATE asset_loan SET status = %s, approved_by_pi = %s WHERE loan_id = %s", 
                       (new_status, session['user_id'], loan_id))
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
        
    issue = request.form.get('issue_description')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # CHUẨN: Chèn vào maintenance_record, Trigger trg_after_insert_maintenance sẽ tự đổi status asset
        cursor.execute("""
            INSERT INTO maintenance_record (record_code, asset_id, technician_id, issue_description, status) 
            VALUES ('', %s, %s, %s, 'In Progress')
        """, (asset_id, session['user_id'], issue))
        conn.commit()
        flash(f'Đã tạo phiếu và chuyển thiết bị ID {asset_id} sang trạng thái bảo trì.', 'warning')
    except Error as e:
        conn.rollback()
        flash(f'Lỗi CSDL: {e.msg}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_teacher_dashboard'))

@app.route('/admin/finish_maintenance/<int:asset_id>', methods=['POST'])
def admin_finish_maintenance(asset_id):
    if 'user_id' not in session or session.get('role') != 'Lab Manager':
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Hoàn tất bản ghi bảo trì gần nhất đang In Progress
        cursor.execute("""
            UPDATE maintenance_record SET status = 'Completed', resolved_date = NOW() 
            WHERE asset_id = %s AND status = 'In Progress' ORDER BY maintenance_id DESC LIMIT 1
        """, (asset_id,))
        # Giải phóng thiết bị
        cursor.execute("UPDATE asset SET status = 'Available' WHERE asset_id = %s", (asset_id,))
        conn.commit()
        flash(f'Đã hoàn tất bảo trì! Thiết bị (ID: {asset_id}) đã sẵn sàng.', 'success')
    except Error as e:
        conn.rollback()
        flash(f'Lỗi CSDL: {e.msg}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_teacher_dashboard'))

@app.route('/fix-passwords')
def fix_passwords():
    # Tạo mã hash CHUẨN cho mật khẩu "12345678" ngay trên máy của bạn
    valid_hash = bcrypt.hashpw(b"12345678", bcrypt.gensalt()).decode('utf-8')
    
    # Kết nối DB và cập nhật lại toàn bộ tài khoản
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE personnel SET password_hash = %s", (valid_hash,))
        conn.commit()
        return f"Đã sửa lỗi thành công! Tất cả tài khoản đã được đổi mật khẩu về 12345678.<br>Mã hash chuẩn mới là: {valid_hash}<br><a href='/'>Bấm vào đây để về trang Đăng nhập</a>"
    except Exception as e:
        return f"Lỗi: {e}"
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
