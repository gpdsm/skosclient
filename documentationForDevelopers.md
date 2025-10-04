# Documentation for mantainers

This package take as an in put a SKOS dictionary and create a clien-side application for visualizing and querying the results.

## Templating
I decides to use the templating system from the standard Python library `string` for avoiding requiring other dependences like Jinja2. One drawback is that the standard syntax `$variable` conflicts with the Javascript templateing system. 
I have changed the delimiter to `|` it seems a good compromise because it is usally not used in HTML and CSS, while other charachter such as `#` and `@` are used. 