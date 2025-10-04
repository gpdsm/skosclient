#!/usr/bin/env python3
"""
Command Line Interface for SKOSClient
"""

import argparse
import sys
from pathlib import Path
from tkinter import NO
from .extractor import SKOSExtractor
import string
import importlib.resources as resources


class AtTemplate(string.Template):
    # Change the delimiter to § because $ and | is used by JavaScript @ by css
    delimiter = '§'
    # Use the standard id pattern (match letters/numbers/underscores)
    idpattern = r'[a-z][_a-z0-9]*'

def render_template(name: str, **kwargs) -> str:
    try:
        tpl_text = resources.files("skosclient.websiteresources").joinpath(name).read_text(encoding='utf-8')
        return AtTemplate(tpl_text).substitute(**kwargs)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template '{name}' not found in skosclient.websiteresources")
    except KeyError as e:
        raise KeyError(f"Missing template variable: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Extract and process SKOS thesauri from Turtle/RDF files",
        prog="skosclient"
    )
    
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input Turtle/RDF file"
    )
    
    parser.add_argument(
        "output_dir",
        type=str,
        help="Output directory for generated JSON files",
        nargs="?"
    )
    
    parser.add_argument(
        "--base-uri",
        type=str,
        help="Override auto-detected base URI for concepts"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    parser.add_argument(
        "--format",
        choices=["turtle", "xml", "n3", "nt"],
        default="turtle",
        help="Input file format (default: turtle)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.is_file():
        print(f"Error: '{input_path}' is not a file", file=sys.stderr)
        sys.exit(1)
    #breakpoint()

    # Validate/create output directory
    output_path = args.output_dir
    if output_path is None:
        output_path = input_path.with_suffix("")
    else:
        output_path = Path(args.output_dir)
    
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error: Cannot create output directory '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create extractor and process
    try:
        print(f"Starting the extractor for creating the SKOS app at {output_path}...")
        extractor = SKOSExtractor(
            base_uri=args.base_uri,
            verbose=args.verbose
        )
        str_output_path = str(output_path)
        print(f"Processing {input_path}...")
        result = extractor.extract(
            input_file=str(input_path),
            output_dir=str_output_path,
            file_format=args.format
        )
        
        print(f"Successfully processed thesaurus!")
        print(f"Output saved in: {str_output_path}")
        print(f"Languages found: {', '.join(result.languages)}")
        print(f"Total concepts: {result.total_concepts}")
        print(f"Relations added: {result.total_relations_added}")
        if result.warnings:
            print(f"Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")

        #outpath = Path(outdir)
        #outpath.mkdir(parents=True, exist_ok=True)
        # breakpoint()
        # Example usage
        html = render_template("index.template.html", title="My App", description="/api")
        (output_path / "index.html").write_text(html)

        for ui_lang in ["en","it","de"]:
            name = f"ui_translations_{ui_lang}.json"
            translation = resources.files("skosclient.websiteresources").joinpath(name).read_text(encoding='utf-8')
            (output_path / name).write_text(translation)
        # Copy other static files without templating
        # for static_file in ["script.js", "style.css"]:
        #    tpl_text = resources.files("skosclient.websiteresources").joinpath(name).read_text(encoding='utf-8')
        #    (output_path / static_file).write_text(data)

    except KeyboardInterrupt:
        print("\n Operation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f" Error processing file: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()