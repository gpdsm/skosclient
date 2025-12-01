
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
        tpl_text = resources.files("skosclient.websiteresources").joinpath(
            name).read_text(encoding='utf-8')
        return AtTemplate(tpl_text).substitute(**kwargs)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Template '{name}' not found in skosclient.websiteresources")
    except KeyError as e:
        raise KeyError(f"Missing template variable: {e}")


def generate_website(base_uri, verobse, output_path, input_path, file_format):
    extractor = SKOSExtractor(base_uri=base_uri, verbose=verobse)
    str_output_path = str(output_path)
    print(f"Processing {input_path}...")
    result = extractor.extract(
        input_file=str(input_path),
        output_dir=str_output_path,
        file_format=file_format
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

    # outpath = Path(outdir)
    # outpath.mkdir(parents=True, exist_ok=True)
    # breakpoint()
    # Example usage
    html = render_template("index.template.html",
                           title="My App", description="/api")
    (output_path / "index.html").write_text(html, encoding="utf-8")

    for ui_lang in ["en", "it", "de"]:
        name = f"ui_translations_{ui_lang}.json"
        translation = resources.files("skosclient.websiteresources").joinpath(
            name).read_text(encoding='utf-8')
        (output_path / name).write_text(translation, encoding="utf-8")
    # Copy other static files without templating
    for static_file in ["script.js", "style.css"]:
        tpl_text = resources.files("skosclient.websiteresources").joinpath(static_file).read_text(encoding='utf-8')
        (output_path / static_file).write_text(tpl_text,encoding="utf-8")
