"""
Comprehensive Unit & Integration Tests for Academic Examination Information Management System.
Tests:
1. Database Schema & Uniqueness Rule: (program_type, examination_year, part, semester)
2. Year Separation: Honours Part 1 (2024) vs Honours Part 1 (2025) remain distinct
3. Professional dependent semesters: Part 1 (Semesters 1, 2), Part 2 (Semesters 3, 4), etc.
4. Separate probable vs actual result dates
5. Grounding & Anti-Hallucination in academic_exam_service.py
6. Public API Endpoints (/api/v1/academic-exams/programs, /lookup, list)
"""

import unittest
from db.sql_store import get_sql_store
from backend.services.academic_exam_service import process_academic_exam_query, format_exam_card_markdown
from backend.services.academic_static_service import get_academic_static_response

class TestAcademicExaminationSystem(unittest.TestCase):
    def setUp(self):
        self.store = get_sql_store()

    def test_uniqueness_and_distinct_years(self):


        """
        Verify Honours Part 1 for 2024 and Honours Part 1 for 2025 remain separate records.
        """
        record_2024 = {
            "program_type": "Honours",
            "examination_year": "2024",
            "part": "Part 1",
            "semester": "N/A",
            "exam_date": "15 May 2024",
            "probable_result_date": "15 August 2024",
            "actual_result_date": "10 August 2024",
            "results_published": "Yes"
        }
        record_2025 = {
            "program_type": "Honours",
            "examination_year": "2025",
            "part": "Part 1",
            "semester": "N/A",
            "exam_date": "20 June 2025",
            "probable_result_date": "25 September 2025",
            "actual_result_date": "",
            "results_published": "No"
        }

        res1 = self.store.upsert_academic_exam_info(record_2024, user_name="Admin")
        res2 = self.store.upsert_academic_exam_info(record_2025, user_name="Admin")

        self.assertIsNotNone(res1)
        self.assertIsNotNone(res2)
        self.assertNotEqual(res1["id"], res2["id"])

        # Fetch 2024
        fetched_2024 = self.store.lookup_academic_exam_info(
            program_type="Honours",
            examination_year="2024",
            part="Part 1"
        )
        self.assertIsNotNone(fetched_2024)
        self.assertEqual(fetched_2024[0]["exam_date"], "15 May 2024")
        self.assertEqual(fetched_2024[0]["actual_result_date"], "10 August 2024")
        self.assertEqual(fetched_2024[0]["results_published"], "Yes")

        # Fetch 2025
        fetched_2025 = self.store.lookup_academic_exam_info(
            program_type="Honours",
            examination_year="2025",
            part="Part 1"
        )
        self.assertIsNotNone(fetched_2025)
        self.assertEqual(fetched_2025[0]["exam_date"], "20 June 2025")
        self.assertEqual(fetched_2025[0]["results_published"], "No")

    def test_update_existing_record_without_duplication(self):
        """
        Editing an existing (program_type, examination_year, part, semester) updates that record.
        """
        initial = {
            "program_type": "Degree Pass",
            "examination_year": "2024",
            "part": "Part 2",
            "semester": "N/A",
            "exam_date": "01 July 2024",
            "probable_result_date": "01 October 2024"
        }
        res_init = self.store.upsert_academic_exam_info(initial, user_name="Admin")
        rec_id = res_init["id"]

        # Update record
        updated = {
            "program_type": "Degree Pass",
            "examination_year": "2024",
            "part": "Part 2",
            "semester": "N/A",
            "exam_date": "05 July 2024",
            "probable_result_date": "10 October 2024",
            "actual_result_date": "08 October 2024",
            "results_published": "Yes"
        }
        res_upd = self.store.upsert_academic_exam_info(updated, user_name="Admin")
        self.assertEqual(res_upd["id"], rec_id)

        # Lookup
        lookup = self.store.get_academic_exam_info_by_id(rec_id)
        self.assertEqual(lookup["exam_date"], "05 July 2024")
        self.assertEqual(lookup["actual_result_date"], "08 October 2024")

    def test_professional_dependent_semesters(self):
        """
        Verify Professional course handles Part 1 -> Semester 1 & Semester 2 distinctly.
        """
        sem1 = {
            "program_type": "Professional",
            "examination_year": "2024",
            "part": "Part 1",
            "semester": "Semester 1",
            "exam_date": "10 March 2024"
        }
        sem2 = {
            "program_type": "Professional",
            "examination_year": "2024",
            "part": "Part 1",
            "semester": "Semester 2",
            "exam_date": "10 September 2024"
        }
        s1_res = self.store.upsert_academic_exam_info(sem1, user_name="Admin")
        s2_res = self.store.upsert_academic_exam_info(sem2, user_name="Admin")
        self.assertNotEqual(s1_res["id"], s2_res["id"])

        lookup_s1 = self.store.lookup_academic_exam_info(
            program_type="Professional",
            examination_year="2024",
            part="Part 1",
            semester="Semester 1"
        )
        self.assertEqual(lookup_s1[0]["exam_date"], "10 March 2024")

        lookup_s2 = self.store.lookup_academic_exam_info(
            program_type="Professional",
            examination_year="2024",
            part="Part 1",
            semester="Semester 2"
        )
        self.assertEqual(lookup_s2[0]["exam_date"], "10 September 2024")

    def test_academic_exam_query_grounding(self):
        """
        Verify process_academic_exam_query grounds answers strictly in SQLite records.
        """
        chat_resp = process_academic_exam_query("অনার্স ১ম বর্ষের পরীক্ষা কবে?")
        self.assertIsNotNone(chat_resp)
        self.assertIn("অনার্স", chat_resp.reply)
        self.assertIn("১ম বর্ষ", chat_resp.reply)
        self.assertGreater(len(chat_resp.citations), 0)

    def test_empty_fields_render_neutral_text(self):
        """
        Empty fields must render 'তথ্য এখনো প্রকাশ করা হয়নি।'
        """
        partial_record = {
            "program_type": "Honours",
            "examination_year": "2026",
            "part": "Part 3",
            "semester": "N/A",
            "exam_date": "12 December 2026",
            "probable_result_date": "",
            "actual_result_date": ""
        }
        markdown = format_exam_card_markdown(partial_record)
        self.assertIn("12 December 2026", markdown)
        self.assertIn("তথ্য এখনো প্রকাশ করা হয়নি।", markdown)

    def test_public_api_endpoints(self):
        """
        Test public endpoints for available programs, lookup, and listing directly.
        """
        from backend.api.academic_exam_routes import get_available_programs, lookup_academic_exam, list_academic_exams
        
        # Test programs
        prog_res = get_available_programs()
        self.assertEqual(prog_res["status"], "success")
        self.assertGreater(len(prog_res["programs"]), 0)

        # Test lookup
        lookup_res = lookup_academic_exam(
            program_type="Honours",
            examination_year="2024",
            part="Part 1"
        )
        self.assertEqual(lookup_res["status"], "success")
        self.assertIn("markdown_card", lookup_res)
        self.assertEqual(lookup_res["record"]["exam_date"], "15 May 2024")

        # Test list
        list_res = list_academic_exams(program_type="Honours", limit=10, offset=0)
        self.assertEqual(list_res["status"], "success")
        self.assertGreater(list_res["total"], 0)

    def test_legacy_service_compatibility(self):
        """
        Verify get_academic_static_response remains fully functional.
        """
        resp = get_academic_static_response("অনার্স পরীক্ষা বিষয়ক তথ্য")
        self.assertIsNotNone(resp)
        self.assertIn("অনার্স", resp.reply)

    def test_interactive_cards_flow(self):
        """
        Verify 2-step interactive card flow:
        1. General category click returns 4 small modern vertical cards for Honours Part 1, 2, 3, 4.
        2. Clicking a card returns database answer formatted in small modern vertical cards.
        """
        resp_gen = process_academic_exam_query("অনার্স পরীক্ষা বিষয়ক তথ্য")
        self.assertIn("অনার্স ১ম বর্ষ পরীক্ষা বিষয়ক তথ্য", resp_gen.reply)
        self.assertIn("অনার্স ২য় বর্ষ পরীক্ষা বিষয়ক তথ্য", resp_gen.reply)
        self.assertIn("অনার্স ৩য় বর্ষ পরীক্ষা বিষয়ক তথ্য", resp_gen.reply)
        self.assertIn("অনার্স ৪থ বর্ষ পরীক্ষা বিষয়ক তথ্য", resp_gen.reply)

        resp_p1 = process_academic_exam_query("অনার্স ১ম বর্ষ পরীক্ষা বিষয়ক তথ্য")
        self.assertIn("অনার্স", resp_p1.reply)
        self.assertIn("১ম বর্ষ", resp_p1.reply)
        self.assertIn("ইনকোর্স ও ফরম পূরণ", resp_p1.reply)
        self.assertIn("পরীক্ষা ও রুটিনের সময়সূচি", resp_p1.reply)
        self.assertIn("ফলাফল ও পুনর্নিরীক্ষণ", resp_p1.reply)

        resp_p4 = process_academic_exam_query("অনার্স ৪থ বর্ষ পরীক্ষা বিষয়ক তথ্য")
        self.assertIn("অনার্স", resp_p4.reply)
        self.assertIn("৪র্থ বর্ষ", resp_p4.reply)

if __name__ == "__main__":
    unittest.main()


