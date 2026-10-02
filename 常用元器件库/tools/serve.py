import http.server, functools, sys
H = http.server.SimpleHTTPRequestHandler
H.extensions_map.update({".svg": "image/svg+xml", ".png": "image/png", ".pdf": "application/pdf"})
root = sys.argv[2]
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), functools.partial(H, directory=root)).serve_forever()
