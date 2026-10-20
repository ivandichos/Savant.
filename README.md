# Savant

Run it with a local web server (do NOT double-click index.html):

    python -m http.server 8000

then open http://localhost:8000 in your browser. (Or use the VS Code "Live Server" extension.)

Product pictures go in assets/products/ as <id>.png and <id>-bottle.png (see the README.txt there).

No server? Double-click index-offline.html instead. It has the Python code inside the page
(css and images stay in their own files). If you edit py/main.py, re-copy it into index-offline.html.

## Login pages
- login.html, signup.html, forgot-password.html (css/auth.css, js/auth.js)
- Put the picture for the left side at assets/login-perfume.png (the placeholder shows until then).
- Accounts are saved in the browser (localStorage), in the same format as the shop, so logging in here also logs you in on index.html.
- This is a front-end demo: passwords are NOT secure and accounts are not shared between devices.
