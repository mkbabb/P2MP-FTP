import argparse
import pathlib
import threading
import socket
import time

from src.utils.utils import recv_message, send_message

ARQ_TIME = 100


def timed_join_all(threads: list[threading.Thread], timeout: int) -> None:
    start = curr_time = time.time()
    end = start + timeout
    while curr_time <= end:
        for t in threads:
            if not t.is_alive():
                t.join()
        time.sleep(0.1)
        curr_time = time.time()


def stop_n_wait_send(
    sockets: list[socket.socket], data: bytes, seq_nums: list[int]
) -> None:

    ixs = set(range(len(sockets)))
    acks = set()

    def inner(socket_ixs: set[int]) -> None:
        def send_recv(n: int, sock: socket.socket) -> None:
            seq_num = seq_nums[n]
            send_message(data, sock, seq_num)

            ack = recv_message(sock)

            seq_nums[n] = ack.seq_num

            acks.add(n)

        threads = []
        for n in socket_ixs:
            sock = sockets[n]
            t = threading.Thread(
                target=send_recv,
                args=(n, sock),
            )
            t.start()
            threads.append(t)

        timed_join_all(threads, ARQ_TIME)

    while len(socket_ixs := ixs.difference(acks)) != 0:
        inner(socket_ixs)


def sender(servers: list[str], port: int, filename: str, mss: int) -> None:
    sockets: list[socket.socket] = []
    seq_nums = [0] * len(servers)

    for hostname in servers:
        sockets.append(socket.create_connection((hostname, port)))

    filepath = pathlib.Path(filename)

    with filepath.open("rb") as file:
        while data := file.read(mss):
            stop_n_wait_send(sockets, data, seq_nums)

    for sock in sockets:
        sock.close()


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("servers", nargs="+", type=str)
    parser.add_argument("port", type=int)
    parser.add_argument("filename", type=str)
    parser.add_argument("mss", type=int)

    args = parser.parse_args()

    servers: list[str] = args.servers
    port = int(args.port)
    filename = args.filename
    mss = int(args.mss)

    sender(servers, port, filename, mss)


if __name__ == "__main__":
    main()
