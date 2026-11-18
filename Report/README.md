   1.1 System Objective

Hệ thống "University Research & Lab Asset Tracker" được xây dựng nhằm mục đích số hóa và tự động hóa quy trình quản lý vòng đời thiết bị nghiên cứu tại các phòng thí nghiệm của trường đại học. Hệ thống giúp theo dõi tình trạng tài sản theo thời gian thực, quản lý lịch sử bảo trì để tăng tuổi thọ thiết bị, và tối ưu hóa luồng phê duyệt mượn/trả tài sản giữa Sinh viên, Nghiên cứu sinh và Giảng viên hướng dẫn (PI - Principal Investigator).


   1.2 Business Rules & Constraints
- Business Rules (Quy tắc nghiệp vụ cốt lõi):
  + BR-01 (Định danh Tài sản): Mỗi tài sản phải có một chuỗi định danh duy nhất dạng mã vạch hoặc RFID (ví dụ: AST-LAB-2026-XXXX). Số sê-ri của tài sản phải là duy nhất trong toàn bộ tổ chức.
  + BR-02 (Cấu trúc Tổ chức): Mỗi phòng thí nghiệm thuộc về duy nhất một Khoa chuyên môn. Tại bất kỳ thời điểm nào, mỗi tài sản nghiên cứu đều thuộc về duy nhất một phòng thí nghiệm.
  + BR-03 (Phân loại Tài sản): Tài sản được chia thành các Nhóm (ví dụ: Quang học, Máy tính, Quang phổ). Phân loại này quy định chu kỳ bảo trì mặc định và mức độ rủi ro (hazard_level: Low, Medium, High) của thiết bị khi vận hành.	
  + BR-04 (Tính hợp lệ của Đặt chỗ): Chỉ tiếp nhận phiếu mượn khi tài sản ‘Available’; due_date phải sau checkout_date. 
  + BR-05 (Không trùng lặp Đặt chỗ): Các khoảng mượn Pending hoặc Active của cùng tài sản không được giao nhau. Trigger khóa dòng asset tương ứng trước khi kiểm tra để tuần tự hóa yêu cầu cùng tài sản.
  + BR-06 (Hạn mức Đặt chỗ & Quy định Vai trò): Thời lượng mượn tài sản đối với người dùng là Sinh viên mặc định là 48 giờ liên tục. Các trường hợp mượn kéo dài hơn bắt buộc phải gắn mã Đề tài nghiên cứu (project_id) và được sự chấp thuận từ Chủ nhiệm đề tài (PI).
  + BR-07 (Ưu tiên Bảo trì): Khi tạo hồ sơ bảo trì, tài sản chuyển sang Under Maintenance; các phiếu Pending có thời điểm bắt đầu từ reported_date trở đi bị từ chối. Tài sản chỉ trở về Available sau khi mọi hồ sơ bảo trì mở được hoàn tất.
  + BR-08 (Quy trình Đăng ký & Phê duyệt Mượn): Mọi yêu cầu mượn thiết bị đều bắt buộc phải đính kèm "Lý do mượn" (loan_reason) chi tiết. Khi tạo mới, phiếu mượn mặc định ở trạng thái 'Pending'. Dựa trên lý do này và mức độ rủi ro (Hazard Level) của thiết bị, Quản lý Lab hoặc Giảng viên hướng dẫn (PI) sẽ quyết định phê duyệt (chuyển sang 'Active') hoặc từ chối (chuyển sang 'Rejected').
  + BR-09 (Tự động Khóa khi xảy ra Sự cố Nghiêm trọng): Mọi sự cố thiết bị được phân loại ở mức "Nghiêm trọng" sẽ tự động chuyển trạng thái thiết bị sang "Ngừng hoạt động" và tạm dừng việc đặt lịch mới cho đến khi thiết bị được kiểm tra lại về mặt an toàn.
  + BR-10 (Khung giờ Bàn giao & Hoàn trả): Mọi giao dịch nhận thiết bị (checkout_date) và hoàn trả thiết bị (due_date) tại phòng thí nghiệm chỉ được thực hiện trong khung giờ hành chính (Sáng: 07:00 – 11:00; Chiều: 13:00 – 17:00, từ Thứ Hai đến Thứ Bảy) để đảm bảo có nhân sự quản lý trực tiếp kiểm tra và xác nhận bàn giao.

