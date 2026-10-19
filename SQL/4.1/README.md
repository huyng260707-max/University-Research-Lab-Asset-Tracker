DDL Script (Tables, Views, Indexes, Triggers)

- 11 Tables
  + deparment
  + lab
  + personnel
  + safety_certification
  + persionnel_certification
  + research_project
  + project_assignment
  + supplier
  + asset
  + aser_loan
  + maintenance_record

- 2 Views
  + view_overdue_assets (Thống kê danh sách các thiết bị quá hạn mượn)
  + view_lab_asset_summary (Tổng giá trị tài sản hiện có theo từng phòng lab)

- 3 Indexes
  + idx_asset_loan_dates
  + idx_asset_status
  + idx_maintenance_asset
 
- 2 Triggers
  + BR-04 (Tính hợp lệ của Đặt chỗ)
  + BR-10 (Tự động khóa thiết bị khi xảy ra sự cố nghiêm trọng)
  
