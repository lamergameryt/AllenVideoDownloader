from tkinter import *
from tkinter import messagebox
import os
import sys
from ctypes import windll
# noinspection PyPackageRequirements
from allen import AllenClient, AllenInvalidUsernamePassword
import utils
import asyncio

tcl = os.environ.get("TCL_LIBRARY", None)
tk = os.environ.get("TK_LIBRARY", None)

if tcl is not None and tk is not None:
    pass
elif len(sys.path) > 1:
    pass
else:
    print("assuming we run in frozen mode")
    print("setting TCL & TK environment")
    p0 = sys.path[0]
    tcl = os.path.join(p0, "tcl8.6")
    tk = os.path.join(p0, "tk8.6")
    os.environ["TCL_LIBRARY"] = tcl
    os.environ["TK_LIBRARY"] = tk

window = Tk()


def close_btn_click():
    window.destroy()


def login_btn_click(form_number, password, login_btn: Button):
    if login_btn['state'] == 'disabled':
        return

    if asyncio.get_event_loop().is_closed():
        asyncio.set_event_loop(asyncio.new_event_loop())

    async_loop = asyncio.get_event_loop()

    if len(form_number.get()) == 0 or len(password.get()) == 0:
        messagebox.showerror(title='Empty Fields', message='Please make sure you enter a form number and a password.')
        return

    try:
        client = AllenClient(username=form_number.get(), password=password.get())
    except AllenInvalidUsernamePassword:
        messagebox.showerror(title='Incorrect Credentials',
                             message='The form number or password entered is incorrect.')
        return

    try:
        login_btn['state'] = 'disabled'
        async_loop.run_until_complete(do_downloads(client, login_btn))
    finally:
        async_loop.close()


async def do_downloads(client: AllenClient, login_btn: Button):
    videos = list()
    for video in client.get_recorded_videos():
        if utils.check_exists(video):
            continue
        videos.append(video)

    downloader = utils.VideoDownloader(videos, window, login_btn)
    downloader.download()


GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080

lastClickX = 0
lastClickY = 0


def set_appwindow(main_window):
    """
    Allow the window to be displayed as an application in the taskbar.

    :param main_window: The tkinter window.
    """
    myappid = 'lamergameryt.allenvideodownloader.1.1.06'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    hwnd = windll.user32.GetParent(main_window.winfo_id())
    stylew = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    stylew = stylew & ~WS_EX_TOOLWINDOW
    stylew = stylew | WS_EX_APPWINDOW
    windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, stylew)
    main_window.wm_withdraw()
    main_window.after(10, lambda: main_window.wm_deiconify())


def save_last_click_pos(event):
    global lastClickX, lastClickY
    lastClickX = event.x
    lastClickY = event.y


def dragging(event):
    x, y = event.x - lastClickX + window.winfo_x(), event.y - lastClickY + window.winfo_y()
    window.geometry("+%s+%s" % (x, y))


def main():
    """
    GUI Properties and behaviour to dragging definition.
    """
    # Disable window controls and enable window moving
    window.overrideredirect(True)
    window.title('Allen Video Downloader')
    window.bind('<Button-1>', save_last_click_pos)
    window.bind('<B1-Motion>', dragging)
    window.geometry("983x526+%d+%d" % (500, 300))
    window.configure(bg="#ffffff")
    window.iconbitmap('assets/logo.ico')
    window.after(10, lambda: set_appwindow(window))

    canvas = Canvas(window, bg="#ffffff", width=983, height=526, bd=0, highlightthickness=0, relief="ridge")
    canvas.place(x=0, y=0)

    """
    Background colour creation and insertion.
    """
    # Creates the blue and white sections seen in the GUI.
    canvas.create_rectangle(0, 0, 517, 526, fill="#b46db2", outline="")
    canvas.create_rectangle(517, 0, 983, 526, fill="#f3f3f3", outline="")
    canvas.create_rectangle(38, 121, 167, 126, fill="#ffffff", outline="")

    """
    Textbox and background creation.
    """
    textbox_img = PhotoImage(file="assets/textbox.png")

    # Create the dark background for input fields
    canvas.create_image(744, 307.5, image=textbox_img)
    canvas.create_image(744, 211.5, image=textbox_img)

    form_number = Entry(bd=0, bg="#e3e3e3", font='Arial 10', highlightthickness=0)
    form_number.place(x=584, y=209, width=320, height=30)
    form_number.focus()

    password = Entry(bd=0, show="*", font="Arial 10", bg="#e3e3e3", highlightthickness=0)
    password.place(x=584, y=305, width=320, height=30)

    # The text displayed above the text input fields
    canvas.create_text(633, 198, text="Form Number", fill="#403f3f", font=("Arial", 11, "bold"))
    canvas.create_text(620.5, 293, text="Password", fill="#403f3f", font=("Arial", 11, "bold"))

    """
    Heading text and description of program.
    """
    canvas.create_text(734.5, 92.5, text="Enter your details.", fill="#403f3f", font=("Arial", 30, "bold"))
    canvas.create_text(259, 92.5, text="Allen Video Downloader", fill="#ffffff", font=("Arial", 30, "bold"))

    canvas.create_text(
        260, 295,
        text="Allen Video Downloader uses Allen’s API\n"
             "and your form number and password to\n"
             "authenticate and fetch the video\n"
             "recordings from their website.\n\n"
             "By using this application, you agree to the\n"
             "Terms and Service specified during the\n"
             "installation of the program.",
        fill="#ffffff",
        font=("Arial", 18))

    """
    Button images and functionality definitions.
    """
    login_img = PhotoImage(file="assets/login.png")
    close_img = PhotoImage(file="assets/close_btn.png")

    login_btn = Button(image=login_img, borderwidth=0, highlightthickness=0,
                       command=lambda: login_btn_click(form_number, password, login_btn), relief="flat")
    login_btn.place(x=616, y=398, width=255, height=48)

    close_btn = Button(image=close_img, borderwidth=0, highlightthickness=0, command=close_btn_click, relief="flat")
    close_btn.place(x=950, y=18, width=10, height=16)

    window.resizable(False, False)
    window.attributes('-topmost', True)
    window.update()
    window.attributes('-topmost', False)
    window.mainloop()


if __name__ == '__main__':
    main()
