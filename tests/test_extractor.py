"""
Basic tests for SKOSClient
"""

import unittest
import tempfile
import json
from pathlib import Path
from skosclient import SKOSExtractor


class TestSKOSExtractor(unittest.TestCase):
    """Test SKOS extraction functionality"""
    
    def setUp(self):
        """Create test data"""
        self.test_ttl_content = '''
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix ex: <http://example.org/thesaurus/> .

ex:computer-science a skos:Concept ;
    skos:prefLabel "Computer Science"@en ;
    skos:prefLabel "Informatica"@it ;
    skos:altLabel "CS"@en ;
    skos:definition "The study of algorithmic processes and computational systems"@en ;
    skos:broader ex:science .

ex:science a skos:Concept ;
    skos:prefLabel "Science"@en ;
    skos:prefLabel "Scienza"@it ;
    skos:narrower ex:computer-science .

ex:artificial-intelligence a skos:Concept ;
    skos:prefLabel "Artificial Intelligence"@en ;
    skos:prefLabel "Intelligenza Artificiale"@it ;
    skos:altLabel "AI" ;
    skos:broader ex:computer-science ;
    skos:related ex:machine-learning .

ex:machine-learning a skos:Concept ;
    skos:prefLabel "Machine Learning"@en ;
    skos:prefLabel "Apprendimento Automatico"@it ;
    skos:altLabel "ML" ;
    skos:broader ex:artificial-intelligence ;
    skos:related ex:artificial-intelligence .
'''
    
    def test_basic_extraction(self):
        """Test basic extraction functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test TTL file
            ttl_file = Path(temp_dir) / "test.ttl"
            with open(ttl_file, 'w', encoding='utf-8') as f:
                f.write(self.test_ttl_content)
            
            # Extract
            extractor = SKOSExtractor(verbose=True)
            result = extractor.extract(str(ttl_file), temp_dir)
            
            # Verify results
            self.assertGreater(len(result.languages), 0)
            self.assertIn('en', result.languages)
            self.assertIn('it', result.languages)
            self.assertGreater(result.total_concepts, 0)
            
            # Check output files exist
            for lang in result.languages:
                concepts_file = Path(temp_dir) / f"concepts_{lang}.json"
                labels_file = Path(temp_dir) / f"labels_to_concept_{lang}.json"
                
                self.assertTrue(concepts_file.exists())
                self.assertTrue(labels_file.exists())
                
                # Load and verify content
                with open(concepts_file, 'r', encoding='utf-8') as f:
                    concepts = json.load(f)
                    self.assertGreater(len(concepts), 0)
                
                with open(labels_file, 'r', encoding='utf-8') as f:
                    labels = json.load(f)
                    self.assertGreater(len(labels), 0)
            
            # Check metadata file
            metadata_file = Path(temp_dir) / "thesaurus_metadata.json"
            self.assertTrue(metadata_file.exists())
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.assertEqual(metadata['base_uri'], 'http://example.org/thesaurus/')
                self.assertIn('statistics_by_language', metadata)
    
    def test_symmetric_relations(self):
        """Test that relations are properly symmetrized"""
        with tempfile.TemporaryDirectory() as temp_dir:
            ttl_file = Path(temp_dir) / "test.ttl"
            with open(ttl_file, 'w', encoding='utf-8') as f:
                f.write(self.test_ttl_content)
            
            extractor = SKOSExtractor()
            result = extractor.extract(str(ttl_file), temp_dir)
            
            # Load English concepts
            concepts_file = Path(temp_dir) / "concepts_en.json"
            with open(concepts_file, 'r', encoding='utf-8') as f:
                concepts = json.load(f)
            
            # Check that computer-science has science as broader
            cs_concept = None
            for concept_id, concept_data in concepts.items():
                if concept_data['prefLabel'] == 'Computer Science':
                    cs_concept = concept_data
                    break
            
            self.assertIsNotNone(cs_concept)
            self.assertGreater(len(cs_concept['broaderConcept']), 0)
            
            # Check that science has computer-science as narrower
            science_concept = None
            for concept_id, concept_data in concepts.items():
                if concept_data['prefLabel'] == 'Science':
                    science_concept = concept_data
                    break
            
            self.assertIsNotNone(science_concept)
            self.assertGreater(len(science_concept['narrowerConcept']), 0)
    
    def test_universal_terms(self):
        """Test that terms without language tags are included in all languages"""
        with tempfile.TemporaryDirectory() as temp_dir:
            ttl_file = Path(temp_dir) / "test.ttl"
            with open(ttl_file, 'w', encoding='utf-8') as f:
                f.write(self.test_ttl_content)
            
            extractor = SKOSExtractor()
            result = extractor.extract(str(ttl_file), temp_dir)
            
            # Load both language files
            for lang in ['en', 'it']:
                labels_file = Path(temp_dir) / f"labels_to_concept_{lang}.json"
                with open(labels_file, 'r', encoding='utf-8') as f:
                    labels = json.load(f)
                    
                    # Both "AI" and "ML" (no language tags) should be in both files
                    self.assertIn('AI', labels)
                    self.assertIn('ML', labels)


if __name__ == '__main__':
    unittest.main()


