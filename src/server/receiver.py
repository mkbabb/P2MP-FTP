import argparse
import pathlib
import random
import socket
import threading
from typing import Optional

from src.utils.utils import recv_message, send_message


def server_receiver(peer_socket: socket.socket, filename: str, p: float) -> None:
    filepath = pathlib.Path(filename)

    with filepath.open("wb") as file:
        while True:
            packet = recv_message(peer_socket)
            r = random.random()

            if packet is not None:
                seq_num = packet.seq_num + 1
                send_message(b"", peer_socket, seq_num)

                if packet.data_len == 0:
                    break
                else:
                    file.write(packet.data)


def server(port: int, filename: str, p: float) -> None:
    address = (socket.gethostname(), port)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(address)
    server_socket.listen(32)

    try:
        while True:
            conn, _ = server_socket.accept()
            t = threading.Thread(
                target=server_receiver,
                args=(conn, filename, p),
            )
            t.start()

    except KeyboardInterrupt:
        pass


def main() -> None:
    def probability_type(s: str) -> Optional[float]:
        x = float(s)
        if not (0 < x <= 1):
            raise argparse.ArgumentTypeError("p value must be between 0 and 1")
        return x

    parser = argparse.ArgumentParser()

    parser.add_argument("port", type=int)
    parser.add_argument("filename", type=str)
    parser.add_argument("p", type=probability_type)

    args = parser.parse_args()

    port = int(args.port)
    filename = args.filename
    p = int(args.p)

    server(port, filename, p)


if __name__ == "__main__":
    main()