- Constraints(Các ràng buộc):
  + Giá tiền của thiết bị bắt buộc phải lớn hơn hoặc bằng 0 (không chấp nhận số âm).
  + Mã số thiết bị và Email của người dùng không được phép trùng lặp trong hệ thống.
  + Tên thiết bị, tên phòng lab và họ tên người dùng là các thông tin bắt buộc, không được để trống.
  + Khi tạo phiếu mượn thiết bị, mã thiết bị và mã sinh viên nhập vào phải là mã có thật trong hệ thống.
  + Không được phép xóa thông tin một phòng lab nếu phòng đó vẫn còn thiết bị đang lưu trữ.
  + Vai trò của nhân sự trong hệ thống (role) chỉ được phép thuộc một trong 6 chức danh hợp lệ: Student, Researcher, Lecturer, PI, Technician, hoặc Lab Manager.
  + Sức chứa tối đa của mỗi phòng thí nghiệm (capacity) bắt buộc phải lớn hơn 0, và vị trí phòng (room_location) không được trùng lặp giữa các phòng Lab.
  + Ngân sách đề tài nghiên cứu (budget) và chi phí bảo trì thiết bị (cost) bắt buộc phải lớn hơn hoặc bằng 0.
  + Ngày kết thúc đề tài (end_date), ngày hoàn trả thực tế (return_date) và ngày hoàn tất bảo trì (resolved_date) không được phép nhỏ hơn ngày bắt đầu tương ứng (start_date, checkout_date, reported_date).
  + Một nhân sự chỉ được phép phân công tham gia tối đa một lần trong cùng một đề tài nghiên cứu (UNIQUE(project_id, personnel_id)).
  + Trạng thái của các thực thể chỉ được nhận các giá trị trong danh mục quy định: Đề tài (Pending, Active, Completed, Terminated), Thiết bị (Available, In Use, Under Maintenance, Decommissioned), Phiếu mượn (Pending, Active, Returned, Overdue, Lost, Rejected), và Bảo trì (Pending, In Progress, Completed, Cancelled).
- User Requirements(UR):
  + UR-01: Sinh viên cần tra cứu tài sản còn sẵn sàng và gửi yêu cầu mượn có nêu mục đích.
  + UR-02: PI cần xem xét yêu cầu của thành viên dự án và quyết định chấp thuận hoặc từ chối.
  + UR-03: Quản lý Lab cần quản lý tài sản, xử lý bảo trì và liên hệ người đang giữ tài sản quá hạn.
  + UR-04: Khoa cần xem số lượng và tổng giá trị tài sản theo Lab và theo Khoa.
- System Functional Requirements (FR):
  + FR-01: Hệ thống chỉ cho phép tạo yêu cầu mượn với tài sản Available và khoảng thời gian hợp lệ.
  + FR-02: Hệ thống lưu lý do mượn, trạng thái phê duyệt, người mượn, tài sản và dự án liên quan.
  + FR-03: Hệ thống ngăn khoảng mượn giao nhau cho cùng tài sản và giới hạn yêu cầu của sinh viên quá 48 giờ theo BR-06.
  + FR-04: Hệ thống khóa tài sản khi có hồ sơ bảo trì và từ chối các yêu cầu Pending tương lai bị ảnh hưởng.
  + FR-05: Hệ thống cung cấp danh sách tài sản quá hạn cùng thông tin liên hệ và báo cáo giá trị tài sản theo Lab/Khoa.
  + FR-06: Hệ thống ghi nhận severity cho hồ sơ bảo trì; Critical chuyển tài sản sang Out of Service.
