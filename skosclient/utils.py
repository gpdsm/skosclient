"""
Utility functions for SKOS processing
"""

from typing import Dict, List, Set
from rdflib import Graph, Literal
from rdflib.namespace import SKOS


def detect_languages(graph: Graph) -> List[str]:
    """Detect all languages present in the thesaurus"""
    languages = set()
    for s, p, o in graph:
        if isinstance(o, Literal) and o.language:
            languages.add(o.language)
    return sorted(list(languages))


def detect_base_uri(graph: Graph) -> str:
    """Detect the most common base URI for concepts"""
    skos = SKOS
    uris = list(graph.subjects(predicate=skos.prefLabel))
    
    if not uris:
        return "http://example.org/thesaurus/"
    
    # Find common prefix among URIs
    uri_strings = [str(uri) for uri in uris]
    if len(uri_strings) == 1:
        # If only one URI, extract base from it
        parts = uri_strings[0].split('/')
        return '/'.join(parts[:-1]) + '/'
    
    # Find longest common prefix
    common_prefix = uri_strings[0]
    for uri in uri_strings[1:]:
        while not uri.startswith(common_prefix):
            common_prefix = common_prefix[:-1]
    
    # Ensure it ends with / or #
    if not common_prefix.endswith(('/', '#')):
        last_slash = common_prefix.rfind('/')
        if last_slash > 0:
            common_prefix = common_prefix[:last_slash + 1]
    
    return common_prefix


def analyze_no_lang_literals(graph: Graph) -> Dict:
    """Analyze literals without language tags"""
    no_lang_literals = set()
    lang_literals = set()
    
    # Collect all literals with and without language
    for s, p, o in graph:
        if isinstance(o, Literal):
            literal_text = str(o)
            if o.language is None:
                no_lang_literals.add((str(s), str(p), literal_text))
            else:
                lang_literals.add((str(s), str(p), literal_text))
    
    # Find unique no-lang literals
    unique_no_lang = set()
    for s, p, text in no_lang_literals:
        # Check if same text exists for same subject/predicate in other languages
        found_in_other_lang = any(
            (s_lang, p_lang, text_lang) for s_lang, p_lang, text_lang in lang_literals
            if s == s_lang and p == p_lang and text == text_lang
        )
        if not found_in_other_lang:
            unique_no_lang.add((s, p, text))
    
    return {
        "total_no_lang": len(no_lang_literals),
        "unique_no_lang": len(unique_no_lang),
        "duplicate_no_lang": len(no_lang_literals) - len(unique_no_lang),
        "unique_samples": list(unique_no_lang)[:5]  # First 5 examples
    }


def validate_skos_graph(graph: Graph) -> Dict:
    """Validate SKOS graph structure and return diagnostics"""
    skos = SKOS
    diagnostics = {
        "total_triples": len(graph),
        "concepts_with_pref_label": 0,
        "concepts_total": 0,
        "orphaned_concepts": 0,
        "missing_pref_labels": [],
        "warnings": []
    }
    
    # Count concepts
    concepts = set(graph.subjects(predicate=skos.prefLabel))
    all_concepts = set()
    
    # Find all concepts (subjects of SKOS properties)
    skos_properties = [skos.prefLabel, skos.altLabel, skos.broader, skos.narrower, 
                      skos.related, skos.definition, skos.note]
    
    for prop in skos_properties:
        for subj in graph.subjects(predicate=prop):
            all_concepts.add(subj)
    
    diagnostics["concepts_total"] = len(all_concepts)
    diagnostics["concepts_with_pref_label"] = len(concepts)
    
    # Find concepts without prefLabel
    for concept in all_concepts:
        if concept not in concepts:
            diagnostics["missing_pref_labels"].append(str(concept))
    
    # Find orphaned concepts (no broader, no narrower relationships)
    orphaned = 0
    for concept in concepts:
        has_broader = bool(list(graph.objects(concept, skos.broader)))
        has_narrower = bool(list(graph.objects(concept, skos.narrower)))
        is_broader = bool(list(graph.subjects(skos.broader, concept)))
        is_narrower = bool(list(graph.subjects(skos.narrower, concept)))
        
        if not (has_broader or has_narrower or is_broader or is_narrower):
            orphaned += 1
    
    diagnostics["orphaned_concepts"] = orphaned
    
    # Add warnings
    if diagnostics["missing_pref_labels"]:
        diagnostics["warnings"].append(f"{len(diagnostics['missing_pref_labels'])} concepts without prefLabel")
    
    if orphaned > 0:
        diagnostics["warnings"].append(f"{orphaned} orphaned concepts (no hierarchical relationships)")
    
    return diagnostics