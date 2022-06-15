"""
    Testing control app
"""

import time
from zmq_node import push_msg, pull_msg


def control_main():
    while True:
        label = input("Enter label: ")
        print(f"Sending: {label}")
        push_msg(label)

        while True:
            response = pull_msg()
            if response:
                print(response[0])
                break

            time.sleep(0.5)

if __name__ == "__main__":
    control_main()
