from domogik.tests.common.helpers import check_domogik_is_running
import os

if __name__ == "__main__":
    print("=== Running unittests ===")
    os.system('python unittests/scenario_parameters.py')
    os.system('python unittests/xplmessage_test.py')

    print("=== Check domogik ===")
    if not check_domogik_is_running():
	exit(1)
    else:
	print(" => Domogik is running")
