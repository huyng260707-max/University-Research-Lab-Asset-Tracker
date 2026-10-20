-- ============================================================================
-- DATABASE SCHEMA ACCORDING TO REVISED REPORT
-- ============================================================================
DROP DATABASE IF EXISTS lab_asset_tracker; 
CREATE DATABASE lab_asset_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; 
USE lab_asset_tracker;

SET GLOBAL event_scheduler = ON;

-- 1. BẢNG DỮ LIỆU
CREATE TABLE department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_code VARCHAR(20) NOT NULL UNIQUE,
    dept_name VARCHAR(100) NOT NULL,
    building VARCHAR(50) NULL,
    phone VARCHAR(20) NULL
) ENGINE=InnoDB;

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

CREATE TABLE safety_certification (
    cert_id INT AUTO_INCREMENT PRIMARY KEY,
    cert_code VARCHAR(20) NOT NULL UNIQUE,
    cert_name VARCHAR(100) NOT NULL,
    validity_months INT NOT NULL DEFAULT 12,
    description TEXT NOT NULL,
    CONSTRAINT chk_cert_validity CHECK (validity_months > 0)
) ENGINE=InnoDB;

CREATE TABLE personnel_certification (
    personnel_id INT NOT NULL,
    cert_id INT NOT NULL,
    issue_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    expiry_date DATE NOT NULL,
    PRIMARY KEY (personnel_id, cert_id),
    CONSTRAINT chk_cert_dates CHECK (expiry_date > issue_date),
    CONSTRAINT fk_pc_personnel FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id) ON DELETE CASCADE,
    CONSTRAINT fk_pc_cert FOREIGN KEY (cert_id) REFERENCES safety_certification(cert_id) ON DELETE CASCADE
) ENGINE=InnoDB;

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

CREATE TABLE supplier (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_code VARCHAR(20) NOT NULL UNIQUE,
    supplier_name VARCHAR(100) NOT NULL,
    contact_email VARCHAR(100) NULL,
    phone VARCHAR(20) NULL,
    address VARCHAR(255) NULL
) ENGINE=InnoDB;

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

