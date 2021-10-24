def test_func(max_val):
    for idx in range(0, max_val):
        match idx:
            case -1:
                print("Miss 1", idx)
            case 4:
                print("Hit 1", idx)
            case 6:
                print("Hit 2", idx)
            case 12:
                print("Miss 2", idx)
            case _:
                print("Other", idx)
