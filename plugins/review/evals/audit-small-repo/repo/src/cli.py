import sys

from src.bank import connect, find_account, withdraw


def main(argv):
    db = connect()
    if argv[1] == "lookup":
        print(find_account(db, argv[2]))
    elif argv[1] == "withdraw":
        print("new balance:", withdraw(db, int(argv[2]), int(argv[3])))


if __name__ == "__main__":
    main(sys.argv)
