#!/usr/bin/env python3
"""Local-only concurrent static server for deterministic browser audits."""
import argparse
import gzip
import io
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class Server(ThreadingHTTPServer):
    request_queue_size = 64

class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    compression = False
    def send_head(self):
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / 'index.html'
        # Optional QA profile mirrors Pages' observed gzip transfer; PDF and
        # images stay byte-identical. Normal Playwright serving is unchanged.
        if self.compression and 'gzip' in self.headers.get('Accept-Encoding', '') and path.is_file() and path.suffix in {'.html', '.css', '.js', '.json', '.xml', '.svg'}:
            body = gzip.compress(path.read_bytes(), mtime=0)
            self.send_response(200)
            self.send_header('Content-type', self.guess_type(str(path)))
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Vary', 'Accept-Encoding')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            return io.BytesIO(body)
        return super().send_head()
    def log_message(self, *_args):
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--directory', default='site')
    parser.add_argument('--gzip', action='store_true')
    args = parser.parse_args()
    Handler.compression = args.gzip
    with Server(('127.0.0.1', args.port), partial(Handler, directory=args.directory)) as server:
        print('Local static browser audit server ready', flush=True)
        server.serve_forever()
