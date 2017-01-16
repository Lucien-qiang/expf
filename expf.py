import cPickle
import gzip
import numpy
import theano

def prepare_data(seqs, labels, maxlen=None):
    """Create the matrices from the datasets.
    
    This pad each sequence to the same lenght: the lenght of the
    longuest sequence or maxlen.
    
    if maxlen is set, we will cut all sequence to this maximum
    lenght.
    
    This swap the axis!
    """
    lengths = [len(s) for s in seqs]
    if maxlen is not None:
        new_seqs = []
        new_labels = []
        new_lengths = []
        for l, s, y in zip(lengths, seqs, labels):
            if l < maxlen:
                new_seqs.append(s)
                new_labels.append(y)
                new_lengths.append(l)

        lengths = new_lengths
        labels = new_labels
        seqs = new_seqs
        if len(lengths) < 1:
            return (None, None, None)
    n_samples = len(seqs)
    maxlen = numpy.max(lengths)
    x = numpy.zeros((maxlen, n_samples)).astype('int64')
    x_mask = numpy.zeros((maxlen, n_samples)).astype(theano.config.floatX)
    for idx, s in enumerate(seqs):
        x[:lengths[idx], idx] = s
        x_mask[:lengths[idx], idx] = 1.0

    return (x, x_mask, labels)


def prepare_test_data(seqs, users, labels):
    lengths = [len(s) for s in seqs]
    u_lengths = [len(l) for l in users]
    y_lengths = [len(l) for l in labels]
    n_samples = len(seqs)
    maxlen = numpy.max(lengths)
    u_maxlen = numpy.max(u_lengths)
    y_maxlen = numpy.max(y_lengths)
    x = numpy.zeros((maxlen, n_samples)).astype('int64')
    u = numpy.zeros((u_maxlen, n_samples)).astype('int64')
    y = numpy.zeros((y_maxlen, n_samples)).astype('int64')
    x_mask = numpy.zeros((maxlen, n_samples)).astype(theano.config.floatX)
    u_mask = numpy.zeros((u_maxlen, n_samples)).astype(theano.config.floatX)
    y_mask = numpy.zeros((y_maxlen, n_samples)).astype(theano.config.floatX)
    for idx, s in enumerate(seqs):
        x[:lengths[idx], idx] = s
        x_mask[:lengths[idx], idx] = 1.0
        u[:u_lengths[idx], idx] = users[idx]
        u_mask[:u_lengths[idx], idx] = 1.0
        y[:y_lengths[idx], idx] = labels[idx]
        y_mask[:y_lengths[idx], idx] = 1.0

    return (
     x, x_mask, u, u_mask, y, y_mask)


def load_data(path='expf.pkl', n_words=100000, maxlen=None, sort_by_len=True):
    """Loads the dataset
    
    :type path: String
    :param path: The path to the dataset (here IMDB)
    :type n_words: int
    :param n_words: The number of word to keep in the vocabulary.
        All extra words are set to unknow (1).
    :type maxlen: None or positive int
    :param maxlen: the max sequence length we use in the train/valid set.
    :type sort_by_len: bool
    :name sort_by_len: Sort by the sequence lenght for the train,
        valid and test set. This allow faster execution as it cause
        less padding per minibatch. Another mechanism must be used to
        shuffle the train set at each epoch.
    
    """
    if path.endswith('.gz'):
        f = gzip.open(path, 'rb')
    else:
        f = open(path, 'rb')
    train_set, vtrain_set, valid_set, test_set = cPickle.load(f)
    f.close()
    if maxlen:
        new_train_set_x = []
        new_train_set_ug = []
        new_train_set_ub = []
        for x, ug, ub in zip(train_set[0], train_set[1], train_set[2]):
            if len(x) < maxlen:
                new_train_set_x.append(x)
                new_train_set_ug.append(ug)
                new_train_set_ub.append(ub)

        train_set = (
         new_train_set_x, new_train_set_ug, new_train_set_ub)
        del new_train_set_x
        del new_train_set_ug
        del new_train_set_ub

    def remove_unk(x):
        return [[(1 if w >= n_words else w) for w in sen] for sen in x]

    test_set_x, test_set_u, test_set_y = test_set
    valid_set_x, valid_set_u, valid_set_y = valid_set
    vtrain_set_x, vtrain_set_u, vtrain_set_y = vtrain_set
    train_set_x, train_set_ug, train_set_ub = train_set
    train_set_x = remove_unk(train_set_x)
    vtrain_set_x = remove_unk(vtrain_set_x)
    valid_set_x = remove_unk(valid_set_x)
    test_set_x = remove_unk(test_set_x)

    def len_argsort(seq):
        return sorted(range(len(seq)), key=lambda x: len(seq[x]))

    if sort_by_len:
        sorted_index = len_argsort(test_set_x)
        test_set_x = [test_set_x[i] for i in sorted_index]
        test_set_u = [test_set_u[i] for i in sorted_index]
        test_set_y = [test_set_y[i] for i in sorted_index]
        sorted_index = len_argsort(valid_set_x)
        valid_set_x = [valid_set_x[i] for i in sorted_index]
        valid_set_u = [valid_set_u[i] for i in sorted_index]
        valid_set_y = [valid_set_y[i] for i in sorted_index]
        sorted_index = len_argsort(vtrain_set_x)
        vtrain_set_x = [vtrain_set_x[i] for i in sorted_index]
        vtrain_set_u = [vtrain_set_u[i] for i in sorted_index]
        vtrain_set_y = [vtrain_set_y[i] for i in sorted_index]
        sorted_index = len_argsort(train_set_x)
        train_set_x = [train_set_x[i] for i in sorted_index]
        train_set_ug = [train_set_ug[i] for i in sorted_index]
        train_set_ub = [train_set_ub[i] for i in sorted_index]
    train = (train_set_x, train_set_ug, train_set_ub)
    vtrain = (vtrain_set_x, vtrain_set_u, vtrain_set_y)
    valid = (valid_set_x, valid_set_u, valid_set_y)
    test = (test_set_x, test_set_u, test_set_y)
    return (train, vtrain, valid, test)