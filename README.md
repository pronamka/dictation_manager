# Dictation Manager

A desktop application built with Python and Flet that helps users effectively learn vocabulary from foreign languages using custom Excel files, spaced repetition, and dictation-style practice.

---

## Features

### Import Your Own Vocabulary

* Prepare any vocabulary list in Excel (.xlsx) format.
* Inside the app, create schemes that define how the app interprets your Excel columns.
* Reuse schemes for multiple files.

### Dictation & Practice Mode

* Start a **dictation session** to train vocabulary.
* The app shows the translation; you must type the correct word.
* Optional **Narrator** reads words aloud.
* Toggle **mix/shuffle** mode to randomize order.
* View **additional information** for each word (examples, notes, etc.).

### Spaced Repetition System (SRS)

* Every word has a **status** based on how well you’ve mastered it.
* The app automatically schedules when each word should reappear.
* Helps focus on weak spots while retaining learned words long-term.

### Flet Desktop UI

* Cross-platform UI (Windows, macOS, Linux).
* Clean, responsive interface.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/pronamka/dictation_manager.git
cd dictation_manager/
```

### 2. Install Dependencies

Make sure you have **Python 3.10+** installed.

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
cd desktop_version/
python main_app.py
```

---

## How to Use

### Step 1: Prepare Your Excel File

Create a spreadsheet with your vocabulary (example):

| word | translation | example sentence | notes |
| ---- | ----------- | ---------------- | ----- |

### Step 2: Create a Scheme

Inside the app:

* Define which column is the **word**, which is the **translation**, and which optional columns contain extra info.
* Save the scheme for future use.

### Step 3: Start Learning

* Select a vocabulary file
* Choose your scheme
* Start a dictation session
* Type the answer, listen with Narrator, and track progress with the SRS system

---

## Technologies Used

* **Python**
* **Flet** for UI
* **openpyxl & pandas** for Excel parsing
* **gtts &  pygame** for text-to-speech
* Custom spaced repetition logic
