#!/bin/sh
# Generates Flutter platform folders and wires the AR bridge into web/index.html
set -e
cd frontend
flutter create . --platforms=web,android,ios --project-name vto_app
grep -q ar.js web/index.html || sed -i 's#</head>#  <script type="module" src="ar.js"></script>\n</head>#' web/index.html
flutter pub get
echo "Run: flutter run -d chrome --dart-define=API_BASE=http://localhost:8000"
