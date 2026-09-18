#!/usr/bin/env python3
import os
import re

# Complete Chapter Title Mapping for Śrīmad Devī Bhāgavatam
CHAPTER_TITLES = {
    (1, 1): "On the questions by Śaunaka and others",
    (1, 2): "On questions put by Śaunaka and other Rsis",
    (1, 3): "On praising the Purāṇas and on each Vyāsa of every Dvāpara Yuga",
    (1, 4): "On the excellency of the Devī",
    (1, 5): "On the narrative of Hayagrīva",
    (1, 6): "On the preparation for war by Madhu Kaiṭabha",
    (1, 7): "On the praise of the Devī",
    (1, 8): "On deciding who is to be worshipped",
    (1, 9): "On the killing of Madhu Kaiṭabha",
    (1, 10): "On Śiva’s granting boons",
    (1, 11): "On the birth of Budha",
    (1, 12): "On the birth of Pururavā",
    (1, 13): "On Urvaśī and Pururavā",
    (1, 14): "On the birth of Śūka Deva and on the duties of householders",
    (1, 15): "On the dispassion of Śūka and the instructions of Bhagavatī to Hari",
    (1, 16): "On Śūka’s desiring to go to Mithilā to see Janaka",
    (1, 17): "On Śūka’s displaying his self-control amidst the women of the palace of Miṭhilā",
    (1, 18): "On Janaka’s giving instructions on truth to Śūka Deva",
    (1, 19): "On the description of the marriage of Śūka",
    (1, 20): "On Vyāsa doing his duties",

    (2, 1): "On the birth of Matsyagandhā",
    (2, 2): "On the birth of Vyāsa Deva",
    (2, 3): "On the description of the curse on Gaṅgā, Mahābhiṣa and Vasus",
    (2, 4): "On the birth of the Vasus",
    (2, 5): "On the marriage of Satyavatī",
    (2, 6): "On the birth of the Pāṇḍavas",
    (2, 7): "On shewing the departed ones",
    (2, 8): "On the extinction of the family of Yadu and on the anecdote of Parīkṣit",
    (2, 9): "On the account of Ruru",
    (2, 10): "On the death of king Parīkṣit",
    (2, 11): "On the Sarpa Yajña",
    (2, 12): "On the birth of Āstika",

    (3, 1): "On the questions put by Janamejaya",
    (3, 2): "On Rudras going towards the heavens on the celestial car",
    (3, 3): "On seeing the Devī",
    (3, 4): "On the hymns to the Great Devī by Viṣṇu",
    (3, 5): "On the chanting of hymns by Hara and Brahmā",
    (3, 6): "On the description of the Devī’s Vibhutis (powers)",
    (3, 7): "On the creation and the Tattvas and their presiding deities",
    (3, 8): "On the Guṇas and their forms",
    (3, 9): "On the characteristics of the Guṇas",
    (3, 10): "On the story of Satyavrata",
    (3, 11): "On the merits of the Devī in the story of Satyavrata",
    (3, 12): "On the Ambā Yajña rules",
    (3, 13): "On the Devī Yajña by Śrī Viṣṇu",
    (3, 14): "On the narration of the glories of the Devī",
    (3, 15): "On the battle between Yudhājit and Vīrasena",
    (3, 16): "On the glory of the Devī",
    (3, 17): "On the story of Viśvāmitra",
    (3, 18): "The Svayambara of Śaśikalā",
    (3, 19): "On the going to the Svayamvara assembly of Sudarśana",
    (3, 20): "On the Svayamvara hall and the kings conversation there",
    (3, 21): "On the king of Benares fulfilling the advice of his daughter",
    (3, 22): "On Sudarśana’s marriage",
    (3, 23): "On the killing of the enemy of Sudarśana in the great war",
    (3, 24): "On the installation of Durgā Devī in the city of Benares",
    (3, 25): "On the installation of the Devī in Ayodhyā and Benares",
    (3, 26): "On the narration of what are to be done in the Navarātri",
    (3, 27): "On the virgins fit to be worshipped and the Glory of the Devī",
    (3, 28): "On the incidents connected with Navarātri",
    (3, 29): "On the stealing of Sītā and the sorrows of Rāma",
    (3, 30): "On the narration of the Navarātra ceremony by Nārada and the performance of that by Rāma Chandra",

    (4, 1): "On the questions put by Janamejaya regarding Kṛṣṇa’s incarnation",
    (4, 2): "On the supremacy of the effects of Karma",
    (4, 3): "On the former curse of Vasudeva and Devakī",
    (4, 4): "On Adharma",
    (4, 5): "On the dialogues of Nara Nārāyaṇa",
    (4, 6): "On the origin of Urvaśī",
    (4, 7): "On Ahamkāra",
    (4, 8): "On going to the Tīrthas",
    (4, 9): "On the fight between the Riṣis and Prahlāda",
    (4, 10): "On the curse on Viṣṇu by Bhṛgu",
    (4, 11): "On Śukrā’s going to Mahādeva to get the Mantra",
    (4, 12): "On Bhṛgu’s curse and the dialogue between Śukrācārya and the Daityas",
    (4, 13): "On cheating the Daityas",
    (4, 14): "On the Daityas getting back their Śukrācārya",
    (4, 15): "On the truce between the Daityas and the Devas",
    (4, 16): "On the Birth of the several Avatāras of Viṣṇu and their deeds",
    (4, 17): "On the questions asked by Janamejaya",
    (4, 18): "On the Devī Earth’s going to the Heavens",
    (4, 19): "On chanting the hymns to the Devī",
    (4, 20): "On Devakī’s marriage",
    (4, 21): "On the killing of the sons of Devakī",
    (4, 22): "On the Part Incarnations of the Several Devas",
    (4, 23): "On the birth of Śrī Kṛṣṇa",
    (4, 24): "On the stealing away of Pradyūmna",
    (4, 25): "On the Devī’s Highest Supremacy",

    (5, 1): "On the superiority of Rudra over Viṣṇu",
    (5, 2): "On the birth of Dānava Mahiṣa",
    (5, 3): "On the Daitya armies getting ready",
    (5, 4): "On the war counsels given by Indra",
    (5, 5): "On the defeat of the Dānava forces of Mahiṣa",
    (5, 6): "On the Deva Dānava fight",
    (5, 7): "On the going of the Devas to Kailāsa",
    (5, 8): "On the description of the origin and the form of the Devī",
    (5, 9): "On the worship by the gods to the Devī",
    (5, 10): "On the messenger’s news to Mahiṣa",
    (5, 11): "On the appearing of the Dānava Tāmra before the Devī",
    (5, 12): "On the holding of counsel by Mahiṣāsura",
    (5, 13): "On the killing of Vāskala and Durmukha",
    (5, 14): "On the killing of Tāmra and Cikṣura",
    (5, 15): "On the slaying of Viḍālākṣa and Asilomā",
    (5, 16): "On the conversation between the Devī and Mahiṣāsura",
    (5, 17): "On Mandodarī’s accounts",
    (5, 18): "On the killing of the Dānava Mahiṣāsura",
    (5, 19): "On the prayer and hymns to the Devī",
    (5, 20): "On the peace of the world",
    (5, 21): "On the conquest of the Heavens by Śumbha and Niśumbha",
    (5, 22): "On the eulogising of the Devī by the Devas",
    (5, 23): "On the prowess of Kauśikī",
    (5, 24): "On the description and Dhūmralocana giving the news",
    (5, 25): "On the killing of Dhūmralocana",
    (5, 26): "On the killing of Caṇḍa and Muṇḍa",
    (5, 27): "On the description of the war of Raktabīja",
    (5, 28): "On the description of the fighting of the goddesses",
    (5, 29): "On the killing of Raktabīja",
    (5, 30): "On the killing of Niśumbha",
    (5, 31): "On the death of Śumbha",
    (5, 32): "On the King Suratha’s going to the forest",
    (5, 33): "On the description of the greatness of the Devī",
    (5, 34): "On the methods of the worship of the Devī",
    (5, 35): "On the receiving of the boons by the King Suratha and the Vaiśya Samādhi",

    (6, 1): "On Triśirā’s austerities",
    (6, 2): "On the birth of Vṛtrāsura",
    (6, 3): "On the Deva defeat and on Vṛtra’s tapasyā",
    (6, 4): "On the defeat of the Devas by Vṛtra",
    (6, 5): "On praising the Devī",
    (6, 6): "On the slaying of Vṛtrāsura",
    (6, 7): "On Indra’s living under disguise in the Mānas Lake",
    (6, 8): "On Śacī’s praising the Devī",
    (6, 9): "On Indra’s getting the fruits of Brahmahattyā and on the downfall of king Nahuṣa",
    (6, 10): "On the phase of Karma",
    (6, 11): "On the ascertainment of Dharma",
    (6, 12): "On the cause of the war between Ādi and Baka",
    (6, 13): "On the description of the battle between Ādi and Baka after the discourse on Śunahśepha",
    (6, 14): "On the birth of Vaśiṣṭha from Mitrā Varuṇa",
    (6, 15): "On the Nimi’s getting of another body and the beginning of the story of Haihayas",
    (6, 16): "On the incidents preliminary to the Haihaya and Bhārgava affairs",
    (6, 17): "On the continuance of the family of Bhṛgu",
    (6, 18): "On the origin of the Haihaya Dynasty",
    (6, 19): "On the origin of Haihayas from a mare",
    (6, 20): "On the son born of mare by Hari",
    (6, 21): "On the installation of Ekavīra and the birth of Ekāvalī",
    (6, 22): "On the narration to Haihaya the stealing away of Ekāvalī",
    (6, 23): "On the battle of Haihaya and Kālaketu",
    (6, 24): "On the description of Vikṣepa Śakti",
    (6, 25): "On the cause of Moha of Vyāsa Deva asked before Nārada",
    (6, 26): "On the description by Nārada of his own Moha",
    (6, 27): "On the marriage of Nārada and his face getting transformed into that of a monkey",
    (6, 28): "On Nārada’s getting the feminine form",
    (6, 29): "On the Nārada’s getting again his male form",
    (6, 30): "On the glory of Mahā Māyā",
    (6, 31): "On the glory of Māyā",

    (7, 1): "On the Solar and Lunar Kings",
    (7, 2): "On the piercing of the eyes of Cyavana Muni",
    (7, 3): "On the bestowing of the daughter of the King Śaryāti to Cyavana Muni",
    (7, 4): "On the conversation between the two Aśvins and the Princess Sukanyā",
    (7, 5): "On the getting of youth by Cyavana Muni",
    (7, 6): "On granting the Aśvins the right to drink the Soma juice",
    (7, 7): "On the twin Aśvins drinking the Soma Cup",
    (7, 8): "On the King Revata and the Solar Dynasty",
    (7, 9): "On the story of Kākutstha and the origin of Māndhātā",
    (7, 10): "On the story of Satyavrata",
    (7, 11): "On the story of Triśaṅku",
    (7, 12): "On the description of Vaśiṣṭha’s curse on Triśaṅku",
    (7, 13): "On the coming of Viśvāmitra to Triśaṅku",
    (7, 14): "On the going to Heavens of Triśaṅku and the commencement of Hariścandra’s narrative",
    (7, 15): "On the story of the King Hariścandra",
    (7, 16): "On the story of Śunahśepha",
    (7, 17): "On the freeing of Śunahśepha and the curing of Hariścandra",
    (7, 18): "On the origin of the quarrel between Hariścandra and Viśvāmitra",
    (7, 19): "On the taking away of Hariścandra’s Kingdom",
    (7, 20): "On the earnestness of Hariścandra to pay off the Dakṣiṇā",
    (7, 21): "On the description of the sorrows of Hariścandra",
    (7, 22): "On the selling of Hariścandra’s wife",
    (7, 23): "On the King Hariścandra’s acknowledging of the slavery of the Cāṇḍāla",
    (7, 24): "On the stay of Hariścandra in the burning ground",
    (7, 25): "On the quarrels between Hariścandra and Viśvāmitra",
    (7, 26): "On the narration of the sorrows of Hariścandra",
    (7, 27): "On the going of Hariścandra to the Heavens",
    (7, 28): "On the glory of the Śatakṣi Devī",
    (7, 29): "On the birth of the Bhagavatī in the house of Dakṣa",
    (7, 30): "On the birth of Gaurī, the seats of the Deity, and the distraction of Śiva",
    (7, 31): "On the Birth of Pārvatī in the House of Himālayās",
    (7, 32): "On Self-realization, Spoken by the World Mother",
    (7, 33): "On the Devī’s Viraṭ Rūpa",
    (7, 34): "On the Knowledge and Final Emancipation",
    (7, 35): "On the Yoga and Mantra Siddhi",
    (7, 36): "On the Highest Knowledge of Brahmā",
    (7, 37): "On Bhakti Yoga",
    (7, 38): "The Vows and the Sacred Places of the Devī",
    (7, 39): "The Worship of the World Mother",
    (7, 40): "The External Worship of the Devī",

    (8, 1): "On the description of the worlds",
    (8, 2): "On the uplifting of the Earth by the Sacrificial Boar",
    (8, 3): "On the description of the family of Manu",
    (8, 4): "On the narration of the family of Priyavrata",
    (8, 5): "On the description of the receptacle of beings and on the mountains and on the origin of rivers",
    (8, 6): "On the rivers and the mountains Sumeru and others",
    (8, 7): "On the Ganges and the Varṣas",
    (8, 8): "On the description of Ilāvrita",
    (8, 9): "On the narration of the division of the continents",
    (8, 10): "On the description of Bhuvanakoṣa",
    (8, 11): "On the description of the continents and of Bhāratavarṣa",
    (8, 12): "On the narration of Plakṣa, Śālmala and Kuśa Dvīpas",
    (8, 13): "On the description of the remaining Dvīpas",
    (8, 14): "On the description of the Lokāloka space",
    (8, 15): "On the motion of the Sun",
    (8, 16): "On the motion of the planets",
    (8, 17): "On the Dhruva Maṇḍalam",
    (8, 18): "On the narrative of Rāhu Maṇḍalam",
    (8, 19): "On the narrative of the Atala, etc.",
    (8, 20): "On the narrative of the Talātala",
    (8, 21): "On the narrative of hells",
    (8, 22): "On the narrative of the sins leading to hells",
    (8, 23): "On the description of the remaining hells",
    (8, 24): "On the worship of the Devī",

    (9, 1): "On the description of Prakṛti",
    (9, 2): "On the origin of Prakṛti and Puruṣa",
    (9, 3): "On the origin of Brahmā, Viṣṇu, Maheśa and others",
    (9, 4): "On the hymn, worship and Kavaca of Sarasvatī Devī",
    (9, 5): "On Sarasvatī stotra by Yājñavalkya",
    (9, 6): "On the coming in this world of Lakṣmī, Gaṅgā and Sarasvatī",
    (9, 7): "On the curses of Gaṅgā, Sarasvatī and Lakṣmī",
    (9, 8): "On the greatness of Kali",
    (9, 9): "On the origin of the Śakti of the Earth",
    (9, 10): "On the offences caused to the Earth and punishments thereof",
    (9, 11): "On the origin of the Ganges",
    (9, 12): "On the origin of Gaṅgā",
    (9, 13): "On the anecdote of Gaṅgā",
    (9, 14): "On the story of Gaṅgā becoming the wife of Nārāyaṇa",
    (9, 15): "On the anecdote of Tulasī",
    (9, 16): "On the incarnation of Mahā Lakṣmī in the house of Kuśadhvaja",
    (9, 17): "On the anecdote of Tulasī",
    (9, 18): "On the union of Śaṅkhacūḍa with Tulasī",
    (9, 19): "On the going of the Devas to Vaikuṇṭha after Tulasī’s marriage with Śaṅkhacūḍa",
    (9, 20): "On the war preparations of Śaṅkhacūḍa with the Devas",
    (9, 21): "On the meeting of Mahādeva and Śaṅkhacūḍa for an encounter in conflict",
    (9, 22): "On the fight between the Devas and Śaṅkhacūḍa",
    (9, 23): "On the killing of Śaṅkhacūḍa",
    (9, 24): "On the glory of Tulasī",
    (9, 25): "On the method of worship of Tulasī Devī",
    (9, 26): "On the narration of Sāvitrī",
    (9, 27): "On the birth, etc., of Sāvitrī",
    (9, 28): "On the story of Sāvitrī",
    (9, 29): "On the anecdote of Sāvitrī, on gifts and on the effects of Karmas",
    (9, 30): "On the conversation between Sāvitrī and Yama and on the fruition of Karmas",
    (9, 31): "On the Yama's giving Śakti Mantra to Sāvitrī",
    (9, 32): "On the enumeration of various hells for sinners",
    (9, 33): "On the description of the destinies of different sinners in different hells",
    (9, 34): "On the description of the various hells",
    (9, 35): "On the description of the various hells for the various sinners",
    (9, 36): "On the destruction of the fear of the Yama of those who are the worshippers of the Five Devatās",
    (9, 37): "On the eighty-six Kuṇḍas and their characteristics",
    (9, 38): "On the glories of the Devī and on the nature of Bhakti",
    (9, 39): "On the story of Mahā Lakṣmī",
    (9, 40): "On the birth of Lakṣmī in the discourse of Nārada and Nārāyaṇa",
    (9, 41): "On the churning of the ocean and on the appearing of Lakṣmī",
    (9, 42): "On the Dhyānam and Stotra of Mahā Lakṣmī",
    (9, 43): "On the history of Svāhā",
    (9, 44): "On the story of Svadhā Devī in the discourse between Nārada and Nārāyaṇa",
    (9, 45): "On the anecdote of Dakṣiṇā",
    (9, 46): "On the anecdote of Ṣaṣṭhī Devī",
    (9, 47): "On Manasā’s story",
    (9, 48): "On the anecdote of Manasā",
    (9, 49): "On the anecdote of Surabhi",
    (9, 50): "On the Glory of Śakti",

    (10, 1): "On the story of Svāyambhuva Manu",
    (10, 2): "On the conversation between Nārada and the Bindhya Mountain",
    (10, 3): "On the obstruction of the Sun’s course by the Bindhya Mountain",
    (10, 4): "On the Devas going to Mahā Deva",
    (10, 5): "On the Devas going to Viṣṇu",
    (10, 6): "On the Devas praying to the Muni Agastya",
    (10, 7): "On the checking of the rise of the Bindhya Range",
    (10, 8): "On the origin of Manu",
    (10, 9): "On the narrative of Cākṣuṣa Manu",
    (10, 10): "On the anecdote of the King Suratha",
    (10, 11): "On the killing of Madhu Kaiṭabha",
    (10, 12): "On the anecdote of Sāvarṇi Manu",
    (10, 13): "On the account of Bhrāmarī Devī",

    (11, 1): "On what is to be thought of in the morning",
    (11, 2): "On cleansing the several parts of the body",
    (11, 3): "On the glories of the Rudrākṣa beads",
    (11, 4): "On the greatness of the Rudrākṣam",
    (11, 5): "On the Rudrākṣam rosaries",
    (11, 6): "On the greatness of Rudrākṣams",
    (11, 7): "On the greatness of one faced, etc., Rudrākṣam",
    (11, 8): "On Bhūta Śuddhi",
    (11, 9): "On the rules of Śirovrata",
    (11, 10): "On the subject of Gauṇa Bhasma",
    (11, 11): "On the description of the greatness of the three kinds of Bhaṣmas",
    (11, 12): "On the greatness in holding the Tripuṇḍra and Bhaṣma",
    (11, 13): "On the greatness of Bhasma",
    (11, 14): "On the greatness in holding the Bibhūti",
    (11, 15): "On the rules of using the Tripuṇḍra and Ūrdhapuṇḍra marks",
    (11, 16): "On the description of Sandhyā Upāsānā",
    (11, 17): "On the description of Sandhyā and other daily practices",
    (11, 18): "On the Greatness of the Devī Pūjā",
    (11, 19): "On the midday Sandhyā",
    (11, 20): "On the description of Brahmā Yajñā, Sandhyās, etc.",
    (11, 21): "On Gāyatrī Puraścaraṇam",
    (11, 22): "On the rules of Vaiśvadeva",
    (11, 23): "On the Tapta Kṛcchra vrata and others",
    (11, 24): "On Sadācāra",

    (12, 1): "On the description of Gāyatrī",
    (12, 2): "On the description of the Śaktis, etc., of the syllables of Gāyatrī",
    (12, 3): "On the description of the Kavaca of Śrī Gāyatrī Devī",
    (12, 4): "On Gāyatrī Hridaya",
    (12, 5): "On the Gāyatrī Stotra",
    (12, 6): "On the one thousand and eight names of the Gāyatrī",
    (12, 7): "On the Dīkṣā vidhi or on the rules of Initiation",
    (12, 8): "On the appearance of the Highest Śakti",
    (12, 9): "On the cause of Śrāddha in other Devas than the Devī Gāyatrī",
    (12, 10): "On the description of Maṇi Dvīpa",
    (12, 11): "On the description of the enclosure walls built of Padmarāga maṇi, etc., of the Maṇi Dvīpa",
    (12, 12): "On the description of Maṇi Dvīpa",
    (12, 13): "On the description of Janamejaya’s Devī Yajñā",
    (12, 14): "On the recitation of the fruits of this Purāṇam"
}

