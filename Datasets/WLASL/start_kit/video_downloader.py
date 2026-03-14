import os, json, time, sys, random, logging, glob
import shutil
import subprocess
import urllib.request
import pandas as pd
import threading
from multiprocessing.dummy import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set this to youtube-dl if you want to use youtube-dl.
# The the README for an explanation regarding yt-dlp vs youtube-dl.
youtube_downloader = "yt-dlp"

# Enable ANSI colors on Windows (pip install colorama)
try:
    import colorama
    colorama.init()
except ImportError:
    pass

# ANSI color codes
class C:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def cprint(msg, color=""):
    """Print colored message to stderr (avoids buffering issues with progress)."""
    sys.stderr.write(f"{color}{msg}{C.RESET}\n")
    sys.stderr.flush()

def request_video(url, referer=''):
    """Fetch video data from URL. Retries with HTTP if HTTPS fails."""
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers = {'User-Agent': user_agent}
    if referer:
        headers['Referer'] = referer

    urls_to_try = [url]
    if url.startswith('https://'):
        urls_to_try.append(url.replace('https://', 'http://', 1))

    last_error = None
    for try_url in urls_to_try:
        try:
            logging.info('Requesting {}'.format(try_url))
            request = urllib.request.Request(try_url, None, headers)
            response = urllib.request.urlopen(request)
            return response.read()
        except Exception as e:
            last_error = e
            if try_url != urls_to_try[-1]:
                logging.info('HTTPS failed, retrying with HTTP: {}'.format(try_url.replace('https://', 'http://', 1)))
            else:
                raise last_error


def save_video(data, saveto):
    with open(saveto, 'wb+') as f:
        f.write(data)

    # please be nice to the host - take pauses and avoid spamming
    time.sleep(random.uniform(0.5, 1.5))


def download_youtube(url, dirname, video_id):
    raise NotImplementedError("Urllib cannot deal with YouTube links.")


def download_aslpro(url, dirname, video_id):
    saveto = os.path.join(dirname, '{}.swf'.format(video_id))
    if os.path.exists(saveto):
        logging.info('{} exists at {}'.format(video_id, saveto))
        return "skipped"
    try:
        data = request_video(url, referer='http://www.aslpro.com/cgi-bin/aslpro/aslpro.cgi')
        save_video(data, saveto)
        return "downloaded"
    except Exception:
        return "failed"


def download_others(url, dirname, video_id):
    saveto = os.path.join(dirname, '{}.mp4'.format(video_id))
    if os.path.exists(saveto):
        logging.info('{} exists at {}'.format(video_id, saveto))
        return "skipped"
    try:
        data = request_video(url)
        save_video(data, saveto)
        return "downloaded"
    except Exception:
        return "failed"


def select_download_method(url):
    if 'aslpro' in url:
        return download_aslpro
    elif 'youtube' in url or 'youtu.be' in url:
        return download_youtube
    else:
        return download_others


def download_nonyt_videos(saveto, gloss, video_id, video_url):
    logging.info('gloss: {}, video: {}.'.format(gloss, video_id))
    download_method = select_download_method(video_url)
    if download_method == download_youtube:
        logging.warning('Skipping YouTube video {}'.format(video_id))
        return "skipped"
    result = download_method(video_url, saveto, video_id)
    if result == "failed":
        logging.error('Unsuccessful downloading - video {}'.format(video_id))
    return result


def check_youtube_dl_version():
    ver = os.popen(f'{youtube_downloader} --version').read()

    assert ver, f"{youtube_downloader} cannot be found in PATH. Please verify your installation."


