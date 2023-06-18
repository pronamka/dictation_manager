import sys
from time import sleep

from core import BaseChecker, WordNotCompleted


class SpellChecker(BaseChecker):
    def __init__(self, comment: str, word: str, transcription: str = ""):
        super().__init__(comment, word)
        self.transcription = f"The transcription is `{transcription}`" if transcription else ""

    def check(self):
        if "n-" in self.words:
            return
        print(self.comment)
        self.get_answers()

    def get_answers(self):
        if len(self.words) == 1 and self.words[0].find("|") != -1:
            words = {i: 0 for i in self.words[0].split('|')}
            sleep(1)
            print(f"WARNING: There are {len(words)} variations. \n"
                  f"You must give all of them.", file=sys.stderr)
            while words:
                used = self.wait_for_right_answer(list(words.keys()))
                del words[used]
        else:
            self.wait_for_right_answer(self.words)

    def wait_for_right_answer(self, words):
        while (s := input()) not in words:
            if s == "1":
                print(f"The word is: {words[0]}")
            elif s == "2":
                print(f"The word was: {words[0]}")
                input("Now type it to remember.\n")
                print(self.transcription)
                print("OK. You will return to this word when you've "
                      "finished everything else.\n")
                raise WordNotCompleted
            else:
                print("WRONG ANSWER", file=sys.stderr)
        else:
            print(f"RIGHT! {self.transcription}\n")
            return s