DDL Script (Tables, Views, Indexes, Triggers)

- 09 Tables
  + deparment
  + lab
  + personnel
  + research_project
  + project_assignment
  + supplier
  + asset
  + aser_loan
  + maintenance_record

- 02 Views
  + view_overdue_assets (Thống kê danh sách các thiết bị quá hạn mượn kèm thông tin liên hệ người mượn)
  + view_asset_summary_by_lab (Tổng hợp số lượng và tổng giá trị tài sản hiện có theo từng Khoa và Phòng Lab.)

- 4 Indexes
  + idx_asset_loan_dates
  + idx_asset_lab_status_cat
  + idx_maintenance_asset_status
  + idx_project_assignment_lookup
 
- 10 Triggers
  + Nhóm tự động sinh mã định danh(BR-01):
    1. trg_auto_asset_code: Tự động tạo mã tài sản (AST-LABx-YYYY-xxxx).
    2. trg_auto_loan_code: Tự động tạo mã phiếu mượn (LN-YYYY-xxxxx).
  + Nhóm kiểm soát đặt chỗ & trạng thái thiết bị (BR-04, BR-05, BR-07):
    1. trg_check_loan_dates_insert: Kiểm tra ngày trả (due_date) phải lớn hơn hoặc bằng ngày mượn (checkout_date) (BR-04).
    2. trg_prevent_overlapping_loans_insert: Chặn đặt mượn trùng khoảng thời gian khi tạo mới phiếu mượn (BR-05).
    3. trg_prevent_overlapping_loans_update: Chặn dời lịch gây trùng lặp thời gian khi cập nhật phiếu mượn (BR-05).
    4. trg_check_asset_availability: Chỉ cho phép mượn thiết bị đang ở trạng thái sẵn sàng (Available) (BR-04 & BR-07).
  + Nhóm kiểm soát hạn mức, phê duyệt & bảo trì (BR-06, BR-08, BR-09):
    1. trg_check_student_loan_limit: Chặn sinh viên mượn quá 48 giờ nếu không gắn mã dự án (project_id) hợp lệ mà sinh viên đó là thành viên (BR-06).
    2. trg_enforce_loan_reason_and_status: Bắt buộc nhập lý do mượn (loan_reason) và gán trạng thái mặc định Pending (BR-08).
    3. trg_after_update_asset_loan: Tự động chuyển trạng thái thiết bị sang In Use khi duyệt mượn và trả về Available khi hoàn trả.
    4. trg_after_insert_maintenance: Tự động khóa thiết bị sang trạng thái Under Maintenance ngay khi phát sinh phiếu bảo trì/sự cố (BR-07 & BR-09).
