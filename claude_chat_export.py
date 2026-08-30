import json
import os
import re
import sys
import shutil
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict
from datetime import datetime


# ============================================================
# RESOURCE PATH
# ============================================================

def resource_path(filename):
    """
    Returns the correct path to a bundled resource.

    Works both when running:
        python 1.py

    and when running the PyInstaller EXE.
    """

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(
            sys._MEIPASS,
            filename
        )

    return os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        filename
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

class ClaudeChatExport:

    UNSUPPORTED = (
        "This block is not supported on your current device yet."
    )

    def __init__(self, root):

        self.root = root

        # ----------------------------------------------------
        # Application icon
        # ----------------------------------------------------

        self.icon_path = resource_path(
            "claude.ico"
        )

        if os.path.exists(
            self.icon_path
        ):

            try:
                self.root.iconbitmap(
                    self.icon_path
                )
            except Exception:
                pass

        # ----------------------------------------------------
        # Window
        # ----------------------------------------------------

        self.root.title(
            "Claude Chat Export"
        )

        self.root.geometry(
            "1400x850"
        )

        self.root.minsize(
            1000,
            650
        )

        self.conversations = []
        self.filtered = []

        self.create_ui()

    # ========================================================
    # USER INTERFACE
    # ========================================================

    def create_ui(self):

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = ttk.Frame(
            self.root
        )

        header.pack(
            fill="x",
            padx=20,
            pady=(15, 5)
        )

        ttk.Label(
            header,
            text="Claude Chat Export",
            font=("Segoe UI", 20, "bold")
        ).pack(
            anchor="w"
        )

        ttk.Label(
            header,
            text=(
                "Browse, read, copy and export "
                "your Claude conversations"
            )
        ).pack(
            anchor="w",
            pady=(2, 10)
        )

        # ----------------------------------------------------
        # File locations
        # ----------------------------------------------------

        files = ttk.LabelFrame(
            self.root,
            text="File Locations"
        )

        files.pack(
            fill="x",
            padx=20,
            pady=5
        )

        ttk.Label(
            files,
            text="conversations.json:"
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=8,
            sticky="w"
        )

        self.json_var = tk.StringVar()

        self.json_entry = ttk.Entry(
            files,
            textvariable=self.json_var
        )

        self.json_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=8,
            sticky="ew"
        )

        ttk.Button(
            files,
            text="Browse JSON...",
            command=self.browse_json
        ).grid(
            row=0,
            column=2,
            padx=10,
            pady=8
        )

        ttk.Label(
            files,
            text="Output folder:"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=8,
            sticky="w"
        )

        self.output_var = tk.StringVar()

        self.output_entry = ttk.Entry(
            files,
            textvariable=self.output_var
        )

        self.output_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=8,
            sticky="ew"
        )

        ttk.Button(
            files,
            text="Browse Folder...",
            command=self.browse_output
        ).grid(
            row=1,
            column=2,
            padx=10,
            pady=8
        )

        files.columnconfigure(
            1,
            weight=1
        )

        # ----------------------------------------------------
        # Toolbar
        # ----------------------------------------------------

        toolbar = ttk.Frame(
            self.root
        )

        toolbar.pack(
            fill="x",
            padx=20,
            pady=10
        )

        ttk.Button(
            toolbar,
            text="Load JSON",
            command=self.load_json
        ).pack(
            side="left",
            padx=4
        )

        ttk.Button(
            toolbar,
            text="Export All",
            command=self.export_all
        ).pack(
            side="left",
            padx=4
        )

        ttk.Button(
            toolbar,
            text="Clear",
            command=self.clear
        ).pack(
            side="left",
            padx=4
        )

        ttk.Label(
            toolbar,
            text="Search:"
        ).pack(
            side="left",
            padx=(30, 5)
        )

        self.search_var = tk.StringVar()

        self.search_var.trace_add(
            "write",
            self.search
        )

        ttk.Entry(
            toolbar,
            textvariable=self.search_var,
            width=40
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # Main panes
        # ----------------------------------------------------

        main_paned = ttk.PanedWindow(
            self.root,
            orient="horizontal"
        )

        main_paned.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        # ====================================================
        # LEFT
        # ====================================================

        left = ttk.Frame(
            main_paned
        )

        main_paned.add(
            left,
            weight=1
        )

        ttk.Label(
            left,
            text="Conversations",
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w",
            padx=5,
            pady=(5, 8)
        )

        list_frame = ttk.Frame(
            left
        )

        list_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "number",
            "date",
            "messages",
            "title"
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading(
            "number",
            text="#"
        )

        self.tree.heading(
            "date",
            text="Updated"
        )

        self.tree.heading(
            "messages",
            text="Messages"
        )

        self.tree.heading(
            "title",
            text="Conversation"
        )

        self.tree.column(
            "number",
            width=45,
            anchor="center"
        )

        self.tree.column(
            "date",
            width=145
        )

        self.tree.column(
            "messages",
            width=80,
            anchor="center"
        )

        self.tree.column(
            "title",
            width=450
        )

        tree_scroll = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=tree_scroll.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        tree_scroll.pack(
            side="right",
            fill="y"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.selected_changed
        )

        # ====================================================
        # RIGHT
        # ====================================================

        right = ttk.Frame(
            main_paned
        )

        main_paned.add(
            right,
            weight=3
        )

        right_header = ttk.Frame(
            right
        )

        right_header.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.chat_title_var = tk.StringVar(
            value="Full Conversation"
        )

        ttk.Label(
            right_header,
            textvariable=self.chat_title_var,
            font=("Segoe UI", 14, "bold")
        ).pack(
            side="left"
        )

        self.message_count_var = tk.StringVar(
            value=""
        )

        ttk.Label(
            right_header,
            textvariable=self.message_count_var
        ).pack(
            side="right"
        )

        # ----------------------------------------------------
        # Full chat
        # ----------------------------------------------------

        chat_frame = ttk.Frame(
            right
        )

        chat_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        self.details = tk.Text(
            chat_frame,
            wrap="word",
            font=("Consolas", 10),
            background="#fafafa",
            foreground="#202020",
            padx=15,
            pady=15,
            undo=False
        )

        details_scroll = ttk.Scrollbar(
            chat_frame,
            orient="vertical",
            command=self.details.yview
        )

        self.details.configure(
            yscrollcommand=details_scroll.set
        )

        self.details.pack(
            side="left",
            fill="both",
            expand=True
        )

        details_scroll.pack(
            side="right",
            fill="y"
        )

        self.details.configure(
            state="disabled"
        )

        # ----------------------------------------------------
        # Text formatting
        # ----------------------------------------------------

        self.details.tag_configure(
            "title",
            font=("Segoe UI", 16, "bold"),
            foreground="#111111"
        )

        self.details.tag_configure(
            "user",
            font=("Segoe UI", 11, "bold"),
            foreground="#0066cc"
        )

        self.details.tag_configure(
            "claude",
            font=("Segoe UI", 11, "bold"),
            foreground="#7a3e00"
        )

        self.details.tag_configure(
            "timestamp",
            foreground="#777777",
            font=("Consolas", 9)
        )

        self.details.tag_configure(
            "separator",
            foreground="#bbbbbb"
        )

        self.details.tag_configure(
            "metadata",
            foreground="#555555"
        )

        # ----------------------------------------------------
        # Mouse wheel
        # ----------------------------------------------------

        self.details.bind(
            "<MouseWheel>",
            self.mousewheel
        )

        self.details.bind(
            "<Button-4>",
            lambda event:
            self.details.yview_scroll(
                -3,
                "units"
            )
        )

        self.details.bind(
            "<Button-5>",
            lambda event:
            self.details.yview_scroll(
                3,
                "units"
            )
        )

        # ====================================================
        # Bottom
        # ====================================================

        bottom = ttk.Frame(
            self.root
        )

        bottom.pack(
            fill="x",
            padx=20,
            pady=12
        )

        ttk.Button(
            bottom,
            text="Copy Full Chat",
            command=self.copy_chat
        ).pack(
            side="left",
            padx=4
        )

        ttk.Button(
            bottom,
            text="Export TXT",
            command=self.export_txt
        ).pack(
            side="left",
            padx=4
        )

        ttk.Button(
            bottom,
            text="Export JSON",
            command=self.export_json
        ).pack(
            side="left",
            padx=4
        )

        ttk.Button(
            bottom,
            text="Export TXT + JSON",
            command=self.export_selected
        ).pack(
            side="left",
            padx=4
        )

        self.status_var = tk.StringVar(
            value="Select conversations.json to begin."
        )

        ttk.Label(
            bottom,
            textvariable=self.status_var
        ).pack(
            side="right",
            padx=10
        )

    # ========================================================
    # MOUSE WHEEL
    # ========================================================

    def mousewheel(self, event):

        if event.delta:

            self.details.yview_scroll(
                int(-event.delta / 120),
                "units"
            )

        return "break"

    # ========================================================
    # BROWSE JSON
    # ========================================================

    def browse_json(self):

        path = filedialog.askopenfilename(
            title="Select Claude conversations.json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        self.json_var.set(
            path
        )

        if not self.output_var.get().strip():

            suggested = os.path.join(
                os.path.dirname(path),
                "claude_exports"
            )

            self.output_var.set(
                suggested
            )

        self.load_json()

    # ========================================================
    # BROWSE OUTPUT
    # ========================================================

    def browse_output(self):

        folder = filedialog.askdirectory(
            title="Select output folder"
        )

        if folder:

            self.output_var.set(
                folder
            )

    # ========================================================
    # LOAD JSON
    # ========================================================

    def load_json(self):

        path = self.json_var.get().strip()

        if not path:

            messagebox.showwarning(
                "No file selected",
                "Please select your Claude conversations.json file."
            )

            return

        if not os.path.isfile(path):

            messagebox.showerror(
                "File not found",
                f"The following file does not exist:\n\n{path}"
            )

            return

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

        except json.JSONDecodeError as error:

            messagebox.showerror(
                "Invalid JSON",
                f"The selected file is not valid JSON.\n\n{error}"
            )

            return

        except Exception as error:

            messagebox.showerror(
                "Unable to load file",
                str(error)
            )

            return

        if isinstance(data, list):

            conversations = data

        elif isinstance(data, dict):

            conversations = data.get(
                "conversations",
                []
            )

        else:

            conversations = []

        if not conversations:

            messagebox.showwarning(
                "No conversations",
                "No conversations were found in this JSON file."
            )

            return

        self.conversations = conversations

        self.conversations.sort(
            key=lambda conversation:
            conversation.get(
                "updated_at",
                ""
            ),
            reverse=True
        )

        self.filtered = self.conversations.copy()

        self.refresh_list()

        self.status_var.set(
            f"Loaded {len(self.conversations)} conversations."
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search(self, *args):

        query = (
            self.search_var.get()
            .strip()
            .lower()
        )

        if not query:

            self.filtered = (
                self.conversations.copy()
            )

        else:

            self.filtered = []

            for conversation in self.conversations:

                title = self.get_title(
                    conversation
                ).lower()

                uuid = str(
                    conversation.get(
                        "uuid",
                        ""
                    )
                ).lower()

                if (
                    query in title
                    or query in uuid
                ):

                    self.filtered.append(
                        conversation
                    )

        self.refresh_list()

    # ========================================================
    # REFRESH LIST
    # ========================================================

    def refresh_list(self):

        for item in self.tree.get_children():

            self.tree.delete(
                item
            )

        for number, conversation in enumerate(
            self.filtered,
            1
        ):

            title = self.get_title(
                conversation
            )

            messages = self.get_current_branch(
                conversation.get(
                    "chat_messages",
                    []
                )
            )

            date = self.format_short(
                conversation.get(
                    "updated_at"
                )
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    number,
                    date,
                    len(messages),
                    title
                )
            )

    # ========================================================
    # TITLE
    # ========================================================

    def get_title(self, conversation):

        title = (
            conversation.get("name")
            or conversation.get("title")
            or ""
        )

        title = str(
            title
        ).strip()

        if title:

            return title

        messages = self.get_current_branch(
            conversation.get(
                "chat_messages",
                []
            )
        )

        for message in messages:

            if message.get(
                "sender"
            ) == "human":

                text = self.get_message_text(
                    message
                )

                if text:

                    text = re.sub(
                        r"\s+",
                        " ",
                        text
                    )

                    return text[:80]

        return "Untitled conversation"

    # ========================================================
    # MESSAGE TEXT
    # ========================================================

    def get_message_text(self, message):

        content = message.get(
            "content"
        )

        if isinstance(
            content,
            list
        ):

            parts = []

            for block in content:

                if not isinstance(
                    block,
                    dict
                ):
                    continue

                if block.get(
                    "type"
                ) == "text":

                    text = block.get(
                        "text",
                        ""
                    )

                    if text and text.strip():

                        parts.append(
                            text
                        )

            if parts:

                return "\n\n".join(
                    part.strip("\n")
                    for part in parts
                )

        text = message.get(
            "text",
            ""
        ) or ""

        text = text.replace(
            self.UNSUPPORTED,
            ""
        )

        return text.strip()

    # ========================================================
    # TIME
    # ========================================================

    @staticmethod
    def parse_time(message):

        timestamp = message.get(
            "created_at",
            ""
        )

        try:

            return datetime.fromisoformat(
                timestamp.replace(
                    "Z",
                    "+00:00"
                )
            )

        except Exception:

            return datetime.min

    # ========================================================
    # DATE
    # ========================================================

    @staticmethod
    def format_short(value):

        if not value:

            return "Unknown"

        try:

            date = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            )

            return date.strftime(
                "%Y-%m-%d %H:%M"
            )

        except Exception:

            return str(value)

    @staticmethod
    def format_full(value):

        if not value:

            return "Unknown"

        try:

            date = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            )

            return date.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        except Exception:

            return str(value)

    # ========================================================
    # CLAUDE BRANCH HANDLING
    # ========================================================

    def get_current_branch(self, messages):

        if not messages:

            return []

        by_uuid = {
            message.get("uuid"): message
            for message in messages
            if message.get("uuid")
        }

        children = defaultdict(list)
        roots = []

        for message in messages:

            parent = message.get(
                "parent_message_uuid"
            )

            if (
                parent
                and parent in by_uuid
            ):

                children[parent].append(
                    message
                )

            else:

                roots.append(
                    message
                )

        if not roots:

            return sorted(
                messages,
                key=self.parse_time
            )

        roots.sort(
            key=self.parse_time
        )

        result = []
        visited = set()

        for root in roots:

            uid = root.get(
                "uuid"
            )

            if uid in visited:

                continue

            path = self.deepest_path(
                root,
                children
            )

            for message in path:

                message_uid = message.get(
                    "uuid"
                )

                if message_uid:

                    visited.add(
                        message_uid
                    )

            result.extend(
                path
            )

        return result

    # ========================================================
    # DEEPEST PATH
    # ========================================================

    def deepest_path(
        self,
        root,
        children
    ):

        depth = {}
        best_child = {}
        state = {}

        stack = [
            (root, False)
        ]

        while stack:

            node, processed = stack.pop()

            uid = node.get(
                "uuid"
            )

            if not processed:

                if state.get(
                    uid
                ) == "done":

                    continue

                state[uid] = "processing"

                stack.append(
                    (node, True)
                )

                for child in children.get(
                    uid,
                    []
                ):

                    child_uid = child.get(
                        "uuid"
                    )

                    if state.get(
                        child_uid
                    ) == "processing":

                        continue

                    stack.append(
                        (child, False)
                    )

            else:

                valid_children = []

                for child in children.get(
                    uid,
                    []
                ):

                    child_uid = child.get(
                        "uuid"
                    )

                    if state.get(
                        child_uid
                    ) != "processing":

                        valid_children.append(
                            child
                        )

                if not valid_children:

                    depth[uid] = 1
                    best_child[uid] = None

                else:

                    best = max(
                        valid_children,
                        key=lambda child:
                        depth.get(
                            child.get("uuid"),
                            0
                        )
                    )

                    depth[uid] = (
                        1
                        + depth.get(
                            best.get("uuid"),
                            0
                        )
                    )

                    best_child[uid] = best

                state[uid] = "done"

        path = []

        current = root

        while current is not None:

            path.append(
                current
            )

            current = best_child.get(
                current.get("uuid")
            )

        return path

    # ========================================================
    # SELECTED CONVERSATION
    # ========================================================

    def get_selected(self):

        selection = self.tree.selection()

        if not selection:

            return None

        item = self.tree.item(
            selection[0]
        )

        values = item.get(
            "values"
        )

        if not values:

            return None

        index = int(
            values[0]
        ) - 1

        if (
            index < 0
            or index >= len(
                self.filtered
            )
        ):

            return None

        return self.filtered[
            index
        ]

    # ========================================================
    # SELECTED CHANGED
    # ========================================================

    def selected_changed(
        self,
        event=None
    ):

        conversation = self.get_selected()

        if conversation:

            self.show_full_conversation(
                conversation
            )

    # ========================================================
    # SHOW FULL CHAT
    # ========================================================

    def show_full_conversation(
        self,
        conversation
    ):

        title = self.get_title(
            conversation
        )

        messages = self.get_current_branch(
            conversation.get(
                "chat_messages",
                []
            )
        )

        self.chat_title_var.set(
            title
        )

        self.message_count_var.set(
            f"{len(messages)} messages"
        )

        self.details.configure(
            state="normal"
        )

        self.details.delete(
            "1.0",
            "end"
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        self.details.insert(
            "end",
            title + "\n",
            "title"
        )

        self.details.insert(
            "end",
            "=" * 90 + "\n\n",
            "separator"
        )

        self.details.insert(
            "end",
            f"UUID: {conversation.get('uuid', 'Unknown')}\n",
            "metadata"
        )

        self.details.insert(
            "end",
            f"CREATED: {self.format_full(conversation.get('created_at'))}\n",
            "metadata"
        )

        self.details.insert(
            "end",
            f"UPDATED: {self.format_full(conversation.get('updated_at'))}\n",
            "metadata"
        )

        self.details.insert(
            "end",
            f"MESSAGE COUNT: {len(messages)}\n\n",
            "metadata"
        )

        self.details.insert(
            "end",
            "=" * 90 + "\n",
            "separator"
        )

        self.details.insert(
            "end",
            "FULL CONVERSATION\n",
            "title"
        )

        self.details.insert(
            "end",
            "=" * 90 + "\n\n",
            "separator"
        )

        # ----------------------------------------------------
        # ALL MESSAGES
        # ----------------------------------------------------

        for number, message in enumerate(
            messages,
            1
        ):

            sender = self.sender(
                message
            )

            timestamp = self.format_full(
                message.get(
                    "created_at"
                )
            )

            body = self.get_message_text(
                message
            )

            if not body:

                body = (
                    "[No readable text in this message]"
                )

            if sender == "USER":

                self.details.insert(
                    "end",
                    f"{number}. USER\n",
                    "user"
                )

            elif sender == "CLAUDE":

                self.details.insert(
                    "end",
                    f"{number}. CLAUDE\n",
                    "claude"
                )

            else:

                self.details.insert(
                    "end",
                    f"{number}. {sender}\n"
                )

            self.details.insert(
                "end",
                f"{timestamp}\n",
                "timestamp"
            )

            self.details.insert(
                "end",
                "-" * 75 + "\n"
            )

            self.details.insert(
                "end",
                body
            )

            self.details.insert(
                "end",
                "\n\n"
            )

            self.details.insert(
                "end",
                "=" * 90 + "\n\n",
                "separator"
            )

        self.details.insert(
            "end",
            "END OF CONVERSATION\n",
            "title"
        )

        self.details.insert(
            "end",
            "=" * 90 + "\n",
            "separator"
        )

        self.details.configure(
            state="disabled"
        )

        self.details.yview_moveto(
            0
        )

    # ========================================================
    # SENDER
    # ========================================================

    @staticmethod
    def sender(message):

        sender = message.get(
            "sender",
            "unknown"
        )

        if sender == "human":

            return "USER"

        if sender == "assistant":

            return "CLAUDE"

        return str(
            sender
        ).upper()

    # ========================================================
    # BUILD PLAIN CHAT
    # ========================================================

    def build_chat(
        self,
        conversation
    ):

        title = self.get_title(
            conversation
        )

        messages = self.get_current_branch(
            conversation.get(
                "chat_messages",
                []
            )
        )

        lines = []

        lines.append(
            "=" * 90
        )

        lines.append(
            title
        )

        lines.append(
            "=" * 90
        )

        lines.append("")

        lines.append(
            f"UUID: {conversation.get('uuid', 'Unknown')}"
        )

        lines.append(
            f"CREATED: {self.format_full(conversation.get('created_at'))}"
        )

        lines.append(
            f"UPDATED: {self.format_full(conversation.get('updated_at'))}"
        )

        lines.append(
            f"MESSAGE COUNT: {len(messages)}"
        )

        lines.append("")

        for number, message in enumerate(
            messages,
            1
        ):

            sender = self.sender(
                message
            )

            timestamp = self.format_full(
                message.get(
                    "created_at"
                )
            )

            body = self.get_message_text(
                message
            )

            if not body:

                body = (
                    "[No readable text in this message]"
                )

            lines.append(
                "=" * 90
            )

            lines.append(
                f"{number}. {sender}"
            )

            lines.append(
                timestamp
            )

            lines.append(
                "-" * 75
            )

            lines.append(
                body
            )

            lines.append("")

        lines.append(
            "=" * 90
        )

        lines.append(
            "END OF CONVERSATION"
        )

        lines.append(
            "=" * 90
        )

        return "\n".join(
            lines
        )

    # ========================================================
    # COPY
    # ========================================================

    def copy_chat(self):

        conversation = self.get_selected()

        if not conversation:

            messagebox.showwarning(
                "No conversation selected",
                "Please select a conversation first."
            )

            return

        try:

            text = self.build_chat(
                conversation
            )

            self.root.clipboard_clear()

            self.root.clipboard_append(
                text
            )

            self.root.update()

            self.status_var.set(
                "Full conversation copied to clipboard."
            )

        except Exception as error:

            messagebox.showerror(
                "Clipboard error",
                str(error)
            )

    # ========================================================
    # SAFE FILENAME
    # ========================================================

    @staticmethod
    def safe_filename(name):

        name = re.sub(
            r'[\\/*?:"<>|]',
            "_",
            str(name)
        )

        name = re.sub(
            r"\s+",
            "_",
            name
        )

        name = name.strip(
            " ._"
        )

        if not name:

            name = "conversation"

        return name[:100]

    # ========================================================
    # EXPORT BASE
    # ========================================================

    def export_base(
        self,
        conversation
    ):

        title = self.safe_filename(
            self.get_title(
                conversation
            )
        )

        updated = conversation.get(
            "updated_at",
            ""
        )

        try:

            date = datetime.fromisoformat(
                updated.replace(
                    "Z",
                    "+00:00"
                )
            )

            date_text = date.strftime(
                "%Y%m%d_%H%M%S"
            )

        except Exception:

            date_text = "unknown"

        uuid = str(
            conversation.get(
                "uuid",
                "unknown"
            )
        )[:8]

        return (
            f"{date_text}_"
            f"{uuid}_"
            f"{title}"
        )

    # ========================================================
    # OUTPUT DIRECTORY
    # ========================================================

    def get_output_folder(self):

        folder = self.output_var.get().strip()

        if not folder:

            folder = filedialog.askdirectory(
                title="Select output folder"
            )

            if not folder:

                return None

            self.output_var.set(
                folder
            )

        try:

            os.makedirs(
                folder,
                exist_ok=True
            )

        except Exception as error:

            messagebox.showerror(
                "Output folder error",
                str(error)
            )

            return None

        return folder

    # ========================================================
    # EXPORT TXT
    # ========================================================

    def export_txt(self):

        conversation = self.get_selected()

        if not conversation:

            messagebox.showwarning(
                "No conversation",
                "Please select a conversation first."
            )

            return

        folder = self.get_output_folder()

        if not folder:

            return

        path = os.path.join(
            folder,
            self.export_base(
                conversation
            ) + ".txt"
        )

        try:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    self.build_chat(
                        conversation
                    )
                )

            self.status_var.set(
                f"TXT exported: {path}"
            )

            messagebox.showinfo(
                "Export complete",
                f"TXT file created:\n\n{path}"
            )

        except Exception as error:

            messagebox.showerror(
                "Export error",
                str(error)
            )

    # ========================================================
    # EXPORT JSON
    # ========================================================

    def export_json(self):

        conversation = self.get_selected()

        if not conversation:

            messagebox.showwarning(
                "No conversation",
                "Please select a conversation first."
            )

            return

        folder = self.get_output_folder()

        if not folder:

            return

        path = os.path.join(
            folder,
            self.export_base(
                conversation
            ) + ".json"
        )

        try:

            export_data = conversation.copy()

            export_data[
                "chat_messages"
            ] = self.get_current_branch(
                conversation.get(
                    "chat_messages",
                    []
                )
            )

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    export_data,
                    file,
                    indent=2,
                    ensure_ascii=False
                )

            self.status_var.set(
                f"JSON exported: {path}"
            )

            messagebox.showinfo(
                "Export complete",
                f"JSON file created:\n\n{path}"
            )

        except Exception as error:

            messagebox.showerror(
                "Export error",
                str(error)
            )

    # ========================================================
    # EXPORT TXT + JSON
    # ========================================================

    def export_selected(self):

        conversation = self.get_selected()

        if not conversation:

            messagebox.showwarning(
                "No conversation",
                "Please select a conversation first."
            )

            return

        folder = self.get_output_folder()

        if not folder:

            return

        base = self.export_base(
            conversation
        )

        txt_path = os.path.join(
            folder,
            base + ".txt"
        )

        json_path = os.path.join(
            folder,
            base + ".json"
        )

        try:

            with open(
                txt_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    self.build_chat(
                        conversation
                    )
                )

            export_data = conversation.copy()

            export_data[
                "chat_messages"
            ] = self.get_current_branch(
                conversation.get(
                    "chat_messages",
                    []
                )
            )

            with open(
                json_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    export_data,
                    file,
                    indent=2,
                    ensure_ascii=False
                )

            self.status_var.set(
                "Conversation exported successfully."
            )

            messagebox.showinfo(
                "Export complete",
                (
                    "Files created:\n\n"
                    f"{txt_path}\n\n"
                    f"{json_path}"
                )
            )

        except Exception as error:

            messagebox.showerror(
                "Export error",
                str(error)
            )

    # ========================================================
    # EXPORT ALL
    # ========================================================

    def export_all(self):

        if not self.conversations:

            messagebox.showwarning(
                "No conversations",
                "Load conversations.json first."
            )

            return

        folder = self.get_output_folder()

        if not folder:

            return

        answer = messagebox.askyesno(
            "Export all conversations",
            (
                f"Export all "
                f"{len(self.conversations)} "
                f"conversations as TXT + JSON?"
            )
        )

        if not answer:

            return

        try:

            count = 0

            for conversation in self.conversations:

                base = self.export_base(
                    conversation
                )

                txt_path = os.path.join(
                    folder,
                    base + ".txt"
                )

                json_path = os.path.join(
                    folder,
                    base + ".json"
                )

                with open(
                    txt_path,
                    "w",
                    encoding="utf-8"
                ) as file:

                    file.write(
                        self.build_chat(
                            conversation
                        )
                    )

                export_data = conversation.copy()

                export_data[
                    "chat_messages"
                ] = self.get_current_branch(
                    conversation.get(
                        "chat_messages",
                        []
                    )
                )

                with open(
                    json_path,
                    "w",
                    encoding="utf-8"
                ) as file:

                    json.dump(
                        export_data,
                        file,
                        indent=2,
                        ensure_ascii=False
                    )

                count += 1

            self.status_var.set(
                f"Exported {count} conversations."
            )

            messagebox.showinfo(
                "Export complete",
                (
                    f"{count} conversations exported.\n\n"
                    f"Output folder:\n{folder}"
                )
            )

        except Exception as error:

            messagebox.showerror(
                "Export error",
                str(error)
            )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self):

        self.conversations = []
        self.filtered = []

        self.json_var.set("")
        self.output_var.set("")
        self.search_var.set("")

        for item in self.tree.get_children():

            self.tree.delete(
                item
            )

        self.details.configure(
            state="normal"
        )

        self.details.delete(
            "1.0",
            "end"
        )

        self.details.configure(
            state="disabled"
        )

        self.chat_title_var.set(
            "Full Conversation"
        )

        self.message_count_var.set(
            ""
        )

        self.status_var.set(
            "Cleared."
        )


# ============================================================
# START
# ============================================================

def main():

    root = tk.Tk()

    app = ClaudeChatExport(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()
