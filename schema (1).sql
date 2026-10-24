DROP DATABASE IF EXISTS lab_asset_tracker; 
CREATE DATABASE lab_asset_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; 
USE lab_asset_tracker;

SET GLOBAL event_scheduler = ON;

-- 1.1 Bảng Department (Khoa / Bộ môn)
CREATE TABLE department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_code VARCHAR(20) NOT NULL UNIQUE,
    dept_name VARCHAR(100) NOT NULL,
    building VARCHAR(50) NULL,
    phone VARCHAR(20) NULL
) ENGINE=InnoDB;

-- 1.2 Bảng Lab (Phòng thí nghiệm)
CREATE TABLE lab (
    lab_id INT AUTO_INCREMENT PRIMARY KEY,
    lab_code VARCHAR(20) NOT NULL UNIQUE,
    department_id INT NOT NULL,
    lab_name VARCHAR(100) NOT NULL,
    room_location VARCHAR(50) NOT NULL UNIQUE,
    capacity INT NOT NULL DEFAULT 10,
    CONSTRAINT chk_lab_capacity CHECK (capacity > 0),
    CONSTRAINT fk_lab_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 1.3 Bảng Personnel (Nhân sự & Sinh viên)
CREATE TABLE personnel (
    personnel_id INT AUTO_INCREMENT PRIMARY KEY,
    personnel_code VARCHAR(20) NOT NULL UNIQUE,
    department_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Student',
    phone VARCHAR(20) NULL,
    start_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT chk_personnel_role CHECK (role IN ('Student', 'Researcher', 'Lecturer', 'PI', 'Technician', 'Lab Manager')),
    CONSTRAINT fk_personnel_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 1.4 Bảng Research Project (Đề tài nghiên cứu)
CREATE TABLE research_project (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    pi_id INT NOT NULL,
    lab_id INT NOT NULL,
    start_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    end_date DATE NULL,
    funding_source VARCHAR(100) NULL,
    budget DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    CONSTRAINT chk_project_budget CHECK (budget >= 0),
    CONSTRAINT chk_project_dates CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT chk_project_status CHECK (status IN ('Pending', 'Active', 'Completed', 'Terminated')),
    CONSTRAINT fk_project_pi FOREIGN KEY (pi_id) REFERENCES personnel(personnel_id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_lab FOREIGN KEY (lab_id) REFERENCES lab(lab_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 1.5 Bảng Project Assignment (Phân công tham gia đề tài)
CREATE TABLE project_assignment (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    personnel_id INT NOT NULL,
    role_in_project VARCHAR(50) NOT NULL DEFAULT 'Member',
    join_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT uq_project_personnel UNIQUE (project_id, personnel_id),
    CONSTRAINT fk_pa_project FOREIGN KEY (project_id) REFERENCES research_project(project_id) ON DELETE CASCADE,
    CONSTRAINT fk_pa_personnel FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 1.6 Bảng Supplier (Nhà cung cấp)
CREATE TABLE supplier (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_code VARCHAR(20) NOT NULL UNIQUE,
    supplier_name VARCHAR(100) NOT NULL,
    contact_email VARCHAR(100) NULL,
    phone VARCHAR(20) NULL,
    address VARCHAR(255) NULL
) ENGINE=InnoDB;

-- 1.7 Bảng Asset (Thiết bị / Tài sản)
CREATE TABLE asset (
    asset_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_code VARCHAR(30) NOT NULL UNIQUE,
    lab_id INT NOT NULL,
    supplier_id INT NOT NULL,
    asset_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'General',
    hazard_level VARCHAR(20) NOT NULL DEFAULT 'Low',
    serial_number VARCHAR(50) NOT NULL UNIQUE,
    purchase_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    purchase_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    warranty_expiry DATE NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Available',
    CONSTRAINT chk_asset_price CHECK (purchase_price >= 0),
    CONSTRAINT chk_asset_hazard CHECK (hazard_level IN ('None', 'Low', 'Medium', 'High')),
    CONSTRAINT chk_asset_status CHECK (status IN ('Available', 'In Use', 'Under Maintenance', 'Decommissioned')),
    CONSTRAINT fk_asset_lab FOREIGN KEY (lab_id) REFERENCES lab(lab_id) ON DELETE RESTRICT,
    CONSTRAINT fk_asset_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 1.8 Bảng Asset Loan (Lượt mượn / trả thiết bị)
CREATE TABLE asset_loan (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_code VARCHAR(30) NOT NULL UNIQUE,
    asset_id INT NOT NULL,
    personnel_id INT NOT NULL,
    project_id INT NULL,
    loan_reason TEXT NOT NULL,
    checkout_date DATETIME NOT NULL DEFAULT NOW(),
    due_date DATETIME NOT NULL,
    return_date DATETIME NULL,
    is_pi_approved BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by_pi INT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    CONSTRAINT chk_loan_due_date CHECK (due_date >= checkout_date),
    CONSTRAINT chk_loan_return_date CHECK (return_date IS NULL OR return_date >= checkout_date),
    CONSTRAINT chk_loan_status CHECK (status IN ('Pending', 'Active', 'Returned', 'Overdue', 'Lost', 'Rejected')),
    CONSTRAINT fk_loan_asset FOREIGN KEY (asset_id) REFERENCES asset(asset_id) ON DELETE RESTRICT,
    CONSTRAINT fk_loan_personnel FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id) ON DELETE RESTRICT,
    CONSTRAINT fk_loan_project FOREIGN KEY (project_id) REFERENCES research_project(project_id) ON DELETE SET NULL,
    CONSTRAINT fk_loan_pi FOREIGN KEY (approved_by_pi) REFERENCES personnel(personnel_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 1.9 Bảng Maintenance Record (Hồ sơ bảo trì)
CREATE TABLE maintenance_record (
    maintenance_id INT AUTO_INCREMENT PRIMARY KEY,
    record_code VARCHAR(30) NOT NULL UNIQUE,
    asset_id INT NOT NULL,
    technician_id INT NOT NULL,
    issue_description TEXT NOT NULL,
    reported_date DATETIME NOT NULL DEFAULT NOW(),
    resolved_date DATETIME NULL,
    cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    CONSTRAINT chk_maint_cost CHECK (cost >= 0),
    CONSTRAINT chk_maint_dates CHECK (resolved_date IS NULL OR resolved_date >= reported_date),
    CONSTRAINT chk_maint_status CHECK (status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')),
    CONSTRAINT fk_maint_asset FOREIGN KEY (asset_id) REFERENCES asset(asset_id) ON DELETE RESTRICT,
    CONSTRAINT fk_maint_tech FOREIGN KEY (technician_id) REFERENCES personnel(personnel_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_asset_loan_status_dates ON asset_loan(asset_id, status, checkout_date, due_date);
CREATE INDEX idx_asset_lab_status_cat ON asset(lab_id, status, category); 
CREATE INDEX idx_maintenance_asset_status ON maintenance_record(asset_id, status, reported_date);
CREATE INDEX idx_project_assignment_lookup ON project_assignment(personnel_id, project_id); 

DELIMITER $$

-- Trigger tự động tạo mã Asset Code
CREATE TRIGGER trg_auto_asset_code BEFORE INSERT ON asset
FOR EACH ROW BEGIN
    IF NEW.asset_code IS NULL OR NEW.asset_code = '' THEN
        SET NEW.asset_code = CONCAT('AST-LAB', NEW.lab_id, '-', YEAR(CURDATE()), '-', LPAD((SELECT IFNULL(MAX(asset_id), 0) + 1 FROM asset), 4, '0'));
    END IF;
END$$

-- Trigger tự động tạo mã Loan Code
CREATE TRIGGER trg_auto_loan_code BEFORE INSERT ON asset_loan
FOR EACH ROW BEGIN
    IF NEW.loan_code IS NULL OR NEW.loan_code = '' THEN
        SET NEW.loan_code = CONCAT('LN-', YEAR(CURDATE()), '-', LPAD((SELECT IFNULL(MAX(loan_id), 0) + 1 FROM asset_loan), 5, '0'));
    END IF;
END$$

-- Trigger 1: Kiểm tra ngày mượn/trả hợp lệ (Áp dụng BR-04)
CREATE TRIGGER trg_check_loan_dates_insert
BEFORE INSERT ON asset_loan
FOR EACH ROW
BEGIN
    IF NEW.due_date < NEW.checkout_date THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'BR-04 Error: due_date không được nhỏ hơn checkout_date.';
    END IF;
END$$

-- Trigger 2: Chống trùng lặp lịch mượn (Áp dụng BR-05)
CREATE TRIGGER trg_prevent_overlapping_loans
BEFORE INSERT ON asset_loan
FOR EACH ROW
BEGIN
    DECLARE overlap_count INT;
    
    SELECT COUNT(*) INTO overlap_count
    FROM asset_loan
    WHERE asset_id = NEW.asset_id
      AND status IN ('Pending', 'Active')
      AND (NEW.checkout_date <= due_date AND NEW.due_date >= checkout_date);
      
    IF overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'BR-05 Error: Thiết bị này đã bị trùng lịch đặt chỗ trong khoảng thời gian trên.';
    END IF;
END$$

-- Trigger 3: Kiểm soát thời gian mượn của Sinh viên (Áp dụng BR-06)
CREATE TRIGGER trg_check_student_loan_limit
BEFORE INSERT ON asset_loan
FOR EACH ROW
BEGIN
    DECLARE user_role VARCHAR(50);
    DECLARE duration_hours INT;
    
    SELECT role INTO user_role FROM personnel WHERE personnel_id = NEW.personnel_id;
    SET duration_hours = TIMESTAMPDIFF(HOUR, NEW.checkout_date, NEW.due_date);
    
    IF user_role = 'Student' AND duration_hours > 48 AND NEW.project_id IS NULL THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'BR-06 Error: Sinh viên mượn quá 48 giờ bắt buộc phải gắn mã Đề tài nghiên cứu (project_id).';
    END IF;
END$$

-- Trigger 4: Kiểm tra trạng thái tài sản trước khi cho mượn (Áp dụng BR-04 & BR-07)
CREATE TRIGGER trg_check_asset_availability
BEFORE INSERT ON asset_loan
FOR EACH ROW
BEGIN
    DECLARE current_asset_status VARCHAR(50);
    
    SELECT status INTO current_asset_status 
    FROM asset 
    WHERE asset_id = NEW.asset_id;
    
    IF current_asset_status != 'Available' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'BR-04 & BR-07 Error: Chỉ có thể tạo phiếu mượn cho tài sản đang ở trạng thái Available.';
    END IF;
END$$

-- Trigger 5: Ép buộc Quy trình duyệt đơn và Lý do mượn (Áp dụng BR-09)
CREATE TRIGGER trg_enforce_loan_reason_and_status
BEFORE INSERT ON asset_loan
FOR EACH ROW
BEGIN
    IF NEW.loan_reason IS NULL OR TRIM(NEW.loan_reason) = '' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'BR-09 Error: Mọi yêu cầu mượn thiết bị bắt buộc phải có Lý do mượn (loan_reason).';
    END IF;
    
    IF NEW.status IS NULL THEN
        SET NEW.status = 'Pending';
    END IF;
END$$

-- Trigger 6: Tự động cập nhật trạng thái thiết bị theo trạng thái đơn mượn
CREATE TRIGGER trg_after_update_asset_loan AFTER UPDATE ON asset_loan
FOR EACH ROW BEGIN
    -- Duyệt đơn (Pending -> Active): Chuyển thiết bị sang In Use
    IF NEW.status = 'Active' AND OLD.status = 'Pending' THEN 
        UPDATE asset SET status = 'In Use' WHERE asset_id = NEW.asset_id; 
    END IF;
    
    -- Trả thiết bị (Active -> Returned): Chuyển thiết bị về Available
    IF NEW.status = 'Returned' AND OLD.status != 'Returned' THEN 
        UPDATE asset SET status = 'Available' WHERE asset_id = NEW.asset_id; 
    END IF;
END$$

-- Trigger 7: Tự động khóa thiết bị khi bảo trì (Áp dụng BR-07, BR-10)
CREATE TRIGGER trg_after_insert_maintenance AFTER INSERT ON maintenance_record
FOR EACH ROW BEGIN
    IF NEW.status IN ('Pending', 'In Progress') THEN 
        UPDATE asset SET status = 'Under Maintenance' WHERE asset_id = NEW.asset_id; 
    END IF;
END$$

DELIMITER ;

-- View 1: Thống kê danh sách thiết bị quá hạn mượn (Overdue Assets)
CREATE OR REPLACE VIEW view_overdue_assets AS
SELECT 
    al.loan_id, 
    al.loan_code, 
    a.asset_id, 
    a.asset_code, 
    a.asset_name,
    p.full_name AS borrower_name, 
    p.email AS borrower_email, 
    p.phone AS borrower_phone,
    al.checkout_date, 
    al.due_date, 
    DATEDIFF(CURRENT_DATE, al.due_date) AS days_overdue
FROM asset_loan al
JOIN asset a ON al.asset_id = a.asset_id
JOIN personnel p ON al.personnel_id = p.personnel_id
WHERE al.status = 'Active' 
  AND al.due_date < CURRENT_DATE;

-- View 2: Tổng hợp số lượng và tổng giá trị tài sản phân bổ theo Phòng Lab & Khoa
CREATE OR REPLACE VIEW view_asset_summary_by_lab AS
SELECT 
    d.dept_name, 
    l.lab_name, 
    l.room_location,
    COUNT(a.asset_id) AS total_assets, 
    IFNULL(SUM(a.purchase_price), 0.00) AS total_asset_value
FROM lab l
JOIN department d ON l.department_id = d.department_id
LEFT JOIN asset a ON l.lab_id = a.lab_id
GROUP BY d.dept_name, l.lab_name, l.room_location;