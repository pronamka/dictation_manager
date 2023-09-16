import sys
from time import sleep

from core import BaseChecker, WordNotCompleted


class SpellChecker(BaseChecker):
    def __init__(self, comment: str, word: str, transcription: str = ""):
        super().__init__(comment, word)
        self.transcription = f"The transcription is `{transcription}`" if transcription else ""

    def check(self):
        if "n-" in [j for i in self.words_variations for j in i]:
            return
        print(self.comment)
        self.get_answers()

    def get_answers(self):
        amount_of_words_variations = len(self.words_variations)
        if amount_of_words_variations > 1:
            sleep(1)
            print(f"WARNING: There are {amount_of_words_variations} variations. \n"
                  f"You must give all of them.", file=sys.stderr)

        self.wait_for_right_answer(self.words_variations)

    def wait_for_right_answer(self, words: list[list]):
        words_plain = {j: num for num, val in enumerate(words) for j in val}
        words = {num: val for num, val in enumerate(words)}
        while words:
            answer = input()
            answer_index = words_plain.get(answer, None)

            if answer == "1":
                print(f"The word is: {words[0]}")
                return
            elif answer == "2":
                print(f"The word was: {words[0]}")
                input("Now type it to remember.\n")
                print(self.transcription)
                print("OK. You will return to this word when you've "
                      "finished everything else.\n")
                raise WordNotCompleted
            elif answer_index is None:
                print("WRONG ANSWER", file=sys.stderr)
                continue
            else:
                print(f"RIGHT! {self.transcription}\n")
                del words[answer_index]
                words_plain = {key: val for key, val in words_plain.items() if val != answer_index}