def download_yt_videos(saveto, video_url):
    if os.path.exists(os.path.join(saveto, video_url[-11:] + '.mp4')) or os.path.exists(os.path.join(saveto, video_url[-11:] + '.mkv')):
        logging.info('YouTube videos {} already exists.'.format(video_url))
        return "skipped"
    out_tpl = saveto + os.path.sep + "%(id)s.%(ext)s"
    urls_to_try = [video_url]
    if video_url.startswith('https://'):
        urls_to_try.append(video_url.replace('https://', 'http://', 1))

    for try_url in urls_to_try:
        result = subprocess.run(
            [youtube_downloader, "-q", "--no-progress", try_url, "-o", out_tpl],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logging.info('Finish downloading youtube video url {}'.format(video_url))
            time.sleep(random.uniform(1.0, 1.5))
            return "downloaded"
        if try_url != urls_to_try[-1]:
            logging.info('HTTPS failed, retrying with HTTP: {}'.format(video_url))

    logging.error('Unsuccessful downloading - youtube video url {}'.format(video_url))
    if result.stderr:
        logging.debug(result.stderr[:500])
    time.sleep(random.uniform(1.0, 1.5))
    return "failed"
    

def process_video(gloss, video_url, video_id, saveto):
    if 'youtube' not in video_url and 'youtu.be' not in video_url:
        return download_nonyt_videos(saveto, gloss, video_id, video_url)
    return download_yt_videos(saveto, video_url)


def get_latest_log(log_dir):
    log_files = glob.glob(os.path.join(log_dir, "*.log"))
    if not log_files:
        return None
    latest_log = max(log_files, key=os.path.getmtime)

    return latest_log


def get_skip_counter(indexfile, logfile):
    skip_counter = 0
    df = pd.read_json(indexfile)
    df_exploded = df.explode("instances", ignore_index=True)
    df_flat = pd.concat([df_exploded.drop(columns=["instances"]), pd.json_normalize(df_exploded["instances"])], axis=1)

    with open(logfile, "r") as f:
        try:
            lines = f.readlines()
            log_df = pd.DataFrame({"raw": [line.strip() for line in lines]})
            log_df["video_id"] = log_df["raw"].str.extract(r"video:?\s*(\d+)")
            last_video_id = log_df["video_id"].dropna()
            if last_video_id.empty:
                return 0
            last_video_id = last_video_id.iloc[-1]
            matched = df_flat[df_flat["video_id"].astype(str) == str(last_video_id)]
            if not matched.empty:
                index = matched.index[0]
                if index > 0:
                    skip_counter = index
        except Exception as e:
            logging.error(f"Error: {e}")

    return skip_counter


class ColoredStreamHandler(logging.StreamHandler):
    """Log handler that colors output by level. Only shows WARNING and ERROR to reduce noise."""
    LEVEL_COLORS = {
        logging.DEBUG: C.DIM,
        logging.INFO: C.GREEN,
        logging.WARNING: C.YELLOW,
        logging.ERROR: C.RED,
    }

    def emit(self, record):
        if record.levelno < logging.WARNING:
            return
        try:
            color = self.LEVEL_COLORS.get(record.levelno, "")
            msg = self.format(record)
            stream = self.stream
            stream.write(f"{color}{msg}{C.RESET}\n")
            stream.flush()
        except Exception:
            self.handleError(record)


def progress_bar(current, total, width=40, done_char="█", empty_char="░"):
    """Return a simple progress bar string."""
    if total <= 0:
        return ""
    pct = current / total
    filled = int(width * pct)
    bar = done_char * filled + empty_char * (width - filled)
    return f"[{bar}] {current}/{total} ({100*pct:.1f}%)"


def check_ffmpeg():
    """Warn once if ffmpeg is not found (helps with YouTube format selection)."""
    if not shutil.which("ffmpeg"):
        cprint("  Note: ffmpeg not found. Install for better YouTube format support.", C.YELLOW)


if __name__ == '__main__':
    indexfile = 'WLASL_subset.json'
    saveto = 'raw_videos_places_3'

    os.makedirs(saveto, exist_ok=True)
    content = json.load(open(indexfile))
    LOGFILE = None  # Disable resume - process all videos (set to get_latest_log(os.getcwd()) to re-enable)

    log_filename = 'download_{}.log'.format(int(time.time()))
    logging.basicConfig(level=logging.DEBUG)
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    file_handler = logging.FileHandler(log_filename, mode='w')
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    root_logger.addHandler(file_handler)
    console_handler = ColoredStreamHandler(sys.stderr)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(console_handler)

    # Banner
    total_instances = sum(len(e["instances"]) for e in content)
    total_glosses = len(content)
    cprint(f"\n{C.BOLD}{C.CYAN}═══ WLASL Video Downloader ═══{C.RESET}", "")
    cprint(f"  Index file: {indexfile}", C.DIM)
    cprint(f"  Output dir: {saveto}", C.DIM)
    cprint(f"  Glosses: {total_glosses}  |  Videos: {total_instances}", C.DIM)
    check_ffmpeg()
    cprint("", "")

    MAX_WORKERS = max(1, (os.cpu_count() or 4) - 4)
    futures = []
    count = 0
    skip_counter = get_skip_counter(indexfile, LOGFILE) - (MAX_WORKERS * 2) if LOGFILE else 0
    skip_counter = max(0, skip_counter)

    if skip_counter > 0:
        cprint(f"  Resuming from previous run (skipping first {skip_counter} videos)", C.YELLOW)

    cprint(f"  Using {MAX_WORKERS} workers\n", C.DIM)
    logging.info('Start downloading videos using multithreading.')

    progress_lock = threading.Lock()
    completed = 0
    stats = {"downloaded": 0, "skipped": 0, "failed": 0}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for entry in content:
            gloss = entry['gloss']
            for inst in entry['instances']:
                if count >= skip_counter:
                    video_url = inst['url']
                    video_id = inst['video_id']
                    futures.append(executor.submit(process_video, gloss, video_url, video_id, saveto))
                count += 1

        total_to_download = len(futures)
        for future in as_completed(futures):
            try:
                status = future.result()
                stats[status] = stats.get(status, 0) + 1
            except Exception as e:
                stats["failed"] += 1
                logging.error(f"Error: {e}")
            with progress_lock:
                completed += 1
                bar = progress_bar(completed, total_to_download)
                sys.stderr.write(f"\r  {C.CYAN}{bar}{C.RESET}   ")
                sys.stderr.flush()

    sys.stderr.write("\n\n")
    cprint(f"{C.BOLD}Done.{C.RESET}  Downloaded: {stats['downloaded']}  |  Skipped (exists): {stats['skipped']}  |  Failed: {stats['failed']}", "")
    cprint(f"  Log saved to: {log_filename}", C.DIM)
    logging.info('All downloads completed.')