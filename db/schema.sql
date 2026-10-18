-- Database Schema for National University AI Knowledge Base & Self-Enrichment Store

CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    pdf_url TEXT,
    category TEXT DEFAULT 'General',
    published_date TEXT,
    content_hash TEXT,
    raw_text TEXT,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admission_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program TEXT NOT NULL,
    level TEXT,
    eligibility TEXT,
    deadline TEXT,
    notes TEXT,
    source_url TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS faq_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source_url TEXT,
    language TEXT DEFAULT 'bn',
    category TEXT DEFAULT 'General',
    confidence REAL DEFAULT 1.0,
    verified_by_admin INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gap_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_query TEXT NOT NULL,
    language TEXT DEFAULT 'bn',
    session_id TEXT,
    reason TEXT,
    status TEXT DEFAULT 'pending', -- pending, researching, candidate_ready, resolved, rejected
    candidate_answer TEXT,
    confidence REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME
);

CREATE TABLE IF NOT EXISTS crawl_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    status TEXT NOT NULL, -- success, partial, failed
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    pages_scraped INTEGER DEFAULT 0,
    new_items INTEGER DEFAULT 0,
    errors TEXT
);

CREATE TABLE IF NOT EXISTS officers_directory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_slug TEXT,
    department_name TEXT,
    department_url TEXT,
    name TEXT NOT NULL,
    designation_bn TEXT,
    designation_en TEXT,
    phone TEXT,
    email TEXT,
    raw_details TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_officer_dept ON officers_directory (department_slug);
CREATE INDEX IF NOT EXISTS idx_officer_name ON officers_directory (name);
CREATE INDEX IF NOT EXISTS idx_officer_desig ON officers_directory (designation_bn, designation_en);


CREATE INDEX IF NOT EXISTS idx_notices_date ON notices(published_date);
CREATE INDEX IF NOT EXISTS idx_faq_question ON faq_entries(question);
CREATE INDEX IF NOT EXISTS idx_gap_status ON gap_queue(status);

-- Many-to-Many Knowledge Base Q&A Tables
CREATE TABLE IF NOT EXISTS qa_knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_question TEXT NOT NULL,
    category TEXT DEFAULT 'General',
    tags TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qa_question_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qa_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qa_id) REFERENCES qa_knowledge_base(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS qa_answer_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qa_id INTEGER NOT NULL,
    answer_text TEXT NOT NULL,
    is_primary INTEGER DEFAULT 0,
    language TEXT DEFAULT 'bn',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qa_id) REFERENCES qa_knowledge_base(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_qa_variants_q ON qa_question_variants(question_text);
CREATE INDEX IF NOT EXISTS idx_qa_category ON qa_knowledge_base(category);

-- Comprehensive Academic Examination & Result Information managed by Admin
CREATE TABLE IF NOT EXISTS academic_exam_information (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_type TEXT NOT NULL, -- 'Honours', 'Degree Pass', 'Master''s', 'Professional'
    program_type_name TEXT NOT NULL DEFAULT '', -- 'অনার্স', 'ডিগ্রি পাস', 'মাস্টার্স', 'প্রফেশনাল'
    course_name TEXT DEFAULT '', -- e.g. 'B.Sc. in Computer Science & Engineering (CSE)', 'BBA', etc.
    examination_year TEXT NOT NULL, -- e.g. '2024', '2025'
    part TEXT NOT NULL DEFAULT 'N/A', -- 'Part 1', 'Part 2', 'Part 3', 'Part 4', 'N/A'
    semester TEXT NOT NULL DEFAULT 'N/A', -- 'Semester 1', 'Semester 2', ..., 'N/A'
    incourse_exam_date TEXT DEFAULT '',
    incourse_marks_deadline TEXT DEFAULT '',
    form_fillup_start_date TEXT DEFAULT '',
    form_fillup_deadline TEXT DEFAULT '',
    exam_date TEXT DEFAULT '',
    routine_publication_date TEXT DEFAULT '',
    admit_card_date TEXT DEFAULT '',
    last_exam_date TEXT DEFAULT '',
    practical_marks_start_date TEXT DEFAULT '',
    practical_marks_deadline TEXT DEFAULT '',
    probable_result_date TEXT DEFAULT '',
    actual_result_date TEXT DEFAULT '',
    results_published TEXT DEFAULT 'No', -- 'Yes' / 'No'
    rescrutiny_start_date TEXT DEFAULT '',
    rescrutiny_deadline TEXT DEFAULT '',
    rescrutiny_result_date TEXT DEFAULT '',
    document_printing_date TEXT DEFAULT '',
    documents_printed TEXT DEFAULT 'No', -- 'Yes' / 'No'
    revaluation_result_url TEXT DEFAULT 'https://results.nu.ac.bd/',
    college_wise_result_url TEXT DEFAULT 'http://103.113.200.68/nu-app/search.php',
    remarks TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'Admin',
    updated_by TEXT DEFAULT 'Admin',
    UNIQUE(program_type, examination_year, part, semester)
);

CREATE INDEX IF NOT EXISTS idx_academic_exam_lookup ON academic_exam_information(program_type, examination_year, part, semester);
CREATE INDEX IF NOT EXISTS idx_academic_exam_prog_part ON academic_exam_information(program_type, part);
CREATE INDEX IF NOT EXISTS idx_academic_exam_year ON academic_exam_information(examination_year);

-- Legacy Table for backwards compatibility
CREATE TABLE IF NOT EXISTS academic_exam_static_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_type TEXT NOT NULL,
    part_or_year TEXT NOT NULL DEFAULT '1',
    exam_year TEXT DEFAULT '',
    incourse_date TEXT DEFAULT '',
    last_date_incourse_marks TEXT DEFAULT '',
    form_fillup_date TEXT DEFAULT '',
    exam_date TEXT DEFAULT '',
    routine_url TEXT DEFAULT '',
    admit_card_date TEXT DEFAULT '',
    last_date_exam TEXT DEFAULT '',
    practical_marks_date TEXT DEFAULT '',
    last_date_practical_marks TEXT DEFAULT '',
    probable_result_date TEXT DEFAULT '',
    result_publish_date TEXT DEFAULT '',
    results_published TEXT DEFAULT 'No',
    rescrutiny_apply_date TEXT DEFAULT '',
    rescrutiny_result_date TEXT DEFAULT '',
    certificate_printing_date TEXT DEFAULT '',
    printed_status TEXT DEFAULT 'No',
    revaluation_result_link TEXT DEFAULT 'https://results.nu.ac.bd/',
    collegewise_result_link TEXT DEFAULT 'http://103.113.200.68/nu-app/search.php',
    notes TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(program_type, part_or_year)
);

CREATE INDEX IF NOT EXISTS idx_academic_static_lookup ON academic_exam_static_info(program_type, part_or_year);
