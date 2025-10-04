# skosclient
A package to build client-side interfaces to SKOS dictionaries.

# Installations

`pip install git+https://github.com/gpdsm/skosclient.git`

# Usage

`skosclient mydictionary.ttl`

`cd mydictionary`

Run a web server:

`python -m http.server`

Open the browser, at the local host address usually `http://localhost:8000/`.


# How it works?
`skosclient` transforms a SKOS dictonary into JSON files optimized to be viewed using a pre-build Vanilla Javascript front-end. The files are stored in the output folder that contains the HTML, Javascript and CSS needed to run the application.

# URLs and permalinks
`skosclient` builds client-side application so SKOS concept will be available using query parameters:

`/mydictionary/?concept={concept_id}&lang=en`

However you can use a reverse proxy server (e.g. Nginx) to create standard concepts URL: 

```ngnix
location /mydictionary/ {
    # Rewrite pattern: /mydictionary/{concept_id} -> /mydictionary/?concept={concept_id}&lang=en
    rewrite ^/mydictionary/([^/]+)$ /kth/?concept=$1&lang=en redirect;
    
    # Serve the actual files
    try_files $uri $uri/ /mydictionary/index.html;
}
```


