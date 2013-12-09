from domogik.tests.common.helpers import check_domogik_is_running
import os

if __name__ == "__main__":
    print("=== Check domogik is running ===")
    if not check_domogik_is_running():
        exit(1)
    else:
        print(" => Domogik is running")

