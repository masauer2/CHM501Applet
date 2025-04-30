import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import webbrowser
import sys
from pylatexenc.latex2text import LatexNodes2Text
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QFileDialog, QListWidget, QMessageBox,
    QGridLayout, QSpinBox
)
from PyQt5.QtGui import QIcon
import datetime
from googleapiclient.discovery import build
from CHM501Applet.quickstart import SCOPES

# Replace with your credentials file path
CREDENTIALS_FILE = 'creds.json'

def to_pretty_html(text):
    return f"""
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
    <script src="CHM501Applet/jquery.jslatex.js"></script>
    <script>
    $(function () {{ $(".latex").latex(); }});
    </script>
    <html>
    <head>
    <style>
        body {{
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 24px;
            color: #333333;
        }}
    </style>
    </head>
    {text}
    </html>
    """

def get_today_events(tstart):
        creds = None

        # Load saved credentials if available
        if os.path.exists('creds/token.pkl'):
            with open('creds/token.pkl', 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, do OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())  # refresh silently
            else:
                flow = InstalledAppFlow.from_client_secrets_file('creds/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for next run
            with open('creds/token.pkl', 'wb') as token:
                pickle.dump(creds, token)

        # Build the Calendar API service
        service = build('calendar', 'v3', credentials=creds)

        # Fetch upcoming 10 events
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' = UTC time
        now = (datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(
            days=tstart)).isoformat() + 'Z'
        end_of_day = (datetime.datetime.utcnow().replace(hour=0, minute=0, second=0,microsecond=0) + datetime.timedelta(
            days=1)).isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now, timeMax=end_of_day, maxResults=10,
                                              singleEvents=True, orderBy='startTime').execute()

        events = events_result.get('items', [])

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))

        return events


class SimpleScheduleNotesApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.fname = ""
        self.tstart = 0



    def save_text(self, popup=True):
        #filename, _ = QFileDialog.getSaveFileName(self, "Save Notes", "", "Text Files (*.txt);;All Files (*)")
        filename = self.fname
        if popup:
            reply = QMessageBox.question(
                self,
                "Save Confirmation",
                f"Do you really want to save your note to {filename}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if filename != "" and reply == QMessageBox.Yes:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(self.text_edit.toPlainText())
            elif filename == "":
                QMessageBox.warning(self, "Save Error", "No filename provided. Please choose a file to save notes.")
                return

        else:
            if filename != "":
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(self.text_edit.toPlainText())


    def text_to_html(self):

        writer = ""
        number_of_lines = len(self.text_edit.toPlainText().split("\n"))
        for linenum in range(len(self.text_edit.toPlainText().split("\n"))):
            line = self.text_edit.toPlainText().split("\n")[linenum]
            if len(line) > 0:
                if line[0:3] == "===":
                    writer += "<font size=\"10px\"> " + line + "</font> <br><br> <body>"
                elif linenum == len(self.text_edit.toPlainText().split("\n")):
                    writer += LatexNodes2Text().latex_to_text(line) + "</body>"
                elif line[0] == '>':
                    writer += "<div class=\"latex\">" + LatexNodes2Text().latex_to_text(line[1:]) + "</div>"
                elif line[0] == '-':
                    writer += "<ul> <li>" + line[1:] + " </li> </ul>"
                elif line[0] == '+':
                    writer += "<font size=\"10px\"> " + line[1:] + "</font> <br><br> <body>"
                else:
                    writer += LatexNodes2Text().latex_to_text(line) + "<br>"
            if len(line) == 0:
                    writer += "<br>"

        write = to_pretty_html(writer)

        soup = BeautifulSoup(write, "html.parser")

        with open("output1.html", "w", encoding='utf-8') as file:
            file.write(str(soup))
        url = "output1.html"
        webbrowser.open('file://' + os.path.realpath(url), new=2)

    def update_notes_title(self):
        #self.save_text(popup=False)
        selected_items = self.events_list.selectedItems()

        if selected_items:
            event_text = selected_items[0].text()
            event_display = ' '.join(event_text.split()[3:])
            # You can parse the event_text to get just the event name if you want
            self.notes_title.setText(f'Notes for: <span style="color: #3498db;">{event_display}</span>')
        else:
            self.notes_title.setText("Notes:")

        if len(selected_items) == 1:
            for item in selected_items:
                event_text = item.text()
                self.fname = f"{event_text}_notes.txt"

                if os.path.exists(self.fname):
                    with open(self.fname, 'r', encoding='utf-8') as file:
                        content = file.read()
                        self.text_edit.setPlainText(content)

        elif len(selected_items) > 1:
            content = []
            content_str = ""
            for item in selected_items:
                event_text = item.text()
                self.fname = f"{event_text}_notes.txt"

                if os.path.exists(self.fname):
                    with open(self.fname, 'r', encoding='utf-8') as file:
                        content_str = f"{content_str}\n{file.read()}"
            self.text_edit.setPlainText(content_str)

        elif len(selected_items) == 0:
            self.text_edit.setPlainText("")

    def update_event_list(self):
        if not self.events:
            self.events_list.addItem("No events found for today.")
        else:
            for event in self.events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', 'No Title')
                # Format time nicely
                try:
                    start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    start_str = start_dt.strftime('%Y-%m-%d %H:%M')
                    self.events_list.addItem(f"{start_str} - {summary}")
                except Exception:
                    self.events_list.addItem(summary)
        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        return self.events_list

    def save_note(self):
        selected_items = self.events_list.selectedItems()

        if len(selected_items) != 1:
            # Show popup warning if multiple or zero items selected
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Save Not Allowed")
            msg.setText("Please select exactly one event to save a note.")
            msg.exec_()
            return

        event = selected_items[0].text()
        text = self.text_edit.toPlainText().strip()

        # Ask where to save
        options = QFileDialog.Options()
        file_path = self.fname
        #file_path, _ = QFileDialog.getSaveFileName(self, "Save Note", f"{event}.txt", "Text Files (*.txt)",options=options)

        if file_path:
            with open(file_path, 'w') as f:
                f.write(f"=== {event} ===\n")
                f.write(text + "\n")

            # Show success popup
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Note Saved")
            msg.setText(f"Note for '{event}' saved successfully!")
            msg.exec_()


    def update_event_list_again(self):
        self.events_list.clear()
        #self.tstart = int(self.clicker.toPlainText())
        self.tstart = self.clicker.value()
        self.events = get_today_events(self.tstart)
        self.events_list = self.update_event_list()

    def init_ui(self):
        self.setWindowIcon(QIcon('applogo.jpg'))
        self.setWindowTitle('Simple Schedule + Notes')

        # Main layout
        layout = QGridLayout()

        # Label for Schedule
        layout.addWidget(QLabel("Today's Schedule:"), 0, 0, 1, 3)

        # Events list (placeholder for now)
        self.events_list = QListWidget()
        self.events_list.setSelectionMode(QListWidget.MultiSelection)
        self.events_list.itemSelectionChanged.connect(self.update_notes_title)
        self.events = get_today_events(5)

        layout.addWidget(self.events_list, 1, 0, 1, 3)

        # Label for Notes


        # Text editor
        self.clickerLabel = QLabel("Date Range (X Days Ago):")
        #self.clickerLabel.setFixedSize(100, 20)
        layout.addWidget(self.clickerLabel, 2, 0, 1, 1)

        #self.clicker = QTextEdit()
        #self.clicker.setFixedSize(500, 20)
        #layout.addWidget(self.clicker, 2, 1, 1, 1)

        self.clicker = QSpinBox(self)
        self.clicker.setRange(0, 99)  # Set min and max values
        self.clicker.setSingleStep(1)
        self.clicker.valueChanged.connect(self.update_event_list_again)
        layout.addWidget(self.clicker, 2, 1, 1, 1)

        self.change_button = QPushButton('Get New Range')
        self.change_button.clicked.connect(self.update_event_list_again)
        layout.addWidget(self.change_button, 2, 2, 1, 1)


        self.notes_title = QLabel("Notes:")
        #self.clickerLabel.setFixedSize(100, 20)
        layout.addWidget(self.notes_title, 3, 0, 1, 3)

        self.text_edit = QTextEdit()
        #self.text_edit.setFixedSize(500,100)
        layout.addWidget(self.text_edit, 4, 0, 1, 3)


        # Save button
        self.save_button = QPushButton('Save Notes')
        self.save_button.clicked.connect(self.save_note)
        layout.addWidget(self.save_button)

        self.gen_button = QPushButton('Generate Summary')
        self.gen_button.clicked.connect(self.text_to_html)
        layout.addWidget(self.gen_button)

        self.setLayout(layout)
        layout.setColumnStretch(0, 1)  # Left column stretches 1x
        layout.setColumnStretch(1, 10)
        layout.setColumnStretch(2, 1) # Right column stretches 2x
        layout.setRowStretch(0, 2)
        layout.setRowStretch(1, 10)
        layout.setRowStretch(2, 1)
        layout.setRowStretch(3, 2)
        layout.setRowStretch(4, 20)  # Right column stretches 2x
        self.resize(500, 500)

def main():
    app = QApplication(sys.argv)
    window = SimpleScheduleNotesApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()