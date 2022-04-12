import argparse
import multiprocessing as mp
import pathlib
import socket
import time
from multiprocessing.pool import AsyncResult, Pool

from src.utils.utils import recv_message, send_message

ARQ_TIME = 1


def timed_join_all(processes: list[AsyncResult], timeout: int) -> None:
    start = curr_time = time.time()
    end = start + timeout
    while curr_time <= end:
        if all((p.ready()) for p in processes):
            return
        time.sleep(0.001)
        curr_time = time.time()


def send_recv(n: int, sock: socket.socket, data: bytes, seq_nums: list[int]) -> tuple:
    send_message(data, sock, seq_nums[n])
    sock.settimeout(ARQ_TIME)
    ack = recv_message(sock)

    return n, ack


def stop_n_wait_send(
    pool: Pool,
    sockets: list[socket.socket],
    data: bytes,
    seq_nums: list[int],
) -> None:
    ixs = set(range(len(sockets)))
    acks: set[int] = set()

    def callback(args) -> None:
        n, packet = args
        seq_nums[n] = packet.seq_num
        acks.add(n)

    def inner(socket_ixs: set[int]) -> None:
        processes: list[AsyncResult] = [
            pool.apply_async(
                send_recv, args=(n, sockets[n], data, seq_nums), callback=callback
            )
            for n in socket_ixs
        ]
        timed_join_all(processes, ARQ_TIME)

    while len(socket_ixs := ixs.difference(acks)) != 0:
        inner(socket_ixs)


def sender(servers: list[str], port: int, filename: str, mss: int) -> None:
    sockets: list[socket.socket] = []
    seq_nums = [0] * len(servers)

    for n, hostname in enumerate(servers):
        sockets.append(socket.create_connection((hostname, port + n)))

    filepath = pathlib.Path(filename)

    with mp.Pool(len(sockets) * 2) as pool:
        with filepath.open("rb") as file:
            while data := file.read(mss):
                stop_n_wait_send(pool, sockets, data, seq_nums)

        stop_n_wait_send(pool, sockets, b"", seq_nums)

        for sock in sockets:
            sock.close()


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("servers", nargs="+", type=str, help="server hostname list")
    parser.add_argument(
        "port", type=int, help="port number to connect to the servers on"
    )
    parser.add_argument(
        "filename", type=str, help="filename for the file to upload via FTP"
    )
    parser.add_argument(
        "mss",
        type=int,
        help="maximum segment size, size of which to break the file up into chunks of size",
    )

    args = parser.parse_args()

    servers: list[str] = args.servers
    port = int(args.port)
    filename = args.filename
    mss = int(args.mss)

    sender(servers, port, filename, mss)


if __name__ == "__main__":
    main()
