def test_func(max_val):
    for idx in range(0, max_val):
        if idx == -1:
            print('Miss 1', idx)
        elif idx == 4:
            print('Hit 1', idx)
        elif idx == 6:
            print('Hit 2', idx)
        elif idx == 12:
            print('Miss 2', idx)
        else:
            print('Other', idx)
