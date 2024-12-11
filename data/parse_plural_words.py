from pathlib import Path
import enchant

file = Path(__file__).parent / "data" / "5_letter_words_spellchecked.txt"
words = file.read_text().splitlines()

not_plural = []
not_plural_ends_with_s = []
plural = []
for word in words:
    if word.endswith("S"):
        # See if the word is plural
        singular = word[:-1]
        d = enchant.Dict("en_US")
        if d.check(singular):
            plural.append(word)
        else:
            not_plural.append(word)
            not_plural_ends_with_s.append(word)

    else:
        not_plural.append(word)

not_plural_file = file.parent / "not_plural_spellchecked.txt"
plural_file = file.parent / "plural_spellchecked.txt"
not_plural_file.write_text("\n".join(not_plural))
plural_file.write_text("\n".join(plural))
for word in not_plural_ends_with_s:
    print(word)
print(len(not_plural_ends_with_s))
