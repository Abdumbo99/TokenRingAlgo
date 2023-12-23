# Token Ring Algorithm
This project was writted for CS442 Distributed Systems and Algorithms at Bilkent University by Abdul Razak Khatib. 
**Code written by me is found in myClient.py**

## Breif Explanation
"Token Ring algorithm achieves mutual exclusion in a distributed system by creating a bus network of processes. A logical ring is constructed with these processes and each process is assigned a position in the ring. Each process knows who is next in line after itself.

### The algorithm works as follows:
When the ring is initialized, process 0 is given a token. The token circulates around the ring. When a process acquires the token from its neighbor, it checks to see if it is attempting to enter a critical region. If so, the process enters the region, does all the work it needs to, and leaves the region. After it has exited, it passes the token to the next process in the ring. It is not allowed to enter the critical region again using the same token. If a process is handed the token by its neighbor and is not interested in entering a critical region, it just passes the token along to the next process."
[denninginstitute.](https://denninginstitute.com/workbenches/token/token.html#:~:text=The%20algorithm%20works%20as%20follows,to%20enter%20a%20critical%20region.)

In this project I used the a file called channel.py (from Distributed Systems, M. van Steen and A. Tannenbaum, textbook [website](https://www.distributed-systems.net/index.php/books/ds3/), “Additional material” section). However, some changes were made. For example BLPOP was used to receive the messages, in this project LPOP was used. The reason for that is that BLPOP blocks for at least a second, which considered a long period for this project. Another change was that the message received from LPOP was not processed or parsed since it is about receiving a signal only regardless of the content.
Only one thread per process was used, then each one of them would communicate with its left neighbor, for receiving requests or sending token, or its right neighbor, for sending request or receiving token, using a redis channel.
Channel are assigned random ids. So to solve this I save one more id, id_in_ring, then using this id I find the index and set them as the left and right neighbours for each thread. I also used a condition to wait for all threads to
be properly initialised and added to the channel before I can assign neighbours and start working.
### The state machine is the following:
1. Check if we reached max count if so return (terminate thread).
2. If the waiting time is up, set wants_token = True.
3. If We don’t the token try and receive it, in case it was sent before to us.
4. If no token was received; send a request to get it.
5. If we get the token we write to the file, before that we update the count and accumulate variables.
6. Afterwards, in case the token was not wanted yet (waiting time not up yet) we check if we received a token (someone else requested it)
7. We receive any pending requests and update a count in case multiple nodes request the token.
8. If the node does not have the token it passes the request.
9. If it has the token it passes it and decrement the count of requests.
Since we were deadline with threads we used global variables and mutex variables, for all shared counts, channel, files, etc.