FOOTER_HTML = """
        <!-- Site Footer -->
        <footer class="doc-footer" style="margin-top: 3rem; padding: 1.5rem 0; border-top: 1px solid #e2e8f0; text-align: center; color: #64748b; font-size: 0.9rem;">
            <p><strong>🙏 Shri Krishnarpanam Asthu 🙏</strong> | Maintained &amp; published via <a href="https://ventpipe.blog" target="_blank" rel="noopener noreferrer" style="color: #0284c7; text-decoration: none; font-weight: 500;">ventpipe.blog</a></p>
        </footer>
"""

def patch_html_files(base_dir="."):
    updated_count = 0

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".html"):
                continue

            match = re.search(r"[B|b](\d+)[\/\\][C|c](\d+)", root)
            if not match:
                match = re.search(r"(\d+)[\.-](\d+)", file)
                if not match:
                    continue

            book_num = int(match.group(1))
            chap_num = int(match.group(2))

            key = (book_num, chap_num)
            if key not in CHAPTER_TITLES:
                continue

            title_text = CHAPTER_TITLES[key]
            file_path = os.path.join(root, file)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. Clean update of <title> in <head>
            clean_page_title = f"Book {book_num} • Chapter {chap_num} - {title_text} | Śrīmad Devī Bhāgavatam"
            content = re.sub(
                r"<title.*?>.*?</title>",
                f"<title>{clean_page_title}</title>",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )

            # 2. Safely append <div class="chapter-desc"> inside <div class="chapter-subtitle">
            # Matches: <div class="chapter-subtitle">...ANYTHING...</div>
            subtitle_pattern = r'(<div\s+class=["\']chapter-subtitle["\'].*?>)(.*?)(</div>)'
            
            def replace_subtitle(m):
                opening_div = m.group(1)
                inner_content = m.group(2)
                closing_div = m.group(3)
                
                # Avoid duplicating if already present
                if 'class="chapter-desc"' in inner_content:
                    return m.group(0)
                
                desc_html = f'<div class="chapter-desc" style="font-size: 0.95rem; margin-top: 0.4rem; color: #475569; font-weight: 500; text-transform: none;">{title_text}</div>'
                return f"{opening_div}{inner_content}{desc_html}{closing_div}"

            content = re.sub(subtitle_pattern, replace_subtitle, content, flags=re.IGNORECASE | re.DOTALL)

            # 3. Inject Footer before closing </body>
            if 'class="doc-footer"' not in content:
                if '</body>' in content:
                    content = content.replace('</body>', f'{FOOTER_HTML}\n</body>')
                else:
                    content += FOOTER_HTML

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            updated_count += 1
            print(f"✅ Patched Book {book_num}, Chapter {chap_num}: {file_path}")

    print(f"\n🎉 Successfully updated {updated_count} chapter pages!")


if __name__ == "__main__":
    patch_html_files()
