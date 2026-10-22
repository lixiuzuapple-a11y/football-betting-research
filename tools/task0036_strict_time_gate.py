"""EV-Lab's adapter precondition before borrowing a third-party TimeSeriesSplit.

The upstream sports-betting backtest sorts rows, but equal-date groups can be
split across training/testing. Check SOURCE date-times, not just positional CV.
"""
from datetime import datetime

def assert_strict_temporal_fold(index, train_indices, test_indices):
    if not train_indices or not test_indices:
        raise ValueError("empty train/test fold")
    train=[index[i] for i in train_indices]
    test=[index[i] for i in test_indices]
    if any(not isinstance(x,datetime) for x in [*train,*test]):
        raise TypeError("require datetime index, not date-less match order")
    if max(train)>=min(test):
        raise ValueError("same-time/date or future-labelled training data in test fold")

def validate_all_folds(index,folds):
    for train,test in folds:
        assert_strict_temporal_fold(index,list(train),list(test))