- Non-Functional Requirements:
  + Bảo mật: Mật khẩu người dùng phải được băm (hash) bằng bcrypt.
  + Hiệu năng: Truy vấn lịch sử mượn thiết bị của một phòng lab trong 5 năm phải trả về kết quả dưới 200ms.

   1.3 Business Glossary
  -  Department (Khoa / Bộ môn): Đơn vị hành chính cao nhất quản lý các phòng thí nghiệm.
    o	dept_name: Tên định danh của khoa (ví dụ: Khoa Công nghệ Thông tin).
    o	building: Tòa nhà đặt văn phòng khoa.
    o	phone: Số điện thoại hotline/liên hệ của văn phòng khoa.
  -  Lab (Phòng thí nghiệm): Không gian vật lý trực thuộc Khoa, chuyên lưu trữ tài sản nghiên cứu.
    o	room_location: Mã định vị vật lý của phòng (ví dụ: A1-102).
    o	capacity: Sức chứa nhân sự tối đa của phòng.

  -  Tài sản nghiên cứu (Research Asset): Đối tượng vật lý (máy móc, thiết bị đo, hóa chất) thuộc sở hữu của nhà trường, có giá trị tài chính, gắn mã định danh duy nhất (Barcode/RFID/Serial) và vị trí quản lý cố định tại một phòng Lab.
  -  Nhân sự (Personnel): Các cá nhân hoạt động trong hệ thống, bao gồm Sinh viên (Student), Kỹ thuật viên (Technician), Quản lý Lab (Lab Manager) và Giảng viên/Chủ nhiệm đề tài (PI).
  -  Chủ nhiệm đề tài (Principal Investigator – PI): Giảng viên hoặc nhà nghiên cứu chịu trách nhiệm pháp lý, điều hành tiến độ và quản lý nguồn ngân sách của một dự án nghiên cứu. 
  -  Giao dịch mượn/trả (Asset Loan): Bản ghi động phản ánh việc cấp quyền sử dụng tạm thời một tài sản cho một nhân sự trong một khoảng thời gian xác định. 
  -  Lịch sử bảo trì (Maintenance Record): Bản ghi kỹ thuật theo dõi các đợt kiểm tra, sửa chữa, chi phí phát sinh và kỹ thuật viên phụ trách bảo dưỡng tài sản. 
  -  Phân công dự án (Project Assignment): Quá trình ghi nhận một nhân sự được tham gia vào một dự án nghiên cứu. Quyền hạn này là cơ sở hợp lệ để nhân sự được phép tạo phiếu mượn (Asset Loan) các thiết bị phục vụ cho dự án đó.
  - Personnel Certification: Bản ghi cấp chứng chỉ an toàn cho nhân sự kèm ngày hết hạn.
  - Asset: Thiết bị/Tài sản nghiên cứu vật lý được gắn mã định danh duy nhất.
  - Đề tài nghiên cứu (Research Project): Nhiệm vụ khoa học được cấp ngân sách, do một Chủ nhiệm đề tài (PI) điều hành tại một phòng Lab xác định, là căn cứ xét duyệt cho các phiếu mượn thiết bị dài hạn trên 48 giờ.
  - Nhà cung cấp (Supplier): Đơn vị phân phối hoặc bảo hành thiết bị vật lý cho phòng thí nghiệm.
  - Vòng đời trạng thái Phiếu mượn (asset_loan.status):
    + Tạo phiếu thành công (Pending): Phiếu mượn vượt qua toàn bộ ràng buộc kiểm tra đầu vào, được lưu vào hệ thống nhưng chưa có hiệu lực bàn giao thiết bị (approved_by_pi là NULL, thiết bị vẫn ở trạng thái Available).
    + Mượn thành công (Active): Phiếu mượn đã được Quản lý Lab hoặc PI phê duyệt, thiết bị chính thức chuyển sang trạng thái In Use.
    + Mượn quá hạn (Overdue): Phiếu mượn đang ở trạng thái Active nhưng đã vượt quá thời điểm due_date mà chưa ghi nhận ngày trả (return_date là NULL).
    + Trả thiết bị thành công (Returned): Thiết bị đã được hoàn trả nguyên vẹn, hệ thống ghi nhận return_date và tự động phục hồi trạng thái thiết bị về Available.
  - Hoàn tất bảo trì (Completed): Trạng thái xác nhận kỹ thuật viên đã xử lý xong sự cố, cập nhật resolved_date và chi phí bảo trì, cho phép thiết bị quay lại trạng thái Available khi không còn phiếu bảo trì mở nào khác.

