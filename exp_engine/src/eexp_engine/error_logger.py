import time
import traceback
import os

class ErrorLogger:
    def __init__(self, log_dir="/error_logs", retention_seconds=15*60):
        self.log_dir = log_dir
        self.retention_seconds = retention_seconds
        os.makedirs(self.log_dir, exist_ok=True)

    def cleanup_old_logs(self):
        now = time.time()
        for fname in os.listdir(self.log_dir):
            fpath = os.path.join(self.log_dir, fname)
            if os.path.isfile(fpath):
                try:
                    mtime = os.path.getmtime(fpath)
                    if now - mtime > self.retention_seconds:
                        os.remove(fpath)
                except Exception as e:
                    print(f"Error cleaning up log file {fpath}: {e}")

    def write_error_log(self, identifier, error, extra_info=None):
        self.cleanup_old_logs()
        ts = int(time.time())
        log_fname = f"error_{identifier}_{ts}.log"
        log_path = os.path.join(self.log_dir, log_fname)
        try:
            with open(log_path, "w") as f:
                if extra_info:
                    for k, v in extra_info.items():
                        f.write(f"{k}: {v}\n")
                f.write(f"Timestamp: {ts}\n")
                f.write(f"Exception: {error}\n")
                f.write("Stack Trace:\n")
                f.write(traceback.format_exc())
        except Exception as log_exc:
            print(f"Failed to write error log: {log_exc}")