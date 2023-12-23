import sys
import threading
import time
from threading import Thread, Lock
from time import sleep

from channel import *

writing_count = 0
accumulate = 0
NP = 20
delta = 100

DATAFILE = "datafile.txt"
LOGFILE = "log.txt"
TOTALCOUNT = 20

mutex = Lock()
channel_mutex = Lock()
ids_in_ring_mutex = Lock()
log_file_mutex = Lock()
datafile_mutex = Lock()
writing_count_mutex = Lock()
accumulate_mutex = Lock()

creation_cond = threading.Condition()

start_time = 0
c = Channel()
ids_in_ring = []
MAX_TIME = 50000


def pass_token(current_node, left_node):
    with channel_mutex:
        current_node_ind = c.subgroup("RING").index(str(current_node).encode("UTF-8"))
        left_node_ind = c.subgroup("RING").index(str(left_node).encode("UTF-8"))
        sender = c.subgroup("RING")[current_node_ind].decode("utf-8")

        c.bind(sender)
        destination = [c.subgroup("RING")[left_node_ind].decode("utf-8")]
        c.sendTo(destination, "token")


def pass_request(current_node, right_node):
    with channel_mutex:
        current_node_ind = c.subgroup("RING").index(str(current_node).encode("UTF-8"))
        right_node_ind = c.subgroup("RING").index(str(right_node).encode("UTF-8"))
        sender = c.subgroup("RING")[current_node_ind].decode("utf-8")
        c.bind(sender)
        destination = [c.subgroup("RING")[right_node_ind].decode("utf-8")]
        c.sendTo(destination, "token")


def receive_token(current_node, right_node):
    with channel_mutex:
        current_node_ind = c.subgroup("RING").index(str(current_node).encode("UTF-8"))
        right_node_ind = c.subgroup("RING").index(str(right_node).encode("UTF-8"))
        receiver = c.subgroup("RING")[current_node_ind].decode("utf-8")
        c.bind(receiver)
        destination = [c.subgroup("RING")[right_node_ind].decode("utf-8")]
        rec = c.recvFrom(destination, 1)

    if rec is not None:
        return True

    if rec is None:
        return False


def receive_request_for_token(current_node, left_node):
    with channel_mutex:
        current_node_ind = c.subgroup("RING").index(str(current_node).encode("UTF-8"))
        left_node_ind = c.subgroup("RING").index(str(left_node).encode("UTF-8"))
        receiver = c.subgroup("RING")[current_node_ind].decode("utf-8")

        c.bind(receiver)
        destination = [c.subgroup("RING")[left_node_ind].decode("utf-8")]
        rec = c.recvFrom(destination, 1)
    if rec is not None:
        return True

    if rec is None:
        return False


def write_log(line, filename):
    with log_file_mutex:
        with open(filename, 'a+') as file:
            file.write(line)


def write_datafile(acc, count, filename):
    with datafile_mutex:
        with open(filename, 'w+') as file:
            file.write(str(acc) + "\n")
            file.write(str(count))


def process(pid):
    local_random = random.Random()
    local_random.seed(start_time + pid)

    os_pid = threading.get_native_id()

    global accumulate
    global writing_count
    my_updates_count = 0
    with channel_mutex:
        id_in_ring = int(c.join("RING"))

    with ids_in_ring_mutex:
        ids_in_ring.append(id_in_ring)

    has_token = False
    wants_token = False
    received_request = False
    passed_request = False
    global mutex

    if pid == 0:
        has_token = True

    if pid != NP - 1:
        with creation_cond:
            creation_cond.wait()

    if pid == NP - 1:
        with creation_cond:
            creation_cond.notify_all()

    left_neighbor = ids_in_ring[(pid + 1) % NP]
    right_neighbor = ids_in_ring[(pid - 1) % NP]
    time_for_next_request = -1
    time_after_last_reset = 0
    requests_count = 0

    while True:
        if writing_count >= TOTALCOUNT:
            return

        if time_for_next_request == -1:
            # generate random time
            time_for_next_request = local_random.randint(0, MAX_TIME)
            time_after_last_reset = time.time() * 1000
            passed_request = False

        remaining_time = time_for_next_request - ((time.time() * 1000) - time_after_last_reset)

        if remaining_time <= 0:
            wants_token = True

        if wants_token:
            if not has_token:
                has_token = receive_token(id_in_ring, right_node=right_neighbor)

                if not has_token and not passed_request:
                    pass_request(id_in_ring, right_node=right_neighbor)
                    passed_request = True
                    print("process %d wants the token" % (pid))

            if has_token:
                with mutex:
                    with accumulate_mutex:
                        accumulate += delta
                    with writing_count_mutex:
                        writing_count += 1
                    my_updates_count += 1

                    write_datafile(accumulate, writing_count, DATAFILE)
                    print("Writing %d" % pid)

                    line = "t=%d, pid= %d, ospid=%d, new=%d, my_updates=%d ,total_count=%d is writing to file\n" % (
                        (time.time() * 1000) - start_time, pid, os_pid, accumulate, my_updates_count, writing_count)
                    write_log(line, LOGFILE)
                    time_for_next_request = -1
                wants_token = False

        if not has_token and not wants_token and requests_count > 0:
            has_token = receive_token(id_in_ring, right_node=right_neighbor)

        received_request = receive_request_for_token(id_in_ring, left_node=left_neighbor)

        if received_request:
            requests_count += 1
            if not has_token:
                pass_request(id_in_ring, right_neighbor)

        if has_token:
            if requests_count > 0:
                has_token = False
                pass_token(id_in_ring, left_neighbor)
                requests_count -= 1


def get_time_since_start():
    return (time.time() * 1000) - start_time


if __name__ == '__main__':

    NP = int(sys.argv[1])
    DATAFILE = sys.argv[2]
    delta = int(sys.argv[3])
    TOTALCOUNT = int(sys.argv[4])
    LOGFILE = sys.argv[5]
    MAX_TIME = int(sys.argv[6])

    start_time = round(time.time() * 1000)
    print("Start time:")
    print(start_time)
    print("Please wait for initalization....\n")
    # process()
    for i in range(0, NP):
        sleep(1)
        t = Thread(target=process, args=(i,))
        t.start()

