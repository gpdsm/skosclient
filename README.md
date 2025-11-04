# SKOSClient

A lightweight tool for building client-side web interfaces for SKOS vocabularies and thesauri. SKOSClient converts RDF/SKOS files into optimized JSON formats and generates a ready-to-deploy single-page application with search, navigation, and multilingual support.

## Features

- 🚀 **Zero backend required** - Fully client-side application
- 🌐 **Multilingual support** - Interface and content in multiple languages
- 🔍 **Full-text search** - Fast label-based search with autocomplete
- 📱 **Responsive design** - Works on desktop and mobile devices
- ⚡ **Optimized performance** - JSON-based data structure for fast loading

## Installation

Install directly from GitHub:
```bash
pip install git+https://github.com/gpdsm/skosclient.git
```

## Quick Start

1. **Generate the application** from your SKOS file:
```bash
skosclient mydictionary.ttl
```

This creates a `mydictionary/` directory containing the complete web application.

2. **Serve the application** locally:

For testing purposes you can serve the application using python. Rember that `http.server` does not handle UTF-8 so some character might not be rendered correctly.

```bash
cd mydictionary
python -m http.server
```

1. **Open in browser**: Navigate to `http://localhost:8000/`

## How It Works

SKOSClient processes your SKOS/RDF vocabulary and generates:

- **JSON concept files** (`concepts_{lang}.json`) - All SKOS concepts with their properties
- **Label-to-ID mappings** (`labels_to_concept_{lang}.json`) - Optimized for fast search
- **Metadata file** (`thesaurus_metadata.json`) - Configuration and available languages
- **Translation files** (`ui_translations_{lang}.json`) - Interface localization
- **Static HTML/CSS/JS** - Complete single-page application

The generated application uses vanilla JavaScript with no dependencies, making it lightweight and easy to deploy on any web server or CDN.

## URL Structure and Permalinks

### Default URLs

Concepts are accessible via query parameters:
```
/mydictionary/?concept={concept_id}&lang=en
/mydictionary/?concept={concept_id}&lang=it&ui=en
```

**Query parameters:**
- `concept` or `id` - The concept identifier
- `lang` - Content language (e.g., 'en', 'it', 'de')
- `ui` or `uilang` - Interface language (optional, auto-detected from browser)

### Clean URLs with Nginx

For SEO-friendly URLs, configure a reverse proxy to rewrite paths:
```nginx
server {
    listen 80;
    server_name www.mywebsite.com;
    root /var/www/html;
    
    location /mydictionary/ {
        # Rewrite: /mydictionary/{concept_id} -> /mydictionary/?concept={concept_id}&lang=en
        rewrite ^/mydictionary/([^/]+)$ /mydictionary/?concept=$1&lang=en permanent;
        
        # Serve the application
        try_files $uri $uri/ /mydictionary/index.html;
    }
    
    # Serve JSON files with correct MIME type
    location ~ \.json$ {
        add_header Content-Type application/json;
        add_header Cache-Control "public, max-age=3600";
    }
}
```

This enables URLs like:
- `/mydictionary/backend` → concept with ID "backend"
- `/mydictionary/formal_language` → concept with ID "formal_language"

### Advanced URL patterns

Support multiple languages in the URL path:
```nginx
location /mydictionary/ {
    # Pattern: /mydictionary/{concept_id}/{lang}
    if ($request_uri ~* "^/mydictionary/([^/]+)/([^/?]+)$") {
        return 301 /mydictionary/?concept=$1&lang=$2;
    }
    
    # Pattern: /mydictionary/{concept_id}
    if ($request_uri ~* "^/mydictionary/([^/?]+)$") {
        return 301 /mydictionary/?concept=$1&lang=en;
    }
    
    try_files $uri $uri/ /mydictionary/index.html;
}
```

## Metadata Configuration

The generated `thesaurus_metadata.json` file can be customized:
```json
{
  "title": "My Thesaurus",
  "description": "A specialized vocabulary for my domain",
  "available_languages": ["en", "it", "fr", "de"],
  "ui_languages": ["en", "it"]
}
```

## Customization

### Styling

Edit the CSS in `index.html` to customize the appearance. The application uses a classic academic style by default but can be easily adapted.

### Translations

Add new interface languages by creating `ui_translations_{lang}.json` files with translations for UI elements.

### Template

Use your own HTML template by creating an `index.template.html` file before running SKOSClient.

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Any browser with ES6+ and `Intl.DisplayNames` support

## Deployment

The generated application is static and can be deployed to:
- Apache/Nginx web servers
- GitHub Pages
- Netlify, Vercel, or similar CDN services
- Amazon S3 + CloudFront
- Any static file hosting service

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Support

For issues and questions, please use the [GitHub issue tracker](https://github.com/gpdsm/skosclient/issues).