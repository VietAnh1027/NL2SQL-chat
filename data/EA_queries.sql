-- 1. Bảng Khoa/Viện (Department)
CREATE TABLE Department (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    building VARCHAR(50),
    foundation_year INT
);

-- 2. Bảng Giảng viên (Professor)
CREATE TABLE Professor (
    professor_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    salary DECIMAL(10, 2),
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
);

-- 3. Bảng Sinh viên (Student)
CREATE TABLE Student (
    student_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    date_of_birth DATE,
    enrollment_year INT,
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
);

-- 4. Bảng Môn học (Course)
CREATE TABLE Course (
    course_id INT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE,
    course_name VARCHAR(100) NOT NULL,
    credits INT,
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
);

-- 5. Bảng Học kỳ (Semester)
CREATE TABLE Semester (
    semester_id INT PRIMARY KEY,
    semester_code VARCHAR(20) UNIQUE, -- Vd: 'FALL2023', 'SPRING2024'
    start_date DATE,
    end_date DATE
);

-- 6. Bảng Phòng học (Classroom)
CREATE TABLE Classroom (
    classroom_id INT PRIMARY KEY,
    building VARCHAR(50),
    room_number VARCHAR(20),
    capacity INT -- Sức chứa của phòng
);

-- 7. Bảng Lớp học phần (Class_Section)
-- Thể hiện việc một môn học được mở vào học kỳ nào, ai dạy, ở phòng nào.
CREATE TABLE Class_Section (
    section_id INT PRIMARY KEY,
    course_id INT,
    professor_id INT,
    semester_id INT,
    classroom_id INT,
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (professor_id) REFERENCES Professor(professor_id),
    FOREIGN KEY (semester_id) REFERENCES Semester(semester_id),
    FOREIGN KEY (classroom_id) REFERENCES Classroom(classroom_id)
);

-- 8. Bảng Đăng ký học/Bảng điểm (Enrollment)
-- Nơi lưu trữ sinh viên học lớp nào và điểm số bao nhiêu.
CREATE TABLE Enrollment (
    enrollment_id INT PRIMARY KEY,
    student_id INT,
    section_id INT,
    final_grade DECIMAL(4, 2), -- Điểm tổng kết (vd: 8.50, 9.75)
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (section_id) REFERENCES Class_Section(section_id)
);

-- 9. Bảng Danh mục Học bổng (Scholarship)
CREATE TABLE Scholarship (
    scholarship_id INT PRIMARY KEY,
    scholarship_name VARCHAR(100),
    amount DECIMAL(10, 2), -- Số tiền học bổng
    sponsor_name VARCHAR(100) -- Đơn vị tài trợ
);

-- 10. Bảng Sinh viên nhận học bổng (Student_Scholarship)
CREATE TABLE Student_Scholarship (
    award_id INT PRIMARY KEY,
    student_id INT,
    scholarship_id INT,
    award_date DATE,
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (scholarship_id) REFERENCES Scholarship(scholarship_id)
);