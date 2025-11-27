#!/usr/bin/env python3
import http.server
import ssl
import os

# Change to the directory containing the files
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create server
server_address = ('0.0.0.0', 3000)
httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)

# Wrap with SSL
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('cert.pem', 'key.pem')
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print(f"Server running on https://0.0.0.0:3000")
print(f"Access from your phone at: https://192.168.0.237:3000")
print("Note: You'll need to accept the self-signed certificate warning in your browser")
httpd.serve_forever()

