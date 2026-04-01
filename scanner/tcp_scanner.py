"""Multi‑threaded TCP scanner with queue and stop event."""

import socket
import threading
import time
import queue

from scanner.service_detector import ServiceDetector

class TCPScanner:
    def __init__(self, target_ip, start_port, end_port, concurrency=100, timing=0.1, stop_event=None):
        self.target_ip = target_ip
        self.start_port = start_port
        self.end_port = end_port
        self.concurrency = concurrency
        self.timing = timing
        self.stop_event = stop_event if stop_event else threading.Event()
        self.service_detector = ServiceDetector()

        # Results
        self.results = []  # list of dicts
        self.progress_callback = None
        self.result_callback = None
        self.total_ports = end_port - start_port + 1
        self.scanned = 0
        self.lock = threading.Lock()

    def run(self, progress_callback=None, result_callback=None):
        self.progress_callback = progress_callback
        self.result_callback = result_callback
        self.scanned = 0
        self.results = []

        # Create a queue of ports
        port_queue = queue.Queue()
        for port in range(self.start_port, self.end_port + 1):
            port_queue.put(port)

        # Create worker threads
        threads = []
        for _ in range(self.concurrency):
            t = threading.Thread(target=self._worker, args=(port_queue,))
            t.start()
            threads.append(t)

        # Wait until either all ports are processed or stop_event is set
        while not self.stop_event.is_set():
            if port_queue.empty():
                break
            time.sleep(0.1)

        # If stop_event is set, drain the queue to allow workers to exit quickly
        if self.stop_event.is_set():
            while not port_queue.empty():
                try:
                    port_queue.get_nowait()
                    port_queue.task_done()
                except queue.Empty:
                    break

        # Wait for all workers to finish
        for t in threads:
            t.join(timeout=1)

    def _worker(self, port_queue):
        while not self.stop_event.is_set():
            try:
                port = port_queue.get(timeout=0.5)
            except queue.Empty:
                break
            self._scan_port(port)
            with self.lock:
                self.scanned += 1
                if self.progress_callback:
                    self.progress_callback(self.scanned, self.total_ports)
            port_queue.task_done()
            # Apply timing delay, but allow stop_event to interrupt quickly
            if self.timing > 0:
                # Sleep in small increments to remain responsive to stop
                sleep_chunks = int(self.timing * 10)  # 0.1 sec chunks
                for _ in range(sleep_chunks):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
                # If we broke early, we may have slept less than the full time.
                # That's acceptable because we want to exit quickly.

    def _scan_port(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.target_ip, port))
            if result == 0:
                # Port open
                service_name, version = self.service_detector.detect(self.target_ip, port)
                with self.lock:
                    self.results.append({
                        "port": port,
                        "service": service_name,
                        "version": version
                    })
                if self.result_callback:
                    self.result_callback(port, service_name, version)
            sock.close()
        except Exception:
            # Ignore errors for closed ports
            pass
