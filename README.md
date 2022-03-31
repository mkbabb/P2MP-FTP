# P2MP-FTP

Implementation of a simple P2MP FTP system: one client transmits a singular file to an
arbitrary number of receivers. Uses UDP, wrapped with an additional ARQ ACK scheme.

## Quick Start

No dependencies! Just Python **3.10**.

Nearly every file found herein is a Python _module_, thus it must be run like so:

    python3 -m $MODULE_NAME

To run the project in totality, with one client-sender node and one server-receiver
node, run the following in two shells:

    python3 -m src.client.sender

    python3 -m src.server.receiver

## [`client.py`](src/client/sender.py)

A client can connect to multiple server-receiver nodes and transmit a file thereupon.
The process of transmitting a file is as thus: a file is read and broken up in to `n`
pieces of size `mss` (maximum segment size). Each a timer is started, counting to
`ARQ_TIME` (automatic retry request time) seconds, and each server is then sent this
data chunk within its own thread. If any thread fails to return an acknowledgement
within that time, the chunk is sent again. This process is repeated until all servers
ACK back.

### positional arguments:

    servers     server hostname list
    port        port number to connect to the servers on
    filename    filename for the file to upload via FTP
    mss         maximum segment size, size of which to break the file up into chunks of size

## [`receiver.py`](src/server/receiver.py)

A server-receiver forks a new processes for each client transferring data thereto. The
UDP ARQ ACK scheme applies similarly: for each datagram processed, an ACK is sent back,
notifying the client that the data has been consumed successfully.

### positional arguments:

    port        port number to spawn the server on
    filename    filename to save the downloaded file to
    p           probability value, between 0 and 1, to simulate a packet loss

## Tasks

For each task, the file used for transfer was [`beatrice.jpg`](data/beatrice.jpg).

## Task 1

For the first task, an `mss` value of 500 (bytes) was used, in conjunction with with a
maximum of 5 receiver servers. As this implementation is written in Python, we found the
GIL (global interpreter lock) to be a large confounding factor in terms of parallelized
performance: with each added server, we found a slowdown of roughly 10x for the first
server, 5x for the second, tapering off to 2x with 5.

## Task 2

For the second task, we used 3 servers in totality, with a variable `mss` value ranging
from 100 to 1000 (divided into increments of 100). We found that there was a linear
relationship between the `mss` value and time between packet transfers. **As the `mss`
value increased, the time between packet transfers also increased, though marginally
so.** This was expected.

## Task 3

For the third and final task, we used, we used 3 servers in totality, with a variable
`p` value ranging from 0.01 to 0.1 (divided into increments of 0.01). We, too, found
that there was a linear relationship between the increased `p` value: **As the `p` value
increased, the time between packet transfers also increased.** This is to be expected,
as when we increase the frequency of packet loss, the time take to transfer will
increase - this is also conjointly related to the `ARQ_TIME` value, which determines the
timeout interval.
