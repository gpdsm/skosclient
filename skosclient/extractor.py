"""
SKOS Thesaurus Extractor

Extracts concepts, labels, and relationships from SKOS thesauri in various RDF formats.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import SKOS, DCTERMS, DC, RDF

from .utils import detect_base_uri, detect_languages, analyze_no_lang_literals


@dataclass
class ExtractionResult:
    """Result of SKOS extraction process"""
    languages: List[str] = field(default_factory=list)
    total_concepts: int = 0
    total_relations_added: int = 0
    base_uri: str = ""
    output_files: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class SKOSExtractor:
    """
    SKOS Thesaurus Extractor
    
    Extracts concepts, labels, and relationships from SKOS thesauri,
    ensuring symmetric relationships and multi-language support.
    """
    
    def __init__(self, base_uri: Optional[str] = None, verbose: bool = False):
        """
        Initialize the extractor
        
        Args:
            base_uri: Override auto-detected base URI for concepts
            verbose: Enable verbose logging
        """
        self.base_uri = base_uri
        self.verbose = verbose
        self.graph: Optional[Graph] = None
        self.skos = SKOS
        self.dcterms = DCTERMS
        self.dc = DC
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[{level}] {message}")
    
    def extract(self, input_file: str, output_dir: str, file_format: str = "turtle") -> ExtractionResult:
        """
        Extract SKOS thesaurus from file
        
        Args:
            input_file: Path to input RDF file
            output_dir: Directory to save output files
            file_format: RDF format (turtle, xml, n3, nt)
            
        Returns:
            ExtractionResult with processing information
        """
        result = ExtractionResult()
        
        # Load and parse the graph
        self.graph = self._load_graph(input_file, file_format)
        self.log(f"Loaded {len(self.graph)} triples from {input_file}")
        
        # Detect base URI and languages
        if not self.base_uri:
            self.base_uri = detect_base_uri(self.graph)
        result.base_uri = self.base_uri
        
        languages = detect_languages(self.graph)
        no_lang_analysis = analyze_no_lang_literals(self.graph)
        
        self.log(f"Detected base URI: {self.base_uri}")
        self.log(f"Detected languages: {languages}")
        self.log(f"No-lang literals: {no_lang_analysis['total_no_lang']} (will be included in all languages)")
        
        # Extract metadata
        metadata = self._extract_metadata(languages, no_lang_analysis, input_file)
        
        # Process each language
        all_stats = {}
        total_relations_added = {"broader_from_narrower": 0, "narrower_from_broader": 0, "related_symmetric": 0}
        
        for lang in languages:
            self.log(f"Processing language: {lang}")
            concepts, labels_to_concept, relations_added = self._process_language(lang)
            
            if not concepts:
                result.warnings.append(f"No concepts found for language: {lang}")
                continue
            
            # Save files for this language
            self._save_language_files(lang, concepts, labels_to_concept, output_dir)
            result.output_files.extend([
                f"labels_to_concept_{lang}.json",
                f"concepts_{lang}.json"
            ])
            
            # Accumulate statistics
            for key in total_relations_added:
                total_relations_added[key] += relations_added[key]
            
            all_stats[lang] = self._calculate_statistics(concepts, labels_to_concept, relations_added)
            self.log(f"Processed {len(concepts)} concepts for language {lang}")
        
        # Save metadata
        metadata["statistics_by_language"] = all_stats
        metadata["symmetric_relations_added"] = total_relations_added
        
        metadata_file = Path(output_dir) / "thesaurus_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        result.output_files.append("thesaurus_metadata.json")
        
        # Fill result
        result.languages = languages
        result.total_concepts = sum(stats["total_concepts"] for stats in all_stats.values())
        result.total_relations_added = sum(total_relations_added.values())
        result.statistics = all_stats
        
        return result
    
    def _load_graph(self, input_file: str, file_format: str) -> Graph:
        """Load RDF graph from file"""
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        graph = Graph()
        try:
            file_uri = input_path.as_uri()
        except ValueError:
            file_uri = input_path

        # Try different parsing strategies
        try:
            graph.parse(file_uri, format=file_format)
            return graph
        except Exception as e:
            self.log(f"Failed to parse as {file_format}: {e}", "WARNING")
            
            # Try other formats
            formats = ["turtle", "xml", "n3", "nt"]
            for fmt in formats:
                if fmt == file_format:
                    continue
                try:
                    graph = Graph()
                    graph.parse(file_uri, format=fmt)
                    self.log(f"Successfully parsed as {fmt}", "INFO")
                    return graph
                except Exception:
                    continue
              
    def _extract_metadata(self, languages: List[str], no_lang_analysis: Dict, input_file: str) -> Dict:
        """Extract thesaurus metadata"""
        metadata = {
            "base_uri": self.base_uri,
            "extraction_date": datetime.now().isoformat(),
            "available_languages": languages,
            "ui_languages" :["en","it","de"],
            "title": {},
            "description": {},
            "creator": None,
            "created": None,
            "modified": None,
            "version": None,
            "source_file": Path(input_file).name,
            "no_lang_analysis": no_lang_analysis
        }
        # SIMPLIFIED: Find all skos:ConceptScheme directly
        schemes = list(self.graph.subjects(predicate=RDF.type, object=self.skos.ConceptScheme))
        
        # DEBUG: provo a veder...
        print(f"Found {len(schemes)} concept schemes")
        for scheme in schemes:
            print(f"Scheme: {scheme}")
            print(f"Number of schemes found: {len(schemes)}")
  
        for scheme in schemes:
        # Extract titles from all possible predicates
            for title_pred in [self.dc.title, self.dcterms.title]:
                for title in self.graph.objects(scheme, title_pred):
                    if isinstance(title, Literal):
                        lang = title.language or "no-lang"
                        metadata["title"][lang] = str(title)
            
            # Extract descriptions from all possible predicates
            for desc_pred in [self.dc.description, self.dcterms.description]:
                for desc in self.graph.objects(scheme, desc_pred):
                    if isinstance(desc, Literal):
                        lang = desc.language or "no-lang"
                        metadata["description"][lang] = str(desc)
            
            # Other metadata
            for creator in self.graph.objects(scheme, self.dcterms.creator):
                metadata["creator"] = str(creator)
                break
            
            for created in self.graph.objects(scheme, self.dcterms.created):
                metadata["created"] = str(created)
                break
            
            for modified in self.graph.objects(scheme, self.dcterms.modified):
                metadata["modified"] = str(modified)
                break
        
        return metadata
    
    def _process_language(self, lang: str) -> Tuple[Dict, Dict, Dict]:
        """Process thesaurus for a specific language"""
        labels_to_concept = {}
        concepts = {}
        
        # Extract all concepts
        for s in self.graph.subjects(predicate=self.skos.prefLabel):
            concept_id = self._uri_to_id(s)
            
            concepts[concept_id] = {
                "prefLabel": None,
                "broaderConcept": set(),
                "narrowerConcept": set(),
                "related": set(),
                "altLabel": set(),
                "definition": set(),
                "note": set(),
                "scopeNote": set(),
                "historyNote": set(),
                "example": set(),
                "editorialNote": set()
            }
            
            # Extract all properties
            self._extract_labels(s, concept_id, lang, concepts, labels_to_concept)
            self._extract_relations(s, concept_id, concepts)
            self._extract_notes(s, concept_id, lang, concepts)
        
        # Convert sets to lists and add prefLabels to relations
        self._finalize_concepts(concepts, lang)
        
        # Ensure symmetric relations
        relations_added = self._ensure_symmetric_relations(concepts, lang)
        
        return concepts, labels_to_concept, relations_added
    
    def _extract_labels(self, uri: URIRef, concept_id: str, lang: str, concepts: Dict, labels_to_concept: Dict) -> None:
        """Extract all types of labels for a concept"""
        # prefLabel
        found_label = False
        
        # First try specific language
        for o in self.graph.objects(uri, self.skos.prefLabel):
            if isinstance(o, Literal) and o.language == lang:
                label_str = str(o)
                concepts[concept_id]["prefLabel"] = label_str
                self._add_label_to_concept("p"+label_str, concept_id, labels_to_concept)
                found_label = True
                break
        
        # Then try no-lang (universal)
        if not found_label:
            for o in self.graph.objects(uri, self.skos.prefLabel):
                if isinstance(o, Literal) and o.language is None:
                    label_str = str(o)
                    # we might consider using p+label_str to indicate is a prefLable
                    concepts[concept_id]["prefLabel"] = label_str
                    self._add_label_to_concept("p"+label_str, concept_id, labels_to_concept)
                    found_label = True
                    break
        
        # Finally fallback to any language
        if not found_label:
            for o in self.graph.objects(uri, self.skos.prefLabel):
                if isinstance(o, Literal):
                    label_str = str(o) # we use p to indicate is a prefLabel
                    concepts[concept_id]["prefLabel"] = label_str
                    self._add_label_to_concept("p"+label_str, concept_id, labels_to_concept)
                    found_label = True
                    break
        
        # Skip concept if no prefLabel found
        if not found_label:
            del concepts[concept_id]
            print("NO PREF LABEL FOUND FOR", concept_id)
            return
        
        # altLabel and hiddenLabel
        for label_type in [self.skos.altLabel, self.skos.hiddenLabel]:
            for o in self.graph.objects(uri, label_type):
                if isinstance(o, Literal):
                    if o.language == lang or o.language is None:
                        if label_type == self.skos.altLabel:
                            concepts[concept_id]["altLabel"].add(str(o))
                            label_str_ = "a"+str(o)
                        else:
                            label_str_ = "h"+str(o)
                        self._process_comma_separated_labels(label_str_, concept_id, labels_to_concept)

    
    def _extract_relations(self, uri: URIRef, concept_id: str, concepts: Dict) -> None:
        """Extract hierarchical and associative relations"""
        # Broader concepts
        for o in self.graph.objects(uri, self.skos.broader):
            broader_id = self._uri_to_id(o)
            concepts[concept_id]["broaderConcept"].add(broader_id)
        
        # Narrower concepts
        for o in self.graph.objects(uri, self.skos.narrower):
            narrower_id = self._uri_to_id(o)
            concepts[concept_id]["narrowerConcept"].add(narrower_id)
        
        # Related concepts
        for o in self.graph.objects(uri, self.skos.related):
            related_id = self._uri_to_id(o)
            concepts[concept_id]["related"].add(related_id)
    
    def _extract_notes(self, uri: URIRef, concept_id: str, lang: str, concepts: Dict) -> None:
        """Extract all types of notes and documentation"""
        note_mappings = [
            (self.skos.definition, "definition"),
            (self.skos.note, "note"),
            (self.skos.scopeNote, "scopeNote"),
            (self.skos.historyNote, "historyNote"),
            (self.skos.example, "example"),
            (self.skos.editorialNote, "editorialNote")
        ]
        
        for note_type, field_name in note_mappings:
            for o in self.graph.objects(uri, note_type):
                if isinstance(o, Literal):
                    if o.language == lang or o.language is None:
                        concepts[concept_id][field_name].add(str(o))
    
    def _finalize_concepts(self, concepts: Dict, lang: str) -> None:
        """Convert sets to sorted lists and add prefLabels to relations"""
        for concept_id, data in concepts.items():
            # Convert sets to sorted lists
            for field in ["altLabel", "definition", "note", "scopeNote", "historyNote", "example", "editorialNote"]:
                data[field] = sorted(list(data[field]))
            
            # Add prefLabels to relations
            for relation_field in ["broaderConcept", "narrowerConcept", "related"]:
                relation_list = []
                for rel_id in data[relation_field]:
                    full_uri = self._id_to_uri(rel_id)
                    pref_label = self._get_pref_label(full_uri, lang)
                    if pref_label:
                        relation_list.append({pref_label: rel_id})
                    else:
                        relation_list.append({rel_id: rel_id})
                data[relation_field] = relation_list
    
    def _ensure_symmetric_relations(self, concepts: Dict, lang: str) -> Dict:
        """Ensure SKOS relations are symmetric"""
        relations_added = {"broader_from_narrower": 0, "narrower_from_broader": 0, "related_symmetric": 0}
        
        # Make a copy of concept IDs to avoid modification during iteration
        concept_ids = list(concepts.keys())
        
        for concept_id in concept_ids:
            data = concepts[concept_id]
            
            # Broader <-> Narrower symmetry
            for broader_relation in data["broaderConcept"]:
                broader_id = list(broader_relation.values())[0] if isinstance(broader_relation, dict) else broader_relation
                
                if broader_id in concepts:
                    # Check if narrower relation exists
                    narrower_found = any(
                        (isinstance(nr, dict) and list(nr.values())[0] == concept_id) or nr == concept_id
                        for nr in concepts[broader_id]["narrowerConcept"]
                    )
                    
                    if not narrower_found:
                        full_uri = self._id_to_uri(concept_id)
                        pref_label = self._get_pref_label(full_uri, lang)
                        if pref_label:
                            concepts[broader_id]["narrowerConcept"].append({pref_label: concept_id})
                        else:
                            concepts[broader_id]["narrowerConcept"].append({concept_id: concept_id})
                        relations_added["narrower_from_broader"] += 1
            
            # Related symmetry
            for related_relation in data["related"]:
                related_id = list(related_relation.values())[0] if isinstance(related_relation, dict) else related_relation
                
                if related_id in concepts:
                    # Check if inverse relation exists
                    related_found = any(
                        (isinstance(rr, dict) and list(rr.values())[0] == concept_id) or rr == concept_id
                        for rr in concepts[related_id]["related"]
                    )
                    
                    if not related_found:
                        full_uri = self._id_to_uri(concept_id)
                        pref_label = self._get_pref_label(full_uri, lang)
                        if pref_label:
                            concepts[related_id]["related"].append({pref_label: concept_id})
                        else:
                            concepts[related_id]["related"].append({concept_id: concept_id})
                        relations_added["related_symmetric"] += 1
        
        self.log(f"Added {sum(relations_added.values())} symmetric relations for {lang}")
        return relations_added
    
    def _save_language_files(self, lang: str, concepts: Dict, labels_to_concept: Dict, output_dir: str) -> None:
        """Save concepts and labels files for a language"""
        output_path = Path(output_dir)
        
        labels_file = output_path / f"labels_to_concept_{lang}.json"
        concepts_file = output_path / f"concepts_{lang}.json"
        
        with open(labels_file, "w", encoding="utf-8") as f:
            json.dump(labels_to_concept, f, ensure_ascii=False, indent=2)
        
        with open(concepts_file, "w", encoding="utf-8") as f:
            json.dump(concepts, f, ensure_ascii=False, indent=2)
    
    def _calculate_statistics(self, concepts: Dict, labels_to_concept: Dict, relations_added: Dict) -> Dict:
        """Calculate statistics for processed language"""
        return {
            "total_concepts": len(concepts),
            "total_labels": len(labels_to_concept),
            "concepts_with_broader": sum(1 for c in concepts.values() if c["broaderConcept"]),
            "concepts_with_narrower": sum(1 for c in concepts.values() if c["narrowerConcept"]),
            "concepts_with_related": sum(1 for c in concepts.values() if c["related"]),
            "concepts_with_alt_labels": sum(1 for c in concepts.values() if c["altLabel"]),
            "concepts_with_definitions": sum(1 for c in concepts.values() if c["definition"]),
            "concepts_with_notes": sum(1 for c in concepts.values() if any([
                c["definition"], c["note"], c["scopeNote"], 
                c["historyNote"], c["example"], c["editorialNote"]
            ])),
            "duplicate_labels_found": sum(1 for label in labels_to_concept.keys() 
                                        if '_' in label and label.split('_')[-1].isdigit()),
            "relations_added": relations_added
        }
    
    # Utility methods
    def _uri_to_id(self, uri: URIRef) -> str:
        """Convert URI to abbreviated ID"""
        uri_str = str(uri)
        if uri_str.startswith(self.base_uri):
            return uri_str[len(self.base_uri):]
        return uri_str
    
    def _id_to_uri(self, concept_id: str) -> URIRef:
        """Convert abbreviated ID to full URI"""
        if concept_id.startswith(('http://', 'https://', 'urn:')):
            return URIRef(concept_id)
        return URIRef(self.base_uri + concept_id)
    
    def _get_pref_label(self, uri: URIRef, lang: str) -> Optional[str]:
        """Get preferred label for URI in specified language"""
        # Try specific language first
        for o in self.graph.objects(uri, self.skos.prefLabel):
            if isinstance(o, Literal) and o.language == lang:
                return str(o)
        
        # Try no-lang
        for o in self.graph.objects(uri, self.skos.prefLabel):
            if isinstance(o, Literal) and o.language is None:
                return str(o)
        
        # Fallback to any language
        for o in self.graph.objects(uri, self.skos.prefLabel):
            if isinstance(o, Literal):
                return str(o)
        
        return None
    
    def _add_label_to_concept(self, label: str, concept_id: str, labels_dict: Dict) -> str:
        """Add label to concept dictionary, handling duplicates"""
        original_label = label
        counter = 1
        
        while label in labels_dict:
            if labels_dict[label] == concept_id:
                return label
            counter += 1
            label = f"{original_label}_{counter}"
        
        labels_dict[label] = concept_id
        return label
    
    def _process_comma_separated_labels(self, label_str: str, concept_id: str, labels_dict: Dict) -> None:
        """Process comma-separated labels into individual entries"""
        if ',' in label_str:
            typeLabel = label_str[0]
            label_str = label_str[1:]
            individual_labels = [label.strip() for label in label_str.split(',')]
            for individual_label in individual_labels:
                if individual_label:
                    self._add_label_to_concept(typeLabel+individual_label, concept_id, labels_dict)
        else:
            self._add_label_to_concept(label_str, concept_id, labels_dict)