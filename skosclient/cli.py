#!/usr/bin/env python3
"""
Command Line Interface for SKOSClient
"""

import argparse
import sys
from pathlib import Path
from tkinter import NO
from .website_generator import generate_website


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
        generate_website(base_uri=args.base_uri,verobse=args.verbose,output_path=output_path,input_path=input_path,file_format=args.format)
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