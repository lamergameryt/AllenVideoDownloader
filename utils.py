import ctypes
import os
import pathlib
import threading
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Progressbar
import wget
# noinspection PyPackageRequirements
from allen import RecordedVideo

seperator = os.sep
output_folder = os.path.expanduser('~') + seperator + 'Documents' + seperator


def check_exists(video: RecordedVideo):
    destination = output_folder + video.subject_name + video.get_recording_date().split(':')[-1] + '.mp4'
    return pathlib.Path(destination).is_file()


def get_confirmation(video: RecordedVideo):
    return messagebox.askyesno('Download Video', f'Do you wish to download {video.subject_name} '
                                                 f'({video.get_recording_date()})?')


def terminate_thread(thread: threading.Thread):
    """Terminates a python thread from another thread.

    :param thread: a threading.Thread instance
    """
    if not thread.is_alive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


class VideoDownloader:
    current_toplevel = None

    def __init__(self, videos: list[RecordedVideo], window: Tk, login_btn: Button):
        self.videos = videos
        self.window = window
        self.login_btn = login_btn

    def _exit_window(self, thread: threading.Thread, index: int):
        if messagebox.askokcancel("Quit", "Do you want to quit downloading the file?"):
            terminate_thread(thread)
            self.current_toplevel.destroy()
            self.download(index + 1)

    def download(self, index: int = 0):
        if not self.videos:
            messagebox.showerror('No videos available', 'No videos are available to download right now!')
            self.login_btn['state'] = 'normal'
            return

        if index >= len(self.videos):
            messagebox.showinfo('Videos Downloaded', 'The selected videos were downloaded!')
            self.login_btn['state'] = 'normal'
            return

        video = self.videos[index]

        if not get_confirmation(video):
            self.download(index + 1)
            return

        destination = output_folder + video.subject_name + video.get_recording_date().split(':')[-1] + '.mp4'
        file_name = destination.split(seperator)[-1]

        root = Toplevel(self.window)
        self.current_toplevel = root

        root.iconbitmap('assets/logo.ico')
        root.resizable(False, False)
        pb = Progressbar(root, orient='horizontal', mode='determinate', length=300)
        pb.start()
        root.title(f'Downloading {file_name}')
        pb.grid(column=0, row=0, columnspan=2, padx=10, pady=20)
        value = StringVar()
        value.set('Starting download . . .')
        value_label = Label(root, textvariable=value)
        value_label.grid(column=0, row=1, columnspan=2)

        def target_thread():
            def bar_progress(current, total, width=80):
                percent = current / total * 100
                pb['value'] = percent
                value.set(f"Current Progress: {round(pb['value'], 2)}%")
                root.update_idletasks()

            wget.download(video.get_link(), destination, bar=bar_progress)
            self.current_toplevel.destroy()
            messagebox.showinfo('Download Complete', f'Downloaded the file {file_name}')
            self.download(index + 1)
            return

        thread = threading.Thread(target=target_thread)

        def start_thread():
            thread.start()

        root.protocol("WM_DELETE_WINDOW", lambda thread=thread, index=index: self._exit_window(thread, index))
        root.after(500, start_thread)