CREATE TABLE asset_required_certification (
    asset_id INT NOT NULL,
    cert_id INT NOT NULL,
    PRIMARY KEY (asset_id, cert_id),
    CONSTRAINT fk_arc_asset FOREIGN KEY (asset_id) REFERENCES asset(asset_id) ON DELETE CASCADE,
    CONSTRAINT fk_arc_cert FOREIGN KEY (cert_id) REFERENCES safety_certification(cert_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE asset_loan (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_code VARCHAR(30) NOT NULL UNIQUE,
    asset_id INT NOT NULL,
    personnel_id INT NOT NULL,
    project_id INT NULL,
    checkout_date DATETIME NOT NULL DEFAULT NOW(),
    due_date DATETIME NOT NULL,
    return_date DATETIME NULL,
    is_pi_approved BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by_pi INT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    CONSTRAINT chk_loan_due_date CHECK (due_date >= checkout_date),
    CONSTRAINT chk_loan_return_date CHECK (return_date IS NULL OR return_date >= checkout_date),
    CONSTRAINT chk_loan_status CHECK (status IN ('Active', 'Returned', 'Overdue', 'Lost')),
    CONSTRAINT fk_loan_asset FOREIGN KEY (asset_id) REFERENCES asset(asset_id) ON DELETE RESTRICT,
    CONSTRAINT fk_loan_personnel FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id) ON DELETE RESTRICT,
    CONSTRAINT fk_loan_project FOREIGN KEY (project_id) REFERENCES research_project(project_id) ON DELETE SET NULL,
    CONSTRAINT fk_loan_pi FOREIGN KEY (approved_by_pi) REFERENCES personnel(personnel_id) ON DELETE SET NULL
) ENGINE=InnoDB;

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

-- 2. TRIGGERS TỰ ĐỘNG SINH MÃ CODE (GIÚP FLASK / APP.PY KHÔNG BỊ LỖI NOT NULL)
DELIMITER $$

CREATE TRIGGER trg_auto_asset_code BEFORE INSERT ON asset
FOR EACH ROW BEGIN
    IF NEW.asset_code IS NULL OR NEW.asset_code = '' THEN
        SET NEW.asset_code = CONCAT('AST-LAB', NEW.lab_id, '-', YEAR(CURDATE()), '-', LPAD((SELECT IFNULL(MAX(asset_id), 0) + 1 FROM asset), 4, '0'));
    END IF;
END$$

CREATE TRIGGER trg_auto_loan_code BEFORE INSERT ON asset_loan
FOR EACH ROW BEGIN
    IF NEW.loan_code IS NULL OR NEW.loan_code = '' THEN
        SET NEW.loan_code = CONCAT('LN-', YEAR(CURDATE()), '-', LPAD((SELECT IFNULL(MAX(loan_id), 0) + 1 FROM asset_loan), 5, '0'));
    END IF;
END$$

-- Trigger kiểm tra điều kiện mượn (BR-04, BR-05, BR-09)
CREATE TRIGGER trg_before_insert_asset_loan BEFORE INSERT ON asset_loan
FOR EACH ROW BEGIN
    DECLARE v_asset_status VARCHAR(30);
    DECLARE v_missing_certs INT DEFAULT 0;
    DECLARE v_overlap_count INT DEFAULT 0;

    SELECT status INTO v_asset_status FROM asset WHERE asset_id = NEW.asset_id;

    IF v_asset_status != 'Available' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Loi: Thiet bi khong o trang thai Available.';
    END IF;

    SELECT COUNT(*) INTO v_missing_certs FROM asset_required_certification arc 
    WHERE arc.asset_id = NEW.asset_id AND arc.cert_id NOT IN (
        SELECT pc.cert_id FROM personnel_certification pc 
        WHERE pc.personnel_id = NEW.personnel_id AND pc.expiry_date >= NEW.checkout_date
    );
    IF v_missing_certs > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Loi: Thieu chung chi an toan con han.';
    END IF;

    SELECT COUNT(*) INTO v_overlap_count FROM asset_loan
    WHERE asset_id = NEW.asset_id AND status = 'Active'
      AND NOT (NEW.due_date < checkout_date OR NEW.checkout_date > due_date);
    IF v_overlap_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Loi: Trung lich muon thiet bi.';
    END IF;
END$$

CREATE TRIGGER trg_after_insert_asset_loan AFTER INSERT ON asset_loan
FOR EACH ROW BEGIN
    IF NEW.status = 'Active' THEN UPDATE asset SET status = 'In Use' WHERE asset_id = NEW.asset_id; END IF;
END$$

CREATE TRIGGER trg_after_update_asset_loan AFTER UPDATE ON asset_loan
FOR EACH ROW BEGIN
    IF NEW.status = 'Returned' AND OLD.status != 'Returned' THEN UPDATE asset SET status = 'Available' WHERE asset_id = NEW.asset_id; END IF;
END$$

CREATE TRIGGER trg_after_insert_maintenance AFTER INSERT ON maintenance_record
FOR EACH ROW BEGIN
    IF NEW.status IN ('Pending', 'In Progress') THEN UPDATE asset SET status = 'Under Maintenance' WHERE asset_id = NEW.asset_id; END IF;
END$$

DELIMITER ;

-- 3. ANALYTICAL VIEWS
CREATE OR REPLACE VIEW view_overdue_assets AS
SELECT 
    al.loan_id, al.loan_code, a.asset_id, a.asset_code, a.asset_name,
    p.full_name AS borrower_name, p.email AS borrower_email, p.phone AS borrower_phone,
    al.checkout_date, al.due_date, DATEDIFF(CURRENT_DATE, al.due_date) AS days_overdue
FROM asset_loan al
JOIN asset a ON al.asset_id = a.asset_id
JOIN personnel p ON al.personnel_id = p.personnel_id
WHERE al.status = 'Active' AND al.due_date < CURRENT_DATE;

CREATE OR REPLACE VIEW view_asset_summary_by_lab AS
SELECT 
    d.dept_name, l.lab_name, l.room_location,
    COUNT(a.asset_id) AS total_assets, SUM(a.purchase_price) AS total_asset_value
FROM lab l
JOIN department d ON l.department_id = d.department_id
LEFT JOIN asset a ON l.lab_id = a.lab_id
GROUP BY d.dept_name, l.lab_name, l.room_location;