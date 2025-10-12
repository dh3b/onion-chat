import curses
import threading
import logging
import socket
import datetime
from onionchat.utils.util_funcs import wrap_text
from onionchat.utils.typing_classes import *
from onionchat.core.generic_chat import GenericChatCore

logger = logging.getLogger(__name__)

class CEditCLI(GenericChatCore):
    """
        Curses based CLI chat interface.
        
        Args:
            input_sym: Input prompt symbol
            timestamps: Whether to show timestamps on messages
        """

    def __init__(self, sock: socket.socket | EmptySocket, encoding: str = "utf-8", recv_timeout: float = 1.0, input_sym: str = ">", timestamps: bool = True) -> None:
        if isinstance(sock, EmptySocket):
            logger.critical("Provided socket has not estabilished conenction")
            raise RuntimeError("Provided socket has not estabilished conenction")
        super().__init__(sock, encoding, recv_timeout)
        self.client_pref = str(sock.getpeername()[0])

        self.stdscr = None
        self.height, self.width = 0, 0
        self.max_display_size, self.max_input_size = 1024, 256
       
        self.input_sym = input_sym.strip() + " "
        self.temp_msgs = []
        self.inp = ""
        self.inp_pos, self.display_pos = 0, 0

        self.dt_format = "[%d-%m-%Y %H:%M:%S] " if timestamps else ""
        self.now = ""

        self.running = False

    def open(self) -> None:
        """Start chat session."""
        self.running = True
        curses.wrapper(self._handle_ui)

    def _handle_ui(self, stdscr) -> None:
        self.stdscr = stdscr

        # Init screen
        self.stdscr.clear()
        self.height, self.width = self.stdscr.getmaxyx()
        self.stdscr.addstr(self.height - 1, 0, self.input_sym)
        self.input_pad = curses.newpad(1, self.max_input_size)
        self.display_pad = curses.newpad(self.max_display_size, self.width)

        self.stdscr.refresh()

        # Init threads
        t_in = threading.Thread(target=self._in_thread)
        t_out = threading.Thread(target=self._out_thread)
        t_clock = threading.Thread(target=self._clock_thread, daemon=True)

        t_in.start()
        logger.debug("Started input thread")
        t_out.start()
        logger.debug("Started ouput thread")
        t_clock.start()
        logger.debug("Started clock thread")

        try:
            t_in.join()
            t_out.join()
            t_clock.join()
        except KeyboardInterrupt:
            pass

    def _clock_thread(self) -> None:
        while self.running:
            self.now = datetime.datetime.now().strftime(self.dt_format)
    
    def _in_thread(self) -> None:
        while self.running:
            key = self.stdscr.getch() # type: ignore
            match key:
                case 10 | curses.KEY_ENTER:  # Enter
                    msg = self.inp.strip()
                    self.inp = ""
                    self.inp_pos = 0
                    self._render_input()
                    if not msg or not msg.isprintable():
                        logger.debug(f"Unable to send invalid message: {msg!r}")
                        continue
                    
                    # Send message while still raw
                    try:
                        super().send_msg(msg)
                    except (BrokenPipeError, OSError):
                        logger.info("Connection lost")
                        self.running = False

                    self.temp_msgs += wrap_text(f"{self.now}You: {msg}", self.width)                  
                    self._render_display()
                case 265 | curses.KEY_F1:  # F1
                    try:
                        super().send_msg("__exit__")
                    except:
                        pass
                    logger.info("Exit chat")
                    self.running = False
                case 127 | curses.KEY_BACKSPACE: # Backspace
                    # remove character left of cursor
                    if self.inp and self.inp_pos > 0:
                        self.inp = self.inp[: self.inp_pos - 1] + self.inp[self.inp_pos :]
                        self.inp_pos -= 1
                        self._render_input()

                # Scrolling
                case curses.KEY_UP:
                    if self.get_bounded_display_pos() > 0:
                        self.display_pos -= 1
                        self._render_display()
                case curses.KEY_DOWN:
                    if self.display_pos < 0:
                        self.display_pos += 1
                        self._render_display()
                case curses.KEY_LEFT:
                    # clamp to start
                    self.inp_pos = max(0, self.inp_pos - 1)
                    self._render_input()
                case curses.KEY_RIGHT:
                    # clamp to end
                    self.inp_pos = min(len(self.inp), self.inp_pos + 1)
                    self._render_input()

                case _:
                    # 32 - 126 printable ASCII
                    if 32 <= key <= 126:
                        try:
                            char = chr(key)
                        except ValueError: 
                            continue

                        # insert at cursor: left + char + right
                        self.inp = self.inp[: self.inp_pos] + char + self.inp[self.inp_pos :]
                        self.inp_pos += 1
                        self._render_input()

    def _out_thread(self) -> None:
        while self.running:
            msg = super().recv_msg()
            
            if isinstance(msg, EmptyMessage):
                continue
            
            if isinstance(msg, TerminateConnection) or msg.strip() == "__exit__":
                logger.info("Peer disconnected")
                self.running = False
                break

            self.temp_msgs += wrap_text(f"{self.now}{self.client_pref}: {msg}", self.width)
            self._render_display()
            
    
    def get_bounded_display_pos(self) -> int:
        """
        Returns current display line position. Helper function, can use outside class threads,
        but is mainly meant for internal use.
        """

        usable_height = self.height - 1
        return max(usable_height, len(self.temp_msgs)) - usable_height + self.display_pos

    def get_bounded_input_pos(self) -> tuple[int, int]:
        """
        Compute input pad column (pad_col) and cursor x on the screen.
        Returns (pad_col, cursor_x).
        This mirrors get_bounded_display_pos but for input rendering/cursor.
        Also a helper function, refer to get_bounded_display_pos() docs.
        """

        usable_width = max(0, self.width - 1 - len(self.input_sym))
        max_pad_col = max(0, len(self.inp) - usable_width)
        # ensure cursor (inp_pos) is within the visible window [pad_col, pad_col+usable_width-1]
        pad_col = min(max(0, self.inp_pos - usable_width + 1), max_pad_col)

        # position cursor on screen relative to pad_col + input_sym
        cursor_x = len(self.input_sym) + (self.inp_pos - pad_col)
        cursor_x = min(max(len(self.input_sym), cursor_x), self.width - 1)
        return pad_col, cursor_x

    def _render_input(self) -> None:
        self.input_pad.clear()
        self.input_pad.addstr(0, 0, self.inp)

        pad_col, cursor_x = self.get_bounded_input_pos()
        self.stdscr.move(self.height - 1, cursor_x) # type: ignore

        self.input_pad.refresh(0, pad_col, self.height - 1, len(self.input_sym), self.height - 1, self.width - 1)

    def _render_display(self) -> None:
        self.display_pad.clear()
        for i, msg in enumerate(self.temp_msgs[:self.max_display_size]):
            self.display_pad.addstr(i, 0, msg)
        self.display_pad.refresh(self.get_bounded_display_pos(), 0, 0, 0, self.height - 2, self.width - 1)