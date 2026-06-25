import http.server
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

class ShortsFilterHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path != '/shorts':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        query_params = urllib.parse.parse_qs(parsed_url.query)
        channel_ids = query_params.get('channel_id')
        if not channel_ids:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing channel_id parameter")
            return

        channel_id = channel_ids[0]
        youtube_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        try:
            req = urllib.request.Request(
                youtube_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Error fetching from YouTube: {e}".encode('utf-8'))
            return

        try:
            ET.register_namespace('', 'http://www.w3.org/2005/Atom')
            ET.register_namespace('yt', 'http://www.youtube.com/xml/schemas/2015')
            ET.register_namespace('media', 'http://search.yahoo.com/mrss/')

            root = ET.fromstring(xml_data)
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', namespace)

            for entry in entries:
                link = entry.find('atom:link[@rel="alternate"]', namespace)
                is_short = False
                if link is not None:
                    href = link.attrib.get('href', '')
                    if '/shorts/' in href:
                        is_short = True
                
                if not is_short:
                    root.remove(entry)

            filtered_xml = ET.tostring(root, encoding='utf-8')
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/xml; charset=utf-8')
            self.end_headers()
            self.wfile.write(filtered_xml)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error processing XML: {e}".encode('utf-8'))

if __name__ == '__main__':
    port = 8081
    server = http.server.HTTPServer(('0.0.0.0', port), ShortsFilterHandler)
    print(f"Shorts filter proxy listening on port {port}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
