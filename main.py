import os
import sys
import time
import socket
import threading
import urllib.request
import webview

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def get_base_dir():
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def start_server_in_thread(port):
    import server
    server.run_server(port=port)

def wait_for_server(port, timeout=10):
    url = f"http://127.0.0.1:{port}/api/book_info"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False

def main():
    port = find_free_port()
    
    # Start Bottle server in background daemon thread
    server_thread = threading.Thread(target=start_server_in_thread, args=(port,), daemon=True)
    server_thread.start()

    # Wait for server ready
    ready = wait_for_server(port, timeout=8)
    if not ready:
        print("Server failed to start in time.")
        sys.exit(1)

    url = f"http://127.0.0.1:{port}/"

    # Create PyWebView window
    window = webview.create_window(
        title='ReadEasy - 瑞典语电子书阅读器',
        url=url,
        width=1280,
        height=860,
        min_size=(850, 600),
        text_select=True,
        confirm_close=False
    )

    # Start PyWebView
    webview.start(gui='edgechromium', debug=False)

if __name__ == '__main__':
    main()
