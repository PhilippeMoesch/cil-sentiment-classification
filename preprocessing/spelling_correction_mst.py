import os
import sys

from preprocessing_interface import PreprocessingInterface
import enchant
from dict import Dict
import multiprocessing as mp
import threading
from math import floor

file_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(file_path, '../embed'))
from mst import MMST
from embeddings import Loader


class SpellingCorrectionMST(PreprocessingInterface):

    def __init__(self):
        self.nb = 0
        self.cores = mp.cpu_count()
        self.load = Loader()
        self.load.loadGloveModel()


    def prep_input(self):
        sentences = []
        with open(self.input, mode='r') as input:
            for line in input:
                sentences.append(line)
                self.nb += 1

        split_size = int(self.nb/self.cores)
        for i in range(self.cores-1):
            with open(self.input + '_' + str(i), "w+") as f:
                for j in range(i*split_size, (i+1)*split_size):
                    f.write(sentences[j])

        i = self.cores-1
        with open(self.input + '_' + str(i), "w+") as f:
            for j in range(i*split_size, self.nb):
                f.write(sentences[j])


    def checker(self, id, d, slang_dict, stop_words, emoji_dict):
        g = MMST(d, slang_dict, stop_words, emoji_dict)
        input = open(self.input + '_' + str(id), "r")
        with open(self.output + '_' + str(id), "w+") as f:
            for line in input:
                try:
                    tmp = g.input_sentence(line, self.load, verbose=False)
                    f.write(tmp)
                except IndexError:
                    print(line)

    def run(self):
        super().run()

        dict = Dict()
        slang_dict = dict.get_slang()
        stop_words = dict.get_stopwords()
        emoji_dict = dict.get_emoticon()
        d = enchant.Dict("en_US")

        self.prep_input()

        # dictionnary defined in MMST __init___
        share = floor(self.nb / self.cores)

        ts = [threading.Thread(target=self.checker, args=(i, d, slang_dict, stop_words, emoji_dict)) for i in range(self.cores)]

        for t in ts:
            t.start()
        for t in ts:
            t.join()
