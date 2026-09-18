import unittest
import re
import os
import tempfile

from process_master import (
    deva_to_int,
    parse_range_label,
    align_ocr_to_wisdom,
    sanitize_layout_pollution,
    validate_input_integrity,
    load_clean_sanskrit,
    extract_linguistic_blocks,
    extract_verse_marker_number,
    determine_verse_header,
    is_colophon_line,
    clean_colophon_text,
    sanitize_sanskrit_text,
    audit_interleaved_file,        # End/Tail Truncation Audit
    audit_check_begin_mismatch,   # Begin/Head Truncation Audit
)
TEST_CLEANUP_RULES = {
    r"Book\s*[I\d]*\s*Chapter\s*[IVXLCDM\d]+\s+\d+": "", 
    r"<\_<": "sweeter",                         
    r"\s+i\b": " ॥",                            
    r"FATT\s+78": "॥ 78",
    r"\bJtis\b": "It is",
    
    # Trim inner spaces so capturing '\1' gets clean digits without extra spaces
    r'[\.।]\s*([०-९\d\-]+(?:\s+[०-९\d\-]+)*)\s*[\.।]\s*$': r'॥ \1 ॥',
}
          
def apply_test_cleanup(text):
    for pattern, replacement in TEST_CLEANUP_RULES.items():
        text = re.sub(pattern, replacement, text)
    return text.strip()


