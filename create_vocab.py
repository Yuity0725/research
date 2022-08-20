import sys
sys.path.append("../")

from data.fashionIQ import FashionIQDataset, FashionIQTestQueryDataset

clothing_types = ["dress", "shirt", "toptee"]
datasets = []
for clothing in clothing_types:
    datasets.append(FashionIQDataset(clothing_type=clothing))
    datasets.append(FashionIQTestQueryDataset(clothing_type=clothing))
caption_positions = [2 for _ in datasets]

from language.vocabulary import SimpleVocabulary
from language.tokenizers import NltkTokenizer
from language.utils import create_read_func, create_write_func

tokenizer = NltkTokenizer()
write_func = create_write_func('fashion_iq_vocab.pkl')
read_func = create_read_func('fashion_iq_vocab.pkl')
SimpleVocabulary.create_and_store_vocabulary_from_datasets(datasets, tokenizer, write_func, caption_pos=caption_positions)

vocab = SimpleVocabulary.create_vocabulary_from_storage(read_func)
print(len(vocab))