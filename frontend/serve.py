"""Simple HTTP server with correct MIME types for ES modules."""
import http.server
import os
import sys

PORT = 38080

class MyHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        '': 'application/octet-stream',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff2': 'font/woff2',
        '.woff': 'font/woff',
    }

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        sys.stdout.write("[%s] %s - %s\n" % (self.log_date_time_string(), self.client_address[0], format % args))
        sys.stdout.flush()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"Serving frontend on http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop")
    httpd = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), MyHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()
