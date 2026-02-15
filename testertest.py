import webbrowser
import os

# Açılmasını istediğin siteyi buraya yaz
url = "https://www.google.com"

# Windows'ta Microsoft Edge'in varsayılan konumu genellikle budur
edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"

# Eğer Edge'i spesifik olarak açmak istersen
if os.path.exists(edge_path):
    webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
    webbrowser.get('edge').open(url)
    print("Edge üzerinden site açıldı.")
else:
    # Eğer yol farklıysa varsayılan tarayıcıda açar
    webbrowser.open(url)
    print("Edge bulunamadı, varsayılan tarayıcıda açılıyor.")