class TestOCRAlignmentPipeline(unittest.TestCase):

    def test_sanitize_sanskrit_text_removes_headers_and_page_numbers(self):
        """
        Test that Book/Chapter headers and standalone page numbers inside Sanskrit
        text blocks are properly stripped out.
        """
        dirty_sanskrit = (
            "राजान कबुः\n"
            "बाला एव वर्ण प्राप्तस्ते तु नृनं भयातुः ।\n"
            "कर्थे ज्ञाता त्वया देवी परम शक्तिक्तनाम ॥ ४० ॥\n"
            "Book III Chapter XXV\n"
            "41\n"
            "उपासिता कर्थ चैव पूजिता च कर्थ नृप ।\n"
            "या प्रसरा तु साहाय्ये चकार त्वयाचिता ॥ 4 1 ॥"
        )

        expected_clean = (
            "राजान कबुः\n"
            "बाला एव वर्ण प्राप्तस्ते तु नृनं भयातुः ।\n"
            "कर्थे ज्ञाता त्वया देवी परम शक्तिक्तनाम ॥ ४० ॥\n"
            "उपासिता कर्थ चैव पूजिता च कर्थ नृप ।\n"
            "या प्रसरा तु साहाय्ये चकार त्वयाचिता ॥ 4 1 ॥"
        )

        cleaned_sanskrit = sanitize_sanskrit_text(dirty_sanskrit)

        self.assertNotIn("Book III Chapter XXV", cleaned_sanskrit)
        self.assertNotIn("\n41\n", cleaned_sanskrit)
        self.assertEqual(cleaned_sanskrit, expected_clean)

    def test_clean_colophon_text_fixes_ocr_corruptions(self):
        """
        Test that corrupted colophon patterns like 'श्वरोउध्याः' and 'द्वितीयकन्धे'
        are properly normalized by clean_colophon_text.
        """
        raw_colophon = "श्रित श्रीमदेवीभगवते महापुराणे द्वितीयकन्धे\nश्वरोउध्याः ॥ ६ ॥"
        
        cleaned = clean_colophon_text(raw_colophon)
        
        self.assertIn("द्वितीयस्कन्धे", cleaned)
        self.assertIn("षष्ठोऽध्यायः ॥ ६ ॥", cleaned)
        self.assertNotIn("श्वरोउध्याः", cleaned)

    def test_corrupted_colophon_line_does_not_break_sequence(self):
        """
        Test that OCR-corrupted end-of-chapter colophons like 'श्वरोउध्याः ॥ ६ ॥'
        are properly identified as colophons and ignored during sequence validation.
        """
        mock_ch6_end = (
            "भीभादयः प्रीतचित्नः पालयामासुर्यतः ॥ ७० ॥\n"
            "श्रित श्रीमदेवीभगवते महापुराणे द्वितीयकन्धे\n"
            "श्वरोउध्याः ॥ ६ ॥\n"
        )
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
            tmp.write(mock_ch6_end)
            tmp_filepath = tmp.name

        try:
            is_valid = validate_input_integrity(tmp_filepath)
            self.assertTrue(is_valid, "Corrupted colophon line incorrectly broke verse sequence validation!")
        finally:
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)

    def test_ignore_colophon_in_verse_sequence(self):
        """
        Test that end-of-chapter colophon markers (even corrupted ones like 'श्वरोउध्याः ॥ ६ ॥')
        are recognized as colophons and do NOT trigger a false verse sequence drop.
        """
        raw_colophon = "श्वरोउध्याः ॥ ६ ॥"
        
        # 1. Assert it is recognized as a colophon
        self.assertTrue(is_colophon_line(raw_colophon))
        
        # 2. Assert it gets normalized correctly
        cleaned = clean_colophon_text(raw_colophon)
        self.assertIn("षष्ठोऽध्यायः ॥ ६ ॥", cleaned)
                
    def test_extract_verse_marker_period_danda_substitution(self):
        """Verify extraction handles single dandas and period-substituted dandas with trailing whitespace."""
        # 1. Single danda with spaces and periods: ' । ४१ । '
        self.assertEqual(extract_verse_marker_number("सिद्धानास्येके कुकश्रेघ कामयानां भजस्य मम् . ४१ ."), "41")
        
        # 2. Mixed single danda and period OCR artifact: ' । 41 .'
        self.assertEqual(extract_verse_marker_number("सा तमाह वरारोहा यदर्थ राजसत्तम् । ४१ ."), "41")

    def test_cleanup_period_dandas_normalization(self):
        """Verify text cleanup normalizes period-delimited verse markers to double dandas."""
        raw_ocr = "सिद्धानास्येके कुकश्रेघ कामयानां भजस्य मम् . ४१ ."
        cleaned = apply_test_cleanup(raw_ocr)
        self.assertIn("॥ ४१ ॥", cleaned)      

    def test_devanagari_numeral_conversion(self):
        self.assertEqual(deva_to_int("३"), 3)
        self.assertEqual(deva_to_int("११"), 11)

    def test_range_label_parsing(self):
        max_verse = 100
        self.assertEqual(parse_range_label("Verse 5-7", max_verse), [5, 6, 7])

    def test_text_normalization_rules(self):
        raw_v3 = "Book  Chapter XI 47 O Sita! Your words are <_< and more full of juice"
        cleaned_v3 = apply_test_cleanup(raw_v3)
        self.assertIn("sweeter", cleaned_v3)

    def test_offset_alignment_engine(self):
        reference_wisdom = "Once on a time the exceedingly beautiful dear wife of Brihaspati, named Tara."
        ocr_input = "Once upon a time the cxccedingly beautiful dear wife of Brhaspati, named 'Tara,"
        aligned_result = align_ocr_to_wisdom(ocr_input, reference_wisdom)
        self.assertIn("beautiful dear wife", aligned_result)

    def test_determine_verse_header(self):
        """Verify dynamic range generation for missing explicit start markers."""
        # Scenario 1: Initial block ends in verse 2 -> Inferred range "1-2"
        self.assertEqual(determine_verse_header(chapter_num=1, current_extracted_num="2", last_processed_verse=0), "1-2")
        
        # Scenario 2: Second block ends in verse 4 -> Inferred range "3-4"
        self.assertEqual(determine_verse_header(chapter_num=1, current_extracted_num="4", last_processed_verse=2), "3-4")
        
        # Scenario 3: Sequential verse 5 -> Single verse label "5"
        self.assertEqual(determine_verse_header(chapter_num=1, current_extracted_num="5", last_processed_verse=4), "5")
        
        # Scenario 4: Existing explicit range marker preserved
        self.assertEqual(determine_verse_header(chapter_num=1, current_extracted_num="5-7", last_processed_verse=4), "5-7")
        
        # Scenario 5: Missing marker (None) -> Fallback increment
        self.assertEqual(determine_verse_header(chapter_num=1, current_extracted_num=None, last_processed_verse=4), "5")

    def test_extract_verse_marker_spaced_digits(self):
        """Verify that OCR-inserted spaces inside verse markers are properly collapsed."""
        self.assertEqual(extract_verse_marker_number("शापस्यांतं कुरु सूत ॥ 4 1 ॥"), "41")
        self.assertEqual(extract_verse_marker_number("मृता मुक्ता च शापतः ॥ 4 5 ॥"), "45")
        self.assertEqual(extract_verse_marker_number("वरवर्णिनी ॥ 4 6 ॥"), "46")
        self.assertEqual(extract_verse_marker_number("प्रभानोउपधा: ॥ 1 1 ॥"), "11")
        self.assertEqual(extract_verse_marker_number("देवो मया दृश्यते ॥ ४ १ ॥"), "41")

    def test_validate_integrity_spaced_verse_markers(self):
        """Ensure input integrity validator tolerates spaced OCR digits without sequence drops."""
        mock_spaced_ocr_content = (
            "अद्विका मुनिना शप्ता मत्स्यी जाता वराप्सराः ॥ 40 ॥\n"
            "शापस्यांतं कुरु सूत कथं स्वर्गमवाप सा ॥ 4 1 ॥\n"
            "दयावान्ब्राह्मणः प्राह तां तदा रुदतीं स्त्रियम् ॥ 42 ॥\n"
            "बालकौ जनयित्वा सा मृता मुक्ता च शापतः ॥ 4 5 ॥\n"
            "जगामामरांगणं च शापान्ते वरवर्णिनी ॥ 4 6 ॥\n"
        )
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
            tmp.write(mock_spaced_ocr_content)
            tmp_path = tmp.name
        try:
            result = validate_input_integrity(tmp_path)
            self.assertTrue(result, "Integrity validation failed on spaced verse markers!")
        finally:
            if os.path.exists(tmp_path): 
                os.remove(tmp_path)

    def test_validate_integrity_with_inline_noise(self):
        mock_corrupted_content = (
            "रहस्यं सर्वशास्त्राणामागमानामनुत्तमम्‌ ॥ 2 ॥\n"
            "एकत्रिंशत्तथा 98 चत्वारिंशच्च सप्तमे ॥ 14 ॥\n"
        )
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
            tmp.write(mock_corrupted_content)
            tmp_path = tmp.name
        try:
            result = validate_input_integrity(tmp_path)
            self.assertTrue(result)
        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)

    def test_jtis_normalization_and_warning_flag(self):
        raw_ocr = "Jtis commonly known that Brahmi is the creator"
        normalized = apply_test_cleanup(raw_ocr)
        self.assertTrue(normalized.startswith("It is"))

    def test_cross_column_layout_pollution_deduplication(self):
        corrupted_ocr_input = (
            "Suta! Fie to the nectar even! as the drinking] Samsara, the constant rounds of births "
            "Suta! Fie to the nectar even! as the drinking of nectar is quite useless in giving Mukti."
        )
        sanitized_ocr = sanitize_layout_pollution(corrupted_ocr_input)
        self.assertLess(len(sanitized_ocr.split("Fie to the")), 3)

    def test_hybrid_numerical_parsing_sanskrit(self):
        mock_sanskrit = (
            "इतिहास इति प्रोक्तं पञ्चमं वेदसंमतम्‌ ॥ 26 ॥\n"
            "कानि तानि पुराणानि ब्रूहि सूत सविस्तरम्‌ ॥ २७ ॥\n"
        )
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
            tmp.write(mock_sanskrit)
            tmp_path = tmp.name
        try:
            verse_dict, _, _ = load_clean_sanskrit(tmp_path)
            self.assertIn(26, verse_dict)
            self.assertIn(27, verse_dict)
        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)

    def test_validate_integrity_ascii_in_sanskrit_warning(self):
        mock_mixed_block = "इतिहास इति प्रोक्तं पञ्चमं वेदसंमतम्‌ ॥ 26 ॥\n"
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
            tmp.write(mock_mixed_block)
            tmp_path = tmp.name
        try:
            result = validate_input_integrity(tmp_path)
            self.assertTrue(result)
        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)

    def test_itihasa_prefix_block_extraction(self):
        """Verify that lines beginning with 'इतिहास' are not accidentally skipped as colophons."""
        mock_data = (
            "समादलक्षणं च तथा भारतं मुनिना कृतम्‌ ।\n"
            "इतिहास इति प्रोक्तं पञ्चमं वेदसंमतम्‌ ॥ 26 ॥\n"
            "So is Mahabharata written by Veda Vyasa...\n"
        )
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
            tmp.write(mock_data)
            tmp_path = tmp.name
        try:
            blocks = extract_linguistic_blocks(tmp_path)
            sanskrit_text = next(text for rtype, text in blocks if rtype == "SANSKRIT")
            self.assertIn("इतिहास", sanskrit_text)
        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)

    def test_boundary_typo_resilience_21_22(self):
        """Ensure character slider successfully captures text up to 'creation).' despite reference typos."""
        wisdom = "is denominated (in this Purāṇa) as Pratisarga (secondary ereation.)"
        ocr = "is denominated (in this Purana) as Pratisarga (secondary creation)."
        res = align_ocr_to_wisdom(ocr, wisdom)
        self.assertTrue(res.endswith("ereation.)"))

    # --- 🔍 AUDIT TRUNCATION TESTS ---
    def test_audit_interleaved_file_flags_head_truncation(self):
        """Verify audit function correctly flags English translations truncated at the beginning."""
        truncated_head_block = (
            "[Ch 1 Verse 1]\n"
            "सूत उवाच ॥\n"
            "English Translation:\n"
            "...ya, the son of Parīkṣit, again asked :--\n"
            "----------------------------------------\n"
        )
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
            tmp.write(truncated_head_block)
            tmp_path = tmp.name

        try:
            # ✅ Call audit_check_begin_mismatch for Head/Begin checks
            issues = audit_check_begin_mismatch(tmp_path)
            self.assertEqual(len(issues), 1)
            self.assertIn("[Ch 1 Verse 1]", issues[0][0])
            self.assertIn("HEAD TRUNCATED", issues[0][1])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # --- 🔍 AUDIT TRUNCATION TESTS ---
    def test_audit_interleaved_file_flags_head_truncation(self):
        """Verify audit function correctly flags English translations truncated at the beginning."""
        truncated_head_block = (
            "[Ch 1 Verse 1]\n"
            "सूत उवाच ॥\n"
            "English Translation:\n"
            "...ya, the son of Parīkṣit, again asked :--\n"
            "----------------------------------------\n"
        )
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
            tmp.write(truncated_head_block)
            tmp_path = tmp.name

        try:
            # ✅ Call audit_check_begin_mismatch for Head/Begin checks
            issues = audit_check_begin_mismatch(tmp_path)
            self.assertEqual(len(issues), 1)
            self.assertIn("[Ch 1 Verse 1]", issues[0][0])
            self.assertIn("HEAD TRUNCATED", issues[0][1])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestVerseRegressionMatrix(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.wisdom_source = (
            "1-86. The Ṛṣis said :-- “O Sūta! Who is that King Pururavā? and who is the Deva girl Urvaśī? "
            "And how did that high-souled King Pururavā come into trouble? "
            "Brihaspati, then, being distressed with the pang of separation from his wife, "
            "sent his pupil to bring back Tārā; but Tārā was then submissive of Candra and therefore refused to come. "
            "It is commonly known that Brahmā is the creator of this universe; and the knowers of the Vedas and the Purāṇas say so; "
            "but they also say that Brahmā is born of the navel-lotus of Viṣṇu. Thus it appears that Brahmā cannot create independently. "
            "Again Viṣṇu, from whose navel lotus Brahmā is born, lies in Yoga sleep on the bed of Ananta (the thousand headed serpent) "
            "in the time of Pralaya; so how can we call Bhagavān Viṣṇu who rests on the thousand headed serpent Ananta as the creator of the universe?"
        )

    def test_verse_01_prefix_suffix_alignment(self):
        ocr = "The Rsis said: O Suta! Who is that King Puriiravi? and who is the Deva girl Urvasi? And how did that high-souled King Purtrava came into trouble?"
        res = align_ocr_to_wisdom(ocr, self.wisdom_source)
        self.assertTrue(res.startswith("The Ṛṣis said"))
        self.assertTrue(res.endswith("come into trouble?"))

    def test_verse_6_7_no_end_truncation(self):
        ocr = (
            "It is commonly known that Brahmi is the creator of this universe; and the knowers of the Vedas and the Puranas say so; "
            "but they also say that Brahma is born of the navel-lotus of Visnu. Thus, it appears that Brahma cannot create independently, "
            "Again, Visnu, from whose navel lotus Brahma is born, lies in Yoga sleep on the bed of Ananta (the thousand-headed serpent) "
            "in the time of Pralaya; so how can we call Bhagavan Visnu who rests on the thousand headed serpent Ananta, as the creator of the universe?"
        )
        res = align_ocr_to_wisdom(sanitize_layout_pollution(ocr), self.wisdom_source)
        self.assertTrue(res.endswith("creator of the universe?"))

    def test_long_colophon_end_preservation(self):
        wisdom_text = (
            "Now describe to us the highly pure Śrīmad Devī Bhāgavatam where all the Lilas "
            "of the Mother of the three worlds purifying the sins, adorned with all the qualifications "
            "are described as yielding all the desires like the Kalpa Vrikṣa (the celestial tree yielding all desires). "
            "Thus ends the second chapter of the first Skandha on the description of the Purāṇa (the text) "
            "in Mahā Purāṇa Śrīmad Devī Bhāgavatam of 18,000 verses by Maharṣi Veda"
        )
        ocr_text = (
            "Now describe to us the highly pure Srimad Devi Bhagavatam where all the Lilas "
            "of the Mother of the three worlds, purifying the sins, adorned with all the qualifications "
            "are described as yielding all the desires like the Kalpa Vrksa (the celestial tree yielding all desires). "
            "Thus ends the Second Chapter of the First Book on the description of the Purana (the text) "
            "in Maha Purana Srimaddevibhagavatam of 18,000 verses by Mahrasi Veda Vyasa."
        )
        res = align_ocr_to_wisdom(ocr_text, wisdom_text)
        self.assertTrue(
            res.endswith("by Maharṣi Veda"), 
            f"End Truncation detected in colophon! Output stopped at: ...{res[-40:]}"
        )

if __name__ == "__main__":
    print("🧪 Executing Consolidated Structural Validation Suite...")
    unittest.main()